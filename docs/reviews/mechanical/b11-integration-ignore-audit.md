# B11 integration: git ignore audit and additive file list

Date: 2026-11-15 UTC. Author: claude-mechanical-dev. Basis: the lead report of 2026-11-15 03:22:00 UTC (two missing geometry inputs).

## Cause of the omission

The root `.gitignore` ignores two file types that the fixture uses:

- `*.step` (line 223, under "CAD outputs generated while testing")
- `*.dxf` (line 238)

Git does not list these files as new files. A copy that uses the git file list therefore omits them. Both files are retained test inputs. They are not generated test output.

## Additive list

The file `docs/reviews/mechanical/b11-integration-additive-list.sha256` lists the two omitted consumed inputs. It was checked with `sha256sum -c`. The path source is `docs/reviews/mechanical/b11-integration-additive-paths.txt`.

| Path | SHA-256 | Read by |
|---|---|---|
| `tests/fixtures/mech-fit-a/real-export/board.step` | `4c2f747d476c11239b86636dfc9cafd0bc63bed23cd4c35e77a6d3a3c2d3d965` | `tests/test_mechanical_fit.py` (real-export STEP test) |
| `tests/fixtures/mech-fit-a/real-export/outline.dxf` | `7f78d95024454e3e64793cc114c04e4c97c867e04bff04c0592230df1f066fcd` | `tests/test_mechanical_fit.py` (real-export DXF test) |

The 22-file list `docs/reviews/mechanical/b11-integration-file-list.sha256` is preserved and unchanged.

## Consumed-input audit

I traced every fixture read in `tests/test_mechanical.py`, `tests/test_mechanical_fit.py`, `skills/pcb-design/scripts/mechanical.py`, `mechanical_fit.py` and `templates/mech-fit-a/make_fixture.py`.

- Test inputs under `tests/fixtures/mech-fit-a/`: `board-interface.json`, `component-evidence.json`, `fixture-source.json`, `real-export/board-PTH.drl`, `real-export/board-NPTH.drl` are in the 22-file list. `real-export/board.step` and `real-export/outline.dxf` are in the additive list.
- Template inputs under `skills/pcb-design/templates/mech-fit-a/`: `fixture-source.json`, `component-evidence.json`, `export-settings.json`, `make_fixture.py` are in the 22-file list.
- `make_fixture.py` writes `board.kicad_pcb`, `board-interface.json`, and `board.yaml` into its output folder. These are generated, not consumed. Their absence from the lists is correct.
- `mechanical.py` imports the accepted helpers `project_io.py` and `validate.py`. These helpers are copies in `skills/pcb-design/scripts/` and are not part of B11. Their presence is a separate skill-package question and the lead should confirm it.
- No consumed file lies outside the 22 files and the two additive files.

## Ignored files that are not consumed

These files are ignored by git. The suites do not read them. They are retained evidence and are not in the accepted manifest, although the handoff record says the manifest covers `b11-residual-evidence/*`.

| Path | SHA-256 |
|---|---|
| `docs/reviews/mechanical/b11-residual-evidence/positive/board.step` | `5109a50209eaebb4e28a82881c3be75c5ffd90f135685c111e7f9d6b1cc2c6a2` |
| `docs/reviews/mechanical/b11-residual-evidence/positive/fit-assembly.step` | `8d9ed46a10ce952a871f8c311617356838bdbea134b04b25e375fcbdd7db811b` |
| `docs/reviews/mechanical/b11-residual-evidence/positive/outline.dxf` | `7f78d95024454e3e64793cc114c04e4c97c867e04bff04c0592230df1f066fcd` |

The `board.step` in the evidence folder and the `board.step` in the test fixtures are different files. Both are retained. The `outline.dxf` bytes are the same in both places.

The `docs/reviews/mechanical/b11-repair-evidence/` folder also holds ignored `.step` and `.dxf` files. It is historical and is not changed.

## Other ignored items

- `__pycache__/` directories under `skills/pcb-design/`, `skills/pcb-design/templates/mech-fit-a/` and `tests/`. These are generated caches and are not inputs.

## Recommendation (decision for the lead)

I did not change `.gitignore`. It is not in the accepted list. Pick one:

1. Add the two fixture paths with `git add -f` at integration.
2. Add narrow negations to `.gitignore`, for example `!tests/fixtures/mech-fit-a/**/*.step` and `!tests/fixtures/mech-fit-a/**/*.dxf`.

Either choice keeps the broad `*.step` and `*.dxf` rules for other generated output.
