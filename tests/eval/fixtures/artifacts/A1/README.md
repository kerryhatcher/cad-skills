# A1: pcb-design value edit (ready)

This fixture holds an owned copy of the accepted RC bare board. It records one design edit: R2 changes from 10k to 20k.

- `before/`: the accepted template `skills/pcb-design/templates/rc-bare-board`, unchanged.
- `after/`: the same project after the edit. The schematic and the board hold 20k. The interface names the edited board.
- `after/expect/r2-value.json`: the expected difference. The author wrote it before the edit.
- `after/out/`: the measured results of the tool commands. The history folder holds the prior board.
- `after/README.md`: the template README, unchanged. It still states R2 = 10 kohm and 2.086 V. This file states the values for R2 = 20 kohm.
- `after/simulations/`: the simulation circuit and its assertion. Both model R2 = 20k.

Procedure, in order:

1. Write the expected difference before the edit.
2. Change the Value of R2 on line 980 of `kicad/board.kicad_sch`. No other line changes.
3. Run `erc`. It passes with zero findings.
4. Run `update --adapter gui --expect expect/r2-value.json`. It passes on the measured image ID `b2731833711a`.
5. Run `interface --apply`. The tool rebinds the interface to the saved board and writes the hash. The author does not edit the hash.
6. Run `drc`. It passes. Run `erc` again, because the board changed. It passes.
7. Run `sim`. It measures 1.298448 V.
8. Run `check --for ready`. It exits 0 and reports `ready`.

The simulation values differ from the template. The template assertion of 2.086 V belongs to R2 = 10k. For R2 = 20k, the author computed the expected value as 3.3 V times (1 minus e to the power of minus 0.5). The result is 1.29845 V. The assertion is 1.298 V, with the template tolerance of 1 percent (0.01298 V).

The focused test `tests/test_artifact_fixtures.py` checks these facts from the repository files. It starts no container and no KiCad process.

Limits: one measured GUI dialog layout, KiCad 10.0.5, the local image only. No supplier record is bound. No provider call. No real HOME is used.
