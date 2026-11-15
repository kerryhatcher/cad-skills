# B6 proposal: skill `pcb-design` (claude-skill-dev)

Date: 2026-11-14 06:54:38 UTC. Status: proposal only. There is no B6 implementation until B5 is accepted and both reviewers agree to the interface in this report.
Basis: plan section 17 (accepted runtime findings) and the measured B5 evidence (`b5-trial-claude.md`, `b5-correction-claude.md`).
The B5 implementation stays frozen. This proposal changes no file of it.

## 1. Scope

B6 makes the skill `skills/pcb-design/` for the **native KiCad route**. The skill does these things: report the environment, validate the project records, run ERC and DRC with parity,
run a numerical simulation assertion, and make and check the neutral exports. It does not design circuits for the user, route a board or qualify a supplier.

| Route | B6 status |
|---|---|
| Native schematic (U1) | Supported. Six measured gate edits: no edit, reorder, value, add part, remove part, footprint change. |
| SKiDL schematic generation (U2) | Unsupported. `check` refuses `circuit_source: skidl` with the finding `source.skidl_unsupported` (exit 1). The reason: generated connectivity was wrong in 3 of 4 runs. |
| SKiDL netlist import (U3) | Experimental. Not in B6. It is a reference note only. |
| IPC API (U5), pcbnew updater (U6) | Not used. U5 untested. U6 measured negative. |

## 2. Bundled files (the skill operates alone)

```
skills/pcb-design/
  SKILL.md                      procedure, option conditions, manual boundaries, routing words
  scripts/pcb.py                the one CLI (PEP 723 header, pinned dependencies)
  scripts/validate.py           copy of contracts/validate.py
  scripts/project_io.py         copy of contracts/project_io.py (lock, confined paths, atomic write)
  scripts/identity.py           copy of the frozen identity reader (and sexp.py)
  schemas/                      copies of the schema files that registry.json names
  templates/trial-led/          the native trial project: schematic, project file, library table, board with footprints, export.yaml, simulation record
  references/                   gui-update.md, export-contract.md, exit-codes.md, trial-limits.md
```

SKILL.md resolves every path relative to itself. No file is read from another skill or from `contracts/` at run time.
`tests/test_skill_packages.py` checks that the copies equal the sources and that no file reaches outside the skill.

## 3. CLI: exact operations

All commands take `--project DIR`. Read-only commands take no lock. A command that writes takes the project lock (`project_io.py`) for the whole operation. All Python runs through `uv run`.

| Command | Operation | Writes |
|---|---|---|
| `pcb.py env [--json]` | Report `kicad-cli --version`, `ngspice`, Python, the container digest. Status 0 only when `kicad-cli` and the ERC and DRC commands answer. | nothing |
| `pcb.py check` | Run `validate.py --project`. Compare the schematic and board hashes with the reports in `out/reports/`. List missing reports as `unprocessed`. Refuse `skidl`. | nothing |
| `pcb.py erc` | `kicad-cli sch erc --exit-code-violations --severity-all --format json -o OUT SCH` | `out/reports/erc.json` |
| `pcb.py drc [--refill-zones]` | `kicad-cli pcb drc --schematic-parity --exit-code-violations --severity-all --format json -o OUT PCB`. With `--refill-zones`: add `--refill-zones --save-board`. | `out/reports/drc.json`. The board when refilled. |
| `pcb.py sim` | Run `ngspice -b CIR -o LOG` for each circuit in `simulations/`. Compare each `.meas` value with `simulations/assertions.json`. | `out/reports/sim-*.log`, `sim.json` |
| `pcb.py settings [--apply]` | Read the three saved plot settings of the board. With `--apply`: set `drillshape 0`, `usegerberattributes no`, `usegerberadvancedattributes no` by text edit. Each entry must occur once. | the board (apply only) |
| `pcb.py export` | Refuse unless `settings` agree. Run the gerbers, drill, pos, step and PDF commands of `references/export-contract.md` into `out/export/`. Run the neutral checks (section 6). | `out/export/`, `export.json` |

The export commands are the measured trial commands: `pcb export gerbers --layers ... --no-x2 --precision 6 --board-plot-params`, `pcb export drill --format excellon --drill-origin absolute --excellon-zeros-format suppressleading -u mm --excellon-separate-th --generate-report`, `pcb export pos --side both --format csv --units mm`, `pcb export step`, `sch export pdf`.
The `settings --apply` writer changes the PCB bytes. All reports bound to the old bytes are then stale. `check` reports them as stale. The agent must run `drc` and `export` again.

## 4. JSON and exit handling

Each command writes one JSON report to standard output with `--json`. The report has: `report_schema_version`, `status`, `exit_code`, `tool_versions`, `inputs` (path and SHA-256), `findings` (code, severity, file, location, message), `outputs` (path and SHA-256), `commands` (argument list and tool exit code), `unprocessed`.
The report has no time and no random value. The same inputs give the same bytes. The rules:

| Exit | Meaning | Mapping |
|---|---|---|
| 0 | Success | tool exit 0 and no finding of severity error |
| 1 | Design failure | `kicad-cli` exit 5 (violations), parity finding, failed assertion, failed export check, invalid record |
| 2 | Incorrect arguments or missing prerequisite | no `kicad-cli`, no `ngspice`, no project file, saved plot settings not agreeing |
| 3 | Tool failure | any other tool exit, a tool report that cannot be parsed, a missing expected output file |

Measured facts that the wrapper must handle (B5): DRC and ERC exit 5 with `--exit-code-violations`. SKiDL `ERC()` exits 0 with warnings (not used). A DRC report with a `lib_footprint_mismatch` warning counts as a violation. The wrapper never hides a finding to reach exit 0.
A waiver applies only when its record binds to the exact PCB or schematic bytes (B234 rule).

## 5. GUI and manual boundaries

- **Update PCB from Schematic** is a manual KiCad GUI step. B5 measured no headless route: standalone `pcbnew` refused it, and the module has no update function. The trial GUI script uses pixel coordinates on one image and stays trial-only.
- The skill states the option conditions: reference relinking off, replace footprints on only for a footprint change, delete unused footprints on only for a part removal. Measured limits go to `references/gui-update.md`: a symbol moved to another sheet loses identity, and a re-added part gets a new UUID and a default position.
- After the manual step the skill requires: `drc` (parity), then an identity comparison with `identity.py` against the board before the update, with the expected differences written first.
- The first-run KiCad dialog, routing and placement of a new design are manual or agent tasks outside the CLI. The template board of the trial project needs no GUI step.

## 6. Neutral export checks (in `export`)

1. Saved plot settings equal the contract (`drillshape 0`, both attribute settings `no`).
2. Gerber file set equals `export.yaml` layers and suffixes.
3. No active `%TF`, `%TA`, `%TO` or `%TD` command in any Gerber (the contract says `x2: false`).
4. One `G04 #@! TF.FileFunction` comment per Gerber. It matches the fixed layer mapping and the copper order of the board. A swapped file fails.
5. Drill files: plated and non-plated split, diameters and positions equal the holes and vias of the board.
6. Placement rows: exactly one row for each board footprint. A repeated reference fails.
7. Header of the Excellon file equals the contract (zero suppression, units, 3:3 format).

Limit: the trial expected values came from layout constants. A general project has none. The skill takes the expected values from the saved board (read by `identity.py`), which is a second source independent of the exporter. This is weaker than the trial check and the skill says so.

## 7. Focused acceptance tests

| Test | Where | Pass condition |
|---|---|---|
| Exit mapping with a stub `kicad-cli` that returns 0, 5, 1 or is absent | host | exit 0, 1, 3, 2 and the finding codes |
| Real ERC: good and defective schematic (3 labels deleted) | container | exit 0 and exit 1 with 3 `pin_not_connected` |
| Real DRC with parity: final trial board, and a board with a footprint mismatch | container | exit 0 and exit 1 |
| `drc --refill-zones` changes the PCB hash and `check` marks the old report stale | container | stale finding |
| Report determinism: two runs, same bytes; `unprocessed` lists skipped checks | host | equal bytes |
| `sim`: 2.0860 V pass, 220 nF fail at 1.2054 V, `ngspice` absent, log without a value | container and host | exit 0, 1, 2, 2 |
| `settings`: wrong value, absent entry, repeated entry; `export` refuses | host | exit 2 or 1 as stated |
| `export` checks 1 to 7 with the negative cases of B5 (swapped copper, active attribute, duplicate row, wrong drill) | host on saved files, container once | each negative fails its check |
| Lock: a second writer gets `lock.held` | host | exit 1 |
| `circuit_source: skidl` | host | `source.skidl_unsupported`, exit 1 |
| Isolation and copies (`test_skill_packages.py`), snippets in SKILL.md (`test_snippets.py`) | host | pass |
| Clean agent run from the template: ERC 0, DRC 0 with parity, sim pass, export 7 of 7. A deliberate ERC error gives exit 1. | container, one run before review | all pass |

## 8. What stays trial-only

| Stays in `examples/pcb-trial/` | Reason |
|---|---|
| `trial_env.sh`, `gui_update.py`, `gui_probe*.sh`, `gui_import.sh`, `limit_probes.sh`, `vz_gate.sh` | Pixel-based GUI drivers and podman paths. One image, one resolution. |
| `edit_native.py`, `gate_expect.py`, `probe_expect.py`, `make_sheet_move.py`, `make_defective_sch.py`, `trial_native_writer.py` | They make trial inputs and expectations. |
| `layout.py` | Its constants (`PLACE`, `VIAS`) describe the trial board. Only the plot-setting writer moves into `pcb.py settings`. |
| `check_exports.py`, `check_rc.py` | Their logic is adapted into `pcb.py`. The trial files keep the layout-constant expectations as independent evidence. |
| `compare_kibot.py`, `trial.kibot*.yaml`, `erc_probe.py` | Evidence that KiBot and SKiDL gave no extra value or a failure. B6 uses kicad-cli directly. |
| `build_draft_package.py` | Design reference for the package builder of the fabrication skill (B8). B6 builds no package. |
| `results/` | Evidence. |

## 9. Decisions for the reviewers

| ID | Question | Proposal |
|---|---|---|
| D1 | Where does the plot-setting writer live? | A `settings` subcommand with `--apply`. `export` never writes the board. |
| D2 | Ship `identity.py` in the skill? | Yes, unchanged, to check an update that the user does by hand. |
| D3 | Expected export values for a general project | From the saved board. State the weaker independence. |
| D4 | Report place | `out/reports/`, names with the first 12 characters of the bound hash. |
| D5 | KiBot in B6 | Not used. The common export tool is kicad-cli for the neutral set. |
| D6 | SKiDL | Refuse in B6. Revisit after a repair of the generator or a measured netlist route. |
| D7 | Container | The derived trial image (KiCad 10.0.5, ngspice, uv). `env` reports its digest. |

Open limits stay visible in SKILL.md: one fixture, one machine, one KiCad version, no supplier qualification, no zone refill inside a GUI update, U3 and U5 untested.
