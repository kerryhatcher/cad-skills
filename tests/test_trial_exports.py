# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Tests for examples/pcb-trial/scripts/check_exports.py and check_rc.py (host, no KiCad, no ngspice).

  uv run tests/test_trial_exports.py

The base files are real output of KiCad 10.0.5 and ngspice (results/final_r2/export, the saved board and results/final_r2/rc).
The first final revision (results/final) must fail the plot-setting and attribute checks. It is history.
Each test changes a copy. A negative test must fail the check that it targets.
"""

from __future__ import annotations

import shutil
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / "examples/pcb-trial"
FINAL = TRIAL / "results/final_r2"  # corrected final revision. results/final is the first revision (history).
HISTORY = TRIAL / "results/final"
sys.path.insert(0, str(TRIAL / "scripts"))
import check_exports as CE  # noqa: E402
import check_rc as RC  # noqa: E402


def export_copy(tmp: Path) -> Path:
    dest = tmp / "export"
    shutil.copytree(FINAL / "export", dest)
    return dest


BOARD = FINAL / "trial.kicad_pcb"


def failed(results) -> list[str]:
    return sorted(r["check"] for r in results if r["status"] == "fail")


def run(d: Path, board: Path = BOARD):
    return failed(CE.check(d, board))


def test_real_export_passes(tmp: Path):
    assert run(FINAL / "export") == []


def test_first_final_revision_fails_the_effective_settings(tmp: Path):
    got = failed(CE.check(HISTORY / "export", HISTORY / "trial.kicad_pcb"))
    assert got == ["board.plot_settings", "gerber.layer_function", "gerber.no_active_attributes"], got


def test_saved_plot_settings_are_checked(tmp: Path):
    text = BOARD.read_text()
    for old, new in (("(drillshape 0)", "(drillshape 1)"), ("(usegerberattributes no)", "(usegerberattributes yes)"),
                     ("(usegerberadvancedattributes no)", "(usegerberadvancedattributes yes)")):
        assert old in text
        board = tmp / "board.kicad_pcb"
        board.write_text(text.replace(old, new))
        assert "board.plot_settings" in run(FINAL / "export", board), old


def test_missing_gerber_layer_fails(tmp: Path):
    d = export_copy(tmp)
    (d / "trial-B_Paste.gbr").unlink()
    got = run(d)
    assert "gerber.layer_set" in got and "gerber.layer_function" in got, got


def test_swapped_copper_files_fail(tmp: Path):
    d = export_copy(tmp)
    top, bottom = d / "trial-F_Cu.gbr", d / "trial-B_Cu.gbr"
    a, b = top.read_bytes(), bottom.read_bytes()
    top.write_bytes(b)
    bottom.write_bytes(a)
    assert run(d) == ["gerber.layer_function"], "the file names are correct but the copper sides are swapped"


def test_file_function_declarations(tmp: Path):
    d = export_copy(tmp)
    path = d / "trial-F_Cu.gbr"
    text = path.read_text()
    line = "G04 #@! TF.FileFunction,Copper,L1,Top*"
    assert text.count(line) == 1
    path.write_text(text.replace(line + "\n", ""))
    assert run(d) == ["gerber.layer_function"], "a missing declaration fails"
    path.write_text(text.replace(line, line + "\n" + line))
    assert run(d) == ["gerber.layer_function"], "a duplicate declaration fails"
    path.write_text(text.replace(line, "G04 #@! TF.FileFunction,Copper,L1,Bot*"))
    assert run(d) == ["gerber.layer_function"], "an incorrect declaration fails"


def test_copper_order_comes_from_the_board(tmp: Path):
    text = BOARD.read_text()
    assert CE.copper_order(text) == {"F_Cu": "Copper,L1,Top", "B_Cu": "Copper,L2,Bot"}
    four = text.replace('(2 "B.Cu" signal)', '(4 "In2.Cu" signal)\n\t\t(6 "In1.Cu" signal)\n\t\t(2 "B.Cu" signal)', 1)
    assert four != text
    order = CE.copper_order(four)
    assert order == {"F_Cu": "Copper,L1,Top", "In1_Cu": "Copper,L2,Inr", "In2_Cu": "Copper,L3,Inr", "B_Cu": "Copper,L4,Bot"}, order
    assert CE.copper_order("(kicad_pcb)") == {}, "a board without a layers block gives no copper mapping"


def test_active_attribute_commands_fail(tmp: Path):
    for command in ("%TF.FileFunction,Copper,L1,Top*%", "%TA.AperFunction,SMDPad,CuDef*%", "%TO.N,/VIN*%", "%TD*%"):
        d = tmp / ("e" + str(abs(hash(command))))
        shutil.copytree(FINAL / "export", d)
        path = d / "trial-Edge_Cuts.gbr"
        path.write_text(path.read_text().replace("%MOMM*%", "%MOMM*%\n" + command, 1))
        assert "%MOMM*%\n" + command in path.read_text()
        assert run(d) == ["gerber.no_active_attributes"], command
    d = export_copy(tmp)
    path = d / "trial-F_Cu.gbr"
    assert "G04 #@!" in path.read_text(), "an ordinary G04 #@! comment is allowed"
    assert run(d) == []


def test_wrong_drill_diameter_fails(tmp: Path):
    d = export_copy(tmp)
    path = d / "trial-PTH.drl"
    path.write_text(path.read_text().replace("T2C1.000", "T2C0.900"))
    assert run(d) == ["drill.pth"]


def test_moved_hole_fails(tmp: Path):
    d = export_copy(tmp)
    path = d / "trial-NPTH.drl"
    path.write_text(path.read_text().replace("X103000Y-103000", "X103500Y-103000"))
    assert run(d) == ["drill.npth"]


def test_placement_rotation_and_side_fail(tmp: Path):
    d = export_copy(tmp)
    path = d / "trial-pos.csv"
    text = path.read_text()
    path.write_text(text.replace("125.000000,-106.000000,180.000000,top", "125.000000,-106.000000,0.000000,top"))
    assert run(d) == ["placement.rows"], "a wrong rotation fails"
    path.write_text(text.replace('"R1","1k","R_0603_1608Metric",115.000000,-106.000000,0.000000,top', '"R1","1k","R_0603_1608Metric",115.000000,-106.000000,0.000000,bottom'))
    assert run(d) == ["placement.rows"], "a wrong side fails"


def test_duplicate_placement_rows_fail_in_either_order(tmp: Path):
    d = export_copy(tmp)
    path = d / "trial-pos.csv"
    lines = path.read_text().splitlines()
    header, rows = lines[0], lines[1:]
    assert len(rows) == 7
    c1 = next(r for r in rows if r.startswith('"C1"'))
    conflicting = c1.replace("125.000000,-118.000000", "999.000000,-118.000000")
    assert conflicting != c1
    for extra, name in ((c1, "identical"), (conflicting, "conflicting")):
        i = rows.index(c1)
        for order, new in (("extra first", rows[:i] + [extra] + rows[i:]), ("extra last", rows[:i + 1] + [extra] + rows[i + 1:])):
            path.write_text("\n".join([header] + new) + "\n")
            assert run(d) == ["placement.rows"], (name, order)
    path.write_text("\n".join([header] + rows[:-1]) + "\n")
    assert run(d) == ["placement.rows"], "a missing row fails: the row count is exactly 7"
    path.write_text("\n".join([header] + rows) + "\n")
    assert run(d) == []


def test_expected_values_do_not_read_the_export(tmp: Path):
    rows = CE.expected_rows()
    assert rows["D1"] == (125.0, -106.0, 180.0) and set(rows) == {"J1", "R1", "D1", "R2", "C1", "MH1", "MH2"}


def test_rc_real_logs(tmp: Path):
    ok, text = RC.judge(RC.measured((FINAL / "rc/good.log").read_text()))
    assert ok, text
    ok, text = RC.judge(RC.measured((FINAL / "rc/wrong.log").read_text()))
    assert not ok, "the log of the 220n capacitor fails the fixed assertion"


def test_rc_wrong_capacitor_in_the_design_fails(tmp: Path):
    # The circuit comes from the placement file. A wrong capacitor value changes the circuit, not the expected value.
    good = tmp / "good.cir"
    RC.make(FINAL / "export/trial-pos.csv", good)
    assert "C1 out 0 1e-07" in good.read_text()
    wrong = tmp / "wrong.cir"
    RC.make(FINAL / "rc/pos_wrong.csv", wrong)
    assert "C1 out 0 2.2e-07" in wrong.read_text()
    assert RC.EXPECTED_VOLT == 2.086 and RC.TOLERANCE == 0.01, "the expected value is fixed"


def test_rc_bounds_and_bad_input(tmp: Path):
    assert RC.judge(2.086 * 1.0099)[0] and not RC.judge(2.086 * 1.0101)[0]
    assert RC.judge(2.086 * 0.9901)[0] and not RC.judge(2.086 * 0.9899)[0]
    log = tmp / "empty.log"
    log.write_text("no value here\n")
    assert RC.main(["assert", str(log)]) == 2
    try:
        RC.value_of("ten")
        raise AssertionError("a bad value was accepted")
    except ValueError:
        pass


def main(argv):
    key = argv[0] if argv else ""
    tests = [(n, f) for n, f in globals().items() if n.startswith("test_") and key in n]
    bad = 0
    with tempfile.TemporaryDirectory() as td:
        for name, fn in tests:
            tmp = Path(td) / name
            tmp.mkdir()
            try:
                fn(tmp)
                print(f"ok   {name}")
            except Exception as err:  # noqa: BLE001
                bad += 1
                print(f"FAIL {name}: {type(err).__name__}: {err}")
    print(f"\n{len(tests) - bad}/{len(tests)} passed")
    return 1 if bad else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
