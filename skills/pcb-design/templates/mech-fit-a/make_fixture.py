#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Generate the B11 fixture `mech-fit-a` from `fixture-source.json`. Standard library only.

  uv run make_fixture.py --out DIR

It writes, in DIR:
  board.kicad_pcb              the KiCad board (drill/place origin = anchor, holes, outline)
  board.yaml                   the board record (mechanical block, coordinate system)
  mechanical/board-interface.json  the interface, with extensions.transform
  mechanical/fixture-source.json   the source record (copied)
  mechanical/component-evidence.json  the evidence record (copied)
  export-settings.json         the exact export switch set (settings record)

The interface values are derived from the source record by the transform of section 3.
The output is deterministic. Object identifiers come from uuid5, not from random values.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
NS = uuid.UUID("b11b11b1-1b11-4b11-8b11-b11b11b11b11")
SCRIPTS = HERE.parent.parent / "scripts"
sys.path.insert(0, str(SCRIPTS))

import mechanical as M  # noqa: E402  (same skill, accepted contract rules)


def oid(name: str) -> str:
    return str(uuid.uuid5(NS, name))


def fmt(v: float) -> str:
    return f"{v:.6f}".rstrip("0").rstrip(".") if v != 0 else "0"


def write_kicad(src: dict, path: Path) -> None:
    """Write the KiCad board. Outline, holes, drill/place origin = anchor, 1.6 mm thickness."""
    ax, ay = src["aux_axis_origin_kicad_mm"]["x"], src["aux_axis_origin_kicad_mm"]["y"]
    pts = src["outline_kicad_mm"]
    closed = pts + [pts[0]]
    lines = []
    for (x1, y1), (x2, y2) in zip(closed, closed[1:]):
        lines.append(f'  (gr_line (start {fmt(x1)} {fmt(y1)}) (end {fmt(x2)} {fmt(y2)})'
                     f' (stroke (width 0.05) (type default)) (layer "Edge.Cuts") (uuid "{oid("edge" + str((x1, y1, x2, y2)))}"))')
    holes = []
    for h in src["holes"]:
        d = h["diameter_mm"]
        if h["plated"]:
            pad = f'(pad "1" thru_hole circle (at 0 0) (size {fmt(d + 1)} {fmt(d + 1)}) (drill {fmt(d)}) (layers "*.Cu" "*.Mask"))'
        else:
            pad = f'(pad "" np_thru_hole circle (at 0 0) (size {fmt(d)} {fmt(d)}) (drill {fmt(d)}) (layers "*.Cu" "*.Mask"))'
        holes.append(f'  (footprint "B11:HOLE" (layer "F.Cu") (uuid "{oid(h["id"])}") (at {fmt(h["x"])} {fmt(h["y"])})\n'
                     f'    (property "Reference" "{h["id"]}" (at 0 0) (layer "F.SilkS") (hide yes))\n    {pad})')
    text = f'''(kicad_pcb
  (version 20260206)
  (generator "pcbnew")
  (generator_version "10.0")
  (general (thickness {fmt(src["stackup"]["thickness_mm"])}))
  (paper "A4")
  (layers
    (0 "F.Cu" signal)
    (2 "B.Cu" signal)
    (1 "F.Mask" user)
    (3 "B.Mask" user)
    (5 "F.SilkS" user "F.Silkscreen")
    (7 "B.SilkS" user "B.Silkscreen")
    (25 "Edge.Cuts" user)
  )
  (setup (aux_axis_origin {fmt(ax)} {fmt(ay)}))
  (net 0 "")
{chr(10).join(lines)}
{chr(10).join(holes)}
)
'''
    path.write_text(text, encoding="utf-8")


def interface_from(src: dict, board_sha256: str) -> dict:
    """Build the interface. Values follow the section 3 transform and the six connector fields."""
    anchor = src["aux_axis_origin_kicad_mm"]
    origin = src["target_origin_mm"]
    transform = {"source_frame": "kicad-board",
                 "source_origin_mm": {"x": anchor["x"], "y": anchor["y"]},
                 "source_axes": {"x": "right", "y": "down"},
                 "target_axes": {"x": "right", "y": "up"}, "scale": 1}
    tp = {"origin": (origin["x"], origin["y"]), "anchor": (anchor["x"], anchor["y"])}
    outline = []
    for x, y in src["outline_kicad_mm"]:
        tx, ty = M.to_target((x, y), tp)
        outline.append({"x": round(tx, 6), "y": round(ty, 6)})
    holes = []
    for h in src["holes"]:
        tx, ty = M.to_target((h["x"], h["y"]), tp)
        holes.append({"id": h["id"], "x": round(tx, 6), "y": round(ty, 6),
                      "diameter_mm": h["diameter_mm"], "plated": h["plated"]})
    frames = []
    for c in src["connector_frames"]:
        tx, ty = M.to_target((c["x"], c["y"]), tp)
        vec = M.target_vector((1.0, 0.0), c["rotation_deg"])
        frames.append({"id": c["id"], "side": c["side"], "x": round(tx, 6), "y": round(ty, 6),
                       "rotation_deg": round(M.target_angle_deg(vec), 6),
                       "insertion_depth_mm": c["insertion_depth_mm"]})
    st = src["stackup"]
    return {
        "schema_id": "cad-skills/board-interface", "schema_version": "1.0",
        "board_revision": src["board_revision"], "board_sha256": board_sha256,
        "units": "mm", "origin_mm": origin, "thickness_mm": st["thickness_mm"],
        "geometry_tolerance_mm": src["geometry_tolerance_mm"], "outline": outline, "cutouts": [],
        "holes": holes, "connector_frames": frames, "height_limits": src["height_limits_mm"],
        "enclosure_clearance_mm": src["enclosure"]["clearance_mm"],
        "dimension_owners": src["dimension_owners"],
        "extensions": {"transform": transform, "angle_tolerance_deg": src["angle_tolerance_deg"]},
    }


def board_yaml(src: dict) -> str:
    st = src["stackup"]
    return f"""schema_id: cad-skills/board
schema_version: '1.0'
name: mech-fit-a
circuit_source: kicad_native
assembly: bare_board
supplier:
  id: example-two-layer
  service: Example two-layer service
  profile_sha256: b37b37495cbab698f921e7b229585ea890cefd7298f3615cd15cec02bb00fb77
quantity: 1
variant: base
electrical_limits:
  supply_voltage:
    value: 3.3
    unit: V
  supply_current:
    value: 0.01
    unit: A
mechanical:
  width_mm: 60.0
  height_mm: 36.0
  thickness_mm: {fmt(st['thickness_mm'])}
coordinate_system:
  units: mm
  origin:
    x_mm: 0
    y_mm: 0
  x_axis: right
  y_axis: up
release_revision: {src['board_revision']}
restrictions:
- text: The fixture is a test template for mechanical fit. It has no electrical function.
  source: B11 fixture statement, 2026-11-15
"""


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Generate the B11 mech-fit-a fixture.")
    parser.add_argument("--out", required=True, type=Path)
    args = parser.parse_args(argv)
    src = json.loads((HERE / "fixture-source.json").read_text(encoding="utf-8"))
    out = args.out
    (out / "mechanical").mkdir(parents=True, exist_ok=True)
    board_path = out / "board.kicad_pcb"
    write_kicad(src, board_path)
    board_sha = hashlib.sha256(board_path.read_bytes()).hexdigest()
    iface = interface_from(src, board_sha)
    (out / "mechanical" / "board-interface.json").write_text(
        json.dumps(iface, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    (out / "board.yaml").write_text(board_yaml(src), encoding="utf-8")
    for name in ("fixture-source.json", "component-evidence.json"):
        (out / "mechanical" / name).write_bytes((HERE / name).read_bytes())
    settings = json.loads((HERE / "export-settings.json").read_text(encoding="utf-8"))
    (out / "export-settings.json").write_text(json.dumps(settings, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"board_sha256 {board_sha}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
