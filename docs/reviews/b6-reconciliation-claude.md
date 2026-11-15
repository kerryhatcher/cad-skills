# B6 reconciliation (claude-skill-dev)

Date: 2026-11-14 07:16:03 UTC. Inputs: `b6-design-root.md`, `b6-design-codex.md`, `b6-design-pi.md`, the lead message of 07:13 UTC, my `b6-response-claude.md`.
The proposal (`441af68e...`) and the response (`1b600087...`) are **unchanged**. This report gives one reconciled interface. It starts no implementation.
Where I changed my own earlier position, I say so. Items that need a lead decision are in section 9.

## 1. Exit codes: one table

Both reviewers and I agree on the precedence **3 > 2 > 1 > 0**. The differences were the class of unsupported input, of plot-setting disagreement and of lock refusal. I align with Codex and with the accepted helpers
(`project_io.py` refusals are exit 1, `validate.py` invalid record is exit 1). **My response put unsupported geometry and disagreeing settings in exit 2. I withdraw that.**

| Exit | Meaning | Examples |
|---|---|---|
| 3 | A tool ran but failed, or its result is unusable | tool exit not in its declared set (0 or 5), crash, timeout, missing output file, unparsable report or log, no measured value after a simulation run, `PostReplaceError`, `PostRenameError` |
| 2 | The command cannot start or cannot be given what it needs | bad arguments, missing project or input file, missing schema directory, missing runtime, tool or image, image digest mismatch, missing or invalid assertion record, existing export destination, manual update required |
| 1 | The project fails the policy | invalid record, `source.skidl_unsupported`, unsupported geometry (`inventory.unsupported_geometry`), unsupported export setting, saved plot settings disagree, unwaived finding, stale waiver, failed assertion, failed export check, missing or stale mandatory report, lock refusal, toolchain mismatch |
| 0 | Success under the stated policy. `pass_with_waivers` is exit 0 and lists each waived finding. | |

The raw tool exit stays in the report. A raw exit 5 maps to wrapper exit 0 only when every finding has a valid waiver.

## 2. Runtime selection: one rule

`--runtime auto|container|native` (default `auto`). **I withdraw `--security-opt label=disable`.** Reason: all B5 runs used `:Z` on a temporary copy, and `label=disable` lowers the container confinement. `:Z` on a disposable execution copy changes only that copy.

| Item | Rule |
|---|---|
| Choice in `auto` | `container` when the lock names an image and `podman` has it locally. Else `native` when `kicad-cli` is on `PATH`. Else exit 2 (`env.no_runtime`) with the missing prerequisites. |
| Image | The lock digest (the local image ID) is the identity. A tag is only a lookup. The wrapper compares `podman image inspect` ID with the lock. A mismatch is exit 2. Never pull, never build. |
| Container command | `podman run --rm --pull=never --network none -w /work -v EXEC:/work:Z -v WORKER:/worker:ro,Z IMAGE ...`. `EXEC` is a fresh temporary copy of the inputs. `WORKER` is a temporary copy of the worker files. Argument arrays only. No socket, no other mount. The installed skill and the project are never relabeled. |
| System-Python worker | `uv run --no-project --no-config --offline --python /usr/bin/python3 python WORKER ARGS`. Diagnostics on stderr, structured output on stdout. |
| Native | The wrapper finds an interpreter that imports the installed `pcbnew`. It does not assume its own interpreter. Native tool versions are measured and compared with the lock. A difference is a finding `toolchain.mismatch` (exit 1) until the user updates the lock. |
| `env` | Needs no project. Reports host tools, images, the chosen runtime and capabilities separately. A missing optional tool (`ngspice`) does not fail an ERC request. A requested operation without its tool is exit 2. |

## 3. Inventory worker uses `pcbnew` (measured now)

The lead's point is right: the missing **updater** does not stop `pcbnew` from **reading** geometry. I measured it (read-only, no implementation: `results/b6-probe/`, logs `B6probe_plain_199` to `B6probe_tht_202`).
The `pcbnew` module of the image (system Python) lists each footprint (reference, board position, rotation, side), each pad hole (type, board position, drill size) and each via hole (position, drill, span), and the copper layer order.

| Case | Result |
|---|---|
| Corrected final board | 6 holes. The multiset (type, diameter, x, -y) equals the Excellon files. |
| J1 rotated 90 degrees, C1 flipped to the bottom | Hole multiset equals the Excellon files. Placement side, rotation and position equal the `pos` file. |
| J1 (through-hole) rotated 90 and flipped to the bottom | Hole multiset equals the Excellon files. J1 side `bottom`, rotation 90 in both. |

So the worker takes KiCad's transformed coordinates from `pcbnew` and adds no rotation or mirror of its own (Codex). My text-transform design is **withdrawn**.
The convention of the exports is one fixed rule in the worker: export Y = negative board Y (measured B5). The import prints assertion messages on stderr. The worker treats stderr as diagnostics only.
Limits of the probe (all stay as refusal cases): circular drills only, one board, no slot, no blind or buried via, no inner layers, no custom pad. Multiplicity is kept (multisets, never dictionaries).
The worker refuses with `inventory.unsupported_geometry` (exit 1, object listed) for a slot or oval drill, a via that is not through-board, a drilled pad of an unsupported type, and an inner-layer case that the export settings do not name. It never omits an object.
The worker includes the mounting-hole footprints because the CLI placement file includes them. The placement filter is one function used for the export check and for the inventory.

Layer functions come from `export.yaml` and the copper order of the board (`Copper,L1,Top` to `Copper,Ln,Bot`). The trial constants stay as regression evidence.
Export settings that the schema allows but the measured subset does not cover (X2 on, other zero suppression or decimals, board origin, drill marks) are refused with `export.unsupported_setting` (exit 1). Schema validity does not mean support.

## 4. Waivers, reports and freshness

- **Waiver binding.** ERC and DRC waivers both bind the exact board and schematic bytes (lead). A waiver matches kind, rule (the finding type), **all** objects of the finding, revision and both hashes. A rule that matches other objects does not waive them. A waiver that matches no finding is stale (exit 1).
- **Severity policy.** Any unwaived finding of severity error or warning is a violation. KiCad also reports severity `exclusion` (a violation that a user excluded in the KiCad UI). I propose to treat it as an unwaived violation (section 9, decision E1).
- **Three files for each operation** (resolves D4 between Pi and me): `out/reports/raw/NAME-FULLHASH.json` (tool bytes with dates, hashed, never changed); `NAME.binding.json` (command, tool versions, raw hash, complete hashes of all inputs: board, **all** schematic sheets, project file, library tables, `export.yaml`, waivers, toolchain lock, circuit and assertion record); `NAME.result.json` (the decision: status, findings, waived list, no time, no raw hash). The 12-character hash is only part of the name. Identity is the full hash inside. Publication order: raw, binding, result last. A result without its binding or raw file counts as missing.
- **Determinism claim.** Only `result.json` can repeat, and only when the findings repeat. Tests use a stub tool or compare decision fields.
- **Readiness (`check`).** All applicable mandatory results are current: ERC, DRC with parity, the simulation when `simulations/` exists, and for export readiness the export record. Missing or stale gives exit 1. An export needs current clean ERC, DRC and simulation, not an earlier export.
- **Refill.** The report binds to the saved board hash after the run. If the bytes did not change, the older bindings stay valid. Both cases are tested.
- **Assertion record** (`simulations/assertions.json`): a list of `{circuit, measurement, expected, tolerance}`. Expected and tolerance must be finite numbers, the pair `(circuit, measurement)` must be unique. No expression language. A simulation directory with no record is exit 2. A log with no value for a declared measurement is exit 3.

## 5. Board interface: a hash refresh does not validate geometry (lead)

`mechanical/board-interface.json` binds the board hash and holds the outline and the holes. After an update, a settings change or a refill, the hash binding is stale. A hash refresh alone does not show that the geometry is still right.
Proposal: `pcb.py interface [--apply]` reads the board geometry with the worker (outline bounding box, the non-plated mounting holes) and compares it with the record within `geometry_tolerance_mm`.

| Case | Behavior |
|---|---|
| Equal (plot-only change, refill) | `--apply` rewrites only `board_sha256` through `atomic_write`. |
| Different (edited geometry) | Refused. The finding `interface.geometry_mismatch` lists the differences (exit 1). The agent revises the dimension fields from the board and the owner rule of the record, then runs the check again. No automatic dimension rewrite. |
| Outline that is not a rectangle | `inventory.unsupported_geometry` (exit 1). B11 owns general outlines. |

`check` reports `interface.board_hash_stale` and `interface.geometry_mismatch` separately. Rerunning DRC alone never clears them.

## 6. Writes and publication (agreed points and the one conflict)

Agreed by all: lock for the whole operation; staging directory for every tool run; the tool never writes the live board; verify the staged result (parses, identity comparison shows only the expected differences; refill shows none); recheck the live source hashes before replacement and refuse a changed source; board replacement with `atomic_write`;
reports with `atomic_write`, raw first and result last; exports staged in an empty directory and published with `publish_dir`; a failed export is never published; the accepted limits of the helpers stay in SKILL.md (no rollback across files, no power-loss claim, `PostReplaceError` and `PostRenameError` give exit 3 and visible new state).
**One conflict:** Pi proposes `export --replace` with a history move. Codex and I propose no overwrite protocol. **Resolved: no `--replace`.** An existing destination is refused (exit 2, symbolic link included). The caller gives `--dest` or accepts the default `out/export/HASH12-N` with the next free N.
`settings --apply` is explicit, verified in staging (only the three settings change), written with `atomic_write`, and lists the bindings that it invalidates.

## 7. Update route, schema path, template

- **`pcb.py update --adapter manual|gui [--replace on|off] [--delete on|off] [--relink on|off]`.** Default `manual`. `manual` writes the handoff file (input hashes, pending operation, expected differences, exact options), reports `update.manual_required` (exit 2), and the agent stops the dependent steps. `gui` is optional, runs in an isolated container with its own Xvfb on a staged copy with an explicit project basename (not `trial`), and refuses outside the tested image, KiCad version and screen (`update.adapter_unavailable`, exit 2).
  It fails on: a measured checkbox state that differs from the request, a timeout, a missing window, an abnormal KiCad exit (the trial script returns 0 after some forced stops, so its return code alone proves nothing). It publishes the staged board only after the predeclared expected-difference comparison and the full parity report pass. One integration edit tests it. The six B5 experiments are not repeated.
- **Schema path** (Pi R2.3 and Codex). Existing convention (`tests/test_skill_packages.py`): the skill has `contracts/README.md` and `contracts/schemas/`. The copied `validate.py` stays unchanged and defaults to `scripts/schemas`. **The controller always passes `--schemas SKILL/contracts/schemas`.** Test: run from an unrelated directory with the repository inaccessible.
  The copies of `validate.py`, `project_io.py`, `identity.py`, `sexp.py` are not in the existing copy set. I propose a small addition to `test_skill_packages.py` that compares these four script copies with their sources.
- **Template.** `board.yaml`, `variants.yaml`, `components/part.yaml`, neutral `manufacturing/supplier.yaml` with its note, `manufacturing/export.yaml`, empty `manufacturing/waivers.yaml`, `toolchain.lock.json` (digest, versions), `mechanical/board-interface.json`, the KiCad project, library tables, schematic and board, `simulations/` (circuit and `assertions.json`), `docs/layout-notes.md`. No package builder in B6.

## 8. Acceptance: the RC-value edit (Codex), and the test list

I adopt Codex's smoke task. It proves design reasoning and has no new-routing expectation.

| Item | Value |
|---|---|
| Task text | "Change the time constant of the RC network from 1 ms to 2 ms. Keep C1 at 100 nF. Make the board ready and test the response." |
| Expected agent action | R2 from 10 kohm to 20 kohm. Update `assertions.json` for the new target. Preserve all symbol, footprint and track UUIDs. Update the PCB (value edit: a supported B5 edit). ERC, DRC with parity, simulation, interface check, export. |
| Independent target (written before the run) | V(1 ms) = 3.3 x (1 - exp(-0.5)) = 1.2984 V, tolerance 1 percent. The test runs its own ngspice with its own assertion record. It does not read the agent's record or output for the target. |
| Independent checks | Identity compare against the expectation written first: only the value of R2 changes, no track or footprint UUID changes. DRC with parity exit 0. Hashes in the bindings equal the files. The export checks pass. |
| Task A | Adapter available in the tested image. |
| Task B | Adapter disabled. The agent must stop with the handoff. `check` exit 1. The final message must not claim readiness. The record states the manual operator and does not call the result unattended. |
| Task C (negative) | "Move R2 to a new sheet and keep identity." The agent must warn and not claim identity kept. |
| Evidence limit | One run for each task. It is a smoke test of the guidance, not a reliability measure. |

The record keeps: prompt, environment, selected skill, actions, results and artifact hashes. The `claude -p` flags are those of the response (`--model`, `--output-format stream-json`, `--no-session-persistence`, `--permission-mode`, `--allowedTools`, `--max-budget-usd`).

Other tests follow the Codex and Pi lists without a new framework: installed skill from an unrelated directory; `env` with no project; missing tool, wrong version, absent optional simulator; inventory with a rotated part, a bottom through-hole part, plated and non-plated holes, a via, a four-layer mapping, a slot refused; warning-only findings, exact waiver, unrelated object, stale hashes, malformed output, missing measurement, mixed precedence; lock refusal, source change during a run, interrupted staged write, existing destination, failure before and after replacement (accepted hooks); the independent B5 trial expectations and negative tests kept.

## 9. Decisions for the lead

| ID | Question | My proposal |
|---|---|---|
| E1 | KiCad severity `exclusion` | Count it as an unwaived violation. An exclusion in the KiCad UI has no reviewer, reason or byte binding. Pi would let it pass as informational. |
| E2 | Native run when the lock names a container | Allowed. The wrapper records the measured versions. A difference from the lock is `toolchain.mismatch` (exit 1) for readiness. |
| E3 | Default adapter | `manual`. The GUI adapter needs an explicit flag. |
| E4 | Default export destination | `out/export/HASH12-N`, with the full hashes inside `export.json`. |
| E5 | Add the four script copies to `test_skill_packages.py` | Yes. It is a small extension of the accepted B4 test. |

The proposal and the response stay unchanged. I wait for the combined design review.
