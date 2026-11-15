# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Measure spacing, annular-ring and edge boundaries with the generated supplier rules."""
import json
import tempfile
from decimal import Decimal
from pathlib import Path
import test_pcb_fab_workflow as base

HEADER = '''(kicad_pcb (version 20260101) (generator "pcbnew")
 (general (thickness 1.6)) (paper "A4")
 (layers (0 "F.Cu" signal) (2 "B.Cu" signal) (25 "Edge.Cuts" user))
 (setup (pad_to_mask_clearance 0))
 (net 0 "") (net 1 "N1") (net 2 "N2")
 (gr_rect (start 0 0) (end 20 20) (stroke (width 0.05) (type default)) (fill none) (layer "Edge.Cuts"))
'''


def body(key, gap):
    if key == "min_space":
        y = Decimal(5) + Decimal("0.2") + gap
        return f''' (segment (start 5 5) (end 15 5) (width 0.2) (layer "F.Cu") (net "N1"))
 (segment (start 5 {y}) (end 15 {y}) (width 0.2) (layer "F.Cu") (net "N2"))\n'''
    if key == "min_annular_ring":
        diameter = Decimal("0.3") + 2 * gap
        return f' (via (at 10 10) (size {diameter}) (drill 0.3) (layers "F.Cu" "B.Cu") (net "N1"))\n'
    x = Decimal("0.1") + gap
    return f' (segment (start {x} 5) (end {x} 15) (width 0.2) (layer "F.Cu") (net "N1"))\n'


def main():
    profile = base.fab.check_profile(base.PROFILE)
    runtime = base.workflow.runtime_identity((base.TEMPLATE / "toolchain.lock.json").read_bytes())
    with tempfile.TemporaryDirectory(prefix="fab-rule-boundaries-") as directory:
        for key, values in [("min_space", ["5.9", "6", "6.1"]),
                            ("min_annular_ring", ["4.9", "5", "5.1"]),
                            ("edge_keepout", ["14.9", "15", "15.1"])]:
            for value, expected in zip(values, ["fail", "pass", "pass"]):
                stage = Path(directory) / f"{key}-{value}"
                stage.mkdir()
                gap = Decimal(value) * Decimal("0.0254")
                board = (HEADER + body(key, gap) + ")\n").encode()
                retained = base.ROOT / "tests/fixtures/pcb-fab-package/rule-boundaries" / f"{key}-{value}mil.kicad_pcb"
                assert retained.read_bytes() == board, "The retained board differs from the test input."
                (stage / "board.kicad_pcb").write_bytes(board)
                (stage / "board.kicad_dru").write_text(base.workflow.supplier_rules_text(profile))
                (stage / "board.kicad_pro").write_text(base.workflow.effective_pro(b"{}", profile))
                code, stdout, stderr = base.workflow.podman(stage, ["kicad-cli", "pcb", "drc", "--severity-all", "--format", "json",
                    "-o", "/work/drc.json", "/work/board.kicad_pcb"])
                report = json.loads((stage / "drc.json").read_text())
                hits = [row for row in report["violations"] if row["type"] in base.workflow.REPORT_KEYS[key]]
                result = "fail" if hits else "pass"
                base.check(f"The board {key} at {value} mil gives {expected}.", code == 0 and result == expected, hits)
                base.check(f"The independent {key} threshold agrees at {value} mil.",
                           base.fab.judge("minimum", value, str(profile["limits"][key]["value"])) == expected)
                print(json.dumps({"condition": key, "mil": value, "independent_gap_mm": str(gap),
                                  "board_sha256": base.sha(board), "runtime": runtime, "hits": hits}, sort_keys=True))
    passed = sum(ok for _, ok in base.RESULTS)
    print(f"\n{passed}/{len(base.RESULTS)} passed")
    return 0 if passed == len(base.RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
