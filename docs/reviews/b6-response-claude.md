# B6 response to the lead design review (claude-skill-dev)

Date: 2026-11-14 07:08:57 UTC. Status: response report for the combined design review. The proposal `b6-proposal-claude.md` is **not changed**. This report lists the
revisions that I propose for R1 to R6. B6 implementation starts only after both reviewers agree. B5 files are not changed.
Measured now (host, no KiCad installed): `podman run --pull=never --network none --security-opt label=disable -v DIR:/work IMAGE` runs KiCad 10.0.5, writes files that the host user owns,
and leaves the SELinux label of the mounted directory as it was (`user_tmp_t` before and after). `contracts/validate.py` run from `/tmp` finds its schemas.

## R1. Skill scope and agent workflow

**Scope.** The CLI checks, runs tools and publishes. The **skill** guides the agent through design and editing. The CLI never designs a circuit.

Skill files (additions to proposal section 2):

| File | Content |
|---|---|
| `references/design-workflow.md` | The 17 steps of plan section 5 as a checklist. Each decision step names the record that holds it: datasheet pins and package pins in `components/part.yaml` (`pin_map`), power budget in `board.yaml` (`electrical_limits`) with the hand calculation in `simulations/`, decoupling and return-path choices in `docs/layout-notes.md` (template file), supplier limits in `manufacturing/supplier.yaml`. |
| `references/schematic-editing.md` | How to edit the native `.kicad_sch` text and keep identity (below). Worked examples: change a value, add a part, remove a part, change a footprint. Each example has its expected-difference file. |
| `references/placement-routing.md` | Order of placement, routing and zone steps. Which steps are text edits of the board, which are GUI or manual. |
| `references/gui-update.md` | The update procedure, option conditions and measured limits. |
| `templates/trial-led/` and `examples/add-c2/` | The template project, and one edited copy with its before snapshot, expectation and result. |

**Identity rules for edits** (measured in B5): never regenerate a schematic file. Edit text in place. Keep the symbol UUID and the `instances` path of each existing symbol. Give a new symbol a new UUID
and an `instances` path of the same root. Change a footprint only through the `Footprint` property. Do not move a symbol to another sheet (identity lost, duplicate added). Do not delete and re-add a part
to change it (new footprint UUID, default position). Write the expected differences **before** the edit (`identity.py` format), run the update, then compare.

**Actions without GUI access (exact).** The agent edits the schematic, runs `pcb.py erc`, writes `out/handoff/update-pcb.md` (project path, options, expected differences) and stops with the report status
`blocked_manual_update`. `pcb.py check` then returns exit 1 (the board is not in sync: `drc` parity or a missing fresh report). The agent must not claim readiness. A user with a native KiCad installation does the update by hand with the option conditions of the handoff file.
No route is a headless schematic-update CLI.

**Optional GUI adapter (examined, kept optional).** `scripts/gui_update.py` and the command `pcb.py update --adapter gui` work **only** in the exact B5 environment: derived image ID `d881df4e...`, KiCad 10.0.5, Xvfb 1600x1000, no window manager.
A preflight checks the image ID, the KiCad version and the screen size. A mismatch exits 2 with `update.environment_mismatch` and tells the user to use the manual route. The adapter works on a staging copy of the project, never on the project files.
The result (saved board in staging) goes through the verification of R5 before it replaces the project board. The adapter never decides a pass. The identity comparison and the parity check decide. Limits stay in SKILL.md: pixel coordinates, one image, first-run dialog handling.

Test scope: a template-only audit does not prove the edit workflow (R6 adds an edit task).

## R2. Runtime and standalone files

**Runtime selection** (`--runtime auto|native|container`, default `auto`):

1. `native`: `kicad-cli` and `ngspice` on `PATH`.
2. `container`: `podman` present and the image present **locally**. The image comes from `toolchain.lock.json` (`container.image`, `container.digest`) or, with no project, from `--image`. The wrapper compares `podman image inspect` ID with the digest. A mismatch exits 2 (`env.image_digest_mismatch`).
3. Neither: exit 2 with `env.no_runtime` and the exact missing prerequisite.

The command never pulls an image (`--pull=never`), never uses the network (`--network none`), and never relabels a path: it uses `--security-opt label=disable`, not `:Z`. The mount is a **staging copy** of the necessary project files, never the project root or a parent.
Tool outputs go to staging and the host copies them out (R5). Output files belong to the host user (measured).

**Worker.** The board-inventory worker (R3) reads board text on the host with the system interpreter through `uv run`. It does not import `pcbnew` (U6 negative, import assertions). No Python runs in the container except through the tested `uv run --no-project --no-config --offline --python /usr/bin/python3` form for the adapter.

**`env` before a project exists.** `pcb.py env [--project DIR] [--image REF] [--json]` needs no project. It reports the host tools, `podman`, the local images (name and ID), the selected runtime, and the versions that the runtime answers (`kicad-cli --version`, `ngspice --version`). With a project it adds the comparison with `toolchain.lock.json`. Exit 0 when the selected runtime answers, 2 when not.

**Standalone installed skill.** The skill carries `contracts/schemas/`, `validate.py`, `project_io.py`, `identity.py`, `sexp.py` and `board_inventory.py`. Test: copy the skill to a temporary directory outside the repository, run `pcb.py check` and `validate.py` from an unrelated working directory with a clean environment, and show that no file outside the skill is read (the test removes the repository from the path and compares file-open traces).

**Template records (complete).** `board.yaml`, `variants.yaml`, `components/part.yaml` (one record for each part type), `manufacturing/supplier.yaml` (placeholder `none-selected` with its evidence note), `manufacturing/export.yaml`, `manufacturing/waivers.yaml` (empty list),
`toolchain.lock.json` (KiCad, ngspice, uv, Python versions, container image and digest), `mechanical/board-interface.json`, `kicad/` (project, library table, schematic, board), `simulations/` (circuit and `assertions.json`), `docs/layout-notes.md`.
`board-interface.json` holds the board hash. `check` reports `interface.board_hash_stale` after a board change. The agent edits that one field (SKILL.md gives the command). B11 later owns this record.

## R3. General export expectations

**Board-inventory worker** `scripts/board_inventory.py BOARD [--json]` (new, small, tested). The accepted identity reader stays unchanged. The worker reads the board text with the same `sexp.py` and lists:

| Item | Fields |
|---|---|
| Holes of pads | reference, pad number, board position, drill diameter, plated or non-plated (from the pad type: `thru_hole` plated, `np_thru_hole` non-plated) |
| Vias | position, drill, plated (always) |
| Footprints | reference, side, position, rotation |
| Copper layers | stack order from the saved board (F.Cu, inner by number, B.Cu) |

**Transform.** Board position = footprint position + rotation of the local pad position by the footprint angle (KiCad: y down, positive angle counter-clockwise on screen). Bottom-side footprints: the worker implements the mirror only if the container test
agrees with `kicad-cli pcb export drill` for a fixture with 4 angles on both sides. If the test disagrees, bottom-side parts are **unsupported**.
**Unsupported and refused with a finding (exit 2, never skipped):** oval or slot drills (`inventory.unsupported_slot`), pads with a drill in a custom shape, footprints with unknown side, arbitrary angles that the test did not cover, a drill without a plating decision. The finding names the reference and the pad.

**Layer functions.** The expected file function of each Gerber comes from `export.yaml` (role and KiCad layer) and the board copper order: copper `Copper,Ln,Top|Inr|Bot`; other roles from a small fixed table of the roles in the schema (mask, paste, silk, outline for top and bottom). No nine-file map. Four-layer and six-layer cases are unit-tested with edited board text and checked once in the container with a real four-layer export.
The trial's independent constants stay in `examples/pcb-trial/` as evidence. A test compares the worker with them on the trial board.

## R4. Reports, failures, freshness

**One rule for findings.** Any unwaived finding of any severity (error or warning) in an ERC or DRC report is a violation. Exit 0 needs zero unwaived findings. This replaces the sentence "no finding of severity error" in the proposal.
The report lists the `ignored_checks` of the tool. A project that ignores a connectivity check (`unconnected_items`, `schematic_parity`) fails with `settings.ignored_connectivity_check`.

**Waivers.** A finding is waived only when a record in `waivers.yaml` matches kind (erc or drc), rule (the finding type), all objects of the finding, and the SHA-256 of the current board (drc) or schematic (erc). A waived finding stays in the report with `waived_by`. A waiver with other bytes is stale: finding `waiver.stale`, exit 1.

**Exit mapping and precedence (one rule, aligned with the accepted validator):**

| Exit | Meaning |
|---|---|
| 3 | A tool ran but failed: exit not 0 and not 5, crash, timeout, a missing output file, a report or log that cannot be read, a missing measured value |
| 2 | The command cannot run or cannot decide: incorrect arguments, missing prerequisite, unsupported input or geometry, saved settings that disagree |
| 1 | Design failure: unwaived finding, failed assertion, failed export check, invalid record, stale or missing mandatory report |
| 0 | None of the above |

When several apply, the highest listed exit code wins (3, then 2, then 1). Every finding stays in the report. The simulation table follows this rule: a missing `.meas` value is exit 3, a missing `ngspice` is exit 2.

**Raw bytes.** The raw tool report is kept unchanged, with its dates, and its SHA-256 is recorded. The wrapper writes a binding file next to it: command, tool versions, raw-report hash, and the hashes of the inputs (board, schematic, project file, `export.yaml`, `assertions.json`).
The wrapper's own JSON report has no time and no random value, so the same raw report and inputs give the same wrapper bytes. No determinism claim applies to the raw report.

**Freshness.** `check` (readiness) needs a binding for each mandatory report whose input hashes equal the current files: ERC, DRC with parity, simulation (when `simulations/` exists) and, for export readiness, the export record. A missing or stale report gives exit 1 and never a ready status.
**Refill.** `drc --refill-zones` records the board hash before and after. If the bytes do not change (already filled), the hash and the bindings stay valid. If they change, the report binds to the new hash and the older bindings that used the old hash are stale. Both cases are tested.

## R5. Writes and publication (accepted project I/O)

The whole operation holds `project_lock`: stage, run, verify, publish. The limits of `project_io.py` stay in SKILL.md: the lock covers cooperating local processes only (no hostile process, no network file system, no power loss, no rollback of several files).

| Step | Mechanism |
|---|---|
| Tool execution | In a new staging directory `out/.tmp-TASK-N/` (confined, created empty). The runtime mounts only this directory. The tool never writes into `kicad/`. |
| Board replacement (`drc --refill-zones`, `settings --apply`, adapter update) | Verify in staging first: the new board parses, and the identity comparison shows only the expected differences (refill: none). Then `atomic_write(project, "kicad/board.kicad_pcb", bytes)`. A failure before the replacement keeps the old bytes. A `PostReplaceError` means the new bytes are in place: the command reports it and exit 3. A crash can leave a `.cad-skills-tmp-*` file. |
| Report publication | The raw report and then the binding file, each with `atomic_write` into `out/reports/`. A report without a binding counts as missing (`report.unbound`). |
| Export publication | Build in a new staging directory, run the checks on staging, then `publish_dir(project, staging, "out/export/HASH12-N")`. An existing destination is refused (exit 2, `export.exists`); the counter N gives a new name. A failed export is **not** published: the staging directory stays as `out/.failed-...` for inspection. A stale file in an older export cannot satisfy a failed one, because `check` looks only at a published directory whose `export.json` binds to the current hashes. |
| Leftovers | `check` lists `.tmp` and `.failed` directories and temp files as findings (exit 1). The wrapper deletes only staging that it made itself in this run after a successful publication. |

**Normal export prerequisites:** fresh ERC pass, fresh DRC pass with parity and no unwaived finding, saved plot settings equal to the contract, simulation pass when `simulations/` exists. Otherwise exit 1 (`export.prerequisite_missing` with the names). `settings --apply` is a separate explicit command. It lists the bindings that it invalidates.

## R6. Acceptance tests (focused)

| Test | Check |
|---|---|
| Host to container | On the real image, `pcb.py env` and `erc` with `--runtime container`. The mounted directory label is the same before and after. No pull (offline). Output files belong to the host user. Missing image: exit 2. Wrong digest: exit 2. |
| Standalone installed skill | The copy test of R2 from an unrelated directory. |
| Exit precedence and mapping | A stub tool returns 0, 5, 1, no output and malformed output. A case with findings and a tool failure returns 3. |
| Waivers | Matching waiver passes and stays listed. A waiver for other bytes or other objects fails. A blanket rule fails. |
| Freshness | Edit the board by one byte: reports become stale and `check` exits 1. Refill on a filled board: same hash, bindings valid. Refill on an unfilled board: new hash. |
| Writes | An injected failure before and after `os.replace`, an existing export directory, and a failed export that leaves staging only. |
| Inventory | Real container export with rotated parts (4 angles), both sides, vias and non-plated holes: worker equals `kicad-cli` drill output. Slot and unknown geometry exit 2. Four-layer layer functions. The trial constants agree on the trial board. |
| **Agent edit task** | See below. |

**Agent execution (exact interface).** A small script `tests/eval_pcb_design.py` (no framework) installs the skill under `TMP/.claude/skills/pcb-design/` with the template copied to `TMP/project`, then runs
`claude -p "TASK" --model claude-sonnet-5-5 --output-format stream-json --verbose --no-session-persistence --permission-mode dontAsk --allowedTools "Bash(uv run:*) Read Edit Write" --max-budget-usd N` with `TMP` as the working directory.
(The flags exist in `claude --help` on this host. The record states the final flags, the model ID, the budget, the task text and the transcript path.) The pass or fail comes only from independent checks that the test makes after the run, **never** from the agent's report:

- Task A (GUI adapter available in the fixed image): "Change R2 to 22k and add C2 (100n) between N_RC and GND, then make the board ready." Checks: the expected differences written by the test before the run (value of R2, added C2 with its nets) equal the observed differences; DRC with parity exit 0; ERC exit 0; the simulation assertion with the new values passes or fails as the assertion record says; export checks pass; the board hash of the readiness reports equals the board.
- Task B (adapter disabled): the same task. Checks: the schematic has the edit, the handoff file exists, `check` exits 1, and the agent's final message does not claim readiness (a fixed set of phrases that the test looks for, with the independent exit code as the main check).
- Task C (negative): "Move R2 to a new sheet and keep identity". The skill must warn and the agent must not claim identity kept.

This is one agent run per task, so the evidence is limited. It is a smoke test of the guidance, not a measure of reliability. The record says so.

## Changes to the interface (summary)

| Item | Proposal | Response |
|---|---|---|
| Subcommands | env, check, erc, drc, sim, settings, export | add `update` (adapter or handoff), and the worker `board_inventory.py`. `identity.py` is run directly (exit codes 0, 1, 2, 3 already match the rule). |
| Exit 0 | No finding of severity error | Zero unwaived findings of any severity |
| Exit for a missing measured value | 2 (simulation table) and 3 (malformed tool) | 3. One rule for all |
| Refill | Changes the hash | May leave the hash unchanged. Bindings follow the hash |
| Determinism | All JSON | Wrapper JSON only. Raw reports keep their bytes |
| Runtime | Container, unspecified | `auto`, image local, digest checked, `label=disable`, staging mount, no pull |
| Export expected values | From the saved board through the identity reader | From `board_inventory.py` (new). Unsupported geometry exits 2 |
| GUI | Manual only | Manual fallback plus an optional adapter in the exact B5 environment |

## New decisions for the reviewers

| ID | Question | Proposal |
|---|---|---|
| D8 | Is `board_inventory.py` the right small worker, and is a text transform with a container test enough? | Yes. Unsupported cases exit 2. |
| D9 | Ship the GUI adapter at all? | Yes, optional, with the preflight and the manual fallback. Reviewers may drop it. |
| D10 | Exit precedence 3, 2, 1? | Yes, as the accepted validator. |
| D11 | Stale-state detection through binding files, not through timestamps? | Yes. |
| D12 | Is one agent run per task enough for the B6 smoke evidence? | Yes, with the limit stated. A repeat run is a B12 item. |

Limits stay as before: one fixture, one machine, one KiCad version, no supplier qualification, no zone refill inside a GUI update, U3 and U5 untested.
