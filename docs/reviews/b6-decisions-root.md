# B6 interface decisions: lead

Date: 2026-11-14. This record resolves differences among the proposal, response, reconciliation, and reviewer addenda. Claude will consolidate the accepted interface into one revised proposal before implementation.

## 1. Exit codes

Use the latest combined reviewer table. It supersedes the older exit-1 recommendation in Claude's reconciliation.

| Exit | Meaning |
|---:|---|
| 3 | Tool execution or result failure, including a missing measured value and a post-replacement synchronization failure. |
| 2 | Incorrect invocation, missing prerequisite, runtime mismatch, or recognized unsupported source, geometry, settings, or adapter. |
| 1 | Invalid record, unwaived violation, failed assertion or comparison, stale or missing mandatory readiness evidence, or lock refusal. |
| 0 | Complete success under the operation's policy. |

Use precedence 3, 2, 1, 0. A malformed assertion record is invalid input data, exit 1. An absent configured assertion file is missing input, exit 2. An existing export destination is an invocation conflict, exit 2.

## 2. Runtime

Use `--security-opt label=disable` only with disposable execution and worker copies. Mount the worker copy read-only. Do not mount the live project, installed skill, repository, host socket, or unrelated directories. Keep `--pull=never` and `--network none`. Do not claim that this preserves SELinux confinement.

For a project, `auto` follows `toolchain.lock.json` and its `execution` field. A missing locked runtime does not cause a silent fallback. An explicit conflicting runtime or version returns exit 2. `env` can report the measured difference. Working commands do not silently change the lock or write successful evidence under a different environment.

With no project, `env` can select the bundled local image or an explicit native runtime. Report capabilities separately. Missing ngspice does not prevent ERC. Use measured command forms, including `kicad-cli version`.

Use the measured KiCad bindings for inventory. The missing updater does not prevent board reads. Keep transformed coordinates and multiplicity. Unsupported geometry returns 2 with named objects.

## 3. Waivers and severity

Preserve the B234 schema and semantics:

- All waivers bind current PCB bytes and the declared revision.
- ERC waivers also bind current schematic bytes.
- DRC waivers match schematic bytes when their `schematic_sha256` is not null.
- Kind, rule, and all object identifiers must match.
- No operation automatically renews waiver hashes.

Treat error, warning, and exclusion findings as violations until an applicable waiver covers them. A KiCad UI exclusion alone is not a project waiver. Informational tool diagnostics remain visible. Mandatory parity and connectivity checks cannot disappear through ignored-check settings.

## 4. Interface rebinding

Reject the proposed bounding-box-and-mounting-hole test as sufficient proof. The record also contains thickness, cutouts, plated holes, connector frames, and other mechanical values.

Keep B6 rebinding narrow. Preserve the prior PCB bytes before a board replacement. Locate the prior revision by the full hash already in the interface. Permit automatic rebinding only when a comparison proves that represented geometry did not change.

A conservative comparison can exclude explicitly permitted electrical value fields, the three plot settings, and derived zone-fill cache fields. It must retain thickness, outline, cutouts, holes, footprint geometry, models, and connector placement. Do not use the identity reader's broad ignored-form list as a mechanical proof. A full-file comparison after narrowly specified normalization is sufficient. No general mechanical engine is necessary.

If the prior revision is absent or another field changes, refuse automatic rebinding. The agent must revise and examine the affected interface data. Keep readiness incomplete until that work is complete. B11 can add general mechanical validation later. Do not restrict otherwise supported board operations to rectangular outlines merely for this helper.

## 5. Update, publication, and records

Keep `manual` as the default adapter and `gui` as an explicit option for the tested image. The skill can select the GUI adapter when its preflight succeeds. It does not ask for new permission for an already authorized local edit.

The adapter must measure option states, normal process exit, expected identity differences, and full parity. It uses staging and publishes through the accepted helper. An intermediate board can still need routing. Record its full diagnostics and non-ready state. Normal export still demands current successful mandatory checks.

Keep immutable raw artifacts, full input hashes, bindings, and a result record published last. Include the actual applicable input closure, including schematic sheets and project rules. Recheck live source hashes before publication. Retained failed-history directories do not permanently block a later valid revision.

There is no export replacement mode. Accept an explicit confined destination, or select `out/export/HASH12-N` under the lock. The full hashes remain authoritative. The result record and `check` name the current published directory. Do not use a mutable symlink or infer current output from directory order.

## 6. Assertions, template, and tests

Keep the assertion record small. Define `tolerance` as the maximum absolute difference in the measurement's units. It must be finite and nonnegative. For the RC tests, encode the stated one-percent tolerance from the independent target. Reject duplicate circuit-and-measurement pairs. No expression language is necessary.

The template is a bare-board design project. Part files are design records, not an assembly package. State their separate validation. Pass the explicit bundled schema path. Extend the existing copy tests for `validate.py`, `project_io.py`, `identity.py`, and `sexp.py`.

Use the RC-time-constant task from Codex. The agent receives the requested 2 ms time constant and unchanged 100 nF capacitor. The independent test expects R2 = 20 kohm and approximately 1.2984 V at 1 ms for a 3.3 V step. It declares the target before the run and does not calculate it from the agent's result. An independent ngspice run can test the resulting circuit, but it is not the source of the expected target.

Keep one run each for the successful edit, disabled-adapter handoff, and hierarchy-limit task. Artifact checks decide success. Repeated multi-host evaluations remain B12 work.

The design references, standalone runtime, meaningful edit workflow, and focused tests from both reviews remain in scope. B5 stays closed. No implementation starts before both reviewers agree to the consolidated proposal.
