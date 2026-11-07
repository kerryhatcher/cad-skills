# Assemblies Reference

`cq.Assembly` groups parts (Workplanes or Shapes) with names, locations, colours, and optional constraints. Children are positioned **relative to their parent**. Export keeps the tree, names, and colours (STEP, XBF/XML, glTF).

## Building

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

`add(obj, loc=None, name=None, color=None, material=None, metadata=None)` — `obj` may be a Workplane, Shape, or Assembly (when adding an Assembly, `loc`/`name`/`color` override the sub-assembly's own). Pass these as keywords. Names must be unique among siblings; nested children are addressed `"feet/foot0"` in `assy.objects`.

Same part many times? Add the **same Workplane object** repeatedly with different `loc` — exporters share the geometry (smaller STEP files).

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

- `parent.loc * child.loc` = global placement of the child.
- To move something in **world** coordinates after solving, pre-multiply: `obj.loc = cq.Location((0, 0, dz)) * obj.loc`.
- `loc.toTuple()` → `((x, y, z), (rx, ry, rz))` degrees, handy for reporting.

## Constraints

Instead of computing locations, declare relationships and call `solve()`. The solver moves children to minimise all constraint costs.

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

### Referencing geometry

| Form | Meaning |
|---|---|
| `"name"` | the whole part (its centre for Point-type costs) |
| `"name?tag"` | object tagged on the part's Workplane (`wp.faces(">Z").tag("top")`) |
| `"name@faces@>Z"` | selector applied to the part: `@faces@`, `@edges@`, `@vertices@` + selector string |
| `constrain("a", shape_a, "b", shape_b, "Kind")` | explicit `cq.Shape`s (use `.val()`), for selections strings can't express |

### Constraint kinds

| Kind | Args | Effect / `param` |
|---|---|---|
| `Point` | 2 | centres coincide; `param` = distance between them (no direction) |
| `Axis` | 2 | angle between normals/directions; `param` deg, **default 180** (facing each other). `param=0` = same direction (pin through a hole) |
| `Plane` | 2 | `Point` + `Axis`. **`param` is the Axis angle**, not an offset |
| `PointInPlane` | 2 | centre of 1st lies in the plane of the 2nd; `param` = offset along that plane's normal |
| `PointOnLine` | 2 | centre of 1st lies on the line of the 2nd; `param` = offset |
| `Fixed` | 1 | part does not move |
| `FixedPoint` | 1 | centre fixed at `param=(x, y, z)` |
| `FixedRotation` | 1 | rotation fixed at `param=(rx, ry, rz)` deg |
| `FixedAxis` | 1 | normal/tangent fixed to `param=(x, y, z)` |

Direction extraction for Axis: planar **Face** → outward normal; **circular Edge** → circle axis (its sense follows the edge orientation — hard to predict, so verify); other **Edge** → tangent at start. Anything else raises `ValueError`. Prefer faces for Axis constraints when you can.

### Getting constraints right

1. **Ground one part** with `Fixed` (or give it a fixed location) — otherwise everything floats.
2. **Count degrees of freedom**: each free part has 6. `Plane` removes 5 (rotation about the shared normal stays free!). Add an `Axis` between two side faces (`param=0` or 180) or `FixedRotation` to lock it.
3. Under-constrained systems "solve" without error but put parts somewhere arbitrary; initial `loc` values bias the result. Over-constrained/contradictory ones converge to a compromise.
4. Selectors in `"name@faces@..."` are evaluated on the part **in its own coordinates**, before placement.
5. After `solve()`, **verify**: `inspect_model.py assy.py --interference`, check each part's reported translation/rotation and look at the render.

Mating example that locks all six DOF:

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

## Colours

`cq.Color("red")` (OCCT names, lowercase, e.g. `"goldenrod"`, `"lightgray"`, `"steelblue"`, `"gray50"`; some CSS names like `"silver"`, `"grey"`, `"crimson"` are **not** valid → `ValueError: Unknown color name`), or `cq.Color(r, g, b, a=1)` with 0–1 floats (always safe). Colour sub-shapes for export: `assy.addSubshape(part.faces(">Z").val(), name="top", color=cq.Color("red"), layer="L1")`.

## Inspect & iterate

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

See `import-export.md` for format details.
