# Expected differences of the U3 edit tests

Each file lists the exact differences that one edit may cause between the gate baseline and the board that KiCad saves after the netlist import. `scripts/identity.py compare` uses them. These files were written before the edit runs. Net names have no "/" prefix, because the SKiDL netlist names the nets without it.

- `remove-d1-delete-off.json` uses the measured native result (`docs/reviews/b5-supplement-addendum-claude.md`, section 1) as the hypothesis: D1 stays, and its path changes to null.
- `line-shift.json` was made from the baseline snapshot before the run. Each footprint changes only the property "SKiDL Line", from `circuit_u3.py:56` to `circuit_u3.py:59`.
