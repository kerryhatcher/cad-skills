# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Helpers that build a valid project and a valid package in a temporary directory.

Nothing here is static. A test builds the tree, edits one thing, and examines the result.
The PCB, the schematic and the reports are small text files. They show record consistency.
They do not show that KiCad ran.
"""

from __future__ import annotations

import copy
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FIX = ROOT / "tests/fixtures/pcb"
SCHEMAS = ROOT / "contracts/schemas"

if "validate" in sys.modules:
    V = sys.modules["validate"]
else:
    _spec = importlib.util.spec_from_file_location("validate", ROOT / "contracts/validate.py")
    V = importlib.util.module_from_spec(_spec)
    sys.modules["validate"] = V
    _spec.loader.exec_module(V)

LAYERS = [
    ("copper_top", "F.Cu", ".GTL"), ("copper_bottom", "B.Cu", ".GBL"), ("mask_top", "F.Mask", ".GTS"),
    ("mask_bottom", "B.Mask", ".GBS"), ("silk_top", "F.Silkscreen", ".GTO"), ("outline", "Edge.Cuts", ".GKO"),
]
PASTE = ("paste_top", "F.Paste", ".GTP")
PCB = b'(kicad_pcb (fixture "layout"))\n'
SCH = b'(kicad_sch (fixture "schematic"))\n'
RETRIEVED = b"<html>supplier page bytes</html>\n"


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write(path: Path, content) -> bytes:
    """Write bytes, text or a JSON-compatible value. Return the bytes."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if isinstance(content, (dict, list)):
        content = json.dumps(content, indent=2) + "\n"
    data = content.encode("utf-8") if isinstance(content, str) else content
    path.write_bytes(data)
    return data


def rect(width, height):
    return [{"x": 0, "y": 0}, {"x": width, "y": 0}, {"x": width, "y": height}, {"x": 0, "y": height}]


def build_project(root: Path, kind: str = "pcba", *, holes=None, extra_layers=(), outline=None,
                  circuit_source: str = "kicad_native") -> Path:
    """Write a valid project into `root`. Return `root`."""
    fixture = lambda name: copy.deepcopy(V.load_record(FIX / name))  # noqa: E731
    profile = fixture("supplier-profile.yaml")
    profile["evidence_sha256"] = sha(RETRIEVED)
    profile["content_sha256"] = V.canonical_hash(profile)
    board = fixture("board.yaml")
    board["assembly"] = kind
    board["circuit_source"] = circuit_source
    board["supplier"] = {"id": profile["id"], "service": profile["service"], "profile_sha256": profile["content_sha256"]}
    layers = list(LAYERS) + ([PASTE] if kind == "pcba" else []) + list(extra_layers)
    export = {
        "schema_id": "cad-skills/export-settings", "schema_version": "1.0", "format": "rs274x", "units": "mm", "x2": False,
        "gerber": {"decimal_places": 6},
        "layers": [{"role": r, "kicad_layer": n, "suffix": s} for r, n, s in layers],
        "drill": {"format": "excellon", "zero_suppression": "leading", "decimal_places": 3,
                  "plated_suffix": "-PTH.drl", "nonplated_suffix": "-NPTH.drl", "separate_files": True},
        "origin": "absolute",
    }
    toolchain = {
        "schema_id": "cad-skills/toolchain-lock", "schema_version": "1.0", "python": "3.13.15", "execution": "native",
        "tools": {"kicad": {"used": True, "version": "10.0.4", "source_url": "https://example.com/kicad", "license": "GPL-3.0-or-later"}},
        "libraries": [], "models": [],
    }
    interface = {
        "schema_id": "cad-skills/board-interface", "schema_version": "1.0", "board_revision": "A", "board_sha256": sha(PCB),
        "units": "mm", "origin_mm": {"x": 0, "y": 0}, "thickness_mm": 1.6, "geometry_tolerance_mm": 0.01,
        "outline": outline or rect(40, 25), "cutouts": [],
        "holes": holes if holes is not None else [
            {"id": "H1", "x": 3, "y": 3, "diameter_mm": 3.2, "plated": False},
            {"id": "H2", "x": 37, "y": 22, "diameter_mm": 1.0, "plated": True}],
        "connector_frames": [], "height_limits": {"top_mm": 10, "bottom_mm": 2}, "enclosure_clearance_mm": 0.5,
        "dimension_owners": {k: "mechanical" for k in ("outline", "holes", "connector_frames", "thickness", "height_limits")},
    }
    waivers = {"schema_id": "cad-skills/waivers", "schema_version": "1.0", "waivers": [
        {"id": "W1", "kind": "erc", "rule": "pin_not_driven", "objects": ["U1"], "reason": "Reviewed.", "reviewer": "R. Reviewer",
         "revision": "A", "board_sha256": sha(PCB), "schematic_sha256": sha(SCH)},
        {"id": "W2", "kind": "drc", "rule": "silk_overlap", "objects": ["R1"], "reason": "Reviewed.", "reviewer": "R. Reviewer",
         "revision": "A", "board_sha256": sha(PCB), "schematic_sha256": None}]}
    write(root / "board.yaml", board)
    write(root / "kicad/board.kicad_pcb", PCB)
    write(root / "kicad/board.kicad_sch", SCH)
    write(root / "variants.yaml", fixture("variants.yaml"))
    write(root / "manufacturing/supplier.yaml", profile)
    write(root / "manufacturing/export.yaml", export)
    write(root / "toolchain.lock.json", toolchain)
    write(root / "mechanical/board-interface.json", interface)
    write(root / "manufacturing/waivers.yaml", waivers)
    write(root / "components/part.yaml", fixture("part.yaml"))
    if circuit_source == "skidl":
        write(root / "src/circuit.py", "# SKiDL source of the trial circuit\n")
    return root


def edit_json(path: Path, change) -> None:
    """Load a JSON or YAML record, apply `change(record)`, and write it as JSON text."""
    record = V.load_record(path)
    change(record)
    write(path, record)


def build_package(project: Path, pkg: Path, *, status: str = "qualified") -> dict:
    """Write a valid package for `project` into `pkg`. Return the manifest dict."""
    board = V.load_record(project / "board.yaml")
    export = V.load_record(project / "manufacturing/export.yaml")
    kind = board["assembly"]
    inputs = []
    for role, rel in V.FIXED_INPUT_PATHS.items():
        if (project / rel).is_file():
            inputs.append({"role": role, "path": rel, "sha256": sha((project / rel).read_bytes())})
    inputs.append({"role": "parts", "path": "components/part.yaml", "sha256": sha((project / "components/part.yaml").read_bytes())})
    if (project / "src/circuit.py").is_file():
        inputs.append({"role": "circuit_source", "path": "src/circuit.py", "sha256": sha((project / "src/circuit.py").read_bytes())})
    # The effective staged supplier files that fab.supplier_rules names as inputs.
    staged = {"supplier_rules": ("out/fab/supplier/board.kicad_dru", b"(version 1)\n"),
              "supplier_settings": ("out/fab/supplier/board.kicad_pro", b"{}\n")}
    for role, (rel, data) in staged.items():
        write(project / rel, data)
        inputs.append({"role": role, "path": rel, "sha256": sha(data)})
    outputs = []

    def out(rel, data, role, layer=None):
        data = write(pkg / rel, data)
        item = {"role": role, "path": rel, "sha256": sha(data), "size_bytes": len(data)}
        if layer:
            item["layer"] = layer
        outputs.append(item)
        return item

    for entry in export["layers"]:
        family = V.family_of(entry["role"])
        out(f"gerber/board{entry['suffix']}", f"{entry['role']}:{entry['kicad_layer']}\n", family, entry["kicad_layer"])
    out("gerber/board-PTH.drl", "plated drill\n", "drill_plated")
    out("gerber/board-NPTH.drl", "nonplated drill\n", "drill_nonplated")
    out("docs/schematic.pdf", "schematic pdf\n", "schematic_pdf")
    out("docs/fabrication.pdf", "fabrication drawing\n", "fabrication_drawing")
    if kind == "pcba":
        out("assembly/bom.csv", "bom\n", "bom")
        out("assembly/placement.csv", "placement\n", "placement")
        out("docs/assembly.pdf", "assembly drawing\n", "assembly_drawing")
        out("docs/test.txt", "test record\n", "test_record")
    by_role = {}
    for item in inputs:
        by_role.setdefault(item["role"], []).append(item)
    checks = []
    for check_id in V.REQUIRED_CHECKS[kind]:
        if check_id == "fab.profile_evidence":
            artifact = out("evidence/supplier-page.html", RETRIEVED, "report")
        else:
            artifact = out(f"reports/{check_id}.txt", f"report of {check_id}\n", "report")
        listed = [{"path": m["path"], "sha256": m["sha256"]} for role in V.CHECK_INPUT_ROLES[check_id] for m in by_role[role]]
        evidence = {"schema_id": "cad-skills/evidence", "schema_version": "1.0", "check_id": check_id, "status": "pass",
                    "inputs": listed, "artifact": {"path": artifact["path"], "sha256": artifact["sha256"]}}
        if check_id == "asm.stock_dated":
            evidence.update(method="manual", reviewer="R. Reviewer", observed_on="2026-11-13")
        else:
            evidence.update(method="tool", tool={"name": "kicad-cli", "version": "10.0.4"})
        item = out(f"evidence/{check_id}.json", evidence, "evidence")
        checks.append({"id": check_id, "status": "pass", "evidence_path": item["path"], "evidence_sha256": item["sha256"]})
    manifest = {
        "schema_id": "cad-skills/manifest", "schema_version": "1.0", "release_id": "trial-1", "kind": kind,
        "board_revision": board["release_revision"], "board_sha256": sha(PCB), "variant": board["variant"],
        "supplier": copy.deepcopy(board["supplier"]), "inputs": inputs, "outputs": outputs,
        "drill_applicability": [], "checks": checks, "status": status, "reasons": [],
        "tool_versions": {"kicad": "10.0.4"},
    }
    if kind == "pcba":
        manifest["applicability"] = {"smd_parts": True, "firmware": False, "stencil": False, "panel": False}
    write_manifest(pkg, manifest)
    return manifest


def write_manifest(pkg: Path, manifest: dict) -> None:
    write(pkg / "manifest.json", manifest)


def examine(project: Path, pkg: Path | None = None):
    """Run the project (and package) checks in this process. Return (exit code, report)."""
    return V.build_report([], SCHEMAS, project, pkg)


def finding_codes(report) -> list[str]:
    return sorted(f["code"] for f in report["findings"])
