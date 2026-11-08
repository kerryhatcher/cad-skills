# Selectors

Selectors filter the objects that `vertices()`, `edges()`, `wires()`, `faces()`, `shells()` and `solids()` give on a Workplane, Sketch or Shape. The strings are short forms of the selector classes in `cq.selectors`.

## String syntax

The axis can be `X`, `Y`, `Z`, or a vector such as `(1, -1, 0)` in the string: `">(1,-1,0)"`.

| Selector | Faces | Edges | Vertices | Class |
|---|---|---|---|---|
| `+Z` / `-X` | the normal points to +Z / −X | the edge direction is +Z / −X (lines only) | – | `DirectionSelector` |
| `\|Z` | the normal is parallel to Z (top **and** bottom) | edges parallel to Z (lines only) | – | `ParallelDirSelector` |
| `#Z` | the normal is perpendicular to Z (the sides) | edges perpendicular to Z | – | `PerpendicularDirSelector` |
| `>Z` / `<Z` | farthest in +Z / −Z (by center) | farthest in +Z / −Z | farthest | `DirectionMinMaxSelector` |
| `>Z[n]` / `<Z[n]` | the n-th face **normal to Z**, in sequence along Z (`[0]` = first, `[-1]` = last, `[-2]` = second farthest) | the n-th **parallel** edge | – | `DirectionNthSelector` |
| `>>Z[n]` / `<<Z[n]` | the n-th face by center position along Z, all orientations | the n-th edge by center | the n-th vertex | `CenterNthSelector` |
| `%PLANE` | face geometry type | – | – | `TypeSelector` |
| `%LINE` / `%CIRCLE` | – | edge geometry type | – | `TypeSelector` |

Face types: `PLANE, CYLINDER, CONE, SPHERE, TORUS, BEZIER, BSPLINE, REVOLUTION, EXTRUSION, OFFSET`. Edge types: `LINE, CIRCLE, ELLIPSE, HYPERBOLA, PARABOLA, BEZIER, BSPLINE, OFFSET`. Upper case and lower case give the same result.

**Important**
- Direction selectors (`+Z`, `|Z`, `#Z`, `>Z[n]`) ignore edges that are not straight. For curved faces, they use the center of mass. For arcs, use `%CIRCLE`, `>>`/`<<` or `BoxSelector`.
- `>Z` gives **all** objects that are at the same farthest position (for example, two coplanar top faces). It does not always give one object.
- An empty result causes an error only in the next operation (`Fillets requires that edges be selected`, or `.val()` gives a `Vector`). Examine the count with `len(wp.vals())`.

## How to use selectors together

Operators: `and`, `or`, `not`, `exc` (except, set difference), with parentheses.

```python
import cadquery as cq

box = cq.Workplane("XY").box(20, 20, 10)
top_outer = box.edges("|Z and >Y")                       # vertical edges at +Y
not_bottom = box.edges("not <Z")                         # all edges except bottom loop
side_faces = box.faces("#Z")                             # 4 side faces
top_and_bottom = box.faces(">Z or <Z")
inner_top = (
    cq.Workplane("XY").box(20, 20, 10).faces(">Z").shell(-2)
    .faces(">Z").edges("not(<X or >X or <Y or >Y)")      # inner rim loop only
)
result = inner_top.chamfer(0.5)
assert len(box.edges("|Z and >Y").vals()) == 2
```

## Nth selection

```python
import cadquery as cq

stepped = (
    cq.Workplane("XY").box(30, 20, 5, centered=(True, True, False))
    .faces(">Z").workplane().rect(20, 20).extrude(5)
    .faces(">Z").workplane().rect(10, 20).extrude(5)
)
# faces normal to Z, sorted along Z: [0]=bottom, [-1]=top, [-2]=middle step(s)
mid = stepped.faces(">Z[-2]")
assert abs(mid.val().Center().z - 10) < 1e-6
result = mid.workplane().pushPoints([(-7.5, 0)]).hole(3)
```

## Selector objects (if strings are not sufficient)

```python
import cadquery as cq
from cadquery import selectors as sel

part = cq.Workplane("XY").box(40, 20, 10).edges("|Z").fillet(2)

# edges inside an axis-aligned box (corners: two opposite points)
in_box = part.edges(sel.BoxSelector((-25, -15, 4), (0, 15, 6)))

# nearest to a point
near = part.vertices(sel.NearestToPointSelector((20, 10, 5)))

# radius filter (circular edges) - nth by radius, 0 = smallest
small_arcs = part.edges(sel.RadiusNthSelector(0))

# length filter
longest = part.edges(sel.LengthNthSelector(-1))

# set algebra on selector objects: + (or), - (except), & (and), -sel (not)
combo = part.edges(sel.DirectionMinMaxSelector(cq.Vector(0, 0, 1)) - sel.TypeSelector("CIRCLE"))
result = part.edges(sel.BoxSelector((-25, -15, 4), (25, 15, 6))).chamfer(0.5)
```

Other classes: `AreaNthSelector`, `CenterNthSelector`, `DirectionNthSelector`, `ParallelDirSelector`, `PerpendicularDirSelector`, `NearestToShapeSelector`, `StringSyntaxSelector`, `SumSelector`, `SubtractSelector`, `AndSelector`, `InverseSelector`. To see them all, run `uv run scripts/cq_api.py selectors`.

## Filters in Python

```python
import cadquery as cq

part = cq.Workplane("XY").box(40, 20, 10).faces(">Z").workplane().pushPoints([(-10, 0), (10, 0)]).hole(4).hole(8, 2)
# lambda filter on shapes
big_circles = part.edges("%CIRCLE").filter(lambda e: e.radius() > 3)
# sort and slice
two_lowest = part.faces().sort(lambda f: f.Center().z)[:2]
result = part
assert len(big_circles.vals()) > 0
```

## Topological selection

```python
import cadquery as cq

box = cq.Workplane("XY").box(10, 10, 10)
faces_of_edge = box.faces(">Z").edges("<Y").ancestors("Face")   # faces sharing that edge
neighbours = box.faces(">Z").siblings("Edge")                    # faces touching the top via an edge
result = box
assert len(faces_of_edge.vals()) == 2
```

## Selection on `Shape` and `Sketch` objects

Shapes accept the same selector strings and set operators:

```python
import cadquery as cq

solid = cq.Solid.makeBox(1, 2, 3)
top_and_bottom_wires = solid.faces(">Z or <Z").wires()
result = solid
```

## How to find selection problems

1. Print the counts: `print(len(wp.faces(">Z").vals()))`.
2. Print the centers and types: `[ (e.geomType(), e.Center().toTuple()) for e in wp.edges(sel).vals() ]`.
3. Render only the selection: put `wp.edges(sel)` in `show_object(...)`, or use a different `inspect_model.py` run.
4. Use **tags**. Do not make the selection again after the geometry changes.
