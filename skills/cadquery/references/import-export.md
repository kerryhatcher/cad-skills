# Import and export

The only fully parametric format of CadQuery is the Python script. All other formats are a copy at one point in time. **STEP and BREP** keep the exact geometry. **STL, 3MF, AMF, glTF, VRML, VTP and ThreeJS** are triangle meshes. **DXF and SVG** are 2D.

## How to select a format

| Purpose | Format |
|---|---|
| Give the model to a different CAD tool (FreeCAD, Fusion, SolidWorks, Onshape) | `.step` |
| Export and import in OCCT with no change | `.brep` (single shape), `.xbf` (assembly) |
| 3D printing | `.3mf` (units and many objects) or `.stl` (all slicers) |
| Laser, waterjet, 2D CNC | `.dxf` (from a planar face or a `Sketch`) |
| Documentation, fast visual check | `.svg` (projection with hidden lines), PNG with `inspect_model.py --png` |
| Views in a web browser | `.glb` / `.gltf` (assemblies, with colors), ThreeJS `.json` |

## Export of shapes and workplanes

```python
import cadquery as cq

part = cq.Workplane("XY").box(20, 20, 10).faces(">Z").workplane().hole(5)

part.export("part.step")                                   # Workplane.export, type from extension
cq.exporters.export(part, "part.stl", tolerance=0.01, angularTolerance=0.1)
cq.exporters.export(part, "part.3mf", tolerance=0.01)
cq.exporters.export(part, "part.stp", "STEP")              # non-standard extension -> explicit type
part.val().exportBrep("part.brep")                         # Shape methods: exportStep/exportStl/exportBrep
result = part
```

The export function finds the type from these extensions: `.step .stl .3mf .amf .svg .dxf .vrml .vtp .brep`. For other extensions (`.stp`, `.wrl`, `.json` for ThreeJS), give the type: `"STEP"`, `"VRML"`, `"TJS"`. glTF and XML/XBF are only for assemblies (first put the part in a `cq.Assembly()`). `scripts/inspect_model.py -o FILE` can export to all these formats.

### Mesh quality (STL, 3MF, AMF, glTF)

- `tolerance` is the maximum chord deviation (model units). `angularTolerance` is the maximum angle between segments (radians).
- **The default of `cq.exporters.export` is `tolerance=0.1`. Small parts then show flat facets.** For printing, use `0.01` mm to `0.05` mm and `angularTolerance=0.1` to `0.2`. Lower values give larger files.
- `Shape.exportStl(..., ascii=False)` writes binary STL (the default). Binary files are smaller.

### Units

The geometry has no units. The convention is **millimeters**. STEP writes a unit header:

```python
# notest
part.export("part.step", unit="MM")                    # default: declare mm
part.export("part_in.step", unit="MM", outputUnit="INCH")  # mm model written as inches (scaled)
cq.importers.importStep("vendor.step", unit="MM")      # convert on import (default mm)
```

Correct units: `MM CM M KM INCH FT MI UM NM`. STL and 3MF files do not have reliable units. Slicers use mm. Thus make the model in mm.

### SVG options

```python
import cadquery as cq

part = cq.Workplane("XY").box(20, 10, 5).edges("|Z").fillet(2).faces(">Z").workplane().hole(4)
cq.exporters.export(
    part, "drawing.svg",
    opt={
        "width": 400, "height": 300,
        "marginLeft": 10, "marginTop": 10,
        "projectionDir": (1, -1, 1),      # view direction (camera looks along -dir)
        "showAxes": False,
        "showHidden": True,
        "strokeWidth": 0.4,
        "strokeColor": (0, 0, 0),
        "hiddenColor": (150, 150, 150),
        # "focus": 50,                    # perspective
    },
)
result = part
```

### DXF (2D)

DXF exports the shapes **in the plane of the current workplane** (sections or faces in that plane). Export a planar face, a 2D wire workplane, or a `Sketch`:

```python
import cadquery as cq

profile = cq.Workplane("XY").rect(60, 40).extrude(3).edges("|Z").fillet(5)
flat = profile.faces("<Z")                       # planar face at z=0 on the XY plane
cq.exporters.export(flat, "plate.dxf")           # laser-cut outline
sk = cq.Sketch().rect(30, 20).vertices().fillet(3)
sk.export("sketch.dxf")
result = profile
```

For a face that is not on XY, first make a workplane on that face: `part.faces(">X").workplane()` …, or use `section()` on the solid.

## Export of assemblies

```python
import cadquery as cq

assy = cq.Assembly(name="demo")
assy.add(cq.Workplane().box(10, 10, 10), name="body", color=cq.Color(1, 0, 0))
assy.add(cq.Workplane().center(2, 2).cylinder(20, 2), name="pin", color=cq.Color(0, 1, 0))

assy.export("demo.step")                    # tree + names + colours
assy.export("demo_fused.step", mode="fused")  # one solid, face colours kept
assy.export("demo.glb")                     # binary glTF
assy.export("demo.xbf")                     # OCCT native, reloadable
cq.exporters.export(assy.toCompound(), "demo.stl", tolerance=0.01)   # mesh of everything
reloaded = cq.Assembly.load("demo.xbf")
result = reloaded
```

To give a name to a sub-shape for STEP: `assy.addSubshape(face, name="top", color=cq.Color("red"), layer="L1")`.

## Import

```python
# notest
import cadquery as cq

step = cq.importers.importStep("bracket.step")                 # Workplane (solids on stack)
solid = step.val()
dxf = cq.importers.importDXF("profile.dxf", tol=1e-6)          # Workplane with face(s) built from the DXF
extruded = dxf.wires().toPending().extrude(10)                 # toPending() is required
inner_only = cq.importers.importDXF("profile.dxf", include=["CUT"])   # filter layers
sk = cq.Sketch().importDXF("profile.dxf")                      # straight into a Sketch
brep = cq.importers.importBrep("part.brep")
assy = cq.Assembly.load("assembly.step")                        # STEP/XBF/XML -> Assembly
```

Imported STEP and BREP solids have no feature history. Change them with selectors and booleans (`cq.Workplane(obj=solid).faces(">Z").workplane().hole(5)`). STEP files of supplier parts (screws, bearings, motors) are good assembly components.

## How to examine exports

- Run `inspect_model.py model.py -o out.step`, then import the file again: `cq.importers.importStep("out.step").val().isValid()`. Compare the `Volume()` with the initial model.
- For meshes, make sure that the number of faces and the file size are applicable. If you will print the part, open the file in a slicer.
- Export again each time that the parameters change. The files have no connection to the script.
