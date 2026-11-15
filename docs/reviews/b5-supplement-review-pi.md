# B5 supplement review: Pi

Date: 2026-11-14.

**Decision: the supplement evidence set is accepted at its stated limits. No blocking defect. Three small record observations remain.**

This review covers the frozen set of `docs/reviews/b5-supplement-files-v2.sha256`. It focuses on T5, T6, the E3 diagnostics, the native limit probes and the option experiments. I made no GUI repeat and no implementation edit. I changed only this report.

## 1. Reviewed bytes

| Item | Value |
|---|---|
| Supplement record | `docs/reviews/b5-supplement-claude.md` |
| Addendum | `docs/reviews/b5-supplement-addendum-claude.md` |
| Supplement manifest | `docs/reviews/b5-supplement-files-v2.sha256`, 325 entries |
| Supplement manifest hash | `e54bc0949d687e999649e9d1de0ba0a4ccf9f98e4b88013b67a3beccb58045a8` |
| Check result | 325 of 325 entries `OK` |
| Main manifest at the supplement freeze | `docs/reviews/b5-files.sha256`, 707 entries |
| Image | `d881df4ef3e2ec76995f4070596550db118b23e7f6db9017f09a418c44c4b1c2` |

Every file under `results/supplement/` is in the v2 manifest. The only manifest paths outside `examples/pcb-trial/` are the two records.

The 325 supplement entries stayed frozen after their freeze. A later authorized repair, which started at 06:48, changed 5 main files: `check_exports.py`, `build_draft_package.py`, `export_final.sh`, `layout.py` and `tests/test_trial_exports.py`. Those 5 files are not in the 325 supplement entries. Thus the current `b5-files.sha256` has 5 stale hashes, but the supplement set still verifies. Do not read this review as a claim that all 707 main entries are unchanged.

The older manifest `b5-supplement-files.sha256` stays as history. The addendum explains that `probe_expect.py` changed after it, so v2 is the complete set. That is correct: the old manifest does not contain the delete-off expectation or the E3 diagnostics.

## 2. T5: ERC exit code

I agree with the T5 result.

| Run | Schematic | Exit | Findings |
|---|---|---:|---|
| `t5d/good` | native schematic | 0 | 0 |
| `t5d/bad` | native schematic with all net labels of the first label removed | 5 | 3 `pin_not_connected`, severity `error` |

The bad run gives the intended finding and a nonzero exit with `--exit-code-violations`. Stop condition S5a did not trigger: the defective fixture produced the expected finding. Stop condition S5b did not trigger: the violation gave a nonzero exit, so the flag is reliable on this fixture.

The three earlier runs `t5`, `t5b` and `t5c` are wrong fixtures or damaged files. Each has an `INVALID.txt`. They stay as history. The valid run is `t5d`. The defect is one kind only (unconnected pins). Other ERC rules are not tested. The supplement states this limit.

## 3. T6: SKiDL `ERC()` exit code

I agree with the T6 result.

| Run | Circuit | SKiDL report | Process exit |
|---|---|---:|---:|
| `T6_good2_177` | correct wiring | no errors or warnings | 0 |
| `T6_bad2_178` | R1 pin 2 and D1 pin 2 unconnected | 4 warnings, 0 errors | 0 |

`ERC()` logs the findings and does not change the process exit code. The defective circuit gives warnings, not errors, and exit 0. Thus the B6 wrapper must read the SKiDL log or the warning and error counts and fail by itself. The record states this. The first probe version read a count attribute that does not exist. Those runs are invalid and marked. The valid runs are `T6_good2_177` and `T6_bad2_178`.

## 4. E3 diagnostics

The E3 set answers the earlier gap. `results/supplement/e3/index.json` holds 13 runs. Each entry has the source description, the `kicad-cli` exit code, the violation list, the unconnected-item count, the parity list, the board and schematic hashes, and the command. Each run directory holds `drc.json`, `exit.txt`, `stdout.txt` and `hashes.txt`.

I recomputed each entry from its retained `drc.json`. The exit code, the violation types, the unconnected count and the parity types agree with the index for all 13 runs. Each board hash matches a saved board in `results/`.

I re-ran the full DRC with schematic parity, offline, on three temporary copies:

| Board | Exit | Violations | Unconnected items | Parity |
|---|---:|---:|---:|---|
| `diag_u3c` | 5 | 12 | 6 | 1 `extra_footprint` |
| `diag_u3g` | 5 | 12 | 6 | 1 `extra_footprint` |
| `lp_sheet_r2` | 5 | 1 | 4 | 1 `duplicate_footprints` |

Each result equals its stored report.

The parity results match the stated expectations:

- `vz_none`, `vz_value`: 0 parity findings. DRC gives `via_dangling` and `track_dangling` and 8 unconnected items. The fixture is an intermediate object-preservation board, not a clean board.
- `u2same_A`, `u2same_B`: 4 `net_conflict` each, consistent with the pad-net differences.
- `diag_u3a`, `diag_u3b`, `diag_u3f`: 0 parity findings. `diag_u3b_h` uses the literal run-h schematic and gives 3 `net_conflict` on VIN, consistent with the wrong wiring of that schematic.
- `diag_u3c` and `diag_u3g`: 1 `extra_footprint` for C2. The sentinel and default-restore states carry the exact expected difference.
- `lp_removed1_delete_off`: 1 `extra_footprint` for D1.
- `lp_readd_d1`: 0 parity findings.
- `lp_sheet_r2`: 1 `duplicate_footprints` for R2.

The addendum states that the U3 shell helper copies the saved board and does not record the KiCad process exit. The parity diagnostics do not supply that process result. The limit is stated correctly.

## 5. Native limit probes and option experiments

I agree with the measured limit results.

| Probe | Expectation before the run | Observed | Result |
|---|---|---|---|
| Remove D1, delete OFF | empty list (D1 stays, nothing changes) | D1 stays with the same UUID and position, but its schematic `path` becomes null | `different` with the one path change. The hypothesis was partly wrong. Parity: 1 `extra_footprint` (D1). |
| Remove D1, then re-add D1 | D1 added with its library ID, value and baseline pad nets. The UUID and position are not predicted | `equal`. The re-added D1 gets a new footprint UUID and default position and rotation | `equal` |
| Move R2 to a sub-sheet | none stated | R2 keeps its old footprint and loses its path, and a new R2 appears | `different` with 2 changes. A limit result, not a pass. |

The delete-off expectation is in `probes/probe_exp2/remove-d1-delete-off.json` (empty list). The re-add expectation is in `probes/probe_exp2/readd-d1.json`. Both come from `scripts/probe_expect.py`, which reads the baseline snapshot only. The re-add comparison is `equal` against that expectation. The re-add measure `d1_uuid_comparison.json` records the new UUID and the default position from the saved snapshots. That is a save-only comparison with no GUI repeat.

The sheet-move probe states no expectation. The record calls it a limit. That is correct for a limit probe. I note that the result is an interpretation after the run, not a pre-stated hypothesis.

## 6. T11 drill-mark evidence and E4 labels

I reproduce the addendum's T11 drill-mark numbers with the retained files. I compared each kicad-cli export in `t11d_drillshape_0_1_2/` with the KiBot files in `t11b/kibot_out/gerbers/`, after date and generator normalization.

| Board plot setting | Differing lines, F.Cu | B.Cu | F.Mask | B.Mask | Silkscreen |
|---|---:|---:|---:|---:|---:|
| `drillshape 0` | 0 | 0 | 0 | 0 | 0 |
| `drillshape 1` | 10 | 10 | 6 | 6 | 0 |
| `drillshape 2` | 13 | 13 | 9 | 9 | 0 |

The one-variable test is correct. The `drillshape 0` export equals KiBot. The `t11c_cli_without_board_params/A` export uses Protel extensions (`.gtl`, `.gbl`, `.gm1`). KiBot 1.9.1 has no `drill_marks` option, so the B and C runs give a warning and no effect. The record correctly rejects that option.

The disposition that the addendum offers (set `drillshape 0` or add a contract field) is resolved by Codex E5 and the lead decision: set `drillshape 0` and keep the schema unchanged. The supplement leaves the frozen scripts unchanged, which is correct for this correction record.

`results/supplement/classification.json` corrects the two E4 labels: `gate3_fpr1_replace_off` is an option experiment with 2 parity findings, and the `export_final.sh` suffix comment describes the `.gbr` names from `--board-plot-params`, not Protel extensions. Historical bytes are unchanged.

## 7. Observations

1. **The supplement step list is not in a `steps.txt`.** The trial record says each step has a line in `results/logs/steps.txt`. The frozen `steps.txt` in the main manifest ends at step `EXPORT_fabpdf_170`. The supplement steps `T5_erc_171` to `T11_drillshape_188` have their `.cmd` and `.out` files in the v2 manifest, but no line in `steps.txt`. The addendum names the step IDs. The individual files are the record. State this, or add a supplement step list.
2. **The sheet-move probe has no expectation before the run.** The record gives the result and the parity finding. It is a limit, so no pass is claimed. Keep it as a limit, or state the hypothesis before a later run.
3. **The U2 parity cause is not examined.** The addendum says the `u2same` parity `net_conflict` comes from the auto net names and gives the cause as not examined. The pad-net comparison in the trial record gives the same result. This is an accepted limit.

## 8. Verdict

The supplement evidence set is accepted at the stated limits. T5, T6, E3 and the limit probes are correct and reproducible. The T11 drill-mark test is correct and matches the E5 decision. No implementation change is necessary for the supplement. The three observations are record clarity items. The final B5 record must name this supplement and its manifest, and the E1 to E6 corrections remain the main work.
