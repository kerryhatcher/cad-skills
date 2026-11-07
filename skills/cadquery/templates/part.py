# /// script
# requires-python = ">=3.10"
# dependencies = ["cadquery>=2.5"]
# ///
"""Parametric mounting plate -- template for a single CadQuery part.

Units: millimetres. Origin: centre of the bottom face. +Z is up.

Run / export:   uv run part.py                (writes part.step + part.stl next to this file)
Inspect:        uv run <skill>/scripts/inspect_model.py part.py --png preview.png
Override:       uv run <skill>/scripts/inspect_model.py part.py --set length=120 --set holes_x=4
"""

from pathlib import Path

import cadquery as cq

# --------------------------------------------------------------------------- #
# Parameters -- top-level literal assignments only, so CQGI / inspect_model.py
# can override them with --set NAME=VALUE.
# --------------------------------------------------------------------------- #
length = 100.0  # X extent
width = 60.0  # Y extent
thickness = 6.0  # Z extent
corner_radius = 5.0  # vertical edge fillet
hole_dia = 4.5  # M4 clearance
cbore_dia = 8.0
cbore_depth = 3.0
holes_x = 2  # hole grid count along X
holes_y = 2  # hole grid count along Y
hole_margin = 8.0  # hole centre distance from plate edge
pocket_depth = 2.0  # 0 disables the top pocket
pocket_inset = 15.0  # pocket wall distance from plate edge
edge_chamfer = 0.5  # top outer edge break

# --------------------------------------------------------------------------- #
# Derived values and sanity checks -- fail early with a readable message
# instead of an opaque OCCT error later.
# --------------------------------------------------------------------------- #
pitch_x = (length - 2 * hole_margin) / max(holes_x - 1, 1)
pitch_y = (width - 2 * hole_margin) / max(holes_y - 1, 1)
pocket_l = length - 2 * pocket_inset
pocket_w = width - 2 * pocket_inset

assert cbore_dia > hole_dia, "counterbore must be wider than the hole"
assert cbore_depth < thickness, "counterbore deeper than the plate"
assert hole_margin > cbore_dia / 2, "holes would break out of the plate edge"
assert corner_radius < min(length, width) / 2, "corner radius too large"
assert pocket_depth < thickness - cbore_depth or pocket_depth == 0, "pocket too deep"
assert pocket_depth == 0 or (pocket_l > 0 and pocket_w > 0), "pocket inset too large"

# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #
plate = (
    cq.Workplane("XY")
    .box(length, width, thickness, centered=(True, True, False))
    .edges("|Z")
    .fillet(corner_radius)
)

# Edge treatments are easiest while the selection is unambiguous: right now the
# top face has only its outer outline, so ">Z" edges == the outline.
if edge_chamfer > 0:
    plate = plate.faces(">Z").edges().chamfer(edge_chamfer)

if pocket_depth > 0:
    plate = (
        plate.faces(">Z")
        .workplane()
        .rect(pocket_l, pocket_w)
        .cutBlind(-pocket_depth)  # negative = into the material
    )

result = (
    plate.faces(">Z")
    # Pin the plane to the top surface: after a pocket, the >Z face set changes,
    # so give the origin explicitly instead of trusting the default centre.
    .workplane(origin=(0, 0, thickness))
    .rarray(pitch_x, pitch_y, holes_x, holes_y)
    .cboreHole(hole_dia, cbore_dia, cbore_depth)
)

# Make the result visible to CQ-editor / CQGI runners (inspect_model.py).
if "show_object" in globals():
    show_object(result, name="plate")  # noqa: F821


# --------------------------------------------------------------------------- #
# Export when run directly (`uv run part.py`). Skipped under CQGI.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    out = Path(__file__).with_suffix("")
    solid = result.val()
    assert solid.isValid(), "generated shape is invalid"
    bb = solid.BoundingBox()
    print(f"bbox {bb.xlen:.2f} x {bb.ylen:.2f} x {bb.zlen:.2f} mm, volume {solid.Volume():.1f} mm^3")
    cq.exporters.export(result, f"{out}.step")
    cq.exporters.export(result, f"{out}.stl", tolerance=0.01, angularTolerance=0.1)
    print(f"wrote {out}.step and {out}.stl")
