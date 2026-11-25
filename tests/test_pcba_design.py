# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "openpyxl==3.1.5", "pyyaml==6.0.3", "xlrd==2.0.1"]
# ///
"""Focused tests for the pcba-design neutral step (sections 4 to 8 of the B9/B10 interface).

  uv run tests/test_pcba_design.py

Each test copies the fixture project to a new temporary directory and edits the copy.
Expected values are written by hand from the fixture definition. The tool under test never
computes them. A test passes only when the exit code, the refusal code, and the values match.
"""

from __future__ import annotations

import datetime as dt
import hashlib
import importlib
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests" / "fixtures" / "pcba-design" / "project"
PCBA = ROOT / "skills" / "pcba-design" / "scripts" / "pcba.py"
AS_OF = "2026-11-15"


def copy_project(tmp: Path) -> Path:
    dest = tmp / "project"
    shutil.copytree(FIXTURE, dest)
    return dest


def run_neutral(project: Path, variant: str = "base", board: str = "board.kicad_pcb"):
    cmd = ["uv", "run", str(PCBA), "neutral", "--project", str(project), "--board", board,
           "--variant", variant, "--as-of", AS_OF]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return proc.returncode, proc.stdout


def refusal_code(stdout: str) -> str:
    data = json.loads(stdout)
    return data["findings"][0]["code"]


def edit(path: Path, old: str, new: str) -> None:
    text = path.read_text(encoding="utf-8")
    if text.count(old) != 1:
        raise AssertionError(f"Fixture edit anchor must occur once in {path.name}: {old!r}")
    path.write_text(text.replace(old, new), encoding="utf-8")


def result(project: Path) -> dict:
    return json.loads((project / "out" / "pcba" / "assembly-neutral.json").read_text(encoding="utf-8"))


def rows_by_ref(data: dict) -> dict:
    return {row["reference"]: row for row in data["rows"]}


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


# --------------------------------------------------------------------------- accepted paths


def test_base_rows_match_board_and_sides():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        code, _ = run_neutral(project)
        expect(code == 0, f"base variant must pass, got exit {code}")
        rows = rows_by_ref(result(project))
        # Hand-written from the fixture board: side, x, y, source rotation, and normalized rotation.
        spec = {
            "R1": ("top", 10.0, 10.0, 0.0), "R2": ("top", 20.0, 10.0, 90.0),
            "R3": ("top", 30.0, 10.0, 180.0), "R4": ("top", 40.0, 10.0, 270.0),
            "D1": ("top", 10.0, 20.0, 0.0), "D2": ("bottom", 20.0, 20.0, 90.0),
            "D3": ("bottom", 30.0, 20.0, 180.0), "D4": ("bottom", 40.0, 20.0, 270.0),
        }
        for ref, (side, x, y, angle) in spec.items():
            row = rows[ref]
            expect(row["side"] == side, f"{ref} side is {row['side']}, expected {side}")
            expect((row["x_mm"], row["y_mm"]) == (x, y), f"{ref} position differs")
            expect(row["source_rotation_deg"] == angle and row["rotation_deg"] == angle,
                   f"{ref} rotation differs")
        expect(rows["J1"]["installation_method"] == "hand_installed", "J1 must be hand installed")
        expect(rows["J1"]["variant_state"] == "populate", "J1 must stay populate")
        expect(rows["TP1"]["variant_state"] == "exclude_from_assembly", "TP1 must be excluded")
        expect(rows["TP1"]["part_path"] == "components/testpoint.yaml", "TP1 keeps its part path")
        expect(rows["TP1"]["per_board_quantity"] == 0, "excluded rows have quantity 0")
        expect(rows["MH1"]["reason"] == "mechanical" and rows["MH1"]["part_path"] is None,
               "MH1 is a mechanical neutral row with no part")


def test_rotation_normalization_keeps_source():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        edit(project / "board.kicad_pcb", "(at 40 10 270)", "(at 40 10 -90)")
        code, _ = run_neutral(project)
        expect(code == 0, f"rotation -90 must pass, got exit {code}")
        row = rows_by_ref(result(project))["R4"]
        expect(row["source_rotation_deg"] == -90.0, "source rotation must stay -90")
        expect(row["rotation_deg"] == 270.0, "normalized rotation of -90 must be 270")


def test_bom_groups_base_variant():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        code, _ = run_neutral(project)
        expect(code == 0, f"base variant must pass, got exit {code}")
        groups = {(g["mpn"], g["installation_method"]): g for g in result(project)["bom_groups"]}
        resistor = groups[("EX-R-0603-10K", "automatic")]
        expect(resistor["references"] == ["R1", "R2", "R3", "R4"], "resistor group references")
        expect(resistor["quantity_per_board"] == 4 and resistor["board_quantity"] == 5, "resistor counts")
        expect(resistor["order_quantity"] == 20, "order quantity is per board times board quantity")
        led = groups[("EX-LED-0603-G", "automatic")]
        expect(led["references"] == ["D1", "D2", "D3", "D4"] and led["order_quantity"] == 20, "LED group")
        header = groups[("EX-HDR-1X02", "hand_installed")]
        expect(header["references"] == ["J1"], "hand installed header stays in the neutral BOM")
        expect(header["order_quantity"] == 5, "hand installed populated row counts in demand")
        expect(len(result(project)["bom_groups"]) == 4, "base variant has exactly four BOM groups")


def test_no_led_variant_splits_dnp_from_populated():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        edit(project / "board.yaml", "variant: base", "variant: no-led")
        code, _ = run_neutral(project, variant="no-led")
        expect(code == 0, f"no-led variant must pass, got exit {code}")
        data = result(project)
        groups = [(g["mpn"], g["variant_state"], tuple(g["references"]), g["order_quantity"])
                  for g in data["bom_groups"] if g["mpn"] == "EX-LED-0603-G"]
        expect(("EX-LED-0603-G", "dnp", ("D1", "D2"), 0) in groups, "DNP LED row is separate with zero order")
        expect(("EX-LED-0603-G", "populate", ("D3",), 5) in groups, "populated LED row is separate")
        rows = rows_by_ref(data)
        expect(rows["D4"]["variant_state"] == "exclude_from_assembly", "D4 is excluded in no-led")


# --------------------------------------------------------------------------- stock (section 8)


def test_stock_statuses_base_variant():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        code, _ = run_neutral(project)
        expect(code == 0, f"base variant must pass, got exit {code}")
        stock = {s["mpn"]: s for s in result(project)["stock"]}
        expect(stock["EX-R-0603-10K"]["status"] == "pass" and stock["EX-R-0603-10K"]["age_days"] == 14,
               "resistor: known stock, age 14 within 30 days")
        led = stock["EX-LED-0603-G"]
        expect(led["status"] == "fail", "LED: quantity 10 is below demand 20 and the date is stale")
        expect(set(led["reasons"]) == {"stock_below_demand", "stock_stale"}, f"LED reasons {led['reasons']}")
        expect(stock["EX-C-0603-100N"]["status"] == "unconfirmed", "capacitor: unknown stock is unconfirmed")
        expect(stock["EX-HDR-1X02"]["status"] == "unconfirmed", "header: nrnd lifecycle is unconfirmed")
        expect("EX-TP-D10" not in stock, "excluded parts have no stock demand")


def test_no_age_limit_skips_staleness():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        edit(project / "board.yaml", "max_age_days: 30", "max_age_days: no_age_limit")
        code, _ = run_neutral(project)
        expect(code == 0, f"no_age_limit must pass, got exit {code}")
        led = next(s for s in result(project)["stock"] if s["mpn"] == "EX-LED-0603-G")
        expect("stock_stale" not in led["reasons"], "no_age_limit must not mark stale")
        expect(led["age_days"] == 75, "age is still recorded as a dated observation")


# --------------------------------------------------------------------------- refusals


def expect_refusal(name, mutate, code_expected, variant="base", board_variant=None):
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        mutate(project)
        code, stdout = run_neutral(project, variant=variant)
        expect(code == 1, f"{name}: expected refusal exit 1, got {code}")
        got = refusal_code(stdout)
        expect(got in code_expected, f"{name}: refusal code {got}, expected one of {code_expected}")
        expect(not (project / "out").exists(), f"{name}: a refusal must write nothing")


def test_refuse_missing_map_entry():
    expect_refusal("missing map entry", lambda p: edit(
        p / "components" / "parts-map.yaml", "  R2:\n    part: components/resistor-10k.yaml\n", ""),
        ["map.missing_entry"])


def test_refuse_missing_mechanical_exclusion_entry():
    expect_refusal("missing exclusion entry", lambda p: edit(
        p / "components" / "parts-map.yaml", "  MH1:\n    mechanical: true\n", ""),
        ["map.missing_exclusion_entry"])


def test_refuse_duplicate_board_reference():
    expect_refusal("duplicate reference", lambda p: edit(
        p / "board.kicad_pcb", '(property "Reference" "D2")', '(property "Reference" "R1")'),
        ["board.duplicate_reference"])


def test_refuse_variant_reference_missing_on_board():
    expect_refusal("missing board reference", lambda p: edit(
        p / "board.kicad_pcb", '(property "Reference" "D4")', '(property "Reference" "D9")'),
        ["board.missing_reference", "map.unknown_reference"])


def test_refuse_unlisted_board_reference():
    def add(p):
        text = (p / "board.kicad_pcb").read_text(encoding="utf-8")
        extra = ('  (footprint "Resistor_SMD:R_0603_1608Metric"\n    (layer "F.Cu")\n    (at 60 10 0)\n'
                 '    (property "Reference" "X1")\n    (property "Value" "10k")\n  )\n')
        (p / "board.kicad_pcb").write_text(text.rstrip()[:-1] + extra + ")\n", encoding="utf-8")
    expect_refusal("unlisted reference", add, ["variant.unlisted_reference"])


def test_refuse_map_path_escape():
    expect_refusal("map path escape", lambda p: edit(
        p / "components" / "parts-map.yaml", "  R1:\n    part: components/resistor-10k.yaml", "  R1:\n    part: components/../resistor-10k.yaml"),
        ["map.path_escape"])


def test_refuse_unknown_map_key():
    expect_refusal("unknown map key", lambda p: edit(
        p / "components" / "parts-map.yaml", "schema_version: \"1.0\"\n", "schema_version: \"1.0\"\nextra: 1\n"),
        ["map.schema"])


def test_refuse_unused_map_entry():
    expect_refusal("unused map entry", lambda p: edit(
        p / "components" / "parts-map.yaml", "  MH1:\n", "  X9:\n    mechanical: true\n  MH1:\n"),
        ["map.unused_entry", "map.unknown_reference"])


def test_refuse_mechanical_entry_that_is_populated():
    expect_refusal("mechanical populated", lambda p: edit(
        p / "variants.yaml", "      MH1: exclude_from_assembly\n    hand_installed:\n      - reference: J1\n        reason: The connector is soldered by hand after assembly.\n  - id: no-led",
        "      MH1: populate\n    hand_installed:\n      - reference: J1\n        reason: The connector is soldered by hand after assembly.\n  - id: no-led"),
        ["map.mechanical_used"])


def test_refuse_hand_installed_reference_not_populated():
    expect_refusal("hand installed not populate", lambda p: edit(
        p / "variants.yaml", "      C1: populate\n      J1: populate\n      TP1: exclude_from_assembly\n      MH1: exclude_from_assembly\n    hand_installed:\n      - reference: J1\n        reason: The connector is soldered by hand after assembly.\n  - id: no-led",
        "      C1: populate\n      J1: dnp\n      TP1: exclude_from_assembly\n      MH1: exclude_from_assembly\n    hand_installed:\n      - reference: J1\n        reason: The connector is soldered by hand after assembly.\n  - id: no-led"),
        ["variant.hand_installed_state"])


def test_refuse_footprint_mismatch():
    expect_refusal("footprint mismatch", lambda p: edit(
        p / "components" / "resistor-10k.yaml", "footprint: Resistor_SMD:R_0603_1608Metric",
        "footprint: Resistor_SMD:R_0402_1005Metric"),
        ["part.footprint_mismatch"])


def test_refuse_missing_stock_policy():
    expect_refusal("missing stock policy", lambda p: edit(
        p / "board.yaml", "extensions:\n  pcba:\n    stock:\n      max_age_days: 30\n", ""),
        ["stock.policy_missing"])


def test_refuse_board_variant_mismatch():
    expect_refusal("board variant mismatch", lambda p: None, ["variant.board_mismatch"], variant="no-led")


# --------------------------------------------------------------------------- determinism and hashes


def test_output_is_deterministic_and_hash_bound():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        run_neutral(project)
        first = (project / "out" / "pcba" / "assembly-neutral.json").read_bytes()
        run_neutral(project)
        second = (project / "out" / "pcba" / "assembly-neutral.json").read_bytes()
        expect(first == second, "two runs on the same inputs must give the same bytes")
        data = json.loads(first)
        for item in data["inputs"]:
            raw = (project / item["path"]).read_bytes()
            expect(hashlib.sha256(raw).hexdigest() == item["sha256"], f"hash of {item['path']} differs")


# --------------------------------------------------------------------------- correction batch


def run_full(project: Path, board: str = "board.kicad_pcb", out: str | None = None, variant: str = "base"):
    cmd = ["uv", "run", str(PCBA), "neutral", "--project", str(project), "--board", board,
           "--variant", variant, "--as-of", AS_OF]
    if out is not None:
        cmd += ["--out", out]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return proc.returncode, proc.stdout, proc.stderr


def file_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_module():
    spec = importlib.util.spec_from_file_location("pcba_under_test", PCBA)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_symlink_outside_components_refused():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        comp = project / "components"
        (project / "outside.yaml").write_bytes((comp / "resistor-10k.yaml").read_bytes())
        (comp / "resistor-10k.yaml").unlink()
        os.symlink("../outside.yaml", comp / "resistor-10k.yaml")
        code, stdout, _ = run_full(project)
        expect(code == 1, f"symlink leaving components must refuse, got exit {code}")
        expect(refusal_code(stdout) == "map.path_escape", f"refusal code {refusal_code(stdout)}")
        expect(not (project / "out").exists(), "a refusal writes nothing")


def test_symlink_inside_components_resolves_to_one_file():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        comp = project / "components"
        os.symlink("resistor-10k.yaml", comp / "resistor-alias.yaml")
        edit(comp / "parts-map.yaml", "  R1:\n    part: components/resistor-10k.yaml",
             "  R1:\n    part: components/resistor-alias.yaml")
        code, _, _ = run_full(project)
        expect(code == 0, f"a link inside components must pass, got exit {code}")
        data = result(project)
        expect(rows_by_ref(data)["R1"]["part_path"] == "components/resistor-10k.yaml",
               "the row records the resolved project-relative path")
        paths = [i["path"] for i in data["inputs"] if i["role"] == "parts"]
        expect(paths.count("components/resistor-10k.yaml") == 1 and "components/resistor-alias.yaml" not in paths,
               f"one snapshot per resolved file, got {paths}")


def test_output_aliasing_board_record_refused_and_input_kept():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        before = file_sha(project / "board.yaml")
        code, stdout, _ = run_full(project, out="board.yaml")
        expect(code == 1 and refusal_code(stdout) == "output.aliases_input", f"got {code} {stdout[:120]}")
        expect(file_sha(project / "board.yaml") == before, "the input bytes are unchanged")


def test_output_hard_link_to_input_refused():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        (project / "out" / "pcba").mkdir(parents=True)
        os.link(project / "board.yaml", project / "out" / "pcba" / "assembly-neutral.json")
        before = file_sha(project / "board.yaml")
        code, stdout, _ = run_full(project)
        expect(code == 1 and refusal_code(stdout) == "output.aliases_input", f"got {code} {stdout[:120]}")
        expect(file_sha(project / "board.yaml") == before, "the hard-linked input is unchanged")


def test_input_changed_before_write_refused():
    mod = load_module()
    real_check = mod.check_output_alias
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))

        def tamper(target, snapshots, out_rel):
            led = project / "components" / "led-green.yaml"
            led.write_text(led.read_text(encoding="utf-8") + "\n# changed after capture\n", encoding="utf-8")
            return real_check(target, snapshots, out_rel)

        mod.check_output_alias = tamper
        try:
            try:
                mod.build(project, "board.kicad_pcb", "base", dt.date(2026, 11, 15),
                          "out/pcba/assembly-neutral.json")
                raise AssertionError("a changed input must refuse")
            except mod.Refused as refusal:
                expect(refusal.finding["code"] == "input.changed", f"code {refusal.finding['code']}")
        finally:
            mod.check_output_alias = real_check
        expect(not (project / "out").exists(), "a refusal writes nothing")


def test_high_precision_tokens_kept_exactly():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        edit(project / "board.kicad_pcb", "(at 10 10 0)", "(at 10.123456789012345678 10 0)")
        code, _, _ = run_full(project)
        expect(code == 0, f"high precision must pass, got exit {code}")
        row = rows_by_ref(result(project))["R1"]
        expect(row["source_tokens"] == {"x": "10.123456789012345678", "y": "10", "angle": "0"},
               f"tokens {row['source_tokens']}")
        expect(row["x_mm"] == float("10.123456789012345678"), "the derived value is the float of the token")


def test_implicit_zero_angle_is_stated():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        edit(project / "board.kicad_pcb", "(at 10 10 0)", "(at 10 10)")
        code, _, _ = run_full(project)
        expect(code == 0, f"an implicit angle must pass, got exit {code}")
        row = rows_by_ref(result(project))["R1"]
        expect(row["angle_source"] == "implicit_zero" and row["source_tokens"]["angle"] is None,
               f"angle representation {row['angle_source']} {row['source_tokens']}")
        expect(row["source_rotation_deg"] == 0.0 and row["rotation_deg"] == 0.0, "implicit zero value")


def expect_token_refusal(name: str, token_text: str, code_expected: str):
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        edit(project / "board.kicad_pcb", "(at 10 10 0)", token_text)
        code, stdout, stderr = run_full(project)
        expect(code == 1, f"{name}: expected exit 1, got {code}")
        expect("Traceback" not in stderr and "Traceback" not in stdout, f"{name}: a traceback is printed")
        data = json.loads(stdout)
        expect(len(data["findings"]) == 1, f"{name}: one finding expected")
        expect(data["findings"][0]["code"] == code_expected, f"{name}: code {data['findings'][0]['code']}")


def test_malformed_token_refused_once():
    expect_token_refusal("malformed", "(at abc 10 0)", "board.malformed_token")


def test_nan_token_refused_once():
    expect_token_refusal("nan", "(at nan 10 0)", "board.nonfinite_token")


def test_overflow_token_refused_once():
    expect_token_refusal("overflow", "(at 1e400 10 0)", "board.nonfinite_token")


def test_conflicting_stock_records_refused():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        comp = project / "components"
        text = (comp / "resistor-10k.yaml").read_text(encoding="utf-8")
        (comp / "resistor-10k-b.yaml").write_text(text.replace("quantity: 2000", "quantity: 1999"), encoding="utf-8")
        edit(comp / "parts-map.yaml", "  R2:\n    part: components/resistor-10k.yaml",
             "  R2:\n    part: components/resistor-10k-b.yaml")
        code, stdout, _ = run_full(project)
        expect(code == 1 and refusal_code(stdout) == "stock.conflicting_records",
               f"got {code} {stdout[:160]}")


def test_identical_repeated_records_count_demand_once():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        comp = project / "components"
        (comp / "resistor-10k-copy.yaml").write_bytes((comp / "resistor-10k.yaml").read_bytes())
        edit(comp / "parts-map.yaml", "  R2:\n    part: components/resistor-10k.yaml",
             "  R2:\n    part: components/resistor-10k-copy.yaml")
        code, _, _ = run_full(project)
        expect(code == 0, f"identical records must pass, got exit {code}")
        data = result(project)
        resistor = next(s for s in data["stock"] if s["mpn"] == "EX-R-0603-10K")
        expect(resistor["demand"] == 20, f"demand counts four references times five boards, got {resistor['demand']}")
        expect(resistor["status"] == "pass", "identical records share one stock result")


def test_assembly_instruction_and_grouping():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        edit(project / "variants.yaml", "        reason: The connector is soldered by hand after assembly.\n  - id: no-led",
             "        reason: The connector is soldered by hand after assembly.\n"
             "      - reference: R1\n        reason: Adhesive mount.\n  - id: no-led")
        code, _, _ = run_full(project)
        expect(code == 0, f"two hand reasons must pass, got exit {code}")
        data = result(project)
        rows = rows_by_ref(data)
        expect(rows["R1"]["assembly_instruction"] == "Adhesive mount.", "R1 keeps its own instruction")
        expect(rows["R2"]["assembly_instruction"] == "" and rows["R2"]["installation_method"] == "automatic",
               "automatic rows have an empty instruction")
        resistor_groups = sorted((g["installation_method"], g["assembly_instruction"], tuple(g["references"]))
                                 for g in data["bom_groups"] if g["mpn"] == "EX-R-0603-10K")
        expect(resistor_groups == [("automatic", "", ("R2", "R3", "R4")),
                                   ("hand_installed", "Adhesive mount.", ("R1",))],
               f"groups {resistor_groups}")


def test_neutral_row_fields_present():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        code, _, _ = run_full(project)
        expect(code == 0, f"base must pass, got exit {code}")
        row = rows_by_ref(result(project))["R1"]
        expect(row["datum"] == "kicad_footprint_origin", "datum")
        expect(row["midpoint_mapping"] == "unconfirmed", "midpoint mapping stays unconfirmed")
        expect(row["board_quantity"] == 5 and row["selected_alternate"] == "", "board quantity and empty alternate")
        expect(row["source_tokens"] == {"x": "10", "y": "10", "angle": "0"}, f"tokens {row['source_tokens']}")


def test_input_records_are_project_relative_and_once():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        code, _, _ = run_full(project)
        expect(code == 0, f"base must pass, got exit {code}")
        data = result(project)
        for item in data["inputs"]:
            expect(not Path(item["path"]).is_absolute(), f"absolute recorded path {item['path']}")
            expect(file_sha(project / item["path"]) == item["sha256"], f"hash of {item['path']}")
        paths = [i["path"] for i in data["inputs"]]
        expect(len(paths) == len(set(paths)), "each input is recorded once")


# --------------------------------------------------------------------------- final repair


SKILL_SCRIPTS = ROOT / "skills" / "pcba-design" / "scripts"


def expect_one_finding(stdout: str, stderr: str, code_expected: str, name: str) -> dict:
    expect("Traceback" not in stderr and "Traceback" not in stdout, f"{name}: a traceback is printed")
    data = json.loads(stdout)
    expect(len(data["findings"]) == 1, f"{name}: one finding expected, got {len(data['findings'])}")
    expect(data["findings"][0]["code"] == code_expected, f"{name}: code {data['findings'][0]['code']}")
    return data["findings"][0]


def test_held_lock_refuses_before_capture():
    sys.path.insert(0, str(SKILL_SCRIPTS))
    import project_io as pio
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        # The board record is broken on purpose. A capture before the lock would report stock.policy_missing.
        edit(project / "board.yaml", "extensions:\n  pcba:\n    stock:\n      max_age_days: 30\n", "")
        holder = pio.acquire_lock(project, "held-by-test")
        try:
            code, stdout, stderr = run_full(project)
        finally:
            pio.release_lock(project, holder["token"])
        expect(code == 1, f"a held lock must refuse, got exit {code}")
        expect_one_finding(stdout, stderr, "project.locked", "held lock")
        expect(not (project / "out").exists(), "a held lock writes nothing")


def test_output_escape_gives_one_finding():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        code, stdout, stderr = run_full(project, out="../escape.json")
        expect(code == 1, f"escaping output must refuse, got exit {code}")
        expect_one_finding(stdout, stderr, "output.path_invalid", "output escape")
        expect(not (Path(tmp) / "escape.json").exists(), "nothing is written outside the project")


def test_output_directory_gives_one_finding():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        code, stdout, stderr = run_full(project, out="components")
        expect(code == 1, f"directory output must refuse, got exit {code}")
        expect_one_finding(stdout, stderr, "output.path_invalid", "output directory")
        expect((project / "components" / "resistor-10k.yaml").is_file(), "the directory is unchanged")


def test_alias_finding_names_requested_path():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        before = file_sha(project / "board.yaml")
        code, stdout, stderr = run_full(project, out="board.yaml")
        expect(code == 1, f"alias must refuse, got exit {code}")
        finding = expect_one_finding(stdout, stderr, "output.aliases_input", "alias message")
        expect("board.yaml" in finding["message"] and "assembly-neutral" not in finding["message"],
               f"the message must name the requested path: {finding['message']}")
        expect(file_sha(project / "board.yaml") == before, "the input bytes are unchanged")


def test_write_failure_gives_one_finding():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        (project / "out").mkdir()
        (project / "out" / "pcba").mkdir()
        os.chmod(project / "out" / "pcba", 0o500)
        try:
            code, stdout, stderr = run_full(project)
        finally:
            os.chmod(project / "out" / "pcba", 0o700)
        if os.geteuid() == 0:
            return  # root ignores directory permissions, so the write does not fail
        expect(code == 1, f"an unwritable output must refuse, got exit {code}")
        expect_one_finding(stdout, stderr, "output.write_failed", "write failure")


def test_post_replace_failure_reports_replaced_output():
    import contextlib
    import io
    mod = load_module()
    real_write = mod.project_io.atomic_write

    def replace_then_fail(project, target, data, **kw):
        real_write(project, target, data)
        cause = OSError(5, "simulated fsync failure")
        error = mod.project_io.PostReplaceError("The new bytes are in place, but a later step failed.")
        error.__cause__ = cause
        raise error

    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        mod.project_io.atomic_write = replace_then_fail
        buffer = io.StringIO()
        try:
            with contextlib.redirect_stdout(buffer):
                code = mod.main(["neutral", "--project", str(project), "--board", "board.kicad_pcb",
                                 "--variant", "base", "--as-of", AS_OF])
        finally:
            mod.project_io.atomic_write = real_write
        expect(code == 1, f"a post-replace failure must exit 1, got {code}")
        data = json.loads(buffer.getvalue())
        expect(data["status"] == "failure", f"status {data.get('status')}")
        expect(data.get("output_replaced") is True, "output_replaced must be true")
        expect(len(data["findings"]) == 1, "one finding expected")
        finding = data["findings"][0]
        expect(finding["code"] == "output.replaced_then_failed", f"code {finding['code']}")
        expect("are in place" in finding["message"] and "synchronization failed" in finding["message"],
               f"message {finding['message']}")
        expect("simulated fsync failure" in finding["message"], "the cause is preserved")
        out = project / "out" / "pcba" / "assembly-neutral.json"
        expect(out.is_file(), "the replaced output exists")
        expect(json.loads(out.read_text(encoding="utf-8"))["variant"] == "base", "the output holds the new bytes")


# --------------------------------------------------------------------------- batch 1: alternates


def sha_of(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def alt_project(tmp: Path, approve: bool = True, alt_text: str | None = None, approval_extra: str = "",
                approve_hash_of_alt: bool = True, schema_version: str = "1.1") -> Path:
    project = copy_project(tmp)
    comp = project / "components"
    primary_text = (comp / "resistor-10k.yaml").read_text(encoding="utf-8")
    alt = alt_text if alt_text is not None else primary_text.replace(
        "manufacturer: Example Passives", "manufacturer: Example Passives Alt").replace(
        "mpn: EX-R-0603-10K", "mpn: EX-R-0603-10K-ALT").replace(
        "datasheet_url: https://example.com/datasheets/ex-r-0603-10k.pdf",
        "datasheet_url: https://example.com/datasheets/ex-r-0603-10k-alt.pdf")
    (comp / "resistor-alt.yaml").write_text(alt, encoding="utf-8")
    edit(comp / "parts-map.yaml", 'schema_version: "1.0"', f'schema_version: "{schema_version}"')
    edit(comp / "parts-map.yaml", "  R1:\n    part: components/resistor-10k.yaml",
         "  R1:\n    part: components/resistor-10k.yaml\n    alternates:\n      - name: alt-r\n"
         "        part: components/resistor-alt.yaml")
    edit(project / "board.yaml", "      max_age_days: 30\n",
         "      max_age_days: 30\n    selected_alternates:\n      R1: alt-r\n")
    if approve:
        alt_sha = sha_of(comp / "resistor-alt.yaml") if approve_hash_of_alt else "0" * 64
        entry = (
            "  - reference: R1\n    variant: base\n"
            "    primary_part_path: components/resistor-10k.yaml\n"
            f"    primary_sha256: {sha_of(comp / 'resistor-10k.yaml')}\n"
            "    alternate_name: alt-r\n"
            "    alternate_part_path: components/resistor-alt.yaml\n"
            f"    alternate_sha256: {alt_sha}\n"
            "    application_evidence:\n      source: Circuit review note for the fixture\n"
            '      retrieved: "2026-11-14"\n      statement: The pull-up value serves this node.\n'
            "    approved_by: Test Reviewer\n"
            '    approved_on: "2026-11-14"\n'
        )
        text = ('schema_id: cad-skills/alternate-approval\nschema_version: "1.0"\napprovals:\n' + entry + approval_extra)
        (comp / "alternate-approvals.yaml").write_text(text, encoding="utf-8")
    return project


def test_approved_alternate_is_used_and_counted_once():
    with tempfile.TemporaryDirectory() as tmp:
        project = alt_project(Path(tmp))
        code, _, _ = run_full(project)
        expect(code == 0, f"an approved alternate must pass, got exit {code}")
        data = result(project)
        row = rows_by_ref(data)["R1"]
        expect(row["selected_alternate"] == "alt-r", "the row names the selected alternate")
        expect(row["part_path"] == "components/resistor-alt.yaml", "the row takes the alternate part path")
        expect(row["mpn"] == "EX-R-0603-10K-ALT", "the row takes the alternate MPN")
        expect(rows_by_ref(data)["R2"]["selected_alternate"] == "", "unselected rows keep an empty name")
        demand = {s["mpn"]: s["demand"] for s in data["stock"]}
        expect(demand["EX-R-0603-10K-ALT"] == 5 and demand["EX-R-0603-10K"] == 15,
               f"demand per part, once per reference: {demand}")
        inputs = [i["path"] for i in data["inputs"]]
        expect("components/alternate-approvals.yaml" in inputs and "components/resistor-alt.yaml" in inputs,
               "approval and alternate are bound inputs")


def expect_alt_refusal(name: str, project: Path, code_expected: str):
    code, stdout, stderr = run_full(project)
    expect(code == 1, f"{name}: expected exit 1, got {code}")
    expect_one_finding(stdout, stderr, code_expected, name)
    expect(not (project / "out").exists(), f"{name}: a refusal writes nothing")


def test_unapproved_alternate_refused_even_with_equal_records():
    with tempfile.TemporaryDirectory() as tmp:
        project = alt_project(Path(tmp), approve=False)
        expect_alt_refusal("unapproved", project, "alternate.unapproved")


def test_stale_approval_refused_when_alternate_bytes_change():
    with tempfile.TemporaryDirectory() as tmp:
        project = alt_project(Path(tmp))
        comp = project / "components"
        (comp / "resistor-alt.yaml").write_text(
            (comp / "resistor-alt.yaml").read_text(encoding="utf-8") + "\n# edited after approval\n", encoding="utf-8")
        expect_alt_refusal("stale", project, "alternate.approval_stale")


def test_approval_with_wrong_alternate_hash_is_stale():
    with tempfile.TemporaryDirectory() as tmp:
        project = alt_project(Path(tmp), approve_hash_of_alt=False)
        expect_alt_refusal("wrong hash", project, "alternate.approval_stale")


def test_duplicate_approval_key_refused():
    with tempfile.TemporaryDirectory() as tmp:
        project = alt_project(Path(tmp))
        comp = project / "components"
        text = (comp / "alternate-approvals.yaml").read_text(encoding="utf-8")
        body = text.split("approvals:\n", 1)[1]
        (comp / "alternate-approvals.yaml").write_text(text + body, encoding="utf-8")
        expect_alt_refusal("duplicate key", project, "alternate.approval_conflict")


def test_footprint_mismatch_refused_after_approval_check():
    with tempfile.TemporaryDirectory() as tmp:
        project = alt_project(Path(tmp), alt_text=None)
        comp = project / "components"
        edit(comp / "resistor-alt.yaml", "footprint: Resistor_SMD:R_0603_1608Metric",
             "footprint: Resistor_SMD:R_0402_1005Metric")
        # Re-approve the edited bytes so that only the footprint check can refuse.
        text = (comp / "alternate-approvals.yaml").read_text(encoding="utf-8")
        old_sha = sha_of(comp / "resistor-alt.yaml")
        (comp / "alternate-approvals.yaml").write_text(
            re.sub(r"alternate_sha256: [0-9a-f]{64}", f"alternate_sha256: {old_sha}", text), encoding="utf-8")
        expect_alt_refusal("footprint", project, "alternate.footprint_mismatch")


def test_unknown_alternate_name_refused():
    with tempfile.TemporaryDirectory() as tmp:
        project = alt_project(Path(tmp))
        edit(project / "board.yaml", "      R1: alt-r\n", "      R1: alt-missing\n")
        expect_alt_refusal("unknown name", project, "alternate.unknown")


def test_approval_for_undeclared_reference_refused():
    with tempfile.TemporaryDirectory() as tmp:
        project = alt_project(Path(tmp), approval_extra="  - reference: R9\n    variant: base\n"
                              "    primary_part_path: components/resistor-10k.yaml\n"
                              f"    primary_sha256: {'0' * 64}\n    alternate_name: alt-r\n"
                              "    alternate_part_path: components/resistor-alt.yaml\n"
                              f"    alternate_sha256: {'0' * 64}\n"
                              "    application_evidence:\n      source: x\n      retrieved: \"2026-11-14\"\n"
                              "      statement: x\n    approved_by: x\n    approved_on: \"2026-11-14\"\n")
        expect_alt_refusal("undeclared reference", project, "alternate.approval_unused")


def test_alternates_need_map_version_1_1():
    with tempfile.TemporaryDirectory() as tmp:
        project = alt_project(Path(tmp), schema_version="1.0")
        code, stdout, stderr = run_full(project)
        expect(code == 1, f"a 1.0 map with alternates must refuse, got exit {code}")
        expect_one_finding(stdout, stderr, "map.schema", "1.0 with alternates")


# --------------------------------------------------------------------------- batch 2: Sierra outputs


def sierra_project(tmp: Path) -> Path:
    """A copy of the fixture whose board has no restrictions. Used only for Sierra positive tests."""
    project = copy_project(tmp)
    text = (project / "board.yaml").read_text(encoding="utf-8")
    old = "restrictions:\n  - text: The board has no export-controlled function.\n    source: Project statement, 2026-11-13\n"
    assert text.count(old) == 1, "restriction anchor"
    (project / "board.yaml").write_text(text.replace(old, "restrictions: []\n"), encoding="utf-8")
    return project


def run_sierra(project: Path, out_dir: str = "out/pcba/sierra", variant: str = "base", board: str = "board.kicad_pcb"):
    cmd = ["uv", "run", str(PCBA), "sierra", "--project", str(project), "--board", board,
           "--variant", variant, "--as-of", AS_OF, "--out-dir", out_dir]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return proc.returncode, proc.stdout, proc.stderr


def rebind_profile(project: Path, text_edit=None) -> None:
    """Edit the supplier profile, recompute its content hash, and rebind the board record hash."""
    spec = importlib.util.spec_from_file_location("validate_for_tests", ROOT / "skills" / "pcba-design" / "contracts" / "validate.py")
    validate = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(validate)
    prof = project / "manufacturing/supplier.yaml"
    text = prof.read_text(encoding="utf-8")
    if text_edit is not None:
        text = text_edit(text)
    record = validate.parse_record(text.encode("utf-8"), ".yaml", "profile")
    text = re.sub(r'content_sha256: "[0-9a-f]{64}"', f'content_sha256: "{validate.canonical_hash(record)}"', text, count=1)
    prof.write_text(text, encoding="utf-8")
    board = project / "board.yaml"
    board.write_text(re.sub(r'profile_sha256: "[0-9a-f]{64}"', f'profile_sha256: "{validate.canonical_hash(record)}"',
                            board.read_text(encoding="utf-8"), count=1), encoding="utf-8")


def sierra_bom(project: Path, out_dir: str = "out/pcba/sierra"):
    import openpyxl
    ws = openpyxl.load_workbook(project / out_dir / "bom" / "sierra-bom.xlsx").active
    return [row for row in ws.iter_rows(values_only=True)]


def test_mechanical_entry_with_alternates_refused():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        comp = project / "components"
        edit(comp / "parts-map.yaml", 'schema_version: "1.0"', 'schema_version: "1.1"')
        edit(comp / "parts-map.yaml", "  MH1:\n    mechanical: true\n",
             "  MH1:\n    mechanical: true\n    alternates:\n      - name: alt-x\n        part: components/resistor-10k.yaml\n")
        code, stdout, stderr = run_full(project)
        expect(code == 1, f"a mechanical entry with alternates must refuse, got exit {code}")
        expect_one_finding(stdout, stderr, "map.alternate_on_mechanical", "mechanical with alternates")


def test_list_valued_selection_refused_once():
    with tempfile.TemporaryDirectory() as tmp:
        project = alt_project(Path(tmp))
        edit(project / "board.yaml", "      R1: alt-r\n", "      R1: [alt-r, alt-s]\n")
        code, stdout, stderr = run_full(project)
        expect(code == 1, f"a list-valued selection must refuse, got exit {code}")
        expect_one_finding(stdout, stderr, "alternate.selection_invalid", "list-valued selection")
        expect(not (project / "out").exists(), "a refusal writes nothing")


def test_numeric_selection_value_refused_once():
    with tempfile.TemporaryDirectory() as tmp:
        project = alt_project(Path(tmp))
        edit(project / "board.yaml", "      R1: alt-r\n", "      R1: 5\n")
        code, stdout, stderr = run_full(project)
        expect(code == 1, f"a numeric selection must refuse, got exit {code}")
        expect_one_finding(stdout, stderr, "alternate.selection_invalid", "numeric selection")


def test_selection_block_that_is_not_a_mapping_refused_once():
    with tempfile.TemporaryDirectory() as tmp:
        project = alt_project(Path(tmp))
        edit(project / "board.yaml", "    selected_alternates:\n      R1: alt-r\n", "    selected_alternates: alt-r\n")
        code, stdout, stderr = run_full(project)
        expect(code == 1, f"a selection that is not a mapping must refuse, got exit {code}")
        expect_one_finding(stdout, stderr, "alternate.selection_invalid", "selection not a mapping")


def test_sierra_outputs_and_contents():
    import xlrd
    with tempfile.TemporaryDirectory() as tmp:
        project = sierra_project(Path(tmp))
        code, stdout, stderr = run_sierra(project)
        expect(code == 0, f"the Sierra step must write, got exit {code} {stdout[:200]}")
        expect("Traceback" not in stderr, "no traceback")
        out = project / "out" / "pcba" / "sierra"
        for rel in ("bom/sierra-bom.xlsx", "placement/sierra-xy-draft.csv", "test/test-record.json",
                    "reports/sierra-status.json"):
            expect((out / rel).is_file(), f"{rel} is written")
        # Exact header strings against the retained Sierra sample file.
        sample = xlrd.open_workbook(ROOT / "docs" / "reviews" / "sierra-source-evidence" / "BOM-Sample-and-Demo.xls")
        sample_header = sample.sheet_by_index(0).row_values(6)
        rows = sierra_bom(project)
        expect(list(rows[6]) == sample_header, "the BOM header equals the retained sample header, exactly")
        expect(rows[0][0].startswith("This is a sample BOM for  Sierra Circuits"), "the sample intro is kept")
        data = [r for r in rows[7:] if r[0] is not None]
        by_mpn = {r[2]: r for r in data}
        expect(by_mpn["EX-R-0603-10K"][1] == 4 and by_mpn["EX-R-0603-10K"][4] == "R1,R2,R3,R4",
               "the resistor row has four references")
        expect(by_mpn["EX-HDR-1X02"][4] == "J1", "the hand-installed header stays in the BOM under include_in_bom")
        status = json.loads((out / "reports" / "sierra-status.json").read_text(encoding="utf-8"))
        expect(status["qualification"] == "unqualified", "the draft is unqualified")
        expect(all(v == "unconfirmed" for k, v in status["conventions"].items() if k != "xy_units"),
               "every open convention stays unconfirmed")
        expect(status["conventions"]["xy_units"] == "stated_by_sample", "the mil unit is recorded as stated")
        expect(status["service"]["service"] == "turnkey_pro", "the service is turnkey_pro")
        expect(status["service"]["fabrication_location"] == "unconfirmed"
               and status["service"]["assembly_location"] == "unconfirmed", "locations stay unconfirmed")
        expect(status["export_applicability"] == "unconfirmed", "export applicability stays unconfirmed")
        csv_lines = (out / "placement" / "sierra-xy-draft.csv").read_text(encoding="utf-8").splitlines()
        expect(csv_lines[0] == "Designator,Footprint,Mid X,Mid Y,Side,Rotation", "XY header")
        expect(len(csv_lines) == 10, f"nine automatic populated rows, got {len(csv_lines) - 1}")
        expect("R1,Resistor_SMD:R_0603_1608Metric,393.7008,393.7008,T,0.000000" in csv_lines, "R1 mil and side")
        expect("D2,LED_SMD:LED_0603_1608Metric,787.4016,787.4016,B,90.000000" in csv_lines, "bottom side and angle")
        expect(not any(line.startswith("J1,") for line in csv_lines), "the hand-installed row is not placed")
        record = json.loads((out / "test" / "test-record.json").read_text(encoding="utf-8"))
        expect(record["physical_test_passed"] is False, "no physical pass")
        hand = [i for i in record["items"] if i["id"] == "hand-install.J1"]
        expect(hand and hand[0]["status"] == "not measured", "the hand-install step is listed as not measured")


def test_dnp_row_uses_dni_text_and_separate_row():
    with tempfile.TemporaryDirectory() as tmp:
        project = sierra_project(Path(tmp))
        edit(project / "board.yaml", "variant: base", "variant: no-led")
        code, _, stderr = run_sierra(project, variant="no-led")
        expect(code == 0, f"no-led must write, got exit {code}")
        rows = [r for r in sierra_bom(project)[7:] if r[0] is not None]
        dni = [r for r in rows if r[3] == "DNI"]
        expect(len(dni) == 1 and dni[0][4] == "D1,D2" and dni[0][1] == 2, f"the DNI row: {dni}")
        populated = [r for r in rows if r[2] == "EX-LED-0603-G" and r[3] in (None, "")]
        expect(len(populated) == 1 and populated[0][4] == "D3", "the populated LED is a separate row")


def test_exclude_policy_removes_hand_row():
    with tempfile.TemporaryDirectory() as tmp:
        project = sierra_project(Path(tmp))
        rebind_profile(project, lambda s: s.replace("hand_installed_bom: include_in_bom",
                                                     "hand_installed_bom: exclude_from_bom"))
        code, _, _ = run_sierra(project)
        expect(code == 0, f"exclude_from_bom must write, got exit {code}")
        rows = [r for r in sierra_bom(project)[7:] if r[0] is not None]
        expect(all(r[4] != "J1" for r in rows), "the hand-installed row is omitted from the BOM")
        status = json.loads((project / "out/pcba/sierra/reports/sierra-status.json").read_text(encoding="utf-8"))
        expect(status["hand_installed_bom"] == "exclude_from_bom", "the policy is recorded")
        record = json.loads((project / "out/pcba/sierra/test/test-record.json").read_text(encoding="utf-8"))
        expect(any(i["id"] == "hand-install.J1" for i in record["items"]), "the test record still lists J1")


def test_missing_policy_stops_only_the_bom():
    with tempfile.TemporaryDirectory() as tmp:
        project = sierra_project(Path(tmp))
        rebind_profile(project, lambda s: s.replace("extensions:\n  pcba:\n    hand_installed_bom: include_in_bom\n", ""))
        code, stdout, _ = run_sierra(project)
        expect(code == 0, f"a missing policy must not stop the placement draft, got exit {code}")
        out = project / "out" / "pcba" / "sierra"
        expect(not (out / "bom" / "sierra-bom.xlsx").exists(), "no BOM is produced")
        expect((out / "placement" / "sierra-xy-draft.csv").is_file(), "the placement draft is still produced")
        status = json.loads((out / "reports" / "sierra-status.json").read_text(encoding="utf-8"))
        expect(status["hand_installed_bom"] == "missing" and status["artifacts"]["bom"] == "not_produced",
               f"status {status}")


def test_unknown_policy_value_stops_only_the_bom():
    with tempfile.TemporaryDirectory() as tmp:
        project = sierra_project(Path(tmp))
        rebind_profile(project, lambda s: s.replace("hand_installed_bom: include_in_bom",
                                                     "hand_installed_bom: maybe"))
        code, _, _ = run_sierra(project)
        expect(code == 0, f"an unknown policy must not stop the placement draft, got exit {code}")
        status = json.loads((project / "out/pcba/sierra/reports/sierra-status.json").read_text(encoding="utf-8"))
        expect(status["hand_installed_bom"] == "unknown" and status["artifacts"]["bom"] == "not_produced",
               f"status {status}")


def test_profile_hash_mismatch_refused():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        board = project / "board.yaml"
        before = board.read_bytes()
        rebind_profile(project, lambda text: text.replace("hand_installed_bom: include_in_bom",
                                                        "hand_installed_bom: exclude_from_bom"))
        board.write_bytes(before)
        code, stdout, stderr = run_sierra(project)
        expect(code == 1, f"a changed profile must refuse, got exit {code}")
        expect_one_finding(stdout, stderr, "supplier.profile_mismatch", "profile hash")
        expect(not (project / "out").exists(), "a refusal writes nothing")


def test_sierra_out_dir_that_is_a_file_refused():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        before = file_sha(project / "board.yaml")
        code, stdout, stderr = run_sierra(project, out_dir="board.yaml")
        expect(code == 1, f"a file as output directory must refuse, got exit {code}")
        expect_one_finding(stdout, stderr, "output.path_invalid", "file as output directory")
        expect(file_sha(project / "board.yaml") == before, "the input is unchanged")


def test_sierra_outputs_are_deterministic():
    with tempfile.TemporaryDirectory() as tmp:
        project = sierra_project(Path(tmp))
        run_sierra(project, out_dir="out/a")
        run_sierra(project, out_dir="out/b")
        for rel in ("placement/sierra-xy-draft.csv", "test/test-record.json", "reports/sierra-status.json"):
            expect(file_sha(project / "out/a" / rel) == file_sha(project / "out/b" / rel),
                   f"{rel} is the same on two runs")


def test_restriction_refusal_keeps_original_text():
    with tempfile.TemporaryDirectory() as tmp:
        project = copy_project(Path(tmp))
        code, stdout, stderr = run_sierra(project)
        expect(code == 1, f"a nonempty restriction must refuse, got exit {code}")
        expect_one_finding(stdout, stderr, "supplier.restriction_review", "restriction")
        message = json.loads(stdout)["findings"][0]["message"]
        expect("The board has no export-controlled function." in message, "the original text is kept")
        expect(not (project / "out").exists(), "a refusal writes nothing")


def test_existing_destination_refused_and_old_bom_kept():
    with tempfile.TemporaryDirectory() as tmp:
        project = sierra_project(Path(tmp))
        code, _, _ = run_sierra(project)
        expect(code == 0, f"the first run must write, got exit {code}")
        old_bom = file_sha(project / "out/pcba/sierra/bom/sierra-bom.xlsx")
        rebind_profile(project, lambda s: s.replace("hand_installed_bom: include_in_bom", "x: 1"))
        code, stdout, stderr = run_sierra(project)
        expect(code == 1, f"an existing destination must refuse, got exit {code}")
        expect_one_finding(stdout, stderr, "output.exists", "existing destination")
        expect(file_sha(project / "out/pcba/sierra/bom/sierra-bom.xlsx") == old_bom,
               "the earlier BOM is untouched, so no stale mix is created")


def test_partial_write_failure_publishes_nothing():
    mod = load_module()
    real_write = mod.project_io.atomic_write
    calls = {"n": 0}

    def fail_second(project, target, data, **kw):
        calls["n"] += 1
        if calls["n"] == 2:
            raise OSError(28, "No space left on device")
        return real_write(project, target, data, **kw)

    with tempfile.TemporaryDirectory() as tmp:
        project = sierra_project(Path(tmp))
        mod.project_io.atomic_write = fail_second
        try:
            try:
                mod.build_sierra(project, "board.kicad_pcb", "base", dt.date(2026, 11, 15), "out/pcba/sierra")
                raise AssertionError("a partial write must refuse")
            except mod.Refused as refusal:
                expect(refusal.finding["code"] == "output.write_failed", f"code {refusal.finding['code']}")
        finally:
            mod.project_io.atomic_write = real_write
        expect(not (project / "out/pcba/sierra").exists(), "no destination is published after a partial write")
        expect(not (project / "out/pcba/.sierra-staging").exists(), "the staging directory is removed")


def test_input_changed_before_publication_refused():
    mod = load_module()
    real_write = mod.project_io.atomic_write
    done = {"first": False}

    def tamper_first(project, target, data, **kw):
        if not done["first"]:
            done["first"] = True
            prof = project / "manufacturing/supplier.yaml"
            prof.write_text(prof.read_text(encoding="utf-8") + "\n# changed after capture\n", encoding="utf-8")
        return real_write(project, target, data, **kw)

    with tempfile.TemporaryDirectory() as tmp:
        project = sierra_project(Path(tmp))
        mod.project_io.atomic_write = tamper_first
        try:
            try:
                mod.build_sierra(project, "board.kicad_pcb", "base", dt.date(2026, 11, 15), "out/pcba/sierra")
                raise AssertionError("a changed profile must refuse before publication")
            except mod.Refused as refusal:
                expect(refusal.finding["code"] in ("input.changed", "supplier.profile_mismatch"),
                       f"code {refusal.finding['code']}")
        finally:
            mod.project_io.atomic_write = real_write
        expect(not (project / "out/pcba/sierra").exists(), "nothing is published")


def expect_overlap_refusal(name: str, out_dir: str):
    with tempfile.TemporaryDirectory() as tmp:
        project = sierra_project(Path(tmp))
        code, stdout, stderr = run_sierra(project, out_dir=out_dir)
        expect(code == 1, f"{name}: expected exit 1, got {code}")
        expect_one_finding(stdout, stderr, "output.path_invalid", name)
        expect(not (project / "out/pcba/.sierra-staging").exists(), f"{name}: no staging is created")
        expect(not (project / out_dir).exists(), f"{name}: no destination is created")


def test_destination_equal_to_staging_refused():
    expect_overlap_refusal("equal to staging", "out/pcba/.sierra-staging")


def test_destination_ancestor_of_staging_refused():
    expect_overlap_refusal("ancestor of staging", "out/pcba")


def test_destination_inside_staging_refused():
    expect_overlap_refusal("inside staging", "out/pcba/.sierra-staging/inner")


def test_dangling_staging_symlink_refused_before_mutation():
    with tempfile.TemporaryDirectory() as tmp:
        project = sierra_project(Path(tmp))
        (project / "out" / "pcba").mkdir(parents=True)
        os.symlink("nowhere", project / "out/pcba/.sierra-staging")
        code, stdout, stderr = run_sierra(project)
        expect(code == 1, f"a dangling staging link must refuse, got exit {code}")
        expect_one_finding(stdout, stderr, "output.staging_link", "dangling staging link")
        expect(os.path.islink(project / "out/pcba/.sierra-staging"), "the link is left in place")
        expect(not (project / "out/pcba/sierra").exists(), "no destination is created")


def test_existing_staging_directory_refused_and_kept():
    with tempfile.TemporaryDirectory() as tmp:
        project = sierra_project(Path(tmp))
        staging = project / "out/pcba/.sierra-staging"
        staging.mkdir(parents=True)
        (staging / "keep.txt").write_text("earlier run", encoding="utf-8")
        code, stdout, stderr = run_sierra(project)
        expect(code == 1, f"an existing staging directory must refuse, got exit {code}")
        expect_one_finding(stdout, stderr, "output.staging_exists", "existing staging directory")
        expect((staging / "keep.txt").read_text(encoding="utf-8") == "earlier run", "the earlier staging is untouched")


# --------------------------------------------------------------------------- batch 3: package


STANDARD = ROOT / "tests" / "fixtures" / "pcba-design" / "standard-project"
BOARD_REL = "kicad/board.kicad_pcb"


def standard_copy(tmp: Path) -> Path:
    """An owned copy of the standard-layout fixture. Package tests use this layout only."""
    dest = tmp / "project"
    shutil.copytree(STANDARD, dest)
    return dest


def package_project(tmp: Path) -> Path:
    """An owned copy of the standard-layout fixture, used for package positive tests."""
    return standard_copy(tmp)


def run_package(project: Path, package_id: str = "pkg-one", variant: str = "base"):
    cmd = ["uv", "run", str(PCBA), "package", "--project", str(project), "--board", BOARD_REL,
           "--variant", variant, "--as-of", AS_OF, "--package-id", package_id]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return proc.returncode, proc.stdout, proc.stderr


def test_package_written_with_thirteen_checks_and_unqualified_status():
    with tempfile.TemporaryDirectory() as tmp:
        project = package_project(Path(tmp))
        code, stdout, stderr = run_package(project)
        expect(code == 0, f"the package must write, got exit {code} {stdout[:200]} {stderr[-200:]}")
        expect("Traceback" not in stderr, "no traceback")
        pkg = project / "out/pcba/packages/pkg-one"
        manifest = json.loads((pkg / "manifest.json").read_text(encoding="utf-8"))
        expect(manifest["status"] == "unqualified", "the package is unqualified")
        ids = sorted(c["id"] for c in manifest["checks"])
        expect(len(ids) == 13 and len(set(ids)) == 13, f"thirteen checks, got {len(ids)}")
        for check in manifest["checks"]:
            evidence = pkg / check["evidence_path"]
            expect(evidence.is_file() and report_sha(evidence) == check["evidence_sha256"],
                   f"one evidence file for {check['id']} with the bound hash")
        status = {c["id"]: c["status"] for c in manifest["checks"]}
        expect(status["design.drc"] == "fail", "the placed board is not routed, so the DRC check fails")
        expect(status["design.erc"] == "pass" and status["design.parity"] == "pass",
               "the schematic is clean and its netlist matches the board")
        expect(status["fab.profile_evidence"] == "pass", "the retained evidence matches the profile hash")
        expect(status["fab.export_inventory"] == "pass" and status["fab.layer_order"] == "pass"
               and status["fab.drill_split"] == "pass", "the exports match the captured settings")
        expect(status["fab.supplier_rules"] == "unconfirmed", "open supplier conventions stay unconfirmed")
        expect(status["asm.stock_dated"] == "fail", "the LED stock is below the demand of 20")
        expect(status["asm.test_record"] == "pass", "the record matches the board limits and hand-install steps")
        record = json.loads((pkg / "test/test-record.json").read_text(encoding="utf-8"))
        expect(record["physical_test_passed"] is False, "no physical pass is recorded")
        expect(not (project / "out/pcba/.package-staging").exists(), "no staging is left")
        validator = subprocess.run(["uv", "run", str(PCBA), "check", "--project", str(project),
                                    "--package", str(pkg)], capture_output=True, text=True, cwd=ROOT)
        expect(validator.returncode == 0, f"the full validator must pass, got {validator.returncode} {validator.stdout[:300]}")


def report_sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_existing_package_id_refused_and_kept():
    with tempfile.TemporaryDirectory() as tmp:
        project = package_project(Path(tmp))
        code, _, _ = run_package(project)
        expect(code == 0, f"the first package must write, got exit {code}")
        before = file_sha(project / "out/pcba/packages/pkg-one/manifest.json")
        code, stdout, stderr = run_package(project)
        expect(code == 1, f"an existing package id must refuse, got exit {code}")
        expect_one_finding(stdout, stderr, "package.exists", "existing package")
        expect(file_sha(project / "out/pcba/packages/pkg-one/manifest.json") == before,
               "the earlier package is kept unchanged")


def test_package_restriction_refused_with_original_text():
    with tempfile.TemporaryDirectory() as tmp:
        project = standard_copy(Path(tmp))
        edit(project / "board.yaml", "restrictions: []\n",
             "restrictions:\n  - text: The board has no export-controlled function.\n    source: Project statement, 2026-11-13\n")
        code, stdout, stderr = run_package(project)
        expect(code == 1, f"a restriction must refuse the package, got exit {code}")
        expect_one_finding(stdout, stderr, "supplier.restriction_review", "package restriction")
        expect("The board has no export-controlled function." in json.loads(stdout)["findings"][0]["message"],
               "the original text is kept")


def test_invalid_package_id_refused():
    with tempfile.TemporaryDirectory() as tmp:
        project = package_project(Path(tmp))
        code, stdout, stderr = run_package(project, package_id="Bad_ID")
        expect(code == 1, f"an invalid id must refuse, got exit {code}")
        expect_one_finding(stdout, stderr, "package.id_invalid", "invalid package id")


def test_staged_gate_refuses_extra_and_missing_files():
    sys.path.insert(0, str(SKILL_SCRIPTS))
    pcba = load_module()
    import package as package_mod
    with tempfile.TemporaryDirectory() as tmp:
        staging = Path(tmp) / "stage"
        staging.mkdir()
        (staging / "a.txt").write_bytes(b"one")
        (staging / "extra.txt").write_bytes(b"two")
        expected = {"a.txt": (hashlib.sha256(b"one").hexdigest(), 3), "missing.txt": ("0" * 64, 0)}
        try:
            package_mod._verify_staged(staging, expected, pcba.Refused)
            raise AssertionError("an extra file must refuse")
        except pcba.Refused as refusal:
            expect(refusal.finding["code"] == "package.extra_file", f"code {refusal.finding['code']}")


def test_package_partial_write_publishes_nothing():
    sys.path.insert(0, str(SKILL_SCRIPTS))
    pcba = load_module()
    import package as package_mod
    real_write = pcba.project_io.atomic_write
    calls = {"n": 0}

    def fail_later(project, target, data, **kw):
        calls["n"] += 1
        if calls["n"] == 5:
            raise OSError(28, "No space left on device")
        return real_write(project, target, data, **kw)

    with tempfile.TemporaryDirectory() as tmp:
        project = package_project(Path(tmp))
        pcba.project_io.atomic_write = fail_later
        try:
            try:
                package_mod.build_package(pcba, project, BOARD_REL, "base", dt.date(2026, 11, 15), "pkg-p")
                raise AssertionError("a partial write must refuse")
            except pcba.Refused as refusal:
                expect(refusal.finding["code"] == "output.write_failed", f"code {refusal.finding['code']}")
        finally:
            pcba.project_io.atomic_write = real_write
        expect(not (project / "out/pcba/packages/pkg-p").exists(), "no package is published")
        expect(not (project / "out/pcba/.package-staging").exists(), "the staging directory is removed")


LOCK_DIGEST = "sha256:b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f"
IMAGE_REF = "localhost/cad-skills-pcb:b6"


def load_check_module(name: str):
    """Load one owned check module by name. The tests use the same module code as the package."""
    sys.path.insert(0, str(SKILL_SCRIPTS))
    return importlib.import_module(name)


def in_process_package(project: Path, hooks: dict | None = None, package_id: str = "pkg-hook"):
    """Run build_package in this process, with optional hooks. Return (pcba module, package module)."""
    sys.path.insert(0, str(SKILL_SCRIPTS))
    pcba = load_module()
    import package as package_mod
    package_mod.build_package(pcba, project, BOARD_REL, "base", dt.date(2026, 11, 15), package_id, _hooks=hooks)
    return pcba, package_mod


def expect_package_refusal(name: str, call, code_expected: str, dest: Path, staging: Path) -> None:
    """Run `call` and expect one refusal with the given code. Match on the finding, not on the class."""
    try:
        call()
    except Exception as refusal:  # noqa: BLE001 - each module load has its own Refused class
        finding = getattr(refusal, "finding", None)
        expect(finding is not None and finding["code"] == code_expected,
               f"{name}: expected {code_expected}, got {finding}")
    else:
        raise AssertionError(f"{name}: the package must refuse")
    expect(not dest.exists(), f"{name}: no package is published")
    expect(not staging.exists(), f"{name}: no staging is left")


def test_missing_schematic_refuses_package():
    with tempfile.TemporaryDirectory() as tmp:
        project = package_project(Path(tmp))
        (project / "kicad/board.kicad_sch").unlink()
        code, stdout, stderr = run_package(project)
        expect(code == 1, f"a missing schematic must refuse, got exit {code}")
        expect_one_finding(stdout, stderr, "package.input_missing", "missing schematic")
        expect(not (project / "out/pcba/packages/pkg-one").exists(), "no package is published")


def test_image_identity_mismatch_refused():
    with tempfile.TemporaryDirectory() as tmp:
        project = package_project(Path(tmp))
        edit(project / "toolchain.lock.json", LOCK_DIGEST, "sha256:" + "0" * 64)
        code, stdout, stderr = run_package(project)
        expect(code == 1, f"an image mismatch must refuse, got exit {code}")
        expect_one_finding(stdout, stderr, "toolchain.image_mismatch", "image identity")


def test_kicad_version_mismatch_refused():
    with tempfile.TemporaryDirectory() as tmp:
        project = package_project(Path(tmp))
        edit(project / "toolchain.lock.json", '"version": "10.0.5"', '"version": "10.0.4"')
        code, stdout, stderr = run_package(project)
        expect(code == 1, f"a KiCad version mismatch must refuse, got exit {code}")
        expect_one_finding(stdout, stderr, "toolchain.version_mismatch", "KiCad version")


def test_source_drift_during_staged_writes_refused():
    with tempfile.TemporaryDirectory() as tmp:
        project = package_project(Path(tmp))
        dest = project / "out/pcba/packages/pkg-hook"
        staging = project / "out/pcba/.package-staging"

        def drift(_staging):
            target = project / "components/led-green.yaml"
            target.write_bytes(target.read_bytes() + b"# drift during staging\n")

        expect_package_refusal("drift during staged writes", lambda: in_process_package(project, {"after_stage": drift}),
                       "cross.input_hash_mismatch", dest, staging)


def test_source_drift_before_publication_refused():
    with tempfile.TemporaryDirectory() as tmp:
        project = package_project(Path(tmp))
        dest = project / "out/pcba/packages/pkg-hook"
        staging = project / "out/pcba/.package-staging"

        def drift():
            target = project / "components/led-green.yaml"
            target.write_bytes(target.read_bytes() + b"# drift before publication\n")

        expect_package_refusal("drift before publication", lambda: in_process_package(project, {"after_validate": drift}),
                       "input.changed", dest, staging)


def test_staged_output_alteration_refused():
    with tempfile.TemporaryDirectory() as tmp:
        project = package_project(Path(tmp))
        dest = project / "out/pcba/packages/pkg-hook"
        staging = project / "out/pcba/.package-staging"

        def alter(staged):
            target = staged / "reports/assembly-neutral.json"
            target.write_bytes(target.read_bytes() + b" ")

        expect_package_refusal("staged output alteration", lambda: in_process_package(project, {"after_stage": alter}),
                       "package.hash_mismatch", dest, staging)


def test_assembly_drawing_marks_dnp_for_no_led_variant():
    with tempfile.TemporaryDirectory() as tmp:
        project = package_project(Path(tmp))
        edit(project / "board.yaml", "variant: base\n", "variant: no-led\n")
        code, stdout, stderr = run_package(project, variant="no-led")
        expect(code == 0, f"the no-led package must write, got exit {code} {stdout[:200]} {stderr[-200:]}")
        pkg = project / "out/pcba/packages/pkg-one"
        svg = (pkg / "drawings/assembly.svg").read_text(encoding="utf-8")
        expect('class="dnp" data-reference="D1"' in svg and 'class="dnp" data-reference="D2"' in svg,
               "the DNP references D1 and D2 carry the DNP mark")
        expect('data-reference="D3"' in svg and 'class="dnp" data-reference="D3"' not in svg,
               "a populated reference has no DNP mark")
        expect('data-reference="J1"' in svg and "J1 HAND" in svg, "the hand-installed reference is marked")
        expect('data-reference="D4"' not in svg, "an excluded reference is not drawn")
        validator_code, _, _ = run_check(project, pkg)
        expect(validator_code == 0, f"the no-led package must pass the full validator, got {validator_code}")


def run_check(project: Path, package: Path):
    cmd = ["uv", "run", str(PCBA), "check", "--project", str(project), "--package", str(package)]
    proc = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT)
    return proc.returncode, proc.stdout, proc.stderr


def test_retained_package_validates_offline():
    retained = ROOT / "tests" / "fixtures" / "pcba-design" / "retained" / "pkg-standard"
    expected = json.loads((ROOT / "tests" / "fixtures" / "pcba-design" / "retained"
                           / "validator-result.json").read_text(encoding="utf-8"))
    code, stdout, stderr = run_check(STANDARD, retained)
    expect(code == 0, f"the retained package must validate, got exit {code} {stdout[:300]}")
    got = json.loads(stdout)
    expect(got["findings"] == expected["findings"] == [], "the retained validator result has no finding")
    expect(got["status"] == expected["status"] == "pass", "the retained validator status is pass")


def test_retained_qualified_status_is_refused_by_validator():
    with tempfile.TemporaryDirectory() as tmp:
        retained = ROOT / "tests" / "fixtures" / "pcba-design" / "retained" / "pkg-standard"
        pkg = Path(tmp) / "pkg"
        shutil.copytree(retained, pkg)
        manifest = pkg / "manifest.json"
        edit(manifest, '"status": "unqualified"', '"status": "qualified"')
        code, stdout, stderr = run_check(STANDARD, pkg)
        expect(code != 0, "a qualified manifest with open checks must fail the validator")
        codes = {f["code"] for f in json.loads(stdout)["findings"]}
        expect("pkg.false_qualification" in codes, f"the validator names the false qualification, got {codes}")


def test_test_record_empty_items_refused():
    checks_asm = load_check_module("checks_asm")
    limits = {"supply_voltage": {"value": 5.0, "unit": "V"}}
    record = json.dumps({"schema": "pcba-design/test-record", "physical_test_passed": False, "items": []}).encode()
    result = checks_asm.test_record(record, limits, [{"reference": "J1", "reason": "Install J1 by hand."}], "base")
    codes = {r["code"] for r in result["reasons"]}
    expect(result["status"] == "fail", "an empty item list must not pass")
    expect("asm.test_items_empty" in codes and "asm.test_step_missing" in codes, f"named reasons, got {codes}")


def test_test_record_missing_hand_install_step_refused():
    checks_asm = load_check_module("checks_asm")
    limits = {"supply_voltage": {"value": 5.0, "unit": "V"}}
    items = [{"id": "limit.supply_voltage", "kind": "limit", "quantity": "supply_voltage",
              "expected": {"value": 5.0, "unit": "V"}, "status": "not measured", "steps": []}]
    record = json.dumps({"physical_test_passed": False, "items": items}).encode()
    result = checks_asm.test_record(record, limits, [{"reference": "J1", "reason": "Install J1 by hand."}], "base")
    expect(result["status"] == "fail", "a missing hand-install step must fail")
    expect(any(r["code"] == "asm.test_step_missing" and "hand-install.J1" in r["text"] for r in result["reasons"]),
           "the missing hand-install step is named")


def test_profile_evidence_changed_byte_fails():
    checks_fab = load_check_module("checks_fab")
    import hashlib
    original = b"retained evidence\n"
    expected = hashlib.sha256(original).hexdigest()
    expect(checks_fab.profile_evidence(original, expected)["status"] == "pass", "the original bytes pass")
    expect(checks_fab.profile_evidence(b"retained evidencf\n", expected)["status"] == "fail",
           "a changed byte must fail")
    expect(checks_fab.profile_evidence(None, expected)["status"] == "pending", "absent evidence is pending")


def test_export_inventory_missing_and_extra_fail_separately():
    checks_fab = load_check_module("checks_fab")
    expected = {"board-F_Cu.gtl": "copper_top", "board-B_Cu.gbl": "copper_bottom"}
    actual = {"board-F_Cu.gtl": b"x", "board-extra.txt": b"y"}
    result = checks_fab.export_inventory(actual, expected)
    codes = {r["code"] for r in result["reasons"]}
    expect(result["status"] == "fail", "missing and extra files fail")
    expect({"fab.file_missing", "fab.file_extra"} <= codes, f"both problems are named, got {codes}")


def gerber(function: str) -> bytes:
    return f"%FSLAX46Y46*%\n%TF.FileFunction,{function}*%\nM02*\n".encode("utf-8")


def test_layer_order_uses_content_not_name():
    checks_fab = load_check_module("checks_fab")
    layers = [("copper_top", "F.Cu"), ("copper_bottom", "B.Cu")]
    renamed = {"renamed.bin": gerber("Copper,L1,Top"), "other.bin": gerber("Copper,L2,Bot")}
    passed = checks_fab.layer_order(renamed, layers)
    expect(passed["status"] == "pass", "a renamed file with the right content passes")
    expect(passed["layer_files"] == {"F.Cu": "renamed.bin", "B.Cu": "other.bin"}, "the content finds each layer")
    wrong = {"board-F_Cu.gtl": gerber("Copper,L2,Bot"), "board-B_Cu.gbl": gerber("Copper,L2,Bot")}
    expect(checks_fab.layer_order(wrong, layers)["status"] == "fail", "wrong layer content fails")


def excellon(holes, tool_inch: str, decimals: int = 4) -> bytes:
    """Write one inch Excellon file, as KiCad does with suppressed trailing zeros. `holes` holds (x_in, y_in) pairs."""
    def digits(value: float) -> str:
        scaled = round(abs(value) * 10 ** decimals)
        text = str(scaled).zfill(2 + decimals).rstrip("0") or "0"
        return ("-" if value < 0 else "") + text
    body = [f"X{digits(x)}Y{digits(y)}" for x, y in holes]
    text = ["M48", "; FORMAT={2:4/ absolute / inch / suppress trailing zeros}", "FMAT,2", "INCH,LZ",
            f"T1C{tool_inch}", "%", "G90", "G05", "T1", *body, "M30"]
    return ("\n".join(text) + "\n").encode("utf-8")


def test_drill_split_fixtures():
    checks_fab = load_check_module("checks_fab")
    # Hole inventory in millimeters. Excellon Y is the negative of the board Y.
    inventory = [{"id": "A", "x": 25.4, "y": 50.8, "diameter_mm": 1.0, "plated": True}]
    plated = excellon([(1.0, -2.0)], "0.0394")
    passed = checks_fab.drill_split({"board-PTH.drl": plated, "board-NPTH.drl": excellon([], "0.1260")},
                                    4, inventory, "board-PTH.drl", "board-NPTH.drl")
    expect(passed["status"] == "pass", f"trailing-zero coordinates match the inventory: {passed['reasons']}")
    negative = [{"id": "N", "x": -5.08, "y": -2.54, "diameter_mm": 1.0, "plated": True}]
    neg_file = excellon([(-0.2, 0.1)], "0.0394")
    expect(checks_fab.drill_split({"board-PTH.drl": neg_file, "board-NPTH.drl": excellon([], "0.1260")},
                                  4, negative, "board-PTH.drl", "board-NPTH.drl")["status"] == "pass",
           "negative coordinates match the inventory")
    doubled = excellon([(1.0, -2.0), (1.0, -2.0)], "0.0394")
    result = checks_fab.drill_split({"board-PTH.drl": doubled, "board-NPTH.drl": excellon([], "0.1260")},
                                    4, inventory, "board-PTH.drl", "board-NPTH.drl")
    expect(result["status"] == "fail" and any(r["code"] == "fab.drill_extra" for r in result["reasons"]),
           "a duplicate hole is an extra hole")
    wrong_plating = [{"id": "A", "x": 25.4, "y": 50.8, "diameter_mm": 1.0, "plated": False}]
    result = checks_fab.drill_split({"board-PTH.drl": plated, "board-NPTH.drl": excellon([], "0.1260")},
                                    4, wrong_plating, "board-PTH.drl", "board-NPTH.drl")
    expect(result["status"] == "fail", "a plating difference fails")
    moved = excellon([(1.1, -2.0)], "0.0394")
    result = checks_fab.drill_split({"board-PTH.drl": moved, "board-NPTH.drl": excellon([], "0.1260")},
                                    4, inventory, "board-PTH.drl", "board-NPTH.drl")
    expect(result["status"] == "fail", "a coordinate difference fails")


def test_drill_split_reads_suppressed_trailing_zeros():
    checks_fab = load_check_module("checks_fab")
    inventory = [{"id": "A", "x": 25.4, "y": 50.8, "diameter_mm": 1.0, "plated": True},
                 {"id": "B", "x": 0.0, "y": 0.0, "diameter_mm": 1.0, "plated": True}]
    text = excellon([(1.0, -2.0), (0.0, 0.0)], "0.0394")
    expect(b"X01Y-02" in text and b"X0Y0" in text, "the writer suppresses trailing zeros as KiCad does")
    result = checks_fab.drill_split({"board-PTH.drl": text, "board-NPTH.drl": excellon([], "0.1260")},
                                    4, inventory, "board-PTH.drl", "board-NPTH.drl")
    expect(result["status"] == "pass", f"suppressed zeros read back exactly: {result['reasons']}")


def test_design_drc_seeded_overlap_fails():
    identity, export = captured_identity()
    checks_design = load_check_module("checks_design")
    board = """(kicad_pcb
  (version 20260206)
  (generator "pcbnew")
  (general (thickness 1.6))
  (layers (0 "F.Cu" signal) (2 "B.Cu" signal) (25 "Edge.Cuts" user))
  (net 0 "") (net 1 "A") (net 2 "B")
  (footprint "TestPoint:TestPoint_Pad_D1.0mm" (layer "F.Cu") (uuid "a1") (at 10 10 0)
    (property "Reference" "TP1" (at 0 -1.5 0) (layer "F.SilkS") (uuid "a2") (effects (font (size 1 1) (thickness 0.15))))
    (pad "1" smd circle (at 0 0) (size 1.0 1.0) (layers "F.Cu" "F.Mask") (net 1 "A") (uuid "a3")))
  (footprint "TestPoint:TestPoint_Pad_D1.0mm" (layer "F.Cu") (uuid "b1") (at 11.1 10 0)
    (property "Reference" "TP2" (at 0 -1.5 0) (layer "F.SilkS") (uuid "b2") (effects (font (size 1 1) (thickness 0.15))))
    (pad "1" smd circle (at 0 0) (size 1.0 1.0) (layers "F.Cu" "F.Mask") (net 2 "B") (uuid "b3")))
  (gr_rect (start 0 0) (end 30 30) (stroke (width 0.05) (type default)) (fill none) (layer "Edge.Cuts") (uuid "e1"))
)
"""
    result = checks_design.drc(export.run_drc(identity, board.encode("utf-8")), "10.0.5")
    expect(result["status"] == "fail", "two pads on different nets with a 0.1 mm gap fail the DRC")
    expect(any("violations" in r["text"] for r in result["reasons"]), "the violation is counted")


def test_supplier_rules_never_pass_while_open():
    checks_fab = load_check_module("checks_fab")
    rules = {"gerber": {"format": "rs274x"},
             "drill": {"format": "excellon", "units": "in", "origin": "absolute", "zero_suppression": "trailing",
                       "decimal_places": 4, "separate_files": True},
             "plane_interpretation": {"status": "unconfirmed"}}
    settings = {"placement": {"origin": {"status": "unconfirmed"}}}
    export = {"format": "rs274x", "origin": "absolute",
              "drill": {"format": "excellon", "zero_suppression": "trailing", "decimal_places": 4,
                        "separate_files": True},
              "extensions": {"pcba": {"drill_units": "in"}}}
    expect(checks_fab.supplier_rules(rules, settings, export)["status"] == "unconfirmed",
           "an open plane and an open placement convention stay unconfirmed")
    rules["plane_interpretation"]["status"] = "confirmed"
    settings["placement"]["origin"]["status"] = "confirmed"
    expect(checks_fab.supplier_rules(rules, settings, export)["status"] == "pass",
           "confirmed conventions that match the settings pass")
    export["drill"]["decimal_places"] = 6
    expect(checks_fab.supplier_rules(rules, settings, export)["status"] == "fail",
           "a setting that differs from the rule fails")


def captured_identity() -> tuple:
    export = load_check_module("export")
    return export.resolve_image(IMAGE_REF, LOCK_DIGEST), export


def test_design_erc_seeded_violation_fails():
    identity, export = captured_identity()
    checks_design = load_check_module("checks_design")
    text = (STANDARD / "kicad/board.kicad_sch").read_text(encoding="utf-8")
    clean = export.run_erc(identity, text.encode("utf-8"))
    expect(checks_design.erc(clean, "10.0.5")["status"] == "pass", "the standard schematic is clean")
    seeded_text = re.sub(r'  \(global_label "VCC"[^\n]*\n', "", text, count=1)
    expect(seeded_text != text, "the seeded label is removed")
    seeded = export.run_erc(identity, seeded_text.encode("utf-8"))
    expect(checks_design.erc(seeded, "10.0.5")["status"] == "fail", "a seeded unconnected pin fails ERC")


def test_design_parity_seeded_pad_fails():
    identity, export = captured_identity()
    checks_design = load_check_module("checks_design")
    sch = (STANDARD / "kicad/board.kicad_sch").read_bytes()
    board = (STANDARD / "kicad/board.kicad_pcb").read_text(encoding="utf-8")
    netlist = export.run_netlist(identity, sch)
    expect(checks_design.parity(netlist, board.encode("utf-8"), "10.0.5")["status"] == "pass",
           "the standard board matches its schematic")
    start = board.index('"Reference" "D3"')
    at = board.index('(net 5 "N3")', start)
    seeded = board[:at] + '(net 6 "N4")' + board[at + len('(net 5 "N3")'):]
    result = checks_design.parity(netlist, seeded.encode("utf-8"), "10.0.5")
    expect(result["status"] == "fail" and any(r["code"] == "design.parity_mismatch" for r in result["reasons"]),
           "a seeded pad on another net fails parity")


def test_final_gate_after_validation_refuses_all_staged_changes():
    """The final gate refuses changes after validation and preserves an earlier package."""
    cases = [("copper", "package.hash_mismatch"), ("manifest", "package.hash_mismatch"),
             ("extra", "package.extra_file"), ("missing", "package.missing_file"),
             ("link", "package.link"), ("hard_link", "package.link")]
    for case, code in cases:
        with tempfile.TemporaryDirectory() as tmp:
            project = package_project(Path(tmp))
            prior = project / "out/pcba/packages/prior"
            prior.mkdir(parents=True)
            (prior / "keep.txt").write_bytes(b"prior package")
            staging = project / "out/pcba/.package-staging"

            def alter():
                copper = staging / "fab/gerber/board-B_Cu.gbl"
                if case == "copper":
                    copper.write_bytes(b"changed copper\n")
                elif case == "manifest":
                    target = staging / "manifest.json"
                    target.write_bytes(target.read_bytes() + b" ")
                elif case == "extra":
                    (staging / "extra.txt").write_bytes(b"extra")
                elif case == "missing":
                    copper.unlink()
                elif case == "link":
                    copper.unlink()
                    copper.symlink_to(prior / "keep.txt")
                else:
                    os.link(copper, project / "hard-link.txt")

            expect_package_refusal(case, lambda: in_process_package(project, {"after_validate": alter}),
                                   code, project / "out/pcba/packages/pkg-hook", staging)
            expect((prior / "keep.txt").read_bytes() == b"prior package", "The earlier package is unchanged.")


def test_inventory_uses_board_holes_without_interface_holes():
    """The package measures four board holes when the interface lists no hole."""
    with tempfile.TemporaryDirectory() as tmp:
        project = package_project(Path(tmp))
        interface = project / "mechanical/board-interface.json"
        record = json.loads(interface.read_bytes())
        record["holes"] = []
        interface.write_text(json.dumps(record), encoding="utf-8")
        code, stdout, stderr = run_package(project)
        expect(code == 0, f"The package failed: {stdout} {stderr}")
        pkg = project / "out/pcba/packages/pkg-one"
        inventory = json.loads((pkg / "reports/board-hole-inventory.json").read_bytes())
        expect(len(inventory["holes"]) == 4, "The board has four holes.")
        expect(inventory["board_sha256"] == file_sha(project / BOARD_REL), "The inventory binds the board bytes.")
        expect(inventory["image_identity"] == LOCK_DIGEST, "The inventory binds the measured image identity.")
        evidence = json.loads((pkg / "evidence/fab.drill_split.json").read_bytes())
        expect(evidence["status"] == "pass", "The drill files match all four board holes.")


def measured_holes(board: bytes):
    """Return the worker inventory and the drill reference from captured board bytes."""
    identity, export = captured_identity()
    worker = (SKILL_SCRIPTS / "board_inventory_worker.py").read_bytes()
    record = json.loads(export.run_board_inventory(identity, board, worker))
    holes = [{"id": h["object"], "x": h["x_mm"], "y": h["y_mm"],
              "diameter_mm": h["diameter_mm"], "plated": h["plated"]} for h in record["holes"]]
    return record, holes


def test_inventory_measures_transformed_pad_and_via():
    """The worker measures global pad coordinates, plating and the through via."""
    board = (STANDARD / BOARD_REL).read_text(encoding="utf-8").replace('(at 30 40 0)', '(at 30 40 90)')
    record, _ = measured_holes(board.encode())
    expect(record["refused"] == [], "The worker supports the fixture holes.")
    holes = {h["object"]: h for h in record["holes"]}
    expect((holes["J1.2"]["x_mm"], holes["J1.2"]["y_mm"]) == (30, 37.46),
           "The second connector pad rotates about the footprint origin.")
    expect(holes["MH1."]["plated"] is False, "The mounting hole is nonplated.")
    via = [h for h in record["holes"] if h["kind"] == "via"]
    expect(len(via) == 1 and (via[0]["x_mm"], via[0]["y_mm"], via[0]["diameter_mm"]) == (45, 30, 0.3),
           "The worker measures the through via independently.")


def test_inventory_refuses_oval_pad():
    """The worker names an unsupported oval drill."""
    board = (STANDARD / BOARD_REL).read_text(encoding="utf-8").replace('(drill 1.0)', '(drill oval 1.0 1.5)', 1)
    record, _ = measured_holes(board.encode())
    expect(any(h["object"] == "J1.1" and "round" in h["reason"] for h in record["refused"]),
           "The worker names the unsupported pad.")
    with tempfile.TemporaryDirectory() as tmp:
        project = package_project(Path(tmp))
        (project / BOARD_REL).write_text(board, encoding="utf-8")
        code, stdout, stderr = run_package(project)
        expect(code == 1, "The package refuses the oval drill.")
        expect_one_finding(stdout, stderr, "drill.unsupported", "oval drill")


def test_measured_drill_reference_detects_missing_pad_via_and_duplicate():
    """The drill comparison detects missing pads, missing vias and duplicate holes."""
    _, holes = measured_holes((STANDARD / BOARD_REL).read_bytes())
    checks = load_check_module("checks_fab")
    plated = b'M48\nFMAT,2\nINCH,LZ\nT1C0.0394\nT2C0.0118\n%\nG90\nG05\nT1\nX011811Y-015748\nX012811Y-015748\nT2\nX017717Y-011811\nM30\n'
    nonplated = excellon([(50/25.4, -50/25.4)], "0.1260")
    files = {"board-PTH.drl": plated, "board-NPTH.drl": nonplated}
    def compare(raw):
        return checks.drill_split({**files, "board-PTH.drl": raw}, 4, holes, "board-PTH.drl", "board-NPTH.drl")
    expect(compare(plated)["status"] == "pass", "The independently specified holes match the board.")
    for line, name in [(b'X011811Y-015748\n', "J1.1"), (b'X017717Y-011811\n', "via@")]:
        result = compare(plated.replace(line, b""))
        expect(any(r["code"] == "fab.drill_missing" and name in r["text"] for r in result["reasons"]),
               "The comparison names the missing board hole.")
    result = compare(plated.replace(b'X011811Y-015748\n', b'X011811Y-015748\n' * 2))
    expect(any(r["code"] == "fab.drill_extra" for r in result["reasons"]), "The duplicate hole fails.")


def test_bom_policy_and_manufacturer_comparison():
    """The BOM comparison applies the captured policy and compares the manufacturer."""
    import io
    import openpyxl
    checks = load_check_module("checks_asm")
    sierra = load_check_module("sierra")
    group = {"manufacturer": "Maker", "mpn": "Part", "references": ["J1"], "quantity_per_board": 1,
             "variant_state": "populate", "installation_method": "hand_installed"}
    table = [["BOM"], [], [], [], [], [], sierra.SAMPLE_HEADERS]
    empty = sierra.xlsx_bytes(table)
    expect(checks.bom_consistent(empty, [group], "exclude_from_bom")["status"] == "pass",
           "The excluded hand-installed part is absent from the supplier BOM.")
    expect(checks.bom_consistent(empty, [group], "include_in_bom")["status"] == "fail",
           "The included hand-installed part cannot be absent.")
    table.append([1, 1, "Part", "", "J1", "", "", "", "", "", "Maker"])
    raw = sierra.xlsx_bytes(table)
    expect(checks.bom_consistent(raw, [group], "include_in_bom")["status"] == "pass", "The matching row passes.")
    wb = openpyxl.load_workbook(io.BytesIO(raw))
    wb.active.cell(8, 11).value = "Another maker"
    out = io.BytesIO()
    wb.save(out)
    expect(checks.bom_consistent(out.getvalue(), [group], "include_in_bom")["status"] == "fail",
           "A different manufacturer fails the independent comparison.")


def test_test_record_variant_instruction_and_duplicate_refused():
    """The evidence compares the variant and instruction and refuses duplicate steps."""
    checks = load_check_module("checks_asm")
    hand = [{"reference": "J1", "reason": "Install J1 after reflow."}]
    original = {"variant": "base", "physical_test_passed": False,
                "items": [{"id": "hand-install.J1", "reference": "J1",
                           "instruction": hand[0]["reason"], "status": "not measured"}]}
    def examine(record):
        return checks.test_record(json.dumps(record).encode(), {}, hand, "base")
    expect(examine(original)["status"] == "pass", "The matching record passes.")
    for change, code in [("variant", "asm.test_variant_mismatch"),
                         ("instruction", "asm.test_instruction_mismatch"),
                         ("missing_instruction", "asm.test_instruction_mismatch"),
                         ("duplicate", "asm.test_step_duplicate")]:
        record = json.loads(json.dumps(original))
        if change == "variant":
            record["variant"] = "no-led"
        elif change == "instruction":
            record["items"][0]["instruction"] = "Use another instruction."
        elif change == "missing_instruction":
            del record["items"][0]["instruction"]
        else:
            record["items"].append(dict(record["items"][0]))
        result = examine(record)
        expect(result["status"] == "fail" and any(r["code"] == code for r in result["reasons"]),
               f"The evidence refuses {change}.")


def test_sierra_standard_layout_content_hash_and_byte_binding():
    """The Sierra command uses the standard path and records the full input hash."""
    with tempfile.TemporaryDirectory() as tmp:
        project = standard_copy(Path(tmp))
        code, stdout, stderr = run_sierra(project, board=BOARD_REL)
        expect(code == 0, f"The standard Sierra run failed: {stdout} {stderr}")
        record = json.loads((project / "out/pcba/sierra/reports/sierra-status.json").read_bytes())
        import yaml
        profile = project / "manufacturing/supplier.yaml"
        content = yaml.safe_load(profile.read_text())["content_sha256"]
        expect(record["profile_sha256"] == content, "The status records the canonical content hash.")
        bound = [item for item in record["inputs"] if item["role"] == "supplier_profile"]
        expect(len(bound) == 1 and bound[0]["sha256"] == file_sha(profile), "The input records the full file hash.")


def test_package_refuses_unexamined_drill_settings_before_tools():
    """The package refuses unsupported drill settings before it calls an export tool."""
    import yaml
    export = load_check_module("export")
    original = export.resolve_image
    calls = []
    def unexpected(*args):
        calls.append(args)
        raise AssertionError("The package called a tool before it refused the settings.")
    cases = [("origin", "board"), ("zero_suppression", "leading"),
             ("zero_suppression", "none"), ("drill_units", "mm"),
             ("decimal_places", 5), ("separate_files", False)]
    export.resolve_image = unexpected
    try:
        for field, value in cases:
            with tempfile.TemporaryDirectory() as tmp:
                project = package_project(Path(tmp))
                path = project / "manufacturing/export.yaml"
                record = yaml.safe_load(path.read_text())
                if field == "origin":
                    record[field] = value
                elif field == "drill_units":
                    record["extensions"]["pcba"][field] = value
                else:
                    record["drill"][field] = value
                path.write_text(yaml.safe_dump(record), encoding="utf-8")
                expected_code = "schema.invalid" if field == "separate_files" else "export.drill_setting_unsupported"
                expect_package_refusal(field, lambda: in_process_package(project),
                                       expected_code,
                                       project / "out/pcba/packages/pkg-hook", project / "out/pcba/.package-staging")
        expect(calls == [], "No unsupported setting reaches the tool.")
    finally:
        export.resolve_image = original


TESTS = [value for name, value in sorted(globals().items()) if name.startswith("test_") and callable(value)]


def main() -> int:
    failures = 0
    for test in TESTS:
        try:
            test()
            print(f"PASS {test.__name__}")
        except AssertionError as err:
            failures += 1
            print(f"FAIL {test.__name__}: {err}")
    print(f"{len(TESTS) - failures} passed, {failures} failed")
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
