# B5 correction review: Codex

Date: 2026-11-14 UTC.

**Decision: accept B5 with its explicit limits.** E1–E6 and Pi-1/Pi-2 are satisfied. No blocking correction remains. The supported native path covers six edits. The replace-off run remains a separate option experiment.

I kept the accepted setup, identity reader, and supplemental observations closed. I changed only this report.

## Final acceptance boundary

Manifest: `docs/reviews/b5-correction-files-v2.sha256`, 1154 entries.

SHA-256: `00297fd7caf708b3f8deaa58202c1cf6ca1bfebfba3c826244f12ff85cb8c188`.

All 1154 entries pass. The replacement manifest differs from the first correction manifest in one line only. That line records the authorized U1 count correction in `b5-correction-claude.md`.

The first manifest hash was `86278c0b6565be2f8ed8ba269caba8445cdef5453260b589f9e15fa337ae1a58`. All 1154 entries passed before the report correction. After that correction, its other 1153 entries still passed. The final v2 manifest records the corrected report hash:

`4a345c13c3e5be10f8f810ecffc4ad92715c1d532e032bf50a393bc91acea5ca`.

The implementation did not change during review. The main trial's only five changed entries are the authorized export reader, package builder, export script, layout script, and export tests. All original main paths remain in the complete manifest. All 325 supplement entries retain their accepted hashes.

| Accepted corrected artifact | SHA-256 |
|---|---|
| `results/final_r2/trial.kicad_pcb` | `56f794242345dd3950d5bd066bea6f2a1d1740c5adfc7152651667210297bd94` |
| `results/final_r2/draft_parent/package/manifest.json` | `a4590a518f7e687147e54d3c5a75913f55bddd7810e9ca5357d6e3cffa267dfe` |

Artifact paths start at `examples/pcb-trial/`.

## Correction decisions

| Item | Accepted result |
|---|---|
| E1 | The reader compares one file-function comment per Gerber with the fixed layer functions and the saved board's copper order. Passed `fab.layer_order` evidence uses that result. Filenames alone no longer establish layer order. |
| E2 | The reader compares exactly seven placement rows and rejects repeated references. Identical and conflicting duplicates fail in both row orders. |
| E3 | The accepted supplement supplies the 13 full diagnostic records with source hashes and tool exits. They remain intermediate-board evidence. |
| E4 | The appended classification keeps replace-off separate from supported matching-source gates. The corrected export comment explains the measured `.gbr` names. The correction report now states six supported edits. |
| E5 | The final saved board uses `drillshape 0`. The corrected copper and mask output agrees with KiBot's no-mark output. |
| E6 | The final board uses `usegerberattributes no` and `usegerberadvancedattributes no`. All nine Gerbers contain no active attribute commands. Their file functions remain ordinary `G04 #@!` comments. The new KiBot config explicitly disables X2 and net attributes. |
| Pi-1 | Three separate current-reader comparisons reproduce exactly. The original comparisons retain their historical bytes. Their result counts and statuses remain unchanged. Added-footprint records now include values. |
| Pi-2 | The record retains the T13 host build, validation, and negative-test commands. It records their exits as 0, 0, and 1. The validation outputs agree. |

The neutral contract remains `x2: false`. The repair tests effective saved settings and generated files. It does not depend on CLI flags alone. No schema expansion occurred.

## Focused measurements

`uv run tests/test_trial_exports.py` passed 16/16, exit 0. The tests cover swapped copper, missing/duplicate/incorrect file functions, active attribute commands, saved settings, and duplicate placement rows. Existing drill, placement, and RC regressions also pass.

I independently called the plot-setting function with each setting absent or repeated. All six malformed inputs raised the expected error. The function does not silently omit a necessary setting.

I compared the first and corrected final boards. Their text differs only in the three authorized plot settings. Their identity comparison is equal. Thus, this correction does not change the circuit, placement, or routing.

I recomputed all seven export results on the corrected revision. All pass. I also recomputed the three Pi-1 results from the retained snapshots. All match their new comparison files.

The complete KiBot comparison returned an empty difference list and exit 0. I separately compared all nine normalized Gerber files. All agree. The comparison also confirms the drill split and placement values. The fixed trial expectations remain the primary export test.

I rebuilt the project and draft package in a temporary directory with the corrected builder. The host build returned 0. All 38 generated project and package files equal the retained corrected files byte for byte.

The fresh draft validation returned 0 with no findings. A temporary `qualified` claim returned 1 with `pkg.false_qualification` and `pkg.reasons_required`. The retained package stays `draft`, with supplier evidence pending.

The reproducible build binds the package PCB, interface hash, input hashes, outputs, and evidence to the corrected board bytes. The layer-order report contains the passed file-function comparison. The inventory report contains the saved-setting, attribute, and exact-placement results.

I ran fresh full ERC and DRC commands on a temporary copy of the corrected revision. Both used `--exit-code-violations --severity-all --format json`. DRC also used `--schematic-parity`. Both returned 0. The reports have zero ERC violations, DRC violations, unconnected items, and parity findings. The PCB hash did not change.

Container measurements used the existing image `d881df4ef3e2ec76995f4070596550db118b23e7f6db9017f09a418c44c4b1c2` with `--pull=never --network none`. No GUI repeat, image build, image pull, repository relabel, or unrelated suite occurred.

The accepted RC positive and negative results remain unchanged. The focused export suite also confirms the corrected revision's retained RC logs and fixed assertion. No repeated simulation was necessary.

## Explicit completion limits

- U1 supports the six measured native edits for this source, fixture, image, and machine. The option and limit results remain separate.
- U2 fails the no-edit gate. The observed SKiDL schematic connectivity failure prevents a supported-regeneration claim.
- U3 remains experimental. The retained no-edit, sentinel, restore, and deletion observations do not establish its untested edit gates. Its KiCad process exit remains unmeasured.
- U5 remains untested. U6 retains its measured negative result. No new API support claim follows.
- The object-preservation results do not establish zone refill during a GUI update. Other machines and KiCad versions remain untested.
- The STEP file lacks the stated component models. The package remains a neutral bare-board draft with no supplier qualification or assembly evidence.

These explicit limits do not prevent B5 completion. They define the boundaries for later batches. B5 supplies a clean reference board and validated draft package. It does not supply a qualified supplier release.
