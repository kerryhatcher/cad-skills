# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Offline tests for skills/pcb-fab-package/scripts/fetch_sources.py.

Run with: uv run tests/test_source_retrieval.py. No test calls a supplier. The fetch function is injected, and the
response bytes are project-authored. The redirect and 404 cases use a server on 127.0.0.1.
"""
import hashlib
import http.server
import os
import shutil
import sys
import tempfile
import threading
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "pcb-fab-package" / "scripts"
SKILL = ROOT / "skills" / "pcb-fab-package"
PROFILES = ROOT / "skills" / "pcb-fab-package" / "supplier" / "profiles"
sys.path.insert(0, str(SCRIPTS))
import fetch_sources as FS  # noqa: E402
import project_io as PIO  # noqa: E402
sys.path.insert(0, str(ROOT / "tests"))
import fab_fixture  # noqa: E402

RESULTS = []
PAGE = b"<!doctype html>\n<title>fixture page</title>\n"
OTHER = b"<!doctype html>\n<title>other fixture</title>\n"
OLE = bytes.fromhex("D0CF11E0A1B11AE1") + b"fixture"
PLAIN = b"plain fixture bytes\n"
LAYOUT_A = (b'<!doctype html>\n<html><head><title>Fixture</title><style>p{color:red}</style>'
            b'<script>var build="a1";</script></head>\n<body><!-- build a1 --><p>Trace 6 mil &amp; space</p>'
            b'<noscript>Enable scripts</noscript><p>Drill 10 mil</p></body></html>\n')
LAYOUT_B = (b'<!doctype html>\n<html lang="en"><head><title>Fixture</title><style>p{color:blue}</style>'
            b'<script src="/app.js?v=b2"></script></head>\n<body class="v2"><!-- build b2 --><p id="t">Trace  6\tmil &#38; space</p>'
            b'<noscript>Scripts are off</noscript><p>Drill 10 mil</p></body></html>\n')
RULE_CHANGE = LAYOUT_A.replace(b"Drill 10 mil", b"Drill 12 mil")
NOT_UTF8 = b"<p>\xff\xfe</p>"


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


def text_sha(data):
    return FS.text_sha256(data)


def layout_root(tmp, label):
    """Make a root whose two-layer profile binds the LAYOUT_A bytes. Each label must be unique."""
    root = new_root(tmp, label)
    (root / "supplier" / "profiles" / "fixture-two-layer.yaml").write_text(profile_text("two-layer", sha(LAYOUT_A)))
    return root


def entry(ident, path, body=PAGE, **over):
    data = {"id": ident, "path": path, "url": f"https://example.invalid/{ident}", "retrieved": "2026-11-15",
            "sha256": sha(body), "content_type": "text/html", "magic": "markup", "license_state": "fixture",
            "distribution_decision": "exclude-full-copy", "profile_binding": None}
    data.update(over)
    return data


def write_manifest(root, entries, drop=None, extra=None, schema="cad-skills/sources", version=1):
    data = {"schema": schema, "schema_version": version, "sources": entries}
    for key in drop or []:
        data.pop(key, None)
    data.update(extra or {})
    path = root / "sources.yaml"
    path.write_text(yaml.safe_dump(data, sort_keys=False))
    return path


def run(manifest, fake, *extra):
    return FS.main(["--manifest", str(manifest), *extra], fetch=fake)


def rows_by_id(report):
    return {row["id"]: row for row in report.get("entries", [])}


def snapshot(path):
    return path.read_bytes() if path.is_file() else None


def files_under(directory):
    return sorted(str(p.relative_to(directory)) for p in directory.rglob("*")) if directory.exists() else []


def test_basic(tmp):
    root = new_root(tmp, "basic")
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html")])
    fake = Fake({"https://example.invalid/page": PAGE})
    code, report = run(manifest, fake)
    check("1: a match writes DIR/<path> and exits 0",
          code == 0 and (root / "supplier/pages/two-layer.html").read_bytes() == PAGE, (code, report))
    root2 = new_root(tmp, "checkonly")
    manifest2 = write_manifest(root2, [entry("page", "supplier/pages/two-layer.html")])
    code2, _ = run(manifest2, Fake({"https://example.invalid/page": PAGE}), "--check-only")
    check("2: --check-only with a match writes nothing and exits 0",
          code2 == 0 and not (root2 / "supplier/pages/two-layer.html").exists(), code2)


def test_changed(tmp):
    root = new_root(tmp, "changed")
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html")])
    profile_before = snapshot(root / "supplier/profiles/fixture-two-layer.yaml")
    manifest_before = snapshot(manifest)
    code, report = run(manifest, Fake({"https://example.invalid/page": OTHER}))
    row = rows_by_id(report)["page"]
    check("3: a changed hash writes nothing, reports changed, exits 1, and leaves the manifest and profile unchanged",
          code == 1 and row["hash_status"] == "changed" and not (root / "supplier/pages/two-layer.html").exists()
          and snapshot(manifest) == manifest_before
          and snapshot(root / "supplier/profiles/fixture-two-layer.yaml") == profile_before, (code, row))


def test_candidate(tmp):
    root = new_root(tmp, "candidate")
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html", sha256=None)])
    code, report = run(manifest, Fake({"https://example.invalid/page": PAGE}))
    row = rows_by_id(report)["page"]
    check("4: a null hash reports candidate, writes nothing, and exits 1",
          code == 1 and row["hash_status"] == "candidate" and not (root / "supplier/pages/two-layer.html").exists(), (code, row))


def test_fetch_failure(tmp):
    root = new_root(tmp, "fetchfail")
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html")])
    code, _ = run(manifest, Fake({"https://example.invalid/page": FS.FetchFailed("timeout")}))
    check("5: a fetch failure exits 3 and writes nothing",
          code == 3 and not (root / "supplier/pages/two-layer.html").exists(), code)


def test_magic_mismatch(tmp):
    root = new_root(tmp, "magic")
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html", body=b"not markup", magic="markup")])
    code, report = run(manifest, Fake({"https://example.invalid/page": b"not markup"}))
    row = rows_by_id(report)["page"]
    check("6: a magic mismatch exits 1 and writes nothing",
          code == 1 and row["magic_status"] == "mismatch" and not (root / "supplier/pages/two-layer.html").exists(), (code, row))


def test_link_destination(tmp):
    root = new_root(tmp, "linkdest")
    outside = tmp / "outside-dest.html"
    outside.write_bytes(b"outside before\n")
    (root / "supplier/pages/two-layer.html").symlink_to(outside)
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html")])
    fake = Fake({"https://example.invalid/page": PAGE})
    code, _ = run(manifest, fake)
    check("7: a link at the destination file is refused with exit 2, the target keeps its bytes, and nothing is fetched",
          code == 2 and outside.read_bytes() == b"outside before\n" and fake.calls == [], (code, fake.calls))


def test_link_parent(tmp):
    root = new_root(tmp, "linkparent")
    outside_dir = tmp / "outside-guidance"
    outside_dir.mkdir()
    (root / "supplier/guidance").symlink_to(outside_dir)
    manifest = write_manifest(root, [entry("guide", "supplier/guidance/x.html")])
    fake = Fake({"https://example.invalid/guide": PAGE})
    code, _ = run(manifest, fake)
    check("8: a link at a parent directory of DIR/<path> is refused with exit 2, and nothing is written outside the root",
          code == 2 and not any(outside_dir.iterdir()) and fake.calls == [], (code, fake.calls))


def test_bad_paths(tmp):
    root = new_root(tmp, "badpath")
    fake = Fake({"https://example.invalid/a": PAGE, "https://example.invalid/b": PAGE})
    m1 = write_manifest(root, [entry("a", "/tmp/absolute.html")])
    m2 = write_manifest(root, [entry("b", "supplier/../escape.html")])
    c1, _ = run(m1, fake)
    c2, _ = run(m2, fake)
    check("9: an absolute path and a .. path are refused with exit 2 before any fetch",
          c1 == 2 and c2 == 2 and fake.calls == [], (c1, c2, fake.calls))


def test_duplicate_destination(tmp):
    root = new_root(tmp, "dupdest")
    manifest = write_manifest(root, [entry("a", "supplier/pages/a.html"), entry("b", "supplier/pages/./a.html")])
    fake = Fake({"https://example.invalid/a": PAGE, "https://example.invalid/b": PAGE})
    code, _ = run(manifest, fake)
    check("10: a duplicate resolved destination is refused with exit 2 before any fetch",
          code == 2 and fake.calls == [], (code, fake.calls))


def test_unknown_entry(tmp):
    root = new_root(tmp, "unknown")
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html")])
    fake = Fake({"https://example.invalid/page": PAGE})
    code, _ = run(manifest, fake, "--entry", "missing")
    check("11: an unknown --entry ID is refused with exit 2 before any fetch", code == 2 and fake.calls == [], code)


def test_empty(tmp):
    root = new_root(tmp, "empty")
    manifest = write_manifest(root, [])
    code, _ = run(manifest, Fake())
    check("12: an empty manifest is refused with exit 2", code == 2, code)


def test_binding_location(tmp):
    root = new_root(tmp, "bindloc")
    fake = Fake({"https://example.invalid/a": PAGE, "https://example.invalid/b": PAGE})
    m1 = write_manifest(root, [entry("a", "supplier/pages/two-layer.html", profile_binding="supplier/pages/x.yaml")])
    m2 = write_manifest(root, [entry("b", "supplier/pages/two-layer.html", profile_binding="profiles/fixture-two-layer.yaml")])
    c1, _ = run(m1, fake)
    c2, _ = run(m2, fake)
    check("13: a profile_binding outside supplier/profiles is refused with exit 2", c1 == 2 and c2 == 2, (c1, c2))


def test_dest_mismatch(tmp):
    root = new_root(tmp, "dest")
    other = tmp / "elsewhere"
    other.mkdir()
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html")])
    code, _ = run(manifest, Fake({"https://example.invalid/page": PAGE}), "--dest", str(other))
    check("14: a --dest that differs from the manifest root is refused with exit 2 for a write",
          code == 2 and not any(other.iterdir()), code)


def test_skipped(tmp):
    root = new_root(tmp, "skipped")
    manifest = write_manifest(root, [
        entry("page", "supplier/pages/two-layer.html"),
        entry("local", "supplier/guidance/local.html", distribution_decision="exclude-local-evidence"),
    ])
    fake = Fake({"https://example.invalid/page": PAGE})
    code, report = run(manifest, fake)
    rows = rows_by_id(report)
    check("15: an exclude-local-evidence entry is skipped, is not fetched, and exits 0 when the others match",
          code == 0 and fake.calls == ["https://example.invalid/page"] and rows["local"]["hash_status"] is None
          and report["overall"] == "all match", (code, fake.calls, report.get("overall")))


def test_mixed_failure(tmp):
    root = new_root(tmp, "mixedfail")
    manifest = write_manifest(root, [entry("a", "supplier/pages/a.html"), entry("b", "supplier/pages/b.html")])
    fake = Fake({"https://example.invalid/a": FS.FetchFailed("timeout"), "https://example.invalid/b": OTHER})
    code, report = run(manifest, fake)
    rows = rows_by_id(report)
    check("16: one fetch failure and one changed entry exit 3 and report both outcomes",
          code == 3 and rows["a"]["fetch_error"] and rows["b"]["hash_status"] == "changed", (code, report))


def test_partial(tmp):
    root = new_root(tmp, "partial")
    manifest = write_manifest(root, [entry("a", "supplier/pages/a.html"),
                                     entry("b", "supplier/pages/b.html", body=OTHER)])
    code, report = run(manifest, Fake({"https://example.invalid/a": PAGE, "https://example.invalid/b": PAGE}))
    check("17: a changed entry in a multi-entry run reports partial, names the written entries, and exits 1",
          code == 1 and report["overall"] == "partial" and (root / "supplier/pages/a.html").is_file()
          and not (root / "supplier/pages/b.html").exists(), (code, report.get("overall")))


def test_duplicates_and_tokens(tmp):
    root = new_root(tmp, "dupid")
    fake = Fake({"https://example.invalid/a": PAGE, "https://example.invalid/b": PAGE})
    m1 = write_manifest(root, [entry("a", "supplier/pages/a.html"), entry("a", "supplier/pages/b.html")])
    m2 = write_manifest(root, [entry("a", "supplier/pages/a.html", magic="pdf")])
    c1, _ = run(m1, fake)
    c2, _ = run(m2, fake)
    check("18: a duplicate id, or a magic token pdf, exits 2 before any fetch", c1 == 2 and c2 == 2 and fake.calls == [], (c1, c2))


def test_license_ignored(tmp):
    root = new_root(tmp, "license")
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html", license_state="changed text")])
    code, _ = run(manifest, Fake({"https://example.invalid/page": PAGE}))
    check("19: a changed license_state does not change the outcome; the match writes and exits 0",
          code == 0 and (root / "supplier/pages/two-layer.html").is_file(), code)


def test_full_copy_match(tmp):
    root = new_root(tmp, "fullcopy")
    manifest = write_manifest(root, [entry("page", "supplier/guidance/full.html", distribution_decision="exclude-full-copy")])
    code, _ = run(manifest, Fake({"https://example.invalid/page": PAGE}))
    check("20: an exclude-full-copy entry that matches is written to DIR/<path> and exits 0",
          code == 0 and (root / "supplier/guidance/full.html").read_bytes() == PAGE, code)


def test_full_copy_candidate(tmp):
    root = new_root(tmp, "fullcand")
    manifest = write_manifest(root, [entry("page", "supplier/guidance/full.html", sha256=None)])
    code, _ = run(manifest, Fake({"https://example.invalid/page": PAGE}))
    check("21: an exclude-full-copy entry with a candidate hash is not written and exits 1",
          code == 1 and not (root / "supplier/guidance/full.html").exists(), code)


def test_valid_binding(tmp):
    root = new_root(tmp, "binding")
    profile_before = snapshot(root / "supplier/profiles/fixture-two-layer.yaml")
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html",
                                           profile_binding="supplier/profiles/fixture-two-layer.yaml")])
    code, _ = run(manifest, Fake({"https://example.invalid/page": PAGE}))
    check("22: a valid profile_binding matches, writes to DIR/<path>, exits 0, and leaves the profile unchanged",
          code == 0 and (root / "supplier/pages/two-layer.html").read_bytes() == PAGE
          and snapshot(root / "supplier/profiles/fixture-two-layer.yaml") == profile_before, code)


def test_checkonly_candidate(tmp):
    root = new_root(tmp, "checkcand")
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html", sha256=None)])
    code, _ = run(manifest, Fake({"https://example.invalid/page": PAGE}), "--check-only")
    check("23: --check-only with a candidate writes nothing and exits 1",
          code == 1 and not (root / "supplier/pages/two-layer.html").exists(), code)


def test_http_scheme(tmp):
    root = new_root(tmp, "http")
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html", url="http://example.invalid/page")])
    fake = Fake({"http://example.invalid/page": PAGE})
    code, _ = run(manifest, fake)
    check("24: an http URL is refused with exit 2 before any fetch", code == 2 and fake.calls == [], code)


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == "/redirect":
            self.send_response(302)
            self.send_header("Location", "/ok")
            self.end_headers()
        elif self.path == "/missing":
            self.send_response(404)
            self.end_headers()
        else:
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(PAGE)

    def log_message(self, *args):
        return


def local_server():
    server = http.server.HTTPServer(("127.0.0.1", 0), _Handler)
    threading.Thread(target=server.serve_forever, daemon=True).start()
    return server, f"http://127.0.0.1:{server.server_address[1]}"


def test_redirect(tmp):
    server, base = local_server()
    try:
        try:
            FS.default_fetch(base + "/redirect")
            redirect_failed = False
        except FS.FetchFailed:
            redirect_failed = True
        body = FS.default_fetch(base + "/ok")
    finally:
        server.shutdown()
    check("25: a 3xx response is a fetch failure, and a 200 response returns its bytes",
          redirect_failed and body == PAGE, (redirect_failed, body[:20]))


def test_bad_schema(tmp):
    root = new_root(tmp, "schema")
    fake = Fake({"https://example.invalid/page": PAGE})
    m1 = write_manifest(root, [entry("page", "supplier/pages/two-layer.html")], schema="other")
    m2 = write_manifest(root, [entry("page", "supplier/pages/two-layer.html")], version="1")
    c1, _ = run(m1, fake)
    c2, _ = run(m2, fake)
    check("26: a wrong schema or schema_version exits 2 before any fetch", c1 == 2 and c2 == 2 and fake.calls == [], (c1, c2))


def test_keys(tmp):
    root = new_root(tmp, "keys")
    fake = Fake({"https://example.invalid/page": PAGE})
    missing = entry("page", "supplier/pages/two-layer.html")
    missing.pop("retrieved")
    unknown = entry("page", "supplier/pages/two-layer.html", title="not allowed")
    c1, _ = run(write_manifest(root, [missing]), fake)
    c2, _ = run(write_manifest(root, [unknown]), fake)
    check("27: a missing required key or an unknown key exits 2 before any fetch", c1 == 2 and c2 == 2 and fake.calls == [], (c1, c2))


def test_types(tmp):
    root = new_root(tmp, "types")
    fake = Fake({"https://example.invalid/page": PAGE})
    code, _ = run(write_manifest(root, [entry("page", "supplier/pages/two-layer.html", sha256="ABC")]), fake)
    check("28: an invalid type (a short sha256) exits 2 before any fetch", code == 2 and fake.calls == [], code)


def test_pre_replace_failure(tmp):
    root = new_root(tmp, "prereplace")
    target = root / "supplier/pages/two-layer.html"
    target.write_bytes(b"<old bytes>\n")
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html")])
    before = files_under(root)
    original = PIO.atomic_write

    def fail_before(project, path, data, **kwargs):
        raise OSError("fixture failure before the replace")

    PIO.atomic_write = fail_before
    try:
        code, report = run(manifest, Fake({"https://example.invalid/page": PAGE}))
    finally:
        PIO.atomic_write = original
    check("29: a pre-replace write failure keeps the old bytes, leaves no new file, and exits 3",
          code == 3 and target.read_bytes() == b"<old bytes>\n" and files_under(root) == before, (code, files_under(root)))


def test_match_and_fetch_failure(tmp):
    root = new_root(tmp, "matchfail")
    manifest = write_manifest(root, [entry("a", "supplier/pages/a.html"), entry("b", "supplier/pages/b.html")])
    fake = Fake({"https://example.invalid/a": PAGE, "https://example.invalid/b": FS.FetchFailed("timeout")})
    code, report = run(manifest, fake)
    check("30: a match and a fetch failure write the match, report partial, and exit 3",
          code == 3 and (root / "supplier/pages/a.html").is_file() and report["overall"] == "partial", (code, report.get("overall")))


def test_all_skipped(tmp):
    root = new_root(tmp, "allskipped")
    manifest = write_manifest(root, [entry("local", "supplier/guidance/local.html", distribution_decision="exclude-local-evidence")])
    fake = Fake()
    code, report = run(manifest, fake)
    check("31: a run where every entry is skipped exits 0 and reports no entry fetched",
          code == 0 and report["overall"] == "no entry fetched" and fake.calls == [], (code, report.get("overall")))


def test_non_2xx(tmp):
    server, base = local_server()
    try:
        try:
            FS.default_fetch(base + "/missing")
            failed = False
        except FS.FetchFailed:
            failed = True
    finally:
        server.shutdown()
    root = new_root(tmp, "non2xx")
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html")])
    code, _ = run(manifest, Fake({"https://example.invalid/page": FS.FetchFailed("HTTP 404")}))
    check("32: a non-2xx response is a fetch failure: exit 3 and nothing written",
          failed and code == 3 and not (root / "supplier/pages/two-layer.html").exists(), (failed, code))


def test_post_replace(tmp):
    root = new_root(tmp, "postreplace")
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html")])
    original = PIO.atomic_write

    def write_then_fail(project, path, data, **kwargs):
        original(project, path, data)
        raise PIO.PostReplaceError("fixture durability failure after the replace")

    PIO.atomic_write = write_then_fail
    try:
        code, report = run(manifest, Fake({"https://example.invalid/page": PAGE}))
    finally:
        PIO.atomic_write = original
    check("33: a post-replace failure is a write error with exit 3, the new bytes stay, and no rollback is claimed",
          code == 3 and report["overall"] == "write error" and (root / "supplier/pages/two-layer.html").read_bytes() == PAGE,
          (code, report.get("overall")))


def test_null_magic(tmp):
    root = new_root(tmp, "nullmagic")
    manifest = write_manifest(root, [entry("page", "supplier/pages/plain.html", body=PLAIN, magic=None)])
    code, report = run(manifest, Fake({"https://example.invalid/page": PLAIN}))
    row = rows_by_id(report)["page"]
    check("34: magic null writes a matching entry with magic status not-tested",
          code == 0 and row["magic_status"] == "not-tested" and (root / "supplier/pages/plain.html").is_file(), (code, row))


def test_checkonly_other_dest(tmp):
    root = new_root(tmp, "checkdest")
    other = tmp / "does-not-exist"
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html")])
    code, _ = run(manifest, Fake({"https://example.invalid/page": PAGE}), "--check-only", "--dest", str(other))
    check("35: --check-only with a differing --dest reads nothing there, writes nothing, and exits by the outcomes",
          code == 0 and not other.exists(), (code, other.exists()))


def test_bad_date(tmp):
    root = new_root(tmp, "date")
    code, _ = run(write_manifest(root, [entry("page", "supplier/pages/two-layer.html", retrieved="2026-02-30")]),
                  Fake({"https://example.invalid/page": PAGE}))
    check("36: a retrieved value that is not a real date exits 2", code == 2, code)


def test_binding_dotdot(tmp):
    root = new_root(tmp, "dotdot")
    code, _ = run(write_manifest(root, [entry("page", "supplier/pages/two-layer.html",
                                              profile_binding="supplier/profiles/../x.yaml")]),
                  Fake({"https://example.invalid/page": PAGE}))
    check("37: a profile_binding with .. exits 2", code == 2, code)


def test_binding_path(tmp):
    root = new_root(tmp, "bindpath")
    fake = Fake({"https://example.invalid/page": PAGE})
    code, _ = run(write_manifest(root, [entry("page", "supplier/guidance/x.html",
                                              profile_binding="supplier/profiles/fixture-two-layer.yaml")]), fake)
    check("38: a bound entry whose path is not under supplier/pages exits 2 before any fetch", code == 2 and fake.calls == [], code)


def test_binding_hash(tmp):
    root = new_root(tmp, "bindhash")
    fake = Fake({"https://example.invalid/page": PAGE})
    code, _ = run(write_manifest(root, [entry("page", "supplier/pages/two-layer.html", sha256="0" * 64,
                                              profile_binding="supplier/profiles/fixture-two-layer.yaml")]), fake)
    check("39: a bound entry whose sha256 differs from the profile evidence exits 2 before any fetch",
          code == 2 and fake.calls == [], code)


def test_changed_and_magic(tmp):
    root = new_root(tmp, "changedmagic")
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html", body=PAGE, magic="markup")])
    code, report = run(manifest, Fake({"https://example.invalid/page": b"not markup at all"}))
    row = rows_by_id(report)["page"]
    check("40: a changed hash and an invalid magic report both statuses, write nothing, and exit 1",
          code == 1 and row["hash_status"] == "changed" and row["magic_status"] == "mismatch"
          and not (root / "supplier/pages/two-layer.html").exists(), (code, row))


def test_candidate_and_magic(tmp):
    root = new_root(tmp, "candmagic")
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html", sha256=None, magic="markup")])
    code, report = run(manifest, Fake({"https://example.invalid/page": b"not markup at all"}))
    row = rows_by_id(report)["page"]
    check("41: a candidate hash and an invalid magic report both statuses, write nothing, and exit 1",
          code == 1 and row["hash_status"] == "candidate" and row["magic_status"] == "mismatch"
          and not (root / "supplier/pages/two-layer.html").exists(), (code, row))


def test_ole2(tmp):
    root = new_root(tmp, "ole")
    manifest = write_manifest(root, [entry("doc", "supplier/guidance/doc.xls", body=OLE, magic="OLE2")])
    code, report = run(manifest, Fake({"https://example.invalid/doc": OLE}))
    row = rows_by_id(report)["doc"]
    check("42: the OLE2 token matches an OLE compound-file header, is ok, and is written",
          code == 0 and row["magic_status"] == "ok" and (root / "supplier/guidance/doc.xls").is_file(), (code, row))


def test_binding_nested(tmp):
    root = new_root(tmp, "nested")
    code, _ = run(write_manifest(root, [entry("page", "supplier/pages/two-layer.html",
                                              profile_binding="supplier/profiles/sub/fixture-two-layer.yaml")]),
                  Fake({"https://example.invalid/page": PAGE}))
    check("43: a profile_binding that is not a direct child of supplier/profiles exits 2", code == 2, code)


def test_release_profiles(tmp):
    root = new_root(tmp, "release")
    entries = []
    for name, key in (("oshpark-single-layer", "single-layer"), ("oshpark-two-layer", "two-layer"),
                      ("oshpark-two-layer-hhdc", "two-layer-hhdc"), ("oshpark-four-layer", "four-layer"),
                      ("oshpark-six-layer", "six-layer")):
        shutil.copy2(PROFILES / f"{name}.yaml", root / "supplier/profiles" / f"{name}.yaml")
        digest = yaml.safe_load((PROFILES / f"{name}.yaml").read_text())["extensions"]["evidence_pages"][key]["sha256"]
        entries.append(entry(key, f"supplier/pages/{key}.html", body=b"<fixture>", sha256=digest,
                             profile_binding=f"supplier/profiles/{name}.yaml"))
    code, report = run(write_manifest(root, entries), Fake({f"https://example.invalid/{e['id']}": b"<fixture>" for e in entries}), "--check-only")
    rows = rows_by_id(report)
    check("44: the five release profile entries pass validation offline; each page key resolves in its profile",
          code == 1 and len(rows) == 5 and all(row["hash_status"] == "changed" for row in rows.values()), (code, report.get("overall")))


def test_profile_symlink_outside(tmp):
    root = new_root(tmp, "profileout")
    outside = tmp / "outside-profile.yaml"
    outside.write_text(profile_text("two-layer", sha(PAGE)))
    before = outside.read_bytes()
    (root / "supplier/profiles/link.yaml").symlink_to(outside)
    fake = Fake({"https://example.invalid/page": PAGE})
    code, report = run(write_manifest(root, [entry("page", "supplier/pages/two-layer.html",
                                                   profile_binding="supplier/profiles/link.yaml")]), fake)
    check("45: a profile link to a file outside the root is refused with exit 2 before any read or fetch",
          code == 2 and fake.calls == [] and outside.read_bytes() == before and "symbolic link" in str(report),
          (code, report))


def test_profile_pages_link(tmp):
    root = new_root(tmp, "profilepages")
    page = root / "supplier/pages/two-layer.html"
    page.write_bytes(PAGE)
    before = page.read_bytes()
    (root / "supplier/profiles/inside.yaml").symlink_to(page)
    fake = Fake({"https://example.invalid/page": PAGE})
    code, report = run(write_manifest(root, [entry("page", "supplier/pages/two-layer.html",
                                                   profile_binding="supplier/profiles/inside.yaml")]), fake)
    check("47: a profile link that resolves into supplier/pages is refused with exit 2 before any read or fetch",
          code == 2 and fake.calls == [] and page.read_bytes() == before and "symbolic link" in str(report), (code, report))


def test_binding_suffix(tmp):
    root = new_root(tmp, "suffix")
    fake = Fake({"https://example.invalid/page": PAGE})
    code, _ = run(write_manifest(root, [entry("page", "supplier/pages/two-layer.pdf",
                                              profile_binding="supplier/profiles/fixture-two-layer.yaml")]), fake)
    check("46: a bound page whose path does not end in .html exits 2 before any fetch",
          code == 2 and fake.calls == [], code)


def test_profiles_dir_link(tmp):
    root = new_root(tmp, "dirlink")
    shutil.rmtree(root / "supplier/profiles")
    (root / "supplier/profiles").symlink_to(root / "supplier/pages")
    fake = Fake({"https://example.invalid/page": PAGE})
    code, report = run(write_manifest(root, [entry("page", "supplier/pages/two-layer.html",
                                                   profile_binding="supplier/profiles/fixture-two-layer.yaml")]), fake)
    check("48: a directory link from supplier/profiles into supplier/pages is refused with exit 2 before any read or fetch",
          code == 2 and fake.calls == [] and "symbolic link" in str(report), (code, report))


def alias_case(tmp, label, dest, *, check_only=False, hard_link_from=None):
    """Run one entry whose destination names a protected input. Return the exit, the fetch calls and the bytes."""
    root = new_root(tmp, label)
    manifest = write_manifest(root, [entry("page", dest)])
    if hard_link_from is not None:
        target = root / dest
        target.parent.mkdir(parents=True, exist_ok=True)
        os.link(root / hard_link_from, target)
    before = {name: snapshot(root / name) for name in ["sources.yaml", "supplier/profiles/fixture-two-layer.yaml"]}
    fake = Fake({"https://example.invalid/page": PAGE})
    extra = ["--check-only"] if check_only else []
    code, _ = run(manifest, fake, *extra)
    after = {name: snapshot(root / name) for name in before}
    return code, fake.calls, before == after


def test_alias_manifest(tmp):
    code, calls, same = alias_case(tmp, "aliasmanifest", "./sources.yaml")
    check("49: a destination that is the manifest, written as ./sources.yaml, exits 2 before any fetch and keeps all inputs",
          code == 2 and calls == [] and same, (code, calls, same))


def test_alias_manifest_normalized(tmp):
    code, calls, same = alias_case(tmp, "aliasnorm", "supplier/pages/../../sources.yaml")
    check("50: a normalized manifest alias with .. exits 2 before any fetch and keeps all inputs",
          code == 2 and calls == [] and same, (code, calls, same))


def test_alias_profile(tmp):
    code, calls, same = alias_case(tmp, "aliasprofile", "supplier/profiles/./fixture-two-layer.yaml")
    check("51: a destination that is a bound profile, written with ./, exits 2 before any fetch and keeps the profile",
          code == 2 and calls == [] and same, (code, calls, same))


def test_alias_unbound_profile(tmp):
    code, calls, same = alias_case(tmp, "aliasunbound", "supplier/profiles/other.yaml")
    check("52: a destination under supplier/profiles that no entry binds exits 2 before any fetch",
          code == 2 and calls == [] and same, (code, calls, same))


def test_alias_hard_link_manifest(tmp):
    code, calls, same = alias_case(tmp, "hardmanifest", "supplier/pages/two-layer.html",
                                   hard_link_from="sources.yaml")
    check("53: a destination that is a hard link to the manifest exits 2 before any fetch and keeps all inputs",
          code == 2 and calls == [] and same, (code, calls, same))


def test_alias_hard_link_profile(tmp):
    code, calls, same = alias_case(tmp, "hardprofile", "supplier/pages/two-layer.html",
                                   hard_link_from="supplier/profiles/fixture-two-layer.yaml")
    check("54: a destination that is a hard link to a profile exits 2 before any fetch and keeps all inputs",
          code == 2 and calls == [] and same, (code, calls, same))


def test_alias_check_only(tmp):
    code, calls, same = alias_case(tmp, "aliascheck", "./sources.yaml", check_only=True)
    check("55: --check-only refuses a manifest alias with exit 2 before any fetch",
          code == 2 and calls == [] and same, (code, calls, same))


def test_alias_normal_guidance(tmp):
    root = new_root(tmp, "aliasnormal")
    manifest = write_manifest(root, [entry("guide", "supplier/guidance/full.html")])
    fake = Fake({"https://example.invalid/guide": PAGE})
    code, _ = run(manifest, fake)
    check("56: a normal guidance destination is not refused and is written with exit 0",
          code == 0 and fake.calls == ["https://example.invalid/guide"]
          and (root / "supplier/guidance/full.html").read_bytes() == PAGE, code)


def test_text_rule(tmp):
    text = FS.visible_text(LAYOUT_A)
    check("57: the visible text keeps the title and paragraph text, drops tags, comments, script, style and"
          " noscript text and attribute values, decodes entities, and gives adjacent tags the same hash",
          text == "Fixture Trace 6 mil & space Drill 10 mil" and "a1" not in text and "red" not in text
          and "build" not in text and "Enable scripts" not in text
          and FS.visible_text(LAYOUT_B) == "Fixture Trace 6 mil & space Drill 10 mil"
          and FS.text_sha256(b"<p>A</p><p>B</p>") == FS.text_sha256(b"<p>A</p>\n<p>B</p>")
          and FS.visible_text(b"<p>A<br>B</p>") == "A B", text)


def test_text_rule_decl_pi_cdata_bom(tmp):
    check("72: a doctype, a processing instruction and a CDATA section each give one space, and one leading"
          " U+FEFF is removed",
          FS.visible_text(b"A<!DOCTYPE x>B") == "A B" and FS.visible_text(b"A<?xml x?>B") == "A B"
          and FS.visible_text(b"A<![CDATA[x]]>B") == "A B"
          and FS.visible_text(b"\xef\xbb\xbfA") == "A"
          and FS.visible_text(b"\xef\xbb\xbf<p>A</p>") == "A"
          and FS.visible_text(b"\xef\xbb\xbf\xef\xbb\xbfA") == "\ufeffA",
          (FS.visible_text(b"A<!DOCTYPE x>B"), FS.visible_text(b"A<?xml x?>B"),
           FS.visible_text(b"A<![CDATA[x]]>B"), FS.visible_text(b"\xef\xbb\xbfA")))


def test_text_hash_value(tmp):
    check("58: the text hash is the SHA-256 of the UTF-8 visible text, layout bytes share one text hash,"
          " and a text change gives a different hash",
          FS.text_sha256(LAYOUT_A) == sha(FS.visible_text(LAYOUT_A).encode("utf-8"))
          and FS.text_sha256(LAYOUT_A) == FS.text_sha256(LAYOUT_B)
          and FS.text_sha256(LAYOUT_A) != FS.text_sha256(RULE_CHANGE)
          and sha(LAYOUT_A) != sha(LAYOUT_B), FS.text_sha256(LAYOUT_A))


def test_text_hash_not_utf8(tmp):
    check("59: bytes that are not UTF-8 give no text hash", FS.text_sha256(NOT_UTF8) is None,
          FS.text_sha256(NOT_UTF8))


def test_text_key_type(tmp):
    root = new_root(tmp, "textkeytype")
    fake = Fake({"https://example.invalid/page": PAGE})
    cases = [("uppercase", "A" * 64), ("short", "a" * 63), ("null", None), ("integer", 1)]
    results = []
    for label, value in cases:
        code, report = run(write_manifest(
            root, [entry("page", "supplier/pages/two-layer.html", text_sha256=value)]), fake)
        results.append(code == 2 and fake.calls == []
                       and "64 lowercase hexadecimal characters" in str(report))
        fake.calls.clear()
    check("60: a text_sha256 that is uppercase, short, null, or not a string exits 2 before any fetch", all(results),
          results)


def test_text_key_magic(tmp):
    root = new_root(tmp, "textkeymagic")
    fake = Fake({"https://example.invalid/page": PAGE})
    code, report = run(write_manifest(root, [entry("page", "supplier/pages/plain.html", body=PLAIN,
                                                   magic=None, content_type="text/plain",
                                                   text_sha256="a" * 64)]), fake)
    check("61: text_sha256 on an entry without the markup magic exits 2 before any fetch and names markup",
          code == 2 and fake.calls == [] and "markup" in str(report), (code, report))


def test_text_key_candidate(tmp):
    root = new_root(tmp, "textkeycandidate")
    fake = Fake({"https://example.invalid/page": PAGE})
    code, report = run(write_manifest(root, [entry("page", "supplier/pages/two-layer.html", sha256=None,
                                                   text_sha256="a" * 64)]), fake)
    check("62: text_sha256 on an entry without a sha256 exits 2 before any fetch and names the sha256 rule",
          code == 2 and fake.calls == [] and "a sha256 value" in str(report), (code, report))


def layout_entry(tmp, label, **over):
    root = layout_root(tmp, label)
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html", body=LAYOUT_A,
                                           profile_binding="supplier/profiles/fixture-two-layer.yaml", **over)])
    return root, manifest


def test_layout_write_mode(tmp):
    root, manifest = layout_entry(tmp, "layoutwrite", text_sha256=text_sha(LAYOUT_A))
    before = {name: snapshot(root / name) for name in
              ["sources.yaml", "supplier/profiles/fixture-two-layer.yaml"]}
    fake = Fake({"https://example.invalid/page": LAYOUT_B})
    code, report = run(manifest, fake)
    row = rows_by_id(report)["page"]
    after = {name: snapshot(root / name) for name in before}
    check("63: a layout change in write mode exits 0, writes nothing, and leaves the manifest and profile unchanged",
          code == 0 and row["hash_status"] == "layout" and row["text_status"] == "match"
          and row["written"] is False and report["overall"] == "none written"
          and not (root / "supplier/pages/two-layer.html").exists() and before == after, (code, row, report))


def test_layout_check_only(tmp):
    _, manifest = layout_entry(tmp, "layoutcheck", text_sha256=text_sha(LAYOUT_A))
    code, report = run(manifest, Fake({"https://example.invalid/page": LAYOUT_B}), "--check-only")
    row = rows_by_id(report)["page"]
    check("64: a layout change in check-only mode exits 0 with overall match or layout and both observed hashes",
          code == 0 and report["overall"] == "match or layout" and row["hash_status"] == "layout"
          and row["observed_text_sha256"] == text_sha(LAYOUT_B)
          and row["observed_sha256"] == sha(LAYOUT_B), (code, row, report))


def test_text_changed(tmp):
    root, manifest = layout_entry(tmp, "textchanged", text_sha256=text_sha(LAYOUT_A))
    code, report = run(manifest, Fake({"https://example.invalid/page": RULE_CHANGE}))
    row = rows_by_id(report)["page"]
    check("65: a text change exits 1 with status changed and writes nothing",
          code == 1 and row["hash_status"] == "changed" and row["text_status"] == "changed"
          and row["written"] is False and not (root / "supplier/pages/two-layer.html").exists(), (code, row))


def test_text_mismatch_on_byte_match(tmp):
    root = new_root(tmp, "textmismatch")
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html", body=LAYOUT_A,
                                           text_sha256=text_sha(RULE_CHANGE))])
    code, report = run(manifest, Fake({"https://example.invalid/page": LAYOUT_A}))
    row = rows_by_id(report)["page"]
    check("66: a byte match with a text mismatch exits 1, writes the page, and gives overall partial",
          code == 1 and row["hash_status"] == "match" and row["text_status"] == "changed"
          and row["written"] is True
          and (root / "supplier/pages/two-layer.html").read_bytes() == LAYOUT_A
          and report["overall"] == "partial", (code, row, report))


def test_no_text_key_as_before(tmp):
    root = new_root(tmp, "notextkey")
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html", body=LAYOUT_A)])
    code, report = run(manifest, Fake({"https://example.invalid/page": LAYOUT_B}))
    row = rows_by_id(report)["page"]
    check("67: an entry without text_sha256 keeps the old behavior and still reports the observed text hash",
          code == 1 and row["hash_status"] == "changed" and row["text_status"] is None
          and row["observed_text_sha256"] == text_sha(LAYOUT_B), (code, row))


def test_layout_and_magic(tmp):
    root = new_root(tmp, "layoutmagic")
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html", body=b"<p>A</p>",
                                           text_sha256=text_sha(b"<p>A</p>"))])
    code, report = run(manifest, Fake({"https://example.invalid/page": b"A"}))
    row = rows_by_id(report)["page"]
    check("68: a layout change with a magic mismatch exits 1 and writes nothing",
          code == 1 and row["hash_status"] == "layout" and row["magic_status"] == "mismatch"
          and row["written"] is False and not (root / "supplier/pages/two-layer.html").exists(), (code, row))


def test_text_not_utf8_recorded(tmp):
    root = new_root(tmp, "notutf8recorded")
    manifest = write_manifest(root, [entry("page", "supplier/pages/two-layer.html", body=LAYOUT_A,
                                           text_sha256=text_sha(LAYOUT_A))])
    code, report = run(manifest, Fake({"https://example.invalid/page": NOT_UTF8}))
    row = rows_by_id(report)["page"]
    check("69: bytes that are not UTF-8 exit 1 with status changed and no observed text hash",
          code == 1 and row["hash_status"] == "changed" and row["text_status"] == "changed"
          and row["observed_text_sha256"] is None, (code, row))


def test_text_plain_entry(tmp):
    root = new_root(tmp, "textplain")
    manifest = write_manifest(root, [entry("page", "supplier/pages/plain.html", body=PLAIN,
                                           magic=None, content_type="text/plain")])
    code, report = run(manifest, Fake({"https://example.invalid/page": PLAIN}))
    row = rows_by_id(report)["page"]
    check("70: a plain-text entry with a byte match exits 0 and reports no text hash",
          code == 0 and row["observed_text_sha256"] is None and row["text_status"] is None, (code, row))


def test_fixture_drops_text_hash(tmp):
    source = tmp / "fixture-source" / "pcb-fab-package"
    shutil.copytree(SKILL, source, ignore=shutil.ignore_patterns("pages", "__pycache__"))
    source_manifest = source / "sources.yaml"
    data = yaml.safe_load(source_manifest.read_text())
    for row in data["sources"]:
        if row["distribution_decision"] == "exclude-full-copy":
            row["text_sha256"] = "0" * 64
    source_manifest.write_text(yaml.safe_dump(data, sort_keys=False))
    skill = fab_fixture.fixture_skill(source)
    out = yaml.safe_load((skill / "sources.yaml").read_text())
    table = {row["url"]: (skill / row["path"]).read_bytes() for row in out["sources"]}
    code, report = FS.main(["--manifest", str(skill / "sources.yaml"), "--check-only"], fetch=Fake(table))
    check("71: the fixture manifest has no text_sha256 and its pages pass check-only",
          all("text_sha256" not in row for row in out["sources"]) and code == 0, (code, report))


def main():
    tmp = Path(tempfile.mkdtemp(prefix="source-retrieval-"))
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
