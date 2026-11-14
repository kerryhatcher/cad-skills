# /// script
# requires-python = ">=3.10"
# dependencies = ["cadquery>=2.5"]
# ///
"""Parametric assembly of a box and a lid. Template for CadQuery models with many parts.

Units: millimeters. A function makes each part at its own origin. The assembly
puts the parts in position with constraints (or explicit Locations). Thus, when
you change a parameter, all parts move to their new positions automatically.

Run and export: uv run assembly.py           (writes assembly.step and assembly.glb)
Inspect:        uv run <skill>/scripts/inspect_model.py assembly.py --interference --png a.png
"""

from pathlib import Path

import cadquery as cq

# ----------------------------------------------------------------- parameters
inner_l = 80.0
inner_w = 50.0
inner_h = 30.0
wall = 2.5
lid_t = 2.5
lip_h = 4.0  # lip of the lid that goes into the box
clearance = 0.3  # on each side, between the lid lip and the box wall
fillet_r = 3.0
explode = 0.0  # a value more than 0 lifts the lid for an exploded view

assert fillet_r < min(inner_l, inner_w) / 2, "the fillet radius is too large"
assert clearance > 0, "a fit with a clearance of 0 makes the parts overlap"

outer_l = inner_l + 2 * wall
outer_w = inner_w + 2 * wall
outer_h = inner_h + wall  # shell() makes a floor with the thickness `wall`


# --------------------------------------------------------------------- parts
def make_box() -> cq.Workplane:
    box = (
        cq.Workplane("XY")
        .box(outer_l, outer_w, outer_h, centered=(True, True, False))
        .edges("|Z")
        .fillet(fillet_r)
        .faces(">Z")
        .shell(-wall)  # opens the top face, and the walls go inward
    )
    # Put a tag on the rim. Then the assembly can mate to it by name.
    box.faces(">Z").tag("rim")
    return box


def make_lid() -> cq.Workplane:
    lip_l = inner_l - 2 * clearance
    lip_w = inner_w - 2 * clearance
    plate = (
        cq.Workplane("XY")
        .box(outer_l, outer_w, lid_t, centered=(True, True, False))
        .edges("|Z")
        .fillet(fillet_r)
    )
    # Put a tag on the flat bottom face BEFORE you add the lip. The tags are in the
    # shared chain context. Thus the assembly can mate to this exact plane later.
    plate.faces("<Z").tag("underside")
    lid = (
        plate.faces("<Z")
        .workplane()
        # Two nested closed wires extrude as a ring (outer wire minus inner wire).
        # Do NOT use shell() here. It makes the full lid hollow.
        .rect(lip_l, lip_w)
        .rect(lip_l - 2 * wall, lip_w - 2 * wall)
        .extrude(lip_h)  # along the face normal (-Z): the lip is below the lid
    )
    return lid


# ------------------------------------------------------------------ assembly
box = make_box()
lid = make_lid()

assy = (
    cq.Assembly(name="enclosure")
    .add(box, name="box", color=cq.Color(0.2, 0.4, 0.8, 1))
    .add(lid, name="lid", color=cq.Color(0.9, 0.9, 0.9, 0.6))
)

# Plane = Point (the centers are at the same position) + Axis (opposite normals: the faces touch).
# CAUTION: for "Plane", the optional param is the Axis ANGLE in degrees, not an
# offset. For a usual mate, keep the default (180 = mating faces).
assy.constrain("box?rim", "lid?underside", "Plane")
# Plane does not stop the rotation about the shared normal. Stop it with an Axis
# constraint between two side faces (param=0: the normals point in the same direction).
assy.constrain("box@faces@>X", "lid@faces@>X", "Axis", param=0)
assy.constrain("box", "Fixed")  # fix one part, so that the solver has a reference
assy.solve()

# Exploded view: multiply on the left to move in WORLD coordinates.
# (Multiply on the right to move along the axes of the lid, which can be turned.)
if explode:
    assy.objects["lid"].loc = cq.Location((0, 0, explode)) * assy.objects["lid"].loc

if "show_object" in globals():
    show_object(assy, name="enclosure")  # noqa: F821

if __name__ == "__main__":
    out = Path(__file__).with_suffix("")
    assy.export(f"{out}.step")  # keeps the names and colors
    assy.export(f"{out}.glb")  # web viewer, fast view
    print(f"wrote {out}.step and {out}.glb")
