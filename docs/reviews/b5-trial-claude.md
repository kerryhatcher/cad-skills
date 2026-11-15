# B5 trial record (claude-skill-dev)

This record lists the results of the B5 trial with their evidence. All paths are under `examples/pcb-trial/` unless stated.
The command log is `results/logs/` (each step has `.cmd`, `.out` and one line in `steps.txt`). Setup facts, versions and the accepted
setup tests are in `docs/reviews/b5-native-checkpoint-claude.md`. KiCad 10.0.5, ngspice 44.2, SKiDL 3.0.0, image `localhost/cad-skills-trial:b5`
(`sha256:d881df4ef3e2ec76995f4070596550db118b23e7f6db9017f09a418c44c4b1c2`). One machine, offline container runs.

## 1. Board update paths (T7, T8)

| Path | Result | Evidence |
|---|---|---|
| U1 native schematic, update in the PCB editor (mechanism U4, defaults) | 7 footprints, paths `/`+symbol UUID. Identity kept by UUID. | `results/native/`, `expected/fixtures/u1_saved_by_kicad.kicad_pcb` |
| Native gate edits (7): none, reorder, value of R2, add C2, remove D1, footprint of R1 (replace on and off) | All 7 give `equal` against the explicit expected files. First run and repeat run (`GUI_gate3_*_154` to `_160`). Each saved board has the full DRC and parity output. | `results/native/corrected/`, `results/native/repeat/`, `results/native/drc/` |
| Invalid first attempts `gate_reorder`, `gate_value`, `gate_addc2` | Marked `INVALID.txt`. They are not gate results. | `results/native/gate_*/INVALID.txt` |
| Arc, via and zone preservation (native update on the saved KiCad board) | `vz_none` and `vz_value`: `equal`. The 3 objects keep UUID, geometry and net. | `results/native/vz_preserve/`, `scripts/vz_gate.sh` |
| Limit probe: rename C1 (relink off and on) | Relink off: `equal`. Relink on: `different` (probe, exploratory). | `results/native/probe_rename_*`, `results/native/corrected/index.json` |
| U2 SKiDL schematic, cross-source (into the native board) | All 7 native footprints lose the path. 5 duplicates are added. This is a source change and not U2 regeneration. | `results/skidl/u2_skidl_e/` |
| U2 SKiDL schematic, same-source (board A then fresh run) | No footprint added, removed or unlinked. 5 pad-net differences. Cause: the schematic that SKiDL generates has wrong connectivity in 3 of 4 successful runs (pin partition comparison, `T4_net_e..i_141..144`). The `trial.net` files are byte-identical and correct. UUID replacement is not the cause. | `results/skidl/`, `results/logs/` |
| U3 netlist import (experimental) | Dialog found. Input is consumed. No-edit update: no difference. Sentinel C2: added. Default restore: C2 stays and its path becomes null. Restore with "delete unused footprints": C2 removed, board equals board B. | `results/skidl_u3/` |

## 2. Final board (T9)

The final board is `results/final/trial.kicad_pcb` (made by `scripts/layout.py --final`, zones refilled and saved by `kicad-cli pcb drc --refill-zones --save-board`).
ERC exit 0. DRC exit 0 with 0 violations and 0 unconnected items. The parity section is empty (`results/final/drc.json`, `erc.json`).
Attempt 1 (`FINAL_drc1_164`) had one `lib_footprint_mismatch`: the text rotation of D1 did not change the field and pad angles. Attempt 2 corrects this (kept as history).
The final schematic is the native schematic. No waiver is used.

## 3. Exports, simulation and package (T10, T12, T13)

| Item | Result | Evidence |
|---|---|---|
| Gerber (9 layers), drill (plated and non-plated), placement, STEP, schematic PDF, fabrication PDF | All commands exit 0. Contract setting to CLI option table: header of `scripts/export_final.sh`. | `results/final/export/` |
| Comparison with the expected values from `scripts/layout.py` | 4 of 4 checks pass: layer set, plated drill, non-plated drill, placement rows. 5 negative tests fail as expected. KiCad writes Y as the negative of the board Y (measured). | `scripts/check_exports.py`, `tests/test_trial_exports.py` |
| RC simulation, fixed assertion | 2.0860 V against 2.086 V, tolerance 1 percent. A 220 nF capacitor gives 1.2054 V and fails. | `results/final/rc/`, `scripts/check_rc.py` |
| Draft package and project | `contracts/validate.py --project --package`: pass, exit 0. Status `draft`. `fab.profile_evidence` is `pending`. A claim of `qualified` fails with `pkg.false_qualification`. | `results/final/draft/` |

## 4. Tests

`tests/test_trial_identity.py` 17 of 17. `tests/test_trial_exports.py` 9 of 9. `tests/test_trial_checker.py` 15 of 15.

## 5. Limits, untested paths and deviations

Not run in this trial (untested, no claim):

- U3 edits other than the no-edit update, the sentinel add and the delete option: value change, footprint change, remove, reorder and rename through the netlist import. U3 stays experimental. Only the tstamp link method ran.
- U5 (IPC API) and U6 (pcbnew updater, recorded negative).
- The limit probes "move R2 to another sheet" and "remove and re-add D1" on the native path (the frozen edit helper has no such operation).
- T5 defective-schematic ERC exit as a separate run, T6 (SKiDL `ERC()` exit), T11 (KiBot comparison).
- Zone refill inside a GUI update. The preservation test shows that the update keeps the zone. It does not refill.
- Second machine, other KiCad versions, KiCad 10.0.8.

Known limits of the evidence:

- The via, zone and arc fixture has objects that I added as text. `kicad-cli pcb upgrade --force` saved it. The `kicad-cli` command has no step log ID.
- The STEP file has no 3D models for C1, J1 and D1. The container has no 3D model library. The package does not use the file.
- The package is a bare-board draft with a neutral placeholder profile (`none-selected`). It has no supplier evidence and no BOM or stock evidence.
- The interface origin and the y-up conversion of the holes are my choice (lower-left corner of the outline).
- The SKiDL schematic generator is not deterministic and gives wrong wiring in 3 of 4 successful runs. SKiDL netlist output is stable (byte-identical).
- U3 and U2 results come from one pair of runs each.

Deviations:

- I used bare `python3` for some edit and parse commands (recorded 06:18 UTC). All later Python runs with `uv run`.
- Some earlier time stamps in the work state were estimates. The `date -u` values are in the step logs.
- The runs `u3d` and `u3e` did not save their boards (invalid, kept).
