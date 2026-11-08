---
name: cadquery
description: Use when creating, modifying, debugging, or exporting parametric 3D CAD models in Python with CadQuery — mechanical parts, enclosures, brackets, 3D-printable or CNC parts, multi-part assemblies, 2D sketches/profiles, or STEP/STL/3MF/DXF/SVG/glTF files. Also use when the user mentions CadQuery, code-CAD, OCCT/OpenCascade, BREP solids, or asks to "model", "design", or "CAD" a physical object in code.
license: MIT
metadata:
  author: Kerry Hatcher
  version: "1.0.0"
  cadquery-version: "2.8"
---

# CadQuery Parametric CAD

## Overview

CadQuery is a Python library (on the OpenCascade kernel) for building exact BREP solids from code. **The script is the model**: named parameters at the top drive every dimension, so changing a number regenerates a valid part.

**Core principle: never trust geometry you have not measured and looked at.** Many CadQuery mistakes fail *silently* (a cut into empty air, a `shell()` that does nothing, a hole on the wrong face). After every build, check validity + bounding box + volume, and render a PNG and look at it.

## Language: Simplified Technical English

Write in ASD-STE100 Simplified Technical English (STE) when you use or change this skill. This applies to documentation, code comments, docstrings, CLI help text, error messages, commit messages and all messages to the user.

- Use approved STE words with one meaning each. Technical names and technical verbs are permitted.
- Use the active voice. Use the imperative for instructions. Use simple present, simple past or simple future.
- Write one topic in each sentence. Maximum 20 words in a procedure step, 25 words in a description.
- Do not use phrasal verbs, idioms, or noun clusters of more than three words.
- Write a warning or caution as a command before the step, then give the reason.
- Do not change code, commands, file names, setting keys or quoted output. Copy them exactly.

The full rules and examples are in `AGENTS.md` at the root of the cad-skills repository.

## Environment (uv)

Always use `uv`; never `pip install` into a system Python.

| Situation | Command |
|---|---|
| One-off model script | Put a PEP 723 header in the script (see `templates/part.py`), then `uv run model.py` |
| Run any script ad hoc | `uv run --with cadquery python model.py` |
| Project with dependencies | `uv init --python 3.12 && uv add cadquery` then `uv run model.py` |
| Interactive check | `uv run --with cadquery python -c "import cadquery as cq; print(cq.__version__)"` |
| Wheels fail to resolve | Pin Python: `uv run -p 3.12 ...` (OCP wheels can lag new Python releases) |

The bundled scripts carry their own PEP 723 headers, so `uv run <skill-dir>/scripts/<name>.py` just works. `<skill-dir>` = the directory containing this SKILL.md.

## Workflow

1. **Pin down the spec** before coding: units (default mm), overall envelope, key functional dimensions, fits/clearances, mating parts, manufacturing method (FDM print, CNC, laser). Ask only if a missing value changes the design; otherwise choose a sensible default and state it.
2. **Start from a template**: copy `templates/part.py` (single part) or `templates/assembly.py` (multi-part). Keep parameters as top-level literal assignments; add `assert` checks for impossible combinations.
3. **Build in small steps.** Add one feature, then verify:
   ```bash
   uv run <skill-dir>/scripts/inspect_model.py model.py --png out/preview.png
   ```
   It reports validity, solid count, bbox, volume, centre of mass; exits non-zero on failure. Then **Read the PNG** to look at it. Use `--views` for iso/front/top/right, `--set name=value` to test other parameter values, `--interference` for assemblies.
4. **Check the numbers against the spec**: bbox equals the intended envelope? Volume dropped after a cut (if not, the cut missed)? Exactly 1 solid for a single part?
5. **Stress parameters**: rebuild at min/max plausible values with `--set` to prove the model is really parametric.
6. **Export**: `-o out/part.step` (CAD exchange, exact) and `-o out/part.stl` / `.3mf` (printing). Assemblies: `.step` keeps names/colours, `.glb` for viewing.
7. **Going to print it?** Hand off to the companion skills if installed: `print-prep` (orientation, printability), `structural-analysis` (will it hold the load? FEA on this same `.py`), `prusaslicer` (G-code for a Prusa MK4/MK4S).

Unsure of a method's arguments? Don't guess — query the installed version:
`uv run <skill-dir>/scripts/cq_api.py Workplane.cboreHole` or `--search chamfer`.

## Mental model (read once)

- **`Workplane` is a stack, not a part.** Every call returns a *new* Workplane holding a list of objects (faces, edges, points, wires, solids) plus a link to its parent. 2D calls (`rect`, `circle`, `polyline().close()`) create **pending wires**; 3D calls (`extrude`, `revolve`, `loft`, `sweep`, `cutBlind`, `cutThruAll`) consume them; `hole()`/`cboreHole()` instead use the *points* on the stack.
- **Context solid**: 3D ops automatically fuse into (or cut from) the first solid up the chain. Use `combine=False` for a separate body, `combine="cut"` to subtract.
- **Operations repeat over the stack**: `.rarray(...)`/`.pushPoints(...)`/`.vertices()` put N points on the stack; the next `circle()`/`hole()` happens at each of them.
- **Workplane from a face**: `.faces(">Z").workplane()` → plane on that face, normal pointing *out* of the solid. Its origin is the **current origin (initially global 0,0,0) projected onto the face** (default `centerOption="ProjectedOrigin"`), NOT the face centre. Use `centerOption="CenterOfBoundBox"` or `origin=(x, y, z)` when you need otherwise.
- **Directions follow the workplane normal**: `extrude(d>0)` grows outward; `cutBlind(-d)` cuts *into* a face-based workplane — `cutBlind(+d)` there silently cuts air.
- **Named planes** (normal): `"XY"` +Z, `"YZ"` +X, `"ZX"` +Y, `"XZ"` **−Y**, `"front"` +Z, `"top"` +Y, `"right"` +X. When unsure, build and check the bbox.
- **Argument order traps**: `cylinder(height, radius)` (height first); `polarArray(radius, startAngle, angle, count)`; `revolve(angle, axisStart, axisEnd)` with the axis in *workplane-local* coordinates.
- **`box`, `rect`, `cylinder`, `sphere` are centred by default.** Use `centered=(True, True, False)` to sit a box on the XY plane.
- **Selectors** pick geometry by direction/position/type: `faces(">Z")` top face, `edges("|Z")` vertical edges, `faces("<X")`, `edges("%CIRCLE")`, combined with `and`/`or`/`not`. Full table: `references/selectors.md`.
- **Exit the chain** with `.val()` (first object) / `.vals()` → `cq.Shape` objects for measuring (`.Volume()`, `.BoundingBox()`, `.isValid()`).

## Quick reference

| Goal | Code |
|---|---|
| Block sitting on XY | `cq.Workplane("XY").box(L, W, H, centered=(True, True, False))` |
| Round vertical corners | `.edges("\|Z").fillet(r)` |
| Feature on top face | `.faces(">Z").workplane()` |
| Through hole(s) at points | `.pushPoints([(x, y), ...]).hole(d)` |
| Hole grid / circle | `.rarray(px, py, nx, ny).hole(d)` / `.polarArray(R, 0, 360, n).hole(d)` |
| Counterbore / countersink | `.cboreHole(d, cb_d, cb_depth)` / `.cskHole(d, csk_d, 82)` |
| Pocket (blind cut) | `.rect(a, b).cutBlind(-depth)` |
| Cut all the way through | `.rect(a, b).cutThruAll()` |
| Boss | `.circle(r).extrude(h)` |
| Hollow out, open top | `.faces(">Z").shell(-wall)` |
| Profile → solid | `.polyline(pts).close().extrude(h)` / `.revolve(360, (0,0,0), (0,1,0))` |
| Complex 2D profile | `cq.Sketch()...` then `.placeSketch(s).extrude(h)` (`references/sketch.md`) |
| Transition between shapes | `.rect(a, b).workplane(offset=h).circle(r).loft()` |
| Pipe along path | `.circle(r).sweep(path_wp)` |
| Mirror half-model | `.mirror("YZ")` (union=True to fuse) |
| Booleans | `a.union(b)`, `a.cut(b)`, `a.intersect(b)` or `a + b`, `a - b`, `a & b` |
| Separate body | `cq.Workplane().box(...)` then combine explicitly |
| Engrave / emboss text | `.text("TXT", size, -depth)` (default `combine="cut"`) / `.text("TXT", size, h, combine="a")` |
| Multi-part | `cq.Assembly().add(part, name=..., loc=cq.Location((x,y,z)), color=cq.Color("red"))` |
| Export | `cq.exporters.export(wp, "part.step")` / `assy.export("assy.step")` |

## Writing robust models

- **One parameter block, named in real units**; derive everything else. No magic numbers in the chain.
- **Order of features**: base solid → major cuts/bosses → holes → fillets/chamfers last (fillets add faces that confuse later selectors and break later booleans). Exception: apply an edge treatment early if that's the only time the selection is unambiguous — note why in a comment.
- **Avoid coplanar/tangent booleans**: when a cutter shares a face with the target, overshoot it by a small amount (e.g. extend 0.01–1 mm past) or use `cutThruAll()`.
- **Prefer construction over boolean soup**: a `Sketch` with modes or nested wires (`rect(...).rect(...)` → ring) is faster and more robust than many unions.
- **Tag** faces you'll need later: `.faces(">Z").tag("top")` then `.faces(tag="top")` / `.workplaneFromTagged("top")`; assemblies reference tags as `"part?tag"`.
- **Functions for repeated parts** (`def make_bracket(width, ...) -> cq.Workplane`), one function per physical part.
- **Fillet radius < adjacent wall/face size.** `StdFail_NotDone` almost always means a radius or chamfer is too large for some selected edge.

## Common mistakes

| Mistake | Symptom | Fix |
|---|---|---|
| `cutBlind(+d)` on a face workplane | Volume unchanged, no error | `cutBlind(-d)` (negative = into material) |
| Assuming `workplane()` origin is face centre | Features offset on off-centre faces | `workplane(centerOption="CenterOfBoundBox")` or explicit `origin=` |
| Fillet/chamfer too large | `StdFail_NotDone: BRep_API: command not done` | Smaller radius, fewer edges, fillet earlier/later, check edge lengths |
| `shell()` thicker than the part allows | Silently unchanged volume or invalid solid | Reduce thickness; check volume dropped |
| Extruding with nothing pending | `ValueError: No pending wires present` | Draw a closed 2D shape first; `.toPending()` after selecting wires |
| `hole`/`cutThruAll` with no solid | `Cannot find a solid on the stack or in the parent chain` | Create the base solid first in the same chain |
| Selector matched nothing | `Fillets requires that edges be selected`, or `.val()` returns a `Vector` | Print `len(wp.vals())` after selecting; fix the selector |
| `workplane()` on many/curved faces | `Selected faces must be co-planar` / `GeomAPI_ProjectPointOnSurf` | Select a single planar face (`faces(">Z")`), or build a `cq.Plane` explicitly |
| Keyword args to multimethods (`Sketch.arc(p1=...)`) | `DispatchError: 0 methods found` | Pass positional arguments |
| `"XZ"` assumed to face +Y | Features mirrored/inside out | XZ normal is −Y; check bbox |
| `Plane` assembly constraint `param=offset` | Part flipped/rotated | `param` is an *angle* for Plane/Axis; offsets via `Point` param or moving `loc` |
| `.text("A", 8, 1)` expecting raised text | Nothing happens (default mode is cut, +distance points away) | `combine="a"` to emboss, or negative distance to engrave |
| `.stp` extension | `Unknown extensions, specify export type explicitly` | Use `.step` or pass `"STEP"` |
| Only checking `isValid()` | Valid but wrong part | Also check bbox, volume, solid count, and look at the PNG |

More symptoms and fixes: `references/troubleshooting.md`.

## Reference files (load as needed)

| File | When |
|---|---|
| `references/workplane.md` | Fluent API: workplanes, 2D drawing, 3D ops, patterns, stack/tags |
| `references/selectors.md` | Selecting faces/edges/vertices; string syntax, Nth, combinations, custom |
| `references/sketch.md` | `cq.Sketch`: face/edge/constraint-based 2D profiles, modes, placing |
| `references/assemblies.md` | Multi-part models, `Location`, constraints, colours, export |
| `references/free-func.md` | `cadquery.func` free-function API, `Shape` methods, `Vector`/`Plane`/`Location` |
| `references/import-export.md` | STEP/STL/3MF/DXF/SVG/glTF, units, mesh tolerance, imports |
| `references/recipes.md` | Verified worked examples (enclosure, revolve, sweep, loft, threads, text, gears, patterns) |
| `references/design-guidelines.md` | Clearances and rules for 3D printing, CNC, laser cutting |
| `references/troubleshooting.md` | Error messages → causes → fixes; debugging techniques |

## Bundled tools

- `scripts/inspect_model.py` — build a script, report geometry, export (`-o`), render PNGs (`--png`, `--views`), override params (`--set`), assembly interference (`--interference`), JSON output (`--json`). Works headless; falls back to SVG if no GL is available (or run under `xvfb-run -a`).
- `scripts/cq_api.py` — signatures/docstrings of the *installed* CadQuery (`Workplane.hole`, `func.sweep`, `--search loft`).
- `templates/part.py`, `templates/assembly.py` — runnable, parametric, PEP 723 starting points.

Docs: https://cadquery.readthedocs.io/en/latest/ (tracks the dev branch; prefer `cq_api.py` for the installed version).
