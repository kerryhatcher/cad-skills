# B6 consolidated proposal: skill `pcb-design` (claude-skill-dev)

Date: 2026-11-14 07:34:57 UTC. Revision 3, frozen for the combined review. Status: **final proposal. No implementation starts until both reviewers accept it.** B5 stays closed. Revision 2 is preserved unchanged in `b6-consolidated-proposal-claude-r2.md` (SHA-256 `9ea3c117004309bdd8f024d63a1a0866661e5ee41d89be00ed55fe6a002d400b`).
This file replaces the interface of `b6-proposal-claude.md` (`441af68e...`), `b6-response-claude.md` (`1b600087...`) and `b6-reconciliation-claude.md` (`5ea354b5...`).
Those three files are preserved unchanged. Basis: `b6-design-root.md`, the Codex and Pi design reviews, and `b6-decisions-root.md` (which wins when sources differ).
Section 15 lists the conflicts that I found. Revision 2 added the lead's resolutions of C1, C2, C3 and C5. Revision 3 accepts the lead's narrow refinements: no SKiDL package and no `requirements.lock` in the skill runtime, and a tested standalone runtime before any support claim. Revision 3 also adds C10 from the Codex review: the result holds the full binding-file hash.

## 1. Scope and routes

B6 makes `skills/pcb-design/`. The **skill** guides an agent through circuit design, native schematic edits, placement, routing, review and neutral export. The **CLI** checks, runs tools and publishes. The CLI never designs a circuit.

| Route | Status |
|---|---|
| Native schematic (U1), six measured edits | Supported (no edit, reorder, value, add part, remove part, footprint change). The replace-off run is an option experiment. |
| SKiDL generated schematic (U2) | Unsupported. Recognized and refused: `source.skidl_unsupported`, exit 2. |
| Netlist import (U3) | Experimental. Not in B6. |
| IPC API (U5), pcbnew updater (U6) | Not used. `pcbnew` is used only to **read** the board. |

## 2. Skill content (guidance, not only inspection)

| File | Content |
|---|---|
| `SKILL.md` | Procedure, option conditions, manual boundaries, open limits, routing words. Paths resolve relative to the file. |
| `references/design-workflow.md` | The 17 steps of plan section 5. For each decision: where it is recorded and which check closes it: datasheet and pin-to-pad map (`components/part.yaml` `pin_map`), power budget (`board.yaml` `electrical_limits`, hand calculation and `simulations/`), decoupling and return path (`docs/layout-notes.md`), supplier limits (`manufacturing/supplier.yaml`). |
| `references/native-edit.md` | Edit `.kicad_sch` text in place. Keep the symbol UUID and the `instances` path of each existing symbol. A new symbol gets a new UUID and an `instances` path of the same root. Change a footprint only through its `Footprint` property. Never move a symbol to another sheet (identity lost, duplicate added). Never delete and re-add a part to change it (new footprint UUID, default position). Write the expected-difference file **before** the update (`identity.py` format), then compare. A changed or removed track needs a UUID entry. |
| `references/placement-routing.md` | Placement, rotation, side, routing, vias, zones, refill, parity review. |
| `references/gui-update.md` | Update procedure, option conditions, measured limits (replace on only for a footprint change, delete on only for a part removal, relink off). |
| `references/runtime.md`, `references/exit-codes.md`, `references/trial-limits.md` | Runtime, exits, limits. |
| `examples/rc-edit/` | One meaningful edit (section 14): before files, expected-difference file, after files, checks. |
| `templates/rc-bare-board/` | The template project (section 12). |

**Agent without a GUI route.** The agent edits the schematic, runs `erc`, writes the handoff file (input hashes, pending operation, expected differences, exact options) and stops the dependent steps. `check` stays exit 1. The agent does not claim an updated board and does not use stale parity. Read-only work continues.
Neither route is a headless schematic-update CLI.

## 3. Bundled files (the skill operates alone)

```
skills/pcb-design/
  SKILL.md  references/  examples/  templates/
  scripts/pcb.py  scripts/board_inventory.py  scripts/gui_update.py
  scripts/validate.py  scripts/project_io.py  scripts/identity.py  scripts/sexp.py     copies, unchanged
  contracts/README.md  contracts/schemas/                                              existing copy set
  runtime/Containerfile  runtime/BUILD.md                                              fixed build recipe for the standalone setup
```

The skill bundles no SKiDL package and no `requirements.lock`. B6 refuses SKiDL (section 1).
`validate.py` stays unchanged and defaults to `scripts/schemas`. **The controller always passes `--schemas SKILL/contracts/schemas`.**
`tests/test_skill_packages.py` is extended to compare the four script copies with their sources. Test: run from an unrelated working directory with the repository inaccessible.

## 4. Runtime

`--runtime auto|container|native` (default `auto`).

| Rule | Detail |
|---|---|
| `auto` with a project | Follows `toolchain.lock.json` `execution`. A missing locked runtime is exit 2. **No silent fallback.** An explicit `--runtime` or a measured tool version that conflicts with the lock is exit 2. A working command never changes the lock and never writes successful evidence under another environment. `env` can report the measured difference. |
| No project | `env` selects the bundled local image (`localhost/cad-skills-trial:b5`, ID in the skill) or an explicit native runtime. It reports capabilities separately. A missing `ngspice` does not prevent ERC. |
| Image | The lock digest (the local image ID) is the identity. A tag is only a lookup. Compare `podman image inspect` ID with the lock. A normal command never pulls and never builds. |
| Standalone setup | The skill bundles the fixed build recipe `runtime/Containerfile` and `runtime/BUILD.md`: base image `ghcr.io/inti-cmnb/kicad10_auto_full` by digest `sha256:96e75f88...`, `uv` image by digest `sha256:e85be844...`, and `ngspice=44.2+ds-1` pinned (a missing pinned package fails the build, it never changes the version silently). The user runs the build (it needs the network). The recipe holds only these pins: the two base digests and `ngspice`. No SKiDL package is installed. `env` then reports the local image ID and the measured versions. The explicit setup procedure in `BUILD.md` compares them with `toolchain.lock.json` and revises the lock (image, digest, versions) with an edit that the user or agent makes on purpose. There is **no** `env --adopt-image` command. A rebuilt image has another ID: `check` returns exit 2 until the lock is revised. A revised lock does not certify the `gui` adapter for the new image (section 11). No standalone support claim is made until the standalone test of section 14 passes. |
| Container command | `podman run --rm --pull=never --network none --security-opt label=disable -w /work -v EXEC:/work -v WORKER:/worker:ro IMAGE ...`. `EXEC` and `WORKER` are **disposable copies**. The live project, the installed skill, the repository, a host socket and other directories are never mounted. Argument arrays only. SKILL.md does **not** claim SELinux confinement for these runs. |
| Tool commands | Measured forms: `kicad-cli version`, `ngspice --version`, `uv --version` (all measured exit 0 in the image). |
| Worker | `uv run --no-project --no-config --offline --python /usr/bin/python3 python WORKER ARGS`. Diagnostics on stderr, structured output on stdout. Native: find an interpreter that imports the installed `pcbnew`. |

## 5. Commands

All Python runs through `uv run`. A command that writes holds `project_lock` for the whole operation. `env` and read-only commands take no lock.

| Command | Operation |
|---|---|
| `pcb.py env [--project DIR] [--runtime ...] [--image REF] [--json]` | Capability and version report. Works without a project. |
| `pcb.py check [--for erc\|drc\|sim\|export\|ready]` | Validate records (`validate.py --project`, and `validate.py FILE` for each `components/*.yaml`: the part records are design records, not an assembly package). Verify each mandatory result against the current inputs. Refuse `skidl`. |
| `pcb.py erc` / `pcb.py drc [--refill-zones]` | `kicad-cli sch erc` / `pcb drc --schematic-parity`, each with `--exit-code-violations --severity-all --format json`. Refill adds `--refill-zones --save-board` on a staged copy. |
| `pcb.py sim` | `ngspice -b CIR -o LOG` for each circuit of `simulations/`. Compare each `.meas` value with `assertions.json`. |
| `pcb.py settings [--apply]` | Read the three saved plot settings. `--apply` writes `drillshape 0`, `usegerberattributes no`, `usegerberadvancedattributes no` (each entry once). |
| `pcb.py update --adapter manual\|gui [--replace on\|off] [--delete on\|off] [--relink on\|off]` | Default `manual`. See section 11. |
| `pcb.py interface --apply --expect FILE` or `pcb.py interface --record-review --reviewer NAME --examined POINTER...` | Rebind `board-interface.json` only when a whole-board comparison with the predeclared expected file proves the represented geometry unchanged. When rebinding is refused, write the review record (section 13). |
| `pcb.py export [--dest PATH]` | Neutral exports with checks (section 10). |
| `board_inventory.py BOARD` | Worker: hole and placement inventory through `pcbnew`. |

## 6. Exit codes (the lead table; precedence 3, 2, 1, 0)

| Exit | Meaning |
|---:|---|
| 3 | Tool execution or result failure: tool exit not in its declared set (0 or 5), crash, timeout, missing output, unparsable report or log, **missing measured value**, post-replacement or post-rename synchronization failure (`PostReplaceError`, `PostRenameError`). |
| 2 | Incorrect invocation, missing prerequisite, runtime mismatch, or a **recognized unsupported** source, geometry, setting or adapter. An absent configured assertion file. An existing export destination. |
| 1 | Invalid record (including a **malformed** assertion record), unwaived violation, failed assertion or comparison, stale or missing mandatory readiness evidence, lock refusal. |
| 0 | Complete success under the operation's policy (`pass_with_waivers` included). |

Every finding stays in the report. A raw tool exit 5 maps to wrapper exit 0 only when every finding has a valid waiver. The raw exit stays in the report.

## 7. Findings and waivers

- Error, warning and **exclusion** findings are violations until a valid waiver covers them. A KiCad UI exclusion alone is not a project waiver. Informational tool diagnostics stay visible and do not fail.
- Parity and connectivity checks cannot be disabled through ignored-check settings: a project that ignores `unconnected_items` or `schematic_parity` fails (`settings.ignored_connectivity_check`, exit 1).
- B234 semantics are kept. Every waiver binds the current PCB bytes and the declared revision. An ERC waiver also binds the current schematic bytes. A DRC waiver matches the schematic bytes when its `schematic_sha256` is not null. Kind, rule and **all** object identifiers must match. A waiver that matches no finding is stale (exit 1).
- No operation renews a waiver hash. After a board change the user must renew waivers. Consequence: any board change stales every ERC waiver (they bind the board).
- **Object identifiers are exact KiCad item UUIDs.** The B234 schema permits arbitrary identifier strings, and a waiver lists the UUIDs of the items of its finding. ERC items are pin UUIDs (measured: the three \`pin_not_connected\` items of the T5 report are the pin UUIDs of the schematic). DRC items are pad, track, via or footprint UUIDs. Reference labels stay in the report for display only. A pad UUID is never collapsed to its footprint reference.
- **Match rule:** the set of UUIDs of the waiver equals the set of item UUIDs of the finding (exact set equality, no superset, no duplicate entry). A waiver for a subset or a superset does not apply.
- **Ambiguity:** an item UUID that occurs more than once in the project (a repeated hierarchical sheet shares symbol UUIDs) cannot be waived: the finding stays unwaived with \`waiver.ambiguous_object\` (exit 1). A report item without a UUID or with the nil UUID stays unwaived (\`waiver.object_unidentifiable\`, exit 1). In the 14 rule types of the B5 reports (498 items) every item had a non-nil UUID.

## 8. Reports, freshness and input closure

For each operation (`erc`, `drc`, `sim`, `export`):

| File | Content | Rule |
|---|---|---|
| `out/reports/raw/NAME-SHA256.json` (or `.log`) | The tool bytes, dates included | Immutable. Named by the full hash of its bytes. |
| `out/reports/NAME.binding.json` | Command, tool and runtime versions, raw hash, **full** hashes of the input closure | Written second. |
| `out/reports/NAME.result.json` | Decision: status, findings, waived list, current output directory for `export`, and the full SHA-256 of the binding file | Written **last**. No time, no raw hash. |

A result without its binding or raw file counts as missing. `check` compares the binding-file hash in the result with the current bytes of the binding file. A mismatch is incomplete evidence (exit 1). A later run can write a new binding and stop before its result. The old result then fails this comparison. Identical binding inputs and raw bytes reproduce the wrapper. A dated raw report changes the binding hash, so repeatability claims compare decision fields, not result bytes. Tests use a stub tool or compare decision fields.
**Input closure:** the board, **all** schematic sheets (found by walking `Sheetfile` entries, each path confined to the project), the KiCad project file, library tables and project rules (`.kicad_dru`), project-local libraries, `export.yaml`, `waivers.yaml`, `board.yaml` revision, `toolchain.lock.json`, and for `sim` the circuit and `assertions.json`.
Execution uses a staged snapshot of this closure. **Before publication the wrapper rechecks the live hashes and refuses a changed source.**
`check` needs a current ERC, a current DRC with parity, a current simulation when `simulations/` exists and, for export readiness, the current export result. Missing or stale is exit 1. An export needs the current clean electrical results, not an earlier export.
Refill binds the report to the saved board hash after the run. If the bytes do not change, existing bindings stay valid. Retained `.failed` history and temporary directories are listed (information) and do not block a later valid revision.

## 9. Writes and publication

| Step | Mechanism |
|---|---|
| Tool run | In a new empty staging directory under `out/`. The tool never writes the live files. |
| Board replacement (refill, `settings --apply`, adapter update) | Verify the staged board (parses; identity comparison shows only the expected differences). **Preserve the prior board** by exclusive create at `out/history/boards/FULLHASH.kicad_pcb` before the replacement. Recheck the live hash. `atomic_write`. |
| Report publication | `atomic_write`: raw, binding, result last. |
| Export publication | Stage in an empty directory, run all commands and checks, then `publish_dir` to a new destination. **No replacement mode.** An explicit confined `--dest`, or `out/export/HASH12-N` chosen under the lock. An existing destination (symbolic link included) is exit 2. The export result record names the published directory and holds the full hashes. `check` reads that record. It never uses a mutable symlink or directory order. A failed export is not published and writes no success record. |

Accepted helper limits stay in SKILL.md: before replacement or rename a handled failure keeps the old bytes or leaves no new destination. After it, a synchronization failure leaves the new bytes visible (exit 3). No rollback across files, no power-loss or network-file-system claim. `settings --apply` lists the bindings that it invalidates.

## 10. Inventory worker and neutral export checks

**Worker.** `board_inventory.py` uses the installed `pcbnew` to **read** the saved board (the missing updater does not prevent reads). It keeps KiCad's transformed coordinates and the multiplicity (multisets). It lists: copper order; footprint reference, board position, rotation, side; every drilled pad (type, position, drill size and shape); every via (position, drill, layer span).
Measured (read-only probe, `results/b6-probe/`): hole multisets equal the Excellon output for the final board, for J1 rotated 90 degrees, and for J1 rotated 90 degrees and flipped to the bottom; placement side, rotation and position equal the `pos` file.
**Unsupported geometry is refused with named objects, exit 2** (slot or oval drill, via that is not through-board, unsupported drilled pad type, copper layer that the export settings do not name). Nothing is omitted. The outline is **not** restricted: the worker does not need it (section 13).
The placement filter is one function used by the export and the inventory. Mounting holes are included when the CLI placement output includes them.

**Export checks.** (1) Saved plot settings equal the contract. (2) File set equals the layers and suffixes of `export.yaml`. (3) No active `%TF`, `%TA`, `%TO` or `%TD` command in any Gerber. (4) One `G04 #@! TF.FileFunction` comment per Gerber, matching the role of the export layer and the copper order of the board (`Copper,Ln,Top|Inr|Bot`). A swapped file, a missing, duplicate or incorrect declaration fails. (5) Drill files: plated and non-plated split; hole multiset equals the inventory. (6) Placement rows equal the inventory, exactly one row for each footprint. (7) Excellon header equals the contract.
Export settings that the schema allows but the measured subset does not cover (X2 on, other zero suppression or decimals, board origin) are refused: `export.unsupported_setting`, exit 2. The trial's independent constants stay as regression evidence. The expected values for a general board come from the inventory, which shares KiCad's reader with the exporter. SKILL.md says so.
Commands: the measured B5 forms (`pcb export gerbers --no-x2 --precision 6 --board-plot-params`, `pcb export drill` with `suppressleading`, `-u mm`, `--excellon-separate-th`, `pcb export pos`, `pcb export step`, `sch export pdf`).

## 11. Update adapter

`manual` (default): writes the handoff file, **preserves the current board** under `out/history/boards/`, reports `update.manual_required` (exit 2) and stops dependent steps. After the user saves the board, the agent runs `drc` (parity) and the identity comparison.
`gui` (explicit option; SKILL.md lets the agent choose it when `env` reports that the preflight succeeds, without new permission for an already authorized local edit): image ID, KiCad 10.0.5, Xvfb 1600x1000, otherwise `update.adapter_unavailable` (exit 2).
The adapter works on a staged copy with an explicit project basename. It measures: option states against the request, normal KiCad process exit (the trial script returns 0 after some forced stops, so its return code alone proves nothing), the expected identity differences (predeclared file), and **full parity**. It publishes through the accepted helper only when these pass.
An updated board can still need routing. The result records its full DRC diagnostics (unconnected items and others) and the state **not ready**. Parity findings block publication. Other diagnostics do not. Normal export still needs the current mandatory results. One integration edit tests the adapter. The B5 experiments are not repeated.

## 12. Template

A **bare-board design project**: `board.yaml` (`assembly: bare_board`), `variants.yaml`, `components/part.yaml` (design records, validated separately), neutral `manufacturing/supplier.yaml` with its note, `manufacturing/export.yaml`, empty `manufacturing/waivers.yaml`, `toolchain.lock.json` (`execution: container`, image and digest, measured versions), `mechanical/board-interface.json`, `mechanical/interface-review.json` (written by `pcb.py interface --record-review` for the template's own interface, with the reviewer name `template-author`; the list of examined pointers covers all top-level keys; SKILL.md labels this as a self-review), the KiCad project, library tables, schematic and board, `simulations/` (circuit and `assertions.json`), `docs/layout-notes.md`. No package builder.
**Assertion record:** a list of `{circuit, measurement, expected, tolerance}`. `tolerance` is the maximum **absolute** difference in the units of the measurement, finite and not negative. A duplicate `(circuit, measurement)` pair is a malformed record (exit 1). An absent configured file is exit 2. No expression language. The template record: 2.086 V with tolerance 0.02086 V (one percent of the independent target).

## 13. Interface rebinding: proof of unchanged represented geometry

A bounding box and the mounting holes are **not** a proof. The interface also holds thickness, cutouts, plated holes, connector frames and other values. B6 therefore compares **whole boards**, not interface fields.
`pcb.py interface --apply --expect FILE` rebinds only when **all** of these hold. Then it rewrites only `board_sha256` through `atomic_write`.

1. The full hash in `board-interface.json` names a preserved prior board in `out/history/boards/` and the bytes of that file hash to that name.
2. `FILE` is the **predeclared** expected-difference file (`identity.py` format). Its SHA-256 equals the hash that the update, settings or refill operation recorded in its binding **before** it changed the board. A file that is absent, or changed after that record, refuses the rebinding. An operation that expects no value change (settings, refill, a plot-only change) writes an empty list `{"differences": []}` as its predeclared file.
3. The prior and the current board are equal after the normalization below. The parser is the unchanged `sexp.py`. Both trees are dumped in one canonical form and compared in full.

**Normalization (exactly these three, nothing else):**

| # | Allowed to differ | Condition |
|---|---|---|
| a | The text of the `Value` property of a footprint | **Only** for a reference that a `changed`, `footprint`, `value` entry of the **predeclared** expected file names, and only when the prior text equals its `before` and the current text equals its `after`. The observed difference never supplies a permission. A value change that the file does not declare refuses the rebinding. |
| b | The values of exactly three entries of `pcbplotparams`: `drillshape`, `usegerberattributes`, `usegerberadvancedattributes` | Each must occur once in each board. |
| c | The derived zone-fill cache: each node `filled_polygon`, with its whole subtree (measured children `layer` and `pts`; an `island` child would sit inside it), that is a direct child of a `zone` node | None else |

**Not excluded (named so that nobody infers a broad list):** `fill` (and its `thermal_gap`, `thermal_bridge_width`, `island_removal_mode`), `filled_areas_thickness`, `hatch`, `min_thickness`, `connect_pads`, `polygon` (the zone outline), `net`, `net_name`, `name`, `priority`, `fill_segments`, and every other setting. A setting is not a cache. `filled_areas_thickness` stays compared unless a later measured test shows that it is derived.
Also retained and compared: version and generator fields, layers and stackup thickness, `setup`, nets, footprint library IDs, positions, rotations, pads, models, tracks, vias, graphics (outline, cutouts), groups, dimensions, connector placement, UUIDs.
The identity reader's broad ignored-form list is **not** used.

**Measured (container, KiCad 10.0.5; `results/b6-probe/c6c_refill_final_r2_stripped/`, step `C6c_refill_205`):** the KiCad-saved final board with its `filled_polygon` node removed, refilled with `drc --refill-zones --save-board`, is **byte-identical** to the original. The only difference between unfilled and refilled is the `filled_polygon` node (children `layer` and `pts`). Limits: one zone, one layer, one island, one board.
**Second measurement (step `C6_refill_203`, `results/b6-probe/c6_refill/`):** a hand-written (text) unfilled board changes more on its first KiCad save: D1 graphic items are reordered with new UUIDs, `filled_areas_thickness` is dropped and the `fill` node is rewritten, besides the new `filled_polygon`. The rule refuses to rebind across such a first save. That is intended: it is a serialization change that this rule does not prove harmless.

If the prior board is absent, the expected file is absent or changed, or any other difference exists, the command refuses (`interface.prior_missing`, `interface.expectation_missing` or `interface.geometry_changed` with the first differing object, exit 1) and `check` reports `interface.geometry_stale` (exit 1). The agent must revise and examine the interface data. Readiness stays incomplete until the review record below exists and is current. Outlines are not restricted to rectangles. B11 can add general mechanical validation later.

**Review record (resolves C1).** One small strict-JSON file, `mechanical/interface-review.json`, written by `pcb.py interface --record-review --reviewer NAME --examined POINTER...`. It is a skill record, not a contracts-registry record: no schema is added to `contracts/`, and `pcb.py` validates its own fields. It is an acknowledgement, not machine proof, and SKILL.md says so.

| Field | Content |
|---|---|
| `record` | the fixed string `pcb-design/interface-review` and `version` `1` |
| `board_sha256` | full hash of the current board |
| `interface_sha256` | full hash of the current `board-interface.json` bytes |
| `reviewer` | non-empty string given by the caller. B6 cannot verify who the reviewer is. An agent that reviews its own edit writes its own name, which is **not** an independent review. |
| `examined` | non-empty list of JSON pointers into `board-interface.json` that the reviewer examined |
| `statement` | short text of what was checked against the final board |

`--record-review` refuses unless: the interface `board_sha256` equals the current board; every pointer exists; and `examined` contains every pointer whose value differs from the prior interface. The wrapper preserves the prior `board-interface.json` by exclusive create at `out/history/interfaces/SHA256.json` together with the prior board. If the prior interface is absent, `examined` must list all top-level keys of the interface.
`check` accepts the interface only in one of two states: (1) an **automatic** rebinding whose `interface.result.json` binds the prior board hash, the current board hash and the predeclared expected-file hash; (2) a current review record (both hashes equal the files). A hash that was edited by hand with neither record gives `interface.geometry_stale` (exit 1). Any later change of the board or of the interface makes a review record stale.

## 14. Acceptance tests (focused, no new framework)

| Test | Where |
|---|---|
| Installed skill from an unrelated directory (schema path, template validation, host-to-container worker path); the four script copies equal their sources | host and container |
| `env` with no project; missing tool, wrong version, absent optional simulator; locked runtime missing (exit 2, no fallback); explicit conflicting runtime (exit 2); disposable mounts only, no pull | host and container |
| Exit mapping and precedence with a stub tool: 0, 5, 1, no output, malformed output, mixed failures; malformed vs absent assertion file; existing export destination; unsupported source, setting, adapter | host |
| Waivers: ERC with both hashes, DRC with null and non-null schematic hash, exact objects, unrelated object, stale hash, revision mismatch, exclusion without waiver, blanket rule | host |
| Inventory: rotated part, bottom through-hole part, plated and non-plated holes, via, four-layer mapping; slot refused with named objects | container (once), host fixtures |
| Freshness and closure: change a sheet, a library table, a rule file, the waivers, the assertion record, the lock; source changed during a run; refill on a filled and an unfilled board | host and container |
| Writes: failure before and after replacement and rename (accepted hooks), interrupted staged write, prior board preserved, existing destination, failed export leaves no success record, failed history does not block a later revision, **one interruption after binding publication and before result publication** (`check` refuses the binding-hash mismatch, exit 1) | host |
| Interface: plot-only change, declared value-only change and refill rebind. Undeclared value change, expected file absent or altered after the update record, thickness, cutout, hole, footprint position, model, connector, library ID, `fill` or `filled_areas_thickness` change, prior board missing: all refuse | host and container |
| B5 independent trial expectations and the swapped-layer, attribute, drill and duplicate-row negatives (kept) | host |
| Adapter: preflight refusal on another image or screen; one integration edit with predeclared differences and full parity | container |
| Standalone runtime: build from `runtime/BUILD.md` (the user runs it), then `env`, `erc`, `drc`, `sim`, `export` and the worker through the bundled image. Required before any standalone support claim | clean host, container |

**Agent runs (one each; artifact checks decide):** the installed skill, `claude -p` with `--model`, `--output-format stream-json`, `--no-session-persistence`, `--permission-mode`, `--allowedTools`, `--max-budget-usd`; the record keeps prompt, flags, model ID, transcript path, environment and artifact hashes.
- **Task A (successful edit, adapter available):** "Change the time constant of the RC network from 1 ms to 2 ms. Keep C1 at 100 nF. Make the board ready and test the response." The test declares **before** the run: R2 = 20 kohm, V(1 ms) about 1.2984 V for a 3.3 V step (3.3 x (1 - exp(-0.5))), absolute tolerance 0.012984 V. It does not derive the target from the agent's result. Checks: identity (only the value of R2 changes, no footprint or track UUID changes; this file is also the predeclared expectation for the interface rebinding), DRC with parity exit 0, ERC exit 0, an independent ngspice run of the resulting circuit within the declared target, bindings equal the files, interface rebinding by whole-board comparison, export checks.
- **Task B (adapter disabled):** same task. Pass only if the schematic edit exists, the handoff and the preserved prior board exist, `check` exits 1, and the final message does not claim readiness. The record names the manual operator and does not call the result unattended.
- **Task C (hierarchy limit):** "Move R2 to a new sheet and keep identity." The agent must warn. The test passes if no identity-kept claim is made.
Limit: one run each, a smoke test of the guidance. Repeated and multi-host evaluations are B12.

## 15. Concrete conflicts and gaps (answers needed before implementation)

| ID | Finding | Proposed answer |
|---|---|---|
| C1 | **Closed (lead).** One strict-JSON review record bound to the full board and interface hashes, with `reviewer` and `examined` fields (section 13). Acknowledgement, not proof. No B11 dependency. | Refinements: `examined` must cover the changed pointers (prior interface preserved); a self-review is labeled as such; the record is a skill record outside the contracts registry. |
| C2 | **Closed (lead).** Bundled fixed build recipe, `env` reports identity and versions, an explicit setup procedure revises the lock after comparison, no `env --adopt-image`. | **Refinement accepted by the lead.** B6 refuses SKiDL, so the SKiDL venv (`requirements.lock`) is omitted from the skill runtime. The recipe bundles only the base digests and the pinned `ngspice`. The hashed `requirements.lock` stays in the trial. The standalone runtime is tested before any support claim (section 14). |
| C3 | **Closed (lead).** Exact KiCad item UUIDs, labels for display, no collapse of pad UUIDs (section 7). | Refinements: exact set equality; a UUID that occurs more than once in the project is unwaivable (`waiver.ambiguous_object`); a missing or nil UUID is unwaivable (`waiver.object_unidentifiable`). Both are exit 1, because the finding stays an unwaived violation. |
| C4 | **Unsupported source is exit 2 now.** Earlier text (proposal D6, Codex, Pi) said exit 1 for `source.skidl_unsupported`. The lead table says exit 2 for a recognized unsupported source, setting, geometry or adapter. | Follow the lead. The earlier documents stay as history. |
| C5 | **Closed (lead).** A supported export contract with disagreeing saved board values is a comparison failure, exit 1 (`export.plot_settings`). A requested export contract outside the measured subset is exit 2 (`export.unsupported_setting`). | None. When both occur, exit 2 wins by precedence. |
| C6 | **Zone-fill cache fields.** Resolved by measurement (section 13): the one derived form is the `filled_polygon` node under `zone`. Refill of a KiCad-saved board was byte-identical to the original. `filled_areas_thickness` and `fill` are **not** excluded. | Closed for the measured case. A refill that changes any other form refuses automatic rebinding. The agent then uses the review record (section 13). |
| C7 | **Prior board exists only for operations through the wrapper.** A user who edits the board in KiCad without a handoff leaves no prior copy. | Rebinding is refused (`interface.prior_missing`). The manual route preserves the board at handoff. SKILL.md says so. |
| C8 | **ERC waivers bind the board.** Any board change, even routing, stales ERC waivers, and no operation renews them. | Accepted consequence of B234. SKILL.md states it. |
| C9 | **`--security-opt label=disable`** supersedes the `:Z` text of both reviewer reports. It was measured only for `kicad-cli version`, a file write and ownership. | The B6 container test runs the full ERC, DRC, export and worker path with it before review. |
| C10 | **Closed (lead, Codex C10).** Section 8 gave mutable binding and result files, but the result did not name its binding. A later run can leave an old success result beside a new binding. | The result holds the full SHA-256 of the binding file. `check` compares it and refuses a mismatch (exit 1). One interruption test runs after binding publication and before result publication (section 14). Repeatability claims compare decision fields, not result bytes. |

## 16. What stays trial-only

Unchanged from the proposal: pixel-based GUI drivers and podman paths (`trial_env.sh`, `gui_probe*.sh`, `limit_probes.sh`, `vz_gate.sh`), edit and expectation makers (`edit_native.py`, `gate_expect.py`, `probe_expect.py`, `make_*.py`, `trial_native_writer.py`), `layout.py` (trial constants), `check_exports.py` and `check_rc.py` (logic adapted, constants kept as evidence), `compare_kibot.py`, `trial.kibot*.yaml`, `erc_probe.py`, `build_draft_package.py` (design reference for B8), `b6_probe_inventory.py` (design probe), `results/`.
`gui_update.py` moves into the skill only after the boundary repairs of section 11 (staged copy, explicit basename, option and exit measurement).

Open limits stay in SKILL.md: one fixture, one machine, one KiCad version, no supplier qualification, no zone refill inside a GUI update, U3 and U5 untested.
