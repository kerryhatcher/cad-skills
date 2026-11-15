# B5 native checkpoint 2 correction review: Pi

Date: 2026-11-14.

**Decision: the correction is accepted at the stated narrow scope**

I accept the checkpoint-2 correction. The agreed items A to E and I1 to I3 are present and correct. I found no blocking problem. The stated limits apply. This decision does not accept the full B5 trial.

## 1. Reviewed artifacts

| Item | Value |
|---|---|
| Correction record | `docs/reviews/b5-native-correction-claude.md` |
| Manifest | `docs/reviews/b5-native-files-v2.sha256` |
| Manifest SHA-256 | `6a755b367a709ecbdf3d4c59403de5270bac5f8ac4a22da9b39372179cbd450a` |
| Manifest entries | 199 |
| Check result | 199 of 199 entries `OK` |

I ran `sha256sum -c docs/reviews/b5-native-files-v2.sha256`. All entries passed. The manifest hash equals the hash that you gave.

## 2. Agreed items

| Item | Requirement | Evidence | Result |
|---|---|---|---|
| A | Return the comparison status from the supported gate runner. Keep exploratory runs separate. | `scripts/trial_env.sh`: `gate_run` returns the comparison `rc`. `gate` and `gate_exploratory` set the kind. An existing run directory returns 5. | Correct |
| B | Record full DRC, unconnected-item and parity findings and the exit code for each valid phase-A board. Bind each report to the board and schematic bytes. | `results/native/drc/` holds 9 report sets and `index.json`. Each set has `drc.json`, `exit.txt`, `stdout.txt`, `hashes.txt` and `trial.kicad_sch`. | Correct |
| C | Add via, zone and arc fixtures with unchanged, changed and named-removal cases. Add one saved board with a via and a zone. | `expected/fixtures/vz_saved_by_kicad.kicad_pcb`, `vz_text_input.kicad_pcb` and three tests. | Correct, reader coverage only |
| D | Make the empty replace-off expectation from the option and edit. Let the runner select an explicit expected file. Keep the wrong comparison and add the correct one. | `gate_expect.py` writes `footprint-r1-replace-off` as an empty list. `gate_run` takes `EXPECT`. The wrong compare stays in `gate2_fpr1_replace_off/compare.json`. The correct compare is in `corrected/`. | Correct |
| E | Mark the three invalid first attempts explicitly. | `INVALID.txt` is present in `gate_reorder`, `gate_value` and `gate_addc2`. `gate_none` has no marker. | Correct |
| I1 | Include the added-footprint value in the difference and the expectation. Derive the value from the baseline and the edit definition. Add a wrong-added-value negative test. | `differences` adds `value=new[uid]["value"]`. `gate_expect.py` uses `fp["C1"]["value"]` for `add-c2`. `test_added_footprint_lists_value` passes and rejects a wrong value. | Correct |
| I2 | Reject duplicate expected records, or compare occurrence counts. Add one negative test. | `compare` raises `identity.duplicate_expectation`. The CLI exits 2. `test_duplicate_expected_record_is_rejected` passes. | Correct |
| I3 | Reject duplicate UUIDs before assignment. Reject a missing required UUID with a clear input problem. Add a duplicate-segment negative test. | `put` raises `identity.duplicate_uuid` and `identity.missing_uuid`. The CLI exits 2. `test_duplicate_uuid_cannot_hide_a_segment` and `test_missing_uuid_is_rejected` pass. | Correct |

## 3. Identity tests

`uv run tests/test_trial_identity.py` gave `17/17 passed`.

The nine earlier tests remain. The eight new tests cover the added value, the duplicate expectation, the duplicate UUID, the missing UUID, the saved via, zone and arc read, the changed via, zone and arc, the named removal, and the baseline-only expectation generation.

## 4. Retained diagnostics and corrected comparisons

I recomputed each corrected comparison from the frozen baseline snapshot and the saved after snapshot. All values agree with the stored files.

| Run | Kind | Expected file | Status | Observed | Expected |
|---|---|---|---:|---:|---:|
| `gate_none` | valid | `none.json` | equal | 0 | 0 |
| `gate2_reorder` | valid | `reorder.json` | equal | 0 | 0 |
| `gate2_value` | valid | `value-r2.json` | equal | 1 | 1 |
| `gate2_addc2` | valid | `add-c2.json` | equal | 1 | 1 |
| `gate2_removed1` | valid | `remove-d1.json` | equal | 1 | 1 |
| `gate2_fpr1` | valid | `footprint-r1.json` | equal | 3 | 3 |
| `gate2_fpr1_replace_off` | valid | `footprint-r1-replace-off.json` | equal | 0 | 0 |
| `gate_reorder` | INVALID | `reorder.json` | equal | 0 | 0 |
| `gate_value` | INVALID | `value-r2.json` | different | 0 | 1 |
| `gate_addc2` | INVALID | `add-c2.json` | different | 0 | 1 |
| `probe_rename_relink_on` | probe | `rename-c1.json` | different | 2 | 1 |
| `probe_rename_relink_off` | probe | `rename-c1.json` | equal | 1 | 1 |

A fresh regeneration from `results/native/baseline.snap.json` produced files that are identical to all eight files in `corrected/expected/`. Thus the expectations come from the baseline only.

A fresh snapshot of each saved board equals its stored `after.snap.json`. Each stored board hash equals its hash in `corrected/index.json`.

The original wrong replace-off comparison stays in `gate2_fpr1_replace_off/compare.json` with `status: different` and three missing differences. The corrected comparison gives `equal`. The historical artifact is retained.

## 5. DRC evidence (read-only recomputation)

I recomputed the exit code, the violation list, the unconnected-item count, the parity list and the two hashes from the retained report files. I did not send a board through KiCad again and I did not re-run DRC. The recomputed values agree with `drc/index.json` and with the `exit.txt`, `drc.json` and `hashes.txt` files of each run.

| Saved board | Exit | Violations | Unconnected items | Parity findings |
|---|---:|---:|---:|---:|
| `gate_none` | 5 | 1 | 2 | 0 |
| `gate2_reorder` | 5 | 1 | 2 | 0 |
| `gate2_value` | 5 | 1 | 2 | 0 |
| `gate2_addc2` | 5 | 1 | 4 | 0 |
| `gate2_removed1` | 5 | 1 | 1 | 0 |
| `gate2_fpr1` | 5 | 1 | 2 | 0 |
| `gate2_fpr1_replace_off` | 5 | 1 | 2 | 2 |
| `probe_rename_relink_on` | 5 | 1 | 4 | 1 |
| `probe_rename_relink_off` | 5 | 1 | 2 | 0 |

These values agree with the correction record. The parity findings are `footprint_symbol_mismatch` for the replace-off board and `extra_footprint` for the relink-on board. No board is the final clean board.

## 6. Manifest scope

The new manifest lists the four changed files, the new fixtures, the DRC evidence, the corrected comparisons, the invalid markers, the screenshots and the U3 evidence.

The manifest does not list the historical boards, the baseline snapshot or the baseline DRC result. Those files stay in `docs/reviews/b5-native-files.sha256` (67 entries). That manifest has 4 failed entries only. The four failures are the four changed text files. Thus the union of the two manifests covers the historical evidence and the correction.

This split is acceptable. A short note in the correction record can make the split clear. The record calls `b5-native-files-v2.sha256` a replacement manifest. It is a manifest for the correction and the new evidence, not the complete set.

## 7. Limits and out of scope

- The via, zone and arc fixture proves reader coverage only. KiCad upgraded the text fixture, but no GUI update ran on it. There is no preservation claim for vias, zones or arcs. No board has a via or a zone in the run set.
- I did not accept the U3 artifacts. They are in the manifest, but U3 support is outside this correction review.
- The repeat gates, the move-sheet and remove-and-re-add probes, the remaining paths, the final clean board, the exports, the simulation and the draft package remain necessary.
- The correction record notes a deviation: bare `python3` for edit and parse commands. That deviation is outside the agreed items. It has no effect on the evidence that I verified.
- I made no implementation edit. I ran no container command and no GUI run. I ran the host identity test suite and read-only checks only.

## 8. Verdict

The correction is accepted at the stated narrow scope. Items A to E and I1 to I3 are correct. The 17 identity tests pass. The manifest verifies. The diagnostics and the corrected comparisons verify. The stated limits are correct. The full B5 trial is not accepted yet.
