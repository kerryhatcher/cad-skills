# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Tests for examples/pcb-trial/scripts/identity.py (host, no KiCad).

  uv run tests/test_trial_identity.py

The base board `expected/fixtures/u1_saved_by_kicad.kicad_pcb` is real output that KiCad 10.0.5 saved after
the scripted update of the native fixture (run `U4_U1_c_110`). Each test changes the text of a copy.
"""

from __future__ import annotations

import json
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRIAL = ROOT / "examples/pcb-trial"
TOOL = TRIAL / "scripts/identity.py"
BASE = TRIAL / "expected/fixtures/u1_saved_by_kicad.kicad_pcb"
VZ = TRIAL / "expected/fixtures/vz_saved_by_kicad.kicad_pcb"
sys.path.insert(0, str(TRIAL / "scripts"))
import identity as ID  # noqa: E402

SEGMENT = '\t(segment\n\t\t(start 101 101)\n\t\t(end 105 101)\n\t\t(width 0.25)\n\t\t(layer "F.Cu")\n\t\t(net "/VIN")\n\t\t(uuid "aaaaaaaa-0000-4000-8000-000000000001")\n\t)\n'


def base_text() -> str:
    return BASE.read_text()


def with_segment(text: str) -> str:
    return text.rstrip()[:-1].rstrip() + "\n" + SEGMENT + ")\n"


def snap(text: str) -> dict:
    return json.loads(json.dumps(ID.snapshot_text(text)))


def result(before: str, after: str, expected: list) -> dict:
    return ID.compare(snap(before), snap(after), expected)


def cli(tmp: Path, before: str, after: str, expected: list):
    (tmp / "b.kicad_pcb").write_text(before)
    (tmp / "a.kicad_pcb").write_text(after)
    for name in ("b", "a"):
        r = subprocess.run(["uv", "run", "-q", str(TOOL), "snapshot", str(tmp / f"{name}.kicad_pcb"), "-o", str(tmp / f"{name}.json")], capture_output=True, text=True)
        if r.returncode != 0:
            return r.returncode, r.stdout
    (tmp / "e.json").write_text(json.dumps({"differences": expected}))
    r = subprocess.run(["uv", "run", "-q", str(TOOL), "compare", str(tmp / "b.json"), str(tmp / "a.json"), "--expect", str(tmp / "e.json")], capture_output=True, text=True)
    return r.returncode, r.stdout


def test_real_saved_output_is_read_in_full(tmp: Path):
    s = snap(base_text())
    refs = sorted(f["reference"] for f in s["footprints"].values())
    assert refs == ["C1", "D1", "J1", "MH1", "MH2", "R1", "R2"], refs
    assert all(f["path"].startswith("/") and f["at"] for f in s["footprints"].values())
    r1 = next(f for f in s["footprints"].values() if f["reference"] == "R1")
    assert r1["pads"]["1"]["net"] == "/VIN" and r1["pads"]["2"]["net"] == "/N_LED", r1["pads"]
    assert "footprint" in s["forms_seen"] and "gr_rect" in s["forms_seen"]
    assert ID.compare(s, s, [])["status"] == "equal"


def test_expected_difference_is_exact(tmp: Path):
    after = base_text().replace('(property "Value" "10k"', '(property "Value" "22k"', 1)
    assert after != base_text()
    expect = [{"op": "changed", "class": "footprint", "ident": "R2", "field": "value", "before": "10k", "after": "22k"}]
    assert result(base_text(), after, expect)["status"] == "equal"
    r = result(base_text(), after, [])
    assert r["status"] == "different" and len(r["unexpected"]) == 1, r
    r = result(base_text(), base_text(), expect)
    assert r["status"] == "different" and len(r["missing"]) == 1, "a listed difference that does not occur fails"
    wrong = [{**expect[0], "after": "33k"}]
    r = result(base_text(), after, wrong)
    assert r["status"] == "different" and r["unexpected"] and r["missing"], r


def test_unauthorized_move(tmp: Path):
    after = base_text().replace("(at 140.455 134.765)", "(at 141.455 134.765)", 1)
    assert after != base_text()
    r = result(base_text(), after, [])
    assert r["status"] == "different" and r["unexpected"][0]["field"] == "at" and r["unexpected"][0]["ident"] == "R1", r


def test_uuid_change(tmp: Path):
    after = base_text().replace('(uuid "8d5ec40a-f1b5-4a3a-b618-20355b9c4c1e")', '(uuid "8d5ec40a-f1b5-4a3a-b618-20355b9c4c1f")', 1)
    assert after != base_text()
    r = result(base_text(), after, [])
    ops = sorted((d["op"], d["ident"]) for d in r["unexpected"])
    assert ops == [("added", "R1"), ("removed", "R1")], r


def test_pad_net_change(tmp: Path):
    after = base_text().replace('(net "/VIN")', '(net "/GND")', 1)
    assert after != base_text()
    r = result(base_text(), after, [])
    assert r["status"] == "different" and r["unexpected"][0]["class"] == "pad" and r["unexpected"][0]["field"] == "net", r


def test_unrelated_track_deletion(tmp: Path):
    with_track = with_segment(base_text())
    r = result(with_track, base_text(), [])
    assert r["status"] == "different" and r["unexpected"][0] == {"class": "segment", "ident": "aaaaaaaa-0000-4000-8000-000000000001", "net": "/VIN", "op": "removed"}, r
    named = [{"op": "removed", "class": "segment", "ident": "aaaaaaaa-0000-4000-8000-000000000001", "net": "/VIN"}]
    assert result(with_track, base_text(), named)["status"] == "equal", "a routing object named by UUID and net is allowed"
    moved = with_track.replace("(end 105 101)", "(end 106 101)", 1)
    r = result(with_track, moved, [])
    assert r["unexpected"][0]["field"] == "end", "a changed track is a difference"


def test_added_footprint_lists_pad_nets(tmp: Path):
    block_start = base_text().index('\t(footprint "Resistor_SMD:R_0603_1608Metric"')
    text = base_text()
    # Remove the first R footprint in the before text: the after text has it as an addition.
    depth, i = 0, block_start
    while True:
        depth += 1 if text[i] == "(" else -1 if text[i] == ")" else 0
        i += 1
        if depth == 0 and i > block_start + 5:
            break
    before = text[:block_start] + text[i:]
    r = result(before, text, [])
    added = [d for d in r["unexpected"] if d["op"] == "added"]
    assert added and added[0]["pad_nets"] == {"1": "/VIN", "2": "/N_LED"} and added[0]["ident"] == "R1", r
    assert result(before, text, [{"op": "added", "class": "footprint", "ident": "R1", "lib_id": "Resistor_SMD:R_0603_1608Metric", "value": "1k",
                                  "pad_nets": {"1": "/VIN", "2": "/N_LED"}}])["status"] == "equal"


def test_unknown_top_level_form_stops_the_reader(tmp: Path):
    after = base_text().rstrip()[:-1].rstrip() + '\n\t(mystery_class\n\t\t(uuid "bbbbbbbb-0000-4000-8000-000000000002")\n\t)\n)\n'
    try:
        ID.snapshot_text(after)
        raise AssertionError("the reader accepted an unknown class")
    except ID.Unparsed as err:
        assert "identity.unparsed_class" in str(err)
    rc, out = cli(tmp, base_text(), after, [])
    assert rc == 3 and "identity.unparsed_class" in out, (rc, out)


def expect_problem(fn, code: str):
    try:
        fn()
    except ID.InputProblem as err:
        assert code in str(err), err
        return
    raise AssertionError(f"no {code} problem")


def test_added_footprint_lists_value(tmp: Path):
    text = base_text()
    start = text.index('\t(footprint "Capacitor_SMD:C_0603_1608Metric"')
    depth, i = 0, start
    while True:
        depth += 1 if text[i] == "(" else -1 if text[i] == ")" else 0
        i += 1
        if depth == 0 and i > start + 5:
            break
    before = text[:start] + text[i:]
    r = result(before, text, [])
    added = r["unexpected"][0]
    assert added["ident"] == "C1" and added["value"] == "100n", added
    good = [{"op": "added", "class": "footprint", "ident": "C1", "lib_id": added["lib_id"], "value": "100n", "pad_nets": added["pad_nets"]}]
    assert result(before, text, good)["status"] == "equal"
    wrong_value = text.replace('(property "Value" "100n"', '(property "Value" "WRONG"', 1)
    assert wrong_value != text
    r = result(before, wrong_value, good)
    assert r["status"] == "different" and r["unexpected"] and r["missing"], "a wrong added value fails"


def test_duplicate_expected_record_is_rejected(tmp: Path):
    after = base_text().replace('(property "Value" "10k"', '(property "Value" "22k"', 1)
    one = {"op": "changed", "class": "footprint", "ident": "R2", "field": "value", "before": "10k", "after": "22k"}
    assert result(base_text(), after, [one])["status"] == "equal"
    expect_problem(lambda: result(base_text(), after, [one, dict(one)]), "identity.duplicate_expectation")
    rc, out = cli(tmp, base_text(), after, [one, dict(one)])
    assert rc == 2 and "identity.duplicate_expectation" in out, (rc, out)


def test_duplicate_uuid_cannot_hide_a_segment(tmp: Path):
    with_track = with_segment(base_text())
    copy = SEGMENT.replace("(end 105 101)", "(end 999 101)")
    first = with_track.index(SEGMENT)
    hidden = with_track[:first] + copy + with_track[first:]
    expect_problem(lambda: snap(hidden), "identity.duplicate_uuid")
    rc, out = cli(tmp, with_track, hidden, [])
    assert rc == 2 and "identity.duplicate_uuid" in out, (rc, out)


def test_missing_uuid_is_rejected(tmp: Path):
    no_uuid = with_segment(base_text()).replace('\t\t(uuid "aaaaaaaa-0000-4000-8000-000000000001")\n', "", 1)
    expect_problem(lambda: snap(no_uuid), "identity.missing_uuid")


def test_saved_via_zone_and_arc_are_read(tmp: Path):
    s = snap(VZ.read_text())
    assert list(s["vias"].values()) == [{"net": "/VIN", "at": [120, 110, 0], "size": "0.6", "drill": "0.3", "layers": '(layers "F.Cu" "B.Cu")'}], s["vias"]
    (zone,) = s["zones"].values()
    assert zone["net"] == "/GND" and zone["name"] == "gnd_pour" and "142" in zone["polygon"], zone
    (arc,) = s["arcs"].values()
    assert arc["mid"] == [102, 106] and arc["net"] == "/VIN", arc
    assert ID.compare(s, s, [])["status"] == "equal"


def changed_text(old: str, new: str) -> str:
    text = VZ.read_text()
    assert text.count(old) == 1, (old, text.count(old))
    return text.replace(old, new, 1)


def test_via_zone_and_arc_changes_are_differences(tmp: Path):
    base = VZ.read_text()
    cases = (
        ("via", "(at 120 110)", "(at 121 110)", "at"),
        ("via", "(drill 0.3)", "(drill 0.35)", "drill"),
        ("arc", "(mid 102 106)", "(mid 102 107)", "mid"),
        ("zone", "(xy 148 108)", "(xy 149 108)", "polygon"),
    )
    for cls, old, new, field in cases:
        r = result(base, changed_text(old, new), [])
        assert r["status"] == "different", (cls, r)
        hits = [d for d in r["unexpected"] if d["class"] == cls and d["field"] == field]
        assert hits, (cls, field, r)
        # A zone polygon change shows in the polygon field and in the definition field. List each observed difference.
        listed = [{**d, "before": json.loads(d["before"]), "after": json.loads(d["after"])} for d in r["unexpected"]]
        assert result(base, changed_text(old, new), listed)["status"] == "equal", (cls, "listed change")
        assert result(base, changed_text(old, new), listed[1:])["status"] == "different" or len(listed) == 1, (cls, "an incomplete list fails")


def test_via_zone_and_arc_removal_by_uuid(tmp: Path):
    base = VZ.read_text()
    for cls, uid, key in (("via", "aaaaaaaa-0000-4000-8000-0000000000b1", "(via"), ("arc", "aaaaaaaa-0000-4000-8000-0000000000a1", "(arc"), ("zone", "aaaaaaaa-0000-4000-8000-0000000000c1", "(zone")):
        start = base.index("\t" + key + "\n")
        depth, i = 0, start
        while True:
            depth += 1 if base[i] == "(" else -1 if base[i] == ")" else 0
            i += 1
            if depth == 0 and i > start + 5:
                break
        after = base[:start] + base[i:]
        r = result(base, after, [])
        assert r["status"] == "different" and r["unexpected"][0]["op"] == "removed" and r["unexpected"][0]["ident"] == uid, (cls, r)
        listed = [{k: v for k, v in r["unexpected"][0].items()}]
        assert result(base, after, listed)["status"] == "equal", (cls, "a removal named by UUID is allowed")
        wrong = [{**listed[0], "ident": "aaaaaaaa-0000-4000-8000-0000000000ff"}]
        assert result(base, after, wrong)["status"] == "different", (cls, "a removal with another UUID fails")


def test_gate_expectations_come_from_the_baseline_only(tmp: Path):
    sys.path.insert(0, str(TRIAL / "scripts"))
    import gate_expect as GE  # noqa: E402
    baseline = tmp / "baseline.snap.json"
    baseline.write_text(json.dumps(snap(base_text())))
    out = tmp / "expected"
    assert GE.main([str(baseline), str(out)]) == 0
    add = json.loads((out / "add-c2.json").read_text())["differences"][0]
    assert add["value"] == "100n", add
    assert json.loads((out / "footprint-r1-replace-off.json").read_text()) == {"differences": []}


def test_cli_exit_codes(tmp: Path):
    rc, out = cli(tmp, base_text(), base_text(), [])
    assert rc == 0 and json.loads(out)["status"] == "equal", (rc, out)
    rc, out = cli(tmp, base_text(), base_text().replace("(at 140.455 134.765)", "(at 142 134.765)", 1), [])
    assert rc == 1, (rc, out)
    r = subprocess.run(["uv", "run", "-q", str(TOOL), "compare", str(tmp / "absent.json"), str(tmp / "absent.json"), "--expect", str(tmp / "absent.json")], capture_output=True, text=True)
    assert r.returncode == 2 and "Traceback" not in r.stderr, r.stderr


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
