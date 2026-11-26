# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Tests for the PCBWay profiles of skills/pcb-fab-package (part pcbway). Run with: uv run tests/test_pcb_fab_pcbway.py

The tests need no network, no container and no stored supplier page. The tests that read a page
or run the CLI use a temporary fixture skill (tests/fab_fixture.py). The tables of the repository
are read with the ast module, so the test reads the repository files, not the fixture copies.
"""

from __future__ import annotations

import ast
import hashlib
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

PCBWAY = ("pcbway-two-layer", "pcbway-four-layer")
OSHPARK_WORKFLOW = {"oshpark-single-layer", "oshpark-two-layer", "oshpark-two-layer-hhdc",
                    "oshpark-four-layer", "oshpark-six-layer"}
PAGE_ID = "pcbway-capabilities"
PAGE_URL = "https://www.pcbway.com/capabilities.html"
PAGE_REL = "supplier/pages/pcbway-capabilities.html"
HEADERS_REL = "supplier/pages/pcbway-capabilities.headers"
ZERO_HASH = "0" * 64
RELEASE = "r1"
# Rows that workflow.mandatory_conditions names but that are not limits (workflow.py:734, :749, :570).
ROW_NAMES = {"mask_web_min_top", "mask_web_min_bottom", "process.outline_tool_compatibility",
             "process.cutout_tool_compatibility"}
# Extensions that workflow.mandatory_conditions names (review 3, CHANGE 2).
EXTENSION_NAMES = {"service.layers", "service.order_multiple", "service.via_construction_prohibited"}
# The rule text of each profile. The workflow and the generator must give these lines (section 3.5).
TWO_LAYER_RULES = (
    "(version 1)\n"
    '(rule "supplier_edge_keepout" (constraint edge_clearance (min 0.25mm)))\n'
    '(rule "supplier_min_annular_ring" (constraint annular_width (min 0.15mm)))\n'
    '(rule "supplier_min_drill" (constraint hole_size (min 0.15mm)))\n'
    '(rule "supplier_min_space" (constraint clearance (min 0.1mm)))\n'
    '(rule "supplier_min_trace" (constraint track_width (min 0.1mm)))\n'
)
FOUR_LAYER_RULES = TWO_LAYER_RULES + (
    '(rule "supplier_plated_drill_to_internal_copper" (constraint hole_clearance (min 0.1778mm)))\n'
)
TEXT_KEYS_COMMON = {"copper_weight_outer", "board_thickness_options", "board_thickness_condition",
                    "soldermask_colors", "soldermask_bridge_by_color"}


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


def test_pcbway_page_rows():
    """Both ids are in the page tables of fab and review with the one page (D4). Neither id is a workflow profile (P2)."""
    fab_pages = repo_literal(REPO / "scripts" / "fab.py", "PROFILE_PAGES")
    review_pages = repo_literal(REPO / "scripts" / "review.py", "PAGE_SETS")
    expect(fab_pages == review_pages, "fab.PROFILE_PAGES and review.PAGE_SETS differ.")
    for pid in PCBWAY:
        expect(fab_pages.get(pid) == {PAGE_ID}, f"{pid} must bind exactly the page {PAGE_ID}.")
    workflow_profiles = repo_literal(REPO / "scripts" / "fab.py", "WORKFLOW_PROFILES")
    expect(workflow_profiles == OSHPARK_WORKFLOW, "WORKFLOW_PROFILES changed. PCBWay must not be added to it.")
    for pid in PCBWAY:
        expect(pid not in workflow_profiles, f"{pid} is a workflow profile.")


def test_pcbway_profiles_validate():
    """Each fixture profile passes check_profile. Each repository profile has no schema finding."""
    registry = VAL.load_registry(SKILL / "contracts" / "schemas")
    for pid in PCBWAY:
        fab.check_profile(fixture_profile_path(pid))
        path = REPO / "supplier" / "profiles" / f"{pid}.yaml"
        findings = VAL.validate_record(repo_profile(pid), registry, str(path))
        expect(findings == [], f"{pid} has schema findings: {findings}")


def test_pcbway_content_hash():
    """The stored content hash of each repository profile equals the hash of its content."""
    for pid in PCBWAY:
        record = repo_profile(pid)
        expect(record["content_sha256"] == fab.content_hash(record), f"{pid}: content_sha256 is stale.")


def test_pcbway_one_page_each():
    """Each PCBWay profile binds exactly the one page. Its evidence hash is the page hash in the manifest."""
    page_sha = manifest_entries()[f"{PAGE_ID}-html"]["sha256"]
    for pid in PCBWAY:
        record = repo_profile(pid)
        bound = record["extensions"]["evidence_pages"]
        expect(set(bound) == {PAGE_ID}, f"{pid} binds {sorted(bound)}. Expected {PAGE_ID}.")
        expect(bound[PAGE_ID]["sha256"] == record["evidence_sha256"] == page_sha,
               f"{pid}: the evidence hash differs from the page hash of the manifest.")


def test_pcbway_manifest_binding():
    """The manifest has the page entry and the headers entry. The page entry binds the two-layer profile only."""
    entries = manifest_entries()
    html = entries[f"{PAGE_ID}-html"]
    headers = entries[f"{PAGE_ID}-headers"]
    expect(html["path"] == PAGE_REL, f"The page path is {html['path']}.")
    expect(html["url"] == PAGE_URL, f"The page URL is {html['url']}.")
    expect(html["magic"] == "markup" and html["content_type"] == "text/html", "The page entry has a wrong type.")
    expect(html["distribution_decision"] == "exclude-full-copy", "The page must not be distributed.")
    expect(html["profile_binding"] == "supplier/profiles/pcbway-two-layer.yaml",
           f"The page binds {html['profile_binding']}.")
    expect(headers["path"] == HEADERS_REL, f"The headers path is {headers['path']}.")
    expect(headers["distribution_decision"] == "exclude-local-evidence", "The headers entry has a wrong decision.")
    expect(headers["profile_binding"] is None, "The headers entry must have no profile binding.")
    expect(html["sha256"] == repo_profile("pcbway-two-layer")["evidence_sha256"],
           "The page hash differs from the two-layer evidence hash.")


def test_pcbway_ignore_rules():
    """Each stored PCBWay page has its exact ignore line. Git ignores it and does not track it."""
    lines = (ROOT / ".gitignore").read_text(encoding="utf-8").splitlines()
    for rel in ("skills/pcb-fab-package/" + PAGE_REL, "skills/pcb-fab-package/" + HEADERS_REL):
        expect("/" + rel in lines, f"The .gitignore file has no exact line /{rel}.")
        done = subprocess.run(["git", "check-ignore", "--no-index", "-q", rel], cwd=ROOT, check=False)
        expect(done.returncode == 0, f"Git does not ignore {rel}.")
    tracked = subprocess.run(["git", "ls-files", "--", "skills/pcb-fab-package/supplier/pages"],
                             cwd=ROOT, capture_output=True, text=True, check=True).stdout
    expect(tracked == "", f"Git tracks a supplier page: {tracked!r}.")


def test_pcbway_kicad_dru_units():
    """Each kicad_dru key of a PCBWay profile has a constraint in the workflow, a minimum, and the unit mm or mil."""
    for pid in PCBWAY:
        record = repo_profile(pid)
        for key in record["division"]["kicad_dru"]:
            expect(key in workflow.RULE_CONSTRAINT, f"{pid}: {key} has no constraint.")
            limit = record["limits"][key]
            expect(limit["unit"] in ("mm", "mil") and limit["kind"] == "minimum",
                   f"{pid}: {key} must be a minimum in mm or mil for the rule file.")


def test_pcbway_mandatory_limits_present():
    """Each mandatory name is a limit. The seven named exclusions are rows or extensions (review 3, CHANGE 2)."""
    for pid in PCBWAY:
        record = repo_profile(pid)
        missing = []
        for name in sorted(workflow.mandatory_conditions(record)):
            if name in ROW_NAMES or name in EXTENSION_NAMES:
                continue
            if name not in record["limits"]:
                missing.append(name)
        expect(not missing, f"{pid}: the mandatory names that are not limits: {missing}")
        for name in EXTENSION_NAMES:
            expect(name in record["extensions"], f"{pid}: the extension {name} is missing.")


def test_pcbway_strict_values():
    """The stricter values of P5 and P6 are in the profiles: mask bridge 4.5 mil, slot 0.8 mm, four-layer height 600 mm."""
    limits = repo_profile("pcbway-two-layer")["limits"]
    expect(Fraction(str(limits["mask_web_min"]["value"])) == Fraction("4.5") and limits["mask_web_min"]["unit"] == "mil",
           "mask_web_min is not 4.5 mil.")
    expect(Fraction(str(limits["min_slot_size"]["value"])) == Fraction("0.8") and limits["min_slot_size"]["unit"] == "mm",
           "min_slot_size is not 0.8 mm.")
    four = repo_profile("pcbway-four-layer")["limits"]
    expect(Fraction(str(four["board_max_height"]["value"])) == Fraction("600"), "Four-layer board_max_height is not 600 mm.")
    expect(Fraction(str(four["board_max_width"]["value"])) == Fraction("560"), "Four-layer board_max_width is not 560 mm.")


def test_pcbway_rules_text():
    """The text of each rule file equals the text that the workflow makes for the profile (section 3.5)."""
    expect(workflow.supplier_rules_text(repo_profile("pcbway-two-layer")) == TWO_LAYER_RULES,
           "The two-layer rules text is different from the expected text.")
    expect(workflow.supplier_rules_text(repo_profile("pcbway-four-layer")) == FOUR_LAYER_RULES,
           "The four-layer rules text is different from the expected text.")


def test_pcbway_mil_conversion():
    """A mil limit converts exactly: 4.5 mil is 1143/10000 mm and 7 mil is 1778/10000 mm."""
    mask = fab.limit_in_mm(repo_profile("pcbway-two-layer")["limits"]["mask_web_min"])
    expect(mask == Fraction(1143, 10000), f"mask_web_min converts to {mask}.")
    drill = fab.limit_in_mm(repo_profile("pcbway-four-layer")["limits"]["plated_drill_to_internal_copper"])
    expect(drill == Fraction(1778, 10000), f"plated_drill_to_internal_copper converts to {drill}.")


def test_pcbway_order_multiple_form():
    """The marked not_stated form passes for a PCBWay id. It fails with a value, and it fails for an OSH Park id (P3)."""
    base = json.loads(fixture_profile_path("pcbway-two-layer").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        fab.check_profile(written_profile(tmp, base))
        marked_with_value = json.loads(json.dumps(base))
        marked_with_value["extensions"]["service.order_multiple"] = {"kind": "not_stated", "value": 5}
        try:
            fab.check_profile(written_profile(tmp, marked_with_value))
        except fab.Invalid:
            pass
        else:
            raise AssertionError("A not_stated form with a value passes for a PCBWay id.")
        oshpark = json.loads(fixture_profile_path("oshpark-two-layer").read_text(encoding="utf-8"))
        oshpark["extensions"]["service.order_multiple"] = {"kind": "not_stated"}
        try:
            fab.check_profile(written_profile(tmp, oshpark))
        except fab.Invalid:
            pass
        else:
            raise AssertionError("The marked form passes for an OSH Park id.")


def test_pcbway_cli_stops():
    """Five commands stop with exit 2 for each PCBWay profile, before any container job starts. The message names
    the PCBWay setup note (P2)."""
    for pid in PCBWAY:
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
                                  "--board", str(board), "--release", RELEASE, "--out", str(facts)],
                "supplier": ["supplier", "--project", str(project), "--profile", profile],
                "review-gate": ["review-gate", "--project", str(project), "--profile", profile,
                                "--review", str(review_file), "--expect-sha256", ZERO_HASH, "--release", RELEASE],
                "package": ["package", "--project", str(project), "--profile", profile, "--release", RELEASE,
                            "--review", str(review_file), "--review-sha256", ZERO_HASH, "--dest", str(dest)],
            }
            for cmd, args in commands.items():
                code, out = run_cli(path_env, *args)
                expect(code == 2, f"{pid} {cmd}: exit {code}. Expected 2. Output: {out}")
                expect("has data only" in out and f"The command {cmd} does not run" in out,
                       f"{pid} {cmd}: the stop message is missing. Output: {out}")
                expect("references/pcbway-kicad-setup.md" in out,
                       f"{pid} {cmd}: the message does not name the PCBWay note. Output: {out}")
            expect(not marker.exists(), f"{pid}: a container job started (the podman stub ran).")
            expect(sorted(p.name for p in project.iterdir()) == ["board.yaml"],
                   f"{pid}: the project changed: {sorted(p.name for p in project.iterdir())}.")
            expect(not facts.exists() and not dest.exists(), f"{pid}: an output file was written.")


def test_jlcpcb_message_unchanged():
    """The message for a JLCPCB profile still names the JLCPCB note (P2: only the path of the profile changes)."""
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        project = tmp / "project"
        project.mkdir()
        code, out = run_cli(os.environ.get("PATH", ""), "review-gate", "--project", str(project),
                            "--profile", str(fixture_profile_path("jlcpcb-two-layer")),
                            "--review", str(tmp / "missing.json"), "--expect-sha256", ZERO_HASH, "--release", RELEASE)
        expect(code == 2, f"review-gate with a JLCPCB profile gave exit {code}. Expected 2. Output: {out}")
        expect("references/jlcpcb-kicad-setup.md" in out, f"The JLCPCB note is not named. Output: {out}")


def test_pcbway_review_source_real_path():
    """The supported command review-source runs on the real path. It gives unchanged, then harmless, then material."""
    profile_path = fixture_profile_path("pcbway-two-layer")
    record = fab.check_profile(profile_path)
    stored = SKILL / "supplier" / "pages" / f"{PAGE_ID}.html"
    stored_sha = hashlib.sha256(stored.read_bytes()).hexdigest()
    facts = review.fact_items(record)
    page_url = record["extensions"]["evidence_pages"][PAGE_ID]["source_url"]
    with tempfile.TemporaryDirectory() as td:
        project = Path(td) / "project"
        live = project / "out" / "fab" / "source-review" / "live"
        live.mkdir(parents=True)
        (live / f"{PAGE_ID}.html").write_bytes(stored.read_bytes())

        def observations(observed_override=None):
            items = []
            for key, (value, unit, source_url) in sorted(facts.items()):
                if key == observed_override:
                    value = 0.09  # a trace below the 0.10 mm limit: a material difference
                items.append({"key": key, "observed_value": value, "observed_unit": unit,
                              "observed_condition": "Project-authored fixture reading.",
                              "source_url": source_url, "reviewer_reading": "Project-authored fixture reading."})
            return items

        def write_observations(name, live_bytes, override=None):
            live_path = live / f"{PAGE_ID}.html"
            live_path.write_bytes(live_bytes)
            body = {
                "schema_id": "pcb-fab-package/source-observations", "schema_version": 1, "release_id": RELEASE,
                "profile_sha256": record["content_sha256"],
                "pages": [{"page_id": PAGE_ID, "source_url": page_url,
                           "stored_path": f"supplier/pages/{PAGE_ID}.html", "stored_sha256": stored_sha,
                           "live_path": f"out/fab/source-review/live/{PAGE_ID}.html",
                           "live_sha256": hashlib.sha256(live_bytes).hexdigest(), "retrieved": "2026-11-26"}],
                "observations": observations(override), "reviewer": "fixture reviewer",
                "statement": "Project-authored fixture statement.",
            }
            path = Path(td) / f"{name}.json"
            path.write_text(json.dumps(body, indent=2), encoding="utf-8")
            return path

        cases = [
            ("unchanged", stored.read_bytes(), None, 0, "unchanged"),
            ("harmless", stored.read_bytes() + b"<!-- fixture live copy -->\n", None, 0, "harmless"),
            ("material", stored.read_bytes(), "min_trace", 1, "material"),
        ]
        for name, live_bytes, override, want_code, want_decision in cases:
            obs = write_observations(name, live_bytes, override)
            # The destination must lie under the project root (PIO.confine). It must not exist yet.
            out = project / "out" / "fab" / f"review-{name}" / "REVIEW.json"
            code, text = run_cli(os.environ.get("PATH", ""), "review-source", "--project", str(project),
                                 "--profile", str(profile_path), "--release", RELEASE,
                                 "--observations", str(obs), "--reviewer", "fixture reviewer", "--out", str(out))
            expect(code == want_code, f"review-source ({name}): exit {code}. Expected {want_code}. Output: {text}")
            written = json.loads(out.read_text(encoding="utf-8"))
            expect(written["decision"] == want_decision,
                   f"review-source ({name}): decision {written['decision']}. Expected {want_decision}.")


def test_pcbway_corner_stop_unit():
    """The corner check stops with exit 2 for each PCBWay profile: no cutter diameter (R2)."""
    for pid in PCBWAY:
        try:
            workflow.corner_conditions(repo_profile(pid), {"corners": []})
        except workflow.Stop as err:
            expect(err.code == workflow.EXIT_UNSUPPORTED, f"{pid}: the stop exit is {err.code}.")
        else:
            raise AssertionError(f"{pid}: the corner check did not stop.")


def test_pcbway_via_fail_closed():
    """Blind, buried and via-in-pad spans fail. Through spans pass with the standard_through declaration."""
    def status(record, declaration, construction):
        measured = {"vias": [{"construction": construction}]}
        return workflow.via_condition(record, declaration, measured)["status"]

    for pid in PCBWAY:
        record = repo_profile(pid)
        expect(status(record, None, "blind") == "fail", f"{pid}: a blind span does not fail.")
        expect(status(record, None, "buried") == "fail", f"{pid}: a buried span does not fail.")
        expect(status(record, "filled_plated_via_in_pad", "through") == "fail",
               f"{pid}: the via-in-pad declaration on through spans does not fail.")
        expect(status(record, "standard_through", "through") == "pass",
               f"{pid}: through spans with standard_through do not pass.")


def test_pcbway_judge_boundaries():
    """The two-layer min_trace of 0.10 mm: 0.09 mm fails, 0.10 mm and 0.11 mm pass."""
    threshold = fab.limit_in_mm(repo_profile("pcbway-two-layer")["limits"]["min_trace"])
    expect(fab.judge("minimum", Fraction("0.09"), threshold) == "fail", "0.09 mm does not fail.")
    expect(fab.judge("minimum", Fraction("0.10"), threshold) == "pass", "0.10 mm does not pass.")
    expect(fab.judge("minimum", Fraction("0.11"), threshold) == "pass", "0.11 mm does not pass.")


def test_pcbway_fact_items_complete():
    """review.fact_items gives one fact for each limit and each extension except evidence_pages. No KeyError."""
    for pid in PCBWAY:
        record = repo_profile(pid)
        facts = review.fact_items(record)
        expected = set(record["limits"]) | (set(record["extensions"]) - {"evidence_pages"})
        expect(set(facts) == expected, f"{pid}: the facts differ from the limits and extensions.")


def test_pcbway_no_cutter_facts():
    """The profiles have no cutter, substrate or thickness fact. The notes list each missing value (R2)."""
    absent = ("process.outline_cutter_diameter", "process.cutout_cutter_diameter",
              "service.substrate", "service.finished_thickness_display_mm")
    for pid in PCBWAY:
        extensions = repo_profile(pid)["extensions"]
        for key in absent:
            expect(key not in extensions, f"{pid} has the fact {key}.")
        for key in absent + ("service.order_multiple",):
            expect(key in extensions["notes.not_stated"], f"{pid}: notes.not_stated does not list {key}.")


def test_pcbway_manual_text_limits():
    """Each PCBWay profile has the text limits of the page for copper, thickness and mask color (amendment I).
    Each is manual evidence, has no unit and no workflow row. The note names the control."""
    for pid in PCBWAY:
        record = repo_profile(pid)
        expected = set(TEXT_KEYS_COMMON) | ({"copper_weight_inner"} if pid == "pcbway-four-layer" else set())
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
