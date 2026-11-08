# /// script
# requires-python = ">=3.10"
# dependencies = ["cadquery>=2.5"]
# ///
"""Parametric mounting plate. Template for a single CadQuery part.

Units: millimeters. Origin: the center of the bottom face. +Z is up.

Run and export: uv run part.py                (writes part.step and part.stl next to this file)
Inspect:        uv run <skill>/scripts/inspect_model.py part.py --png preview.png
Change values:  uv run <skill>/scripts/inspect_model.py part.py --set length=120 --set holes_x=4
"""

from pathlib import Path

import cadquery as cq

# --------------------------------------------------------------------------- #
# Parameters. Use only top-level literal assignments. Then CQGI and
# inspect_model.py can change them with --set NAME=VALUE.
# --------------------------------------------------------------------------- #
length = 100.0  # X dimension
width = 60.0  # Y dimension
thickness = 6.0  # Z dimension
corner_radius = 5.0  # fillet on the vertical edges
hole_dia = 4.5  # M4 clearance
cbore_dia = 8.0
cbore_depth = 3.0
holes_x = 2  # number of holes along X
holes_y = 2  # number of holes along Y
hole_margin = 8.0  # distance from the hole center to the plate edge
pocket_depth = 2.0  # 0 removes the top pocket
pocket_inset = 15.0  # distance from the pocket wall to the plate edge
edge_chamfer = 0.5  # chamfer on the top outer edge

# --------------------------------------------------------------------------- #
# Calculated values and checks. If a value is not possible, stop immediately
# with a clear message. If not, an OCCT error that is difficult to read occurs later.
# --------------------------------------------------------------------------- #
pitch_x = (length - 2 * hole_margin) / max(holes_x - 1, 1)
pitch_y = (width - 2 * hole_margin) / max(holes_y - 1, 1)
pocket_l = length - 2 * pocket_inset
pocket_w = width - 2 * pocket_inset

assert cbore_dia > hole_dia, "the counterbore must be wider than the hole"
assert cbore_depth < thickness, "the counterbore is deeper than the plate"
assert hole_margin > cbore_dia / 2, "the holes go through the plate edge"
assert corner_radius < min(length, width) / 2, "the corner radius is too large"
assert pocket_depth < thickness - cbore_depth or pocket_depth == 0, "the pocket is too deep"
assert pocket_depth == 0 or (pocket_l > 0 and pocket_w > 0), "the pocket inset is too large"

# --------------------------------------------------------------------------- #
# Model
# --------------------------------------------------------------------------- #
plate = (
    cq.Workplane("XY")
    .box(length, width, thickness, centered=(True, True, False))
    .edges("|Z")
    .fillet(corner_radius)
)

# Add edge treatments when the selection is clear. At this step, the top face
# has only its outer outline. Thus the ">Z" edges are the outline.
if edge_chamfer > 0:
    plate = plate.faces(">Z").edges().chamfer(edge_chamfer)

if pocket_depth > 0:
    plate = (
        plate.faces(">Z")
        .workplane()
        .rect(pocket_l, pocket_w)
        .cutBlind(-pocket_depth)  # a negative value cuts into the material
    )

result = (
    plate.faces(">Z")
    # Put the plane on the top surface. After a pocket, the >Z faces change.
    # Thus give the origin explicitly. Do not use the default center.
    .workplane(origin=(0, 0, thickness))
    .rarray(pitch_x, pitch_y, holes_x, holes_y)
    .cboreHole(hole_dia, cbore_dia, cbore_depth)
)

# Give the result to CQ-editor and to CQGI tools (inspect_model.py).
if "show_object" in globals():
    show_object(result, name="plate")  # noqa: F821


# --------------------------------------------------------------------------- #
# Export when you run the file directly (`uv run part.py`). CQGI does not run this part.
# --------------------------------------------------------------------------- #
if __name__ == "__main__":
    out = Path(__file__).with_suffix("")
    solid = result.val()
    assert solid.isValid(), "the generated shape is not valid"
    bb = solid.BoundingBox()
    print(f"bbox {bb.xlen:.2f} x {bb.ylen:.2f} x {bb.zlen:.2f} mm, volume {solid.Volume():.1f} mm^3")
    cq.exporters.export(result, f"{out}.step")
    cq.exporters.export(result, f"{out}.stl", tolerance=0.01, angularTolerance=0.1)
    print(f"wrote {out}.step and {out}.stl")
