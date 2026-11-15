# B2–B4 interface checklist: Codex

Date: 2026-11-13.

Sources: the Claude implementation proposal and sections 3–4, 6, 9–11, and 14–15 of `docs/pcb-pcba-plan.md`.

Scope: a proposed combined infrastructure batch. This report does not review changing B1 files. Agreement follows reconciliation with Claude's concrete proposal.

**Batch boundary**

Combine B2–B4 where their interfaces share tests. Reuse the agreed B1 loader, registry, type checker, hashes, findings, and exit precedence. Add no general workflow engine or second schema interpreter.

Keep repository contracts as primary sources. Future skills receive standalone copies. X2 is closed: disk cost up to 15 GB needs no user cleanup.

**Record interfaces**

All new records use explicit schema IDs and supported versions. Apply strict types, finite numbers, nested unknown-field rejection, and B1 date rules.

| Record | Necessary invariants | Minimum tests |
|---|---|---|
| Waivers | Unique waiver ID, rule ID, nonempty affected-object IDs, reason, reviewer, source revision, and board hash. Match the exact finding scope. Preserve the original finding. | Missing mandatory field, duplicate ID, changed board hash, unmatched object, and unrelated finding. |
| Package manifest | Release ID, package kind, selected variant, supplier identity and profile hash, source revision, input hashes, toolchain hash, export settings, output paths and hashes, and qualification status. | Missing artifact, changed bytes, duplicate path, stale profile, inconsistent variant, and false qualification. |
| Board interface | Millimeter units, coordinate frame, thickness, outline, holes, connector frames, height limits, insertion space, clearances, board revision, and board hash. Give constrained dimensions an owner. | Valid asymmetric fixture, invalid dimensions, missing frame, unsupported units, duplicate feature ID, and inconsistent board hash. |
| Toolchain lock | Named tools and libraries with exact versions or immutable revisions. Record source and license information. Record the container image digest when a container applies. | Missing mandatory tool, mutable image tag alone, duplicate tool identity, missing library revision, and explicit unused optional tool. |

Use a list of waiver records. Do not use a wildcard that suppresses an entire rule. A waiver records a review decision. It does not turn an omitted check into a pass.

Give manifests explicit `draft` and `qualified` states. Qualification needs all applicable checks and artifacts. Pending, failed, or unconfirmed evidence prevents qualification. A structurally valid manifest alone cannot establish qualification.

List mandatory check IDs by package kind in a small constant table. Test a missing check and a missing check result. Do not make a general expression language.

A manifest does not include its own bytes in its output hash list. Hash its referenced files exactly. If another record references the manifest, define that hash separately.

Define one coordinate convention now: origin, axis directions, handedness, angle units, bottom-side convention, and upper/lower height signs. Connector frames must use the same convention. Require positive thickness and hole diameters. Require finite coordinates and nonnegative clearances.

Use explicit optional records for absent connectors or insertion constraints. Do not invent zero dimensions for unknown data. Geometry correctness and enclosure fit remain later integration tests.

Optional tools can be absent when the selected operation does not use them. Do not make SKiDL mandatory for native KiCad records. Keep unknown license evidence visible. Distribution approval remains a later condition.

**Cross-file references and export contract**

- Give cross-file validation an explicit entry point with a project root and named input records.
- Keep single-record schema validation separate from filesystem inspection.
- Require exactly one selected variant to exist.
- Match supplier ID, service, and profile hash across the board, profile, and manifest.
- Match source revision and board hash across the interface, waivers, and manifest.
- Match the toolchain reference to the exact lock-file bytes.
- Validate individual records before cross-file comparisons.
- Report a missing reference with its source file and field location.
- Preserve earlier reports when referenced hashes change.

Test two valid variants, a missing variant, changed profile content, mismatched service, stale waiver, and changed toolchain bytes. Test invalid input without a secondary exception.

Where the records lack component instances, defer complete reference coverage to the assembly batch. Do not infer board instances from a catalog of part types.

The neutral export contract must state RS-274X, X2 policy, millimeter units, layer mapping, drill precision, and zero suppression. Separate plated and non-plated drills. Record the selected values in the manifest. Select one default X2 policy before agreement.

This batch can validate explicit settings and expected file roles with fixtures. Actual export geometry and supplier acceptance remain later tests.

**Project lock and atomic writes**

Use one small helper module with explicit project-root arguments. Support ordinary cooperating processes on the tested local filesystem. Do not claim distributed-lock guarantees.

| Operation | Necessary invariant | Minimum test |
|---|---|---|
| Acquire lock | Atomically make `.cad-skills.lock` before mutable input reads. Store host, PID, start identity, task ID, and an ownership token. | Two processes compete. Exactly one enters the mutation section. |
| Release lock | Remove only the lock owned by the caller. Release after success or handled failure. | A different token cannot remove the lock. An exception releases the owned lock. |
| Interrupted owner | Never remove a lock merely because it is old. Ambiguous ownership stops mutation. | Terminate an owner. The next writer stops without replacement. |
| Path confinement | Resolve paths against the explicit root. Reject escapes, including symlink escapes and escaping schema references. | Reject `../`, an external absolute path, an external symlink, and a nonexistent leaf under an external symlink. |
| Atomic file replacement | Use a temporary sibling file. Flush and synchronize it before replacement. Preserve the old destination before replacement. | Inject failure before replacement. The original bytes remain complete. |
| Package publication | Stage a complete package before publication. Publish only after artifact and manifest validation. | Inject a missing artifact. No qualified package appears. |

Use explicit recovery for abandoned locks. B2–B4 does not need automatic stale-lock removal. Read-only reports do not acquire the mutation lock.

Document the failure boundary. Atomic replacement protects one file. It does not roll back several project files or guarantee recovery after power loss.

For packages, use a new release directory with an unused name. Reject an existing destination. This prevents partial replacement without a transaction framework.

Do not claim protection against hostile concurrent symlink changes. Ordinary path-confinement tests and cooperating writers are sufficient for this batch.

**Isolation and snippets**

- Define the copy set explicitly: registry, referenced schemas, operating references, and necessary helper modules.
- Compare present copies byte for byte with the primary files.
- Reject missing files within a declared copy set.
- Test isolation helpers with a temporary minimal package before PCB skills exist.
- Execute that package from an unrelated directory without repository paths or sibling skills.
- Test one changed copy and one removed dependency.

A different working directory alone does not prove isolation. Make original paths inaccessible during the isolated test, or state the weaker test limit. Complete standalone PCB tasks remain later acceptance tests.

Use a small explicit map from skill name to execution environment. Keep the current mechanical environment. Route PCB blocks to a separate pinned worker in the selected container.

Test an unknown skill, a known mechanical block, a PCB dispatch, and a missing selected worker. Report executed, failed, and intentionally incomplete blocks separately. Missing tools must not produce a passing block.

Before container selection, test dispatch with a temporary worker. Do not report that as PCB execution. Do not add empty skill directories or hide executable examples with `# notest`.

**CI and completion evidence**

Run the contract, safety, package-helper, and routing tests in one infrastructure job. Preserve the mechanical job and workflow-level `permissions: contents: read`. Pin external actions. Supply no supplier credentials.

Do not add an empty green PCB integration job. Add the real container job after B5 selects its digest. Until then, identify PCB execution as pending.

Test that necessary `components/` sources remain visible to Git. Add KiCad local-state ignore patterns without hiding source boards, schemas, fixtures, or evidence. Test a deliberate incorrect ignore rule.

For review, supply changed-file hashes, commands, test results, and explicit pending integration tests. Do not count fixtures as proof of KiCad operation.

This checklist is a basis for interface agreement. Claude's concrete proposal must settle field names, check IDs, CLI entry points, and the X2 export policy before implementation.

**B234 proposal review — blocking corrections**

Reviewed proposal: `docs/reviews/b2-b4-proposal-claude.md`, dated 2026-11-14.

I agree with the combined batch structure. I do not yet agree with its interface. Apply R1–R4 below before implementation.

**R1: bind layout evidence to board bytes**

Use `board_sha256` for the exact bytes of `kicad/board.kicad_pcb`. Apply this meaning to waivers, the board interface, and the manifest.

Keep separate manifest inputs for `board.yaml` and `kicad/board.kicad_sch`. Use explicit roles such as `board_record`, `board`, and `schematic`. For SKiDL, retain the circuit-source input separately.

The project validator reads native KiCad files as bytes for hashes. It does not parse them as YAML records. Manifest role paths must identify the selected project inputs. An arbitrary file with the correct declared hash cannot substitute for the selected board.

Minimum tests:

- Change only the PCB bytes. Existing waivers, interface, and manifest must fail their board-hash comparisons.
- Change only `board.yaml`. Its manifest input hash must fail without a false PCB-hash mismatch.
- Change only the schematic bytes. Its manifest input hash must fail.
- Give the board role another file. Reject the substituted input.

This correction follows the plan's board identity and release-evidence rules. It does not call for KiCad execution.

**R2: test whole-string acceptance**

Exact length constraints repair fixed-length hashes. They do not repair variable-length IDs, paths, or versions.

Use full-string matching in Python. For schema patterns, prevent acceptance before a final newline. Add explicit control-character rejection to manifest paths and identifier fields where applicable.

Test final newlines in `release_id`, a relative manifest path, a version string, and a tool version. Also test fixed-length hashes and digests. Assert failure through the validator, not only through a pattern helper.

Keep ordinary descriptive text separate from identifiers. Do not ban line breaks from all prose fields.

**R3: state the replacement boundary correctly**

Before `os.replace`, failure preserves the old destination bytes. After replacement, a directory synchronization failure can leave the new bytes in place.

Do not promise old bytes after all handled failures. Report the post-replacement failure without an automatic rollback claim.

Test failure before replacement and failure during directory synchronization after replacement. The second case must report failure while the destination contains the complete new bytes. Neither case leaves a temporary file.

Hold the project mutation lock across publication. Validate the staged package before publication. The low-level rename helper can remain independent of schema validation. The caller must enforce that order.

**R4: qualification needs artifacts and evidence**

The required check-ID table is a useful baseline. A caller's list of `pass` strings cannot establish qualification.

Add a small mandatory-role table. For bare boards, require copper and mask for the declared layers, outline, separate drill files, schematic PDF, fabrication drawing, and check reports. Include silkscreen where the export settings declare it.

For PCBA, add BOM, placement, assembly drawing, and test record. Require paste, firmware, stencil, and panel data only under explicit applicable conditions. Keep those conditions as simple fields or a small table.

Map layer-specific outputs to the selected export-layer entries. A single copper file must not satisfy a multilayer package. Test a missing inner layer and exchanged layer identities.

Give each required check a reference to an evidence file with an exact-byte hash. The evidence must identify its check, result, and examined input hashes. Compare those values with the manifest and project. Pending or mismatched evidence prevents qualification.

For supplier evidence, compare the selected profile's evidence hash with the referenced retrieved bytes. This establishes byte identity, not authenticity or current supplier acceptance.

Tests must reject missing roles despite all-pass strings, missing evidence, changed evidence bytes, stale input hashes, and a non-pass applicable result. Draft records can retain incomplete evidence explicitly.

Fixture reports are sufficient for these infrastructure tests. Tool-produced reports and independent geometry measurements remain later integration work. Describe this batch as qualification-record consistency, not proof of manufactured-board correctness.

**Agreements and proportional scope**

I agree with these proposal choices:

- Keep `x2: false` as the neutral default, with explicit project settings for a supplier override.
- Add reasons to the five existing `# notest` markers.
- Test existing skill names, descriptions, and instruction length.
- Keep the lock timestamp. It is ownership data, not a deterministic report field.
- Add job timeouts and preserve the mechanical job.
- Defer real isolation and container execution with explicit limits.

Use the package kind and a small set of applicability fields for R4. Do not add an evidence engine or a supplier-rule language.

Remove the proposed global `git status` comparison as a correctness gate. It can fail when another agent edits a report. It also misses further edits to an already modified file. Use temporary execution directories and compare relevant source-file bytes when necessary. Keep the stated absence of a sandbox.

Treat only identifiable file references as paths in the static package scan. Do not interpret all backticked values as file paths. Test a command example and a numeric code span to prevent false findings.

B1 correction remains separate. This review changes only this report. Explicit B234 agreement remains pending a proposal that incorporates R1–R4.
