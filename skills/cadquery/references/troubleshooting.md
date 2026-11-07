# Troubleshooting

## Debugging workflow

1. **Bisect the chain.** Split a long fluent chain into named steps and check each one (`print(len(wp.vals()), wp.val().isValid())`). Comment out features from the end until it builds.
2. **Look at the selection, not just the result.** `show_object(wp.edges(sel))`, or print centres and types:
   `[(e.geomType(), e.Center().toTuple()) for e in wp.edges(sel).vals()]`.
3. **Measure** after each feature: bbox, volume, solid count (`scripts/inspect_model.py`). A feature that didn't change the volume didn't happen.
4. **Render** (`--png`, `--views`) and look. Orthographic `--view front/top/right` exposes misplacements.
5. **Check the API of the installed version**: `scripts/cq_api.py Workplane.<method>` — online docs follow the dev branch.
6. **Vary parameters** (`--set`) to find the boundary where it breaks; add an `assert` there.

## Error messages

| Error | Usual cause | Fix |
|---|---|---|
| `StdFail_NotDone: BRep_API: command not done` (fillet/chamfer) | radius/length larger than an adjacent face, or edges meet at a vertex where the fillet can't be built | smaller radius; fillet fewer edges; fillet before booleans that create small faces; do larger radii first; round 2D profiles in a `Sketch` instead |
| `StdFail_NotDone` (shell / hollow) | thickness ≥ local feature size, complex lofts/sweeps | thinner wall; build the inner solid explicitly and `cut` it |
| `StdFail_NotDone` (revolve / sweep / loft) | profile crosses the revolve axis; profile not at path start; self-intersecting sweep | keep the profile on one side of the axis; place the section at the path start, perpendicular; increase bend radius; `transition="round"` |
| `ValueError: No pending wires present` | 3D op with no closed 2D shape on the context; wires came from a selection or import | draw a closed shape first; `.wires().toPending()` for selected/imported wires; `.close()` open polylines |
| `ValueError: Cannot find a solid on the stack or in the parent chain` | `hole`, `cutBlind`, `cutThruAll`, `shell` before any solid exists | create the base solid in the same chain (or `cq.Workplane(obj=solid)`) |
| `ValueError: Selected faces must be co-planar.` | `.workplane()` after selecting several non-coplanar faces | narrow the selection to one face (`faces(">Z")`, `.first()`) |
| `ValueError: If multiple objects selected, they all must be planar faces.` | selection contains curved faces | select planar faces only (`%PLANE`) or create a `cq.Plane` explicitly |
| `StdFail_NotDone: GeomAPI_ProjectPointOnSurf::LowerDistanceParameters` | `.workplane()` on a curved face | workplane needs a planar face; use `cq.Workplane(cq.Plane(origin, xDir, normal))` |
| `ValueError: Fillets requires that edges be selected` | selector matched nothing | check the selector; print the count |
| `AttributeError: 'Vector' object has no attribute ...` after `.val()` | empty selection — `val()` returned the workplane origin | fix the selector |
| `DispatchError: ... 0 methods found` | keyword args to a multimethod (`Sketch.arc`, `Sketch.segment`, `Shape.moved`, func API) | pass positional arguments |
| `ValueError: Unknown extensions, specify export type explicitly` | `.stp`, `.wrl`, `.json`, `.glb` via `cq.exporters.export` | use `.step`, pass the type (`"STEP"`, `"VRML"`, `"TJS"`), or `Assembly.export` for glTF |
| `ValueError: Unknown color name: silver` | not an OCCT colour name | `cq.Color(r, g, b)` floats, or a valid name (`"gray80"`, `"lightgray"`) |
| `StdFail_NotDone` on a primitive, `ValueError: normal should be non null`, `Standard_ConstructionError` | zero-size feature (`rect(0, 0)`, coincident points) or zero vector (`normal=(0,0,0)`) — usually a parameter combination | `assert` parameters can't reach 0 / negative sizes |
| `Standard_NoSuchObject` / `TopoDS::Face` errors | wrong shape type passed (e.g. a Wire where a Face is needed) | convert: `cq.Face.makeFromWires(w)`; check `.val()` type |
| Import errors (`ImportError: OCP`, wheel resolution failures) | Python too new for available `cadquery-ocp` wheels | `uv run -p 3.12 ...`; or `uv python install 3.12` |
| VTK `bad X server connection` warnings | headless machine | harmless if the PNG is written; else `xvfb-run -a uv run ...` |

## Silent failures (no error, wrong geometry)

| Symptom | Cause | Fix |
|---|---|---|
| Cut/pocket had no effect | `cutBlind(+d)` on a face workplane cuts outward into air | negative distance; or `extrude(-d, combine="cut")` |
| Text didn't appear | `text(..., +d)` with default `combine="cut"` | `combine="a"` to emboss; negative distance to engrave |
| `shell()` did nothing | thickness too big for the part | smaller thickness; verify volume dropped |
| Features in the wrong place on a side face | workplane origin is the projected global origin; local x axis isn't global X | `centerOption="CenterOfBoundBox"` or `origin=`; render front/right views |
| Feature mirrored / on the opposite side | `XZ` plane normal is −Y; extrude direction follows the workplane normal | check bbox; flip sign or use `invert=True` |
| Two solids instead of one | features don't touch (gap) or touch only at an edge/face (coplanar) | overlap by a small amount; check `len(wp.solids().vals())` |
| Box floating above/below origin | `box` is centred by default | `centered=(True, True, False)` |
| Hole too shallow / blind when it should be through | `hole(d, depth)` measures from the workplane, which may not be the face you think | `hole(d)` (through all) or check the workplane offset |
| Pattern count off by one | `rarray` counts vs spacing confusion; `polarArray(..., 360, n)` | `rarray(xSpacing, ySpacing, xCount, yCount)`; for full circles use `angle=360` and n items |
| Assembly part flipped | `Plane`/`Axis` constraint `param` is an angle (default 180); circular-edge axis sense depends on orientation | leave `param` default for mates; verify solved locations; prefer planar faces |
| Assembly part spun about an axis | `Plane` constraint leaves rotation about the normal free | add an `Axis` constraint between side faces or `FixedRotation` |
| Interference "found" between touching parts | intersection returned zero-thickness faces | count only `intersect(...).Solids()` volumes (inspect_model does) |
| STL looks faceted | `cq.exporters.export` default `tolerance=0.1` | `tolerance=0.01`, `angularTolerance=0.1` |

## Performance

- Booleans dominate run time. Build all tools into one Workplane/Compound and cut **once**; avoid `for ...: part = part.cut(...)`.
- Use many pending wires in one `cutThruAll()`/`extrude()` instead of separate ops.
- Pass `clean=False` to ops in tight loops; call `.clean()` once at the end.
- Fillets on hundreds of edges are slow: fillet in 2D (Sketch) before extruding when possible.
- Assemblies: reuse the same part object for repeated components.
- `cadquery.func.setThreads(n)` enables parallel booleans.

## Geometry validity

- `shape.isValid()` False → `shape.fix()` sometimes repairs; better to remove the cause (coplanar booleans, tiny edges, self-intersections).
- `cadquery.func.check(shape)` returns True/False like `isValid()`; isolate the bad feature by bisecting the chain.
- Exact coincidence is the #1 cause of bad booleans. Overlap tools by 0.01–0.1 mm, or extend cutters past the faces they cut.
