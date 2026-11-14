# Workplane (fluent API)

`cq.Workplane` is the primary modeling API. Each method gives a **new** Workplane. The chain makes a history (the "stack"). To get the exact signatures for the installed version, run `uv run scripts/cq_api.py Workplane.<method>`.

## Contents
- [Stack model](#stack-model)
- [Make and position workplanes](#make-and-position-workplanes)
- [2D drawing](#2d-drawing)
- [Points and patterns](#points-and-patterns)
- [3D primitives](#3d-primitives)
- [Operations from profile to solid](#operations-from-profile-to-solid)
- [Holes, pockets, features](#holes-pockets-features)
- [Fillet, chamfer, shell](#fillet-chamfer-shell)
- [Booleans and combine modes](#booleans-and-combine-modes)
- [Transformations and mirrors](#transformations-and-mirrors)
- [Stack navigation, tags, exit from the chain](#stack-navigation-tags-exit-from-the-chain)
- [Plugins: how to extend Workplane](#plugins-how-to-extend-workplane)

## Stack model

```
Workplane
 ├─ objects   list of Vector / Location / Shape / Sketch currently selected
 ├─ plane     the current 2D coordinate system (origin, xDir, zDir)
 ├─ parent    previous Workplane in the chain
 └─ ctx       shared context: pendingWires, pendingEdges, tags, firstPoint
```

- **Pending wires:** closed 2D shapes that `extrude`, `revolve`, `loft`, `sweep`, `cutBlind` or `cutThruAll` will use. `toPending()` changes selected wires or edges (for example, from an import) into pending wires.
- **Context solid:** the first solid on the stack or in the parent chain above it. Operations that add material fuse into it. Operations that remove material cut it. `findSolid()` gives it.
- **Automatic repetition:** the stack can have N points, vertices or faces. Then the tool applies `circle()`, `rect()`, `hole()` and operations relative to `workplane()` at each of them.
- **Construction geometry:** `rect(..., forConstruction=True)` makes a wire that you use only for its `vertices()`.

## Make and position workplanes

```python
import cadquery as cq

# Named planes: XY(+Z) YZ(+X) ZX(+Y) XZ(-Y) YX(-Z) ZY(-X)
# front(+Z) back(-Z) left(-X) right(+X) top(+Y) bottom(-Y)
wp = cq.Workplane("XY")
wp2 = cq.Workplane("XY", origin=(0, 0, 10))                       # offset origin
wp3 = cq.Workplane(cq.Plane(origin=(0, 0, 5), xDir=(1, 0, 0), normal=(0, 1, 1)))  # arbitrary

base = cq.Workplane("XY").box(40, 30, 10)
top = base.faces(">Z").workplane()                                # on top face, normal +Z
off = base.faces(">Z").workplane(offset=5)                        # 5 above the face
inv = base.faces("<Z").workplane(invert=True)                     # flip normal
ctr = base.faces(">X").workplane(centerOption="CenterOfBoundBox") # face centre
rot = base.faces(">Z").workplane().transformed(rotate=(0, 30, 0), offset=(5, 0, 0))
mov = top.center(10, 5)          # shift local origin (relative, accumulates)
abs_ = top.moveTo(10, 5)         # current point only (does not move origin)
on_vertex = base.faces(">Z").vertices("<XY").workplane(centerOption="CenterOfMass")
result = rot.rect(4, 4).extrude(3)
```

`centerOption` (how the tool selects the origin when you make a workplane on a face or vertex):

| Value | Origin |
|---|---|
| `"ProjectedOrigin"` (default) | The current origin (initially global `(0,0,0)`) projected onto the plane of the face |
| `"CenterOfBoundBox"` | The center of the bounding box of the selected objects |
| `"CenterOfMass"` | The center of mass of the selected objects |

To set the origin explicitly (global coordinates), give `origin=(x, y, z)`. After `.faces(">Z").workplane()`, the local x axis is usually the global +X axis. But on side faces, this is possibly not true. Build the model and examine it, or use `.transformed()`.

`copyWorkplane(other)` starts a new chain on the plane of a different Workplane: `cq.Workplane().copyWorkplane(base.faces(">Z").workplane())`.

## 2D drawing

All coordinates are **local** to the current workplane. Closed shapes automatically become pending wires.

| Method | Notes |
|---|---|
| `rect(xLen, yLen, centered=True, forConstruction=False)` | `centered=(False, False)` → corner at the current point |
| `circle(radius)` | |
| `ellipse(x_radius, y_radius, rotation_angle=0)` | |
| `polygon(nSides, diameter, circumscribed=False)` | regular polygon (the diameter of the circumscribed circle) |
| `slot2D(length, diameter, angle=0)` | slot (overall length). The length must be larger than the diameter |
| `polyline(points, includeCurrent=False)` | open polyline. Use `.close()` to make a wire |
| `lineTo(x, y)`, `line(dx, dy)`, `hLine(d)`, `vLine(d)`, `hLineTo(x)`, `vLineTo(y)`, `polarLine(d, angle)`, `polarLineTo(r, angle)` | segments from the current point |
| `threePointArc(p1, p2)`, `radiusArc(end, r)`, `tangentArcPoint(end, relative=True)`, `sagittaArc(end, sag)` | arcs from the current point (the sign of `r` or `sag` selects the side) |
| `spline(pts, tangents=None, periodic=False, includeCurrent=False)` | |
| `parametricCurve(func, N=400, start=0, stop=1, makeWire=True)` | `func(t) -> (x, y[, z])` |
| `close()` | adds a line to the start point → pending wire |
| `offset2D(d, kind="arc")` | offsets pending or selected wires (+ out, − in) |
| `mirrorX()`, `mirrorY()` | mirrors the current *open* edges and joins them → closed wire |
| `text(txt, fontsize, distance, combine="cut", halign, valign, font)` | 3D text (refer to the section below) |

Nested closed wires extrude as a part with holes (outer wire minus inner wire):

```python
import cadquery as cq

ring = cq.Workplane("XY").circle(20).circle(15).extrude(5)            # tube section
frame = cq.Workplane("XY").rect(50, 30).rect(40, 20).extrude(3)      # picture frame

# Line/arc profile -> extrude
profile = (
    cq.Workplane("XY")
    .moveTo(0, 0)
    .lineTo(30, 0)
    .lineTo(30, 10)
    .threePointArc((20, 18), (10, 10))
    .lineTo(0, 10)
    .close()
    .extrude(5)
)

# Half profile mirrored -> symmetric closed wire
sym = (
    cq.Workplane("XY")
    .hLine(10).vLine(4).hLine(-6).vLine(8).hLine(-4)
    .mirrorY()          # mirror about local Y axis and join
    .extrude(2)
)
result = sym
```

## Points and patterns

| Method | What it puts on the stack |
|---|---|
| `pushPoints([(x, y), ...])` or a list of `cq.Location` | the given points (local coordinates) |
| `rarray(xSpacing, ySpacing, xCount, yCount, center=True)` | rectangular grid |
| `polarArray(radius, startAngle, angle, count, fill=True, rotate=True)` | circular pattern. `rotate` turns each location |
| `.rect(w, h, forConstruction=True).vertices()` | 4 corners of a rectangle |
| `.vertices()` / `.edges()` / `.faces()` | the centers of the selected objects |
| `sketch().rarray(...)/parray(...)/distribute(...)` | patterns in a Sketch |

```python
import cadquery as cq

plate = cq.Workplane("XY").box(80, 60, 5)
result = (
    plate.faces(">Z").workplane()
    .rect(64, 44, forConstruction=True).vertices().hole(4)     # corner holes
    .faces(">Z").workplane()
    .polarArray(15, 0, 360, 6).hole(3)                         # bolt circle
    .faces(">Z").workplane()
    .pushPoints([(-30, 0), (30, 0)]).slot2D(10, 4, 90).cutThruAll()
)
```

`each(callback)` / `eachpoint(shape_or_callback)` put a shape at each item on the stack:

```python
import cadquery as cq

pin = cq.Workplane("XY").circle(1).extrude(4).val()  # a Shape at the origin
base = cq.Workplane("XY").box(30, 30, 3, centered=(True, True, False))
pins = base.faces(">Z").workplane().rarray(10, 10, 3, 3).eachpoint(pin, combine="a")
result = pins
```

## 3D primitives

By default, the center of all primitives is at the current point. Use `centered=(bx, by, bz)` to change this. By default, the primitives join the context solid.

| Method | Signature (primary arguments) |
|---|---|
| `box` | `box(length, width, height, centered=True)` |
| `cylinder` | `cylinder(height, radius, direct=(0,0,1), angle=360, centered=True)`. **The height is first** |
| `sphere` | `sphere(radius, angle1=-90, angle2=90, angle3=360)` |
| `wedge` | `wedge(dx, dy, dz, xmin, zmin, xmax, zmax)` |
| `torus`, `cone` | use `cq.Solid.makeTorus(...)`, `cq.Solid.makeCone(r1, r2, h)` or `cadquery.func` |

One primitive at each point: `.rarray(10, 10, 2, 2).box(4, 4, 4)`.

## Operations from profile to solid

| Method | Important arguments | Notes |
|---|---|---|
| `extrude(until, combine=True, both=False, taper=None)` | `until`: distance, `"next"`, `"last"`, or a `Face` | A negative value goes opposite to the normal. `both=True` is symmetric. `taper` is in degrees |
| `cutBlind(until, both=False, taper=None)` | distance (usually **negative** on a face workplane) | |
| `cutThruAll(clean=True, taper=0)` | | cuts through the full context solid (in the two directions) |
| `revolve(angleDegrees=360, axisStart=None, axisEnd=None)` | the axis points are in **local** coordinates | the profile must not cross the axis |
| `twistExtrude(distance, angleDegrees)` | | |
| `loft(ruled=False, combine=True)` | 2 or more pending wires on different workplanes are necessary | |
| `sweep(path, multisection=False, isFrenet=False, transition="right", normal=None, auxSpine=None)` | `path`: Workplane, Wire or Edge | use `isFrenet=True` for helices |
| `interpPlate(edges, pts, thickness)` | | surface patch with N sides |
| `split(keepTop=False, keepBottom=False)` | after `.workplane()` | cuts a solid with the plane of the workplane |

```python
import cadquery as cq

# extrude up to the next face (blind to geometry, not a number)
base = cq.Workplane("XY").box(20, 20, 2).faces(">Z").workplane(offset=10).rect(20, 20).extrude(2)
boss = base.faces("<Z[1]").workplane().circle(3).extrude("next")   # grows up until it meets the upper plate

# loft rectangle -> circle
loft = cq.Workplane("XY").rect(20, 20).workplane(offset=15).circle(6).loft()

# revolve a profile drawn in XZ about the local Y (global Z) axis
cup = (
    cq.Workplane("XZ")
    .polyline([(0, 0), (20, 0), (22, 30), (19, 30), (17, 3), (0, 3)]).close()
    .revolve(360, (0, 0, 0), (0, 1, 0))
)

# sweep a circle along a path drawn on another plane
path = cq.Workplane("XZ").polyline([(0, 0), (0, 20), (20, 40)])
pipe = cq.Workplane("XY").circle(3).sweep(path, transition="round")

# taper extrude (draft angle) and symmetric extrude
drafted = cq.Workplane("XY").rect(20, 10).extrude(10, taper=5)
sym = cq.Workplane("XY").circle(5).extrude(4, both=True)    # z from -4 to +4

# split a solid with the current workplane (here XY through the origin)
half = cq.Workplane("XY").sphere(10).split(keepTop=True)
# (a sphere has no planar face, so .faces(">Z").workplane() would fail here)
result = cup
```

## Holes, pockets, features

| Method | Signature |
|---|---|
| `hole(diameter, depth=None)` | through all if `depth=None`. The tool drills along −normal |
| `cboreHole(diameter, cboreDiameter, cboreDepth, depth=None)` | counterbore |
| `cskHole(diameter, cskDiameter, cskAngle, depth=None)` | countersink (82° for inch screws, 90° for metric screws) |
| `text(txt, fontsize, distance, combine="cut", ...)` | By default, it **cuts**: use −distance to engrave. Use `combine="a"` and +distance to emboss |

```python
import cadquery as cq

block = cq.Workplane("XY").box(60, 30, 10)
result = (
    block.faces(">Z").workplane()
    .pushPoints([(-20, 0)]).cboreHole(5.5, 10, 5.5)     # M5 SHCS counterbore
    .faces(">Z").workplane()
    .pushPoints([(0, 0)]).cskHole(4.5, 9, 90)            # M4 countersunk
    .faces(">Z").workplane()
    .pushPoints([(20, 0)]).hole(3, depth=6)              # blind hole
    .faces("<Y").workplane(centerOption="CenterOfBoundBox")
    .text("CQ", 6, -0.5)                                 # engraved label on the front
)
```

## Fillet, chamfer, shell

| Method | Notes |
|---|---|
| `fillet(radius)` | on the selected edges (or on all edges of the selected solids) |
| `chamfer(length, length2=None)` | asymmetric if you give `length2` |
| `shell(thickness, kind="arc")` | The tool removes the selected faces (the part becomes open). A negative value adds the wall to the inner side (the outer dimensions stay the same). With no selected faces (on a solid), the result is a closed hollow solid. |

```python
import cadquery as cq

result = (
    cq.Workplane("XY").box(40, 30, 20)
    .edges("|Z").fillet(4)        # vertical edges first (bigger radius)
    .faces(">Z").shell(-2)        # open-top box, 2 mm walls
    .faces(">Z").edges().chamfer(0.4)   # break the rim edges (inner+outer)
)
```

The radius must not be too large. The fillet radius must be less than half of the smallest adjacent face width. After a shell, it must be less than the wall thickness. Fillet the larger radii first.

## Booleans and combine modes

```python
import cadquery as cq

a = cq.Workplane("XY").box(20, 20, 20)
b = cq.Workplane("XY").sphere(13)
u = a.union(b)          # or a + b ; a | b
d = a.cut(b)            # or a - b
i = a.intersect(b)      # or a & b ; a * b
# Many tools at once: build them in one Workplane, cut once (much faster than looping)
tools = cq.Workplane("XY").rarray(5, 5, 3, 3).cylinder(30, 1)
holes = a.cut(tools)
result = holes
```

`combine` on 3D operations: `True`/`"a"` fuses (default), `"cut"`/`"s"` subtracts, `False` keeps the new solid separated (the result is only the new solid). `clean=True` (default) merges coplanar faces. If the clean step fails or is slow, give `clean=False`.

## Transformations and mirrors

```python
import cadquery as cq

part = cq.Workplane("XY").box(10, 4, 2, centered=False)
moved = part.translate((5, 0, 0))
turned = part.rotate((0, 0, 0), (0, 0, 1), 45)            # axis start, axis end, degrees
about = part.rotateAboutCenter((0, 0, 1), 30)
mirrored = part.mirror("YZ")                              # copy only
both = part.mirror("YZ", union=True)                      # original + mirror fused
on_face = part.mirror(part.faces(">X"), union=True)       # mirror across a face
result = both
```

## Stack navigation, tags, exit from the chain

| Method | Function |
|---|---|
| `end(n=1)` | goes back n steps in the chain |
| `first()`, `last()`, `item(i)` | make the selection smaller |
| `tag(name)` | gives a name to this point in the chain |
| `faces(sel, tag=name)` / `edges(..., tag=)` | selects from an object with a tag, not from the current object |
| `workplaneFromTagged(name)` | gives the workplane with the tag again |
| `add(obj)`, `newObject(objs)` | push shapes or workplanes onto the stack |
| `val()`, `vals()` | first object / all objects (exit from the chain) |
| `findSolid()` | the context solid |
| `solids()`, `wires()`, `shells()`, `vertices()` | selection by type |
| `filter(pred)`, `sort(key)`, `wp[i]`, `wp[a:b]` | selection in Python |
| `invoke(fn)` | calls `fn(wp)` in the chain (features with conditions) |
| `toPending()` | makes the selected wires or edges pending for the next 3D operation |
| `consolidateWires()` | joins pending edges into wires |
| `ctx`, `plane`, `objects`, `parent` | internal data. Useful to find problems |

```python
import cadquery as cq

def maybe_hole(enabled):
    return lambda wp: wp.hole(3) if enabled else wp

result = (
    cq.Workplane("XY").box(20, 20, 5).tag("base")
    .faces(">Z").workplane().circle(4).extrude(6)
    .faces(">Z").workplane().invoke(maybe_hole(True))
    .faces("<Z", tag="base").edges().chamfer(0.5)   # select from the tagged state's solid
)
assert len(result.solids().vals()) == 1
```

Note: `faces(sel, tag=...)` selects from the shape *as it was* at the time of the tag. But the next operation (`chamfer`) applies to the current context solid. Thus the edges must stay in the solid with no change.

## Plugins: how to extend Workplane

```python
import cadquery as cq

def rounded_pad(self, w, h, r, t):
    """Plugin: a rounded-rectangle pad of thickness t at every point on the stack."""
    pad = cq.Workplane("XY").rect(w, h).extrude(t).edges("|Z").fillet(r).val()
    # eachpoint places the shape at each stack location (in workplane coords)
    return self.eachpoint(pad, combine="a")

cq.Workplane.roundedPad = rounded_pad

result = (
    cq.Workplane("XY").box(50, 50, 3, centered=(True, True, False))
    .faces(">Z").workplane()
    .rarray(25, 25, 2, 2)
    .roundedPad(10, 6, 2, 1.5)
)
```

A more simple method is usually better. Write functions `def feature(wp: cq.Workplane, ...) -> cq.Workplane`, and use `.invoke(lambda wp: feature(wp, ...))`.
