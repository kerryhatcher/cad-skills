# B5 trial review: Codex

Date: 2026-11-14 UTC.

Decision: **B5 remains incomplete.** I accept the measured native repeat results, object preservation, final clean board, and RC results within their limits. Two export evidence defects need correction. Some agreed evidence remains absent.

I kept the accepted setup and identity reader corrections closed. I changed only this report.

## Reviewed bytes

The manifest is `docs/reviews/b5-files.sha256`. All 707 entries passed before and after this review. The manifest hash stayed unchanged:

`86395ff3fa7692f3cbf2ba65ee898be9cc7c443f08ca13419b162441406caf60`

The agreed revision-4 proposal hash also stayed unchanged:

`458ff984c4a552f2a7a339ec937f6a066b187bb61ea2c210b3cfdba8dea5c0f6`

| File | SHA-256 before and after |
|---|---|
| `results/final/trial.kicad_pcb` | `ce5e0f3bd6a68b69ffe3a4982f3d88e66d828e8c5570bcc1bba00d63850c1973` |
| `results/final/trial.kicad_sch` | `a07579562689394465aea162c87d6a4d00d241162579c584d83b78bfa8e6fd98` |
| `scripts/check_exports.py` | `7c469b1ae6ae55f7c02745748bc7fe2b617faf54d66bb2957d74619d9abca45b` |
| `scripts/build_draft_package.py` | `ed63a8dbbb9f6d6952d0013954d86bf6e4d3db55e837872e0c3a4e164d63939f` |
| `scripts/export_final.sh` | `037288fa62372002fb24c0902aa441efb3d58d826edbac230abb5dc4e9fc3c70` |

Paths in this table start at `examples/pcb-trial/`.

## Concrete corrections

### E1. Filename evidence does not establish layer order

`scripts/build_draft_package.py:138` makes passed `fab.layer_order` evidence from `gerber.layer_set`. That test compares filenames only.

Reproduction: copy `results/final/export` to a temporary directory. Exchange the bytes of `trial-F_Cu.gbr` and `trial-B_Cu.gbr`. Keep their names. `check_exports.check()` still reports `gerber.layer_set: pass`. The package builder uses this result for `fab.layer_order: pass`.

This is incorrect passed evidence, even in a draft package. A filename inventory does not establish the copper side or order.

Minimum correction: keep `fab.layer_order` pending with an explicit reason until a small trial-specific comparison supports it. Alternatively, compare the saved board's copper order and the Gerber file-function declarations with the intended two-layer mapping. The existing drill report also records L1 F.Cu and L2 B.Cu. Bind the evidence to the applicable files. Add a swapped-copper negative test if the builder retains a passed result. No general Gerber parser is necessary.

### E2. Duplicate placement rows can pass

`scripts/check_exports.py:87` assigns each CSV row to a dictionary entry by reference. A later row replaces an earlier row.

Reproduction: copy the export directory. Insert an extra C1 row before the correct C1 row. Change its X coordinate from `125.000000` to `999.000000`. Keep the correct row afterward. The file now has eight placement rows. The reader still reports `placement.rows: pass`.

Minimum correction: reject a repeated reference before dictionary assignment. Compare the row count with the seven expected references. Add duplicate-identical and duplicate-conflicting regressions. Both row orders must fail. Keep the existing position, rotation, and side comparisons.

### E3. Some phase-A diagnostics remain absent

The repeat native gates retain full DRC and parity records. The new `vz_preserve`, U2 same-source, and valid U3 saved boards do not.

Revision 4 asks for full DRC findings for each phase-A board. It also asks for a parity result for each U4 input. GUI exit 0 and an identity comparison do not supply those results.

Minimum correction: add diagnostic records for the two preservation boards, the U2 A/B boards, and valid U3 states A/B/C/F/G. Record source hashes, command options, tool exit codes, and full findings. Keep invalid U3 D/E as historical attempts. Use the matching source for ordinary U3 states. State the exact expected C2 difference for the sentinel and default-restore states. Do not repeat the GUI operations.

For U3, distinguish the shell helper's exit 0 from the KiCad process exit. The helper currently copies the board without an explicit KiCad exit measurement. State this limit if that process result is unavailable.

### E4. Correct two result labels and one command comment

The replace-off comparison correctly reports `equal`. However, `gate3_fpr1_replace_off/drc.json` has two parity findings. The log labels this run `kind=supported`. Keep this as an option experiment, not a supported matching-source gate. An appended classification can correct the record without changing historical bytes.

`scripts/export_final.sh:6` says `suffixes -> Protel extensions`. The command and measured output use `.gbr` names. The draft export settings also specify `.gbr` suffixes. Correct the comment and command table to describe those names. No export format change is necessary.

## Measured results that I accept

I recomputed all seven repeat snapshots from their saved boards. All match the stored snapshots. I compared them with the baseline and the accepted expectations. All seven comparisons are equal. The six supported edits have empty parity sections. Their intermediate DRC findings remain visible. The replace-off experiment retains its two expected parity findings.

The earlier valid outcomes and the new repeat outcomes support the six native edits. Invalid historical attempts remain excluded. This evidence applies to this source, fixture, image, and machine.

The two preservation snapshots each contain one arc, one through-board connection object (`via`), and one zone. The no-edit update has no difference. The value update changes only R2 from `10k` to `22k`. UUIDs, geometry, and nets of those objects remain equal. These saved GUI results extend the earlier reader-only coverage. They do not prove zone refill during a GUI update. The fixture contains no straight track segments. The native repeat boards supply the separate segment-preservation evidence.

I ran focused commands in temporary copies with this existing image:

`d881df4ef3e2ec76995f4070596550db118b23e7f6db9017f09a418c44c4b1c2`

All container runs used `--pull=never --network none`. No image build, image pull, repository relabel, or GUI repeat occurred.

- Full `kicad-cli pcb drc --schematic-parity --exit-code-violations --severity-all --format json` returned 0. The report has zero violations, unconnected items, and parity findings.
- Full `kicad-cli sch erc --exit-code-violations --severity-all --format json` returned 0 with zero violations.
- Fresh ngspice runs returned 0. The fixed assertion passed at 2.0860 V and failed at 1.2054 V for 220 nF. The assertion exits were 0 and 1. The target remained 2.086 V at 1.000 ms, with 1 percent tolerance.
- `uv run tests/test_trial_exports.py` passed 9/9. E1 and E2 identify gaps beyond those tests.
- `uv run contracts/validate.py --project .../draft/project --package .../draft/package --json` returned 0 without findings.

The final board repair corrects D1 field and pad angles. The first failed DRC report remains as history. The fresh full reports support the final clean-board result.

The package explicitly stays `draft`. Supplier evidence remains pending. This is the correct qualification boundary. A validator pass establishes the contract result. It does not repair the unsupported passed layer-order evidence in E1.

## U2 and U3 conclusions

The U2 A/B source hashes match fresh SKiDL runs G/H. Thus, the new test uses the same source path. Its saved snapshots show five pad-net changes without footprint addition, removal, or unlinking.

I compared the four retained KiCad XML pin partitions. Run G matches the intended partition. Runs E/H/I do not. Their SKiDL netlists have the same SHA-256. These results support a measured connectivity failure in three of four successful schematic generations. They do not establish a UUID-replacement failure or a general failure rate. U2 does not pass the no-edit gate.

All seven U3 snapshots match their saved boards. A to B has no difference. B to C adds C2. C2 has no pad nets. The default restore retains C2 with a null path. The delete-enabled restore F equals B. These facts support netlist consumption and the observed option behavior. U3 remains experimental. It has no complete edit gate, repeat gate, or clean-parity claim.

## Exact remaining acceptance work

1. Correct E1 and E2. Regenerate affected reports, evidence, package hashes, and validation results. Add only their focused regressions.
2. Supply E3 diagnostics. Correct the E4 labels and comment. Preserve historical result bytes.
3. Complete T5 with a defective schematic that produces the intended ERC finding. Record the finding and nonzero exit with `--exit-code-violations`.
4. Complete T6 with a defective SKiDL circuit. Record `ERC()` findings and the process exit separately.
5. Complete T11. Compare KiBot's layer set, drill split, and placement columns with the independent trial expectations. Record differences.
6. Complete the two agreed native limit probes: move R2 to another sheet, and remove then re-add D1. A measured identity failure is an acceptable limit result.
7. Supply the native D1-removal option experiment with deletion off, or identify its retained evidence. Revision 4 specifies both option states. The frozen evidence shows deletion on only.
8. Keep explicit U1–U6 status rows. U2 fails its no-edit gate. U3 stays experimental. U5 stays untested. U6 retains its negative result. Do not imply support for the omitted paths.

No supplier qualification, general parser, new evidence engine, or unrelated mechanical suite is necessary for these corrections.

## Supplemental context: drill-mark setting

Date: 2026-11-14, 06:43 UTC.

I read `docs/reviews/b5-supplement-claude.md` as active context. This appendix does not accept a frozen supplement. The supplemental diagnostic files remain active.

### E5. Use no drill marks for the manufacturing Gerbers

The CLI/KiBot difference has a measured setting cause. The final board stores `(drillshape 1)` under `pcbplotparams`. The export script selects `--board-plot-params`. The installed CLI help says that this option uses the board's Gerber plot settings.

The installed KiCad bindings define these constants:

- `DRILL_MARKS_NO_DRILL_SHAPE = 0`
- `DRILL_MARKS_SMALL_DRILL_SHAPE = 1`
- `DRILL_MARKS_FULL_DRILL_SHAPE = 2`

The installed KiBot source, `/usr/lib/python3/dist-packages/kibot/out_gerber.py:65`, explicitly calls `po.SetDrillMarksType(0)`. Its Gerber output does not use the `drill_marks` option of drawing formats.

I exported two temporary copies of the frozen final board with the existing offline image. One retained `drillshape 1`. The other used `drillshape 0`. Both exports returned 0. I kept the same layer list, `--no-x2`, `--precision 6`, and `--board-plot-params`.

After the existing date/generator normalization, the zero-mark exports equal the supplemental KiBot files for all four disputed layers:

| Layer | Lines present only with `drillshape 1` |
|---|---|
| F.Cu | 6 |
| B.Cu | 6 |
| F.Mask | 2 |
| B.Mask | 2 |

The copper differences include additional flash commands at the two non-plated mounting holes. The mask differences contain an aperture declaration and selection. They do not, by themselves, show additional mask geometry. Thus, the record must not describe all four differences as equivalent geometry changes.

**Decision:** use no drill marks for these neutral manufacturing Gerbers. The separate Excellon files define the holes. Do not accept the copper difference as harmless tool variation. Drill marks can serve a drawing, but they must not add drawing marks to these manufacturing layers.

Minimum correction: explicitly set the saved board's Gerber plot setting to `drillshape 0` before the final exports. Retain the command's explicit use of the board plot settings. Record this setting in the trial's command table. Do not add a nonexistent Gerber `drill_marks` option to KiBot.

Then regenerate the CLI Gerbers, the T11 comparison, and the draft package from the corrected revision. Update its PCB hash, interface binding, input hashes, and evidence. Refresh the full clean reports for those exact PCB bytes. Preserve the earlier outputs as history. This correction needs no contract schema change or general Gerber parser.

The supplemental T5, T6, and limit-probe statements remain context until their frozen review. The supplement's final incomplete-status sentence does not close E1–E5 or the remaining evidence work above.

## Supplemental context: effective X2 settings

Date: 2026-11-14, 06:45 UTC.

### E6. Saved plot settings override the X2 CLI flags

I confirm the lead's contract finding. The neutral contract stays `x2: false`. The frozen Gerbers contain active `%TF` attributes, although the export command includes `--no-x2`.

I ran three exports in temporary copies with the same offline image. All used `--board-plot-params`, the same nine layers, precision 6, and drill marks off. All returned 0.

| Saved attribute settings | CLI flags | Active attribute commands in F.Cu |
|---|---|---|
| Both `yes` | `--no-x2` | 52 |
| Both `no` | `--no-x2` | 0 |
| Both `yes` | `--no-x2 --no-netlist` | 52 |

The settings are `usegerberattributes` and `usegerberadvancedattributes`. The measured result confirms that CLI flags alone do not establish the effective settings for this command.

With both settings off, the file-function line is:

```text
G04 #@! TF.FileFunction,Copper,L1,Top*
```

This is a comment, not the active `%TF.FileFunction,Copper,L1,Top*%` command. Thus, E1 can retain bounded layer identification after X2 is off.

**Repair agreement:** set and test these saved settings before the corrected exports:

```text
(drillshape 0)
(usegerberattributes no)
(usegerberadvancedattributes no)
```

Keep `--no-x2` in the CLI command as an explicit statement of intent. Set KiBot's `use_gerber_x2_attributes: false` and `use_gerber_net_attributes: false` explicitly. KiBot currently defaults both options to true.

Test the generated files, not only the saved fields or command text. All nine manufacturing Gerbers must contain no active `%TF`, `%TA`, `%TO`, or `%TD` attribute commands. Ordinary `G04 #@!` comments remain compatible with the selected output.

For E1, read the single file-function comment from each generated file. Compare it with the trial's fixed layer mapping. F.Cu must identify `Copper,L1,Top`. B.Cu must identify `Copper,L2,Bot`. Compare the other seven roles with their corresponding fixed functions. Reject missing, duplicate, or incorrect function declarations. The swapped-copper regression must fail. This is a bounded header comparison, not a general Gerber parser.

Regenerate the affected exports and exact-byte evidence as stated in E5. Keep the neutral contract unchanged. No schema expansion is necessary.
