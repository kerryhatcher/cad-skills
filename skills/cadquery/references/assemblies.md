# Assemblies

`cq.Assembly` puts parts (Workplanes or Shapes) in groups, with names, locations, colors and optional constraints. The position of each child is **relative to its parent**. The export keeps the tree, the names and the colors (STEP, XBF/XML, glTF).

## How to make an assembly

```python
import cadquery as cq

base = cq.Workplane("XY").box(40, 40, 5, centered=(True, True, False))
post = cq.Workplane("XY").cylinder(30, 4, centered=(True, True, False))

assy = (
    cq.Assembly(name="stand")
    .add(base, name="base", color=cq.Color("gray"))
    .add(post, name="post", loc=cq.Location((0, 0, 5)), color=cq.Color(0.8, 0.1, 0.1, 1))
)

# Nested sub-assembly: children inherit the sub-assembly's location
sub = cq.Assembly(name="feet")
for i, (x, y) in enumerate([(-15, -15), (15, -15), (15, 15), (-15, 15)]):
    sub.add(cq.Workplane("XY").cylinder(2, 3), name=f"foot{i}", loc=cq.Location((x, y, -1)))
assy.add(sub, name="feet")
result = assy
```

`add(obj, loc=None, name=None, color=None, material=None, metadata=None)`:

- `obj` can be a Workplane, a Shape or an Assembly. If you add an Assembly, `loc`, `name` and `color` replace the values of the sub-assembly.
- Give these arguments as keywords.
- The names of the children of one parent must be different. In `assy.objects`, the name of a nested child is `"feet/foot0"`.

Do you use the same part many times? Add the **same Workplane object** many times, each with a different `loc`. The exporters use one copy of the geometry (smaller STEP files).

## Locations

```python
import cadquery as cq

t = cq.Location((10, 0, 5))                          # translation
r = cq.Location((0, 0, 0), (0, 0, 1), 45)            # rotate 45 deg about +Z through the origin
tr = cq.Location((10, 0, 0), (1, 0, 0), 90)          # translate, then rotated 90 deg about X
combo = t * r                                        # apply r first, then t (right-to-left)
xyz = cq.Location(cq.Vector(5, 0, 0), cq.Vector(0, 0, 1), 30)
# Shapes also accept keyword placement: shape.moved(x=5, rz=30)  (rotations in degrees)
part = cq.Workplane("XY").box(10, 2, 2).val()
placed = part.moved(combo)
result = placed
```

- `parent.loc * child.loc` = the global position of the child.
- To move an object in **world** coordinates after the solver, multiply on the left: `obj.loc = cq.Location((0, 0, dz)) * obj.loc`.
- `loc.toTuple()` → `((x, y, z), (rx, ry, rz))` in degrees. This is useful for reports.

## Constraints

You do not have to calculate the locations. Declare the relations between parts, and call `solve()`. The solver moves the children to make the total constraint cost as small as possible.

```python
import cadquery as cq

plate = (
    cq.Workplane("XY").box(60, 40, 4)          # z from -2 to 2
    .faces(">Z").workplane().pushPoints([(-20, 0), (20, 0)]).hole(5)
)
pin = cq.Workplane("XY").cylinder(20, 2.5)     # centred: z from -10 to 10

# Tag mating features on the parts (selectors run in each part's own coordinates)
plate.faces("<Z").edges("%CIRCLE").edges("<X").tag("hole_left_bottom")
pin.faces("<Z").edges().tag("pin_bottom")      # circular edge -> centre + axis

assy = (
    cq.Assembly()
    .add(plate, name="plate", color=cq.Color("lightgray"))
    .add(pin, name="pin", color=cq.Color("goldenrod"))
    .constrain("plate", "Fixed")                                          # ground the base part
    # Plane = Point (concentric, flush bottoms) + Axis(180). The sense of a
    # circular edge's axis depends on edge orientation, so param=0 here would
    # flip the pin downward -- always verify the solved location.
    .constrain("plate?hole_left_bottom", "pin?pin_bottom", "Plane")
    .solve()
)
# Spin about the pin's own axis is still free (harmless for a cylinder).
(x, y, z), rot = assy.objects["pin"].loc.toTuple()
assert abs(x + 20) < 1e-3 and abs(y) < 1e-3 and abs(z - 8) < 1e-3   # pin centre at (-20, 0, 8)
result = assy
```

### How to refer to geometry

| Form | Meaning |
|---|---|
| `"name"` | the full part (its center for Point-type costs) |
| `"name?tag"` | an object with a tag on the Workplane of the part (`wp.faces(">Z").tag("top")`) |
| `"name@faces@>Z"` | a selector applied to the part: `@faces@`, `@edges@`, `@vertices@` and a selector string |
| `constrain("a", shape_a, "b", shape_b, "Kind")` | explicit `cq.Shape` objects (use `.val()`), for selections that strings cannot express |

### Constraint types

| Type | Arguments | Effect / `param` |
|---|---|---|
| `Point` | 2 | The centers are at the same position. `param` = distance between them (no direction) |
| `Axis` | 2 | Angle between the normals or directions. `param` in degrees, **default 180** (the faces point to each other). `param=0` = same direction (pin through a hole) |
| `Plane` | 2 | `Point` + `Axis`. **`param` is the Axis angle**, not an offset |
| `PointInPlane` | 2 | The center of the first object is in the plane of the second. `param` = offset along the normal of that plane |
| `PointOnLine` | 2 | The center of the first object is on the line of the second. `param` = offset |
| `Fixed` | 1 | The part does not move |
| `FixedPoint` | 1 | The center stays at `param=(x, y, z)` |
| `FixedRotation` | 1 | The rotation stays at `param=(rx, ry, rz)` degrees |
| `FixedAxis` | 1 | The normal or tangent stays along `param=(x, y, z)` |

How the Axis constraint gets a direction:

- Planar **Face**: the outward normal.
- **Circular Edge**: the axis of the circle. Its direction agrees with the edge orientation, which is difficult to know before. Examine the result.
- Other **Edge**: the tangent at the start.
- All other objects cause a `ValueError`.

If possible, use faces for Axis constraints.

### How to make constraints correct

1. **Fix one part** with `Fixed` (or give it a fixed location). If not, all parts are free to move.
2. **Count the degrees of freedom.** Each free part has 6. `Plane` removes 5 (the rotation about the shared normal stays free). To stop this rotation, add an `Axis` constraint between two side faces (`param=0` or 180), or add `FixedRotation`.
3. The solver gives no error for under-constrained systems, but the parts go to positions that you cannot predict. The initial `loc` values change the result. For over-constrained or contradictory systems, the solver gives a compromise.
4. The solver applies the selectors in `"name@faces@..."` to the part **in the coordinates of the part**, before the part moves.
5. After `solve()`, **examine the result**: run `inspect_model.py assy.py --interference`. Examine the translation and rotation of each part, and examine the render.

Example of mates that stop all six degrees of freedom:

```python
import cadquery as cq

box = cq.Workplane("XY").box(40, 30, 20, centered=(True, True, False))
lid = cq.Workplane("XY").box(40, 30, 3, centered=(True, True, False))

assy = (
    cq.Assembly()
    .add(box, name="box", color=cq.Color(0.2, 0.4, 0.8, 1))
    .add(lid, name="lid", color=cq.Color(0.9, 0.9, 0.9, 1))
    .constrain("box", "Fixed")
    .constrain("box@faces@>Z", "lid@faces@<Z", "Plane")        # touch, centred, facing
    .constrain("box@faces@>X", "lid@faces@>X", "Axis", param=0) # lock spin about Z
    .solve()
)
lid_loc = assy.objects["lid"].loc.toTuple()
assert abs(lid_loc[0][2] - 20) < 1e-3 and all(abs(a) < 1e-3 for a in lid_loc[1])
result = assy
```

## Colors

`cq.Color("red")` uses OCCT names in lower case, for example `"goldenrod"`, `"lightgray"`, `"steelblue"`, `"gray50"`. Some CSS names, such as `"silver"`, `"grey"` and `"crimson"`, are **not** correct and cause `ValueError: Unknown color name`. `cq.Color(r, g, b, a=1)` with floats from 0 to 1 always operates. To give colors to sub-shapes for export: `assy.addSubshape(part.faces(">Z").val(), name="top", color=cq.Color("red"), layer="L1")`.

## Examine the assembly and change it

```python
import cadquery as cq

assy = cq.Assembly().add(cq.Workplane().box(1, 1, 1), name="a")
for name, child in assy.traverse():          # (path_name, Assembly) pairs, depth-first
    print(name, child.loc.toTuple())
compound = assy.toCompound()                 # single Compound in world coordinates
print(list(assy.objects))                    # flat dict of all named nodes
result = compound
```

## Export

```python
# notest
assy.export("out.step")                              # names, colours, tree
assy.export("out.step", mode="fused")                # one fused solid, keeps colours of faces
assy.export("out.glb")                               # binary glTF (web viewers); .gltf = text
assy.export("out.xbf")                               # OCCT binary (round-trips via Assembly.load)
assy.export("out.step", unit="MM", outputUnit="M")   # scale on write
cq.exporters.export(assy.toCompound(), "out.stl")    # single mesh for printing
loaded = cq.Assembly.load("out.xbf")                 # STEP/XBF/XML import (new assembly)
```

Refer to `import-export.md` for more data about the formats.
