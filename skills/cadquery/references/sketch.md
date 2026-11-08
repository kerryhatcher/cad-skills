# Sketch

`cq.Sketch` makes 2D faces for extrude, revolve, loft, sweep and cut. It is frequently cleaner than a chain of 2D Workplane calls. Shapes join with boolean **modes**. Selections let you fillet or chamfer 2D corners. You can use the result again.

Important differences from Workplane:
- **No history:** the changes occur in the sketch. To make a different version, use `.copy()`.
- **Selections stay** until `.reset()`. If you do not call `reset()`, the next operation occurs at the selected vertices or edges.
- The methods are **multimethods**. Give the arguments by position (`arc((0,0), (1,1), (2,0))`). Do not give positional parameters as keywords.

## Three methods to make a sketch

### 1. From faces (the most frequent method)

Join primitive faces with `mode`:

| mode | Effect |
|---|---|
| `"a"` (default) | add (fuse) |
| `"s"` | subtract |
| `"i"` | intersect |
| `"r"` | replace the faces that are there |
| `"c"` | construction only (`tag=` is necessary), for the location of other items |

Primitives: `rect(w, h, angle=0)`, `circle(r)`, `ellipse(a1, a2, angle=0)`, `trapezoid(w, h, a1, a2=None, angle=0)`, `slot(w, h, angle=0)`, `regularPolygon(r, n, angle=0)`, `polygon(pts, angle=0)`, `face(shape_or_sketch)`.
Locations: `push([(x, y), ...])`, `rarray(xs, ys, nx, ny)`, `parray(r, a1, da, n, rotate=True)`, `distribute(n, start=0, stop=1, rotate=True)` (along the selected edges or wires).

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

### 2. From edges

Put the edges, then make a face with `assemble()`. Use this method for custom outlines.

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

### 3. From constraints (experimental)

Only segments and arcs. Put a tag on each edge, add the constraints, call `solve()`, then call `assemble()`.

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

| Constraint | Number of objects | Argument |
|---|---|---|
| `Fixed` | 1 | `None` |
| `FixedPoint` | 1 | `None` (arc center) or `0..1` position on the object |
| `Coincident` | 2 | `None` |
| `Angle` | 2 | angle (degrees) between the tangents |
| `Length` | 1 | length |
| `Distance` | 2 | `(None or 0..1, None or 0..1, distance)` |
| `Radius` | 1 | radius (arcs) |
| `Orientation` | 1 | `(x, y)` direction (segments) |
| `ArcAngle` | 1 | angle of the arc |

If a result looks incorrect, examine the solver status with `s._solve_status`. For final models, use explicit calculations in sketches from faces or edges.

## Selection in a sketch

`faces()`, `edges()`, `wires()` and `vertices()` accept the usual selector strings (and `tag=`). Some operations use the selection: `fillet(r)`, `chamfer(d)`, `offset`, `distribute`, `delete()`, and all primitives (the sketch puts them at each selected location). Always call `.reset()` before the next step that is not related.

## How to use sketches with a Workplane

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

These operations accept placed sketches: `extrude`, `twistExtrude`, `revolve`, `sweep`, `loft`, `cutBlind`, `cutThruAll`. Loft uses only the outer wires (it ignores the inner wires and gives no error).

## Join and offset

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

## Import and export

```python
# notest
s = cq.Sketch().importDXF("profile.dxf", tol=1e-6)   # DXF -> sketch faces
s.export("profile.dxf")                               # also .svg / .step ...
```

## Frequent problems

- A circle adds one *seam vertex*. Thus, after you add or subtract circles, `vertices()` also selects that point (a rectangle minus a circle has 5 vertices). Fillet the corners before you add circles, or select with `tag=`.
- After many `mode="a"` operations, `clean()` removes the internal edges. Some offset and fillet operations need this step.
- The center of `rect(w, h)` is at the location. There is no `centered=` argument. To move the rectangle, first use `push([(x, y)])`.
- `moved(...)` gives a moved copy. `located(loc)` sets an absolute location.
