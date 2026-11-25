# B11 skill documentation review

Reviewer: codex-mechanical-dev. Date: 2026-11-15.

Reviewed `skills/pcb-design/SKILL.md` at SHA-256 `1505b298f00c5cc9177e04f305e854dd463334869701d6caee956b940545afb0`.

**Decision: agree.**

## Review

- The `references/mechanical-fit.md` link resolves.
- The command list matches the `pcb.py mechanical` actions: `check`, `readiness`, `export`, `fit` and `release`. Each action takes a positional path. The optional `--image` option applies to `export` only.
- The fixture generator command matches the reference. The text states that the other commands run on the generated fixture.
- The scope row limits support to `mech-fit-a` and states that it uses proxy components.
- The new section states that `check` validates the fixture contract. It states that `fit` examines the proxy envelope. It also states that neither command proves detailed component fit or supplier approval.
- The Files entries identify `mechanical.py` as the command module, `mechanical_fit.py` as its geometry library, and the fixture generator.
- The new wording uses `examine` for the action and does not imply detailed fit.

## Retained test inputs

I read `docs/reviews/mechanical/b11-integration-ignore-audit.md` and compared the two files with its listed hashes. Both match:

- `tests/fixtures/mech-fit-a/real-export/board.step`: `4c2f747d476c11239b86636dfc9cafd0bc63bed23cd4c35e77a6d3a3c2d3d965`.
- `tests/fixtures/mech-fit-a/real-export/outline.dxf`: `7f78d95024454e3e64793cc114c04e4c97c867e04bff04c0592230df1f066fcd`.

`tests/test_mechanical_fit.py` reads both paths in its real-export tests. I did not edit files or rerun suites.
