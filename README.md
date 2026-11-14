# cad-skills

Agent skills for CAD work. You can install them with the [`skills`](https://skills.sh) CLI into Claude Code, Codex, Cursor, OpenCode and [many other agents](https://github.com/vercel-labs/skills/blob/main/docs/agents.md).

## Skills

| Skill | Function |
|---|---|
| [`cadquery`](skills/cadquery/SKILL.md) | Make parametric 3D CAD models in Python with [CadQuery](https://cadquery.readthedocs.io/). It includes parts, sketches, assemblies and export to STEP, STL, 3MF, DXF, SVG and glTF. Its tools examine, measure and render models. Thus the agent can make sure that its work is correct. All Python runs with `uv`. |
| [`structural-analysis`](skills/structural-analysis/SKILL.md) | Find if a part is sufficiently strong for its task. It does a linear static FEA (gmsh and scikit-fem, quadratic tetrahedra) of CadQuery or STEP models. It calculates safety factors with data for **printed** Prusament and Jessie materials. It also examines the layer adhesion for the print orientation. It renders the boundary conditions and the stress to PNG files, and exports VTU files for ParaView. |
| [`print-prep`](skills/print-prep/SKILL.md) | Prepare a model for FDM printing. It examines the mesh. It makes sure that the part is not too large for the build volume. It compares print orientations and puts them in sequence from best to worst. It compares the supports, the area on the bed, the risk that the part falls, and the load across the layers. It also examines the wall thickness and exports the turned model as 3MF or STL. It includes design rules for FDM on the Prusa MK4. |
| [`prusaslicer`](skills/prusaslicer/SKILL.md) | Slice with PrusaSlicer, with no GUI. It uses the Prusa profiles for the MK4 and MK4S, which include Prusament and Jessie filaments. You can change the settings that give strength. It makes sure that the G-code is for the correct printer, nozzle and temperatures. It shows the time, the filament and the slicer warnings. It can read `.bgcode` files. |

Use the four skills in this sequence:

1. **Model** the part (`cadquery`).
2. **Turn and examine** the part for printing (`print-prep`).
3. **Calculate the strength** with the same build direction (`structural-analysis`).
4. **Slice** the part (`prusaslicer`).

## How to install the skills

```bash
# this project (select the agents in a menu)
npx skills add kerryhatcher/cad-skills

# one skill, one agent, for all projects
npx skills add kerryhatcher/cad-skills --skill cadquery -a claude-code -g

# show the contents of the repository
npx skills add kerryhatcher/cad-skills --list
```

The computer that runs the agent must have:

- [uv](https://docs.astral.sh/uv/). It downloads CadQuery when necessary. It is not necessary to install CadQuery.
- Node.js (minimum version 22.20), for the `skills` CLI.
- [PrusaSlicer](https://www.prusa3d.com/page/prusaslicer_424/) (minimum version 2.8), for the `prusaslicer` skill only. On Linux: `flatpak install flathub com.prusa3d.PrusaSlicer`.

## Contents of `cadquery`

```
skills/cadquery/
├── SKILL.md                    # procedure, mental model, quick reference, frequent mistakes
├── references/                 # the agent reads these when necessary
│   ├── workplane.md            # fluent API: workplanes, 2D, 3D operations, patterns, tags
│   ├── selectors.md            # selection of faces, edges and vertices
│   ├── sketch.md               # cq.Sketch: profiles from faces, edges or constraints
│   ├── assemblies.md           # Assembly, Location, constraints, colors
│   ├── free-func.md            # cadquery.func, Shape API, Vector/Plane/Location
│   ├── import-export.md        # formats, units, mesh tolerance, imports
│   ├── recipes.md              # 12 tested examples
│   ├── design-guidelines.md    # general rules for FDM, CNC, laser and sheet metal
│   └── troubleshooting.md      # error message → cause → repair
├── scripts/
│   ├── inspect_model.py        # build, validate, measure, export and render PNG views
│   └── cq_api.py               # signatures and docstrings of the installed CadQuery
└── templates/
    ├── part.py                 # start file for a parametric part (PEP 723)
    └── assembly.py             # start file for a parametric assembly (PEP 723)
```

The scripts have [PEP 723](https://peps.python.org/pep-0723/) headers. Thus they run on all computers with `uv run`:

```bash
uv run skills/cadquery/scripts/inspect_model.py my_part.py --png out/preview.png --views -o out/my_part.step
uv run skills/cadquery/scripts/cq_api.py Workplane.cboreHole
```

`inspect_model.py` does these tasks:

- It shows if the model is correct. It also shows the number of solids, the bounding box, the volume and the center of mass.
- It changes top-level parameters (`--set width=50`).
- It finds interference in an assembly (`--interference`).
- It exports to all supported formats (`-o`).
- It renders PNG views (iso, front, top, right) with no screen. An agent that can read images can examine these views.

## Example: from a model to a print

```bash
# 1. orientation and printability (shows the build direction for the FEA)
uv run skills/print-prep/scripts/printability.py bracket.py --load-axis z --png out/orient.png -o out/bracket.3mf
# 2. can the part hold 100 N in this orientation?
uv run skills/structural-analysis/scripts/fea.py bracket.py --material jessie-petg \
    --fix "face:7" --force "face:5=0,0,-100" --build-dir y --sf-target 3 --png out/fea.png
# 3. slice for an MK4 with settings for strength
uv run skills/prusaslicer/scripts/slice.py slice out/bracket.3mf --printer MK4 \
    --filament "Jessie PETG" --perimeters 5 --infill 40% -o out/bracket.bgcode
```

## Tests

The test script runs each ```` ```python ```` code block in the Markdown files of the skills. It uses the CadQuery version that `uv` installs:

```bash
uv run tests/test_snippets.py          # all blocks
uv run tests/test_snippets.py -k recipes -v
```

If a code block cannot run without other code, put `# notest` on its first line.

The FEA, printability and slicer tools have regression tests:

- The FEA results agree with beam theory.
- The profile resolution agrees with the Prusa profile bundle.
- If the computer has PrusaSlicer, a test slices a model.

```bash
uv run tests/test_print_tools.py
```

CI runs the two test scripts each time that you push commits (`.github/workflows/test.yml`).

### Language

Write all documentation, code comments, help text, commit messages and agent messages in ASD-STE100 Simplified Technical English (STE). `AGENTS.md` gives the rules and examples. `CLAUDE.md` imports `AGENTS.md` for Claude Code.

## License

MIT
