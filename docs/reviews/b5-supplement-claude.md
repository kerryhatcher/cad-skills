# B5 supplemental record (claude-skill-dev)

This record adds the evidence that skill-dev-lead requested at 06:33:57 UTC. The 707 files of `docs/reviews/b5-files.sha256` are not changed
(all 707 hashes still match). The new files are in `docs/reviews/b5-supplement-files.sha256`. Paths are under `examples/pcb-trial/` unless stated.
All Python ran through `uv`. The command log is `results/logs/` (new IDs `T5_erc_171` to `U5U6_discovery_184`).

## Results

| Item | Result | Evidence |
|---|---|---|
| T5 ERC exit, good and defective schematic | Good schematic: exit 0, 0 violations. Defective schematic (3 labels of net VIN deleted): exit 5, 3 `pin_not_connected` errors. | `results/supplement/t5/t5d/`, log `T5_erc_d_174` |
| T6 SKiDL `ERC()` exit | `ERC()` does not change the exit code. Good circuit: exit 0, "No errors or warnings". Defective circuit (R1 pin 2 and D1 pin 2 not connected): exit 0 with 4 warnings and 0 errors. The B6 wrapper must read the SKiDL log or the counts and fail by itself. | `skidl/erc_probe.py`, `results/supplement/t6/`, logs `T6_good2_177`, `T6_bad2_178` |
| T11 KiBot 1.9.1 against the kicad-cli exports | Same 9 Gerber layer names. Drill split equal (holes, diameters, positions). Placement rows equal as numbers (KiBot writes 4 decimals, kicad-cli 6). Differences: (1) KiBot names the drill files `trial-PTH_drill.drl` and `trial-NPTH_drill.drl`. (2) The kicad-cli copper and mask files (`F_Cu`, `B_Cu`, `F_Mask`, `B_Mask`) have drill marks that the KiBot files do not have (6 and 2 lines). (3) KiBot gives the warning W181 (cannot map the schematic to a UUID). KiBot agreement is not a correctness proof. | `trial.kibot.yaml`, `results/supplement/t11/`, log `T11_kibot2_180` |
| Limit probe: remove D1, then re-add D1 (native update with the original schematic on the board without D1) | `equal` with the expectation written before the run (`scripts/probe_expect.py`): D1 added with library ID, value `Green` and pad nets from the baseline. No other difference. Not measured: the new UUID and the position of the added D1. | `results/supplement/probes/lp_readd_d1/`, log `GUI_lp_readd_d1_182` |
| Limit probe: move R2 into a hierarchical sub-sheet (netlist equals the expected map, ERC clean) | The update keeps the old footprint R2 but sets its path to null, and adds a new footprint R2 (value `10k`). Identity is not kept when the schematic path of a symbol changes (replace on, delete off). Not tested: delete option on, relink on. No expectation was stated for this probe. | `scripts/make_sheet_move.py`, `results/supplement/probes/lp_sheet*`, logs `LP_sheet_check_181`, `GUI_lp_sheet_r2_183` |
| U5 IPC API | Untested. Measured prerequisites: the Python package `kipy` is not in the image (not in `/usr/bin/python3` and not in `/opt/trial-venv`), `KICAD_API_SOCKET` is unset, and the offline container cannot install a package. A GUI session with the API server enabled is also necessary. No claim about the API functions. | `results/supplement/probes/u5_u6_discovery.out`, log `U5U6_discovery_184` |
| U6 pcbnew updater | Measured negative for the Python module. `import pcbnew` works (10.0.5). The names that contain netlist, update, schematic or import are `ImportSpecctraSES`, `UpdateUserInterface` and the layer constants. There is no netlist import or update-from-schematic function. | same file |
| U3 netlist import | Unchanged: experimental. No promotion from the no-edit and sentinel tests. | `results/skidl_u3/`, `docs/reviews/b5-trial-claude.md` |

## Defects of my trial scripts and invalid runs (kept as history)

- T5: three versions of `scripts/make_defective_sch.py` were wrong. Version 1 deleted one label of a net that has other labels (no violation, `T5_erc_171`). Versions 2 and 3 started the block scan at the tab and not at the parenthesis (`T5_erc_b_172`, `T5_erc_c_173`). The runs have `INVALID.txt`. The valid run is `T5_erc_d_174`.
- T6: the first `erc_probe.py` read a count attribute that does not exist (`T6_good_175`, `T6_bad_176`, `INVALID.txt`). The valid runs are `T6_good2_177` and `T6_bad2_178`.
- T11: the first config had the incorrect option `map: none` (`T11_kibot_179`, exit 7, `INVALID.txt`). The valid run is `T11_kibot2_180`.
- Herdr: the client (protocol 22) cannot talk to the server (protocol 19). I did not stop the server. I give reports in this terminal and in the message to the user.

## Limits

- One machine, one run of each probe. No repeat run of the two limit probes.
- The sheet-move probe uses one hand-written sub-sheet. The result can differ with the delete option on or a relink.
- The T5 defect is one kind (unconnected pins). Other ERC rules are not tested.
- The T11 comparison uses one KiBot configuration. The drill-mark difference depends on the plot settings of both tools.
- B5 stays incomplete only for the items that are listed as untested here and in `b5-trial-claude.md` (U3 edits, U5).
