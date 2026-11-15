# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Build the draft project and the draft package of the trial from the real final board (T13). Host script.

  uv run scripts/build_draft_package.py FINAL_DIR OUT_DIR

FINAL_DIR is `results/final`: the saved board and schematic, `export/`, `drc.json`, `erc.json` and the check results.
OUT_DIR gets `project/` and `package/`. Check them with
  uv run contracts/validate.py --project OUT_DIR/project --package OUT_DIR/package --json

The package status is `draft`. B5 selects no supplier, so it has no supplier evidence. The check `fab.profile_evidence`
is `pending`. The script invents no passed check. Each passed check has a real report: the ERC and DRC reports of
KiCad, the parity section of the DRC report, and the result of `check_exports.py`.
The supplier profile is a neutral placeholder (`none-selected`). It has no supplier limit.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
_spec = importlib.util.spec_from_file_location("validate", ROOT / "contracts/validate.py")
V = importlib.util.module_from_spec(_spec)
sys.modules["validate"] = V
_spec.loader.exec_module(V)
sys.path.insert(0, str(HERE))
import check_exports  # noqa: E402

LAYERS = [("copper_top", "F.Cu", "-F_Cu.gbr", "F_Cu"), ("copper_bottom", "B.Cu", "-B_Cu.gbr", "B_Cu"), ("mask_top", "F.Mask", "-F_Mask.gbr", "F_Mask"),
          ("mask_bottom", "B.Mask", "-B_Mask.gbr", "B_Mask"), ("silk_top", "F.Silkscreen", "-F_Silkscreen.gbr", "F_Silkscreen"),
          ("silk_bottom", "B.Silkscreen", "-B_Silkscreen.gbr", "B_Silkscreen"), ("paste_top", "F.Paste", "-F_Paste.gbr", "F_Paste"),
          ("paste_bottom", "B.Paste", "-B_Paste.gbr", "B_Paste"), ("outline", "Edge.Cuts", "-Edge_Cuts.gbr", "Edge_Cuts")]
KICAD_VERSION = "10.0.5"
# The derived trial image (log T0b). The digest is the image ID that the setup recorded in `RECORD_DIGEST`.
IMAGE = "localhost/cad-skills-trial:b5"
IMAGE_DIGEST = "sha256:d881df4ef3e2ec76995f4070596550db118b23e7f6db9017f09a418c44c4b1c2"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write(path: Path, content) -> bytes:
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, (dict, list)):
        content = json.dumps(content, indent=2) + "\n"
    data = content.encode() if isinstance(content, str) else content
    path.write_bytes(data)
    return data


def rect(w, h):
    return [{"x": 0, "y": 0}, {"x": w, "y": 0}, {"x": w, "y": h}, {"x": 0, "y": h}]


def build_project(final: Path, project: Path) -> None:
    pcb, sch = (final / "trial.kicad_pcb").read_bytes(), (final / "trial.kicad_sch").read_bytes()
    note = b"No supplier is selected for the B5 trial. This file is a neutral placeholder and not supplier evidence.\n"
    profile = {"schema_id": "cad-skills/supplier-profile", "schema_version": "1.0", "id": "none-selected", "revision": "0", "service": "No supplier selected",
               "source_url": "https://example.com/none-selected", "retrieved": "2026-11-14", "evidence_sha256": sha(note), "content_sha256": "0" * 64,
               "units": "mm", "limits": {"selection": {"kind": "recommendation", "scope": "fabrication", "value_kind": "text",
                                                       "value": "No supplier is selected. The trial has no supplier limit.",
                                                       "source_url": "https://example.com/none-selected", "retrieved": "2026-11-14"}},
               "division": {"kicad_dru": [], "project_settings": [], "geometric_tests": [], "manual_evidence": ["selection"]}}
    profile["content_sha256"] = V.canonical_hash(profile)
    board = {"schema_id": "cad-skills/board", "schema_version": "1.0", "name": "pcb-trial", "circuit_source": "kicad_native", "assembly": "bare_board",
             "supplier": {"id": profile["id"], "service": profile["service"], "profile_sha256": profile["content_sha256"]}, "quantity": 1, "variant": "base",
             "electrical_limits": {"supply_voltage": {"value": 3.3, "unit": "V"}},
             "mechanical": {"width_mm": 40.0, "height_mm": 25.0, "thickness_mm": 1.6},
             "coordinate_system": {"units": "mm", "origin": {"x_mm": 0, "y_mm": 0}, "x_axis": "right", "y_axis": "up"}, "release_revision": "A",
             "restrictions": [{"text": "The board is a trial board with no export-controlled function.", "source": "B5 trial statement, 2026-11-14"}]}
    variants = {"schema_id": "cad-skills/variants", "schema_version": "1.0", "variants": [
        {"id": "base", "references": {r: "populate" for r in ("J1", "R1", "R2", "C1", "D1")} | {"MH1": "exclude_from_assembly", "MH2": "exclude_from_assembly"}}]}
    export = {"schema_id": "cad-skills/export-settings", "schema_version": "1.0", "format": "rs274x", "units": "mm", "x2": False, "gerber": {"decimal_places": 6},
              "layers": [{"role": r, "kicad_layer": n, "suffix": s} for r, n, s, _ in LAYERS],
              "drill": {"format": "excellon", "zero_suppression": "leading", "decimal_places": 3, "plated_suffix": "-PTH.drl", "nonplated_suffix": "-NPTH.drl",
                        "separate_files": True}, "origin": "absolute"}
    toolchain = {"schema_id": "cad-skills/toolchain-lock", "schema_version": "1.0", "python": "3.13", "execution": "container",
                 "container": {"image": IMAGE, "digest": IMAGE_DIGEST},
                 "tools": {"kicad": {"used": True, "version": KICAD_VERSION, "source_url": "https://www.kicad.org/", "license": "GPL-3.0-or-later"},
                           "ngspice": {"used": True, "version": "44.2", "source_url": "https://ngspice.sourceforge.io/", "license": "BSD-3-Clause"}},
                 "libraries": [], "models": []}
    # Board coordinates: the lower-left corner of the outline (100,125 in KiCad) is the origin. X is right and Y is up.
    interface = {"schema_id": "cad-skills/board-interface", "schema_version": "1.0", "board_revision": "A", "board_sha256": sha(pcb), "units": "mm",
                 "origin_mm": {"x": 0, "y": 0}, "thickness_mm": 1.6, "geometry_tolerance_mm": 0.01, "outline": rect(40, 25), "cutouts": [],
                 "holes": [{"id": "MH1", "x": 3, "y": 22, "diameter_mm": 3.2, "plated": False}, {"id": "MH2", "x": 37, "y": 3, "diameter_mm": 3.2, "plated": False}],
                 "connector_frames": [], "height_limits": {"top_mm": 10, "bottom_mm": 2}, "enclosure_clearance_mm": 0.5,
                 "dimension_owners": {k: "mechanical" for k in ("outline", "holes", "connector_frames", "thickness", "height_limits")}}
    waivers = {"schema_id": "cad-skills/waivers", "schema_version": "1.0", "waivers": []}
    write(project / "board.yaml", board)
    write(project / "kicad/board.kicad_pcb", pcb)
    write(project / "kicad/board.kicad_sch", sch)
    write(project / "variants.yaml", variants)
    write(project / "manufacturing/supplier.yaml", profile)
    write(project / "manufacturing/export.yaml", export)
    write(project / "toolchain.lock.json", toolchain)
    write(project / "mechanical/board-interface.json", interface)
    write(project / "manufacturing/waivers.yaml", waivers)
    (project / "manufacturing/none-selected-note.txt").write_bytes(note)


def build_package(final: Path, project: Path, pkg: Path) -> dict:
    board = V.load_record(project / "board.yaml")
    inputs = [{"role": role, "path": rel, "sha256": sha((project / rel).read_bytes())} for role, rel in V.FIXED_INPUT_PATHS.items() if (project / rel).is_file()]
    outputs = []

    def out(rel, data, role, layer=None):
        data = write(pkg / rel, data)
        item = {"role": role, "path": rel, "sha256": sha(data), "size_bytes": len(data)}
        if layer:
            item["layer"] = layer
        outputs.append(item)
        return item

    exp = final / "export"
    for role, kicad_layer, suffix, name in LAYERS:
        out(f"gerber/board{suffix}", (exp / f"trial-{name}.gbr").read_bytes(), V.family_of(role), kicad_layer)
    out("gerber/board-PTH.drl", (exp / "trial-PTH.drl").read_bytes(), "drill_plated")
    out("gerber/board-NPTH.drl", (exp / "trial-NPTH.drl").read_bytes(), "drill_nonplated")
    out("docs/schematic.pdf", (exp / "schematic.pdf").read_bytes(), "schematic_pdf")
    out("docs/fabrication.pdf", (exp / "fabrication.pdf").read_bytes(), "fabrication_drawing")
    drc, erc = json.loads((final / "drc.json").read_text()), (final / "erc.json").read_bytes()
    results = check_exports.check(exp, final / "trial.kicad_pcb")
    by = {r["check"]: r for r in results}
    reports = {
        "design.erc": erc,
        "design.drc": json.dumps({k: v for k, v in drc.items() if k != "schematic_parity"}, indent=2).encode() + b"\n",
        "design.parity": json.dumps({"source": drc["source"], "schematic_parity": drc["schematic_parity"]}, indent=2).encode() + b"\n",
        # The file-name inventory alone does not show the copper side (review E1). The layer order comes from the file-function comment of each Gerber
        # and the copper order of the saved board. The inventory adds the effective plot settings, the attribute check and the exact placement rows.
        "fab.export_inventory": json.dumps([by["board.plot_settings"], by["gerber.layer_set"], by["gerber.no_active_attributes"], by["placement.rows"]], indent=2).encode() + b"\n",
        "fab.layer_order": json.dumps([by["gerber.layer_function"], by["gerber.layer_set"]], indent=2).encode() + b"\n",
        "fab.drill_split": json.dumps([by["drill.pth"], by["drill.npth"]], indent=2).encode() + b"\n",
        "fab.profile_evidence": b"Pending. B5 selects no supplier and has no supplier evidence.\n",
    }
    by_role = {}
    for item in inputs:
        by_role.setdefault(item["role"], []).append(item)
    checks = []
    for check_id in V.REQUIRED_CHECKS["bare_board"]:
        artifact = out(f"reports/{check_id}.json" if check_id != "fab.profile_evidence" else "reports/fab.profile_evidence.txt", reports[check_id], "report")
        passed = check_id != "fab.profile_evidence" and (check_id not in ("design.erc", "design.drc", "design.parity") or True)
        if check_id == "design.drc":
            passed = not drc["violations"] and not drc["unconnected_items"]
        if check_id == "design.parity":
            passed = not drc["schematic_parity"]
        if check_id == "design.erc":
            passed = all(not s["violations"] for s in json.loads(erc)["sheets"])
        if check_id.startswith("fab.") and check_id != "fab.profile_evidence":
            passed = all(r["status"] == "pass" for r in json.loads(reports[check_id]))
        status = "pass" if passed else ("pending" if check_id == "fab.profile_evidence" else "fail")
        listed = [{"path": m["path"], "sha256": m["sha256"]} for role in V.CHECK_INPUT_ROLES[check_id] for m in by_role[role]]
        tool = {"name": "check_exports.py", "version": "b5-trial"} if check_id.startswith("fab.") else {"name": "kicad-cli", "version": KICAD_VERSION}
        evidence = {"schema_id": "cad-skills/evidence", "schema_version": "1.0", "check_id": check_id, "status": status, "inputs": listed,
                    "artifact": {"path": artifact["path"], "sha256": artifact["sha256"]}, "method": "tool", "tool": tool}
        item = out(f"evidence/{check_id}.json", evidence, "evidence")
        checks.append({"id": check_id, "status": status, "evidence_path": item["path"], "evidence_sha256": item["sha256"]})
    manifest = {"schema_id": "cad-skills/manifest", "schema_version": "1.0", "release_id": "b5-trial-draft", "kind": "bare_board",
                "board_revision": board["release_revision"], "board_sha256": sha((project / "kicad/board.kicad_pcb").read_bytes()), "variant": board["variant"],
                "supplier": copy.deepcopy(board["supplier"]), "inputs": inputs, "outputs": outputs, "drill_applicability": [], "checks": checks,
                "status": "draft", "reasons": [{"code": "fab.profile_evidence_pending", "text": "B5 selects no supplier. The check fab.profile_evidence is pending."}], "tool_versions": {"kicad": KICAD_VERSION, "ngspice": "44.2"}}
    write(pkg / "manifest.json", manifest)
    return manifest


def main(argv=None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if len(args) != 2:
        print("build_draft_package: give FINAL_DIR and OUT_DIR")
        return 2
    final, out = Path(args[0]), Path(args[1])
    if (out / "project").exists() or (out / "package").exists():
        print("build_draft_package: the output directory is not empty. Use a new directory.")
        return 2
    build_project(final, out / "project")
    build_package(final, out / "project", out / "package")
    return 0


if __name__ == "__main__":
    sys.exit(main())
