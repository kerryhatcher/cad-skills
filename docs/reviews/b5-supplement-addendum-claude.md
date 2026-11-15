# B5 supplement addendum (claude-skill-dev)

Date: 2026-11-14 06:44:09 UTC. This record adds to `docs/reviews/b5-supplement-claude.md`. The 707 files of `b5-files.sha256` are not changed.
The older supplement manifest `b5-supplement-files.sha256` stays as history. `probe_expect.py` changed after it (the delete-off expectation).
The complete supplement set is `docs/reviews/b5-supplement-files-v2.sha256`. Paths are under `examples/pcb-trial/` unless stated.

## 1. D1 removal with deletion OFF (native, replace on, relink off)

Hypothesis written before the run (`scripts/probe_expect.py`): D1 stays on the board and nothing changes.
Observed (`GUI_lp_removed1_delete_off_185`): the footprint D1 stays (same UUID, same position), but its schematic `path` changes to null.
The comparison with the empty expectation is `different` with exactly this one difference. The hypothesis was partly wrong: the footprint is unlinked.
Parity: one `extra_footprint` (D1). DRC: `lib_footprint_mismatch`, 2 unconnected items, exit 5.
The deletion-ON result (D1 removed, `equal` against `remove-d1.json`) stays in the frozen evidence.
Evidence: `results/supplement/probes/lp_removed1_delete_off/`, screenshots in `results/supplement/probes/shots/`.

## 2. Remove then re-add D1: UUID measured

Source: the saved snapshots (no GUI repeat). File: `results/supplement/probes/lp_readd_d1/d1_uuid_comparison.json`.

| State | Footprint UUID | Schematic path | Position |
|---|---|---|---|
| Baseline (before removal) | `4b40f9a3-a36b-401f-934b-c5bfce32e707` | `/ca407196-c3e8-5fc0-b85c-f32de932b957` | 125, 106, 180 degrees |
| Re-added D1 | `4930f048-ace0-4c08-a3be-657096168f2a` | same path | 132.545, 132.295, 0 degrees |

The re-added D1 gets a new footprint UUID. The schematic path is the same, because the symbol UUID is the same. The position and the rotation are the default values, not the original values.
This is separate from the allowed added-footprint expectation, which does not predict a random UUID.

## 3. E3 diagnostics (DRC and parity, no GUI repeat)

Command: `kicad-cli pcb drc --schematic-parity --exit-code-violations --severity-all --format json` (`scripts/diag_drc.sh`, step `DIAG_drc_186`, image `localhost/cad-skills-trial:b5`, offline).
Each board is bound to its source: `results/supplement/e3/index.json` has the SHA-256 of the board and of each schematic, the exit code of kicad-cli, and the full findings (`drc.json` for each run).
All 13 runs exit 5 (the boards are intermediate boards with violations or unconnected items). None is a clean-board claim.

| Board | Schematic source | Parity findings | Matches the expectation? |
|---|---|---|---|
| `vz_none`, `vz_value` | native | 0 | yes. DRC: `via_dangling`, `track_dangling` (the text-added via and arc have no connection) |
| U2 A | SKiDL run g | 4 `net_conflict` | The board has auto net names (`Net-(C1-Pad1)`, `Net-(D1-A)`). The schematic gives `N_RC` and `N_LED`. Cause not examined. |
| U2 B | SKiDL run h | 4 `net_conflict` | consistent with the earlier pad-net differences |
| U3 A, B, F | SKiDL run g (the netlists of g and h have the same bytes) | 0 | yes |
| U3 B with the schematic of run h | SKiDL run h | 3 `net_conflict` (VIN) | consistent with the wrong wiring of that schematic |
| U3 C (sentinel) and G (default restore) | SKiDL run g | 1 `extra_footprint` (C2) | yes. The exact expected difference: C2 is on the board, not in the schematic, with no pad nets. G has path null. |
| D1 delete off | native without D1 | 1 `extra_footprint` (D1) | see section 1 |
| re-added D1 | native | 0 | yes |
| R2 in a sub-sheet | root and sub-sheet | 1 `duplicate_footprints` (R2) | consistent with the added duplicate R2 |

Invalid U3 runs D and E are not examined (historical). Limit: the U3 shell helper copies the saved board and does not record the KiCad process exit. The exit of KiCad for U3 is therefore not measured.

## 4. T11 drill marks: cause and disposition

Cause (measured, `T11_drillshape_188`, `results/supplement/t11/drill_marks/t11d_drillshape_0_1_2/`): the final board stores `(drillshape 1)` in its plot parameters (0 none, 1 small, 2 full).
The T10 command uses `--board-plot-params`, so kicad-cli plots small drill marks in the copper and mask files. One-variable test: with `drillshape 0` in a copy of the board, all 9 kicad-cli Gerber files equal the KiBot files (stable content, 0 differing lines).
With `drillshape 1`: 10 differing lines in each copper file and 6 in each mask file. With `drillshape 2`: 13 and 9.
KiBot 1.9.1 has no `drill_marks` option for the gerber output (warning W015 in `T11_drillmarks_187`). Its files have no marks.
Without `--board-plot-params`, kicad-cli writes Protel extensions (`.gtl`, `.gbl`) and other differences (`results/supplement/t11/drill_marks/t11c_cli_without_board_params/`).
Disposition (proposal for the lead, no script change made): the export contract has no drill-mark setting, so the marks come from a hidden board setting. Before final acceptance, either set `drillshape` to 0 in the final board (no marks in fabrication Gerbers) and re-export, or add an explicit drill-mark field to the export contract. The frozen export and package scripts are unchanged.

## 5. E4 labels

`results/supplement/classification.json` classifies `gate3_fpr1_replace_off` as an option experiment (2 parity findings) and corrects the comment of `export_final.sh` line 6: the `.gbr` names come from `--board-plot-params`, not from Protel extensions. Historical bytes are unchanged.
