# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Exercise the supplier prohibition with measured via spans and declared processes."""
import json
import tempfile
from pathlib import Path
import test_pcb_fab_workflow as base

W = base.workflow
KEY = "service.via_construction_prohibited"


def main():
    with tempfile.TemporaryDirectory(prefix="fab-vias-") as temporary:
        tmp = Path(temporary)
        project = base.fresh_project(tmp, "through")
        design = project / "out/fab/design"
        W.design(project, base.PROFILE, design)
        board_record = project / "board.yaml"
        original = board_record.read_text()
        for declaration, expected in [("standard_through", "pass"), ("unconfirmed", "pending"),
                                      (None, "pending"), ("filled_plated_via_in_pad", "fail")]:
            text = original.replace("via_process: standard_through", f"via_process: {declaration}")
            if declaration is None:
                text = original.split("\nextensions:")[0]
            board_record.write_text(text)
            out = project / "out/fab" / f"supplier-{declaration}"
            code, result = W.supplier(project, base.PROFILE, out, design)
            row = next(row for row in result["rows"] if row["condition"] == KEY)
            base.check(f"The declared process {declaration} gives {expected}.",
                       row["status"] == expected and row["via_count"] == 2 and code == 1, row)
            report = json.loads((out / "via-report.json").read_text())
            base.check(f"The report binds the board and declaration for {declaration}.",
                       report["measurement"]["board_sha256"] == base.sha((project / "kicad/board.kicad_pcb").read_bytes())
                       and report["board_record_sha256"] == base.sha(board_record.read_bytes()))
        board_record.write_text(original.replace("standard_through", "unknown-process"))
        try:
            W.supplier(project, base.PROFILE, project / "out/fab/invalid", design)
            code = 0
        except W.Stop as err:
            code = err.code
        base.check("An unknown declaration refuses with exit 2.", code == 2)
        fixture = base.ROOT / "tests/fixtures/pcb-fab-package/hole-clearance/internal-blind-via-0.2mm.kicad_pcb"
        for kind in ("buried", "blind"):
            project = base.fresh_project(tmp, kind)
            board = fixture.read_text()
            if kind == "blind":
                board = board.replace('(layers "In1.Cu" "In2.Cu")', '(layers "F.Cu" "In1.Cu")')
            (project / "kicad/board.kicad_pcb").write_text(board)
            before = W.snapshot(project, {"profile": base.PROFILE})
            out = project / "out/fab/supplier"
            code, result = W.supplier(project, base.PROFILE, out, project / "absent-design")
            row = result["rows"][0]
            base.check(f"The measured {kind} span fails before the absent design result.",
                       code == 1 and result["schema_id"].endswith("supplier-precondition")
                       and row["condition"] == KEY and row["status"] == "fail"
                       and row["prohibited_spans"][0]["construction"] == kind, result)
            base.check(f"The {kind} refusal preserves the source and writes no success binding.",
                       W.snapshot(project, {"profile": base.PROFILE}) == before
                       and not (out / "supplier-binding.json").exists())
            try:
                W.validate_supplier_result(result, base.fab.check_profile(base.PROFILE))
                refused = False
            except W.Stop:
                refused = True
            base.check(f"A package cannot use the {kind} precondition as a complete result.", refused)
        project = base.fresh_project(tmp, "no-vias")
        fixture = base.ROOT / "tests/fixtures/pcb-fab-package/hole-clearance/r24-internal-track-10mil.kicad_pcb"
        (project / "kicad/board.kicad_pcb").write_bytes(fixture.read_bytes())
        data = W.captured(project, {"profile": base.PROFILE})
        out = project / "out/fab/via-only"
        out.mkdir(parents=True)
        row = W.measure_vias(data, out, W.Outputs(project, out), W.runtime_identity(data["toolchain.lock.json"]),
                             base.fab.check_profile(base.PROFILE))
        base.check("A measured zero count makes the condition not applicable.",
                   row["via_count"] == 0 and row["status"] == "pass", row)
    passed = sum(ok for _, ok in base.RESULTS)
    print(f"\n{passed}/{len(base.RESULTS)} passed")
    return 0 if passed == len(base.RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
