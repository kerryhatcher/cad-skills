# B5 correction record (claude-skill-dev)

Date: 2026-11-14 06:51:29 UTC. Authorization: skill-dev-lead, 06:48:29 UTC (E1 to E6, Pi-1, Pi-2). The freeze was lifted for `check_exports.py`, `build_draft_package.py`,
`export_final.sh`, `layout.py` (plot settings) and `tests/test_trial_exports.py`. These 5 files are the only changed entries of `b5-files.sha256`.
The 325-file supplement (`b5-supplement-files-v2.sha256`) is unchanged. `identity.py`, the setup and B234 are unchanged.
The first final revision (`results/final`, with its draft package and exports) stays as history. Paths are under `examples/pcb-trial/`.

## Corrected final revision: `results/final_r2/`

| Item | Result | Evidence |
|---|---|---|
| Board | `layout.py --final` now sets the saved plot settings `drillshape 0`, `usegerberattributes no`, `usegerberadvancedattributes no` and fails if one entry is absent. KiCad keeps them after refill and save. | `results/final_r2/trial.kicad_pcb`, steps `R2_layout_189`, `R2_final_drc_190` |
| Clean reports for these bytes | DRC exit 0: 0 violations, 0 unconnected, empty parity. ERC exit 0. | `results/final_r2/drc.json`, `erc.json` |
| Design identity unchanged by the plot correction | `identity.py compare` of the first and the corrected board: `equal`. A text diff without the three settings: 0 lines. | `results/correction/identity/` |
| Exports | 6 commands exit 0 (`R2_export_191`, `R2_fabpdf_192`). | `results/final_r2/export/` |
| E1, E2, E6 checks (`check_exports.py EXPORT_DIR BOARD`) | 7 of 7 pass: saved plot settings, layer set, no active attribute command in 9 files, one `G04 #@! TF.FileFunction` comment per file against the fixed mapping and the board copper order, drill, placement (exactly 7 rows, no repeated reference). The first final revision fails 3 checks (plot settings, attributes, layer function). | `scripts/check_exports.py` |
| T11 with a NEW config `trial.kibot.v3.yaml` (`use_gerber_x2_attributes: false`, `use_gerber_net_attributes: false`) | No difference: 9 Gerbers, drill split, placement. `trial.kibot.yaml` is unchanged. | `results/final_r2/t11/`, step `R2_kibot_195` |
| RC assertion | 2.0860 V pass. 220 nF: 1.2054 V fail. | `results/final_r2/rc/`, steps `R2_rc_good_193`, `R2_rc_wrong_194` |
| Draft package | `validate.py`: pass, exit 0, 0 findings. Status `draft`. `fab.profile_evidence` pending. `fab.layer_order` now comes from `gerber.layer_function` (E1). A `qualified` claim fails with `pkg.false_qualification`. Package PCB hash `56f794242345dd39...` equals the board. | `results/final_r2/draft_parent/` |
| Pi-2 host commands | Logged with exit codes: `T13r2_build_196` (0), `T13r2_validate_197` (0), `T13r2_negative_198` (1, expected). | `results/logs/` |

## Other corrections

| Item | Correction |
|---|---|
| E1 | Layer order comes from the file-function comment of each Gerber, not from file names. Tests: swapped copper bytes with correct names fail; missing, duplicate and incorrect declarations fail; the copper order follows the board (4-layer case). No job-file-only check. |
| E2 | A repeated reference fails before comparison, in both row orders, identical and conflicting. The row count is exactly 7. |
| E4 | The comment of `export_final.sh` is corrected (header with the table below). The appended classification of `gate3_fpr1_replace_off` stays (`results/supplement/classification.json`). |
| E5, E6 | Drill marks off and X2 off through the saved settings. `--no-x2` and `--board-plot-params` stay. KiBot uses the neutral X2 options. No schema change. |
| Pi-1 | Current-reader comparisons of the 3 stale records: `results/correction/pi1/`. Same status and counts. The added-footprint records now have `value`. The historical files are unchanged. |

## Contract, CLI and effective value

| Contract setting | CLI option or saved setting | Effective value (measured) |
|---|---|---|
| format rs274x | `pcb export gerbers` | RS-274X files |
| units mm | gerbers: always mm. `pos --units mm`. `drill -u mm` | `%MOMM*%`. Positions and holes in mm |
| x2 false | `--no-x2` and saved `usegerberattributes no`, `usegerberadvancedattributes no` (the saved settings override `--no-x2`) | 0 active `%TF` `%TA` `%TO` `%TD` in 9 files. File function as `G04 #@! TF.FileFunction` comment |
| gerber.decimal_places 6 | `--precision 6` | `%FSLAX46Y46*%` |
| drill marks (no contract field) | saved `drillshape 0` | no marks. Copper and mask files equal KiBot files |
| drill zero_suppression leading, decimal_places 3 | `--excellon-zeros-format suppressleading` | header `FORMAT={3:3/ absolute / metric / suppress leading zeros}` |
| drill separate_files | `--excellon-separate-th` | `trial-PTH.drl`, `trial-NPTH.drl` (package: `board-PTH.drl`, `board-NPTH.drl`) |
| origin absolute | `--drill-origin absolute`, no `--use-drill-file-origin` | absolute coordinates. KiCad writes Y as the negative of the board Y |
| layer suffixes | `--board-plot-params` with saved `usegerberextensions no` | `trial-F_Cu.gbr` and others (package: `board` plus the contract suffix). No Protel extensions |
| layers | `--layers` with 9 KiCad layer names | 9 files |

## U1 to U6 status

| Row | Status |
|---|---|
| U1 native schematic, GUI update | Supported for 6 gate edits (no edit, reorder, value of R2, add C2, remove D1, footprint of R1) on this source, fixture, image and machine (first and repeat runs). The replace-off run is a separate option experiment with 2 parity findings. It is not a supported gate (agreed E4). Arc, via and zone preserved. Limits: no zone refill in a GUI update. |
| U2 SKiDL schematic, GUI update | FAILS the no-edit gate. Cross-source: paths lost, duplicates added. Same-source: 5 pad-net differences. The SKiDL schematic has wrong connectivity in 3 of 4 successful runs. |
| U3 netlist import | Experimental. Input consumption, no-edit update, sentinel add and the delete option measured. Other edits untested. |
| U4 update mechanism and options | Measured: replace on and off, delete on and off (D1 removal: deleted, or kept with path null), relink on and off (rename probe). Move to another sheet loses identity. Re-added D1 gets a new UUID. |
| U5 IPC API | Untested. `kipy` is absent, no API socket, no network. |
| U6 pcbnew updater | Measured negative: no update function in the module. |

## Limits and untested

U3 edits other than the no-edit and sentinel tests, U5, zone refill inside a GUI update, other machines and KiCad versions. The STEP file has no 3D models. The package is a bare-board draft with no supplier evidence.
The tests ran: `tests/test_trial_exports.py` 16 of 16, `tests/test_trial_identity.py` 17 of 17.
