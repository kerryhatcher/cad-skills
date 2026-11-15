# B5 native checkpoint review: Pi

Date: 2026-11-14.

**Decision: checkpoint 2 not accepted yet. Five narrow evidence gaps remain.**

The identity reader and the expectation method are sound. The six valid gate edits give the expected differences exactly. The saved-board and GUI option evidence is present.

The checkpoint is not final B5 acceptance. Five evidence gaps must be corrected before acceptance of this part.

**1. Reviewed identity**

| Item | Value |
|---|---|
| Manifest | `docs/reviews/b5-native-files.sha256` |
| Manifest SHA-256 | `ab732d880ffb6cecf83b0be90875ae5bfbdb068b57a68f5266cb24c69ea9905c` |
| `scripts/identity.py` SHA-256 | `1c4392c40c8fd05e02891ed627104d3a22fa0fae475d35ed867e645248f2b6df` |
| `scripts/gate_expect.py` SHA-256 | `6b1633982f56c10ead1b04de1a729fb23ab8dacdd090235e462d8569f8003513` |
| `scripts/trial_env.sh` SHA-256 | `31e2b50226ed256a8ae07cd39dfbf24f8b5bea2d26b426ab1cdc7c378b892d63` |
| `scripts/edit_native.py` SHA-256 | `7ad0256bbd99f9e47f4fec94eade6b1034121b28cf923851fc4ef6a07ffa565a` |
| `tests/test_trial_identity.py` SHA-256 | `adcdc85bb9a91040b325febf6efcde9040627b2aa7a2a597dde9a1c61d63452f` |

All 67 manifest entries passed before the focused probes and after the focused probes. The files did not change.

**2. Accepted points**

- The identity reader handles footprints, segments, arcs, vias, zones and `gr_*` graphics. It lists the ignored forms. An unknown top-level form gives `identity.unparsed_class` and exit 3.
- The comparison is exact in both directions. An unlisted difference fails. A listed difference that does not occur fails.
- The expectation generator reads the baseline snapshot and the edit definitions. It does not read an after-board. A regeneration from the frozen baseline reproduced the six gate-edit expectation files.
- The six valid gate edits give `status: equal`: `gate_none`, `gate2_reorder`, `gate2_value`, `gate2_addc2`, `gate2_removed1`, `gate2_fpr1`.
- The expected files for those edits contain no segment difference. A changed or removed track would be an unexpected difference. Routing objects are therefore preserved in the tested segment set.
- Each result directory holds `trial.kicad_pcb`, `after.snap.json`, `compare.json` and `gui_summary.json`.
- The GUI summaries record the requested options and the measured before and after states, the KiCad exit code, and the board hashes before and after.
- The invalid first attempts are documented in the checkpoint record. Their result files stay.
- `uv run tests/test_trial_identity.py` passed 9/9.

**3. Gap A: `gate()` returns success for every run**

Location: `scripts/trial_env.sh`, the `gate` function.

The function computes `compare_rc` and writes it to `gates.txt`. It then runs `return 0` unconditionally. A caller cannot distinguish a supported gate pass from an exploratory expected failure.

Root observation: distinguish exploratory expected failures from the supported gate runner.

Correction:

1. Return `compare_rc` from the supported gate function.
2. Use a separate function or an explicit option for an exploratory run. Do not let an exploratory failure report success.
3. Record the expected file that each run uses.

**4. Gap B: no per-board DRC or parity findings for phase A**

The manifest holds `results/native/baseline_drc.json` only. It does not hold DRC or schematic parity results for the saved phase-A boards (`gate_none`, `gate2_*`, `probe_*`).

The proposal asks for the full DRC exit code and the findings of each phase-A board, even when the parity section is empty. The checkpoint record gives the baseline DRC result (1 violation and 2 unconnected items). It gives the GUI dialog result ("Total warnings: 0, errors: 0") for the runs. The dialog result is not a DRC or parity result.

Correction:

1. Run `kicad-cli pcb drc` and the schematic parity check on each saved phase-A board.
2. Record the exit code, the violation list, the unconnected list, and the parity section for each board.
3. Add those files to the manifest. Do not hide a non-empty result.
4. Keep the baseline result. It is not a substitute for the per-board results.

**5. Gap C: via, zone and arc coverage is absent**

The baseline and every saved board have 0 vias, 0 zones and 0 arcs. The baseline has 6 segments and 1 graphic.

The identity reader has code for vias, zones and arcs, but no real saved output exercises it. The identity test file has no via, zone or arc case. The reader's behavior for those classes is therefore unverified.

Do not make a preservation claim for vias or zones without saved KiCad evidence.

Root condition: examine the absent via and zone coverage before final acceptance.

Correction:

1. Add a text fixture with one via, one zone and one arc. Test snapshot and compare for each class.
2. Test a changed via, a changed zone polygon, and a changed arc. Test a listed removal by UUID.
3. Add one real saved board that contains a via and a zone. Record its source. Saved KiCad evidence is necessary before a preservation claim for vias or zones.
4. Keep the small fixture scope. This is not a general parser.

**6. Gap D: replace-off expectation and comparison are not recorded correctly**

`scripts/gate_expect.py` writes `none`, `reorder`, `value-r2`, `add-c2`, `remove-d1`, `footprint-r1` and `rename-c1`. It does not write `footprint-r1-replace-off.json`, although that file is in the frozen expected set. Its origin is not recorded.

The `gate` function chooses the expected file by operation name only. For `gate2_fpr1_replace_off` it uses `expected/footprint-r1.json`, the replace-on expectation. The run applied no footprint change. The frozen `compare.json` therefore shows `status: different` with three missing differences.

The correct comparison is a replace-off expectation with no differences. A focused probe compared the replace-off snapshot against an empty expectation: `status: equal`, 0 observed, 0 expected.

Correction:

1. Add `footprint-r1-replace-off.json` to `gate_expect.py` as an empty difference list, or record its manual origin.
2. Make the gate runner take the expected file or a label that includes the option state. Do not select the expectation by operation name alone.
3. Record the correct comparison for the replace-off run. Do not leave the wrong comparison as the only artifact.

**7. Gap E: invalid runs are not self-labeled**

The invalid runs `gate_reorder`, `gate_value` and `gate_addc2` remain in `results/native/`. Their compare files show `equal`, `different` and `different`. The checkpoint record labels them invalid, but the artifacts themselves do not.

Correction:

1. Add an explicit invalid marker to each invalid run directory, or move them under `results/native/invalid/`.
2. Keep the record note. The marker prevents a later reader from counting an invalid run as a gate result.

**8. Focused probes and limits**

- I regenerated the expected files from the frozen baseline snapshot with `scripts/gate_expect.py`. The six gate-edit files matched. Only `footprint-r1-replace-off.json` was absent from the generator output.
- I compared the replace-off snapshot against an empty expectation on a temporary file. Result: equal.
- I read the compare statuses of the valid and invalid runs.
- I counted via, zone and arc forms in the saved boards. All are zero.
- I used host scripts and temporary output files. I did not rebuild or pull an image. I did not edit an implementation file.
- This checkpoint does not cover the repeat gate runs, the remaining limit probes, U2 to U6, the final clean board, the exports, the simulation or the draft package.

**9. Verdict**

Checkpoint 2 is not accepted yet. Correct gaps A to E. Gaps A and B are necessary before the gate evidence is trustworthy. Gaps C and D are necessary before the identity evidence is complete. Gap E is a clarity correction.

The checkpoint is a focused step. Final B5 acceptance still needs the repeat gates, the remaining paths, the clean board, the exports, the simulation and the draft package.

This review changes only this report. It makes no implementation edit.
