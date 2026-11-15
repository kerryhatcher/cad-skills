# B5 native checkpoint 2: correction record (claude-skill-dev)

Date: 2026-11-14, 06:18:42 UTC. Authorization: skill-dev-lead, 06:10:44 UTC. Scope: Pi A to E and Codex I1 to I3 only.

## Changes

| Item | Change |
|---|---|
| I1 | `identity.py` lists the value of an added footprint. `gate_expect.py` derives the expected value of C2 from the baseline value of C1. Test: wrong added value fails. |
| I2 | A duplicate expected record stops the comparison (exit 2, `identity.duplicate_expectation`). Test added. |
| I3 | A duplicate UUID or a missing UUID stops the reader (exit 2, `identity.duplicate_uuid`, `identity.missing_uuid`). Tests added. |
| A | `gate` returns the comparison result. `gate_exploratory` is separate and also returns the real result. A run directory that exists is not overwritten. |
| B | `results/native/drc/` holds the full DRC and parity output of 9 saved boards. `index.json` binds each report to the board hash and the schematic hash. |
| C | Tests for arc, via and zone: read, changed, removed by UUID. Real saved board `vz_saved_by_kicad.kicad_pcb`. |
| D | `footprint-r1-replace-off` is in `gate_expect.py` (empty list). The runner takes an explicit expected file. Corrected comparisons are in `results/native/corrected/`. |
| E | `INVALID.txt` in `gate_reorder`, `gate_value` and `gate_addc2`. |

## Measured results

- `uv run tests/test_trial_identity.py`: 17 of 17 passed (9 before).
- All 7 valid runs give `equal` against the corrected expectations, including `gate2_addc2` (with value) and `gate2_fpr1_replace_off` (empty expectation).
- The re-read snapshot of each of the 12 boards equals its stored snapshot.
- DRC with parity gives exit 5 on all 9 boards. Parity findings: 0, except `gate2_fpr1_replace_off` (2, `footprint_symbol_mismatch`) and `probe_rename_relink_on` (1, `extra_footprint`). None of these boards is the final clean board.
- The old manifest `b5-native-files.sha256` has 4 failed entries: `identity.py`, `gate_expect.py`, `trial_env.sh`, `test_trial_identity.py`. All other entries match. `sexp.py` and the accepted setup are unchanged.
- Replacement manifest: `docs/reviews/b5-native-files-v2.sha256` (199 entries, all match). It lists the changed files, the new evidence, the screenshots and the U3 evidence.

## Limits

- The via, zone and arc fixture has objects that I added as text. `kicad-cli pcb upgrade --force` saved the board. No GUI update ran on it. There is no preservation claim for vias, zones or arcs.
- The `kicad-cli` command for the fixture has no step log ID.
- The repeat gates, the move-sheet and remove-and-re-add probes, and the remaining paths are not run yet.
- Deviation: I used bare `python3` for edit and parse commands. See the work state record.
