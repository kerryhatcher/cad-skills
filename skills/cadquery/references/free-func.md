# Free-function API, shapes and geometry

Below the fluent `Workplane` is the **Shape** layer (`cq.Solid`, `cq.Face`, `cq.Edge`, …) and the **free-function API** in `cadquery.func`. These functions have no state: they accept shapes and give new shapes. There is no hidden stack and there are no pending wires. The code is longer, but fully explicit. Use this API for generated geometry, surfaces, many instances, code that must be fast, and shapes that are difficult to make with a chain.

Topology sequence: `Vertex → Edge → Wire → Face → Shell → Solid → CompSolid → Compound`.

## Example

```python
from cadquery.func import circle, loft, fill, cap, solid

dh, r = 2.0, 1.0
e1 = circle(r)
e2 = circle(1.5 * r).moved(z=dh)
e3 = circle(r).moved(z=1.5 * dh)

side = loft(e1, e2, e3)                                   # side surface through 3 sections
bottom = fill(side.edges("<Z"))                           # planar fill
top = cap(side.edges(">Z"), side, [(0, 0, 1.6 * dh)])     # curvature-continuous cap
s = solid(side, bottom, top)                              # sew faces into a solid

result = s.moved((-3 * r, 0, 0), (3 * r, 0, 0))          # two copies -> Compound
```

## Primitives

| Function | Result |
|---|---|
| `segment(p1, p2)`, `polyline(*pts)`, `polygon(*pts)` | edge, wire, closed wire |
| `circle(r)`, `ellipse(r1, r2)`, `rect(w, h)` | closed edge or wire (in XY, center at the origin) |
| `spline(pts, tgts=None, periodic=False)` | edge |
| `plane(w, l)` / `plane()` | finite or infinite planar face |
| `box(w, l, h)`, `cylinder(d, h)`, `sphere(d)`, `torus(d1, d2)`, `cone(d, h)` / `cone(d1, d2, h)` | Solids. **The func primitives use diameters** (but `Workplane.cylinder(height, radius)` uses a radius). Use `.moved()` to set the position |
| `text(txt, size)` / `text(txt, size, spine, planar=False)` / `text(txt, size, spine, base)` | Text faces, text along a curve, or text projected onto a surface |
| `vertex(x, y, z)` | vertex |

```python
from cadquery.func import segment, circle, plane, box, cylinder, compound

e = segment((0, 0), (0, 1))
c = circle(1)
f = plane(1, 1.5)
b = box(1, 1, 1)
cyl = cylinder(2, 3)
result = compound(e, c.moved(x=2), f.moved(x=4), b.moved(x=6), cyl.moved(x=9))
assert abs(cyl.BoundingBox().xlen - 2) < 1e-6          # diameter 2, not radius
```

## Construction

| Function | Result |
|---|---|
| `wire(*edges)` | wire from edges |
| `face(outer_wire, *inner_wires)` | planar face (the inner wires make holes) |
| `shell(*faces, tol=1e-6, ctx=None)` | sewn shell |
| `solid(*faces_or_shells)` / `solid(outer_list, inner=[...])` | solid from closed faces or a shell (inner = cavities) |
| `compound(*shapes)` | compound (it also accepts a list) |
| `fill(edges_or_wire, constraints=[])` | fill surface (can be non-planar) |
| `cap(edges, ctx_shape, constraints)` | G1/G2 cap that agrees with a context surface |
| `offset2D(wire, d, kind="arc")` | planar wire offset |

## Operations

| Function | Notes |
|---|---|
| `extrude(shape, (dx, dy, dz))` | edge→face, wire→shell, face→solid |
| `revolve(shape, p, d, a=360)` | about the axis through `p` along `d` |
| `loft(*sections, cap=False, ruled=False, continuity="C2")` | sections = wires, edges or faces |
| `sweep(profile_or_list, path, aux=None, cap=False, transition="transformed")` | a list of profiles gives a multisection sweep |
| `fuse(a, b, ...)`, `cut(a, b)`, `intersect(a, b)`, `split(a, tool)` | also the operators `+`, `-`, `*`, `/` |
| `fillet(shape, edges, r)`, `chamfer(shape, edges, d)` | select the edges on the shape |
| `fillet2D(face, vertices, r)`, `chamfer2D(face, vertices, d)` | 2D corners |
| `hollow(solid, faces, t)` / `hollow(solid, t)` | shell with removed faces / closed hollow solid |
| `draft(ctx, base_face, faces, angle)` | adds draft to faces, relative to a neutral base face |
| `prism(...)` | local prism feature (boss or pocket) on a face |
| `offset(shape, t, cap=True, both=False)` | makes a solid from a face or a shell with a thickness |
| `clean(shape)`, `check(shape)` | merges coplanar faces / examines validity |
| `project`, `imprint`, `closest`, `isSubshape`, `setThreads` | other functions |

```python
from cadquery.func import rect, face, circle, spline, extrude, sweep, loft, revolve, fill, compound

r = rect(1, 0.5)
f = face(r, circle(0.2).moved(x=0.2))                 # face with a hole
path = spline([(0, 0, 0), (0, -1, 2)], [(0, 0, 1), (0, -1, 1)])

s1 = extrude(fill(r), (0, 0, 1))                     # solid
s2 = sweep(f, path)
s3 = loft(r, circle(0.2).moved(z=1), cap=True)
s4 = revolve(fill(r), (0.5, 0, 0), (0, 1, 0), 90)
result = compound([s.moved(x=2 * i) for i, s in enumerate((s1, s2, s3, s4))])
```

## Booleans

```python
from cadquery.func import cylinder, plane, fuse, cut, intersect, split, compound

c1 = cylinder(2, 2)           # diameter 2, height 2
c2 = cylinder(1, 3)
f1 = plane(2, 2).moved(z=1)
u = c1 + c2                   # fuse
d = c1 - c2                   # cut
i = c1 * c2                   # intersect
lower = (c1 / f1).solids("<Z")  # split by a face, keep the lower solid
result = compound(u, d.moved(x=3), i.moved(x=6), lower.moved(x=9))
```

**Speed:** booleans are the slowest operation. Do not fuse in a loop. Put the cutters in one `compound(...)` and cut one time: `base - compound(*tools)`.

## Selection on shapes

Shapes accept selector strings and set algebra directly:

- Plural methods (they give a Shape or a Compound): `vertices()`, `edges()`, `wires()`, `faces()`, `shells()`, `solids()`.
- Singular methods (they give exactly one object, or **raise** an error): `vertex()`, `edge()`, `wire()`, `face()`, `shell()`, `solid()`. These are good as assertions.
- Operators on selections: `a & b` (intersection), `a | b` (union), `a % b` (difference). Also `ancestors(shape, kind)` and `siblings(shape, kind)`.

```python
from cadquery.func import box, fillet

b = box(10, 10, 10)
top = b.face(">Z")                               # exactly one face, else raises
vert = b.edges("|Z")
rounded = fillet(b, vert, 1.0)
assert len(rounded.Faces()) == 10
result = rounded
```

## Position

`move()` (moves the shape) / `moved()` (moves a copy). Arguments: a `Location`, a tuple `(x, y, z)`, the keywords `x=, y=, z=, rx=, ry=, rz=` (degrees), or **many** locations or tuples. Many locations give a Compound of copies (a pattern).

```python
from cadquery.func import sphere, cylinder, compound

locs = [(0, -1, 0), (0, 1, 0)]
s = sphere(1).moved(locs)                        # 2 copies
c = cylinder(1, 2).moved(rx=15).moved(*locs)
result = compound(s, c.moved(x=3))
```

## History (experimental)

Give `history=History()` and `name="..."` to operations that accept them. Then query the generated or modified faces by operation name: `hist["hollow"].generated()`, `.modified()`, `.last()`. This lets you select the faces that a specified operation made, not faces at a position. The API can change. Examine it with `scripts/cq_api.py func.History`.

## Geometry classes

```python
import cadquery as cq

v = cq.Vector(1, 2, 3)
w = v + cq.Vector(0, 0, 1)            # arithmetic, .dot(), .cross(), .normalized(), .Length
p = cq.Plane(origin=(0, 0, 5), xDir=(1, 0, 0), normal=(0, 0, 1))
p2 = p.rotated((0, 0, 45))            # rotate about local axes (deg)
local = p.toLocalCoords(cq.Vector(1, 1, 5))
world = p.toWorldCoords((1, 1))
loc = cq.Location(p)                  # plane -> location
bb = cq.Workplane().box(2, 3, 4).val().BoundingBox()   # .xmin .xmax .xlen .center .DiagonalLength
result = cq.Workplane(p2).rect(2, 1).extrude(1)
```

## Measurements and checks of shapes

| Call | Result |
|---|---|
| `s.isValid()` | BRep check |
| `s.Volume()`, `s.Area()`, `edge.Length()` | |
| `s.BoundingBox()` | `BoundBox` |
| `s.Center()`, `cq.Shape.centerOfMass(s)` | `Vector` |
| `s.Solids()`, `s.Faces()`, `s.Edges()` | lists |
| `s.geomType()` | `"PLANE"`, `"CYLINDER"`, `"LINE"`, `"CIRCLE"`, … |
| `face.normalAt(pt=None)` | `Vector` |
| `s1.distance(s2)` | minimum distance |
| `s.fix()` | tries to repair the shape |
| `s.toSplines()`, `s.toNURBS()` | approximate or exact conversion to B-splines |

## How to use this API with the fluent API

```python
import cadquery as cq
from cadquery.func import box, circle, wire

shape = cq.Workplane().box(10, 5, 5).val()                 # Workplane -> Shape
wp = cq.Workplane(obj=box(10, 10, 10))                     # Shape -> Workplane
wp = wp.faces(">Z").workplane().circle(1).cutThruAll()
tool = wire(circle(1.0))
wp2 = cq.Workplane().box(10, 10, 10).newObject([tool]).toPending().cutThruAll()
result = wp2
```

To use OCCT directly, use `shape.wrapped` (a `TopoDS_Shape`) and `from OCP.<Package> import <Class>`. To change the results back to CadQuery shapes, use `cq.Shape.cast(topods)`.
