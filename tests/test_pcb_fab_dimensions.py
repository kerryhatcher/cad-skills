# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Measure board dimensions through the design and supplier commands."""
import json
import tempfile
from decimal import Decimal
from pathlib import Path
import test_pcb_fab_acceptance as base


def main():
    with tempfile.TemporaryDirectory(prefix="fab-dimensions-") as directory:
        for key, axis, values, expected in [
            ("board_max_width", "width", ["406.3", "406.4", "406.5"], ["pass", "pass", "fail"]),
            ("board_max_height", "height", ["558.7", "558.8", "558.9"], ["pass", "pass", "fail"]),
            ("board_min_edge", "width", ["6.34", "6.35", "6.36"], ["fail", "pass", "pass"]),
        ]:
            for value, want in zip(values, expected):
                project = base.fresh_project(Path(directory), f"{key}-{value}")
                path = project / "kicad/board.kicad_pcb"
                text = path.read_text()
                end_x = Decimal(100) + Decimal(value) if axis == "width" else Decimal(140)
                end_y = Decimal(100) + Decimal(value) if axis == "height" else Decimal(125)
                assert text.count("\t\t(end 140 125)\n") == 1
                path.write_text(text.replace("\t\t(end 140 125)\n", f"\t\t(end {end_x} {end_y})\n"))
                design = base.run_fab("design", "--project", str(project), "--profile", str(base.PROFILE))
                supplier = base.run_fab("supplier", "--project", str(project), "--profile", str(base.PROFILE))
                inventory = json.loads((project / "out/fab/design/inventory.json").read_text())
                result = json.loads((project / "out/fab/supplier/supplier-result.json").read_text())
                row = next(r for r in result["rows"] if r["condition"] == key)
                base.check(f"The saved board measures {value} mm on {axis}.",
                           Decimal(str(inventory["outline"][axis])) == Decimal(value), inventory["outline"])
                base.check(f"The supplier gives {want} for {key} at {value} mm.", row["status"] == want, row)
                print(json.dumps({"condition": key, "dimension_mm": value, "board_sha256": base.sha(path.read_bytes()),
                    "design_exit": design.returncode, "supplier_exit": supplier.returncode, "row": row}, sort_keys=True))
    passed = sum(ok for _, ok in base.RESULTS)
    print(f"\n{passed}/{len(base.RESULTS)} passed")
    return 0 if passed == len(base.RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
