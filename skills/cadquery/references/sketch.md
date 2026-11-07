# Sketch Reference

`cq.Sketch` builds 2D faces for extrude/revolve/loft/sweep/cut. It is often cleaner than chaining 2D Workplane calls: shapes combine with boolean **modes**, selections let you fillet/chamfer 2D corners, and the result is reusable.

Key differences from Workplane:
- **No history** — modifications happen in place; use `.copy()` to branch.
- **Selections persist** until `.reset()`. Forgetting `reset()` makes the next op apply at the selected vertices/edges.
- Methods are **multimethods**: pass arguments positionally (`arc((0,0), (1,1), (2,0))`), never as keywords for the positional parameters.

## Three ways to build

### 1. Face-based (most common)

Combine primitive faces with `mode`:

| mode | Effect |
|---|---|
| `"a"` (default) | add / fuse |
| `"s"` | subtract |
| `"i"` | intersect |
| `"r"` | replace existing faces |
| `"c"` | construction only (needs `tag=`), used for locating |

Primitives: `rect(w, h, angle=0)`, `circle(r)`, `ellipse(a1, a2, angle=0)`, `trapezoid(w, h, a1, a2=None, angle=0)`, `slot(w, h, angle=0)`, `regularPolygon(r, n, angle=0)`, `polygon(pts, angle=0)`, `face(shape_or_sketch)`.
Locations: `push([(x, y), ...])`, `rarray(xs, ys, nx, ny)`, `parray(r, a1, da, n, rotate=True)`, `distribute(n, start=0, stop=1, rotate=True)` (along selected edges/wires).

```python
import cadquery as cq

s = (
    cq.Sketch()
    .trapezoid(40, 30, 80)
    .vertices().circle(3, mode="s")      # subtract a circle at every corner
    .reset()
    .vertices().fillet(2)                # fillet remaining 2D corners
    .reset()
    .rarray(8, 1, 4, 1)
    .slot(6, 2, mode="s", angle=90)      # 4 vertical slots
)
result = cq.Workplane("XY").placeSketch(s).extrude(4)
```

Construction geometry and tags:

```python
import cadquery as cq

s = (
    cq.Sketch()
    .rect(30, 20, mode="c", tag="frame")   # not part of the face; only for locating
    .vertices(tag="frame")
    .circle(4)                             # bosses at the frame corners
    .reset()
    .rect(30, 20)                          # now the real body
    .clean()
)
result = cq.Workplane("XY").placeSketch(s).extrude(3)
```

### 2. Edge-based

Place edges, then `assemble()` into a face. Needed for custom outlines.

```python
import cadquery as cq

s = (
    cq.Sketch()
    .segment((0, 0), (40, 0))
    .segment((40, 15))                 # continues from the last point
    .arc((30, 22), (20, 15))           # three-point arc: from last point via (30,22) to (20,15)
    .segment((0, 15))
    .close()
    .assemble(tag="face")
    .edges("%LINE", tag="face")
    .vertices()
    .chamfer(1)
)
result = cq.Workplane("XY").placeSketch(s).extrude(5)
```

Edge methods: `segment(p1, p2)` / `segment(p2)` / `segment(length, angle)`, `arc(p1, p2, p3)` / `arc(p2, p3)` / `arc(center, r, start_angle, sweep_angle)`, `spline(pts, tangents=None, periodic=False)`, `bezier(pts)`, `close()`, `assemble(mode="a", tag=None)`.

### 3. Constraint-based (experimental)

Only segments and arcs. Tag each edge, add constraints, `solve()`, then `assemble()`.

```python
import cadquery as cq

s = (
    cq.Sketch()
    .segment((0, 0), (0, 3.0), "s1")
    .arc((0.0, 3.0), (1.5, 1.5), (0.0, 0.0), "a1")
    .constrain("s1", "Fixed", None)
    .constrain("s1", "a1", "Coincident", None)
    .constrain("a1", "s1", "Coincident", None)
    .constrain("s1", "a1", "Angle", 45)
    .solve()
    .assemble()
)
result = cq.Workplane("XY").placeSketch(s).extrude(1)
```

| Constraint | Arity | Argument |
|---|---|---|
| `Fixed` | 1 | `None` |
| `FixedPoint` | 1 | `None` (arc centre) or `0..1` position on the entity |
| `Coincident` | 2 | `None` |
| `Angle` | 2 | angle (deg) between tangents |
| `Length` | 1 | length |
| `Distance` | 2 | `(None or 0..1, None or 0..1, distance)` |
| `Radius` | 1 | radius (arcs) |
| `Orientation` | 1 | `(x, y)` direction (segments) |
| `ArcAngle` | 1 | angular span (arcs) |

Check the solver status with `s._solve_status` if a result looks wrong. For production models prefer explicit math in face/edge-based sketches.

## Selection inside a sketch

`faces()`, `edges()`, `wires()`, `vertices()` accept the usual selector strings (and `tag=`). Selection-dependent ops: `fillet(r)`, `chamfer(d)`, `offset`, `distribute`, `delete()`, and any primitive (placed at each selected location). Always `.reset()` before the next unrelated step.

## Using sketches with Workplane

```python
import cadquery as cq

# In-place: .sketch() ... .finalize() returns to the workplane chain
plate = (
    cq.Workplane("XY").box(50, 50, 5)
    .faces(">Z")
    .sketch()
    .regularPolygon(15, 6, tag="outer")
    .regularPolygon(10, 6, mode="s")
    .vertices(tag="outer").fillet(2)
    .finalize()
    .extrude(3)
)

# Reuse an existing sketch on a face
slot = cq.Sketch().slot(20, 6, angle=0)
cut = plate.faces("<Z").workplane().placeSketch(slot).cutThruAll()

# Multiple locations: sketch is placed at each point on the stack
studs = (
    cq.Workplane("XY").box(40, 40, 4)
    .faces(">Z").workplane().rarray(20, 20, 2, 2)
    .sketch().circle(4).circle(2, mode="s").finalize()
    .extrude(6)
)

# Loft between sketches: pass all in ONE placeSketch call
s1 = cq.Sketch().rect(20, 20).vertices().fillet(3)
s2 = cq.Sketch().circle(6)
loft = cq.Workplane("XY").placeSketch(s1, s2.moved(z=25)).loft()
result = loft
```

Operations that accept placed sketches: `extrude`, `twistExtrude`, `revolve`, `sweep`, `loft`, `cutBlind`, `cutThruAll`. Loft uses outer wires only (inner wires silently ignored).

## Combining & offsetting

```python
import cadquery as cq

a = cq.Sketch().rect(20, 20).vertices().fillet(3).reset()
b = cq.Sketch().circle(6)
diff = a - b                        # also: a + b (fuse), a * b (intersect)
same = a.copy().face(b, mode="s")   # equivalent via face()

outline = cq.Sketch().rect(10, 40).circle(10).clean()
grown = outline.copy().wires().offset(2)              # outward offset (adds)
shrunk = outline.copy().wires().offset(-2, mode="r")  # inward: replace original

result = (
    cq.Workplane("XY").placeSketch(grown).extrude(4)
    .faces(">Z").workplane().placeSketch(outline).cutBlind(-2)
)
```

## Import / export

```python
# notest
s = cq.Sketch().importDXF("profile.dxf", tol=1e-6)   # DXF -> sketch faces
s.export("profile.dxf")                               # also .svg / .step ...
```

## Gotchas

- A circle contributes one *seam vertex*, so `vertices()` after adding/subtracting circles also selects that point (a rect minus a circle has 5 vertices) — fillet corners before adding circles, or select via `tag=`.
- `clean()` after many `mode="a"` ops removes internal edges; needed before offset/fillet in some cases.
- `rect(w, h)` is centred; there is no `centered=` argument. Use `push([(x, y)])` first to move it.
- `moved(...)` returns a moved copy; `located(loc)` sets an absolute location.
