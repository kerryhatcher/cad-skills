# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Tests for the profile-driven supplier rules of pcb-fab-package (issue #8). Run with: uv run tests/test_pcb_fab_profile_rules.py

The tests start no container job. They use the fixture skill and temporary directories.
"""
import copy
import json
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from fab_fixture import fixture_skill  # noqa: E402

REPO = ROOT / "skills" / "pcb-fab-package"
SKILL = fixture_skill(REPO)
sys.path.insert(0, str(SKILL / "scripts"))
import fab  # noqa: E402
import validate as VAL  # noqa: E402
import workflow  # noqa: E402

OSHPARK = ("oshpark-single-layer", "oshpark-two-layer", "oshpark-two-layer-hhdc", "oshpark-four-layer",
           "oshpark-six-layer")
DATA_ONLY = ("jlcpcb-two-layer", "jlcpcb-four-layer", "pcbway-two-layer", "pcbway-four-layer")


def expect(condition, message):
    """Raise AssertionError with the message when the condition is false."""
    if not condition:
        raise AssertionError(message)


def repo_profile(pid):
    """Return the checked record of a repository profile. No page is read."""
    return VAL.load_record(REPO / "supplier" / "profiles" / f"{pid}.yaml")


def stop_of(fn, *args):
    """Return (code, message) for a workflow.Stop, or (None, None)."""
    try:
        fn(*args)
    except workflow.Stop as err:
        return err.code, str(err)
    return None, None


def profile_copy(pid="oshpark-two-layer"):
    return copy.deepcopy(repo_profile(pid))


# ------------------------------------------------------------------ step 2: the units of the supplier rules
def test_rules_text_units_equal():
    """The same length in in, mil and mm gives the same rule text."""
    for value, unit in ((0.005, "in"), (5, "mil"), (0.127, "mm")):
        profile = profile_copy()
        profile["limits"]["min_trace"] = dict(profile["limits"]["min_trace"], value=value, unit=unit)
        text = workflow.supplier_rules_text(profile)
        expect('(rule "supplier_min_trace" (constraint track_width (min 0.127mm)))' in text,
               f"The rule text for min_trace in {unit} is incorrect:\n{text}")


def test_rules_text_no_exponent():
    """A value in mm with a zero after the point gives no exponent in the rule text."""
    profile = profile_copy()
    profile["limits"]["edge_keepout"] = dict(profile["limits"]["edge_keepout"], value=10, unit="mm")
    text = workflow.supplier_rules_text(profile)
    expect("(min 10mm)" in text, f"The edge_keepout text is not 10mm:\n{text}")
    expect("E+" not in text, f"The rule text has an exponent:\n{text}")


def test_rules_text_unknown_unit():
    """A unit that is not mm, mil or in gives exit 2."""
    profile = profile_copy()
    profile["limits"]["min_trace"] = dict(profile["limits"]["min_trace"], unit="cm")
    code, _ = stop_of(workflow.supplier_rules_text, profile)
    expect(code == workflow.EXIT_UNSUPPORTED, f"The unit cm gives the code {code}, not 2.")


def test_rules_text_unknown_rule():
    """A kicad_dru key without a KiCad constraint gives exit 2, not KeyError."""
    profile = profile_copy()
    profile["division"]["kicad_dru"].append("min_thing")
    profile["limits"]["min_thing"] = copy.deepcopy(profile["limits"]["min_trace"])
    code, _ = stop_of(workflow.supplier_rules_text, profile)
    expect(code == workflow.EXIT_UNSUPPORTED, f"The unknown rule gives the code {code}, not 2.")


def test_rules_text_bad_value():
    """A rule value that is not a finite number greater than 0 gives exit 2."""
    for value in ("abc", "NaN", "Infinity", 0, -1):
        profile = profile_copy()
        profile["limits"]["min_trace"] = dict(profile["limits"]["min_trace"], value=value)
        code, _ = stop_of(workflow.supplier_rules_text, profile)
        expect(code == workflow.EXIT_UNSUPPORTED, f"The value {value!r} gives the code {code}, not 2.")


def test_unit_tables_agree():
    """The workflow and fab tables give the same factor for each unit."""
    expect(set(workflow.RULE_UNIT_MM) == set(fab.UNIT_MM), "The two unit tables have different units.")
    for unit in ("mm", "mil", "in"):
        expect(Fraction(workflow.RULE_UNIT_MM[unit]) == fab.UNIT_MM[unit],
               f"The factor of {unit} is not equal in the two unit tables.")


SILK = {"condition": "silk_line_min_short_text", "method": "manual_evidence", "mandatory": True,
        "status": "pending", "interpretation": "manual evidence is required before qualification"}


def finding(key):
    return {"condition": key, "method": "manual_evidence", "mandatory": False, "status": "finding",
            "interpretation": "recommendation: reported, never a failure"}


def legacy_mandatory(profile):
    """The mandatory names of the code before this part."""
    return set(sorted(profile["division"]["kicad_dru"])) | {
        "board_min_edge", "board_max_width", "board_max_height", "min_slot_size", "mask_web_min",
        "mask_web_min_top", "mask_web_min_bottom", "service.layers", "service.order_multiple",
        "silk_line_min_short_text", "service.via_construction_prohibited",
        "process.outline_tool_compatibility", "process.cutout_tool_compatibility"}


def manual_copy(kind):
    """A copy with the manual-evidence limit pad_to_silk_min of the given kind."""
    profile = profile_copy()
    profile["limits"]["pad_to_silk_min"] = {"kind": kind, "scope": "fabrication", "value_kind": "number",
                                             "value": 6, "unit": "mil"}
    profile["division"]["manual_evidence"].append("pad_to_silk_min")
    return profile


# ------------------------------------------------------------------ step 4: the conditions from the division
def test_oshpark_mandatory_unchanged():
    """The mandatory names of the five OSH Park profiles do not change."""
    for pid in OSHPARK:
        for record in (repo_profile(pid), fab.check_profile(SKILL / "supplier/profiles" / f"{pid}.yaml")):
            expect(workflow.mandatory_conditions(record) == legacy_mandatory(record),
                   f"{pid}: the mandatory names changed.")


def test_oshpark_optional_unchanged():
    """The optional tuple of the five OSH Park profiles does not change."""
    for pid in OSHPARK:
        expect(workflow.optional_conditions(repo_profile(pid)) == ("silk_line_recommended", "overlapping_drill_clearance"),
               f"{pid}: the optional names changed.")


def test_oshpark_manual_rows_unchanged():
    """The manual rows of the five OSH Park profiles do not change."""
    for pid in OSHPARK:
        expect(workflow.manual_rows(repo_profile(pid), SILK)
               == [SILK, finding("silk_line_recommended"), finding("overlapping_drill_clearance")],
               f"{pid}: the manual rows changed.")


def test_manual_minimum_is_pending():
    """A manual-evidence minimum without a procedure is a pending mandatory row."""
    profile = manual_copy("minimum")
    expect("pad_to_silk_min" in workflow.mandatory_conditions(profile), "The minimum is not mandatory.")
    expect("pad_to_silk_min" not in workflow.optional_conditions(profile), "The minimum is optional.")
    rows = workflow.manual_rows(profile, SILK)
    expect({"condition": "pad_to_silk_min", "method": "manual_evidence", "mandatory": True, "status": "pending",
            "interpretation": "Give manual evidence. The row stays pending until then."} in rows,
           f"The minimum row is not pending: {rows}")
    expect(workflow.rows_exit(workflow.manual_rows(profile, dict(SILK, status="pass"))) == workflow.EXIT_FAIL,
           "The pending row does not keep the result fail-closed.")


def test_manual_recommendation_is_optional():
    """A manual-evidence recommendation is an optional finding row."""
    profile = manual_copy("recommendation")
    expect("pad_to_silk_min" not in workflow.mandatory_conditions(profile), "The recommendation is mandatory.")
    expect("pad_to_silk_min" in workflow.optional_conditions(profile), "The recommendation is not optional.")
    rows = workflow.manual_rows(profile, SILK)
    expect(rows[0] == SILK and finding("pad_to_silk_min") in rows,
           f"The recommendation row is not after the silk row: {rows}")


def test_check_division_core_set():
    """Each profile must have every core limit, the silk minimum, and no unknown division name."""
    core = [("geometric_tests", name) for name in ("board_min_edge", "board_max_width", "board_max_height",
                                                   "min_slot_size", "mask_web_min")]
    core += [("kicad_dru", name) for name in ("min_trace", "min_space", "min_annular_ring", "min_drill",
                                              "edge_keepout")]
    for section, name in core:
        profile = profile_copy()
        profile["division"][section].remove(name)
        del profile["limits"][name]
        code, message = stop_of(workflow.check_division, profile)
        expect(code == workflow.EXIT_UNSUPPORTED and name in message,
               f"The missing {section} name {name} gives the code {code} and the message {message!r}.")
    profile = profile_copy()
    profile["division"]["manual_evidence"].remove("silk_line_min_short_text")
    del profile["limits"]["silk_line_min_short_text"]
    code, message = stop_of(workflow.check_division, profile)
    expect(code == workflow.EXIT_UNSUPPORTED and "silk_line_min_short_text" in message,
           f"The missing silk minimum gives the code {code} and the message {message!r}.")


def test_check_division_refuses():
    """check_division stops each division that the workflow cannot measure."""
    cases = []
    profile = profile_copy()
    profile["division"]["kicad_dru"].append("min_thing")
    profile["limits"]["min_thing"] = copy.deepcopy(profile["limits"]["min_trace"])
    cases.append((profile, "has no KiCad constraint"))
    profile = profile_copy()
    profile["division"]["kicad_dru"].append("fake_rule")
    profile["limits"]["fake_rule"] = copy.deepcopy(profile["limits"]["min_trace"])
    workflow.RULE_CONSTRAINT["fake_rule"] = "track_width"
    cases.append((profile, "has no DRC report keys"))
    profile = profile_copy()
    profile["division"]["geometric_tests"].append("extra_test")
    profile["limits"]["extra_test"] = copy.deepcopy(profile["limits"]["min_slot_size"])
    cases.append((profile, "has no workflow measurement"))
    profile = profile_copy()
    profile["division"]["project_settings"] = ["some_setting"]
    cases.append((profile, "cannot apply division.project_settings"))
    profile = manual_copy("requirement")
    cases.append((profile, "Use minimum, maximum or recommendation"))
    profile = profile_copy()
    profile["extensions"]["service.order_multiple"] = {"kind": "not_stated"}
    cases.append((profile, "The profile states no order multiple. The workflow cannot examine the order quantity."))
    try:
        for profile, wanted in cases:
            code, message = stop_of(workflow.check_division, profile)
            expect(code == workflow.EXIT_UNSUPPORTED and wanted in message,
                   f"The division gives the code {code} and the message {message!r}, not {wanted!r}.")
    finally:
        workflow.RULE_CONSTRAINT.pop("fake_rule", None)


def test_check_division_repository_profiles():
    """The OSH Park profiles pass. The data-only profiles stop at the order multiple."""
    for pid in OSHPARK:
        code, message = stop_of(workflow.check_division, repo_profile(pid))
        expect(code is None, f"{pid}: check_division gives the code {code} and the message {message!r}.")
    for pid in DATA_ONLY:
        code, message = stop_of(workflow.check_division, repo_profile(pid))
        expect(code == workflow.EXIT_UNSUPPORTED and "no order multiple" in message,
               f"{pid}: check_division gives the code {code} and the message {message!r}.")


def test_data_only_mandatory_names():
    """Each manual-evidence minimum of a data-only profile is mandatory. A recommendation is optional."""
    for pid in DATA_ONLY:
        profile = repo_profile(pid)
        for key in profile["division"]["manual_evidence"]:
            kind = profile["limits"][key]["kind"]
            if kind in ("minimum", "maximum"):
                expect(key in workflow.mandatory_conditions(profile), f"{pid}: {key} is not mandatory.")
            else:
                expect(key in workflow.optional_conditions(profile), f"{pid}: {key} is not optional.")
    expect("pth_hole_to_internal_copper" in workflow.mandatory_conditions(repo_profile("jlcpcb-four-layer")),
           "pth_hole_to_internal_copper is not mandatory for jlcpcb-four-layer.")
    expect("board_min_thickness" in workflow.mandatory_conditions(repo_profile("pcbway-two-layer")),
           "board_min_thickness is not mandatory for pcbway-two-layer.")


def test_validate_optional_rows_from_profile():
    """validate_supplier_result takes the optional names from the profile."""
    profile = manual_copy("recommendation")
    rows = [{"condition": name, "method": "x", "mandatory": True, "status": "pass"}
            for name in sorted(workflow.mandatory_conditions(profile))]
    rows += [finding(key) for key in workflow.optional_conditions(profile)]
    body = {"profile": profile["id"], "profile_sha256": profile["content_sha256"], "rows": rows, "exit": 0}
    result = dict(body, content_sha256=VAL.canonical_hash(body))
    expect(workflow.validate_supplier_result(result, profile) == result,
           "A recommendation row from the profile is refused.")
    other = repo_profile("oshpark-two-layer")
    body = {"profile": other["id"], "profile_sha256": other["content_sha256"], "rows": rows, "exit": 0}
    code, message = stop_of(workflow.validate_supplier_result, dict(body, content_sha256=VAL.canonical_hash(body)), other)
    expect(code == workflow.EXIT_FAIL and "is not a recommendation" in message,
           f"A recommendation row of another profile gives the code {code} and the message {message!r}.")


def test_commands_stop_before_container():
    """The design and supplier commands stop a bad division before any container job."""
    import test_pcb_fab_workflow as base
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        record = json.loads((SKILL / "supplier/profiles/oshpark-two-layer.yaml").read_text())
        record["division"]["geometric_tests"].remove("board_max_height")
        del record["limits"]["board_max_height"]
        record["content_sha256"] = fab.content_hash(record)
        bad = tmp / "bad.yaml"
        bad.write_text(json.dumps(record, indent=2) + "\n")
        fab.check_profile(bad)
        calls = []

        def no_container(*args, **kwargs):
            calls.append(args)
            raise AssertionError("a container job started")

        old_podman, old_runtime = workflow.podman, workflow.runtime_identity
        workflow.podman, workflow.runtime_identity = no_container, no_container
        try:
            project = base.fresh_project(tmp, "bad")
            code, message = stop_of(workflow.design, project, bad, project / "out/fab/design")
            expect(code == 2 and "board_max_height" in message and calls == [],
                   f"design gives the code {code} and the message {message!r}.")
            code, message = stop_of(workflow.supplier, project, bad, project / "out/fab/supplier",
                                    project / "out/fab/design")
            expect(code == 2 and "board_max_height" in message and calls == [],
                   f"supplier gives the code {code} and the message {message!r}.")
        finally:
            workflow.podman, workflow.runtime_identity = old_podman, old_runtime


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
