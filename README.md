# cad-skills

Agent skills for CAD work. Installable with the [`skills`](https://skills.sh) CLI into Claude Code, Codex, Cursor, OpenCode, and [many more agents](https://github.com/vercel-labs/skills/blob/main/docs/agents.md).

## Skills

| Skill | What it gives your agent |
|---|---|
| [`cadquery`](skills/cadquery/SKILL.md) | Build parametric 3D CAD models in Python with [CadQuery](https://cadquery.readthedocs.io/): parts, sketches, assemblies, STEP/STL/3MF/DXF/SVG/glTF export, plus tools to inspect, measure, and render models so the agent can verify its own work. Uses `uv` for all Python. |

## Install

```bash
# this project (choose agents interactively)
npx skills add kerryhatcher/cad-skills

# one skill, one agent, globally
npx skills add kerryhatcher/cad-skills --skill cadquery -a claude-code -g

# see what's in the repo
npx skills add kerryhatcher/cad-skills --list
```

Requirements on the machine running the agent: [uv](https://docs.astral.sh/uv/) (CadQuery is fetched on demand — no manual install) and Node.js ≥ 22.20 for the `skills` CLI.

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

## Development

Every ```` ```python ```` block in the skill's Markdown is executed against the current CadQuery release:

```bash
uv run tests/test_snippets.py          # all blocks
uv run tests/test_snippets.py -k recipes -v
```

Mark fragments that can't run standalone with `# notest` on the first line. CI runs the same check on every push (`.github/workflows/test.yml`).

## License

MIT
