# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Offline tests for recheck_sources.py. No test contacts a supplier.

Run with: uv run tests/test_recheck_sources.py. The fetch function is injected, and the page bytes are
project-authored. A test that forgets to inject a fetch fails at once, because the default fetch raises.
"""
import datetime
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SKILL = ROOT / "skills" / "pcb-fab-package"
SCRIPTS = SKILL / "scripts"
REAL_MANIFEST = SKILL / "sources.yaml"
sys.path.insert(0, str(SCRIPTS))
import fetch_sources as FS  # noqa: E402
import recheck_sources as RC  # noqa: E402


def _no_network(url):
    raise AssertionError(f"network access is not allowed in tests: {url}")


FS.default_fetch = _no_network

RESULTS = []
PAGE = b"<!doctype html>\n<title>fixture page</title>\n"
OTHER = b"<!doctype html>\n<title>other fixture</title>\n"
PLAIN = b"plain fixture bytes\n"
MARKER_PAGE = b"<!doctype html>\n<title>MARKER-7f3a</title>\n"
FIXED = datetime.datetime(2026, 11, 25, 12, 0, 0, tzinfo=datetime.timezone.utc)
BOUND = "supplier/profiles/fixture-two-layer.yaml"
PAGE_PATH = "supplier/pages/two-layer.html"
PAGE_URL = "https://example.invalid/page"


def check(name, cond, detail=""):
    RESULTS.append((name, bool(cond)))
    print(("ok   " if cond else "FAIL ") + name + ("" if cond else f": {detail}"))


def sha(data):
    return hashlib.sha256(data).hexdigest()


class Fake:
    """Return fixture bytes per URL, or raise the exception stored for that URL. Record each call."""

    def __init__(self, table=None):
        self.table = table or {}
        self.calls = []

    def __call__(self, url):
        self.calls.append(url)
        value = self.table.get(url)
        if isinstance(value, BaseException):
            raise value
        if value is None:
            raise FS.FetchFailed(f"no fixture for {url}")
        return value


def profile_text(key, digest):
    return yaml.safe_dump({"id": "fixture-two-layer", "extensions": {"evidence_pages": {
        key: {"sha256": digest, "source_url": "https://example.invalid/page"}}}}, sort_keys=False)


def new_root(tmp, label):
    root = tmp / label
    (root / "supplier" / "pages").mkdir(parents=True)
    (root / "supplier" / "profiles").mkdir(parents=True)
    (root / "supplier" / "profiles" / "fixture-two-layer.yaml").write_text(profile_text("two-layer", sha(PAGE)))
    return root


def entry(ident, path, body=PAGE, **over):
    data = {"id": ident, "path": path, "url": f"https://example.invalid/{ident}", "retrieved": "2026-11-15",
            "sha256": sha(body), "content_type": "text/html", "magic": "markup", "license_state": "fixture",
            "distribution_decision": "exclude-full-copy", "profile_binding": None}
    data.update(over)
    return data


def write_manifest(root, entries):
    path = root / "sources.yaml"
    path.write_text(yaml.safe_dump({"schema": "cad-skills/sources", "schema_version": 1, "sources": entries},
                                   sort_keys=False))
    return path


def snapshot(path):
    return path.read_bytes() if path.is_file() else None


def files_under(directory):
    return sorted(str(p.relative_to(directory)) for p in directory.rglob("*")) if directory.exists() else []


def state(root):
    return {rel: snapshot(root / rel) for rel in files_under(root)}


WATCH_URLS = {
    "oshpark-four-layer-html": "https://example.invalid/oshpark-four-layer-html",
    "oshpark-six-layer-html": "https://example.invalid/oshpark-six-layer-html",
}


def watch_root(tmp, label, skip=(), edit=None):
    """Write two bound watch pages, their two local-evidence headers and the manifest. Return the manifest path.

    skip removes manifest ids. edit changes the entry mappings before the manifest is written."""
    root = tmp / label
    (root / "supplier" / "pages").mkdir(parents=True)
    (root / "supplier" / "profiles").mkdir(parents=True)
    for name in ("four-layer", "six-layer"):
        (root / "supplier" / "profiles" / f"{name}.yaml").write_text(profile_text(name, sha(PAGE)))
    rows = [
        entry("oshpark-four-layer-html", "supplier/pages/four-layer.html",
              profile_binding="supplier/profiles/four-layer.yaml"),
        entry("oshpark-four-layer-headers", "supplier/pages/four-layer.headers", body=b"HTTP/1.1 200 OK\n",
              distribution_decision="exclude-local-evidence", magic=None, content_type="text/plain"),
        entry("oshpark-six-layer-html", "supplier/pages/six-layer.html",
              profile_binding="supplier/profiles/six-layer.yaml"),
        entry("oshpark-six-layer-headers", "supplier/pages/six-layer.headers", body=b"HTTP/1.1 200 OK\n",
              distribution_decision="exclude-local-evidence", magic=None, content_type="text/plain"),
    ]
    rows = [row for row in rows if row["id"] not in skip]
    if edit is not None:
        edit(rows)
    return write_manifest(root, rows)


def run_check(argv, fake, environ=None, watch=()):
    """Run the check with an injected fetch. Fixture manifests pass no watch list unless a test needs one."""
    return RC.main(argv, fetch=fake, environ={} if environ is None else environ, now=FIXED, watch=watch)


def test_all_match(tmp):
    root = new_root(tmp, "match")
    manifest = write_manifest(root, [entry("page", PAGE_PATH, profile_binding=BOUND)])
    fake = Fake({PAGE_URL: PAGE})
    code, text = run_check(["--manifest", str(manifest)], fake)
    check("1: all match exits 0 and the Markdown says no action",
          code == 0 and "No action" in text, (code, text[:300]))


def test_changed_page(tmp):
    root = new_root(tmp, "changed")
    manifest = write_manifest(root, [entry("page", PAGE_PATH, profile_binding=BOUND)])
    code, text = run_check(["--manifest", str(manifest), "--format", "json"], Fake({PAGE_URL: OTHER}))
    report = json.loads(text)
    row = report["entries"][0]
    check("2: a changed page exits 1 with the recorded and the observed hash",
          code == 1 and row["status"] == "changed" and row["recorded_sha256"] == sha(PAGE)
          and row["observed_sha256"] == sha(OTHER), (code, row))
    check("3: the action names the profile binding and fab.py review-source",
          row["action"] is not None and BOUND in row["action"] and "fab.py review-source" in row["action"]
          and report["actions"] == [row["action"]], report["actions"])


def test_candidate_entry(tmp):
    root = new_root(tmp, "candidate")
    manifest = write_manifest(root, [entry("page", PAGE_PATH, sha256=None)])
    code, text = run_check(["--manifest", str(manifest), "--format", "json"], Fake({PAGE_URL: PAGE}))
    row = json.loads(text)["entries"][0]
    check("4: a null manifest hash exits 1 with status candidate and the candidate hash",
          code == 1 and row["status"] == "candidate" and row["candidate_sha256"] == sha(PAGE), (code, row))


def test_magic_mismatch(tmp):
    root = new_root(tmp, "magic")
    manifest = write_manifest(root, [entry("page", "supplier/pages/plain.html", body=PLAIN)])
    code, text = run_check(["--manifest", str(manifest), "--format", "json"],
                           Fake({"https://example.invalid/page": PLAIN}))
    row = json.loads(text)["entries"][0]
    check("5: a correct hash with a wrong magic token exits 1 with status magic-mismatch",
          code == 1 and row["status"] == "magic-mismatch" and row["magic_status"] == "mismatch", (code, row))


def test_fetch_failure(tmp):
    root = new_root(tmp, "failure")
    manifest = write_manifest(root, [entry("page", PAGE_PATH)])
    code, text = run_check(["--manifest", str(manifest), "--format", "json"],
                           Fake({PAGE_URL: FS.FetchFailed("HTTP 503")}))
    row = json.loads(text)["entries"][0]
    check("6: a fetch failure exits 3 with status fetch-error and the fetch action",
          code == 3 and row["status"] == "fetch-error" and row["action"] == RC.ACTION_FETCH, (code, row))


def test_changed_and_fetch_failure(tmp):
    root = new_root(tmp, "both")
    manifest = write_manifest(root, [entry("page", PAGE_PATH, profile_binding=BOUND),
                                     entry("other", "supplier/pages/other.html")])
    fake = Fake({PAGE_URL: OTHER, "https://example.invalid/other": FS.FetchFailed("timeout")})
    code, text = run_check(["--manifest", str(manifest), "--format", "json"], fake)
    report = json.loads(text)
    statuses = {row["id"]: row["status"] for row in report["entries"]}
    check("7: a changed page and a fetch failure exit 3 and both rows are in the report",
          code == 3 and statuses == {"page": "changed", "other": "fetch-error"}, (code, statuses))
    check("8: the actions hold the review action and the fetch action",
          RC.ACTION_FETCH in report["actions"] and any("fab.py review-source" in a for a in report["actions"]),
          report["actions"])


def test_local_evidence_skipped(tmp):
    root = new_root(tmp, "skipped")
    manifest = write_manifest(root, [
        entry("page", PAGE_PATH, profile_binding=BOUND),
        entry("page-headers", "supplier/pages/two-layer.headers", body=b"HTTP/1.1 200 OK\n",
              distribution_decision="exclude-local-evidence", magic=None, content_type="text/plain"),
    ])
    fake = Fake({PAGE_URL: PAGE})
    code, text = run_check(["--manifest", str(manifest), "--format", "json"], fake)
    rows = {row["id"]: row["status"] for row in json.loads(text)["entries"]}
    check("9: a local-evidence entry is not fetched and has status skipped-local-evidence",
          code == 0 and fake.calls == [PAGE_URL] and rows["page-headers"] == "skipped-local-evidence",
          (code, fake.calls, rows))


def test_manifest_defect(tmp):
    def drop_url(rows):
        rows[0].pop("url")

    manifest = watch_root(tmp, "defect", edit=drop_url)
    fake = Fake()
    code, text = run_check(["--manifest", str(manifest)], fake, watch=RC.WATCH_ITEMS)
    check("10: a manifest defect exits 2 with the fetch_sources message and no fetch",
          code == 2 and fake.calls == [] and "missing keys" in text, (code, fake.calls, text))


def test_writes_nothing(tmp):
    root = new_root(tmp, "writes")
    shutil.rmtree(root / "supplier" / "pages")
    manifest = write_manifest(root, [entry("page", PAGE_PATH, profile_binding=BOUND)])
    before = state(root)
    code_changed, _ = run_check(["--manifest", str(manifest)], Fake({PAGE_URL: OTHER}))
    after_changed = state(root)
    code_match, _ = run_check(["--manifest", str(manifest)], Fake({PAGE_URL: PAGE}))
    after_match = state(root)
    check("11: a changed run and a match run change no file and create no supplier/pages",
          code_changed == 1 and code_match == 0 and before == after_changed == after_match
          and not (root / "supplier" / "pages").exists(), (code_changed, code_match))


def test_no_pages_dir_needed(tmp):
    root = new_root(tmp, "nopages")
    shutil.rmtree(root / "supplier" / "pages")
    manifest = write_manifest(root, [entry("page", PAGE_PATH, profile_binding=BOUND)])
    code, _ = run_check(["--manifest", str(manifest)], Fake({PAGE_URL: PAGE}))
    check("12: a root with no supplier/pages and a bound profile exits 0 on a match",
          code == 0 and not (root / "supplier" / "pages").exists(), code)


def test_watch_items_reported(tmp):
    manifest = watch_root(tmp, "watch")
    fake = Fake({WATCH_URLS["oshpark-four-layer-html"]: PAGE, WATCH_URLS["oshpark-six-layer-html"]: PAGE})
    code, text = run_check(["--manifest", str(manifest), "--format", "json"], fake, watch=RC.WATCH_ITEMS)
    watch = {row["entry"]: row for row in json.loads(text)["watch"]}
    check("13: the JSON watch list has both items with their dates",
          code == 0 and watch["oshpark-four-layer-html"]["since"] == "2026-01-28"
          and watch["oshpark-six-layer-html"]["since"] == "2025-12-15", (code, watch))
    code_md, md = run_check(["--manifest", str(manifest)], fake, watch=RC.WATCH_ITEMS)
    check("14: the Markdown names both watch dates", "2026-01-28" in md and "2025-12-15" in md, md[:300])


def test_watch_item_changed(tmp):
    manifest = watch_root(tmp, "watchchanged")
    fake = Fake({WATCH_URLS["oshpark-four-layer-html"]: PAGE, WATCH_URLS["oshpark-six-layer-html"]: OTHER})
    code, text = run_check(["--manifest", str(manifest), "--format", "json"], fake, watch=RC.WATCH_ITEMS)
    watch = {row["entry"]: row["status"] for row in json.loads(text)["watch"]}
    check("15: a changed watch page exits 1 and its watch row has status changed",
          code == 1 and watch["oshpark-six-layer-html"] == "changed", (code, watch))


def test_watch_item_missing(tmp):
    manifest = watch_root(tmp, "watchmissing", skip=("oshpark-six-layer-html",))
    fake = Fake()
    code, text = run_check(["--manifest", str(manifest)], fake, watch=RC.WATCH_ITEMS)
    check("16: a missing watch id exits 2, names the id, and fetches nothing",
          code == 2 and "oshpark-six-layer-html" in text and fake.calls == [], (code, text))


def test_watch_not_selected(tmp):
    manifest = watch_root(tmp, "notselected")
    fake = Fake({WATCH_URLS["oshpark-four-layer-html"]: PAGE})
    code, text = run_check(["--manifest", str(manifest), "--entry", "oshpark-four-layer-html", "--format", "json"],
                           fake, watch=RC.WATCH_ITEMS)
    watch = {row["entry"]: row["status"] for row in json.loads(text)["watch"]}
    check("17: an unselected watch item has status not-selected and the run exits 0",
          code == 0 and watch["oshpark-six-layer-html"] == "not-selected", (code, watch))


def test_ci_guard_refuses(tmp):
    root = new_root(tmp, "ci")
    manifest = write_manifest(root, [entry("page", PAGE_PATH)])
    fake = Fake({PAGE_URL: PAGE})
    code, text = run_check(["--manifest", str(manifest)], fake, environ={"CI": "true"})
    check("18: the CI guard exits 2, names --allow-ci, and fetches nothing",
          code == 2 and fake.calls == [] and "--allow-ci" in text, (code, text))


def test_ci_guard_allow(tmp):
    root = new_root(tmp, "ciallow")
    manifest = write_manifest(root, [entry("page", PAGE_PATH)])
    fake = Fake({PAGE_URL: PAGE})
    code, _ = run_check(["--manifest", str(manifest), "--allow-ci"], fake, environ={"CI": "true"})
    check("19: --allow-ci lets a run continue in a CI shell and exits 0 on a match",
          code == 0 and fake.calls == [PAGE_URL], (code, fake.calls))


def test_bad_arguments(tmp):
    root = new_root(tmp, "args")
    manifest = write_manifest(root, [entry("page", PAGE_PATH)])
    fake = Fake({PAGE_URL: PAGE})
    code_missing, _ = run_check(["--format", "json"], fake)
    code_format, _ = run_check(["--manifest", str(manifest), "--format", "xml"], fake)
    check("20: missing --manifest or an unknown --format exits 2 and fetches nothing",
          code_missing == 2 and code_format == 2 and fake.calls == [], (code_missing, code_format, fake.calls))


def test_entry_not_mapping(tmp):
    root = new_root(tmp, "notmapping")
    manifest = write_manifest(root, [entry("page", PAGE_PATH), "not a mapping"])
    fake = Fake({PAGE_URL: PAGE})
    try:
        code, text = run_check(["--manifest", str(manifest)], fake)
    except TypeError as err:  # a traceback is a defect of the command
        code, text = None, f"traceback: {err}"
    check("26: a manifest entry that is not a mapping exits 2 with a message and fetches nothing",
          code == 2 and fake.calls == [] and "not a mapping" in text, (code, text))


def test_json_shape(tmp):
    root = new_root(tmp, "shape")
    manifest = write_manifest(root, [entry("page", PAGE_PATH, profile_binding=BOUND)])
    code, text = run_check(["--manifest", str(manifest), "--format", "json"], Fake({PAGE_URL: PAGE}))
    report = json.loads(text)
    keys = {"schema", "schema_version", "run_utc", "manifest_sha256", "overall", "exit", "entries", "watch", "actions"}
    check("21: the JSON report has the documented keys and the manifest hash",
          set(report) == keys and report["manifest_sha256"] == sha(manifest.read_bytes())
          and report["run_utc"] == "2026-11-25T12:00:00Z" and report["exit"] == code == 0
          and report["overall"] == "all match", sorted(report))


def test_report_has_no_page_bytes(tmp):
    root = new_root(tmp, "bytes")
    manifest = write_manifest(root, [entry("page", PAGE_PATH, body=MARKER_PAGE)])
    fake = Fake({PAGE_URL: MARKER_PAGE})
    _, md = run_check(["--manifest", str(manifest)], fake)
    _, js = run_check(["--manifest", str(manifest), "--format", "json"], fake)
    check("22: neither the Markdown nor the JSON holds the page text",
          "MARKER-7f3a" not in md and "MARKER-7f3a" not in js, "marker found")


def test_real_manifest_watch_ids(tmp):
    data = FS.load_manifest(REAL_MANIFEST)
    by_id = {row["id"]: row for row in data["sources"]}
    for item in RC.WATCH_ITEMS:
        row = by_id.get(item["entry"])
        check(f"23: watch item {item['entry']} is in the real manifest, bound, and full-copy",
              row is not None and row["profile_binding"] is not None
              and row["distribution_decision"] == "exclude-full-copy"
              and (SKILL / row["profile_binding"]).is_file(), item["entry"])


def test_real_manifest_offline(tmp):
    data = FS.load_manifest(REAL_MANIFEST)
    full = [row for row in data["sources"] if row["distribution_decision"] == "exclude-full-copy"]
    local = [row for row in data["sources"] if row["distribution_decision"] == "exclude-local-evidence"]
    fake = Fake()
    code, text = RC.main(["--manifest", str(REAL_MANIFEST), "--format", "json"], fetch=fake, environ={}, now=FIXED)
    report = json.loads(text)
    statuses = [row["status"] for row in report["entries"]]
    check("24: the real manifest passes validation offline and reports every entry",
          code == 3 and len(report["entries"]) == len(data["sources"]) and len(fake.calls) == len(full),
          (code, len(report["entries"]), len(full)))
    check("25: the real manifest gives fetch-error for each full copy and skipped-local-evidence for each header",
          statuses.count("fetch-error") == len(full) and statuses.count("skipped-local-evidence") == len(local),
          statuses)


def test_main_subprocess_ci(tmp):
    # A manifest path that does not exist. The CI guard must stop the run before it reads the manifest
    # or contacts a page. Thus an exit code 2 with the refusal text shows that no fetch occurs.
    missing = tmp / "subprocess-ci" / "sources.yaml"
    env = {"CI": "1", "PATH": ""}
    done = subprocess.run([sys.executable, str(SCRIPTS / "recheck_sources.py"), "--manifest", str(missing)],
                          capture_output=True, text=True, env=env)
    check("27: the __main__ path with CI set exits 2, writes the refusal to stderr, and contacts no page",
          done.returncode == 2 and done.stdout == "" and "--allow-ci" in done.stderr
          and "No such file" not in done.stderr, (done.returncode, done.stdout, done.stderr))


def main():
    tmp = Path(tempfile.mkdtemp(prefix="recheck-sources-"))
    try:
        for name, value in sorted(globals().items()):
            if name.startswith("test_") and callable(value):
                value(tmp)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    passed = sum(1 for _, ok in RESULTS if ok)
    print(f"\n{passed}/{len(RESULTS)} passed")
    return 0 if passed == len(RESULTS) else 1


if __name__ == "__main__":
    sys.exit(main())
