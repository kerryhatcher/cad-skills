# Troubleshooting

## Procedure to find a problem

1. **Divide the chain into parts.** Change a long fluent chain into named steps. Examine each step (`print(len(wp.vals()), wp.val().isValid())`). Remove features from the end, one at a time (make them comments), until the build is satisfactory.
2. **Examine the selection, not only the result.** Use `show_object(wp.edges(sel))`, or print the centers and the types:
   `[(e.geomType(), e.Center().toTuple()) for e in wp.edges(sel).vals()]`.
3. **Measure** after each feature: bbox, volume, number of solids (`scripts/inspect_model.py`). If a feature did not change the volume, the feature did not occur.
4. **Render** (`--png`, `--views`) and examine the images. Orthographic views (`--view front/top/right`) show features that are in an incorrect position.
5. **Examine the API of the installed version:** `scripts/cq_api.py Workplane.<method>`. The online documentation is for the development version.
6. **Change the parameters** (`--set`) to find the value where the build breaks. Add an `assert` statement for that value.

## Error messages

| Error | Usual cause | Repair |
|---|---|---|
| `StdFail_NotDone: BRep_API: command not done` (fillet or chamfer) | The radius or length is larger than an adjacent face. Or the edges meet at a vertex where the kernel cannot make the fillet | Use a smaller radius. Fillet less edges. Fillet before booleans that make small faces. Make the larger radii first. As an alternative, round the 2D profile in a `Sketch` |
| `StdFail_NotDone` (shell, hollow part) | The thickness is equal to or more than the local feature dimension. Complex lofts or sweeps | Use a thinner wall. Make the inner solid explicitly, and `cut` it |
| `StdFail_NotDone` (revolve, sweep, loft) | The profile crosses the axis of the revolve. The profile is not at the start of the path. The sweep intersects itself | Keep the profile on one side of the axis. Put the section at the start of the path, perpendicular to it. Increase the bend radius. Use `transition="round"` |
| `ValueError: No pending wires present` | A 3D operation with no closed 2D shape on the context. The wires came from a selection or an import | First make a closed shape. For selected or imported wires, use `.wires().toPending()`. Use `.close()` on open polylines |
| `ValueError: Cannot find a solid on the stack or in the parent chain` | `hole`, `cutBlind`, `cutThruAll` or `shell` before a solid is in the chain | Make the first solid in the same chain (or use `cq.Workplane(obj=solid)`) |
| `ValueError: Selected faces must be co-planar.` | `.workplane()` after you select many faces that are not coplanar | Select only one face (`faces(">Z")`, `.first()`) |
| `ValueError: If multiple objects selected, they all must be planar faces.` | The selection has curved faces | Select only planar faces (`%PLANE`), or make a `cq.Plane` explicitly |
| `StdFail_NotDone: GeomAPI_ProjectPointOnSurf::LowerDistanceParameters` | `.workplane()` on a curved face | A workplane must be on a planar face. Use `cq.Workplane(cq.Plane(origin, xDir, normal))` |
| `ValueError: Fillets requires that edges be selected` | The selector found no edges | Examine the selector. Print the number of selected objects |
| `AttributeError: 'Vector' object has no attribute ...` after `.val()` | The selection is empty, and `val()` gave the workplane origin | Repair the selector |
| `DispatchError: ... 0 methods found` | Keyword arguments to a multimethod (`Sketch.arc`, `Sketch.segment`, `Shape.moved`, func API) | Use positional arguments |
| `ValueError: Unknown extensions, specify export type explicitly` | `.stp`, `.wrl`, `.json` or `.glb` with `cq.exporters.export` | Use `.step`, or give the type (`"STEP"`, `"VRML"`, `"TJS"`). For glTF, use `Assembly.export` |
| `ValueError: Unknown color name: silver` | The name is not an OCCT color name | Use `cq.Color(r, g, b)` with floats, or a correct name (`"gray80"`, `"lightgray"`) |
| `StdFail_NotDone` on a primitive, `ValueError: normal should be non null`, `Standard_ConstructionError` | A feature with a dimension of 0 (`rect(0, 0)`, points at the same position) or a vector of 0 (`normal=(0,0,0)`). Usually a parameter combination causes this | Add `assert` statements, so that the parameters cannot become 0 or negative |
| `Standard_NoSuchObject` / `TopoDS::Face` errors | The method received an incorrect shape type (for example, a Wire, but the method must have a Face) | Change the type: `cq.Face.makeFromWires(w)`. Examine the type of `.val()` |
| Import errors (`ImportError: OCP`, `uv` cannot find wheels) | No `cadquery-ocp` wheels are available for this new Python version | `uv run -p 3.12 ...`, or `uv python install 3.12` |
| VTK `bad X server connection` warnings | The computer has no screen | If the tool wrote the PNG, ignore the warning. If not, use `xvfb-run -a uv run ...` |

## Errors with no error message (incorrect geometry)

| Symptom | Cause | Repair |
|---|---|---|
| A cut or pocket had no effect | `cutBlind(+d)` on a face workplane cuts out of the part, into empty space | Use a negative distance, or `extrude(-d, combine="cut")` |
| The text is not on the part | `text(..., +d)` with the default `combine="cut"` | Use `combine="a"` to emboss. Use a negative distance to engrave |
| `shell()` did not change the part | The thickness is too large for the part | Use a smaller thickness. Make sure that the volume decreased |
| Features in an incorrect position on a side face | The workplane origin is the projected global origin. The local x axis is not the global X axis | Use `centerOption="CenterOfBoundBox"` or `origin=`. Render the front and right views |
| A feature is mirrored, or on the opposite side | The normal of the `XZ` plane is −Y. The extrude direction agrees with the workplane normal | Examine the bbox. Change the sign, or use `invert=True` |
| Two solids, not one | The features do not touch (gap), or they touch only at an edge or a face (coplanar) | Make the features overlap by a small distance. Examine `len(wp.solids().vals())` |
| The box is above or below the origin | By default, `box` puts its center at the origin | `centered=(True, True, False)` |
| The hole is blind, but it must go through the part | `hole(d, depth)` measures from the workplane, and the workplane can be on a different face | Use `hole(d)` (through all), or examine the workplane offset |
| The pattern has one item too many or too few | `rarray` uses spacing and count. `polarArray(..., 360, n)` | `rarray(xSpacing, ySpacing, xCount, yCount)`. For a full circle, use `angle=360` and n items |
| An assembly part is flipped | The `param` of a `Plane` or `Axis` constraint is an angle (default 180). The direction of an axis from a circular edge changes with the orientation | Keep the default `param` for mates. Examine the solved locations. Use planar faces if possible |
| An assembly part turns about an axis | A `Plane` constraint does not stop the rotation about the normal | Add an `Axis` constraint between side faces, or `FixedRotation` |
| The tool finds interference between parts that only touch | The intersection gave faces with a thickness of 0 | Use only the volumes of `intersect(...).Solids()` (`inspect_model` does this) |
| The STL has large flat facets | The default of `cq.exporters.export` is `tolerance=0.1` | Use `tolerance=0.01` and `angularTolerance=0.1` |

## Speed

- Booleans use most of the run time. Put all cutters into one Workplane or Compound, and cut **one time**. Do not use `for ...: part = part.cut(...)`.
- Use many pending wires in one `cutThruAll()` or `extrude()`, not many different operations.
- In loops that run many times, give `clean=False` to the operations. Then call `.clean()` one time at the end.
- Fillets on hundreds of edges are slow. If possible, make the fillets in 2D (Sketch) before you extrude.
- Assemblies: use the same part object again for components that are the same.
- `cadquery.func.setThreads(n)` lets the kernel do booleans in parallel.

## Geometry validity

- If `shape.isValid()` gives False, `shape.fix()` can sometimes repair the shape. But it is better to remove the cause (coplanar booleans, very small edges, self-intersections).
- `cadquery.func.check(shape)` gives True or False, as `isValid()` does. To find the bad feature, divide the chain into parts.
- The most frequent cause of bad booleans is faces at exactly the same position. Make the cutters overlap by 0.01 mm to 0.1 mm, or make the cutters go farther than the faces that they cut.
