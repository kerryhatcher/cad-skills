# cad-skills

Agent skills for CAD work. Installable with the [`skills`](https://skills.sh) CLI into Claude Code, Codex, Cursor, OpenCode, and [many more agents](https://github.com/vercel-labs/skills/blob/main/docs/agents.md).

## Skills

| Skill | What it gives your agent |
|---|---|
| [`cadquery`](skills/cadquery/SKILL.md) | Build parametric 3D CAD models in Python with [CadQuery](https://cadquery.readthedocs.io/): parts, sketches, assemblies, STEP/STL/3MF/DXF/SVG/glTF export, plus tools to inspect, measure, and render models so the agent can verify its own work. Uses `uv` for all Python. |
| [`structural-analysis`](skills/structural-analysis/SKILL.md) | Check whether a part will survive its job: linear-static FEA (gmsh + scikit-fem, quadratic tets) of CadQuery/STEP models, safety factors against **printed** Prusament/Jessie material data, and a layer-adhesion check for the print orientation. Renders boundary conditions and stress PNGs, and exports VTU for ParaView. |
| [`print-prep`](skills/print-prep/SKILL.md) | Get a model ready for FDM: mesh health, build-volume fit, ranked print orientations (supports, bed contact, tip-over, load across layers), wall-thickness check, re-oriented 3MF/STL export, design-for-FDM rules for the Prusa MK4. |
| [`prusaslicer`](skills/prusaslicer/SKILL.md) | Slice headless with PrusaSlicer using Prusa's official MK4/MK4S profiles (incl. Prusament and Jessie filaments), with strength overrides. Verifies the G-code really targets the right printer, nozzle and temperatures, and reports time, filament and slicer warnings. Reads `.bgcode`. |

The four skills chain together: **model** (`cadquery`) → **orient & check** (`print-prep`) → **prove strength** (`structural-analysis`, same build direction) → **slice** (`prusaslicer`).

## Install

```bash
# this project (choose agents interactively)
npx skills add kerryhatcher/cad-skills

# one skill, one agent, globally
npx skills add kerryhatcher/cad-skills --skill cadquery -a claude-code -g

# see what's in the repo
npx skills add kerryhatcher/cad-skills --list
```

Requirements on the machine running the agent: [uv](https://docs.astral.sh/uv/) (CadQuery is fetched on demand — no manual install) and Node.js ≥ 22.20 for the `skills` CLI. The `prusaslicer` skill also needs [PrusaSlicer](https://www.prusa3d.com/page/prusaslicer_424/) ≥ 2.8 (Linux: `flatpak install flathub com.prusa3d.PrusaSlicer`).

## What's in `cadquery`

```
skills/cadquery/
├── SKILL.md                    # workflow, mental model, quick reference, common mistakes
├── references/                 # loaded on demand
│   ├── workplane.md            # fluent API: workplanes, 2D, 3D ops, patterns, tags
│   ├── selectors.md            # face/edge/vertex selection
│   ├── sketch.md               # cq.Sketch: face/edge/constraint-based profiles
│   ├── assemblies.md           # Assembly, Location, constraints, colours
│   ├── free-func.md            # cadquery.func, Shape API, Vector/Plane/Location
│   ├── import-export.md        # formats, units, mesh tolerance, imports
│   ├── recipes.md              # 12 verified worked examples
│   ├── design-guidelines.md    # FDM, CNC, laser, sheet-metal rules of thumb
│   └── troubleshooting.md      # error message → cause → fix
├── scripts/
│   ├── inspect_model.py        # build + validate + measure + export + render PNG views
│   └── cq_api.py               # signatures/docstrings of the installed CadQuery
└── templates/
    ├── part.py                 # parametric single-part starter (PEP 723)
    └── assembly.py             # parametric assembly starter (PEP 723)
```

The scripts carry [PEP 723](https://peps.python.org/pep-0723/) headers, so they run anywhere with `uv run`:

```bash
uv run skills/cadquery/scripts/inspect_model.py my_part.py --png out/preview.png --views -o out/my_part.step
uv run skills/cadquery/scripts/cq_api.py Workplane.cboreHole
```

`inspect_model.py` reports validity, solid count, bounding box, volume and centre of mass; overrides top-level parameters (`--set width=50`); checks assembly interference (`--interference`); exports any supported format (`-o`); and renders off-screen PNGs (iso/front/top/right) that a multimodal agent can look at.

## Printing workflow example

```bash
# 1. orientation + printability (prints the build direction to use in FEA)
uv run skills/print-prep/scripts/printability.py bracket.py --load-axis z --png out/orient.png -o out/bracket.3mf
# 2. will it hold 100 N with the chosen orientation?
uv run skills/structural-analysis/scripts/fea.py bracket.py --material jessie-petg \
    --fix "face:7" --force "face:5=0,0,-100" --build-dir y --sf-target 3 --png out/fea.png
# 3. slice for an MK4 with strength settings
uv run skills/prusaslicer/scripts/slice.py slice out/bracket.3mf --printer MK4 \
    --filament "Jessie PETG" --perimeters 5 --infill 40% -o out/bracket.bgcode
```

## Development

Every ```` ```python ```` block in the skill's Markdown is executed against the current CadQuery release:

```bash
uv run tests/test_snippets.py          # all blocks
uv run tests/test_snippets.py -k recipes -v
```

Mark fragments that can't run standalone with `# notest` on the first line.

The FEA, printability and slicing tools have regression tests (FEA checked against beam theory; profile resolution checked against Prusa's bundle; a real slice if PrusaSlicer is installed):

```bash
uv run tests/test_print_tools.py
```

CI runs both on every push (`.github/workflows/test.yml`).

## License

MIT
