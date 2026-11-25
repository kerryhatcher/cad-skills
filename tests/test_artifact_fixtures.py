# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Focused checks for the artifact fixtures A1 and A2.

  uv run tests/test_artifact_fixtures.py            # all tests
  uv run tests/test_artifact_fixtures.py a1         # only tests with 'a1' in their name

The checks read repository files and run the identity reader. They start no container,
no KiCad process and no simulator. They call no provider and contact no supplier.
The expected values come from the design. They are not copied from tool output.
"""

from __future__ import annotations

import hashlib
import json
import math
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / "tests" / "eval" / "fixtures" / "artifacts"
A1_BEFORE = FIXTURES / "A1" / "before"
A1_AFTER = FIXTURES / "A1" / "after"
TEMPLATE = ROOT / "skills" / "pcb-design" / "templates" / "rc-bare-board"
IDENTITY = ROOT / "skills" / "pcb-design" / "scripts" / "identity.py"


def sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def tree_hashes(root: Path) -> dict[str, str]:
    return {p.relative_to(root).as_posix(): sha(p) for p in sorted(root.rglob("*")) if p.is_file()}


def expect(condition: bool, message: str) -> None:
    if not condition:
        raise AssertionError(message)


def run_identity(*args: str) -> str:
    """Run the identity reader with the current interpreter. It uses the standard library only."""
    done = subprocess.run([sys.executable, str(IDENTITY), *args], capture_output=True, text=True)
    expect(done.returncode == 0, f"identity.py {args[0]} exited {done.returncode}: {done.stderr}")
    return done.stdout


# ---------------------------------------------------------------- A1: pcb-design edit


def test_a1_before_is_the_accepted_template():
    """The before tree matches the accepted RC template byte for byte."""
    expect(tree_hashes(A1_BEFORE) == tree_hashes(TEMPLATE), "before tree differs from the template")


def test_a1_schematic_changes_one_value_line():
    """The only schematic change is one Value line, from 10k to 20k."""
    before = (A1_BEFORE / "kicad" / "board.kicad_sch").read_text(encoding="utf-8").splitlines()
    after = (A1_AFTER / "kicad" / "board.kicad_sch").read_text(encoding="utf-8").splitlines()
    expect(len(before) == len(after), "the schematic line count changed")
    changed = [i for i, (a, b) in enumerate(zip(before, after)) if a != b]
    expect(len(changed) == 1, f"expected one changed schematic line, found {len(changed)}")
    i = changed[0]
    expect(before[i].strip() == '(property "Value" "10k"', "the changed line is not the 10k value")
    expect(after[i].strip() == '(property "Value" "20k"', "the new line is not the 20k value")


def test_a1_expected_difference_is_hand_written_and_matches_identity():
    """The expectation names the one design change. The identity reader finds exactly that change."""
    expect_file = A1_AFTER / "expect" / "r2-value.json"
    data = json.loads(expect_file.read_text(encoding="utf-8"))
    expected = {"differences": [{"op": "changed", "class": "footprint", "ident": "R2",
                                 "field": "value", "before": "10k", "after": "20k"}]}
    expect(data == expected, "the expectation does not name the 10k to 20k change of R2")
    bound = json.loads((A1_AFTER / "out" / "reports" / "update.expect.json").read_text(encoding="utf-8"))
    expect(bound == expected, "the bound expectation copy differs in content from the hand-written expectation")
    with tempfile.TemporaryDirectory() as tmp:
        before_json = Path(tmp) / "before.json"
        after_json = Path(tmp) / "after.json"
        run_identity("snapshot", str(TEMPLATE / "kicad" / "board.kicad_pcb"), "-o", str(before_json))
        run_identity("snapshot", str(A1_AFTER / "kicad" / "board.kicad_pcb"), "-o", str(after_json))
        result = json.loads(run_identity("compare", str(before_json), str(after_json), "--expect", str(expect_file)))
    expect(result["status"] == "equal", f"identity comparison is not equal: {result}")
    expect(result["unexpected"] == [] and result["missing"] == [], f"identity differences: {result}")
    expect(result["observed"] == 1 and result["expected"] == 1, f"unexpected counts: {result}")


def test_a1_interface_is_bound_by_the_tool_with_byte_bindings():
    """The interface names the edited board. The result record binds the template board and the expectation."""
    iface = json.loads((A1_AFTER / "mechanical" / "board-interface.json").read_text(encoding="utf-8"))
    expect(iface["board_sha256"] == sha(A1_AFTER / "kicad" / "board.kicad_pcb"),
           "the interface does not name the edited board")
    record = json.loads((A1_AFTER / "out" / "reports" / "interface.result.json").read_text(encoding="utf-8"))
    expect(record["status"] == "pass", f"interface result is not pass: {record['status']}")
    expect(record["prior_board_sha256"] == sha(A1_BEFORE / "kicad" / "board.kicad_pcb"),
           "the prior board hash is not the template board hash")
    expect(record["expect_sha256"] == sha(A1_AFTER / "out" / "reports" / "update.expect.json"),
           "the expectation hash does not match the bound expectation copy")
    expect(record["interface_sha256"] == sha(A1_AFTER / "mechanical" / "board-interface.json"),
           "the interface hash does not match the interface file")


def test_a1_simulation_matches_the_independent_formula():
    """The RC step response at 1 ms with R2 = 20 kohm equals 3.3 V times (1 - exp(-0.5))."""
    expected = 3.3 * (1 - math.exp(-1e-3 / (20e3 * 100e-9)))
    assertion = json.loads((A1_AFTER / "simulations" / "assertions.json").read_text(encoding="utf-8"))[0]
    expect(abs(assertion["expected"] - expected) <= 1e-3, f"assertion expected value {assertion['expected']} differs")
    expect(abs(assertion["tolerance"] - 0.01 * expected) < 1e-4, "tolerance is not one percent of the value")
    circuit = (A1_AFTER / "simulations" / "rc.cir").read_text(encoding="utf-8")
    expect("R2 in out 20k" in circuit, "the circuit does not model R2 = 20k")
    result = json.loads((A1_AFTER / "out" / "reports" / "sim.result.json").read_text(encoding="utf-8"))
    measured = float(re.search(r"vtau = ([0-9.]+)", result["findings"][0]["description"]).group(1))
    expect(abs(measured - expected) <= assertion["tolerance"], f"measured {measured} is outside the tolerance")




REPORTS = A1_AFTER / "out" / "reports"


def report(name: str) -> dict:
    return json.loads((REPORTS / name).read_text(encoding="utf-8"))


def test_a1_erc_and_drc_records_pass():
    """The retained ERC and DRC records pass with no finding and no waiver."""
    for op in ("erc", "drc"):
        result = report(f"{op}.result.json")
        expect(result["operation"] == op, f"{op} record names {result['operation']}")
        expect(result["status"] == "pass", f"{op} status is {result['status']}")
        expect(result["tool_exit"] == 0 and result["exit_code"] == 0, f"{op} exit codes are not 0")
        expect(result["findings"] == [] and result["unwaived"] == [] and result["waived"] == [],
               f"{op} record holds findings or waivers")


def test_a1_update_record_is_ready_with_equal_identity():
    """The retained update record is ready, its identity comparison is equal, and its options are off."""
    result = report("update.result.json")
    expect(result["operation"] == "update", f"update record names {result['operation']}")
    expect(result["state"] == "ready" and result["status"] == "pass", "update record is not ready and pass")
    expect(result["identity"] == "equal", f"identity is {result['identity']}")
    expect(result["tool_exit"] == 0 and result["exit_code"] == 0, "update exit codes are not 0")
    expect(result["findings"] == [] and result["unwaived"] == [], "update record holds findings")
    expect(result["options"] == {"delete": "off", "relink": "off", "replace": "off"}, "update options differ")


def test_a1_raw_outputs_match_their_bindings():
    """Each raw output file is named by its hash, and its bytes have that hash. Each tool exit is 0."""
    for op in ("erc", "drc", "sim", "update"):
        binding = report(f"{op}.binding.json")
        expect(binding["operation"] == op, f"{op} binding names {binding['operation']}")
        expect(binding["tool_exit"] == 0, f"{op} tool exit is {binding['tool_exit']}")
        raw = A1_AFTER / binding["raw_file"]
        expect(raw.is_file(), f"{op} raw file is missing")
        expect(sha(raw) == binding["raw_sha256"], f"{op} raw file bytes differ from raw_sha256")
        expect(binding["raw_sha256"] in raw.name, f"{op} raw file name does not carry its hash")


def test_a1_result_records_name_their_binding_files():
    """Each result record names the binding file that the tool wrote for it."""
    for op in ("erc", "drc", "sim", "update"):
        result = report(f"{op}.result.json")
        expect(result["binding_sha256"] == sha(REPORTS / f"{op}.binding.json"),
               f"{op} result does not name its binding file")


def test_a1_closure_hashes_match_the_frozen_bytes():
    """Each closure entry names a file of the after tree with exactly that hash."""
    for op in ("erc", "drc", "sim"):
        closure = report(f"{op}.binding.json")["closure"]
        expect(closure, f"{op} binding has an empty closure")
        for rel, digest in closure.items():
            path = A1_AFTER / rel
            expect(path.is_file(), f"{op} closure file is missing: {rel}")
            expect(sha(path) == digest, f"{op} closure hash differs for {rel}")
        expect(closure["kicad/board.kicad_pcb"] == sha(A1_AFTER / "kicad" / "board.kicad_pcb"),
               f"{op} closure does not name the edited board")

# ---------------------------------------------------------------- A2: fabrication package input

A2 = FIXTURES / "A2"
A2_PROFILE = A2 / "profile" / "oshpark-two-layer.yaml"
SKILL_PROFILE = ROOT / "skills" / "pcb-fab-package" / "supplier" / "profiles" / "oshpark-two-layer.yaml"


def test_a2_project_inputs_match_the_accepted_template():
    """Every template file is present in the fixture with the same bytes. Only out/fab is added."""
    template = tree_hashes(TEMPLATE)
    fixture = {k: v for k, v in tree_hashes(A2 / "project").items() if not k.startswith("out/fab/")}
    expect(fixture == template, "A2 project inputs differ from the accepted template")


def test_a2_profile_copy_is_the_selected_profile():
    """The profile copy equals the skill profile. The tool binds the profile content hash of that file."""
    expect(sha(A2_PROFILE) == sha(SKILL_PROFILE), "profile copy differs from the skill profile")
    content_hash = json.loads(A2_PROFILE.read_text(encoding="utf-8"))["content_sha256"]
    status = json.loads((A2 / "status.json").read_text(encoding="utf-8"))
    supplier = json.loads((A2 / "project" / "out" / "fab" / "supplier" / "supplier-result.json").read_text(encoding="utf-8"))
    expect(status["profile_sha256"] == content_hash, "status does not name the profile content hash")
    expect(supplier["profile_sha256"] == content_hash, "supplier result does not name the profile content hash")


def test_a2_source_manifest_matches_the_repository_sources():
    """Each line of sources.sha256 names a repository file whose bytes have that hash."""
    lines = (A2 / "sources.sha256").read_text(encoding="utf-8").splitlines()
    expect(len(lines) > 0, "source manifest is empty")
    for line in lines:
        digest, rel = line.split("  ", 1)
        expect((ROOT / rel).is_file(), f"source file is missing: {rel}")
        expect(sha(ROOT / rel) == digest, f"source hash differs: {rel}")


def test_a2_design_step_passes():
    """The design step exits 0 on the fixture project."""
    result = json.loads((A2 / "project" / "out" / "fab" / "design" / "design-result.json").read_text(encoding="utf-8"))
    expect(result["exit"] == 0, f"design exit is {result['exit']}")


def test_a2_order_multiple_fails_by_the_independent_rule():
    """Quantity 5 is not a multiple of 3, so the order condition must fail."""
    board = (A2 / "project" / "board.yaml").read_text(encoding="utf-8")
    quantity = int(re.search(r"^quantity: (\d+)$", board, re.MULTILINE).group(1))
    profile = json.loads(A2_PROFILE.read_text(encoding="utf-8"))
    multiple = profile["extensions"]["service.order_multiple"]["value"]
    expected = "fail" if quantity % multiple != 0 else "pass"
    supplier = json.loads((A2 / "project" / "out" / "fab" / "supplier" / "supplier-result.json").read_text(encoding="utf-8"))
    row = next(r for r in supplier["rows"] if r["condition"] == "service.order_multiple")
    expect(row["status"] == expected, f"order condition is {row['status']}, expected {expected}")


def test_a2_status_is_incomplete_and_matches_the_results():
    """The supplier step exits 1. The status record counts the rows of the result file."""
    supplier = json.loads((A2 / "project" / "out" / "fab" / "supplier" / "supplier-result.json").read_text(encoding="utf-8"))
    status = json.loads((A2 / "status.json").read_text(encoding="utf-8"))
    expect(supplier["exit"] == 1, f"supplier exit is {supplier['exit']}, expected 1")
    mandatory = [r for r in supplier["rows"] if r["mandatory"]]
    counts = {
        "mandatory_total": len(mandatory),
        "mandatory_pass": sum(1 for r in mandatory if r["status"] == "pass"),
        "mandatory_fail": sorted(r["condition"] for r in mandatory if r["status"] == "fail"),
        "mandatory_pending": sorted(r["condition"] for r in mandatory if r["status"] == "pending"),
        "recommendations_reported": sum(1 for r in supplier["rows"] if not r["mandatory"]),
    }
    expect(status["supplier"] == counts, f"status counts differ from the result rows: {counts}")
    expect(counts["mandatory_fail"] == ["service.order_multiple"], "unexpected mandatory failure")
    expect(counts["mandatory_pending"] == ["silk_line_min_short_text"], "unexpected pending condition")
    expect(status["overall"] == "incomplete", "status is not incomplete")
    expect(status["commands"]["package"] == "not run", "package must not be recorded as run")


if __name__ == "__main__":
    key = sys.argv[1] if len(sys.argv) > 1 else ""
    tests = [(n, f) for n, f in list(globals().items()) if n.startswith("test_") and key in n]
    failed = 0
    for name, fn in tests:
        try:
            fn()
            print(f"ok   {name}")
        except Exception as error:  # noqa: BLE001
            failed += 1
            print(f"FAIL {name}: {type(error).__name__}: {error}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    sys.exit(1 if failed else 0)
