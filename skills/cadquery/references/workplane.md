# Workplane (Fluent API) Reference

`cq.Workplane` is the main modelling API. Each method returns a **new** Workplane; the chain forms a history (the "stack"). Check exact signatures for the installed version with `uv run scripts/cq_api.py Workplane.<method>`.

## Contents
- [Stack model](#stack-model)
- [Creating & positioning workplanes](#creating--positioning-workplanes)
- [2D drawing](#2d-drawing)
- [Points & patterns](#points--patterns)
- [3D primitives](#3d-primitives)
- [Profile → solid operations](#profile--solid-operations)
- [Holes, pockets, features](#holes-pockets-features)
- [Fillet, chamfer, shell](#fillet-chamfer-shell)
- [Booleans & combine modes](#booleans--combine-modes)
- [Transforms & mirroring](#transforms--mirroring)
- [Stack navigation, tags, escaping the chain](#stack-navigation-tags-escaping-the-chain)
- [Plugins: extending Workplane](#plugins-extending-workplane)

## Stack model

```
Workplane
 ├─ objects   list of Vector / Location / Shape / Sketch currently selected
 ├─ plane     the current 2D coordinate system (origin, xDir, zDir)
 ├─ parent    previous Workplane in the chain
 └─ ctx       shared context: pendingWires, pendingEdges, tags, firstPoint
```

- **Pending wires**: closed 2D shapes waiting to be consumed by `extrude`/`revolve`/`loft`/`sweep`/`cutBlind`/`cutThruAll`. `toPending()` turns selected wires/edges (e.g. from an import) into pending ones.
- **Context solid**: the first solid found on the stack or up the parent chain. Additive ops fuse into it, subtractive ops cut it. `findSolid()` returns it.
- **Implicit iteration**: if the stack has N points/vertices/faces, `circle()`, `rect()`, `hole()`, `workplane()`-relative ops are applied at each.
- **Construction geometry**: `rect(..., forConstruction=True)` makes a wire you only use for its `vertices()`.

## Creating & positioning workplanes

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

`centerOption` (how the origin is chosen when creating a workplane from a face/vertex):

| Value | Origin |
|---|---|
| `"ProjectedOrigin"` (default) | Current origin (initially global `(0,0,0)`) projected onto the face plane |
| `"CenterOfBoundBox"` | Centre of the selected objects' bounding box |
| `"CenterOfMass"` | Centre of mass of the selected objects |

Pass `origin=(x, y, z)` to set it explicitly (global coords). After `.faces(">Z").workplane()` the local x axis is usually global +X, but for side faces it may not be — check by building, or set `.transformed()`.

`copyWorkplane(other)` starts a fresh chain on another Workplane's plane: `cq.Workplane().copyWorkplane(base.faces(">Z").workplane())`.

## 2D drawing

All coordinates are **local** to the current workplane. Closed shapes become pending wires automatically.

| Method | Notes |
|---|---|
| `rect(xLen, yLen, centered=True, forConstruction=False)` | `centered=(False, False)` → corner at current point |
| `circle(radius)` | |
| `ellipse(x_radius, y_radius, rotation_angle=0)` | |
| `polygon(nSides, diameter, circumscribed=False)` | regular polygon (diameter of circumscribed circle) |
| `slot2D(length, diameter, angle=0)` | obround / slot (overall length) |
| `polyline(points, includeCurrent=False)` | open polyline; `.close()` to make it a wire |
| `lineTo(x, y)`, `line(dx, dy)`, `hLine(d)`, `vLine(d)`, `hLineTo(x)`, `vLineTo(y)`, `polarLine(d, angle)`, `polarLineTo(r, angle)` | segment builders from current point |
| `threePointArc(p1, p2)`, `radiusArc(end, r)`, `tangentArcPoint(end, relative=True)`, `sagittaArc(end, sag)` | arcs from current point (sign of `r`/`sag` picks side) |
| `spline(pts, tangents=None, periodic=False, includeCurrent=False)` | |
| `parametricCurve(func, N=400, start=0, stop=1, makeWire=True)` | `func(t) -> (x, y[, z])` |
| `close()` | closes with a line to the start point → pending wire |
| `offset2D(d, kind="arc")` | offset pending/selected wires (+ out, − in) |
| `mirrorX()`, `mirrorY()` | mirror the current *open* edges and join → closed wire |
| `text(txt, fontsize, distance, combine="cut", halign, valign, font)` | 3D text (see below) |

Nested closed wires extrude as a part with holes (outer minus inner):

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

## Points & patterns

| Method | Puts on the stack |
|---|---|
| `pushPoints([(x, y), ...])` or list of `cq.Location` | given points (local coords) |
| `rarray(xSpacing, ySpacing, xCount, yCount, center=True)` | rectangular grid |
| `polarArray(radius, startAngle, angle, count, fill=True, rotate=True)` | circular pattern; `rotate` orients each location |
| `.rect(w, h, forConstruction=True).vertices()` | 4 corners of a rectangle |
| `.vertices()` / `.edges()` / `.faces()` | centres of selected entities |
| `sketch().rarray(...)/parray(...)/distribute(...)` | patterns inside a Sketch |

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

`each(callback)` / `eachpoint(shape_or_callback)` place arbitrary shapes at each stack item:

```python
import cadquery as cq

pin = cq.Workplane("XY").circle(1).extrude(4).val()  # a Shape at the origin
base = cq.Workplane("XY").box(30, 30, 3, centered=(True, True, False))
pins = base.faces(">Z").workplane().rarray(10, 10, 3, 3).eachpoint(pin, combine="a")
result = pins
```

## 3D primitives

All are centred on the current point by default; `centered=(bx, by, bz)` to change; combine with the context solid by default.

| Method | Signature (main args) |
|---|---|
| `box` | `box(length, width, height, centered=True)` |
| `cylinder` | `cylinder(height, radius, direct=(0,0,1), angle=360, centered=True)` — **height first** |
| `sphere` | `sphere(radius, angle1=-90, angle2=90, angle3=360)` |
| `wedge` | `wedge(dx, dy, dz, xmin, zmin, xmax, zmax)` |
| `torus`, `cone` | via `cq.Solid.makeTorus(...)`, `cq.Solid.makeCone(r1, r2, h)` or `cadquery.func` |

Repeated primitive at each point: `.rarray(10, 10, 2, 2).box(4, 4, 4)`.

## Profile → solid operations

| Method | Key args | Notes |
|---|---|---|
| `extrude(until, combine=True, both=False, taper=None)` | `until`: distance, `"next"`, `"last"`, or a `Face` | negative = opposite the normal; `both=True` symmetric; `taper` in degrees |
| `cutBlind(until, both=False, taper=None)` | distance (usually **negative** on a face workplane) | |
| `cutThruAll(clean=True, taper=0)` | | cuts through the whole context solid (both sides) |
| `revolve(angleDegrees=360, axisStart=None, axisEnd=None)` | axis points in **local** coords | profile must not cross the axis |
| `twistExtrude(distance, angleDegrees)` | | |
| `loft(ruled=False, combine=True)` | needs ≥2 pending wires on different workplanes | |
| `sweep(path, multisection=False, isFrenet=False, transition="right", normal=None, auxSpine=None)` | `path`: Workplane/Wire/Edge | `isFrenet=True` for helices |
| `interpPlate(edges, pts, thickness)` | | N-sided surface patch |
| `split(keepTop=False, keepBottom=False)` | after `.workplane()` | cut a solid with the workplane plane |

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
| `hole(diameter, depth=None)` | through-all if `depth=None`, drilled along −normal |
| `cboreHole(diameter, cboreDiameter, cboreDepth, depth=None)` | counterbore |
| `cskHole(diameter, cskDiameter, cskAngle, depth=None)` | countersink (82° imperial, 90° metric) |
| `text(txt, fontsize, distance, combine="cut", ...)` | default **cuts**: use −distance to engrave; `combine="a"` + distance to emboss |

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
| `fillet(radius)` | on selected edges (or all edges of selected solids) |
| `chamfer(length, length2=None)` | asymmetric if `length2` given |
| `shell(thickness, kind="arc")` | on selected faces → those faces are removed (opened). Negative = wall grows inward (keeps outer size). With no faces selected (on a solid) → closed hollow. |

```python
import cadquery as cq

result = (
    cq.Workplane("XY").box(40, 30, 20)
    .edges("|Z").fillet(4)        # vertical edges first (bigger radius)
    .faces(">Z").shell(-2)        # open-top box, 2 mm walls
    .faces(">Z").edges().chamfer(0.4)   # break the rim edges (inner+outer)
)
```

Radius must fit: fillet radius < half the smallest adjacent face width, and < wall thickness after shelling. Fillet larger radii first.

## Booleans & combine modes

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

`combine` on 3D ops: `True`/`"a"` fuse (default), `"cut"`/`"s"` subtract, `False` keep separate (result is just the new solid). `clean=True` (default) merges coplanar faces; pass `clean=False` if cleaning fails or is slow.

## Transforms & mirroring

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

## Stack navigation, tags, escaping the chain

| Method | Purpose |
|---|---|
| `end(n=1)` | go back n steps in the chain |
| `first()`, `last()`, `item(i)` | narrow the selection |
| `tag(name)` | name this point in the chain |
| `faces(sel, tag=name)` / `edges(..., tag=)` | select from a tagged object instead of current |
| `workplaneFromTagged(name)` | restore the tagged workplane |
| `add(obj)`, `newObject(objs)` | push shapes/workplanes onto the stack |
| `val()`, `vals()` | first object / all objects (exit the chain) |
| `findSolid()` | the context solid |
| `solids()`, `wires()`, `shells()`, `vertices()` | selection by type |
| `filter(pred)`, `sort(key)`, `wp[i]`, `wp[a:b]` | Python-level selection |
| `invoke(fn)` | call `fn(wp)` mid-chain (conditional features) |
| `toPending()` | make selected wires/edges pending for the next 3D op |
| `consolidateWires()` | join pending edges into wires |
| `ctx`, `plane`, `objects`, `parent` | internals — handy for debugging |

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

Note: `faces(sel, tag=...)` selects from the shape *as it was* when tagged, but the subsequent operation (`chamfer`) applies to the current context solid — the edges must still exist unchanged.

## Plugins: extending Workplane

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

Simpler and usually better: write plain functions `def feature(wp: cq.Workplane, ...) -> cq.Workplane` and use `.invoke(lambda wp: feature(wp, ...))`.
