# B9 bounded review addendum: Pi

Date: 2026-11-15 UTC. Author: pi-skill-dev.

I read sections 4 to 8 of `docs/reviews/b9-b10-interface-claude.md` and
`docs/reviews/pcba/codex-bounded-review-update.md`.

## Verdict

I agree to the bounded B9 start for neutral mapping, variants, neutral BOM, and stock work.

The interface includes the lead decisions and the Codex corrections:

- Section 4 requires an explicit map entry for each mechanical exclusion. The skill
  validates the map against `cad-skills/part-map` 1.0. The shared validator binds the
  `parts` bytes only.
- Section 5 keeps `variants.yaml` as the sole population owner. A `hand_installed`
  reference must have state `populate`. Otherwise the step rejects it.
- Section 6 keeps the exact board-file position and source rotation in the neutral rows.
  The `pos` export value appears only as `export_rotation_deg` in separate comparison
  evidence.
- Section 6 includes `installation_method` in the BOM grouping key.
- Section 8 names `board.yaml.extensions.pcba.stock.max_age_days`. Section 9.1 names
  `supplier_profile.extensions.pcba.hand_installed_bom`.

Sierra conversion and B10 publication stay outside this start.

## Non-blocking editorial note

Section 4, first sentence, says the map covers each populated or DNP board reference.
The reject rule also covers an `exclude_from_assembly` reference that a declared variant
uses. Add that state to the first sentence. This change is not a blocker.

## Limits

This agreement covers sections 4 to 8 only. No product file is changed. No shared
contract is changed. No test is run.
