# SKILL.md mechanical documentation re-review: Pi

Date: 2026-11-15. Reviewer: pi-mechanical-dev, pane w1P:pE.

Subject: `skills/pcb-design/SKILL.md`, SHA-256 `1505b298f00c5cc9177e04f305e854dd463334869701d6caee956b940545afb0`. Diff against HEAD: 24 insertions, 0 deletions. Text-only review. I edited no file and ran no suite.

This re-review replaces the review of `e053bd64...`. Scope: the `## Mechanical fit` section, the Scope table row, and the Files entries.

**Decision: agree. No findings. All prior items are addressed.**

## 1. Prior findings addressed

| Item | State |
|---|---|
| D1 Files entry | Addressed. The entry now reads "`scripts/mechanical.py`: the mechanical fit commands. It uses `scripts/mechanical_fit.py`, the geometry library." |
| D2 "safe envelope" | Addressed. The text no longer makes a safety claim. It says "`fit` examines the proxy envelope." |
| D3 `readiness` | Addressed. The block lists `uv run scripts/pcb.py mechanical readiness DIR`. |
| D4 `DIR` generation | Addressed. The block lists `uv run templates/mech-fit-a/make_fixture.py --out DIR`, and the prose states that the generator makes the fixture in `DIR`. |
| D5 "check" as a verb | Addressed. The first sentence uses "examine". |
| Codex note | Addressed. The prose states "`check` validates only the fixture contract. `fit` examines the proxy envelope. Neither command proves detailed component fit or supplier approval." |

## 2. Verified

- The subject hash matches the requested value. The diff is 24 insertions and 0 deletions.
- Every referenced `references/*.md` name exists, including `references/mechanical-fit.md`.
- The commands match `scripts/pcb.py`:
  - `check DIR` maps to `mechanical.py check --fixture DIR`.
  - `readiness DIR`, `export DIR`, `fit DIR` and `release DIR` map to `--project DIR`.
  - The `--image` option exists, applies to `export` only, and the dispatch forwards it for `export` only.
- The fixture and proxy scope matches `references/mechanical-fit.md`: the fixture `mech-fit-a`, proxy components, a contract check and a proxy envelope, and no detailed-fit claim.
- The Scope row and the Files entries are consistent with the reference.
- The exit-code pointer to `references/mechanical-fit.md` is correct.

## 3. Limits

- This is a text-only review of one file. I ran no suite and no command.
