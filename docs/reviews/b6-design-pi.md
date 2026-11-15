# B6 design review: Pi

Date: 2026-11-14.

**Decision: the B6 proposal is not ready for implementation. The direction is right. The interface needs the corrections below. I agree with root R1 to R6.**

I reviewed the proposal and the root review. I used the accepted B5 evidence and source reads only. I made no implementation edit and no new probe.

## 1. Reviewed bytes

| Item | Value |
|---|---|
| Proposal | `docs/reviews/b6-proposal-claude.md` |
| Proposal SHA-256 | `441af68ebbb33b72072c7aad358cece51930d5ffd107bdbdf7d0108715ff9c76` |
| Root review | `docs/reviews/b6-design-root.md`, SHA-256 `be0ca7e690712bdf6440fc72aa23eef831173078be422f6078420fc8f91d16ed` |
| B5 basis | `b5-trial-claude.md`, `b5-correction-claude.md`, `b5-acceptance-root.md` |

I measured the proposal file. The measured hash matches the hash in the root review. The earlier lead message omitted two characters. The file did not change.

## 2. Explicit agreements

I agree with the proposal on these points:

- The skill is `skills/pcb-design/` and it operates alone. It uses only its own files at run time.
- The native route uses `kicad-cli` for ERC, DRC with parity, and the neutral exports. It does not use KiBot (D5).
- SKiDL schematic generation is refused with `source.skidl_unsupported` (D6). The reason is the measured wrong connectivity in 3 of 4 runs.
- The frozen `identity.py` ships unchanged (D2). It is the identity check after a manual update.
- The neutral export settings are `drillshape 0`, `usegerberattributes no` and `usegerberadvancedattributes no`. The exported Gerbers use `.gbr` names and one `G04 #@! TF.FileFunction` comment.
- The trial image is the tested runtime (D7). The image digest is reported.
- The accepted B5 limits stay visible: one fixture, one machine, one KiCad version, no supplier qualification, no zone refill inside a GUI update, U3 and U5 untested.

I also agree with the direction of R1 to R6. The corrections below make each point testable.

## 3. R1: skill scope and the agent design/edit workflow

The proposal scope is too small. It reports, validates, checks and exports a completed template. Root R1 requires the skill to guide design, native schematic edits, placement, routing and review. A template audit must not stand as proof of an edited-board workflow.

### R1.1 Add the design and edit references

Add these to the bundled skill:

| File | Content |
|---|---|
| `references/design-workflow.md` | Requirements, datasheet and part selection, symbol and footprint assignment, power and return path, schematic capture, ERC, placement, routing, DRC and review, export. One step for each decision. |
| `references/native-edit.md` | Safe native schematic and board edits. The symbol UUID and path rules. The expected-difference file written before the update. The `identity.py` comparison after the update. |
| `references/placement-routing.md` | Placement, rotation, side, courtyard, routing, vias, zones, refill and the DRC parity review. |
| `examples/` | One meaningful edit task with the before files, the expected difference, the after files and the checks. |

State where each decision enters: a datasheet rating, a footprint choice, a power rail, a return path, a placement rule and a routing rule. Each item names the evidence and the check that closes it.

### R1.2 State the identity rules

The procedure must say:

- Keep the symbol UUID and the footprint UUID for an edit that changes a value, a field or a position.
- Do not delete and re-add a symbol unless a new identity is intended.
- Run the update with the option state that the edit needs: relink off, replace on only for a footprint change, delete unused footprints on only for a part removal.
- Write the expected difference before the update, then run `identity.py compare`.
- A changed or removed track needs an expected difference with its UUID.
- A moved symbol to another sheet loses identity, and a re-added part gets a new UUID and a default position. These are measured limits.

### R1.3 Add the optional tested GUI adapter

Do not discard the measured GUI route without an examined adapter. Add an optional adapter for the exact B5 environment:

```text
pcb.py update --project DIR [--adapter gui|manual] [--replace on|off] [--delete on|off] [--relink on|off]
```

- `manual` is the default adapter. `gui` is an explicit option, and the skill can select it when its preflight succeeds for an already authorized local edit. It requires the tested image, the KiCad 10.0.5 dialog, Xvfb, xdotool and the exact `1600x1000x24` screen. It refuses with `update.adapter_unavailable` (exit 2) if the image digest, the KiCad version, the screen size or the dialog differs. It does not ask for new permission for an already authorized local edit.
- The adapter runs the measured B5 GUI sequence. It writes the saved board, the GUI summary, the dialog option states and the KiCad process exit.
- `--adapter manual` prints the handoff checklist and stops with `update.manual_required` (nonzero). The agent must not continue as if the board changed.
- The manual fallback stays for a native KiCad installation and for an agent without GUI access. After the operator saves the board, the agent runs `drc` and the identity comparison.

State clearly: neither route is a headless schematic-update CLI. The GUI adapter is a tested automation for one image and one screen. It is not a general solution.

### R1.4 Make the acceptance test an edit task

The final test must include one meaningful agent edit, not only a template run. Example: change the value of R2 and add one part in the native schematic, write the expected difference, run the update through the optional adapter or the manual handoff, then run `drc`, the identity comparison and `export`. An independent check verifies the changed value, the added part, the preserved identities and the export. The B5 template run stays as one test, not the proof of the workflow.

## 4. R2: standalone runtime and files

### R2.1 Define native and container invocation

Add a runtime section to `SKILL.md` and to `pcb.py env`:

- Default: container. The tested image is selected by digest `sha256:d881df4ef3e2ec76995f4070596550db118b23e7f6db9017f09a418c44c4b1c2` or by the tag `localhost/cad-skills-trial:b5`.
- The container command uses `--pull=never --network none`, a temporary copy of the project mounted with `:Z`, and the tested system Python: `uv run --no-project --no-config --offline --python /usr/bin/python3 python`.
- Native: the host has no KiCad in the B5 environment. A native run requires `kicad-cli`, `ngspice` and `uv`. `env` reports the mode and the versions.
- Missing prerequisite: exit 2 with a clear `runtime.image_missing` or `runtime.tool_missing`. No image pull and no relabel of a repository path during a normal command.

### R2.2 Let `env` run before a project exists

The proposal says all commands take `--project DIR`. That is not correct for `env`. Make `--project` optional or absent for `env`, and for the schema and tool discovery. Add a test that runs `pcb.py env --json` from an unrelated working directory with no project.

### R2.3 Fix the bundled validator schema path

The current validator defaults `--schemas` to `HERE / "schemas"`, where `HERE` is the directory of `validate.py`. The proposal puts `scripts/validate.py` and the schemas at `schemas/` in the skill root. The default would be `scripts/schemas/`, which does not exist.

Choose one:

- Put the schema copy at `scripts/schemas/`, or
- Make `pcb.py` pass an absolute `--schemas <skill-root>/schemas`.

Add a test that runs the bundled validator from an unrelated working directory with no `contracts/` access. The schema path must resolve from the skill, not the caller's CWD.

### R2.4 State the complete template records

The template must contain every record that `validate.py` needs:

- `kicad/board.kicad_pcb`
- `kicad/board.kicad_sch`
- `board.yaml`
- `variants.yaml`
- `manufacturing/export.yaml`
- `manufacturing/supplier.yaml`
- `manufacturing/waivers.yaml`
- `mechanical/board-interface.json`
- `toolchain.lock.json`

The `toolchain.lock.json` records the image digest and the measured tool versions. The template must pass the bundled validator when the skill is installed outside the repository.

## 5. R3: general-board inventory

The proposal's check 5 uses `identity.py` for the expected holes. That is not sufficient. The identity reader gives a pad's UUID, position and net. It does not give the drill diameter, the plating class, the pad type, the pad local transform, the footprint side, or a via's drill. A general board needs those values.

### R3.1 Add a small board-inventory worker

Add one bounded worker, for example `scripts/inventory.py`, or a function set in `pcb.py`. It reads the saved board with the bundled `sexp.py` and returns:

- For each footprint: reference, position, rotation, side (top or bottom), and each pad's local position, drill, shape, type (`smd`, `thru_hole`, `np_thru_hole`, `connect`) and net.
- The absolute pad position after the footprint rotation and the board-side transform.
- Each via's position, drill, size and net. A via is plated.
- The plated and non-plated hole sets with diameters and positions.
- The placement rows with reference, position, rotation and side.

Keep `identity.py` unchanged. The worker is a second reader of the board, independent of the exporter. It is the expected-value source for the drill and placement checks.

### R3.2 State the unsupported geometry and fail explicitly

The worker must reject or clearly limit:

- slots and oval drills,
- custom pads and non-circular pad shapes,
- pads with an offset or a non-90-degree rotation that the transform does not support,
- a footprint on a side or layer that the worker does not handle,
- a board with an inner copper layer that the export map does not name.

An unsupported item gives `inventory.unsupported_geometry` with the reference and the pad, and exit 2 or 3. Do not silently omit it.

### R3.3 Derive layer functions from the project, not the trial map

The proposal's check 4 uses the fixed nine-layer map. That map is trial evidence. For a general board:

- Take the layer list and suffixes from `manufacturing/export.yaml`.
- Take the copper order from the saved board `(layers ...)` block.
- Map each copper layer to `Copper,Ln,Top|Inr|Bot`.
- Map mask, paste, silk and outline from the export settings and the fixed family names.

Keep the trial's nine-layer constants and the swapped-copper test as test evidence. They are not the general mapping.

## 6. R4: report semantics

### R4.1 One severity and waiver policy

Resolve the contradiction. Define one rule:

- A finding of severity `error` or `warning` fails the check unless a waiver covers it.
- An `exclusion` finding is a violation until an applicable waiver covers it. A KiCad UI exclusion is not a project waiver. Informational tool diagnostics stay visible without failing the check.
- A waiver applies only when its record binds to the exact board bytes, the exact schematic bytes for an ERC waiver (and for a DRC waiver when the schematic hash is not null), the check id, the finding code and the location.
- A waived finding is listed as `waived`. The readiness status is `pass_with_waivers` if no unwaived finding remains. A waiver that matches no finding is stale and fails (exit 1).
- The wrapper never hides a finding to reach exit 0.

The B5 measurement that a `lib_footprint_mismatch` warning counts as a violation drives this rule.

### R4.2 One exit precedence

The proposal gives exit 2 for a missing measured value in `sim`, but exit 3 for a malformed tool result in the general table. Use one order:

| Exit | Condition |
|---|---|
| 2 | Incorrect arguments or a missing prerequisite: no project, no tool, no input file, no schema directory, unsupported runtime |
| 3 | Tool failure or an unusable tool result: a nonzero tool exit other than the violation code, an unparsable report, a missing expected output, a log with no measured value |
| 1 | A design finding, an invalid record, or a missing or stale mandatory report |
| 0 | All required checks pass |

Thus a simulation log that exists but has no value is exit 3. A missing `ngspice` is exit 2. A DRC warning is exit 1. A stale report is exit 1.

### R4.3 Separate deterministic wrapper bytes from raw tool bytes

The proposal says the report has no time and the same inputs give the same bytes. The raw `kicad-cli` and `ngspice` reports contain dates and other variable bytes. Keep them exactly as the tools write them and hash those bytes.

Define two artifacts:

- The wrapper decision report, for example `out/reports/erc-<hash12>.json`. It is deterministic only if it excludes the raw report hash. The decision fields (`status`, `findings`, `inputs`, `commands`, `unprocessed`) can be deterministic.
- The raw tool report, for example `out/reports/raw/erc-<hash12>.json`. It keeps the tool bytes and their hash.

If the wrapper report includes the raw report hash, state that the wrapper bytes are not deterministic across runs. The test "two runs, same bytes" uses a stub tool with stable output, or compares only the decision fields.

### R4.4 Report freshness and refill

- `check` compares the schematic and board hashes with each mandatory report. A missing report is `unprocessed`. A report bound to other bytes is `stale`. Either state gives exit 1 for a readiness request.
- `drc --refill-zones` must not demand a board hash change. Test the actual before and after hash. If the hash changes, publish the new board and mark the old reports stale. If the hash does not change, the board is unchanged and the new report binds to the same bytes. Test both an unfilled board and an already filled board.

## 7. R5: writes and publication

### R5.1 Stage and replace with the project-I/O helpers

Use `project_io.py` for every write:

- `settings --apply`: read the board, edit the text in memory, parse it, compare the identity snapshot to show that only the three settings changed, then `atomic_write` the board. Publish a settings report bound to the new hash.
- `drc --refill-zones`: copy the board to a temporary path in the project, run `kicad-cli` on the copy with `--refill-zones --save-board`, parse the saved copy, then `atomic_write` its bytes to the project board. If the tool fails or the save is incomplete, the project board is unchanged.
- `erc` and `drc`: write the raw report to a temporary file, parse it, then `atomic_write` it to `out/reports/`.
- `export`: stage to `out/.staging/export-<hash>/`, run all commands and checks, then `publish_dir` to `out/export/`. A failure leaves the old export untouched.

Keep the lock for the whole operation. Use `confine` for every path.

### R5.2 Existing output directory

Define the behavior:

- There is no export replacement mode. `export` accepts an explicit confined destination, or it selects `out/export/<hash12>-<N>` under the lock.
- An existing destination is refused with `export.exists` (exit 2). Do not overwrite or back up an older export.
- A failed export is not published. The staging directory stays for inspection and cannot satisfy a later readiness check.
- The result record and `check` name the current published directory. Do not use a mutable symlink or infer the current directory from the order.

### R5.3 Reports required before a normal export

`export` requires current `erc` and `drc` reports bound to the exact schematic and board bytes, and the saved settings must agree. If a report is missing or stale, `export` refuses or exports with an explicit `unverified` status. State which choice applies. The B5 flow required the clean DRC and ERC before the exports.

### R5.4 Invalidate bindings on a settings change

`settings --apply` changes the board bytes. It must record the new hash, mark the old DRC and export reports stale, and make `export` refuse until `drc` runs again. The agent must run `drc` and `export` after a settings change.

## 8. R6: acceptance tests

Keep the proposal's focused tests. Add these:

| Test | Where | Pass condition |
|---|---|---|
| `env` with no project, from an unrelated CWD | host | exit 0, correct mode and versions |
| Installed skill from an unrelated CWD with no repository access | host | all commands use the bundled files; the validator finds its schemas |
| General inventory: rotated footprint, bottom-side pad, via, non-plated hole | host | the expected holes and placement rows |
| General inventory: slot or custom pad | host | `inventory.unsupported_geometry`, nonzero, no silent omit |
| Exit precedence: missing value log, missing tool, DRC warning, stale report | host and container | exit 3, 2, 1, 1 |
| Determinism: wrapper decision vs raw report | host with a stub tool | decision fields equal; raw bytes preserved |
| Refill on an unfilled board and an already filled board | container | the correct stale or unchanged branch |
| Interrupted tool write | host with a stub | the board and old reports are unchanged |
| Existing `out/export/` and a failed export | host | refuse or replace; no stale success |
| Optional GUI adapter: exact image and screen; wrong image or screen | container and host | saved board and option states; `update.adapter_unavailable` |
| Manual handoff without GUI | host | `update.manual_required`, no false success |
| One agent edit task with independent checks | container, one run | identity, value, drill/placement, reports and export agree |

Do not repeat the unchanged B5 trial experiments. Reuse the B5 evidence for the real ERC, DRC, simulation and export checks where the test does not change.

## 9. Decisions D1 to D7

| ID | Agreement or correction |
|---|---|
| D1 | Agree with `settings --apply`; `export` never writes the board. Add the atomic write, the parse and identity check, the report invalidation and the stale-before-export rule. |
| D2 | Agree: ship `identity.py` unchanged. Add the separate inventory worker for drills, plating, transforms and placement. |
| D3 | Correct: the saved board is the source, but `identity.py` cannot supply drill and plating values. Use the inventory worker. State the weaker independence and the unsupported geometry. |
| D4 | Agree with `out/reports/` and hash12 names. Put the full hash in the report, keep the raw reports beside the decision reports, and bind the freshness check to the full hash. |
| D5 | Agree: no KiBot. |
| D6 | Agree: refuse SKiDL with `source.skidl_unsupported`. Keep the U3 reference note. |
| D7 | Agree with the tested image. Add the native and container invocation, image selection, `--pull=never --network none`, the `:Z` project copy, and the missing-image behavior. |

## 10. Verdict

The B6 proposal is not ready for implementation. The core direction is accepted: standalone native skill, `kicad-cli` checks, neutral exports, the frozen identity reader, the tested image, and the B5 limits.

The required interface corrections are:

1. Add the design and edit workflow references and examples, the identity rules, and the optional tested GUI adapter with the manual fallback.
2. Define the native and container runtime, make `env` work without a project, fix the schema path, and state the complete template records.
3. Add the general-board inventory worker, the explicit unsupported-geometry failures, and the project-derived layer functions.
4. Use one severity and waiver policy, one exit precedence, separate deterministic decision bytes from raw tool bytes, and test the refill hash branch.
5. Define staged writes and publication, the existing output directory behavior, the required pre-export reports and the settings invalidation.
6. Add the host-to-container, installed-skill, general-inventory, safe-write and meaningful edit-task tests.

Claude remains the sole implementer. I agree to review the corrected interface after those changes.

## 11. Combined-interface recommendation after the response

Date: 2026-11-14.

I read `b6-response-claude.md`, SHA-256 `1b6000877eb75377ce6ae87b21b8f15478dd39c72aa71f3303eb978eda9bc1b7`, and the root findings. The response resolves most of R1 to R6. The combined interface below closes the open points. Claude remains the sole implementer.

### 11.1 D8 to D12

| ID | Resolution |
|---|---|
| D8 | Use a small `board_inventory.py`, but make the installed KiCad bindings (`pcbnew`) the primary reader. The U6 negative is about the netlist/update function. It does not disqualify `pcbnew` as a board reader. Run the worker in the selected runtime: the container uses `/usr/bin/python3` with `pcbnew`, a native run uses the native KiCad Python. A text reader is a fallback only after a measured test shows the binding is unavailable or unsuitable for the needed values. The worker returns KiCad's already transformed board coordinates. Do not apply the footprint rotation or the bottom-side mirror a second time. Return lists or multisets, not a dictionary by reference. |
| D9 | Ship the GUI adapter as optional. Keep the preflight on the image ID, the KiCad version and the screen size. Run it on a staging copy in its own container. Accept an explicit project basename. Compare the measured checkbox states with the requested states. A mismatch, timeout, missing window, forced process stop or abnormal KiCad exit fails. Publish the staged board only after the identity comparison and the full parity report pass. Keep the manual handoff for a native install or an agent without GUI access. |
| D10 | Accept the precedence 3 > 2 > 1 > 0. Use 2 for unsupported input, geometry or settings, as well as a missing prerequisite or bad arguments. Use 1 for a design or readiness failure. This resolves the Claude/Codex difference: unsupported input gives exit 2 and status `unsupported`, never a pass. |
| D11 | Accept stale detection through binding files with exact input hashes, not timestamps. Store full hashes. A 12-character hash is a display hint only. Bind the board, schematic, project file, export settings, waivers, circuits, assertions and the board interface. A missing or stale binding gives exit 1 and no ready status. |
| D12 | Accept one agent run per task as a smoke test with the limit stated. Replace the add-C2 task with the 20 kohm RC edit below. A second run stays a B12 item. |

### 11.2 Root findings

| Finding | Resolution |
|---|---|
| Inventory reader | The U6 negative does not disqualify `pcbnew` as an inventory reader. Prefer the small KiCad worker. Use a text reader only if a measured test shows a binding gap. Add a test where the worker and `kicad-cli pcb export drill`/`pos` agree on a fixture with four angles, both sides, vias and non-plated holes. |
| ERC waivers | A waiver binds both the PCB and the schematic bytes under the B234 rule. Every waiver record carries `board_sha256` and `schematic_sha256` (and the revision). For an ERC waiver, both current hashes must match. For a DRC waiver, the board hash must match and the schematic hash must match when it is not null. A match also needs kind, rule and all object identifiers. A waiver with other bytes is stale (`waiver.stale`, exit 1). A broad wildcard does not waive other objects. |
| Board interface | Do not refresh `board-interface.json` by changing only the hash after a geometry change. Reject a bounding-box-and-mounting-hole test as sufficient. Preserve the prior PCB bytes and locate the prior revision by its full hash. Permit automatic rebinding only after a conservative full-file comparison, with narrowly specified normalization, proves that the represented geometry did not change. The normalization can exclude only the permitted electrical value fields (named by the predeclared expected-difference file), the three plot settings and the derived zone-fill cache fields. It must retain thickness, outline, cutouts, holes, footprint geometry, models and connector placement. Do not use the identity reader's broad ignored-form list. If the prior revision is absent or any other field changes, refuse automatic rebinding and require the agent to revise and examine the interface. `check` reports `interface.geometry_stale`, exit 1, until that work is complete. |
| Agent task | Use the value-only RC edit, not the add-C2 task. The add-C2 task needs routing and conflicts with a clean board and a no-routing-difference expectation. |
| Runtime mounts | Use the measured `--security-opt label=disable` only with disposable execution and worker copies. Mount the worker copy read-only and the execution copy writable. Do not mount the live project, the installed skill, the repository, a host socket or an unrelated directory. Keep `--pull=never` and `--network none`. Do not claim that this preserves SELinux confinement. If a platform requires `:Z`, apply it only to the disposable copy and record the label before and after. |
| Unsupported exit | Unsupported input, geometry or settings is exit 2 with status `unsupported`. Keep exit 1 for a design or readiness failure. Use one rule in the report and the tests. |

### 11.3 The 20 kohm RC agent task

Use this as the B6 smoke test:

```text
Change R2 from 10 kohm to 20 kohm. Keep C1 at 100 nF. The RC time constant becomes 2 ms.
Update the simulation assertion for a 3.3 V step at 1 ms to 1.2984 V, with an absolute tolerance of 0.012984 V (1 percent of the independent target).
Preserve the symbols, the footprint identities, the placement and the routing. Make the board ready.
```

The independent check uses the fixed value 1.2984 V at 1 ms. It does not derive the value from the completed output.

Checks after the run:

- The identity difference is only the value of R2 from `10k` to `20k`. No footprint, path, pad net or routing difference.
- The schematic and board carry R2 = 20 kohm.
- DRC with parity gives exit 0 with no unwaived finding. ERC gives exit 0.
- The simulation gives 1.2984 V at 1 ms within the absolute tolerance 0.012984 V.
- The export checks pass 7 of 7. The reports bind to the final board hash.
- The board interface geometry is unchanged. Only its hash binding changes.
- The agent's report is not the pass source. The independent checks are.

For the adapter-disabled case, the same edit must produce the schematic change, the handoff file, `check` exit 1 and no readiness claim. For the negative case, the move-R2-to-another-sheet task must warn and must not claim identity kept.

### 11.4 Decisions root resolution

I read `docs/reviews/b6-decisions-root.md`, SHA-256 `ee4d9e175568be1acfedde1bfd4873b310965934de7b1160133629655f119d39`. It resolves the remaining differences. I agree with:

- Exit 3, 2, 1, 0 with the stated precedence. A malformed assertion record is exit 1. An absent configured assertion file is exit 2. An existing export destination is exit 2.
- `--security-opt label=disable` only with disposable execution and worker copies, a read-only worker mount, and no live project, skill, repository, socket or unrelated mount. No SELinux confinement claim.
- The locked runtime. `auto` follows `toolchain.lock.json` and its `execution` field. A missing locked runtime does not fall back silently. An explicit conflict is exit 2. `env` reports the difference. Missing `ngspice` does not prevent ERC.
- Error, warning and exclusion findings are violations until waived. A KiCad UI exclusion is not a project waiver. Informational diagnostics stay visible. Mandatory parity and connectivity checks cannot disappear through ignored-check settings.
- The conservative interface rebinding. The prior bytes and full hash are the anchor. Only a narrow normalization can permit automatic rebinding. Thickness, outline, cutouts, holes, footprint geometry, models and connector placement must stay equal. An absent prior revision or another changed field refuses automatic rebinding.
- Manual is the default adapter. The GUI adapter is explicit and selectable after its preflight. It measures the option states, the normal process exit, the expected identity differences and the full parity. It uses staging and the accepted publish helper. An intermediate board can still need routing. Record its full diagnostics and non-ready state. No new permission for an already authorized local edit.
- No export replacement mode. Use an explicit confined destination or `out/export/<hash12>-<N>` under the lock. The result record and `check` name the current directory. No mutable symlink. Recheck the live source hashes before publication. A retained failed-history directory does not block a later valid revision.
- The small assertion record with an absolute tolerance. The bare-board template with part records as design records. The explicit bundled schema path. The copy tests for `validate.py`, `project_io.py`, `identity.py` and `sexp.py`. The 20 kohm RC task. One run each for the edit, the handoff and the hierarchy limit.

The consolidated proposal must state two remaining details:

1. The source of the permitted electrical value fields for the interface comparison. Use the predeclared expected-difference file, not the observed diff. If the expected file is absent, refuse automatic rebinding.
2. The exact normalization list for the derived zone-fill cache fields. Name the derived fields. Do not exclude a setting such as `filled_areas_thickness` unless a measured test shows that it is a derived cache.

## 12. Explicit agreement with the decisions root

I agree with `b6-decisions-root.md` as the interface decision record. It resolves exit 2 capability refusals, the temporary `label=disable` mounts, the exclusion severity, the locked runtime, the conservative interface rebinding and the absolute assertion tolerance.

I have no remaining design defect. The two specification details in section 11.4 are not disagreements. The consolidated proposal must state them so the implementation cannot infer a broad allowlist or a broad normalization.

I will review Claude's consolidated proposal when it exists. B5 stays closed. No implementation starts before both reviewers agree to the consolidated proposal.

## 13. Consolidated proposal: C1, C2, C3 and C5

I read `b6-consolidated-proposal-claude.md`. The lead hash `d7144f9042c67c4e059b817b11586a5df34bc77f38b4d25992e6cba33710c35c` was the earlier version. The file changed during the review. The current bytes measure `9ea3c117004309bdd8f024d63a1a0866661e5ee41d89be00ed55fe6a002d400b`. The C1/C2/C3/C5 sections match the reviewed content and already incorporate the lead's resolutions with refinements. I agree with the lead's resolutions and the current refinements.

| ID | Lead resolution | Agreement and concrete interface |
|---|---|---|
| C1 | One small explicit strict-JSON review record bound to the full board and interface hashes, with `reviewer` and `examined`. It is an acknowledgement, not machine proof. No B11 dependency. No Markdown. | Agree. The current file has `mechanical/interface-review.json` with `record`, `version`, `board_sha256`, `interface_sha256`, `reviewer`, `examined` (pointers into `board-interface.json`) and `statement`. `--record-review` refuses unless the interface board hash equals the current board, every pointer exists, and `examined` covers every changed pointer. The prior interface is preserved at `out/history/interfaces/SHA256.json` with the prior board. A self-review is labeled as such. It is a skill record outside the contracts registry. `check` accepts the interface only with an automatic rebinding result or a current review record. A hand-edited hash with neither gives `interface.geometry_stale`, exit 1. The record does not by itself make an export ready. |
| C2 | Bundle the fixed build recipe and dependency lock for standalone setup. `env` reports local identity and versions. An explicit setup procedure can revise the project lock after comparison. No new `env --adopt-image`. | Agree. The current file has `runtime/Containerfile` and `runtime/BUILD.md` with the fixed base and uv digests and the pinned `ngspice`. `env` is read-only and reports the local image ID, the measured versions and the difference from the lock. The setup builds the image (a user action, network needed), compares the identity and versions, then revises `toolchain.lock.json` by a deliberate edit. No normal command writes the lock. A rebuilt image or a mismatch is exit 2 until the lock is revised. The unused SKiDL `requirements.lock` is not bundled. |
| C3 | The schema permits arbitrary object identifier strings. Match exact KiCad item UUIDs; keep reference labels for display. Do not collapse pad UUIDs to one footprint reference. Tracks and vias can use UUIDs. | Agree. The current file uses exact item UUIDs in the waiver `objects`. ERC items are pin UUIDs. DRC items are pad, track, via or footprint UUIDs. The report shows the reference label for display only. The match is exact set equality: no subset, no superset, no duplicate entry. An ambiguous UUID (it occurs more than once in the project) or a missing or nil UUID leaves the finding unwaived (`waiver.ambiguous_object` or `waiver.object_unidentifiable`), exit 1. My earlier exit 2 was too strong. |
| C5 | A supported export contract with disagreeing saved board values is a comparison, exit 1. An unsupported requested export contract is a capability refusal, exit 2. | Agree. The current file uses `export.plot_settings`, exit 1, for disagreeing saved values, and `export.unsupported_setting`, exit 2, for a requested contract outside the measured subset. Exit 2 wins when both occur. `settings --apply` fixes the three plot settings. A remaining detail: state the code for an absent or repeated plot-setting entry. I recommend exit 2 (`settings.unsupported_board`), because `settings --apply` cannot set it safely. |

The current file no longer has the earlier C1 Markdown, C2 `env --adopt-image` or C3 reference-mapping conflicts. It incorporates the lead's resolutions.

The proposal's section 13 resolves my two earlier open details. The predeclared expected-difference file is the only source of permitted value changes. The zone-fill normalization is the `filled_polygon` node under `zone`, and `fill` and `filled_areas_thickness` stay compared. I agree.

C4, C6, C7, C8 and C9 are consistent with the agreed interface. I found no other concrete conflict in the consolidated proposal. B5 stays closed. I agree to the interface after the four resolutions.

## 14. C10 and revision 2

The lead accepted C1/C2/C3/C5 and the narrow refinements. Revision 2 measures `9ea3c117004309bdd8f024d63a1a0866661e5ee41d89be00ed55fe6a002d400b`.

### C10: result-to-binding chain

I agree with C10. The result must contain the full hash of its binding file, and `check` must reject a mixed binding/result after an interrupted publication.

Concrete interface:

- `out/reports/NAME.binding.json` holds the raw-report hash and the full input-closure hashes.
- `out/reports/NAME.result.json` holds `binding_sha256`, the full SHA-256 of the binding-file bytes, plus the decision fields. The result is written last.
- `check` verifies the chain:
  1. the raw-file hash equals the binding's `raw_sha256`;
  2. the binding-file hash equals the result's `binding_sha256`;
  3. the binding's input-closure hashes equal the current inputs.
- A missing link or a mismatch is `report.binding_mismatch` (or `report.mixed`), exit 1. A missing result is missing evidence, exit 1. An old result with a new binding is rejected. A new result with an old binding is rejected.
- The result's `binding_sha256` changes when the raw report changes. Do not claim byte-determinism for the whole result. Limit the determinism test to the decision fields, or use a stub tool with stable raw bytes.
- The result contains no separate raw hash. The binding hash covers the raw hash through the chain.
- The write order is raw, then binding, then result. An interruption leaves at most a new raw/binding without a matching result, and `check` rejects it.

The proposal's statement that the result has no raw hash stays true. The binding hash is added.

### Unused SKiDL dependencies

Confirmed: the unused SKiDL dependencies stay trial-only. The skill carries the fixed base and uv digests and the pinned `ngspice` in `runtime/Containerfile` and `runtime/BUILD.md`. It does not bundle the SKiDL `requirements.lock`.

### Status

I will review the frozen corrected proposal when it exists. B5 stays closed. No broad tests were run.

## 15. Frozen revision 3: final review

I read `docs/reviews/b6-consolidated-proposal-claude-r3.md`. The measured hash is `a46998a5a3f1b72c3a38700638f2b7b3d172e2d731e9428ad0cc4ca938bec48f`. The r2 copy measures `9ea3c117004309bdd8f024d63a1a0866661e5ee41d89be00ed55fe6a002d400b`. Both match the lead's values.

I reviewed the r2 to r3 diff. It contains the agreed changes:

- C1 review record: strict JSON, full board and interface hashes, `reviewer`, `examined` pointers, prior interface preserved, self-review labeled, skill record outside the contracts registry.
- C2: no SKiDL package and no `requirements.lock` in the skill runtime. Only the two base digests and the pinned `ngspice`. No `env --adopt-image`. A revised lock does not certify the GUI adapter for a new image.
- C3: exact item UUIDs, exact set equality, no pad collapse, reference labels for display. Ambiguous or missing/nil UUIDs leave the finding unwaived, exit 1.
- C5: `export.plot_settings` exit 1; `export.unsupported_setting` exit 2; exit 2 wins.
- C6: a refill that changes another form refuses automatic rebinding and uses the review record.
- C10: the result holds the full binding-file hash; `check` compares it; an interruption after binding and before result is rejected; repeatability compares decision fields, not result bytes.
- The template includes its own `mechanical/interface-review.json` as a labeled self-review.

### Standalone row wording (confirmed)

The lead clarified the standalone row. No user action is pending. The acceptance test has two parts.

1. **Existing image.** Install the skill outside the repository and run it on this measured host with the existing image. Run `env`, `erc`, `drc`, `sim`, `export` and the worker.
2. **Bundled build recipe.** Run the bundled `runtime/BUILD.md` build once within the existing image budget. Then run the applicable CLI and worker checks on the resulting image. Do not claim the recipe works from the old image alone. The new image digest does not certify the GUI adapter; the adapter preflight must refuse it until it passes on that image.

Record the measured host accurately: hostname, operating system and kernel. Record the absolute isolated workspace paths: the installed skill path, the project path and the image build context. Do not use `clean host` or a placeholder `TMP`.

This changes the test wording only. The implementation interface is unchanged.

I confirm this wording. I give final explicit agreement to frozen revision 3. I found no other remaining defect. B5 stays closed. No implementation or broad tests were run.

## 16. Note for the later B6 frozen-set review

The lead found a new `check_skill` guard that skips a code-span path when its first segment is absent from the skill. It lets a missing directory or file pass. The lead directed Claude to remove the guard and to keep the accepted B234 missing-reference behavior. A project-relative example must use an explicit project placeholder or a fenced example. During the B6 frozen-set review, I will confirm that the scanner still catches a code span such as `missing-dir/file.py`. This is a restoration of accepted behavior, not a new scanner framework. No container test is necessary for this check.

## 17. B6 README documentation correction

Date: 2026-11-14.

**Decision: I agree.** Change only the project and package example paths in the source `contracts/README.md` to explicit `${PROJECT}/...` and `${PACKAGE}/...` placeholders. Then copy the corrected source bytes unchanged into the skill at `skills/pcb-design/contracts/README.md`. Preserve the real schema links and the fenced code. Keep the restored scanner. No scanner exception and no dropped README.

The scanner flags these tokens in the source README:

- `kicad/board.kicad_pcb` → `${PROJECT}/kicad/board.kicad_pcb`
- `kicad/board.kicad_sch` → `${PROJECT}/kicad/board.kicad_sch`
- `manufacturing/supplier.yaml` → `${PROJECT}/manufacturing/supplier.yaml`
- `manufacturing/export.yaml` → `${PROJECT}/manufacturing/export.yaml`
- `mechanical/board-interface.json` → `${PROJECT}/mechanical/board-interface.json`
- `manufacturing/waivers.yaml` → `${PROJECT}/manufacturing/waivers.yaml`
- `DIR/manifest.json` → `${PACKAGE}/manifest.json`

The scanner skips a code span that contains `{`, `}`, or `$`. The placeholders therefore pass. Keep the schema file names, the real schema links, and the fenced code unchanged. For consistency, prefix the whole "A project has these files" table with `${PROJECT}/`, including `board.yaml`, `variants.yaml` and `toolchain.lock.json`.

The copy `skills/pcb-design/contracts/README.md` is currently absent. Add it with the corrected bytes. The `check_copies` test then passes, because both files change together. No other skill has a `contracts/` copy.

No implementation was done. This is the verdict to send to the lead.
