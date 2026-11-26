# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Tests for the JLCPCB profiles of skills/pcb-fab-package (part jlc). Run with: uv run tests/test_pcb_fab_jlcpcb.py

The tests need no network, no container and no stored supplier page. The tests that read a page
or run the CLI use a temporary fixture skill (tests/fab_fixture.py). The tables of the repository
are read with the ast module, so the test reads the repository files, not the fixture copies.
"""

from __future__ import annotations

import ast
import json
import os
import shutil
import subprocess
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from fab_fixture import fixture_skill  # noqa: E402

REPO = ROOT / "skills" / "pcb-fab-package"
SKILL = fixture_skill(REPO)
SCRIPTS = SKILL / "scripts"
sys.path.insert(0, str(SCRIPTS))
import fab  # noqa: E402
import review  # noqa: E402
import validate as VAL  # noqa: E402
import workflow  # noqa: E402

JLCPCB = ("jlcpcb-two-layer", "jlcpcb-four-layer")
OSHPARK_WORKFLOW = {"oshpark-single-layer", "oshpark-two-layer", "oshpark-two-layer-hhdc",
                    "oshpark-four-layer", "oshpark-six-layer"}
PAGE_ID = "jlcpcb-pcb-capabilities"
PAGE_URL = "https://jlcpcb.com/capabilities/pcb-capabilities"
PAGE_REL = "supplier/pages/jlcpcb-pcb-capabilities.html"
HEADERS_REL = "supplier/pages/jlcpcb-pcb-capabilities.headers"
ZERO_HASH = "0" * 64
# Rows that workflow.mandatory_conditions names but that are not limits (workflow.py:734, :749).
MASK_ROWS = {"mask_web_min_top", "mask_web_min_bottom"}
# Rows and extensions that workflow.mandatory_conditions names with a prefix: the tool
# compatibility rows (workflow.py:570) and the service.* and process.* extensions.
DERIVED_PREFIXES = ("process.", "service.")
TWO_LAYER_RULES = (
    "(version 1)\n"
    '(rule "supplier_edge_keepout" (constraint edge_clearance (min 0.2mm)))\n'
    '(rule "supplier_min_annular_ring" (constraint annular_width (min 0.18mm)))\n'
    '(rule "supplier_min_drill" (constraint hole_size (min 0.15mm)))\n'
    '(rule "supplier_min_space" (constraint clearance (min 0.1mm)))\n'
    '(rule "supplier_min_trace" (constraint track_width (min 0.1mm)))\n'
)


def expect(condition, message):
    """Raise AssertionError with the message when the condition is false."""
    if not condition:
        raise AssertionError(message)


def repo_profile(pid):
    """Return the checked record of a repository profile. No page is read."""
    return VAL.load_record(REPO / "supplier" / "profiles" / f"{pid}.yaml")


def fixture_profile_path(pid):
    return SKILL / "supplier" / "profiles" / f"{pid}.yaml"


def repo_literal(path, name):
    """Return the literal value of a module-level assignment, read with ast. The module is not imported."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    for node in tree.body:
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == name for t in node.targets):
            return ast.literal_eval(node.value)
    raise AssertionError(f"{name} is not a literal assignment in {path}")


def manifest_entries():
    data = yaml.safe_load((REPO / "sources.yaml").read_text(encoding="utf-8"))
    return {entry["id"]: entry for entry in data["sources"]}


def written_profile(directory, record):
    """Write a profile with a correct content hash. The hash of the fixture pages is not changed."""
    record = dict(record)
    record["content_sha256"] = fab.content_hash(record)
    path = directory / "profile.yaml"
    path.write_text(json.dumps(record, indent=2) + "\n", encoding="utf-8")
    return path


def run_cli(path_env, *args):
    """Run the fixture CLI through uv, as the existing tests do. Return the exit code and the output."""
    env = dict(os.environ, PATH=path_env)
    done = subprocess.run(["uv", "run", "--quiet", str(SCRIPTS / "fab.py"), *args],
                          capture_output=True, text=True, env=env, check=False)
    return done.returncode, done.stdout + done.stderr


def test_page_tables_agree():
    """The page tables of fab and review are equal (D4). The workflow profiles are the five OSH Park ids."""
    fab_pages = repo_literal(REPO / "scripts" / "fab.py", "PROFILE_PAGES")
    review_pages = repo_literal(REPO / "scripts" / "review.py", "PAGE_SETS")
    expect(fab_pages == review_pages, "fab.PROFILE_PAGES and review.PAGE_SETS differ.")
    for pid in JLCPCB:
        expect(fab_pages.get(pid) == {PAGE_ID}, f"{pid} must bind exactly the page {PAGE_ID}.")
    workflow_profiles = repo_literal(REPO / "scripts" / "fab.py", "WORKFLOW_PROFILES")
    expect(workflow_profiles == OSHPARK_WORKFLOW,
           f"WORKFLOW_PROFILES is {sorted(workflow_profiles)}. Expected the five OSH Park ids.")
    expect(workflow_profiles <= set(fab_pages), "WORKFLOW_PROFILES names an id that has no page table row.")


def test_jlcpcb_profiles_validate():
    """Each fixture profile passes check_profile. Each repository profile has no schema finding."""
    registry = VAL.load_registry(SKILL / "contracts" / "schemas")
    for pid in JLCPCB:
        fab.check_profile(fixture_profile_path(pid))
        path = REPO / "supplier" / "profiles" / f"{pid}.yaml"
        findings = VAL.validate_record(repo_profile(pid), registry, str(path))
        expect(findings == [], f"{pid} has schema findings: {findings}")


def test_jlcpcb_content_hash():
    """The stored content hash of each repository profile equals the hash of its content."""
    for pid in JLCPCB:
        record = repo_profile(pid)
        expect(record["content_sha256"] == fab.content_hash(record), f"{pid}: content_sha256 is stale.")


def test_jlcpcb_one_page_each():
    """Each JLCPCB profile binds exactly the one page. Its evidence hash is the page hash in the manifest."""
    entries = manifest_entries()
    page_sha = entries[f"{PAGE_ID}-html"]["sha256"]
    for pid in JLCPCB:
        record = repo_profile(pid)
        bound = record["extensions"]["evidence_pages"]
        expect(set(bound) == {PAGE_ID}, f"{pid} binds {sorted(bound)}. Expected {PAGE_ID}.")
        expect(bound[PAGE_ID]["sha256"] == record["evidence_sha256"] == page_sha,
               f"{pid}: the evidence hash differs from the page hash of the manifest.")


def test_jlcpcb_manifest_binding():
    """The manifest has the page entry and the headers entry. The page entry binds the two-layer profile only."""
    entries = manifest_entries()
    html = entries[f"{PAGE_ID}-html"]
    headers = entries[f"{PAGE_ID}-headers"]
    expect(html["path"] == PAGE_REL, f"The page path is {html['path']}.")
    expect(html["url"] == PAGE_URL, f"The page URL is {html['url']}.")
    expect(html["magic"] == "markup" and html["content_type"] == "text/html", "The page entry has a wrong type.")
    expect(html["distribution_decision"] == "exclude-full-copy", "The page must not be distributed.")
    expect(html["profile_binding"] == "supplier/profiles/jlcpcb-two-layer.yaml",
           f"The page binds {html['profile_binding']}.")
    expect(headers["path"] == HEADERS_REL, f"The headers path is {headers['path']}.")
    expect(headers["distribution_decision"] == "exclude-local-evidence", "The headers entry has a wrong decision.")
    expect(headers["profile_binding"] is None, "The headers entry must have no profile binding.")
    expect(html["sha256"] == repo_profile("jlcpcb-two-layer")["evidence_sha256"],
           "The page hash differs from the two-layer evidence hash.")


def test_jlcpcb_ignore_rules():
    """Each stored JLCPCB page has its exact ignore line. Git ignores it and does not track it."""
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    for rel in ("skills/pcb-fab-package/" + PAGE_REL, "skills/pcb-fab-package/" + HEADERS_REL):
        expect("/" + rel in lines, f"The .gitignore file has no exact line /{rel}.")
        done = subprocess.run(["git", "check-ignore", "--no-index", "-q", rel], cwd=ROOT, check=False)
        expect(done.returncode == 0, f"Git does not ignore {rel}.")
    tracked = subprocess.run(["git", "ls-files", "--", "skills/pcb-fab-package/supplier/pages"],
                             cwd=ROOT, capture_output=True, text=True, check=True).stdout
    expect(tracked == "", f"Git tracks a supplier page: {tracked!r}.")


def test_jlcpcb_kicad_dru_units():
    """Each kicad_dru key of a JLCPCB profile has a constraint in the workflow, a minimum and the unit mm."""
    for pid in JLCPCB:
        record = repo_profile(pid)
        for key in record["division"]["kicad_dru"]:
            expect(key in workflow.RULE_CONSTRAINT, f"{pid}: {key} has no constraint.")
            limit = record["limits"][key]
            expect(limit["unit"] == "mm" and limit["kind"] == "minimum",
                   f"{pid}: {key} must be a minimum in mm for the rule file.")


def test_jlcpcb_mandatory_limits_present():
    """Each mandatory name of the workflow is a limit, except the named exclusions (CHANGE 2 of review 3)."""
    for pid in JLCPCB:
        record = repo_profile(pid)
        for name in sorted(workflow.mandatory_conditions(record)):
            if name in MASK_ROWS or name.startswith(DERIVED_PREFIXES):
                continue
            expect(name in record["limits"], f"{pid}: the mandatory name {name} is not a limit.")


def test_jlcpcb_strict_values():
    """The stricter page values are in both profiles: mask bridge 0.13 mm, board 599 x 497 mm (R10)."""
    expected = {"mask_web_min": "0.13", "board_max_width": "599", "board_max_height": "497"}
    for pid in JLCPCB:
        limits = repo_profile(pid)["limits"]
        for key, value in expected.items():
            expect(limits[key]["unit"] == "mm", f"{pid}: {key} is not in mm.")
            expect(Fraction(str(limits[key]["value"])) == Fraction(value),
                   f"{pid}: {key} is {limits[key]['value']}. Expected {value}.")


def test_jlcpcb_rules_text():
    """The text of the two-layer rules equals the text that the workflow makes for the profile."""
    expect(workflow.supplier_rules_text(repo_profile("jlcpcb-two-layer")) == TWO_LAYER_RULES,
           "The two-layer rules text is different from the expected text.")


def test_jlcpcb_order_multiple_form():
    """The marked not_stated form passes for a JLCPCB id, and fails with a value or for an OSH Park id (CHANGE 1)."""
    base = json.loads(fixture_profile_path("jlcpcb-two-layer").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        fab.check_profile(written_profile(tmp, base))
        marked_with_value = json.loads(json.dumps(base))
        marked_with_value["extensions"]["service.order_multiple"] = {"kind": "not_stated", "value": 3}
        try:
            fab.check_profile(written_profile(tmp, marked_with_value))
        except fab.Invalid:
            pass
        else:
            raise AssertionError("A not_stated form with a value passes for a JLCPCB id.")
        oshpark = json.loads(fixture_profile_path("oshpark-two-layer").read_text(encoding="utf-8"))
        oshpark["extensions"]["service.order_multiple"] = {"kind": "not_stated"}
        try:
            fab.check_profile(written_profile(tmp, oshpark))
        except fab.Invalid:
            pass
        else:
            raise AssertionError("The marked form passes for an OSH Park id.")
        requirement = json.loads(json.dumps(base))
        requirement["extensions"]["service.order_multiple"] = {"kind": "requirement", "value": "3"}
        try:
            fab.check_profile(written_profile(tmp, requirement))
        except fab.Invalid:
            pass
        else:
            raise AssertionError("A text value for the order multiple passes.")


def test_jlcpcb_cli_stops():
    """Five commands stop with exit 2 for each JLCPCB profile, before any container job starts (Q2)."""
    for pid in JLCPCB:
        with tempfile.TemporaryDirectory() as td:
            tmp = Path(td)
            project = tmp / "project"
            project.mkdir()
            shutil.copy(ROOT / "tests" / "fixtures" / "pcb" / "board.yaml", project / "board.yaml")
            stub_dir = tmp / "bin"
            stub_dir.mkdir()
            marker = tmp / "podman-ran.txt"
            stub = stub_dir / "podman"
            stub.write_text(f'#!/bin/sh\necho ran > "{marker}"\nexit 3\n', encoding="utf-8")
            stub.chmod(0o755)
            path_env = f"{stub_dir}{os.pathsep}{os.environ.get('PATH', '')}"
            profile = str(fixture_profile_path(pid))
            facts, dest = tmp / "facts.json", tmp / "dest"
            review_file, inventory, board = tmp / "review.json", tmp / "inventory.json", tmp / "board.kicad_pcb"
            commands = {
                "design": ["design", "--project", str(project), "--profile", profile],
                "drawing-facts": ["drawing-facts", "--inventory", str(inventory), "--profile", profile,
                                  "--board", str(board), "--release", "r1", "--out", str(facts)],
                "supplier": ["supplier", "--project", str(project), "--profile", profile],
                "review-gate": ["review-gate", "--project", str(project), "--profile", profile,
                                "--review", str(review_file), "--expect-sha256", ZERO_HASH, "--release", "r1"],
                "package": ["package", "--project", str(project), "--profile", profile, "--release", "r1",
                            "--review", str(review_file), "--review-sha256", ZERO_HASH, "--dest", str(dest)],
            }
            for cmd, args in commands.items():
                code, out = run_cli(path_env, *args)
                expect(code == 2, f"{pid} {cmd}: exit {code}. Expected 2. Output: {out}")
                expect("contains only values" in out and f"The command {cmd} does not run" in out,
                       f"{pid} {cmd}: the stop message is missing. Output: {out}")
            expect(not marker.exists(), f"{pid}: a container job started (the podman stub ran).")
            expect(sorted(p.name for p in project.iterdir()) == ["board.yaml"],
                   f"{pid}: the project changed: {sorted(p.name for p in project.iterdir())}.")
            expect(not facts.exists() and not dest.exists(), f"{pid}: an output file was written.")


def test_oshpark_cli_not_stopped():
    """An OSH Park profile is not refused. review-gate reaches the review check and exits 1 (no review record)."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        project = tmp / "project"
        project.mkdir()
        shutil.copy(ROOT / "tests" / "fixtures" / "pcb" / "board.yaml", project / "board.yaml")
        code, out = run_cli(os.environ.get("PATH", ""), "review-gate", "--project", str(project),
                            "--profile", str(fixture_profile_path("oshpark-two-layer")),
                            "--review", str(tmp / "missing.json"), "--expect-sha256", ZERO_HASH, "--release", "r1")
        expect(code == 1, f"review-gate with an OSH Park profile gave exit {code}. Expected 1. Output: {out}")
        expect("the source review record is missing" in out, f"Unexpected output: {out}")
        expect("contains only values" not in out, "The OSH Park profile is refused as a profile that contains only values.")


def test_jlcpcb_corner_stop_unit():
    """The corner check stops with exit 2 for a JLCPCB profile: no cutter diameter in inches (R2, R3)."""
    for pid in JLCPCB:
        try:
            workflow.corner_conditions(repo_profile(pid), {"corners": []})
        except workflow.Stop as err:
            expect(err.code == workflow.EXIT_UNSUPPORTED, f"{pid}: the stop exit is {err.code}.")
        else:
            raise AssertionError(f"{pid}: the corner check did not stop.")


def test_jlcpcb_via_fail_closed():
    """Blind, buried and via-in-pad spans fail. Through spans pass with the standard_through declaration."""
    def status(record, declaration, construction):
        measured = {"vias": [{"construction": construction}]}
        return workflow.via_condition(record, declaration, measured)["status"]

    for pid in JLCPCB:
        record = repo_profile(pid)
        expect(status(record, None, "blind") == "fail", f"{pid}: a blind span does not fail.")
        expect(status(record, None, "buried") == "fail", f"{pid}: a buried span does not fail.")
        expect(status(record, "filled_plated_via_in_pad", "through") == "fail",
               f"{pid}: the via-in-pad declaration on through spans does not fail.")
        expect(status(record, "standard_through", "through") == "pass",
               f"{pid}: through spans with standard_through do not pass.")


def test_jlcpcb_judge_boundaries():
    """The two-layer min_trace of 0.10 mm: 0.09 mm fails, 0.10 mm and 0.11 mm pass."""
    threshold = fab.limit_in_mm(repo_profile("jlcpcb-two-layer")["limits"]["min_trace"])
    expect(fab.judge("minimum", Fraction("0.09"), threshold) == "fail", "0.09 mm does not fail.")
    expect(fab.judge("minimum", Fraction("0.10"), threshold) == "pass", "0.10 mm does not pass.")
    expect(fab.judge("minimum", Fraction("0.11"), threshold) == "pass", "0.11 mm does not pass.")


def test_jlcpcb_fact_items_complete():
    """review.fact_items gives one fact for each limit and each extension except evidence_pages. No KeyError."""
    for pid in JLCPCB:
        record = repo_profile(pid)
        facts = review.fact_items(record)
        expected = set(record["limits"]) | (set(record["extensions"]) - {"evidence_pages"})
        expect(set(facts) == expected, f"{pid}: the facts differ from the limits and extensions.")


def test_jlcpcb_no_cutter_facts():
    """The profiles have no cutter, substrate or thickness fact. The notes list each missing value (Q2, Q3)."""
    absent = ("process.outline_cutter_diameter", "process.cutout_cutter_diameter",
              "service.substrate", "service.finished_thickness_display_mm")
    for pid in JLCPCB:
        extensions = repo_profile(pid)["extensions"]
        for key in absent:
            expect(key not in extensions, f"{pid} has the fact {key}.")
        for key in absent + ("service.order_multiple",):
            expect(key in extensions["notes.not_stated"], f"{pid}: notes.not_stated does not list {key}.")


def test_jlcpcb_manual_text_limits():
    """Each JLCPCB profile has text limits for the copper weight, the board thickness and the mask bridge that the
    page states (amendment I). Each is manual evidence, has no unit and no workflow row, and the note names the control."""
    expected = {"copper_weight_outer", "board_thickness_options", "board_thickness_condition",
                "soldermask_bridge_by_color"}
    for pid in JLCPCB:
        record = repo_profile(pid)
        text_keys = {key for key, limit in record["limits"].items() if limit["value_kind"] == "text"}
        expect(text_keys == expected, f"{pid}: the text limits are {sorted(text_keys)}.")
        for key in expected:
            limit = record["limits"][key]
            expect(record["division"]["manual_evidence"].count(key) == 1, f"{pid}: {key} is not manual evidence.")
            expect(limit["kind"] == "recommendation" and "unit" not in limit,
                   f"{pid}: {key} must be a recommendation without a unit.")
            expect(isinstance(limit["value"], str) and limit["value"].strip() != "",
                   f"{pid}: {key} has no text value.")
        note = record["extensions"].get("notes.manual_conditions", "").lower()
        expect("no workflow row" in note and "control" in note,
               f"{pid}: the note does not name the control for the manual conditions.")


TESTS = [value for name, value in list(globals().items()) if name.startswith("test_") and callable(value)]


def main():
    failed = 0
    for fn in TESTS:
        try:
            fn()
            print(f"ok   {fn.__name__}")
        except Exception as err:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {type(err).__name__}: {err}")
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
