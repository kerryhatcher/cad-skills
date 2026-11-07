# Import & Export Reference

CadQuery's only fully parametric format is the Python script itself. Everything else is a snapshot: **STEP/BREP** keep exact geometry; **STL/3MF/AMF/glTF/VRML/VTP/ThreeJS** are triangle meshes; **DXF/SVG** are 2D.

## Choosing a format

| Need | Format |
|---|---|
| Hand off to another CAD tool (FreeCAD, Fusion, SolidWorks, Onshape) | `.step` |
| Exact OCCT round-trip | `.brep` (single shape), `.xbf` (assembly) |
| 3D printing | `.3mf` (units + multiple objects) or `.stl` (universal) |
| Laser / waterjet / CNC 2D | `.dxf` (from a planar face or `Sketch`) |
| Docs / quick visual | `.svg` (projection with hidden lines), PNG via `inspect_model.py --png` |
| Web viewing | `.glb` / `.gltf` (assemblies, coloured), ThreeJS `.json` |

## Exporting shapes / workplanes

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

Extensions inferred automatically: `.step .stl .3mf .amf .svg .dxf .vrml .vtp .brep`. Anything else (`.stp`, `.wrl`, `.json` for ThreeJS) needs the type: `"STEP"`, `"VRML"`, `"TJS"`. glTF and XML/XBF are assembly-only (wrap a part in `cq.Assembly()` first). `scripts/inspect_model.py -o FILE` handles all of these.

### Mesh quality (STL / 3MF / AMF / glTF)

- `tolerance` = max chord deviation (model units); `angularTolerance` = max angle between segments (radians).
- **`cq.exporters.export` defaults to `tolerance=0.1` — visibly faceted on small parts.** For printing use `0.01`–`0.05` mm and `angularTolerance=0.1`–`0.2`. Lower = bigger files.
- `Shape.exportStl(..., ascii=False)` writes binary STL (default) — smaller.

### Units

Geometry is unit-less; convention is **millimetres**. STEP writes a unit header:

```python
# notest
part.export("part.step", unit="MM")                    # default: declare mm
part.export("part_in.step", unit="MM", outputUnit="INCH")  # mm model written as inches (scaled)
cq.importers.importStep("vendor.step", unit="MM")      # convert on import (default mm)
```

Valid units: `MM CM M KM INCH FT MI UM NM`. STL/3MF carry no reliable units: slicers assume mm — model in mm.

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

DXF exports the shapes **in the current workplane plane** (sections/faces lying in it). Export a planar face, a 2D wire workplane, or a `Sketch`:

```python
import cadquery as cq

profile = cq.Workplane("XY").rect(60, 40).extrude(3).edges("|Z").fillet(5)
flat = profile.faces("<Z")                       # planar face at z=0 on the XY plane
cq.exporters.export(flat, "plate.dxf")           # laser-cut outline
sk = cq.Sketch().rect(30, 20).vertices().fillet(3)
sk.export("sketch.dxf")
result = profile
```

For a face not on XY, build a workplane on it first: `part.faces(">X").workplane()` … or `section()` the solid.

## Exporting assemblies

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

Name a sub-shape for STEP: `assy.addSubshape(face, name="top", color=cq.Color("red"), layer="L1")`.

## Importing

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

Imported STEP/BREP solids are dumb geometry: modify them with selectors + booleans (`cq.Workplane(obj=solid).faces(">Z").workplane().hole(5)`), they have no feature history. Vendor parts (screws, bearings, motors) imported from STEP make good assembly components.

## Verifying exports

- `inspect_model.py model.py -o out.step` then re-import: `cq.importers.importStep("out.step").val().isValid()` and compare `Volume()` to the original.
- For meshes, check face count/size is sane and open it in a slicer if printing.
- Re-run the export whenever parameters change — files are not linked to the script.
