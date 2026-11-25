# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Release packaging inventory and exclusion checks for supplier evidence.

  uv run tests/test_release_packaging.py            # all tests
  uv run tests/test_release_packaging.py real       # only tests with 'real' in their name

The checks read repository bytes and hashes. They call no provider and contact no supplier.
Fixtures are project-authored. No test fixture holds supplier bytes (D-7).

Limits:
- Zero fetch scripts exist. The packaging test is provisional. A final standalone release cannot
  pass without the necessary setup path (lead decision, 2026-11-15).
- The manifests name URLs and expected hashes. They do not approve anything. The supplier-profile
  content and evidence hashes and the source-review record remain the binding authority.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests" / "eval"))

import packaging as P  # noqa: E402
from common import sha256_bytes  # noqa: E402

PCB_FAB = ROOT / "skills" / "pcb-fab-package"


def tracked_files() -> list[str]:
    out = subprocess.run(["git", "ls-files"], cwd=ROOT, capture_output=True, text=True, check=True)
    return [line for line in out.stdout.splitlines() if line]


def real_distribution() -> dict:
    return P.merged_distribution(ROOT, P.load_yaml(ROOT / "tests" / "eval" / "distribution.yaml"))


def write(path: Path, data: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)


def codes(findings: list[dict]) -> set[str]:
    return {f["code"] for f in findings}


def expect_no_findings(findings: list[dict], label: str) -> None:
    if findings:
        raise AssertionError(f"{label}: {json.dumps(findings, indent=1)}")


# ---------------------------------------------------------------- real repository


def test_real_manifest_fields_and_hashes(tmp: Path):
    """D-2, D-5, D-8 on the committed manifests. Every hash matches the bytes on disk."""
    findings = P.check_entries(ROOT, PCB_FAB, P.load_yaml(PCB_FAB / "sources.yaml"),
                               "skills/pcb-fab-package/sources.yaml")
    findings += P.check_entries(ROOT, ROOT, P.load_yaml(ROOT / "tests/eval/distribution.yaml"),
                                "tests/eval/distribution.yaml")
    expect_no_findings(findings, "manifest fields, hashes and magic")


def test_real_coverage_every_supplier_source_has_an_entry(tmp: Path):
    """The test compares seventeen supplier sources with the manifest."""
    dist = real_distribution()
    entry_paths = {entry["path"] for entry in dist["sources"]}
    sources = P.supplier_sources(ROOT, dist)
    if len(sources) != 17:
        raise AssertionError(f"expected 17 stored supplier sources, found {len(sources)}: {sources}")
    expect_no_findings(P.check_coverage(ROOT, dist, entry_paths), "coverage")


def test_real_distribution_excludes_supplier_copies(tmp: Path):
    """The distributed set holds no full copy, no local evidence and no unlisted supplier file."""
    dist = real_distribution()
    distributed, excluded = P.build_distribution(tracked_files(), dist)
    expect_no_findings(P.check_distribution(distributed, dist, root=ROOT), "distributed set")
    entry_paths = {entry["path"] for entry in dist["sources"]}
    missing = sorted(entry_paths - set(excluded))
    if missing:
        raise AssertionError(f"these supplier entries are not excluded: {missing}")


def test_real_headers_are_excluded_as_local_evidence(tmp: Path):
    """D-4 with the regression rule. Every tracked .headers file is out of the distribution."""
    dist = real_distribution()
    _, excluded = P.build_distribution(tracked_files(), dist)
    headers = [p for p in tracked_files() if p.endswith(".headers")]
    if len(headers) != 8:
        raise AssertionError(f"expected 8 header files, found {len(headers)}")
    outside = [p for p in headers if p not in excluded]
    if outside:
        raise AssertionError(f"header files still distributed: {outside}")


def test_real_fixtures_hold_no_supplier_bytes(tmp: Path):
    """D-7 on the committed fixtures and the test tree."""
    dist = real_distribution()
    hashes = {entry["sha256"] for entry in dist["sources"]}
    fixtures = ["tests/fixtures/pcb-design", "tests/fixtures/pcb-fab-package", "tests/eval"]
    expect_no_findings(P.check_fixtures(ROOT, fixtures, hashes), "fixture bytes")


def test_real_allowlisted_profiles_are_project_authored_data(tmp: Path):
    """The profile YAML files are allowed. They hold URLs and hashes, not supplier copies."""
    dist = real_distribution()
    profiles = [p for p in tracked_files() if "/supplier/profiles/" in f"/{p}"]
    expect_no_findings(P.check_distribution(profiles, dist), "profiles")


def test_real_regression_without_exclusions_is_detected(tmp: Path):
    """If the packager forgets the exclusions, the checks find each defect."""
    dist = real_distribution()
    found = codes(P.check_distribution(tracked_files(), dist))
    for needed in ("D-3", "D-4", "R-regression"):
        if needed not in found:
            raise AssertionError(f"regression check did not find {needed}. Found {sorted(found)}")


def test_real_no_acknowledgment_gate(tmp: Path):
    """The lead rejected a mandatory license acknowledgment. The manifests must not require one."""
    for name in ("skills/pcb-fab-package/sources.yaml", "tests/eval/distribution.yaml"):
        text = (ROOT / name).read_text(encoding="utf-8").lower()
        if "acknowledg" in text:
            raise AssertionError(f"{name} mentions an acknowledgment field")


def test_real_fetch_scripts_are_provisional(tmp: Path):
    """Informational. Zero fetch scripts is provisional. Report the count, do not fail on it."""
    fetch = sorted(p.relative_to(ROOT).as_posix() for p in ROOT.glob("skills/*/supplier/fetch_*.py"))
    print(f"     fetch scripts: {len(fetch)} (provisional packaging test)")


# ---------------------------------------------------------------- project-authored fixtures


def _fixture_skill(root: Path, page: bytes, sha: str | None = None, extra: dict | None = None) -> Path:
    skill = root / "skills" / "demo"
    write(skill / "supplier" / "pages" / "page.html", page)
    entry = {
        "id": "demo-page", "path": "supplier/pages/page.html", "url": "https://example.test/page/",
        "retrieved": "2026-11-15", "sha256": sha or sha256_bytes(page), "content_type": "text/html",
        "magic": "markup", "license_state": "informational fixture", "distribution_decision": "exclude-full-copy",
        "profile_binding": None,
    }
    entry.update(extra or {})
    # JSON scalars are valid YAML. The manifest is written as a list with one entry.
    lines = ["schema: cad-skills/sources", "schema_version: 1", "sources:",
             f"  - id: {json.dumps(entry['id'])}"]
    lines += [f"    {key}: {json.dumps(value)}" for key, value in entry.items() if key != "id"]
    write(skill / "sources.yaml", ("\n".join(lines) + "\n").encode("utf-8"))
    return skill


def test_fixture_entry_passes_when_bytes_match(tmp: Path):
    skill = _fixture_skill(tmp, b"<html><body>project fixture page</body></html>")
    manifest = P.load_yaml(skill / "sources.yaml")
    expect_no_findings(P.check_entries(tmp, skill, manifest, "demo/sources.yaml"), "matching fixture")


def test_fixture_changed_bytes_need_a_new_review(tmp: Path):
    """D-5. A changed page does not pass against the old hash."""
    skill = _fixture_skill(tmp, b"<html><body>original</body></html>")
    write(skill / "supplier" / "pages" / "page.html", b"<html><body>changed</body></html>")
    found = P.check_entries(tmp, skill, P.load_yaml(skill / "sources.yaml"), "demo/sources.yaml")
    if "D-5" not in codes(found):
        raise AssertionError(f"changed bytes were not reported: {found}")


def test_fixture_profile_binding_must_agree(tmp: Path):
    """D-5. The profile's evidence hash is the binding authority. A different value is a finding."""
    page = b"<html><body>bound page</body></html>"
    skill = _fixture_skill(tmp, page, extra={"profile_binding": "profile.yaml"})
    write(skill / "profile.yaml", b'{"evidence_sha256": "' + b"0" * 64 + b'"}\n')
    found = P.check_entries(tmp, skill, P.load_yaml(skill / "sources.yaml"), "demo/sources.yaml")
    if "D-5" not in codes(found):
        raise AssertionError(f"profile binding mismatch was not reported: {found}")


def test_fixture_magic_must_match_the_content_type(tmp: Path):
    """D-8. Magic identifies the format only. A PDF entry with other bytes is a finding."""
    skill = tmp / "evidence"
    write(skill / "xy.pdf", b"not a pdf")
    entry = {"id": "x", "path": "xy.pdf", "url": None, "url_state": "fixture", "retrieved": "2026-11-15",
             "sha256": sha256_bytes(b"not a pdf"), "content_type": "application/pdf", "magic": "%PDF",
             "license_state": "fixture", "distribution_decision": "exclude-full-copy"}
    found = P.check_entries(tmp, skill, {"sources": [entry]}, "evidence/sources")
    if "D-8" not in codes(found):
        raise AssertionError(f"magic mismatch was not reported: {found}")


def test_fixture_missing_required_field(tmp: Path):
    """D-2. An entry without license_state is a finding, and nothing else is needed to pass it."""
    skill = _fixture_skill(tmp, b"<html>fixture</html>")
    manifest = P.load_yaml(skill / "sources.yaml")
    del manifest["sources"][0]["license_state"]
    found = P.check_entries(tmp, skill, manifest, "demo/sources.yaml")
    if "D-2" not in codes(found):
        raise AssertionError(f"missing field was not reported: {found}")


def test_fixture_unlisted_supplier_page_is_a_coverage_finding(tmp: Path):
    """D-1. A page on disk with no manifest entry is a finding."""
    _fixture_skill(tmp, b"<html>listed</html>")
    write(tmp / "skills" / "demo" / "supplier" / "pages" / "extra.html", b"<html>unlisted</html>")
    dist = {"allowlist": [], "sources": []}
    found = P.check_coverage(tmp, dist, {"skills/demo/supplier/pages/page.html"})
    if [f["file"] for f in found] != ["skills/demo/supplier/pages/extra.html"]:
        raise AssertionError(f"unexpected coverage findings: {found}")


def test_fixture_supplier_bytes_in_a_fixture_are_a_finding(tmp: Path):
    """D-7. A test fixture that copies a supplier source's bytes is a finding."""
    page = b"<html>a supplier source</html>"
    write(tmp / "tests" / "fx" / "copy.html", page)
    found = P.check_fixtures(tmp, ["tests/fx"], {sha256_bytes(page)})
    if codes(found) != {"D-7"}:
        raise AssertionError(f"fixture copy was not reported: {found}")


def test_fixture_distribution_excludes_pages_and_local_evidence(tmp: Path):
    """A fixture distribution: a page and its headers are excluded, a source file stays."""
    dist = {
        "sources": [
            {"path": "skills/demo/supplier/pages/page.html", "distribution_decision": "exclude-full-copy",
             "sha256": "a" * 64},
            {"path": "skills/demo/supplier/pages/page.headers", "distribution_decision": "exclude-local-evidence",
             "sha256": "b" * 64},
        ],
        "allowlist": ["skills/demo/sources.yaml"],
        "excluded_patterns": ["skills/demo/supplier/pages/**"],
    }
    tracked = ["skills/demo/sources.yaml", "skills/demo/supplier/pages/page.html",
               "skills/demo/supplier/pages/page.headers", "skills/demo/README.md"]
    distributed, excluded = P.build_distribution(tracked, dist)
    if distributed != ["skills/demo/sources.yaml", "skills/demo/README.md"]:
        raise AssertionError(f"unexpected distributed set: {distributed}")
    expect_no_findings(P.check_distribution(distributed, dist, root=ROOT), "fixture distributed set")
    if len(excluded) != 2:
        raise AssertionError(f"expected two excluded files, found {excluded}")


def test_fixture_unlisted_supplier_file_is_not_distributed(tmp: Path):
    """D-6. A supplier-path file that is not on the allowlist is a finding."""
    dist = {"sources": [], "allowlist": ["skills/demo/sources.yaml"], "excluded_patterns": []}
    found = P.check_distribution(["skills/demo/supplier/notes.txt"], dist)
    if codes(found) != {"D-6"}:
        raise AssertionError(f"unlisted supplier file was not reported: {found}")


def test_fixture_distributed_full_copy_is_d3(tmp: Path):
    dist = {"sources": [{"path": "skills/demo/supplier/pages/page.html",
                         "distribution_decision": "exclude-full-copy", "sha256": "c" * 64}],
            "allowlist": [], "excluded_patterns": []}
    found = P.check_distribution(["skills/demo/supplier/pages/page.html"], dist)
    if "D-3" not in codes(found):
        raise AssertionError(f"full copy in the distributed set was not reported: {found}")


def test_fixture_provisional_zero_fetch_scripts_is_not_a_finding(tmp: Path):
    """A standalone release needs a setup path. The provisional packaging test does not invent one."""
    dist = {"sources": [], "allowlist": ["skills/demo/supplier/fetch_pages.py"], "excluded_patterns": []}
    expect_no_findings(P.check_distribution(["skills/demo/supplier/fetch_pages.py"], dist), "fetch allowlist")


def test_fixture_supplier_file_outside_pages_is_a_coverage_finding(tmp: Path):
    """P-2. A stored supplier source anywhere under supplier/ needs an entry, not only pages/."""
    _fixture_skill(tmp, b"<html>listed</html>")
    write(tmp / "skills" / "demo" / "supplier" / "notes" / "quote.pdf", b"%PDF-1.4 unlisted")
    dist = {"allowlist": ["skills/demo/supplier/profiles/*.yaml"], "sources": []}
    found = P.check_coverage(tmp, dist, {"skills/demo/supplier/pages/page.html"})
    if [f["file"] for f in found] != ["skills/demo/supplier/notes/quote.pdf"]:
        raise AssertionError(f"supplier file outside pages was not reported: {found}")


def test_fixture_entry_without_a_magic_key_is_a_finding(tmp: Path):
    """P-1. A missing magic key is reported. A null value is allowed for header text only."""
    skill = _fixture_skill(tmp, b"<html>fixture</html>")
    manifest = P.load_yaml(skill / "sources.yaml")
    del manifest["sources"][0]["magic"]
    found = P.check_entries(tmp, skill, manifest, "demo/sources.yaml")
    if "D-2" not in codes(found):
        raise AssertionError(f"missing magic key was not reported: {found}")


def test_fixture_magic_null_is_refused_for_each_document_type(tmp: Path):
    """P-6. A null magic value is refused for HTML, PDF and XLSX. Header text may keep null."""
    cases = {
        "text/html": b"<html>page</html>",
        "application/pdf": b"%PDF-1.4 document",
        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet": b"PK\x03\x04 workbook",
    }
    for content_type, data in cases.items():
        entry = {"id": "x", "path": "x.bin", "url": "https://example.test/x", "retrieved": "2026-11-15",
                 "sha256": sha256_bytes(data), "content_type": content_type, "magic": None,
                 "license_state": "fixture", "distribution_decision": "exclude-full-copy"}
        write(tmp / "x.bin", data)
        found = P.check_entries(tmp, tmp, {"sources": [entry]}, "fixture")
        if "D-8" not in codes(found):
            raise AssertionError(f"null magic accepted for {content_type}: {found}")
    header = {"id": "h", "path": "x.bin", "url": "https://example.test/x", "retrieved": "2026-11-15",
              "sha256": sha256_bytes(cases["text/html"]), "content_type": "text/plain", "magic": None,
              "license_state": "fixture", "distribution_decision": "exclude-local-evidence"}
    write(tmp / "x.bin", cases["text/html"])
    expect_no_findings(P.check_entries(tmp, tmp, {"sources": [header]}, "fixture"), "header null magic")


def test_fixture_full_copy_at_an_unrelated_path_is_d3(tmp: Path):
    """P-7. A full copy at an unrelated path is found by its bytes, not by its path."""
    page = b"<html>a full supplier copy</html>"
    write(tmp / "docs" / "notes" / "copy.html", page)
    dist = {"sources": [{"path": "skills/demo/supplier/pages/page.html",
                         "distribution_decision": "exclude-full-copy", "sha256": sha256_bytes(page)}],
            "allowlist": [], "excluded_patterns": []}
    found = P.check_distribution(["docs/notes/copy.html"], dist, root=tmp)
    if "D-3" not in codes(found):
        raise AssertionError(f"full copy at an unrelated path was not found: {found}")


def test_fixture_project_authored_pdf_is_not_blocked_by_type(tmp: Path):
    """P-7. A project-authored PDF with bytes that match no excluded hash is not a finding."""
    write(tmp / "docs" / "own.pdf", b"%PDF-1.4 project fixture")
    dist = {"sources": [{"path": "skills/demo/supplier/pages/page.html",
                         "distribution_decision": "exclude-full-copy", "sha256": "d" * 64}],
            "allowlist": [], "excluded_patterns": []}
    expect_no_findings(P.check_distribution(["docs/own.pdf"], dist, root=tmp), "project PDF")


def _xls_entry(path: str, data: bytes, magic: str | None) -> dict:
    return {"id": "x", "path": path, "url": "https://example.test/x", "retrieved": "2026-11-15",
            "sha256": sha256_bytes(data), "content_type": "application/vnd.ms-excel", "magic": magic,
            "license_state": "fixture", "distribution_decision": "exclude-full-copy"}


def test_fixture_ole2_magic_accepts_the_prefix(tmp: Path):
    """A project-authored file that starts with the OLE2 signature passes the OLE2 magic check."""
    data = P.OLE2_PREFIX + b"\x00" * 504
    write(tmp / "x.xls", data)
    entry = _xls_entry("x.xls", data, "OLE2")
    expect_no_findings(P.check_entries(tmp, tmp, {"sources": [entry]}, "fixture"), "OLE2 prefix")


def test_fixture_ole2_magic_rejects_other_bytes(tmp: Path):
    """The parser reports D-8 for an incorrect OLE2 prefix."""
    data = b"PK\x03\x04" + b"\x00" * 504
    write(tmp / "x.xls", data)
    found = P.check_entries(tmp, tmp, {"sources": [_xls_entry("x.xls", data, "OLE2")]}, "fixture")
    if "D-8" not in codes(found):
        raise AssertionError(f"OLE2 magic accepted other bytes: {found}")


def test_fixture_xls_null_magic_is_refused(tmp: Path):
    """The parser reports D-8 when an Excel entry has null magic."""
    data = P.OLE2_PREFIX + b"\x00" * 504
    write(tmp / "x.xls", data)
    found = P.check_entries(tmp, tmp, {"sources": [_xls_entry("x.xls", data, None)]}, "fixture")
    if "D-8" not in codes(found):
        raise AssertionError(f"null magic accepted for application/vnd.ms-excel: {found}")



def test_fixture_skill_outside_repo_resolves_its_relative_binding(tmp: Path):
    """The relative profile resolves under the skill directory. The checker root is not a repository."""
    page = b"<html><body>outside repository</body></html>"
    skill = _fixture_skill(tmp, page, extra={"profile_binding": "supplier/profiles/demo.yaml"})
    write(skill / "supplier" / "profiles" / "demo.yaml", ("evidence_sha256: " + sha256_bytes(page) + "\n").encode("utf-8"))
    other_root = tmp / "not-the-repository"
    other_root.mkdir()
    manifest = P.load_yaml(skill / "sources.yaml")
    expect_no_findings(P.check_entries(other_root, skill, manifest, "demo/sources.yaml"), "outside repository")


def test_fixture_profile_link_and_escape_are_refused(tmp: Path):
    """The checker reports D-9 for a symbolic link or a '..' path in a profile binding."""
    page = b"<html><body>link and escape case</body></html>"
    real = tmp / "real-profile.yaml"
    write(real, ("evidence_sha256: " + sha256_bytes(page) + "\n").encode("utf-8"))
    skill = _fixture_skill(tmp, page, extra={"profile_binding": "supplier/profiles/link.yaml"})
    (skill / "supplier" / "profiles").mkdir(parents=True, exist_ok=True)
    os.symlink(real, skill / "supplier" / "profiles" / "link.yaml")
    found = P.check_entries(tmp, skill, P.load_yaml(skill / "sources.yaml"), "demo/sources.yaml")
    if "D-9" not in codes(found):
        raise AssertionError(f"profile symbolic link was not refused: {found}")
    manifest = P.load_yaml(skill / "sources.yaml")
    manifest["sources"][0]["profile_binding"] = "../../real-profile.yaml"
    found = P.check_entries(tmp, skill, manifest, "demo/sources.yaml")
    if "D-9" not in codes(found):
        raise AssertionError(f"escaping profile binding was not refused: {found}")



def test_fixture_symlinked_manifest_directory_is_refused(tmp: Path):
    """The parser refuses a linked manifest directory and a linked parent."""
    page = b"<html><body>linked manifest directory</body></html>"
    real_root = tmp / "real"
    skill = _fixture_skill(real_root, page, extra={"profile_binding": "supplier/profiles/demo.yaml"})
    write(skill / "supplier" / "profiles" / "demo.yaml", ("evidence_sha256: " + sha256_bytes(page) + "\n").encode("utf-8"))
    manifest = P.load_yaml(skill / "sources.yaml")
    expect_no_findings(P.check_entries(tmp, skill, manifest, "demo/sources.yaml"), "real manifest directory")
    os.symlink(skill, tmp / "linked-skill")
    found = P.check_entries(tmp, tmp / "linked-skill", manifest, "demo/sources.yaml")
    if "D-9" not in codes(found):
        raise AssertionError("The parser accepted a linked manifest directory.")
    os.symlink(real_root, tmp / "alias")
    found = P.check_entries(tmp, tmp / "alias" / "skills" / "demo", manifest, "demo/sources.yaml")
    if "D-9" not in codes(found):
        raise AssertionError("The parser accepted a linked parent.")


def test_repository_manifest_relative_bindings_resolve_under_their_directory(tmp: Path):
    """Each binding of the repository skill manifest resolves under its manifest directory and exists."""
    bindings = [entry["profile_binding"] for entry in P.load_yaml(PCB_FAB / "sources.yaml")["sources"]
                if entry.get("profile_binding")]
    if len(bindings) != 5:
        raise AssertionError(f"expected five bindings, found {len(bindings)}")
    for binding in bindings:
        if binding.startswith("skills/"):
            raise AssertionError(f"binding is not relative to its manifest directory: {binding}")
        resolved = P.confined_profile(PCB_FAB, binding)
        if resolved != PCB_FAB / binding:
            raise AssertionError(f"binding does not resolve under the manifest directory: {binding}")
        if not resolved.is_file():
            raise AssertionError(f"resolved profile is missing: {binding}")

if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else ""
    tests = [(n, f) for n, f in list(globals().items()) if n.startswith("test_") and key in n]
    failed = 0
    with tempfile.TemporaryDirectory() as td:
        for name, fn in tests:
            tmp = Path(td) / name
            tmp.mkdir()
            try:
                fn(tmp)
                print(f"ok   {name}")
            except Exception as error:  # noqa: BLE001
                failed += 1
                print(f"FAIL {name}: {type(error).__name__}: {error}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
