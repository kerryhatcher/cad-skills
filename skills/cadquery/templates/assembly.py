# /// script
# requires-python = ">=3.10"
# dependencies = ["cadquery>=2.5"]
# ///
"""Parametric box-with-lid assembly -- template for multi-part CadQuery models.

Units: millimetres. Each part is built by a function at its own origin; the
assembly places parts with constraints (or explicit Locations) so that
changing a parameter re-positions everything automatically.

Run / export:   uv run assembly.py           (writes assembly.step + assembly.glb)
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
lip_h = 4.0  # lid lip that drops inside the box
clearance = 0.3  # per side, lid lip to box wall
fillet_r = 3.0
explode = 0.0  # >0 lifts the lid for an exploded view

assert fillet_r < min(inner_l, inner_w) / 2, "fillet radius too large"
assert clearance > 0, "a zero-clearance fit makes the parts overlap"

outer_l = inner_l + 2 * wall
outer_w = inner_w + 2 * wall
outer_h = inner_h + wall  # shell() makes the floor `wall` thick


# --------------------------------------------------------------------- parts
def make_box() -> cq.Workplane:
    box = (
        cq.Workplane("XY")
        .box(outer_l, outer_w, outer_h, centered=(True, True, False))
        .edges("|Z")
        .fillet(fillet_r)
        .faces(">Z")
        .shell(-wall)  # open the top face, walls grow inward
    )
    # Tag the rim so the assembly can mate to it by name.
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
    # Tag the flat underside BEFORE adding the lip: tags live in the shared
    # chain context, so the assembly can still mate to this exact plane.
    plate.faces("<Z").tag("underside")
    lid = (
        plate.faces("<Z")
        .workplane()
        # Two nested closed wires extrude as a ring (outer minus inner).
        # Do NOT use shell() here -- it would hollow the whole lid.
        .rect(lip_l, lip_w)
        .rect(lip_l - 2 * wall, lip_w - 2 * wall)
        .extrude(lip_h)  # along the face normal (-Z): lip hangs below
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

# Plane = Point (centres coincide) + Axis (normals opposite -> faces touch).
# WARNING: for "Plane" the optional param is the Axis ANGLE in degrees, not an
# offset. Leave it at the default (180 = mating faces) for a normal mate.
assy.constrain("box?rim", "lid?underside", "Plane")
# Plane leaves rotation about the shared normal free -- lock it with an Axis
# constraint between two side faces (param=0 -> normals point the same way).
assy.constrain("box@faces@>X", "lid@faces@>X", "Axis", param=0)
assy.constrain("box", "Fixed")  # ground one part so the solver has a reference
assy.solve()

# Exploded view: pre-multiplying applies the shift in WORLD coordinates
# (post-multiplying would move along the lid's own, possibly rotated, axes).
if explode:
    assy.objects["lid"].loc = cq.Location((0, 0, explode)) * assy.objects["lid"].loc

if "show_object" in globals():
    show_object(assy, name="enclosure")  # noqa: F821

if __name__ == "__main__":
    out = Path(__file__).with_suffix("")
    assy.export(f"{out}.step")  # names + colours preserved
    assy.export(f"{out}.glb")  # web viewer / quick look
    print(f"wrote {out}.step and {out}.glb")
