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
    for value, unit in (("abc", "mm"), ("NaN", "mm"), ("Infinity", "mm"), (0, "mm"), (-1, "mm"),
                        ("1/0", "in"), ("1/3", "in")):
        profile = profile_copy()
        profile["limits"]["min_trace"] = dict(profile["limits"]["min_trace"], value=value, unit=unit)
        code, message = stop_of(workflow.supplier_rules_text, profile)
        expect(code == workflow.EXIT_UNSUPPORTED,
               f"The value {value!r} in {unit} gives the code {code} and the message {message!r}, not 2.")


def test_rules_text_exact_28_digits():
    """A value with 28 significant digits converts exactly to millimeters."""
    profile = profile_copy()
    profile["limits"]["min_trace"] = dict(profile["limits"]["min_trace"],
                                          value="0.1234567890123456789012345678", unit="in")
    text = workflow.supplier_rules_text(profile)
    expect('(rule "supplier_min_trace" (constraint track_width (min 3.13580244091358024409135802212mm)))' in text,
           f"The 28-digit rule text is incorrect:\n{text}")


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
    for key in ("min_trace", "edge_keepout", "mask_web_min"):
        for value in ("abc", "nan", "inf", 0, -1, "1/0", "1/3"):
            profile = profile_copy()
            profile["limits"][key] = dict(profile["limits"][key], value=value)
            cases.append((profile, f"the limit {key} must have a finite value greater than 0"))
    for value in ("abc", "nan", "inf", None, 0, -1, "1/3"):
        profile = profile_copy()
        profile["limits"]["silk_line_min_short_text"] = dict(profile["limits"]["silk_line_min_short_text"],
                                                             value=value)
        cases.append((profile, "the limit silk_line_min_short_text must have a finite value greater than 0"))
        for kind in ("minimum", "maximum"):
            profile = manual_copy(kind)
            profile["limits"]["pad_to_silk_min"]["value"] = value
            cases.append((profile, "the limit pad_to_silk_min must have a finite value greater than 0"))
    try:
        for profile, wanted in cases:
            code, message = stop_of(workflow.check_division, profile)
            expect(code == workflow.EXIT_UNSUPPORTED and wanted in message,
                   f"The division gives the code {code} and the message {message!r}, not {wanted!r}.")
    finally:
        workflow.RULE_CONSTRAINT.pop("fake_rule", None)


def test_check_division_manual_recommendation_value():
    """check_division does not examine the value of a manual recommendation."""
    profile = manual_copy("recommendation")
    profile["limits"]["pad_to_silk_min"]["value"] = 0
    code, message = stop_of(workflow.check_division, profile)
    expect(code is None, f"The recommendation with the value 0 gives the code {code} and the message {message!r}.")


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
    """The design and supplier commands stop an incorrect division before any container job."""
    import test_pcb_fab_workflow as base
    with tempfile.TemporaryDirectory() as directory:
        tmp = Path(directory)
        records = {}
        record = json.loads((SKILL / "supplier/profiles/oshpark-two-layer.yaml").read_text())
        record["division"]["geometric_tests"].remove("board_max_height")
        del record["limits"]["board_max_height"]
        record["content_sha256"] = fab.content_hash(record)
        records["missing"] = record
        record = json.loads((SKILL / "supplier/profiles/oshpark-two-layer.yaml").read_text())
        record["limits"]["min_trace"] = dict(record["limits"]["min_trace"], value="abc")
        record["content_sha256"] = fab.content_hash(record)
        records["value"] = record
        bad = {}
        for label, record in records.items():
            bad[label] = tmp / f"{label}.yaml"
            bad[label].write_text(json.dumps(record, indent=2) + "\n")
            fab.check_profile(bad[label])
        calls = []

        def no_container(*args, **kwargs):
            calls.append(args)
            raise AssertionError("a container job started")

        old_podman, old_runtime = workflow.podman, workflow.runtime_identity
        workflow.podman, workflow.runtime_identity = no_container, no_container
        try:
            project = base.fresh_project(tmp, "bad")
            for label, name in (("missing", "board_max_height"), ("value", "min_trace")):
                code, message = stop_of(workflow.design, project, bad[label], project / "out/fab/design")
                expect(code == 2 and name in message and calls == [],
                       f"design for {label} gives the code {code} and the message {message!r}.")
                code, message = stop_of(workflow.supplier, project, bad[label], project / "out/fab/supplier",
                                        project / "out/fab/design")
                expect(code == 2 and name in message and calls == [],
                       f"supplier for {label} gives the code {code} and the message {message!r}.")
        finally:
            workflow.podman, workflow.runtime_identity = old_podman, old_runtime


def _board_for(profile, *, thickness_mm=1.6, outer_oz=1, inner_oz=None, mask_color="green", substrate="FR4",
               supplier_id=None, profile_sha=None):
    """Return a minimal board record matching the given profile and fabrication options."""
    fab_ext = {"via_process": "standard_through"}
    if outer_oz is not None:
        fab_ext["copper_outer_oz"] = outer_oz
    if inner_oz is not None:
        fab_ext["copper_inner_oz"] = inner_oz
    if mask_color is not None:
        fab_ext["mask_color"] = mask_color
    if substrate is not None:
        fab_ext["substrate"] = substrate
    return {
        "supplier": {"id": supplier_id or profile["id"],
                     "profile_sha256": profile_sha or profile["content_sha256"]},
        "mechanical": {"width_mm": 40.0, "height_mm": 25.0, "thickness_mm": thickness_mm},
        "extensions": {"fabrication": fab_ext},
    }


def _row_map(rows):
    return {r["condition"]: r for r in rows}


def test_fabrication_option_conditions():
    """Structured options compare copper weight, board thickness and mask color with board.yaml and supplier.yaml."""
    expect(workflow.fabrication_option_conditions(repo_profile("oshpark-two-layer"), {}) == [],
           "OSH Park profile must return no option rows.")
    for pid, inner in (("jlcpcb-two-layer", None), ("jlcpcb-four-layer", 0.5),
                       ("pcbway-two-layer", None), ("pcbway-four-layer", 1)):
        prof = repo_profile(pid)
        board = _board_for(prof, inner_oz=inner)
        rows = _row_map(workflow.fabrication_option_conditions(prof, board, prof))
        expect(all(rows[k]["status"] == "pass" for k in workflow.FABRICATION_OPTION_ROWS),
               f"{pid}: valid options did not pass: {rows}")
        # Pending when outer copper or mask color is absent or unconfirmed.
        pending = _row_map(workflow.fabrication_option_conditions(
            prof, _board_for(prof, outer_oz=None, inner_oz=inner, mask_color="unconfirmed"), prof))
        expect(pending["service.copper_weight"]["status"] == "pending"
               and pending["service.mask_color"]["status"] == "pending",
               f"{pid}: missing or unconfirmed declarations did not stay pending: {pending}")
        # Wrong copper weight fails.
        bad_cu = _row_map(workflow.fabrication_option_conditions(prof, _board_for(prof, outer_oz=2, inner_oz=inner), prof))
        expect(bad_cu["service.copper_weight"]["status"] == "fail", f"{pid}: 2 oz outer copper did not fail.")
        # Wrong mask color fails.
        bad_color = _row_map(workflow.fabrication_option_conditions(
            prof, _board_for(prof, inner_oz=inner, mask_color="orange"), prof))
        expect(bad_color["service.mask_color"]["status"] == "fail", f"{pid}: orange mask color did not fail.")
        # Wrong board thickness fails.
        bad_thick = _row_map(workflow.fabrication_option_conditions(
            prof, _board_for(prof, thickness_mm=1.5, inner_oz=inner), prof))
        expect(bad_thick["service.board_thickness"]["status"] == "fail", f"{pid}: 1.5 mm thickness did not fail.")
        # Mismatched supplier.yaml or board.yaml supplier stops with EXIT_FAIL.
        other_sup = copy.deepcopy(prof)
        other_sup["fabrication_options"]["mask_color"]["allowed"].append("orange")
        code, _ = stop_of(workflow.fabrication_option_conditions, prof, board, other_sup)
        expect(code == workflow.EXIT_FAIL, f"{pid}: mismatched supplier.yaml gave {code}, not 1.")
        code, _ = stop_of(workflow.fabrication_option_conditions, prof,
                          _board_for(prof, inner_oz=inner, profile_sha="0" * 64), prof)
        expect(code == workflow.EXIT_FAIL, f"{pid}: mismatched board.yaml supplier hash gave {code}, not 1.")
        # Invalid declaration types stop with EXIT_UNSUPPORTED.
        code, _ = stop_of(workflow.fabrication_option_conditions, prof,
                          _board_for(prof, outer_oz=True, inner_oz=inner), prof)
        expect(code == workflow.EXIT_UNSUPPORTED, f"{pid}: bool copper weight gave {code}, not 2.")
        code, _ = stop_of(workflow.fabrication_option_conditions, prof,
                          _board_for(prof, inner_oz=inner, mask_color=123), prof)
        expect(code == workflow.EXIT_UNSUPPORTED, f"{pid}: non-string mask color gave {code}, not 2.")

    # JLCPCB 0.4 mm thickness is allowed by list but below 0.6 mm manual review threshold -> pending.
    jlc2 = repo_profile("jlcpcb-two-layer")
    thin = _row_map(workflow.fabrication_option_conditions(jlc2, _board_for(jlc2, thickness_mm=0.4), jlc2))
    expect(thin["service.board_thickness"]["status"] == "pending", f"0.4 mm JLCPCB did not stay pending: {thin}")
    # Mask bridge mismatch: green mask with weakened mask_web_min < bridge_min_by_color[color] fails.
    weak = copy.deepcopy(jlc2)
    weak["limits"]["mask_web_min"]["value"] = 0.08
    weak_rows = _row_map(workflow.fabrication_option_conditions(weak, _board_for(weak, mask_color="green"), weak))
    expect(weak_rows["service.mask_color"]["status"] == "fail", "Mask bridge mismatch did not fail.")


def test_optional_geometric_rows():
    """Optional geometric_tests check board_min_thickness, min_plated_slot_size, via_hole_to_hole_min and pad_hole_to_hole_min."""
    prof = repo_profile("pcbway-two-layer")
    # PCBWay 2L: board_min_thickness 0.3 mm, min_plated_slot_size 0.5 mm, via_hole_to_hole_min 11 mil (0.2794 mm), pad_hole_to_hole_min 16 mil (0.4064 mm)
    inv_pass = {
        "slots": [{"attr": "pth", "minor_mm": 0.5}, {"attr": "npth", "minor_mm": 0.4}],
        "holes": [
            {"kind": "via", "x": 0.0, "y": 0.0, "diameter": 0.3},
            {"kind": "via", "x": 0.5794, "y": 0.0, "diameter": 0.3},  # center 0.5794 - 0.3 = 0.2794 mm == 11 mil
            {"kind": "pad", "x": 10.0, "y": 0.0, "diameter": 1.0},
            {"kind": "pad", "x": 11.4064, "y": 0.0, "diameter": 1.0},  # edge gap 0.4064 mm == 16 mil
        ],
    }
    rows = _row_map(workflow.optional_geometric_rows(prof, inv_pass, _board_for(prof, thickness_mm=0.3), slot_code=0))
    expect(all(rows[k]["status"] == "pass" for k in ("board_min_thickness", "min_plated_slot_size",
                                                      "via_hole_to_hole_min", "pad_hole_to_hole_min")),
           f"Boundary passing cases failed: {rows}")
    inv_fail = {
        "slots": [{"attr": "pth", "minor_mm": 0.499}],
        "holes": [
            {"kind": "via", "x": 0.0, "y": 0.0, "diameter": 0.3},
            {"kind": "via", "x": 0.579399, "y": 0.0, "diameter": 0.3},
            {"kind": "pad", "x": 10.0, "y": 0.0, "diameter": 1.0},
            {"kind": "pad", "x": 10.0, "y": 0.0, "diameter": 1.0},  # coincident
        ],
    }
    rows_fail = _row_map(workflow.optional_geometric_rows(prof, inv_fail, _board_for(prof, thickness_mm=0.29), slot_code=0))
    expect(all(rows_fail[k]["status"] == "fail" for k in ("board_min_thickness", "min_plated_slot_size",
                                                           "via_hole_to_hole_min", "pad_hole_to_hole_min")),
           f"Failing cases did not fail: {rows_fail}")


def test_extra_manual_procedures_and_rows():
    """Manual procedures check board_sha256 and optional silk_gerber_sha256 and populate manual_rows."""
    import hashlib
    prof = repo_profile("jlcpcb-four-layer")
    board_bytes = b"board-bytes"
    silk_bytes = b"silk-bytes"
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        proj = tmp / "project"
        out = proj / "out/fab/supplier"
        out.mkdir(parents=True)
        art = proj / "out/fab/manual/check.txt"
        art.parent.mkdir(parents=True)
        art.write_bytes(b"manual check artifact\n")
        art_sha = hashlib.sha256(art.read_bytes()).hexdigest()
        board_sha = hashlib.sha256(board_bytes).hexdigest()
        silk_sha = hashlib.sha256(silk_bytes).hexdigest()
        outputs = workflow.Outputs(proj, out)

        def write_rec(name, cond, inputs, result="pass"):
            p = tmp / f"{name}.json"
            p.write_text(json.dumps({
                "schema_id": "pcb-fab-package/manual-evidence", "schema_version": 1, "condition": cond,
                "result": result, "procedure": "Checked manually.", "artifact_path": "out/fab/manual/check.txt",
                "artifact_sha256": art_sha, "inputs": inputs, "reviewer": "R. Reviewer", "statement": "Checked.",
            }))
            return p

        p_pth = write_rec("pth", "pth_hole_to_internal_copper", {"board_sha256": board_sha}, "pass")
        info, status, interp = workflow.check_manual_record(
            p_pth, p_pth.read_bytes(), art.read_bytes(), board_bytes, silk_bytes,
            "pth_hole_to_internal_copper", out, outputs)
        expect(status == "pass" and info["path"] == "manual-pth_hole_to_internal_copper-evidence.json",
               f"Unexpected manual record result: {info}, {status}")
        rows = _row_map(workflow.manual_rows(
            prof, SILK, {"pth_hole_to_internal_copper": {"condition": "pth_hole_to_internal_copper",
                                                         "method": "manual_evidence", "mandatory": True,
                                                         "status": status, "interpretation": interp}}))
        expect(rows["pth_hole_to_internal_copper"]["status"] == "pass"
               and rows["silk_text_min_height"]["status"] == "pending",
               f"manual_rows did not keep unspecified conditions pending: {rows}")
        # Wrong input keys (including silk_gerber_sha256 for pth_hole_to_internal_copper) must stop.
        bad_keys = write_rec("badkeys", "pth_hole_to_internal_copper",
                             {"board_sha256": board_sha, "silk_gerber_sha256": silk_sha})
        code, _ = stop_of(workflow.check_manual_record, bad_keys, bad_keys.read_bytes(), art.read_bytes(),
                          board_bytes, silk_bytes, "pth_hole_to_internal_copper", out, outputs)
        expect(code == workflow.EXIT_FAIL, f"Wrong manual input keys gave {code}, not 1.")
        # Stale board hash must stop for silk_text_min_height.
        stale = write_rec("stale", "silk_text_min_height", {"board_sha256": "0" * 64, "silk_gerber_sha256": silk_sha})
        code, _ = stop_of(workflow.check_manual_record, stale, stale.read_bytes(), art.read_bytes(),
                          board_bytes, silk_bytes, "silk_text_min_height", out, outputs)
        expect(code == workflow.EXIT_FAIL, f"Stale manual record gave {code}, not 1.")


def test_drawing_facts_with_board_record():
    """drawing_facts reads substrate, thickness and copper from board.yaml when the profile omits them."""
    inv = {"outline": {"width": 40.0, "height": 25.0}, "holes": [], "slots": [], "copper_layers": ["F.Cu", "B.Cu"]}
    for pid, inner in (("jlcpcb-two-layer", None), ("pcbway-four-layer", 2)):
        prof = repo_profile(pid)
        board = _board_for(prof, thickness_mm=1.6, outer_oz=1, inner_oz=inner, substrate="FR4 TG155")
        facts = fab.drawing_facts(inv, prof, b"board", "r1", b"prof", board_record=board)
        expect(facts["profile"]["substrate"] == "FR4 TG155"
               and facts["profile"]["finished_thickness_mm"] == 1.6,
               f"{pid}: unexpected drawing facts {facts['profile']}")
        if inner is not None:
            expect(facts["profile"]["copper"] == "1 oz outer, 2 oz inner",
                   f"{pid}: unexpected copper string {facts['profile']['copper']!r}")
        pdf = fab.drawing_pdf(facts)
        expect(pdf.startswith(b"%PDF-1.4\n"), f"{pid}: drawing_pdf did not build a PDF.")
        # Missing board_record or missing substrate refuses with fab.Invalid.
        for bad_board in (None, _board_for(prof, inner_oz=inner, substrate=None),
                          _board_for(prof, thickness_mm=1.5, inner_oz=inner)):
            try:
                fab.drawing_facts(inv, prof, b"board", "r1", b"prof", board_record=bad_board)
            except fab.Invalid:
                pass
            else:
                raise AssertionError(f"{pid}: invalid board_record passed drawing_facts.")


def test_check_profile_fabrication_options():
    """fab.check_profile refuses inconsistent fabrication_options."""
    base = json.loads((SKILL / "supplier/profiles/pcbway-four-layer.yaml").read_text())
    with tempfile.TemporaryDirectory() as td:
        tmp = Path(td)
        cases = [
            lambda r: r["fabrication_options"]["copper_weight"].pop("inner_oz"),
            lambda r: r["fabrication_options"]["board_thickness"].update(min_mm=0.5),
            lambda r: r["limits"]["mask_web_min"].update(value=3.0),
        ]
        for idx, mutate in enumerate(cases):
            rec = copy.deepcopy(base)
            mutate(rec)
            rec["content_sha256"] = fab.content_hash(rec)
            p = tmp / f"bad-{idx}.yaml"
            p.write_text(json.dumps(rec))
            try:
                fab.check_profile(p)
            except fab.Invalid:
                pass
            else:
                raise AssertionError(f"Case {idx} passed check_profile.")


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
