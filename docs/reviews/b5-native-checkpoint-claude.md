# B5 checkpoint 2 record (Claude): native identity gate edits

Date: 2026-11-14 (runs 05:44 to 05:54 UTC, from the step log clock).

Scope: the native path with input U1, the update mechanism U4, and the identity reader. I made no commit, no push, no image rebuild, and no change to the accepted setup files (`b5-setup-final-files.sha256` still verifies, 16 of 16). This is a focused checkpoint, not the final trial record.

**1. What is frozen for this review**

`docs/reviews/b5-native-files.sha256` (67 files, SHA-256 `ab732d880ffb6cecf83b0be90875ae5bfbdb068b57a68f5266cb24c69ea9905c`): the identity reader, the layout script, the native edit script, the expectation generator, the GUI script, the environment helper with the `gate` function (`scripts/trial_env.sh`), `tests/test_trial_identity.py`, the real-output fixture, and every result file under `examples/pcb-trial/results/native/`.

Key hashes: `identity.py` `1c4392c4…`, `gui_update.py` `c6e3c897…`, `edit_native.py` `7ad0256b…` (after the fix in section 5), `tests/test_trial_identity.py` `adcdc85b…`. `uv run tests/test_trial_identity.py`: exit 0, 9/9 (`identity_tests_002.out`).

Scratch paths: trial copy `<scratchpad>/b5/trial/out/`, logs `<scratchpad>/b5/logs` (`gates.txt`, `steps.txt`).

**2. Method (what keeps the expectation independent of the output)**

1. The baseline is the board that KiCad saved after the first scripted update (run `U4_U1_c_110`), then `scripts/layout.py` (unequal positions, `D1` rotated 180 degrees, straight tracks). The baseline is intermediate experiment data. Its DRC (`G_baseline_drc_112`) gave 1 violation and 2 unconnected items. These are recorded, and not hidden.
2. `scripts/gate_expect.py` writes each expected-difference file from the BASELINE snapshot and the edit definition only. It never reads an after-board. The files were written before the runs (`results/native/expected/`).
3. `scripts/edit_native.py` makes the text edit of the schematic. `scripts/gui_update.py` runs the update with measured option states. `identity.py compare --expect` requires equality both ways: an unlisted difference fails, and a listed difference that does not occur fails.

**3. Measured results (native path, input U1, mechanism U4, baseline to saved board)**

All runs: KiCad exit code 0, process ended normally, dialog "Total warnings: 0, errors: 0".

| Run (log ID) | Edit | Options measured from the screen | Observed / expected differences | Result |
|---|---|---|---|---|
| `gate_none` (`GUI_gate_none_113`) | second update, no edit | relink off, replace on, delete off | 0 / 0 | equal |
| `gate2_reorder` (`GUI_gate2_reorder_122`) | reorder `R2` before `J1` in the source | same | 0 / 0 | equal |
| `gate2_value` (`GUI_gate2_value_117`) | `R2` value 10k to 22k | same | 1 / 1 (`R2` value) | equal |
| `gate2_addc2` (`GUI_gate2_addc2_118`) | add `C2` with labels | same | 1 / 1 (one new footprint, pads `/N_RC`, `/GND`) | equal |
| `gate2_removed1` (`GUI_gate2_removed1_119`) | remove `D1` and its labels | relink off, replace on, **delete on** | 1 / 1 (`D1` removed) | equal |
| `gate2_fpr1` (`GUI_gate2_fpr1_120`) | `R1` footprint 0603 to 0805 | relink off, replace on, delete off | 3 / 3 (library ID, two pad positions) | equal |

Observations that the expected files stated before the run and the runs confirmed: the removal of `D1` leaves the tracks unchanged (no routing object changed). The footprint change keeps the footprint UUID, the position, and the pad UUIDs. Only the library ID and the two pad positions change.

**4. Dialog option results**

| Run | Option state | Result |
|---|---|---|
| `gate2_fpr1_replace_off` (`GUI_gate2_fpr1_replace_off_121`) | replace **off** | 0 differences. The footprint change is not applied. "Replace footprints with those specified by symbols" is necessary for the footprint-change gate edit. The comparison against the `replace off` expectation (empty) is equal. The table row `different` in `compare.json` of that run is the comparison against the replace-on expectation that the helper `gate` hard-codes by edit name. It is a helper limit, not a result. |
| `gate2_removed1` | delete **on** | The footprint `D1` is removed. The remove-D1 gate edit needs "Delete footprints with no symbols". The default (off) was not run for this edit in this checkpoint. |
| Limit probe `probe_rename_relink_off` (`GUI_probe_rename_relink_off_123`) | relink off (default) | Rename `C1` to `C9`: 1 difference, the reference changes in place and the UUID and the path stay. Equal to the expected hypothesis. |
| Limit probe `probe_rename_relink_on` (`GUI_probe_rename_relink_on_124`) | relink **on** | Rename `C1` to `C9`: the old footprint `C1` loses its schematic path, and a NEW footprint `C9` is added with the pad nets. Identity is NOT kept. This is a measured limit: re-linking by reference breaks identity for a renamed reference. |

Dialog labels and defaults were recorded at the first GUI run (`b5-work-state-claude.md`). The default state is: relink off, replace on, delete off, override locks off, update fields on.

**5. Failed or invalid first attempts (kept)**

| Item | What happened |
|---|---|
| `GUI_gate_value_115`, `GUI_gate_addc2_116`, and the first reorder `GUI_gate_reorder_114` | Invalid. `edit_native.py` had a bug: its `block()` function returned an empty span, so each edit left the schematic unchanged. The runs saw no change (0 observed), and the first reorder was "equal" only because nothing was edited. I fixed `block()` (a quote-aware span) and reran all edits as `gate2_*` with new log IDs. The old results stay in `results/native/gate_*` and are labeled invalid. |
| `GUI_gate_none_113` | Valid. The no-edit run does not depend on the edit script. |
| Earlier GUI runs | `U4_U1_a_107` (stopped at the first-run dialog), `U4_U1_a_108` and `U4_U1_b_109` (a checkbox reader bug toggled "replace" off) are in the setup checkpoint record. |

**6. Artifact paths and hashes**

Each `results/native/NAME/` directory holds `trial.kicad_pcb` (the saved board), `after.snap.json`, `compare.json` and `gui_summary.json`. The baseline files are `results/native/baseline.kicad_pcb`, `baseline.snap.json`, `baseline_drc.json`, and the expected files are in `results/native/expected/`. The full hashes are in `b5-native-files.sha256`. The first 12 characters of the saved-board hashes: `gate2_addc2` `68b9a25f0373`, `gate2_fpr1` `4aadf3e79a74`, `gate2_removed1` `649465e1a6bd`, `gate2_value` `702c9d567855`, `gate2_reorder` and `gate_none` `0218820a118d` (the same bytes as the baseline after a no-op update), `probe_rename_relink_off` `60e0e4e1d030`, `probe_rename_relink_on` `771aa3a3ce03`.

**7. Result against the gate, and limits**

- Native path, input U1, mechanism U4: all six gate edits give the expected differences exactly, once each. The final B5 gate needs the supported gates twice in a row (a repeat run for each edit). I have not repeated them yet.
- Not run yet: the limit probes "move `R2` to another sheet" and "remove and add `D1` again", the default option state (delete off) for the remove edit, and relink on for the other edits.
- U1 and U4 have a measured result. U2 (SKiDL schematic), U3 (netlist import), U5 (IPC API), U6 (`pcbnew` updater) have none yet.
- Tracks, vias and zones: the baseline has 6 straight segments and no via or zone, so the reader's zone and via paths are tested only by text fixtures.
- The reader was tested on real KiCad output for one board (`u1_saved_by_kicad`). The gate boards are also real saved output.
- The baseline layout is incomplete (1 violation, 2 unconnected items). The final reference board is separate work.
- STE lint was not run on this record.

**8. Next**

SKiDL T4 to T6 with U2 and U3, then the repeat runs of the supported gates, the remaining limit probes, the final board, the exports, the simulation, and the draft package. These use unfrozen files only.
