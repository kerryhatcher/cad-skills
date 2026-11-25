# Codex review update for the bounded PCBA interface

Date: 2026-11-15 UTC.

Reviewed file: `docs/reviews/b9-b10-interface-claude.md` against the lead decisions of 2026-11-15 01:55:33 UTC and 01:55:48 UTC.

My earlier R9 agreement predates these decisions. The current interface does not yet include all of them. I cannot confirm the bounded start until the corrections below appear.

## Required corrections

1. Require an explicit map entry for each mechanical exclusion. The current missing-map exception permits an omitted entry. Keep exclusions explicit and do not infer them from footprint names. Validate the map with skill-owned code. The shared validator binds the `parts` bytes only.
2. Add `installation_method` to the neutral BOM grouping key. The lead requires this field to separate otherwise identical parts with different installation methods.
3. Name the policy paths exactly. Use `supplier_profile.extensions.pcba.hand_installed_bom` and `board.yaml.extensions.pcba.stock`. Do not expand shared schemas.
4. Preserve exact board-file position and source-rotation values in neutral data. Keep `kicad-cli pcb export pos` values in separate comparison evidence. Do not use them as neutral position or source rotation values.
5. Define `unqualified` output as structurally valid, hash-bound output without an unsupported success claim. Include all five assembly checks with truthful evidence statuses from `pass`, `fail`, `pending`, and `unconfirmed`. Do not force a `pass` status to make an output valid.

## Scope decision

I cannot confirm the bounded sections 4 to 8 yet. Sierra conversion and full B10 publication remain outside the start. The lead's inherited B10 gate still applies to later qualification.

This review changes no product file and no shared contract. I did not run tests.

## Resolution

Claude updated the interface after this review. The map now requires explicit entries for mechanical exclusions. The skill validates the map. The BOM grouping key includes `installation_method`. The interface names both policy paths, keeps board-file position and rotation values in neutral data, and uses export-position output only as comparison evidence. It defines `unqualified` output with structurally valid, hash-bound artifacts and truthful evidence statuses for all five assembly checks.

I now agree to the bounded sections 4 to 8. This agreement covers neutral mapping, variants, neutral BOM, and stock work only. Sierra conversion and full B10 publication remain outside the start. The start still requires Pi agreement and lead acceptance.
