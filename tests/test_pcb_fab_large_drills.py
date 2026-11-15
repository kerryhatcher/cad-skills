# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Measure 250 mil and 251 mil drills without an invented maximum."""
import json
import tempfile
from decimal import Decimal
from pathlib import Path
import test_pcb_fab_acceptance as base


def main():
    with tempfile.TemporaryDirectory(prefix="fab-large-drills-") as directory:
        for value in ("250", "251"):
            project = base.fresh_project(Path(directory), value)
            diameter = Decimal(value) * Decimal("0.0254")
            board = project / "kicad/board.kicad_pcb"
            text = board.read_text().replace("(size 3.2 3.2)", f"(size {diameter} {diameter})", 1)
            text = text.replace("(drill 3.2)", f"(drill {diameter})", 1)
            board.write_text(text)
            design = base.run_fab("design", "--project", str(project), "--profile", str(base.PROFILE))
            supplier = base.run_fab("supplier", "--project", str(project), "--profile", str(base.PROFILE))
            assert (project / "out/fab/supplier/supplier-result.json").is_file(), (design.returncode, design.stdout, design.stderr, supplier.returncode, supplier.stdout, supplier.stderr)
            inventory = json.loads((project / "out/fab/design/inventory.json").read_text())
            result = json.loads((project / "out/fab/supplier/supplier-result.json").read_text())
            row = next(row for row in result["rows"] if row["condition"] == "min_drill")
            base.check(f"The board inventory measures the {value} mil drill.",
                       sum(Decimal(str(hole["diameter"])) == diameter for hole in inventory["holes"]) == 1,
                       inventory["holes"])
            base.check(f"The {value} mil drill passes the supplier drill condition.", row["status"] == "pass", row)
            base.check(f"The {value} mil drill has no invented maximum row.",
                       not any("max_drill" in item["condition"] for item in result["rows"]))
            print(json.dumps({"mil": value, "diameter_mm": str(diameter), "board_sha256": base.sha(board.read_bytes()),
                              "design_exit": design.returncode, "supplier_exit": supplier.returncode, "drill_row": row}, sort_keys=True))
    passed = sum(ok for _, ok in base.RESULTS)
    print(f"\n{passed}/{len(base.RESULTS)} passed")
    return 0 if passed == len(base.RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
