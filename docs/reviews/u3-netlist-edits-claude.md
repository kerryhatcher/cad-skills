# U3 netlist-import edit tests (claude-skill-dev)

Date: 2026-11-16. This record completes the U3 edit tests that `docs/reviews/b5-trial-claude.md` (section 5) lists as not run.
All paths are under `examples/pcb-trial/` unless stated. The evidence is in `results/skidl_u3/edits/`.

## 1. Setup

| Item | Value |
|---|---|
| Image | `localhost/cad-skills-trial:b5`, ID `sha256:d881df4ef3e2ec76995f4070596550db118b23e7f6db9017f09a418c44c4b1c2` (the B5 image). Offline runs (`--network none`). |
| Tools | KiCad 10.0.5, SKiDL 3.0.0. One machine. |
| SKiDL source | `skidl/circuit_u3.py`. It writes a netlist only. It has the 7 parts of the native fixture, each with a tag. |
| GUI driver | `scripts/gui_import.py`. It opens File > Import > Netlist, sets the options, reads each option back from the screen, loads, updates, saves and closes KiCad. |
| Link method | "Link footprints using component tstamps". The tstamp of a SKiDL part comes from its hierarchy and its tag, not from its reference. |
| Gate | `scripts/identity.py compare` against the files in `results/skidl_u3/edits/expected/`. These files were written before the runs. |
| Net check | `scripts/u3_netcheck.py`. It compares each pad net, path and reference of the saved board with the netlist. The netlist route has no reliable schematic, thus this check replaces `--schematic-parity`. |
| Unread-change audit | `scripts/u3_unread_audit.py`. It finds footprint child forms that changed but that `identity.py` does not read. |
| Run scripts | `scripts/u3_env.sh` and `scripts/u3_gates.sh`. They contain the path of the scratch copy of this run. |

## 2. Start board and gate baseline

`scripts/u3_start_board.py` makes the start board from `results/native/baseline.kicad_pcb`. It adds the via, the arc and the zone of `expected/fixtures/vz_saved_by_kicad.kicad_pcb`.
It replaces each footprint path with the SKiDL tstamp of the same reference. It removes the "/" prefix of each net name, because the SKiDL netlist has no prefix.
The start board has 7 footprints, 6 segments, 1 via, 1 arc and 1 zone.

The first import (step `GUI_U3base_319`, edit `none`) gives the gate baseline `baseline.kicad_pcb`. This step is a source conversion, not a gate result.
It changed only the footprint properties of the 7 footprints (`start_to_base.json`). The netlist adds the fields `Description`, `SKiDL Tag` and `SKiDL Line`. Positions, pads, tracks, the via, the arc and the zone did not change.

## 3. Results

Each edit ran two times (r1 and r2) from the same baseline. All 20 runs saved the board, set the options as requested, and stopped KiCad with exit 0.

| Edit | Options | Gate (r1, r2) | Net check | Unread-change audit |
|---|---|---|---|---|
| `none` | replace on, delete off | equal, equal. The saved board has the same bytes as the baseline. | pass | none |
| `reorder` | replace on, delete off | equal, equal | pass | none |
| `value-r2` | replace on, delete off | equal, equal | pass | none |
| `add-c2` | replace on, delete off | equal, equal | pass | none |
| `remove-d1` | replace on, delete on | equal, equal | pass | none |
| `remove-d1` | replace on, delete off | equal, equal. D1 stays and its path changes to null. | fail: `extra_footprint` D1 | none |
| `footprint-r1` | replace on, delete off | equal, equal | pass | the new footprint body of R1 (expected) |
| `footprint-r1` | replace off, delete off | equal, equal | pass | **R1 `(attr smd)` changes to `(attr smd dnp)`** |
| `rename-c1` | replace on, delete off | equal, equal | pass | none |
| `line-shift` | replace on, delete off | equal, equal. Each of the 7 footprints changes its `SKiDL Line` property. | pass | none |

The results of the two option probes (delete off, replace off) are not a supported edit. They show the effect of the option.

The r1 and r2 boards have the same bytes for 8 of the 10 edits. The two exceptions:

- `add-c2`: KiCad gives the new C2 a random UUID. The board sorts the footprints by UUID, thus the order of the file changes.
- `footprint-r1`: R1 keeps its footprint UUID and its pad UUIDs. Two properties and two `fp_line` forms of the new body get new random UUIDs.

## 4. Findings

1. **The netlist route passes the same edit gate as the native route.** Value, add, remove, footprint change, reorder and rename all give the expected differences. Placement, tracks, the via, the arc and the zone stay the same.
2. **The rename keeps the identity.** The tag stays `C1`, thus the tstamp stays the same. Only the reference changes. A change of the tag is a new part. This was not tested.
3. **`reorder` does not change the netlist.** SKiDL sorts the parts. Thus this edit cannot change the board on this route.
4. **`SKiDL Line` causes changes on each footprint.** SKiDL writes the source line of each part into the netlist. A source edit that moves the lines of the parts changes this property on each footprint that moves. The change is a property only. The gate reports it as a difference, thus each expectation must list it. Possible solutions: remove the field before the import, or make the gate ignore it. Both need a decision.
5. **`identity.py` does not read the `attr` form.** With "replace" off, KiCad marks R1 "Do not place" (`dnp`), and the gate reports `equal`. The native board `results/native/repeat/gate3_fpr1_replace_off/trial.kicad_pcb` has the same mark. The B5 records classify that run as an option experiment, but they do not record the mark. `skills/pcb-design/scripts/identity.py` has the same code. A `dnp` mark removes a part from the BOM and the placement files, thus this gap is important for PCBA. I did not change the frozen reader.
6. **The delete-off result is the same on both routes.** D1 stays on the board with a null path. The net check reports it as `extra_footprint`.

## 5. Limits

- One machine, one fixture, KiCad 10.0.5 and SKiDL 3.0.0 only. Two runs of each edit.
- Only the tstamp link method ran. The reference link method did not run.
- The GUI driver uses absolute screen coordinates. The change list is recorded only as screenshots (`shots/`). The driver does not save the text report of the dialog.
- The net check does not compare the footprint library ID with the netlist. The unread-change audit compares only footprints that are in both boards.
- No DRC ran on the saved boards. The baseline is not fully routed.
- Not tested: a tag change, a part in a SKiDL subcircuit (hierarchy), a net rename, and zone refill.
- Steps 301 to 310 are invalid. `circuit_u3.py` changed after them (the edit `line-shift` moved the part line). Their logs stay in `logs/`. Steps 311 to 339 are the valid run.

## 6. Proposal for the lead

U3 can change from "experimental" to "supported for the measured edits", with these conditions:

- The skill uses the tstamp link method, replace on, and delete on for a removal.
- Each part has an explicit tag. The skill never changes a tag.
- The skill runs the net check after each import, because no schematic parity is available.
- The gate handles `SKiDL Line` (finding 4) before the route is supported.
- The identity reader reads the `attr` form (finding 5). This change applies to the native route also.

The support decision belongs to the lead. This record does not change the skill.

## 7. Tests

`uv run tests/test_trial_u3.py`: 13 of 13. `tests/test_trial_identity.py`: 17 of 17. `tests/test_trial_checker.py`: 15 of 15.
`tests/test_trial_exports.py`: 15 of 16. `test_rc_real_logs` fails because `results/final_r2/rc/good.log` is not in the repository. This failure also occurs on `origin/main` without these changes.
