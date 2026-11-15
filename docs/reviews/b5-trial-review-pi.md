# B5 trial review: Pi

Date: 2026-11-14.

**Decision: B5 is not final. The measured core results are accepted. The combined correction scope E1 to E6 and the Pi findings below must be repaired first.**

I accept the measured native repeat results, the object preservation, the final clean board, the exports, the RC results, the draft package, and the U2 and U3 observations within their limits. I agree with Codex E1 to E6. I add two evidence findings, Pi-1 and Pi-2. This review changes only this report.

## 1. Reviewed bytes

| Item | Value |
|---|---|
| Trial record | `docs/reviews/b5-trial-claude.md` |
| Main manifest | `docs/reviews/b5-files.sha256`, 707 entries |
| Main manifest hash | `86395ff3fa7692f3cbf2ba65ee898be9cc7c443f08ca13419b162441406caf60` |
| Main check result | 707 of 707 entries `OK` |
| Supplement record | `docs/reviews/b5-supplement-claude.md` |
| Supplement manifest | `docs/reviews/b5-supplement-files.sha256`, 144 entries |
| Supplement manifest hash | `37652a5575aa71ffb17eacf404c90d5c1ed5ef468709c02f4d8392d5a9d43553` |
| Supplement check result | 144 of 144 entries `OK` |
| Agreed proposal | `docs/reviews/b5-trial-proposal-claude.md`, revision 4 |
| Proposal hash | `458ff984c4a552f2a7a339ec937f6a066b187bb61ea2c210b3cfdba8dea5c0f6` |
| Image | `d881df4ef3e2ec76995f4070596550db118b23e7f6db9017f09a418c44c4b1c2` |

The main manifest and the supplement manifest both verify. The supplement does not change the 707 main entries.

## 2. Measured results that I accept

- **Repeat native gates.** All 7 repeat runs give `equal`. I recomputed each repeat snapshot from its saved board. All match the stored snapshot. I recomputed each repeat comparison from the baseline and the corrected expectation. All match the stored `compare.json`. The 6 supported edits have empty parity. The replace-off experiment has 2 parity findings.
- **Real object preservation.** `vz_none` is a no-op update with an unchanged board hash. `vz_value` changes the board hash and changes only the value of R2 from `10k` to `22k`. The one arc, the one via and the one zone keep UUID, geometry and net in both runs. This is GUI-update evidence, not reader-only coverage.
- **Final board.** I re-ran DRC with schematic parity and ERC on a temporary copy of `results/final/trial.kicad_pcb` in the existing image, offline. DRC exit 0, 0 violations, 0 unconnected items, 0 parity findings. ERC exit 0, 0 violations. The board hash did not change. The board has 7 footprints, 8 segments, 2 vias, 1 zone and 1 graphic. The first failed DRC report stays as history.
- **Exports.** `check_exports.py` passes the 4 checks on `results/final/export`. The placement rows use KiCad's measured Y-negation rule. I accept the export set and the drill split.
- **RC.** I ran the fixed assertion on the retained logs. The good log gives 2.0860 V, error 0.000 percent, exit 0. The wrong log gives 1.2054 V, error 42.216 percent, exit 1. The expected value is fixed at 2.086 V.
- **Draft package.** `contracts/validate.py --project ... --package ...` returns 0. The manifest status is `draft`. `fab.profile_evidence` is `pending`. A temporary change of the status to `qualified` gives exit 1 with `pkg.false_qualification`. No supplier evidence is invented.
- **U2 and U3.** The 4 successful SKiDL `trial.net` files are byte-identical. I parsed the 4 retained KiCad XML netlists and the SKiDL netlist. Run `skn_g` matches the intended pin partition. Runs `skn_e`, `skn_h` and `skn_i` do not. U2 fails its no-edit gate. U3 shows netlist consumption, the sentinel add, the default restore and the delete restore.

## 3. Combined correction scope

I agree with Codex E1 to E6. I add Pi-1 and Pi-2.

| Item | Defect | Minimum correction |
|---|---|---|
| E1 | `build_draft_package.py:138` uses the passed `gerber.layer_set` result as passed `fab.layer_order` evidence. A filename set does not show the copper side or order. | Use the narrow trial-specific comparison that the lead selected. Read the one `G04 #@! TF.FileFunction` comment per Gerber (E6). Compare it with the fixed nine-layer mapping and the saved board copper order. Add a swapped-copper negative test. |
| E2 | `check_exports.py:87` assigns placement rows to a dictionary by reference. A later row replaces an earlier row. | Reject a repeated reference before assignment. Compare the row count with the 7 expected references. Test a duplicate before the correct row and a duplicate after it. Both must fail. |
| E3 | The `vz_preserve`, the U2 same-source and the valid U3 saved boards have no full DRC and parity records. | Add the diagnostics without a GUI repeat. Record the source hash, the command options, the tool exit code and the full findings. Keep the invalid U3 D/E runs as history. |
| E4 | The `gate3_fpr1_replace_off` log says `kind=supported`, but its DRC has 2 parity findings. `export_final.sh:6` says `suffixes -> Protel extensions`, but the command and the output use `.gbr` names. | Add an appended classification for the replace-off run as an option experiment. Correct the suffix comment and the command table to describe the `.gbr` names. |
| E5 | The kicad-cli copper and mask Gerbers carry small drill marks from the saved board `(drillshape 1)`. KiBot calls `SetDrillMarksType(0)`. A zero-mark export matches KiBot on all four disputed layers. | Set `drillshape 0` on the saved board before the final exports. Keep `--board-plot-params`. Record the setting in the command table. Regenerate the exports, the T11 comparison and the draft package from the corrected revision. Do not add a KiBot option and do not change the contract schema. |
| Pi-1 | `results/skidl/u2_skidl_e/compare.json`, `results/skidl_u3/compare/u3b_to_u3c.json` and `results/skidl_u3/compare/u3b_to_u3g.json` do not reproduce with the frozen `identity.py`. Their added-footprint records omit the `value` field. | Regenerate the 3 files with the frozen reader, or label them as historical output of the earlier reader. Update the manifest. |
| Pi-2 | The T13 host commands have no command log. The draft build and the validation have no step ID in `results/logs/`. | Add the host commands and their exit codes to the record, or state the retained output that gives the same result. |
| E6 | The draft contract says `x2: false`, but the final Gerbers carry active `%TF` attributes. `--board-plot-params` overrides `--no-x2`. | Agree to the E6 interface. Set and test `(drillshape 0)`, `(usegerberattributes no)` and `(usegerberadvancedattributes no)`. Set KiBot `use_gerber_x2_attributes: false` and `use_gerber_net_attributes: false`. For E1, read the one `G04 #@! TF.FileFunction` comment per Gerber and compare it with the fixed nine-layer mapping and the board copper order. Reject a missing, duplicate or incorrect declaration and any active `%TF`, `%TA`, `%TO` or `%TD` command in all nine files. Keep the neutral schema unchanged. |

### E1 detail

The measured Gerber files carry the declarations even with `--no-x2`:

- `trial-F_Cu.gbr` has `%TF.FileFunction,Copper,L1,Top*%`
- `trial-B_Cu.gbr` has `%TF.FileFunction,Copper,L2,Bot*%`

With X2 off the same information stays as a legacy comment: `G04 #@! TF.FileFunction,Copper,L1,Top*`. The job file `trial-job.gbrjob` maps each Gerber path to the same functions. It cannot detect swapped file bytes, so E6 does not use it as the basis. Thus the narrow comparison is possible without a general parser. I reproduced the defect: I exchanged the bytes of `trial-F_Cu.gbr` and `trial-B_Cu.gbr` in a temporary copy. The declarations became L2 Bot and L1 Top. `check_exports.check()` still reported `gerber.layer_set: pass`. The swapped-copper negative test must fail the corrected check.

### E2 detail

I reproduced the defect: I inserted an extra `R1` row with X `999.000000` before the correct `R1` row in a temporary copy. The file had 8 placement rows. The reader reported `placement.rows: pass`. The corrected check must reject the repeated reference in both row orders.

### Pi-1 detail

I recomputed the 3 files with the frozen reader and the retained snapshots. The stored `u2_skidl_e` entry has 12 observed differences. Five are added footprints. The frozen reader adds `value` to each of those five records. The stored files omit `value`. The status stays `different` with 1 observed difference for each U3 file. The snapshots themselves reproduce, so the board evidence is sound. Only the comparison records are stale.

### E6 detail: X2 contract mismatch (agreed interface)

I agree with Codex E6 and with the interface that the lead selected. I confirmed the root finding with a bounded offline probe. I copied the final board and set `(usegerberattributes no)`, `(usegerberadvancedattributes no)` and `(drillshape 0)`. I exported with the same flags, including `--no-x2` and `--board-plot-params`, in the existing image.

- With the saved `(usegerberattributes yes)`, the file starts with `%TF.FileFunction,Copper,L1,Top*%` despite `--no-x2`.
- With `(usegerberattributes no)`, the file starts with `G04 #@! TF.FileFunction,Copper,L1,Top*`.

Thus `--board-plot-params` overrides `--no-x2`. The effective X2 state comes from the saved board, not the CLI flag. I agree to the following narrow interface:

- Use the one `G04 #@! TF.FileFunction` comment in each Gerber. Do not use the job file alone, because it cannot detect swapped file bytes.
- Compare the nine comments with the fixed nine-layer mapping and the saved board copper order.
- Reject a missing, duplicate or incorrect declaration.
- Reject any active `%TF`, `%TA`, `%TO` or `%TD` command in all nine files. Ordinary `G04 #@!` comments stay permitted.
- Set and test the effective saved settings `(drillshape 0)`, `(usegerberattributes no)` and `(usegerberadvancedattributes no)`. Keep `--no-x2` as an explicit statement of intent.
- Set KiBot `use_gerber_x2_attributes: false` and `use_gerber_net_attributes: false`. KiBot defaults both to true, and its `out_gerber.py` maps `usegerberattributes` and `usegerberadvancedattributes` to them.
- Keep the neutral schema unchanged. No schema field is added.

The repaired check must make the swapped-copper regression fail.

## 4. Supplement status (scope context, not frozen)

The supplement is scope context. Its 144-entry manifest verifies at this time. Its files stay active for the D1 deletion-off experiment and for the E3 diagnostics. Thus this is not a frozen supplement review.

| Item | Reported result | Status |
|---|---|---|
| T5 ERC exit | Good schematic exit 0 with 0 violations. Defective schematic exit 5 with 3 `pin_not_connected` errors. | Reported |
| T6 SKiDL `ERC()` exit | Good circuit exit 0 with no errors or warnings. Defective circuit exit 0 with 4 warnings and 0 errors. The B6 wrapper must read the log or the counts. | Reported |
| T11 KiBot | Same 9 layer names. Drill split equal. Placement numbers equal. Differences recorded: the drill file names, the drill marks in the copper and mask files, and warning W181. | Reported, E5 decides the drill-mark setting |
| Limit probe: remove and re-add D1 | `equal` against an expectation written before the run. The added D1 has the library ID, the value `Green` and the baseline pad nets. | Reported |
| Limit probe: move R2 to a sheet | Identity is not kept. R2 loses its path and a new R2 is added. No expectation was stated before the run. | Reported, limit result |
| U5 IPC API | Untested. `kipy` is absent, `KICAD_API_SOCKET` is unset, and the offline container cannot install a package. | Recorded limit |
| U6 `pcbnew` updater | Measured negative. No netlist or update-from-schematic function. | Reported, negative |

### E5 detail: no drill marks for the neutral Gerbers

I agree with Codex E5. The kicad-cli copper and mask files carry small drill marks. KiBot does not write them. I compared the retained files:

| File | Lines only in the kicad-cli file |
|---|---|
| `trial-F_Cu.gbr` | 2 drill apertures and 6 `D03` flashes |
| `trial-B_Cu.gbr` | 2 drill apertures and 6 `D03` flashes |
| `trial-F_Mask.gbr` | 1 drill aperture, its selection and duplicate flashes at existing openings |
| `trial-B_Mask.gbr` | 1 drill aperture, its selection and duplicate flashes at existing openings |

The cause is in the saved board plot parameters. `results/final/trial.kicad_pcb` holds `(pcbplotparams (drillshape 1))`. The installed bindings define `DRILL_MARKS_NO_DRILL_SHAPE = 0`, `DRILL_MARKS_SMALL_DRILL_SHAPE = 1` and `DRILL_MARKS_FULL_DRILL_SHAPE = 2`. The export command uses `--board-plot-params`, so it takes the saved value. `kicad-cli pcb export gerbers` has no drill-mark flag. The installed KiBot calls `po.SetDrillMarksType(0)` in `out_gerber.py`.

Codex measured the decisive result offline. A temporary copy of the frozen board with `drillshape 0` gives exports that equal the supplemental KiBot files on all four disputed layers, after date and generator normalization. That measurement kept the board X2 attributes on. The Pi-3 repair turns X2 off on both tools, so the T11 comparison must use the same neutral X2 state. The copper difference is 6 additional flash commands per layer, including the two non-plated mounting holes. The mask difference is an aperture declaration, its selection and duplicate flashes at openings that the mask already has. It is not by itself extra mask geometry.

The correct neutral setting is no drill marks. The separate Excellon files define the holes. The trial must set `drillshape 0` on the saved board before the final exports, keep `--board-plot-params`, and record the setting in the command table. Do not add a KiBot `drill_marks` option and do not change the contract schema. Regenerate the exports, the T11 comparison and the draft package from the corrected revision. Update the PCB hash, the interface binding, the input hashes and the evidence. Refresh the full clean reports for the exact new PCB bytes. Preserve the earlier outputs as history.

## 5. Exact remaining acceptance work

1. Correct E1. Add the narrow copper-order and file-function check against the two-layer mapping. Read the one `G04 #@! TF.FileFunction` comment per Gerber (E6). Do not use the job file as the source, because it cannot detect swapped file bytes. Add the swapped-copper negative test. Regenerate the `fab.layer_order` evidence, the package hashes and the validation report.
2. Correct E2. Reject repeated placement references. Add the two row-order negative tests. Regenerate the `fab.export_inventory` evidence, the package hashes and the validation report.
3. Supply the E3 diagnostics for the 2 preservation boards, the U2 cross-source and same-source boards, and the valid U3 boards A, B, C, F and G. Do not repeat a GUI run. State the exact expected C2 parity difference for the sentinel and default-restore states.
4. Correct E4. Add the classification for `gate3_fpr1_replace_off`. Correct the `export_final.sh` suffix comment and the command table. Change no historical result bytes.
5. Correct Pi-1. Regenerate the 3 stale comparison files with the frozen reader, or label them as historical. Update the manifest.
6. Correct Pi-2. Add the T13 host commands and exit codes, or the retained output that gives the same result.
7. Correct E6. Set and test `(drillshape 0)`, `(usegerberattributes no)` and `(usegerberadvancedattributes no)` in the saved board before the final exports. Keep `--no-x2` as explicit intent. Set `use_gerber_x2_attributes: false` and `use_gerber_net_attributes: false` in the T11 KiBot config. For E1, read the one `G04 #@! TF.FileFunction` comment per Gerber, compare it with the fixed nine-layer mapping and the board copper order, and reject a missing, duplicate or incorrect declaration and any active `%TF`, `%TA`, `%TO` or `%TD` command in all nine files. Keep the neutral schema unchanged.
8. Fold the supplement results into the final record and name the supplement manifest. The supplement is still active, so do not freeze it until the D1 deletion-off experiment and the E3 diagnostics are complete.
9. Correct E5. Set `drillshape 0` on the saved board before the final exports. Keep `--board-plot-params`. Record the setting in the command table. Regenerate the final board, the clean reports for the exact bytes, the exports, the T11 comparison, the interface binding, the input hashes, the package and the manifest. Do not add a KiBot option and do not change the contract schema. Preserve the earlier outputs.
10. Add the T2 three-column table to the record: contract setting, CLI option, value used. Include the drill-mark and X2 settings. The current mapping lives in the `export_final.sh` header and the setup checkpoint. It is not a table in the record.
11. Supply the native D1-removal option experiment with deletion off, or identify its retained evidence. Revision 4 asks for both option states. The frozen evidence shows deletion on only.
12. Keep the U1 to U6 status rows explicit. U2 fails its no-edit gate. U3 stays experimental. U5 stays untested. U6 keeps its negative result. Do not imply support for an omitted path.

No supplier qualification, general parser, new engine or unrelated suite is necessary.

## 6. Limits

- The preservation test supports the reader and the GUI update for the arc, the via and the zone. It does not test a zone refill during a GUI update. The fixture has no straight track segment. The native repeat boards supply the separate segment evidence.
- The U2 and U3 results come from one pair of runs each. U3 is one link method. The untested U3 edits stay untested.
- The supplement has one run of each probe. The sheet-move result can differ with another option state.
- I ran no container command for the supplement and no GUI run. I used the existing image, temporary copies, host scripts and retained reports only.
