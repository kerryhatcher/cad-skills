# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Tests for the U3 helpers `u3_netcheck.py`, `u3_start_board.py` and `u3_unread_audit.py` (host, no KiCad).

  uv run tests/test_trial_u3.py

The base board `results/skidl_u3/edits/baseline.kicad_pcb` is real output that KiCad 10.0.5 saved after the first
netlist import (step `GUI_U3base`). The netlists are real SKiDL 3.0.0 output. Each negative test changes a copy.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / "examples/pcb-trial"
EDITS = TRIAL / "results/skidl_u3/edits"
NETCHECK = TRIAL / "scripts/u3_netcheck.py"
START = TRIAL / "scripts/u3_start_board.py"
AUDIT = TRIAL / "scripts/u3_unread_audit.py"
BASE = EDITS / "baseline.kicad_pcb"
sys.path.insert(0, str(TRIAL / "scripts"))
import identity as ID  # noqa: E402


def net(op: str) -> Path:
    return EDITS / "net" / op / "trial.net"


def netcheck(board: Path, netlist: Path):
    r = subprocess.run(["uv", "run", "-q", str(NETCHECK), str(board), str(netlist)], capture_output=True, text=True)
    return r.returncode, (json.loads(r.stdout) if r.stdout.strip() else {}), r.stderr


def kinds(out: dict) -> list:
    return sorted((f["kind"], f.get("ref") or f.get("pad")) for f in out.get("findings", []))


def test_baseline_matches_its_netlist(tmp: Path):
    rc, out, _ = netcheck(BASE, net("none"))
    assert rc == 0 and out["components"] == 7 and out["pins"] == 10, (rc, out)


def test_added_part_is_a_missing_footprint(tmp: Path):
    rc, out, _ = netcheck(BASE, net("add-c2"))
    assert rc == 1 and kinds(out) == [("missing_footprint", "C2")], (rc, out)


def test_removed_part_is_an_extra_footprint(tmp: Path):
    rc, out, _ = netcheck(BASE, net("remove-d1"))
    assert rc == 1 and kinds(out) == [("extra_footprint", "D1")], (rc, out)


def test_changed_pad_net_is_found(tmp: Path):
    text = BASE.read_text()
    block_start = text.index('(property "Reference" "R1"')
    pad = text.index('(net "N_LED")', block_start)
    board = tmp / "b.kicad_pcb"
    board.write_text(text[:pad] + '(net "VIN")' + text[pad + len('(net "N_LED")'):])
    rc, out, _ = netcheck(board, net("none"))
    assert rc == 1 and kinds(out) == [("pad_net", "R1.2")], (rc, out)


def test_changed_path_is_found(tmp: Path):
    text = BASE.read_text().replace('(path "/91628e47-8f83-5ba1-abed-4cb134d83eea")', '(path "/00000000-0000-4000-8000-000000000000")')
    board = tmp / "b.kicad_pcb"
    board.write_text(text)
    rc, out, _ = netcheck(board, net("none"))
    assert rc == 1 and kinds(out) == [("path_mismatch", "R1")], (rc, out)


def test_renamed_reference_is_found_by_reference(tmp: Path):
    rc, out, _ = netcheck(BASE, net("rename-c1"))
    assert rc == 1 and kinds(out) == [("extra_footprint", "C1"), ("missing_footprint", "C9")], (rc, out)


def test_bad_input_exits_2(tmp: Path):
    (tmp / "empty.net").write_text("(export)\n")
    rc, out, err = netcheck(BASE, tmp / "empty.net")
    assert rc == 2 and "error" in out and "Traceback" not in err, (rc, out, err)
    rc, out, err = netcheck(tmp / "absent.kicad_pcb", net("none"))
    assert rc == 2 and "Traceback" not in err, (rc, out, err)


def test_start_board_is_reproduced(tmp: Path):
    out = tmp / "start.kicad_pcb"
    r = subprocess.run(["uv", "run", "-q", str(START), "--board", str(TRIAL / "results/native/baseline.kicad_pcb"),
                        "--extra", str(TRIAL / "expected/fixtures/vz_saved_by_kicad.kicad_pcb"), "--netlist", str(net("none")), "-o", str(out)],
                       capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert out.read_text() == (EDITS / "start.kicad_pcb").read_text()
    snap = ID.snapshot_text(out.read_text())
    assert (len(snap["footprints"]), len(snap["segments"]), len(snap["vias"]), len(snap["arcs"]), len(snap["zones"])) == (7, 6, 1, 1, 1)


def test_start_board_refuses_a_netlist_without_a_reference(tmp: Path):
    r = subprocess.run(["uv", "run", "-q", str(START), "--board", str(TRIAL / "results/native/baseline.kicad_pcb"),
                        "--extra", str(TRIAL / "expected/fixtures/vz_saved_by_kicad.kicad_pcb"),
                        "--netlist", str(TRIAL / "results/skidl_u3/run_g.net"), "-o", str(tmp / "x.kicad_pcb")], capture_output=True, text=True)
    assert r.returncode == 2 and "no tstamp for MH" in r.stderr and not (tmp / "x.kicad_pcb").exists(), (r.returncode, r.stderr)


def audit(after: Path):
    r = subprocess.run(["uv", "run", "-q", str(AUDIT), str(BASE), str(after)], capture_output=True, text=True)
    return r.returncode, json.loads(r.stdout)


def test_audit_finds_the_hidden_dnp_mark(tmp: Path):
    rc, out = audit(EDITS / "runs/footprint-r1-replace-off_r1/trial.kicad_pcb")
    assert rc == 1 and out["unread_changes"] == [{"ref": "R1", "form": "attr", "before": ["(attr smd)"], "after": ["(attr smd dnp)"]}], out


def test_audit_is_clean_for_a_no_edit_import(tmp: Path):
    rc, out = audit(EDITS / "runs/none_r1/trial.kicad_pcb")
    assert rc == 0 and out["footprints_compared"] == 7 and out["unread_changes"] == [], out


def test_audit_ignores_new_child_uuids(tmp: Path):
    text = BASE.read_text()
    first_line = text.index("(fp_line")
    at = text.index('(uuid "', first_line) + len('(uuid "')
    board = tmp / "b.kicad_pcb"
    board.write_text(text[:at] + "00000000-0000-4000-8000-0000000000ff" + text[at + 36:])
    rc, out = audit(board)
    assert rc == 0, out


def test_expectations_are_valid(tmp: Path):
    snap = json.loads(json.dumps(ID.snapshot_text(BASE.read_text())))
    files = sorted((EDITS / "expected").glob("*.json"))
    assert len(files) == 10, files
    for f in files:
        expected = json.loads(f.read_text())["differences"]
        ID.compare(snap, snap, expected)  # A repeated difference raises InputProblem.
    shift = json.loads((EDITS / "expected/line-shift.json").read_text())["differences"]
    assert len(shift) == 7 and all(d["field"] == "properties" for d in shift)


def main(argv):
    key = argv[0] if argv else ""
    tests = [(n, f) for n, f in globals().items() if n.startswith("test_") and key in n]
    failed = 0
    with tempfile.TemporaryDirectory() as td:
        for name, fn in tests:
            tmp = Path(td) / name
            tmp.mkdir()
            try:
                fn(tmp)
                print(f"ok   {name}")
            except Exception as e:  # noqa: BLE001
                failed += 1
                print(f"FAIL {name}: {type(e).__name__}: {e}")
    print(f"\n{len(tests) - failed}/{len(tests)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
