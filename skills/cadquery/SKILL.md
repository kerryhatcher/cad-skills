---
name: cadquery
description: Use this skill to make, change, debug or export parametric 3D CAD models in Python with CadQuery. Examples are mechanical parts, enclosures, brackets, 3D-printed parts and CNC parts. Other examples are assemblies, 2D sketches and profiles, and STEP, STL, 3MF, DXF, SVG or glTF files. Also use this skill when the user writes about CadQuery, code-CAD, OCCT, OpenCascade or BREP solids. Use it when the user tells you to "model", "design" or "CAD" a physical object in code.
license: MIT
metadata:
  author: Kerry Hatcher
  version: "1.0.0"
  cadquery-version: "2.8"
---

# CadQuery parametric CAD

## Overview

CadQuery is a Python library that makes accurate BREP solids from code. It uses the OpenCascade kernel. **The script is the model.** Named parameters at the top of the script control all dimensions. When you change a number, the script makes a new, correct part.

**Primary rule: do not use geometry that you did not measure and examine.** Many CadQuery mistakes cause no error message. Examples: a cut that removes no material, a `shell()` that does nothing, a hole on the incorrect face. After each build, examine the validity, the bounding box and the volume. Then render a PNG and examine it.

## Language: Simplified Technical English

Write in ASD-STE100 Simplified Technical English (STE) when you use or change this skill. This rule applies to documentation, code comments, docstrings, CLI help text, error messages, commit messages and all messages to the user.

- Use approved STE words with one meaning each. You can use technical nouns and technical verbs.
- Use the active voice. Use the imperative for instructions. Use the simple present, simple past or simple future tense.
- Write one topic in each sentence. Use a maximum of 20 words in a procedure step, and 25 words in a description.
- Do not use phrasal verbs, idioms, semicolons, or noun clusters of more than three words.
- Write a WARNING or CAUTION as a command before the step. Then give the risk.
- Do not change code, commands, file names, configuration keys or quoted output. Copy them without changes.

`AGENTS.md` at the root of the cad-skills repository gives all the rules and examples.

## Environment (uv)

Always use `uv`. Do not use `pip install` into a system Python.

| Condition | Command |
|---|---|
| Model script for one task | Put a PEP 723 header in the script (refer to `templates/part.py`). Then run `uv run model.py` |
| Run a script with no header | `uv run --with cadquery python model.py` |
| Project with dependencies | `uv init --python 3.12 && uv add cadquery`, then `uv run model.py` |
| Fast test | `uv run --with cadquery python -c "import cadquery as cq; print(cq.__version__)"` |
| `uv` cannot find wheels | Set the Python version: `uv run -p 3.12 ...` (OCP wheels for a new Python release are available only after some time) |

Each script of this skill has a PEP 723 header. Thus `uv run <skill-dir>/scripts/<name>.py` operates with no other steps. `<skill-dir>` is the directory that contains this SKILL.md.

## Procedure

1. **Get the specification** before you write code:
   - Units (default mm), the overall envelope and the important dimensions.
   - Fits, clearances and mating parts.
   - The manufacturing method (FDM print, CNC, laser).

   If a missing value changes the design, get the value from the user. If not, select an applicable default value and tell the user.
2. **Start from a template.** Copy `templates/part.py` (one part) or `templates/assembly.py` (many parts). Keep the parameters as top-level literal assignments. Add `assert` statements for combinations that are not possible.
3. **Build the model in small steps.** Add one feature, then examine the result:
   ```bash
   uv run <skill-dir>/scripts/inspect_model.py model.py --png out/preview.png
   ```
   The tool shows the validity, the number of solids, the bbox, the volume and the center of mass. If the build has an error, the exit status is not 0. Then **read the PNG** and examine the model. Use `--views` for iso, front, top and right views. Use `--set name=value` to test other parameter values. Use `--interference` for assemblies.
4. **Compare the numbers with the specification:**
   - Is the bbox equal to the necessary envelope?
   - Did the volume decrease after a cut? If not, the cut did not touch the part.
   - Is there only one solid for a single part?
5. **Test the parameters.** Build the model again with the minimum and maximum values (`--set`). This shows that the model is fully parametric.
6. **Export the model:**
   - `-o out/part.step` for other CAD programs (accurate geometry).
   - `-o out/part.stl` or `.3mf` for printing.
   - For assemblies, `.step` keeps the names and colors. Use `.glb` for viewing.
7. **If you will print the part,** use the related skills (if you have them):
   - `print-prep`: orientation and printability.
   - `structural-analysis`: FEA on the same `.py` file, to find if the part can hold the load.
   - `prusaslicer`: G-code for a Prusa MK4 or MK4S.

If you are not sure about the arguments of a method, do not use a value that you do not know. Query the installed version:
`uv run <skill-dir>/scripts/cq_api.py Workplane.cboreHole` or `--search chamfer`.

## Mental model (read this section one time)

- **A `Workplane` is a stack, not a part.** Each method gives a *new* Workplane. The Workplane holds a list of objects (faces, edges, points, wires, solids) and a connection to its parent.
- **2D calls make pending wires.** Examples: `rect`, `circle`, `polyline().close()`. 3D calls (`extrude`, `revolve`, `loft`, `sweep`, `cutBlind`, `cutThruAll`) use these wires. But `hole()` and `cboreHole()` use the *points* on the stack.
- **Context solid:** a 3D operation adds to (or cuts from) the first solid in the chain above it. Use `combine=False` for a different body. Use `combine="cut"` to remove material.
- **Operations occur at each item on the stack.** `.rarray(...)`, `.pushPoints(...)` and `.vertices()` put N points on the stack. The next `circle()` or `hole()` occurs at each of these points.
- **Workplane on a face:** `.faces(">Z").workplane()` gives a plane on that face. Its normal points *out* of the solid. Its origin is **the current origin projected onto the face**. The initial origin is the global point 0,0,0 (default `centerOption="ProjectedOrigin"`). The origin is NOT the center of the face. If you must have a different origin, use `centerOption="CenterOfBoundBox"` or `origin=(x, y, z)`.
- **Directions agree with the workplane normal.** `extrude(d>0)` adds material in the direction of the normal. On a workplane on a face, `cutBlind(-d)` cuts *into* the solid. `cutBlind(+d)` removes no material and gives no error.
- **Named planes** (normal direction): `"XY"` +Z, `"YZ"` +X, `"ZX"` +Y, `"XZ"` **−Y**, `"front"` +Z, `"top"` +Y, `"right"` +X. If you are not sure, build the model and examine the bbox.
- **The sequence of arguments can cause errors:**
  - `cylinder(height, radius)`: the height is first.
  - `polarArray(radius, startAngle, angle, count)`.
  - `revolve(angle, axisStart, axisEnd)`: the axis is in *workplane-local* coordinates.
- **By default, the center of a `box`, `rect`, `cylinder` or `sphere` is at the origin.** To put a box on the XY plane, use `centered=(True, True, False)`.
- **Selectors** select geometry by direction, position or type. Examples: `faces(">Z")` (top face), `edges("|Z")` (vertical edges), `faces("<X")`, `edges("%CIRCLE")`. You can use selectors together with `and`, `or` and `not`. Refer to `references/selectors.md` for the full table.
- **To get shapes from the chain,** use `.val()` (first object) or `.vals()`. These give `cq.Shape` objects that you can measure (`.Volume()`, `.BoundingBox()`, `.isValid()`).

## Reference table

| Task | Code |
|---|---|
| Block on the XY plane | `cq.Workplane("XY").box(L, W, H, centered=(True, True, False))` |
| Round the vertical corners | `.edges("\|Z").fillet(r)` |
| Feature on the top face | `.faces(">Z").workplane()` |
| Through holes at points | `.pushPoints([(x, y), ...]).hole(d)` |
| Holes in a grid or a circle | `.rarray(px, py, nx, ny).hole(d)` / `.polarArray(R, 0, 360, n).hole(d)` |
| Counterbore or countersink | `.cboreHole(d, cb_d, cb_depth)` / `.cskHole(d, csk_d, 82)` |
| Pocket (blind cut) | `.rect(a, b).cutBlind(-depth)` |
| Cut through all material | `.rect(a, b).cutThruAll()` |
| Boss | `.circle(r).extrude(h)` |
| Hollow part, open top | `.faces(">Z").shell(-wall)` |
| Profile to solid | `.polyline(pts).close().extrude(h)` / `.revolve(360, (0,0,0), (0,1,0))` |
| Complex 2D profile | `cq.Sketch()...`, then `.placeSketch(s).extrude(h)` (`references/sketch.md`) |
| Change from one shape to a different shape | `.rect(a, b).workplane(offset=h).circle(r).loft()` |
| Pipe along a path | `.circle(r).sweep(path_wp)` |
| Mirror a half model | `.mirror("YZ")` (`union=True` makes one solid from the two halves) |
| Booleans | `a.union(b)`, `a.cut(b)`, `a.intersect(b)` or `a + b`, `a - b`, `a & b` |
| Different body | `cq.Workplane().box(...)`, then use a boolean to add it |
| Engrave or emboss text | `.text("TXT", size, -depth)` (default `combine="cut"`) / `.text("TXT", size, h, combine="a")` |
| Many parts | `cq.Assembly().add(part, name=..., loc=cq.Location((x,y,z)), color=cq.Color("red"))` |
| Export | `cq.exporters.export(wp, "part.step")` / `assy.export("assy.step")` |

## How to write models that operate correctly

- **Use one parameter block, with names and units.** Calculate all other values from these parameters. Do not put numbers with no name in the chain.
- **Sequence of features:** first solid → large cuts and bosses → holes → fillets and chamfers. Fillets add faces. These faces can cause incorrect selections and boolean errors in subsequent steps. But if an edge selection is clear only at the start, add the fillet at that step. Write the cause in a comment.
- **Prevent booleans with coplanar or tangent faces.** A cutter can have a face on the same plane as a face of the target. Then make the cutter larger by 0.01 mm to 1 mm. As an alternative, use `cutThruAll()`.
- **Make shapes with construction, not with many booleans.** A `Sketch` with modes or nested wires is faster than many unions, and it causes less errors. Example: `rect(...).rect(...)` gives a ring.
- **Tag the faces that you will use again:** `.faces(">Z").tag("top")`, then `.faces(tag="top")` or `.workplaneFromTagged("top")`. Assemblies refer to tags as `"part?tag"`.
- **Use a function for each physical part** (`def make_bracket(width, ...) -> cq.Workplane`). This lets you make many parts of the same type.
- **The fillet radius must be smaller than the adjacent wall or face.** `StdFail_NotDone` almost always shows a radius or a chamfer that is too large. It is too large for one of the selected edges.

## Frequent errors

| Error | Symptom | Repair |
|---|---|---|
| `cutBlind(+d)` on a face workplane | The volume does not change. There is no error | `cutBlind(-d)` (a negative value cuts into the material) |
| You think that the `workplane()` origin is at the face center | Features move away from their position on faces that are not at the center | `workplane(centerOption="CenterOfBoundBox")` or an explicit `origin=` |
| Fillet or chamfer too large | `StdFail_NotDone: BRep_API: command not done` | Use a smaller radius or less edges. Add the fillet at a different step. Measure the edge lengths |
| `shell()` thicker than the part | The volume does not change, or the solid is not valid | Use a smaller thickness. Make sure that the volume decreased |
| `extrude` with no pending wire | `ValueError: No pending wires present` | First make a closed 2D shape. After you select wires, use `.toPending()` |
| `hole` or `cutThruAll` with no solid | `Cannot find a solid on the stack or in the parent chain` | First make the first solid in the same chain |
| The selector found no geometry | `Fillets requires that edges be selected`, or `.val()` gives a `Vector` | After the selection, print `len(wp.vals())`. Repair the selector |
| `workplane()` on many faces or on a curved face | `Selected faces must be co-planar` / `GeomAPI_ProjectPointOnSurf` | Select one planar face (`faces(">Z")`), or make a `cq.Plane` explicitly |
| Keyword arguments for multimethods (`Sketch.arc(p1=...)`) | `DispatchError: 0 methods found` | Use positional arguments |
| You think that `"XZ"` points to +Y | The features are on the opposite side, or they point in the opposite direction | The XZ normal is −Y. Examine the bbox |
| `Plane` assembly constraint with `param=offset` | The part turns or flips | For Plane and Axis, `param` is an *angle*. For an offset, use a `Point` constraint or move `loc` |
| `.text("A", 8, 1)` for raised text | No change occurs (the default mode is cut, and +distance points out of the solid) | Use `combine="a"` to emboss, or a negative distance to engrave |
| `.stp` extension | `Unknown extensions, specify export type explicitly` | Use `.step`, or give `"STEP"` |
| You examine only `isValid()` | The part is valid but not correct | Also examine the bbox, the volume and the number of solids. Then examine the PNG |

For more symptoms and repairs, refer to `references/troubleshooting.md`.

## Reference files (read when necessary)

| File | Contents |
|---|---|
| `references/workplane.md` | Fluent API: workplanes, 2D drawing, 3D operations, patterns, stack and tags |
| `references/selectors.md` | Selection of faces, edges and vertices: string syntax, Nth, combinations, custom selectors |
| `references/sketch.md` | `cq.Sketch`: 2D profiles from faces, edges or constraints, modes, placement |
| `references/assemblies.md` | Models with many parts, `Location`, constraints, colors, export |
| `references/free-func.md` | `cadquery.func` free-function API, `Shape` methods, `Vector`, `Plane`, `Location` |
| `references/import-export.md` | STEP, STL, 3MF, DXF, SVG, glTF, units, mesh tolerance, imports |
| `references/recipes.md` | Tested examples: enclosure, revolve, sweep, loft, threads, text, gears, patterns |
| `references/design-guidelines.md` | Clearances and rules for 3D printing, CNC and laser cutting |
| `references/troubleshooting.md` | Error messages → causes → repairs. Methods to find problems |

## Tools in this skill

- `scripts/inspect_model.py`: builds a script and shows the geometry data. It also exports (`-o`), renders PNG files (`--png`, `--views`), changes parameters (`--set`), finds interference in assemblies (`--interference`) and writes JSON (`--json`). It operates with no screen. If it cannot use OpenGL, it makes SVG files. As an alternative, run it with `xvfb-run -a`.
- `scripts/cq_api.py`: shows the signatures and docstrings of the *installed* CadQuery (`Workplane.hole`, `func.sweep`, `--search loft`).
- `templates/part.py`, `templates/assembly.py`: start files that you can run. They are parametric and have PEP 723 headers.

Documentation: https://cadquery.readthedocs.io/en/latest/. This documentation is for the development version. For the installed version, use `cq_api.py`.
