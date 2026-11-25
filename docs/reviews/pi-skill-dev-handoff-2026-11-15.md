# pi-skill-dev handoff (2026-11-15)

Context state: high. The session file is about 3.5 MB and 600 messages. This handoff records
the state for a fresh session.

## Role and team

- I am `pi-skill-dev`, a reviewer only. Pane `w1P:p6`. I do not edit product code.
- Lead: `skill-dev-lead`, pane `w1P:p3`.
- Author: `claude-skill-dev`, pane `w1P:p4`.
- Reviewer: `codex-skill-dev`, pane `w1P:p5`.
- Herdr: use `/proc/482044/exe` (the installed binary is incompatible). The prefix rule is
  `[YYYY-MM-DD - HH:MM:SS UTC] To: NAME; From: pi-skill-dev - `.
- Reports go under `docs/reviews/`. Use STE. Use `uv` for host Python. No commits, no broad
  suites, no product edits.

## Accepted

- B1-B6 and the scoped B7 geometry work. Do not repeat them.
- Publication correction: `b7-residual-publication-repair-claude.md` `08ec5765…`, workflow
  `b81466ee…`, fab `5be6e136…`, test `a973b5be…`. Later the alias freeze: record
  `31f8480f…`, `fetch_sources.py` `35e21d37…`, `test_source_retrieval.py` `1d61a5a2…`.
- Setup documentation freeze 2: `oshpark-setup-documentation-freeze-2-claude.md` `9caa8271…`.
- Rows 23 and 24: `b7-internal-copper-acceptance-root.md`. Four-layer fixtures, independent
  gaps, focused cases pass.
- The normalized manifest `skills/pcb-fab-package/sources.yaml` `fd415dc5…`.

## Open at handoff

- Row 28: outline and cutout concave corner radii. The corner rule is derived tool
  compatibility from the published cutter diameters (0.068 in outline, 0.040 in cutout),
  stored under process facts. Not a `limits` supplier minimum. No shared schema change.
- Row 29: implement the supplier via construction check. The key is
  `service.via_construction_prohibited` in the profile extension, the source evidence and the
  mandatory supplier row. Blind or buried spans give exit 1 with the refused precondition
  report. Missing or unconfirmed declarations are pending. A declared
  `filled_plated_via_in_pad` fails. A board without vias is not applicable with the zero
  count. An unknown declaration is exit 2. The B6 worker stays unchanged.
- The dimension correction `b7-outline-dimension-correction-root.md`: the B7 inventory adds
  the Edge.Cuts stroke width. The correction zeroes the Edge.Cuts stroke widths in memory
  before the bounding-box call, includes board and footprint drawings, does not save the
  board, and keeps the B6 worker and the hole measurements unchanged.
- The completion gap list: `current-state-inventory-review-pi.md`. Rows 3, 6, 7a/7b, 8, 13,
  13c, 16, 22, 23, 24, 25, 26, 28, 29, 31, 32, 36, 41, 44, 45 and standalone. Rows 23/24 are
  now accepted.

## Do not

- Rerun accepted suites or reopen accepted geometry and publication decisions.
- Inspect changing code unless asked.
- Edit product code. Court `docs/reviews/` only.

## My report files

- `current-state-inventory-review-pi.md`
- `source-retrieval-implementation-freeze-review-pi.md`
- `source-retrieval-alias-freeze-review-pi.md`
- `oshpark-setup-documentation-freeze-review-pi.md`
- `b7-internal-copper` (rows 23/24) is `b7-internal-copper-acceptance-root.md` (lead).
- `pi-skill-dev-handoff-2026-11-15.md` (this file).