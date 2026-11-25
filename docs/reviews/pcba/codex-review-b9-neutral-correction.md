# Review of the corrected B9 neutral batch

Date: 2026-11-15 UTC.

Reviewed the frozen file list in `docs/reviews/pcba/b9-neutral-correction-claude.md`. I checked all 30 listed hashes. All matched. The author reports 35 focused tests passed. I did not rerun them. This review covers neutral mapping, variants, neutral rows, BOM groups, stock, and the 15 correction items. Sierra conversion and B10 publication stay outside scope.

## Before and after hashes

| File | Before | After |
|---|---|---|
| `docs/reviews/b9-b10-interface-claude.md` | `0be00806d483b138fa9155229b4a5977330f1775493debac2479ad82dc5049cb` | `36d7e1b0917417d6e537db57fd46a92d4b949303e1d13d5f40b93e0a29b1d361` |
| `skills/pcba-design/scripts/pcba.py` | `6f9b56a912bf699b07ff83d2e2893cc566b8954df22f45e3728bef9cd365c0c7` | `1e69b6f3bced2cb9b30556829a6ced51b6d8330a0a1c1353239e2033bc3471a4` |
| `tests/test_pcba_design.py` | `1efb62f0c00706ebeb9fa0dccbd20fed7c3fdfc18c58d4ac01f587cb6b625ca1` | `123592419d4cbe7a7ee3953a8e1ffb09bccc0e8cac6912c8326689efc905b454` |
| `skills/pcba-design/SKILL.md` | `da3d22eb0cd74078fbb35ae175126f3595e7e265b8d4802d53b1a6e3315ec91f` | `da3d22eb0cd74078fbb35ae175126f3595e7e265b8d4802d53b1a6e3315ec91f` |

## Findings

1. **The skill guide still calls float values exact.** In `skills/pcba-design/SKILL.md`, the board input rule says the positions and rotations are copied exactly. The interface now says `x_mm`, `y_mm`, and `source_rotation_deg` are derived finite numbers. `source_tokens` keeps the exact board-file text. Change the guide to describe these two forms correctly.
2. **The focused tests do not test lock refusal before capture.** The code takes the project lock in `main` before `build`. The frozen record maps this item to `test_input_changed_before_write_refused`, which tests freshness, not lock scope. Add a focused test that holds the lock before the command and confirms that the command refuses without reading or writing project data.

## Correction review

The code now confines resolved part paths under `components/`, reuses snapshots by resolved path, and records project-relative paths. It rejects output aliases by resolved path and hard-link identity. The CLI holds the project lock through capture, freshness checks, and the atomic write. It rehashes all inputs before the write.

The neutral rows keep raw coordinate tokens and finite derived numbers. The code names malformed and non-finite token findings. It records the implicit zero-angle case. The rows include datum, midpoint status, board quantity, alternate value, and zero per-board quantity for excluded references.

The BOM rows keep the hand-install reason and group by instruction and installation method. Stock checks reject conflicting stock or lifecycle records. Identical records share stock data. Demand counts each populated reference once.

## Integration note

The frozen record correctly assigns the missing `snippet_envs.json` route to the release workstream. The `test_snippet_routing` failure remains a pending integration item. It does not establish a neutral-step test failure.

## Decision

The code changes address the 15 authorized correction items. Do not accept the batch until the guide wording and lock-scope test are corrected. Alternates remain unsupported. This review does not accept alternate-part support or Sierra and B10 work.

This report changes no product file or shared contract.
