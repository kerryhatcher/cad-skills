# U3 netlist-import edit tests: evidence

The record is `docs/reviews/u3-netlist-edits-claude.md`.

- `net/OP/trial.net`: the SKiDL netlist of each edit (`skidl/circuit_u3.py OP`).
- `start.kicad_pcb`: the start board (`scripts/u3_start_board.py`).
- `baseline.kicad_pcb`, `baseline.snap.json`: the gate baseline. KiCad saved it after the first import (step `GUI_U3base_319`).
- `start_to_base.json`, `base_gui_summary.json`: the comparison and the GUI summary of that first import.
- `expected/`: the expected differences. They were written before the edit runs.
- `runs/NAME_rN/`: the saved board, the GUI summary, the snapshot, the gate result (`compare.json`), the net check (`netcheck.json`) and the unread-change audit (`unread_audit.json`) of each run.
- `shots/`: the change list after "Load and Test Netlist" and the dialog after "Update PCB", for the base run and each r1 run.
- `logs/`: the command and output of each step, `steps.txt` and `gates.txt`. Steps 301 to 310 are invalid (see the record, section 5).
