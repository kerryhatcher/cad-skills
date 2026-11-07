# Recipes (verified)

Complete, runnable examples of common modelling tasks. Every block is executed by `tests/test_snippets.py`, so it works on the pinned CadQuery version. Copy one, rename parameters, and adapt. Units: mm.

## Contents
1. [Electronics enclosure with screw bosses and lid](#1-electronics-enclosure-with-screw-bosses-and-lid)
2. [Revolved part: knob with knurl and D-shaft bore](#2-revolved-part-knob-with-knurl-and-d-shaft-bore)
3. [Swept handle and pipe bend](#3-swept-handle-and-pipe-bend)
4. [Helix: spring and external thread](#4-helix-spring-and-external-thread)
5. [Lofted duct transition (rect → round), hollow](#5-lofted-duct-transition-rect--round-hollow)
6. [Involute spur gear](#6-involute-spur-gear)
7. [L-bracket with gusset and slots](#7-l-bracket-with-gusset-and-slots)
8. [Honeycomb vent pattern](#8-honeycomb-vent-pattern)
9. [Laser-cut finger-joint panel (2D → DXF)](#9-laser-cut-finger-joint-panel-2d--dxf)
10. [Embossed label and engraved text](#10-embossed-label-and-engraved-text)
11. [Pillow block bearing housing](#11-pillow-block-bearing-housing)
12. [Hinge pair as an assembly](#12-hinge-pair-as-an-assembly)

---

## 1. Electronics enclosure with screw bosses and lid

```python
import cadquery as cq

# parameters
L, W, H = 100.0, 60.0, 35.0      # outer size of the base
wall = 2.0
corner_r = 4.0
boss_d, boss_hole = 7.0, 2.5     # M3 self-tapping pilot
screw_clear, head_d = 3.4, 6.5
lid_t = 2.5
boss_inset = wall + boss_d / 2   # boss centre distance from outer edge

base = (
    cq.Workplane("XY")
    .box(L, W, H, centered=(True, True, False))
    .edges("|Z").fillet(corner_r)
    .faces(">Z").shell(-wall)                       # open top, walls inward
)

# bosses: start on the inside of the floor, grow up to 1 mm below the rim
boss_pts = [(sx * (L / 2 - boss_inset), sy * (W / 2 - boss_inset))
            for sx in (-1, 1) for sy in (-1, 1)]
base = (
    base.faces("<Z").workplane(invert=True, offset=-wall)   # plane on top of the floor, normal +Z
    .pushPoints(boss_pts)
    .circle(boss_d / 2)
    .extrude(H - wall - 1.0)
    .faces(">Z[-2]").workplane()                             # boss tops (below the rim)
    .pushPoints(boss_pts)
    .hole(boss_hole, depth=H - wall - 2)
)

lid = (
    cq.Workplane("XY")
    .box(L, W, lid_t, centered=(True, True, False))
    .edges("|Z").fillet(corner_r)
    .faces(">Z").workplane()
    .pushPoints(boss_pts)
    .cskHole(screw_clear, head_d, 90)
)

result = (
    cq.Assembly(name="enclosure")
    .add(base, name="base", color=cq.Color("steelblue"))
    .add(lid, name="lid", loc=cq.Location((0, 0, H)), color=cq.Color("lightgray"))
)
assert base.val().isValid() and len(base.solids().vals()) == 1
```

Notes: `faces("<Z").workplane(invert=True, offset=-wall)` puts a +Z-facing plane on the inner floor. `">Z[-2]"` selects the second-highest set of Z-normal faces — here the boss tops, because the rim is the highest.

## 2. Revolved part: knob with knurl and D-shaft bore

```python
import cadquery as cq

D, H = 30.0, 18.0          # knob diameter / height
skirt_h = 4.0
shaft_d, flat = 6.0, 1.0   # D-shaft and depth of its flat
ribs, rib_d = 24, 1.6

# half profile in XZ (x = radius, local y = global Z after "XZ"... see note)
profile = (
    cq.Workplane("XZ")
    .polyline([(0, 0), (D / 2, 0), (D / 2, skirt_h), (D / 2 - 2, H), (0, H)])
    .close()
    .revolve(360, (0, 0, 0), (0, 1, 0))            # axis = local Y of XZ = global Z
)
knob = profile.faces(">Z").edges().fillet(2)

# knurl: cut small cylinders around the skirt
knurl = (
    cq.Workplane("XY")
    .polarArray(D / 2, 0, 360, ribs)
    .circle(rib_d / 2)
    .extrude(skirt_h + 3)
)
knob = knob.cut(knurl)

# D-shaped blind bore from the bottom
d_profile = (
    cq.Sketch()
    .circle(shaft_d / 2)
    .push([(shaft_d / 2, 0)]).rect(2 * flat, shaft_d, mode="s")
)
result = knob.faces("<Z").workplane().placeSketch(d_profile).cutBlind(-12)
assert result.val().isValid()
```

On the `"XZ"` workplane, local x = global X and local y = global **Z** (its normal is −Y), so profiles drawn there revolve nicely about local Y.

## 3. Swept handle and pipe bend

```python
import cadquery as cq

# Handle: rounded-rectangle section swept along a U path with round transitions
span, rise, r_section = 100.0, 35.0, 6.0
path = cq.Workplane("XZ").polyline([(-span / 2, 0), (-span / 2, rise), (span / 2, rise), (span / 2, 0)])
section = cq.Sketch().rect(2 * r_section, 3 * r_section).vertices().fillet(3)  # round the section in 2D
handle = (
    cq.Workplane("XY", origin=(-span / 2, 0, 0))   # section plane at the path start, normal along the path
    .placeSketch(section)
    .sweep(path, transition="round")
)

# Pipe bend: annulus swept along a tangent arc
R, od, wall = 40.0, 20.0, 2.0
bend = cq.Workplane("XZ").moveTo(0, 0).radiusArc((R, R), R)   # 90 deg arc
pipe = cq.Workplane("XY").circle(od / 2).circle(od / 2 - wall).sweep(bend)

result = pipe
assert handle.val().isValid() and pipe.val().isValid()
```

The profile must sit at the start of the path and be roughly perpendicular to it. Round the *section* in 2D (Sketch fillet) instead of filleting the swept solid's edges afterwards — 3D fillets on sweeps usually fail with `StdFail_NotDone`. For multiple sections use `sweep(path, multisection=True)` with several pending wires.

## 4. Helix: spring and external thread

```python
import cadquery as cq

# Compression spring: circle swept along a helix (isFrenet keeps the section upright)
pitch, height, coil_r, wire_d = 5.0, 30.0, 10.0, 1.5
helix = cq.Wire.makeHelix(pitch=pitch, height=height, radius=coil_r)
spring = (
    cq.Workplane("XZ")
    .center(coil_r, 0)
    .circle(wire_d / 2)
    .sweep(cq.Workplane().add(helix), isFrenet=True)
)

# Simplified (cosmetic-accurate) metric thread on a rod: triangular profile swept on a helix
major_d, thread_pitch, length = 10.0, 1.5, 20.0
depth = 0.6134 * thread_pitch            # ISO external thread depth
minor_r = major_d / 2 - depth
core = cq.Workplane("XY").circle(minor_r + 0.01).extrude(length)   # tiny overlap -> robust fuse
thread_helix = cq.Wire.makeHelix(pitch=thread_pitch, height=length - thread_pitch, radius=minor_r)
tooth = (
    cq.Workplane("XZ")
    .polyline([(minor_r, -0.45 * thread_pitch), (major_d / 2, -0.05 * thread_pitch),
               (major_d / 2, 0.05 * thread_pitch), (minor_r, 0.45 * thread_pitch)])
    .close()
    .sweep(cq.Workplane().add(thread_helix), isFrenet=True)
)
rod = core.union(tooth)
result = rod
assert spring.val().isValid() and rod.val().isValid()
```

True threads are slow and fragile (helical booleans). For printed parts use cosmetic threads only when needed; otherwise model the minor-diameter hole and tap it, or use heat-set inserts. Keep the thread profile slightly overlapping the core (here `+0.01`) — coincident surfaces make the union fail.

## 5. Lofted duct transition (rect → round), hollow

```python
import cadquery as cq

a, b, d, length, wall = 60.0, 30.0, 40.0, 50.0, 2.0

def transition(w, h, dia):
    return cq.Workplane("XY").rect(w, h).workplane(offset=length).circle(dia / 2).loft(ruled=False)

outer = transition(a, b, d)
inner = transition(a - 2 * wall, b - 2 * wall, d - 2 * wall)
duct = outer.cut(inner)            # open at both ends, constant wall at the end sections
result = duct
assert result.val().isValid() and len(result.solids().vals()) == 1
```

`outer.faces(">Z or <Z").shell(-wall)` is the obvious approach but fails (`StdFail_NotDone`) on most lofts — subtract an inner loft instead. Loft works best when sections have similar edge counts; for filleted rectangles use `cq.Sketch` sections with `placeSketch(s1, s2.moved(z=...))`.

## 6. Involute spur gear

```python
import math
import cadquery as cq

module, teeth, width, bore = 2.0, 20, 8.0, 8.0
pressure = math.radians(20)

rp = module * teeth / 2            # pitch radius
rb = rp * math.cos(pressure)       # base radius
ra = rp + module                   # addendum (tip) radius
rf = rp - 1.25 * module            # dedendum (root) radius

def involute(r_base, r):
    """Polar angle of the involute point at radius r."""
    alpha = math.acos(r_base / r)
    return math.tan(alpha) - alpha

# half tooth thickness angle at the pitch circle
half = math.pi / (2 * teeth) + involute(rb, rp)
radii = [max(rb, rf) + i * (ra - max(rb, rf)) / 10 for i in range(11)]
right = [(r * math.cos(-half + involute(rb, r)), r * math.sin(-half + involute(rb, r))) for r in radii]
left = [(x, -y) for x, y in reversed(right)]
tooth_pts = [(rf * math.cos(-half), rf * math.sin(-half))] + right + left + [(rf * math.cos(half), rf * math.sin(half))]

tooth = cq.Workplane("XY").polyline(tooth_pts).close().extrude(width)
root = cq.Workplane("XY").circle(rf + 0.01).extrude(width)
gear = root
teeth_solids = [tooth.val().rotate((0, 0, 0), (0, 0, 1), i * 360 / teeth) for i in range(teeth)]
gear = gear.union(cq.Workplane().add(cq.Compound.makeCompound(teeth_solids)))   # one boolean, not N
gear = gear.faces(">Z").workplane().hole(bore)
result = gear
assert abs(result.val().BoundingBox().xlen - 2 * ra) < 0.2
```

Rotating copies and fusing once as a compound is far faster than unioning inside the loop.

## 7. L-bracket with gusset and slots

```python
import cadquery as cq

w, leg_a, leg_b, t = 40.0, 50.0, 40.0, 4.0
slot_l, slot_w = 12.0, 5.5
gusset = 18.0
bend_r = 3.0

# L profile in the XZ plane, extruded along Y (width)
bracket = (
    cq.Workplane("XZ")
    .polyline([(0, 0), (leg_a, 0), (leg_a, t), (t, t), (t, leg_b), (0, leg_b)])
    .close()
    .extrude(w / 2, both=True)                 # symmetric: y from -w/2 to w/2
)
# inside bend fillet: the edge parallel to Y at (t, t)
bracket = bracket.edges(cq.selectors.NearestToPointSelector((t, 0, t))).fillet(bend_r)

# triangular gusset in the middle
gus = (
    cq.Workplane("XZ")
    .polyline([(t, t), (t + gusset, t), (t, t + gusset)])
    .close()
    .extrude(t / 2, both=True)
)
bracket = bracket.union(gus)

# slots in both legs
bracket = (
    bracket.faces("<Z").workplane(centerOption="CenterOfBoundBox")
    .center(8, 0)
    .slot2D(slot_l, slot_w, 0)
    .cutThruAll()
    .faces("<X").workplane(centerOption="CenterOfBoundBox")
    .center(0, 8)
    .slot2D(slot_l, slot_w, 90)
    .cutThruAll()
)
result = bracket
assert len(result.solids().vals()) == 1
```

`NearestToPointSelector` is the most reliable way to grab one specific internal edge. Watch the slot placement on side faces: local axes of `faces("<X").workplane()` are not global X/Y — render and check.

## 8. Honeycomb vent pattern

```python
import math
import cadquery as cq

panel_l, panel_w, t = 120.0, 80.0, 3.0
cell, web, margin = 8.0, 1.6, 8.0          # hex across-flats, wall between hexes, border

pitch_x = cell + web
pitch_y = pitch_x * math.sqrt(3) / 2
pts = []
ny = int((panel_w - 2 * margin) // pitch_y)
nx = int((panel_l - 2 * margin) // pitch_x)
for j in range(ny):
    for i in range(nx):
        x = -((nx - 1) * pitch_x) / 2 + i * pitch_x + (pitch_x / 2 if j % 2 else 0)
        y = -((ny - 1) * pitch_y) / 2 + j * pitch_y
        if abs(x) + cell / 2 < panel_l / 2 - margin:
            pts.append((x, y))

across_corners = cell / math.cos(math.radians(30))
result = (
    cq.Workplane("XY").box(panel_l, panel_w, t)
    .faces(">Z").workplane()
    .pushPoints(pts)
    .polygon(6, across_corners)        # polygon() takes the circumscribed diameter
    .cutThruAll()
)
assert result.val().isValid()
```

One `cutThruAll()` with many pending wires is a single boolean — fast. Avoid `for p in pts: wp = wp.cut(...)`.

## 9. Laser-cut finger-joint panel (2D → DXF)

```python
import cadquery as cq

length, height, t = 120.0, 60.0, 3.0      # panel size, material thickness
fingers = 7                                # odd -> symmetric

def finger_edge_cuts(edge_len, n, depth):
    """Rectangles (centre x, width) to remove along an edge, every other finger."""
    f = edge_len / n
    return [(-edge_len / 2 + f * (i + 0.5), f) for i in range(n) if i % 2 == 1]

sk = cq.Sketch().rect(length, height)
for x, f in finger_edge_cuts(length, fingers, t):
    sk = sk.push([(x, height / 2 - t / 2)]).rect(f, t, mode="s").reset()
    sk = sk.push([(x, -height / 2 + t / 2)]).rect(f, t, mode="s").reset()
sk = sk.clean()

panel = cq.Workplane("XY").placeSketch(sk).extrude(t)
cq.exporters.export(panel.faces("<Z"), "panel.dxf")   # bottom face at z=0 -> 2D outline
result = panel
assert result.val().isValid()
```

Add kerf compensation by offsetting the sketch outward by half the kerf: `sk.copy().wires().offset(kerf / 2)`.

## 10. Embossed label and engraved text

```python
import cadquery as cq

plate = cq.Workplane("XY").box(60, 20, 3).edges("|Z").fillet(3)
embossed = plate.faces(">Z").workplane().text("CADQUERY", 7, 0.8, combine="a")   # raised
engraved = plate.faces(">Z").workplane().text("v1.0", 5, -0.5)                  # default combine="cut"
result = embossed
assert embossed.val().Volume() > plate.val().Volume() > engraved.val().Volume()
```

`text()` defaults to `combine="cut"`: positive distance with the default does nothing visible. Font: `font="Arial"` or `fontPath="/path/to/font.ttf"`; `kind="bold"`; `halign`/`valign`.

## 11. Pillow block bearing housing

```python
import cadquery as cq

length, height, width, t = 80.0, 60.0, 100.0, 10.0
bearing_d, pad = 22.0, 12.0     # bearing OD, edge pad around bolt holes
cbore_hole, cbore_d, cbore_depth = 2.4, 4.4, 2.1

result = (
    cq.Workplane("XY")
    .box(length, height, t)
    .faces(">Z").workplane()
    .hole(bearing_d)
    .faces(">Z").workplane()
    .rect(length - pad, height - pad, forConstruction=True)
    .vertices()
    .cboreHole(cbore_hole, cbore_d, cbore_depth)
    .edges("|Z")
    .fillet(2.0)
)
assert result.val().isValid()
```

The classic pattern: construction rectangle → `vertices()` → hole op at each corner.

## 12. Hinge pair as an assembly

```python
import cadquery as cq

leaf_w, leaf_h, t = 30.0, 40.0, 2.0
knuckle_d, pin_d, gap = 6.0, 2.0, 0.3
n_knuckles = 5
seg = leaf_h / n_knuckles

def leaf(odd: bool) -> cq.Workplane:
    plate = cq.Workplane("XY").box(leaf_w, leaf_h, t, centered=(False, True, False))
    knuckles = [
        cq.Workplane("XZ", origin=(0, -leaf_h / 2 + seg * i + gap / 2, knuckle_d / 2))
        .circle(knuckle_d / 2)
        .extrude(-(seg - gap))                     # XZ normal is -Y: negative extrudes toward +Y
        for i in range(n_knuckles) if (i % 2 == 1) == odd
    ]
    body = plate
    for k in knuckles:              # few bodies; for many, fuse a compound once
        body = body.union(k)
    # pin bore along Y through all knuckles: explicit cutter, overshooting both ends
    bore = (
        cq.Workplane("XZ", origin=(0, leaf_h / 2 + 1, knuckle_d / 2))
        .circle(pin_d / 2 + gap)
        .extrude(leaf_h + 2)        # XZ normal is -Y, so +extrude runs toward -Y
    )
    return body.cut(bore)

a = leaf(False)
b = leaf(True).rotate((0, 0, 0), (0, 0, 1), 180)  # mirror image across the hinge axis
pin = cq.Workplane("XZ", origin=(0, leaf_h / 2, knuckle_d / 2)).circle(pin_d / 2).extrude(leaf_h)

result = (
    cq.Assembly(name="hinge")
    .add(a, name="leaf_a", color=cq.Color("gray80"))
    .add(b, name="leaf_b", color=cq.Color("gray"))
    .add(pin, name="pin", color=cq.Color("goldenrod"))
)
```

`faces("<X").workplane()` would fail here (the knuckles add curved faces at the minimum X) — an explicit cutter solid is more robust. Check moving-part clearances with `inspect_model.py hinge.py --interference`; for print-in-place hinges keep `gap` ≥ 0.3 mm.
