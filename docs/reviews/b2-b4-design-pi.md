# B2 to B4 scope assessment: Pi

Date: 2026-11-14.

Inputs: `docs/reviews/implementation-proposal-claude.md`, `docs/pcb-pcba-plan.md` sections 3, 4, 7, 9, 10 and 11, `tests/test_snippets.py`, `tests/test_print_tools.py`, and `.github/workflows/test.yml`.

Status: this is the B2 to B4 scope checklist and the final proposal assessment. Section 15 gives the explicit agreement and the remaining blockers. Sections 2 to 14 are the invariants behind it.

**1. Recommended batch shape**

Use one combined infrastructure batch with three ordered workstreams and one acceptance gate. Do not create a fourth batch and do not add a framework.

| Part | Work | Files |
|---|---|---|
| A. Contracts | Waiver, manifest, board-interface, toolchain and neutral export schemas. Cross-file checks. | `contracts/schemas/*`, `contracts/validate.py`, fixtures |
| B. Safety | Project lock, atomic write, path confinement, ignore rules. | `contracts/project_io.py`, fixtures |
| C. Packaging | Schema-copy agreement, skill isolation, snippet routing, CI. | `tests/test_skill_packages.py`, `tests/test_snippets.py`, `tests/snippet_envs.json`, `.github/workflows/test.yml` |

All three parts run on this host without KiCad. One review examines one change. If any part fails, the batch does not merge. This is smaller than three separate review cycles and keeps the shared fixtures and validator together.

Do not add a second validator CLI. Add `--project DIR` and `--package DIR` modes to `contracts/validate.py`. Keep one report shape and one exit policy.

**2. Waiver schema**

Minimum fields: `schema_id`, `schema_version`, `waivers` list. Each waiver has `id`, `rule`, `objects`, `reason`, `reviewer`, `revision`.

| ID | Invariant |
|---|---|
| W1 | `id` is unique and nonblank. |
| W2 | `rule` is a nonblank rule name. Reject `*`, `all`, and `any`. |
| W3 | `objects` has at least one nonblank object. Reject an empty list, `*`, and `all`. |
| W4 | `reason`, `reviewer` and `revision` are nonblank. A whitespace-only string fails. |
| W5 | `revision` equals `board.release_revision`. |
| W6 | The pair (`rule`, `object`) is unique in the file. A second waiver for the same pair fails. |
| W7 | An empty `waivers` list is valid. |
| W8 | No status, owner, expiry or approval history in B2. The file content is the waiver set for one release. Git keeps history. |

Tests: valid empty list, valid one waiver, duplicate id, duplicate pair, empty objects, wildcard rule, wildcard object, blank reason, blank reviewer, revision mismatch, unknown field.

The check that a waiver matches a real ERC or DRC finding needs tool output. Defer it to B7 and B8. Do not fake it in B2.

**3. Package manifest schema**

Minimum fields: `schema_id`, `schema_version`, `package_id`, `kind`, `board_revision`, `board_sha256`, `supplier` (`id`, `service`, `profile_sha256`), `variant`, `toolchain_sha256`, `waivers_sha256`, `export_settings_sha256`, `inputs`, `outputs`, `status`, `reasons`, `tool_versions`.

| ID | Invariant |
|---|---|
| M1 | `kind` is `bare_board` or `pcba`. |
| M2 | `variant` is required for `pcba` and absent for `bare_board`. |
| M3 | Each input and output has `path`, `sha256`, and `role`. The path is relative, uses `/`, and has no `.` or `..` segment. |
| M4 | `sha256` is 64 lowercase hexadecimal characters. |
| M5 | Input paths are unique. Output paths are unique. An input path is not also an output path. |
| M6 | `outputs` has at least one item. `inputs` includes the board, variants, profile, toolchain, board interface, and export settings. |
| M7 | `waivers_sha256` is a hash or null. A null value means the project has no waiver file. |
| M8 | `status` is `draft`, `qualified` or `unqualified`. An `unqualified` package has at least one reason. A `qualified` package has no reason. |
| M9 | `reasons` items have a nonblank `code` and `text`. |
| M10 | `tool_versions` is a nonempty map of nonblank names to nonblank versions. |
| M11 | `package_id` matches `^[a-z0-9][a-z0-9._-]*$`. |
| M12 | The manifest does not list itself in `inputs` or `outputs`. |
| M13 | No creation time or random value. Reproducibility comes from the record hashes and the release revision. |
| M14 | The role set is closed. Use the plan list: copper, mask, silk, paste, outline, drill plated, drill non-plated, BOM, placement, schematic PDF, fabrication drawing, assembly drawing, test record, firmware, stencil, panel, report, image, waiver report. Reject an unknown role. |
| M15 | Every listed output file exists under the package root. Its byte hash equals the record hash. |
| M16 | Every listed input file exists under the project root. Its byte hash equals the record hash. |

Tests: duplicate path, absolute path, `..` path, unknown role, missing output file, changed output byte, input used as output, pcba without variant, bare board with variant, unqualified without reason, qualified with reason, manifest lists itself, hash in uppercase, hash with 63 characters.

**4. Board-interface schema**

Minimum fields: `schema_id`, `schema_version`, `units`, `origin_mm`, `x_axis`, `y_axis`, `thickness_mm`, `outline`, `cutouts`, `holes`, `connector_frames`, `height_limits`, `enclosure_clearance_mm`, `board_revision`, `board_sha256`.

| ID | Invariant |
|---|---|
| I1 | `units` is `mm`. |
| I2 | `origin_mm` is the board coordinate of the interface origin. All geometry in this file uses board coordinates. A consumer subtracts `origin_mm` to get interface coordinates. Write this rule in the schema description and README. |
| I3 | `x_axis` and `y_axis` are 2D unit vectors in board coordinates. Their dot product is 0 within 1e-9. Their cross product is positive. A left-handed pair fails. |
| I4 | `thickness_mm` is a finite number greater than 0. |
| I5 | `outline` is a simple polygon with at least 3 points, no repeated first and last point, no duplicate consecutive points, and nonzero area. Segments do not cross. |
| I6 | Each cutout obeys I5. A cutout is optional. |
| I7 | Each hole has a unique nonblank `id`, finite `x` and `y`, a `diameter_mm` greater than 0, and a boolean `plated`. |
| I8 | Each connector frame has a unique nonblank `id`, a `side` of `top` or `bottom`, a finite `rotation_deg` in [0, 360), and a positive `insertion_depth_mm`. |
| I9 | `height_limits.top_mm` and `bottom_mm` are nonnegative. Top height is measured from the top surface. Bottom height is measured from the bottom surface. Write this rule in the description. |
| I10 | `enclosure_clearance_mm` is nonnegative. |
| I11 | `board_revision` and `board_sha256` equal the board record values. |

Tests: valid offset origin, mirrored axis pair, non-orthogonal axes, zero-length axis, zero thickness, two-point outline, self-crossing outline, duplicate hole id, zero hole diameter, duplicate frame id, side `left`, rotation 360, negative height, revision mismatch, board hash mismatch.

The geometry checks are small functions on a point list. Do not add a geometry library in B2.

**5. Toolchain lock schema**

Minimum fields: `schema_id`, `schema_version`, `python`, `container`, `tools`, `libraries`, `models`, `java`.

| ID | Invariant |
|---|---|
| T1 | Every version is a nonblank exact string. Reject a range, a caret, a wildcard, `latest`, and `auto`. |
| T2 | `python` is an exact version. |
| T3 | `container` has `image` and `digest`. `image` is nonblank and does not end with `:latest`. `digest` matches `^sha256:[0-9a-f]{64}$`. |
| T4 | `tools` is a map from a closed name set to `{version, source_url, license}`. B2 uses `kicad`, `kibot`, `skidl`, `ngspice`, `freerouting`. |
| T5 | `libraries` and `models` are lists of `{name, version, source_url, license}`. A redistributed item also has `sha256`. |
| T6 | `source_url` starts with `http://` or `https://`. `license` is nonblank. Use `unknown` only with a written reason in `notes`. |
| T7 | `java` is optional and exact when present. |
| T8 | The lock file has no self-hash field. |
| T9 | A host-only project can omit `container`. A package that uses KiCad export requires it. The package requirement table is deferred to B5. |

Tests: image `:latest`, bad digest, version range, missing license, missing source, unknown tool name, `java: "25"` passes, `java: 25` fails, empty tools map fails.

**6. Neutral export settings**

B2 needs a small settings record, not an exporter. Minimum fields: `schema_id`, `schema_version`, `format`, `units`, `x2`, `layers`, `drill`, `origin`.

| ID | Invariant |
|---|---|
| E1 | `format` is `rs274x`. `units` is `mm`. `x2` is a boolean. The neutral default is `false`. |
| E2 | `layers` covers copper, mask, silk, paste, and outline. Each role occurs once. |
| E3 | `drill` has `format` (`excellon`), `zero_suppression` (`leading` or `trailing` or `none`), `plated_suffix`, and `nonplated_suffix`. The suffixes differ and are nonblank. |
| E4 | `origin` is `absolute` or `board`. Do not accept `auto`. |
| E5 | No value is `auto`, `default` or `null` unless the schema names it. |

Tests: missing plated drill role, same suffix for both drill files, `x2: "no"`, `zero_suppression: "auto"`, duplicate layer role.

**7. Cross-file invariants**

Add these rules to the project and package modes. Use `cross.*` finding codes. A semantic or cross-file defect exits 1. A missing project or package file exits 2. A schema or validator failure exits 3. The B1 precedence and report rules apply without change.

| ID | Invariant |
|---|---|
| X1 | `board.variant` exists in `variants.variants`. |
| X2 | `board.supplier.profile_sha256` equals the canonical profile hash. `board.supplier.id` and `service` equal the profile values. |
| X3 | `board.release_revision` equals `board_interface.board_revision`, each waiver `revision`, and `manifest.board_revision`. |
| X4 | The manifest hashes equal the canonical board, variants, profile, toolchain, interface and export-settings hashes. |
| X5 | For `pcba`, `manifest.variant` equals `board.variant`. |
| X6 | All records use a supported schema version. A mixed major version fails. |
| X7 | All referenced paths are confined to the project root or the package root. |
| X8 | The manifest input role set includes the records that X4 names. |
| X9 | `board.assembly` agrees with `manifest.kind`: `bare_board` maps to `bare_board`, `pcba` maps to `pcba`. |

Defer these rules: that a variant reference exists in a part list, that a waiver matches a tool finding, and that a toolchain contains every tool that a package used. They need B5, B7, B8 and B9 data.

Tests: missing variant, changed profile limit with a stale hash, three different revisions, manifest variant mismatch, bare board package for a PCBA board, older minor record, path escape through a symlink.

**8. Lock, atomic write, path confinement**

| ID | Invariant |
|---|---|
| S1 | The lock path is `<project>/.cad-skills.lock`. |
| S2 | The lock is a JSON object with `pid`, `host`, `started_at`, `task`, and a random 128-bit `token`. `started_at` is an ISO 8601 UTC string. |
| S3 | Acquire with an exclusive create (`O_CREAT | O_EXCL`). Write, flush and close the file before the caller changes project data. |
| S4 | An existing lock is a failure with owner data. Do not remove it because it is old. Do not add a force or stale-break flag in this batch. The user removes the file after checking the owner. |
| S5 | Release reads the file, compares the token, and removes the file only on a match. A mismatch is a warning and the file stays. |
| S6 | Read-only commands do not acquire the lock. A validation report can run while a writer holds the lock. |
| S7 | Atomic write uses a temporary file in the target directory, fsync of the file, `os.replace`, and fsync of the directory. |
| S8 | A failed write leaves the old file unchanged. The temporary file is removed on a handled failure. A crash can leave a temporary file, and the old file stays valid. |
| S9 | Atomic write rejects a target that is a symbolic link. It also rejects a target outside the project root. |
| S10 | Path confinement resolves the real path, then checks it is under the project root. Reject an absolute path, a `..` escape, and a symlink escape. A nonexistent path is checked through its resolved parent. |
| S11 | There is no multi-file transaction. Write order is data files first and the manifest last. A crash can leave a draft package, not a qualified package. |
| S12 | `.cad-skills.lock` and temporary file names are ignored by Git. |

Tests: one writer holds the lock and a second writer exits 1 with `lock.held` and changes no file, read-only validation passes while the lock is held, a child process exits without release and the lock remains with owner data, a malformed lock blocks a writer, a wrong token does not remove the lock, an interrupted write keeps the old bytes, a symlink target is rejected, a `..` path is rejected, a symlink to an outside directory is rejected, the ignore test passes.

The lock test must use two OS processes. An in-process test can hide file-lock behavior.

**9. Isolation and schema copies**

| ID | Invariant |
|---|---|
| P1 | No skill file refers to `../` outside its own directory, to `contracts/`, or to another skill by path. |
| P2 | A copied skill runs from a temporary directory with `python -I`, a clean environment, and no repository path in `sys.path`. |
| P3 | A copied skill does not write outside its temporary work directory. |
| P4 | A schema copy set is `registry.json`, every schema file named by the registry, and `README.md`. The set and bytes equal the repository contracts. |
| P5 | A skill with no schema copy is reported, not failed, in B4. The three PCB skills must include a copy when they appear in B6 to B9. |
| P6 | Tests do not install a skill into a global path. |

B4 can test the checker with two fixture skills: one self-contained skill that reads its own reference, and one that reads `../other-skill/data.json`. The second must fail P1. Add a copy fixture with a missing file, an extra file, and a changed byte. Each must fail P4.

Do not add a container or a sandbox requirement for P2. The static scan plus the copy-run fixture is proportional. An audit-hook test is optional.

**10. Snippet routing**

| ID | Invariant |
|---|---|
| R1 | One table maps each skill name to an environment name, a worker command, and a result check. Use `tests/snippet_envs.json`. |
| R2 | Every directory under `skills/` has an entry. An unknown skill fails with `snippet.unrouted`. |
| R3 | Every Python block is executed or skipped with a written reason. |
| R4 | A `# notest` marker needs a reason after the marker. The five current markers get a reason in this batch. |
| R5 | A worker runs as a subprocess with a timeout and returns JSON with `status`, `stdout`, and `stderr`. Do not execute a non-default environment in the test process. |
| R6 | The CadQuery result check applies only to the `cadquery` environment. Other environments use `none` or a declared JSON check. |
| R7 | A snippet run does not change the repository tree. Compare `git status --porcelain` before and after. |
| R8 | An unavailable environment is a failure, not a skip. A PCB block before B5 fails with `snippet.env_unavailable`. |
| R9 | The final report gives counts per environment and the skipped blocks with reasons. |
| R10 | The routing table includes the `pcb` environment in B4. Its command stays unset until B5 pins the image. |

Tests: unknown skill, missing environment, `# notest` without a reason, a failing snippet, a timeout, a dry-run that lists the routing, a valid CadQuery block that still passes, a PCB fixture block that fails as unavailable, and no repository change.

Keep the current `test_snippets.py` interface. Add `--list-envs` and `--dry-run`. Do not add a plugin protocol.

**11. CI**

| ID | Invariant |
|---|---|
| C1 | `permissions: contents: read` is at workflow level. |
| C2 | One `contracts` job runs `uv run tests/test_pcb_tools.py`, `uv run tests/test_skill_packages.py`, and the snippet routing dry-run. |
| C3 | Do not add an empty container job. B5 adds the container job with the pinned image and digest. A job that always skips is not evidence. |
| C4 | Actions stay pinned by full commit SHA. |
| C5 | The uv cache glob includes `contracts/**/*.py`. |
| C6 | Jobs have a `timeout-minutes` value. |
| C7 | No `continue-on-error`, no `|| true`, and no skipped test that reports a pass. |
| C8 | Pull-request jobs use no supplier credentials and no secrets. |
| C9 | The workflow test reads `permissions` without the default PyYAML `on:` boolean defect. Use the JSON-compatible loader or a text check. |
| C10 | The existing `snippets` job keeps its current steps. |

Tests: workflow permission present, job names present, command strings present, no `continue-on-error`, each `uses:` has a 40-character SHA, cache includes contracts, timeout present.

**12. Acceptance gate for the combined batch**

The batch passes when:

- All schemas load with the B1 validator.
- The project and package modes give the named finding and exit code for each defect.
- Cross-file hashes and revisions agree.
- Lock, atomic write and path tests pass with two processes.
- The isolation fixtures pass and fail as named.
- Snippet routing passes a dry-run and the existing CadQuery suite.
- The CI checks pass on the real workflow file.
- No test reports a skipped check as a pass.
- No KiCad tool is necessary.

Report the commands, dependency versions, and final file hashes for review.

**13. Scope simplifications that preserve the feature**

1. One combined batch, not three. One gate.
2. No empty container CI job. Add it in B5 with the pinned image.
3. No waiver lifecycle or approval history. The release revision scopes the file.
4. No manifest timestamp. Use record hashes and the release revision.
5. No force-unlock or automatic stale-lock removal. The user removes the file after checking the owner.
6. No multi-file transaction. Write data first and the manifest last.
7. Snippet routing is a table plus one worker protocol, not a plugin system.
8. Isolation is a static scan plus a copy-run fixture, not a sandbox.
9. Schema copies are checked where present. The PCB skills must add them from B6.
10. No exporter in B2. Only the neutral settings record.
11. No migration engine. B1 has one version and an explicit registry.
12. No BOM or reference semantic checks before B9.

**14. Deferred and objection conditions**

Deferred to later batches: waiver-to-DRC match, tool presence per package, unknown reference checks, PCB schema copies, container snippet execution, and real package files.

I object if the B2 to B4 proposal adds a second validator CLI, a plugin or framework layer, an automatic stale-lock break, a manifest timestamp, a CI job that always skips, or a test that reports a missing environment as a pass.

**15. B234 proposal assessment and final blockers (2026-11-14)**

Status: conditional agreement. I accept the combined batch shape, the three-part split, the no-framework rule, and Codex R1 to R4. I accept the root refinements in this section. The blockers below are the final Pi list. They are not candidates.

B1 repair is underway. This section does not re-review B1. B234 must use the repaired B1 routines. B234 implementation waits for the B1 correction hashes and both B1 reviews.

**15.1 Accepted without change**

- One B234 batch with one gate. No second validator CLI. B1 report shape and exit policy stay.
- Five new schemas, the `--project` and `--package` modes, and the cross-file rule set.
- Codex R1 to R4. R1 board identity, R2 whole-string acceptance, R3 replacement boundary, and R4 artifact and evidence qualification.
- Removal of the global `git status` correctness gate. Use relevant source-byte comparison and temporary execution directories.
- One coordinate convention with right-handed board axes.
- `x2: false` as the neutral export default.
- Reasons on the five existing `# notest` markers.
- Lock timestamp as ownership data. No stale-lock removal. No force flag.
- No container CI job in B234. No manifest timestamp. No multi-file transaction. No geometry library. No exporter. No sandbox claim.
- Optional container or native execution. Exact versions for a native tool.

**15.2 PB1: board identity and ERC waiver binding**

This refines Codex R1 and the root ERC condition.

- `board_sha256` identifies the exact bytes of `kicad/board.kicad_pcb` in the waiver record, the board interface, and the manifest.
- Manifest inputs keep separate roles for `board_record` (`board.yaml`), `board` (`kicad/board.kicad_pcb`), and `schematic` (`kicad/board.kicad_sch`). A SKiDL project keeps the `circuit_source` role.
- Each waiver has `kind` (`erc` or `drc`), `board_sha256`, and `revision`. An `erc` waiver also has `schematic_sha256`. A `drc` waiver may set `schematic_sha256` to null.
- Cross codes: `cross.board_pcb_hash_mismatch`, `cross.board_record_hash_mismatch`, `cross.schematic_hash_mismatch`, and `cross.waiver_schematic_hash_mismatch`.

Minimum tests:

1. Change only the PCB bytes. Every waiver and the interface fail their board-hash checks.
2. Change only `board.yaml`. The manifest board-record input fails. The interface and waivers pass.
3. Change only the schematic bytes. Every `erc` waiver fails. A `drc` waiver and the interface pass.
4. Give the `board` role another file with a declared hash. Reject the substituted input.

**15.3 PB2: drill applicability and no empty output**

This refines Codex R4.

- Every manifest output has `size_bytes`, an integer greater than 0. A zero-byte output fails `pkg.output_empty`.
- Required roles follow Codex R4. A bare board requires copper for each declared layer, mask, outline, a drill result, schematic PDF, fabrication drawing, and check report. Silkscreen is required when the export settings declare a silk layer. A PCBA package adds BOM, placement, assembly drawing, and test record. Paste is required when the assembly has surface-mount parts.
- A required drill role that is absent needs an explicit applicability item: `{role, condition, reason, evidence}`. The condition is `no_plated_holes` or `no_nonplated_holes`. The reason is nonblank. The evidence identifies an input record or a check record.
- Do not use an empty drill file as the drill output. Do not invent zero dimensions.
- Codes: `pkg.artifact_missing`, `pkg.applicability_missing`, `pkg.applicability_reason_missing`, `pkg.output_empty`.

Minimum tests:

1. No non-plated drill file and no applicability item. Fail.
2. An applicability item with condition, reason, and evidence. Pass.
3. A zero-byte drill file. Fail.
4. A two-layer board with one copper file. Fail.
5. A PCBA package without paste and with surface-mount parts. Fail.

**15.4 PB3: evidence is one small versioned record**

This refines Codex R4 and the root condition. It is not a framework.

- Add `cad-skills/evidence` to the registry. One evidence record has `schema_id`, `schema_version`, `check_id`, `status`, `method` (`tool` or `manual`), `inputs` (path and SHA-256), `artifact` (path and SHA-256, optional), `reviewer`, `date`, and `notes`.
- The manifest `checks` item keeps `id`, `status`, and `evidence_sha256` or null. It does not repeat the evidence body.
- A `method: tool` record requires `artifact` and at least one input. A `method: manual` record requires a nonblank reviewer and a valid date.
- A `pass` check requires an evidence record. `pending` and `unconfirmed` may have no evidence and prevent qualification.
- A qualified package requires every required check to be `pass` with valid evidence, every required artifact role to be present, and every absent conditional role to have an applicability item.
- The cross check compares the evidence `check_id`, `status`, input hashes, and artifact hash with the manifest and project. A mismatch fails.
- Compare the selected profile `evidence_sha256` with the referenced retrieved bytes. This proves byte identity, not supplier acceptance.
- Codes: `pkg.check_evidence_missing`, `pkg.check_evidence_mismatch`, `pkg.check_manual_incomplete`, `pkg.evidence_unknown`.

Minimum tests:

1. All-pass `checks` strings with no evidence records. Qualification fails.
2. Evidence with one changed input hash. Fail.
3. Changed evidence bytes. Fail.
4. A manual record with reviewer and date. Pass for that check.
5. A `pending` required check. Qualification fails.
6. An unsupported evidence schema version. Fail.

**15.5 PB4: source-byte checks replace the global tree check**

- Remove `snippet.tree_changed` and the whole-repository `git status` comparison from the isolation and snippet tests.
- Copy a skill to a temporary directory. Record the hashes of the skill source files. Run the copy from an unrelated temporary directory with `python -I`, a cleaned environment, and a temporary HOME. Compare the source hashes only.
- Run each snippet environment in a temporary working directory. Compare the copied skill source and the temporary tree. Do not compare the repository.
- Keep the stated limit. This shows that the fixture needs no repository path. It is not a sandbox. B12 runs the real isolated tasks.

Minimum tests:

1. An unrelated report edit does not affect the result.
2. A changed copied skill source fails.
3. A write outside the temporary directory fails.

**15.6 PB5: B234 uses the repaired B1 routines**

- B234 calls the repaired `parse_record`, `canonical_hash`, strict type checker, and full-string helper in `contracts/validate.py`. It does not copy an old pattern or a local hash function.
- Every new constrained string uses a semantic full-string check, not only the schema pattern. This covers `release_id`, manifest paths, versions, tool versions, tokens, digests, dates, rule names, and object names.
- Identifiers and paths reject control characters, including a final newline, carriage return, tab, and NUL. Prose fields such as `reason` and `notes` may contain line breaks.
- Tests pass a final newline through the validator for `release_id`, a manifest path, a version string, a tool version, a hash, a digest, and a date. Also test a valid exact string.

B234 does not add a new B1 repair item. This is the consumption rule for the repaired routines.

**15.7 Non-blocking recommendations**

- Set the `snippets` job timeout after a measurement. Fifteen minutes is tight for the CadQuery, FEA, and PrusaSlicer steps.
- For a project with a `board` input, require `tools.kicad.used: true` and an exact version. Defer the full check-to-tool map to B5.
- Add a schema test for `dimension_owners`: exactly the five keys and only `electrical` or `mechanical`.
- Add `export.suffix_duplicate`: two layer entries must not use the same file suffix.
- Test that an inline command example and a numeric code span are not treated as file references in the package scan.

**15.8 Acceptance gate for B234**

The B234 revision passes when:

- The B1 repair is accepted by both reviewers. B234 uses the repaired routines.
- PB1 to PB5 have named tests that fail for the named defect.
- A qualified fixture package has the required artifact roles and valid evidence records.
- A changed PCB, board record, or schematic gives the correct distinct failure.
- An absent drill file has an applicability item and no empty file substitute.
- The isolation and snippet tests compare source bytes in temporary directories and do not use a whole-repository status gate.
- No test reports a skipped check as a pass. No KiCad tool is necessary.
