# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Measure centerline bounds for board and footprint Edge.Cuts graphics."""
import json
import tempfile
from pathlib import Path
import test_pcb_fab_workflow as base


def main():
    base.workflow.runtime_identity((base.TEMPLATE / "toolchain.lock.json").read_bytes())
    with tempfile.TemporaryDirectory(prefix="fab-outline-") as directory:
        for owner in ("board", "footprint"):
            for stroke in ("0", "0.05", "1.0"):
                stage = Path(directory) / f"{owner}-{stroke}"
                stage.mkdir()
                shape = f'(gr_rect (start 0 0) (end 406.4 6.35) (stroke (width {stroke}) (type default)) (fill none) (layer "Edge.Cuts"))'
                if owner == "footprint":
                    shape = '(footprint "Outline" (layer "F.Cu") (at 0 0) ' + shape.replace("gr_rect", "fp_rect") + ')'
                source = ('(kicad_pcb (version 20260101) (generator "pcbnew") (general (thickness 1.6)) '
                          '(layers (0 "F.Cu" signal) (2 "B.Cu" signal) (25 "Edge.Cuts" user)) '
                          '(setup (pad_to_mask_clearance 0)) ' + shape + ')\n').encode()
                board = stage / "board.kicad_pcb"
                board.write_bytes(source)
                code, stdout, stderr = base.workflow.podman(stage, ["/usr/bin/python3", "/worker/board_inventory_slots.py", "/work/board.kicad_pcb"], worker=base.SCRIPTS)
                inventory = json.loads(stdout) if code == 0 else {}
                outline = inventory.get("outline", {})
                base.check(f"The {owner} outline with stroke {stroke} has exact centerline dimensions.",
                           code == 0 and outline == {"x": 0.0, "y": 0.0, "width": 406.4, "height": 6.35},
                           (code, outline, stderr))
                base.check(f"The {owner} source with stroke {stroke} stays unchanged.", board.read_bytes() == source)
                print(json.dumps({"owner": owner, "stroke_mm": stroke, "source_sha256": base.sha(source), "inventory": inventory}, sort_keys=True))
    passed = sum(ok for _, ok in base.RESULTS)
    print(f"\n{passed}/{len(base.RESULTS)} passed")
    return 0 if passed == len(base.RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
