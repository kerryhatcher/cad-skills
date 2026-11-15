# B2 to B4 combined interface proposal (Claude)

Date: 2026-11-14.

Status: proposal only. I change no implementation file until the lead gives the next instruction. I made no commit, push, or external action.

Inputs: `b2-b4-design-codex.md`, `b2-b4-design-pi.md`, the B1 code in `contracts/`, and the root decisions of 2026-11-14.

**1. Batch shape**

One combined infrastructure batch ("B234") and one acceptance gate. It has three workstreams:

| Part | Work |
|---|---|
| A. Records | Five new schemas, record rules, and cross-file checks in the existing `contracts/validate.py` |
| B. Safety | `contracts/project_io.py` (lock, confined paths, atomic write, package publication) |
| C. Packaging | Schema-copy and reference checks, snippet routing, CI, ignore rules |

There is no second validator CLI, no schema interpreter, no plugin layer, and no workflow framework. The B1 report shape and exit policy do not change. No KiCad tool is necessary.

**2. Reconciled decisions**

Where the two checklists differ, this proposal uses the root decision. The table lists each point.

| Point | Decision |
|---|---|
| Hash scope | Each `sha256` in a manifest, in `board_sha256`, `toolchain_sha256`, `waivers_sha256` and `export_settings_sha256` covers the exact bytes of one file. Only `content_sha256` of a supplier profile uses the B1 canonical hash. `board.supplier.profile_sha256` equals the profile `content_sha256`. |
| Variant in packages | Every manifest has `variant`. A bare-board package keeps the selected variant for provenance. |
| Waiver binding | The waiver file has one `board_sha256` (bytes of `board.yaml`). Each waiver also has `revision`. Both must agree with the board. |
| Container | Optional. `execution` is `container` or `native`. A container needs `image` and `digest`. A native installed tool needs exact versions only. |
| Coordinates | One convention for all records (section 5). The board record fields `x_axis` and `y_axis` must be `right` and `up`. The interface has no axis fields. |
| Geometry tolerance | The interface keeps `geometry_tolerance_mm`. It is the largest distance between an arc and its polygon. Checks compare dimensions within this value. |
| Manifest self-hash | None. The manifest does not list itself. Another record that names a manifest hash must say so in a later batch. |
| Stale locks | Code never removes a lock. The user removes the file after the user finds that the owner stopped. There is no force flag. |
| Isolation | Copy and reference tests do not prove a sandbox. The final gate (B12) runs real isolated tool tasks. The test output states this limit. |
| `../` references | A local reference is valid if its resolved path stays in the skill directory. A substring ban is not used. |
| Empty CI job | None. The container job comes with B5. |

**3. Records (Part A)**

All new records follow B1: `schema_id`, `schema_version` `"1.0"`, strict types, nested unknown-field rejection, `extensions`, and the date and hash patterns. Codes are `schema.*` for structure and the codes below for relations. Each defect gives one finding.

New schema IDs and files: `cad-skills/waivers`, `cad-skills/manifest`, `cad-skills/board-interface`, `cad-skills/toolchain-lock`, `cad-skills/export-settings`. Files are `<name>.schema.json` in `contracts/schemas/`. The batch adds each file to `registry.json`.

**3.1 `cad-skills/waivers`**

Fields: `board_sha256`, `waivers` (a list, which can be empty). Waiver: `id`, `rule`, `objects` (list), `reason`, `reviewer`, `revision`.

| Check ID | Defect |
|---|---|
| `waiver.duplicate_id` | Two waivers have the same `id` |
| `waiver.duplicate_pair` | The same (`rule`, object) pair occurs in two waivers |
| `waiver.wildcard` | `rule` or an object is `*`, `all`, or `any` (not case-sensitive) |
| `schema.invalid` | An empty `objects` list, or a blank `reason`, `reviewer` or `revision` |

A waiver records a review decision. It is not a pass. Matching a waiver to a tool finding is B7 and B8 work.

**3.2 `cad-skills/manifest`**

Fields: `release_id`, `kind` (`bare_board` or `pcba`), `board_revision`, `board_sha256`, `variant`, `supplier` (`id`, `service`, `profile_sha256`), `toolchain_sha256`, `export_settings_sha256`, `waivers_sha256` (hash or null), `inputs`, `outputs`, `checks`, `status`, `reasons`, `tool_versions`.

- `release_id` matches `^[a-z0-9][a-z0-9._-]*$`.
- `inputs` and `outputs` items: `path`, `sha256`, `role`. The path is relative, uses `/`, and has no `.`, `..` or empty segment. Output paths are relative to the package root. Input paths are relative to the project root.
- Input roles: `board`, `variants`, `supplier_profile`, `toolchain`, `board_interface`, `export_settings`, `waivers`, `parts`, `circuit_source`, `kicad_project`.
- Output roles (closed): `copper`, `mask`, `silk`, `paste`, `outline`, `drill_plated`, `drill_nonplated`, `bom`, `placement`, `schematic_pdf`, `fabrication_drawing`, `assembly_drawing`, `test_record`, `firmware`, `stencil`, `panel`, `report`, `image`, `waiver_report`.
- `checks` items: `id`, `status` (`pass`, `fail`, `pending`, `unconfirmed`).
- `reasons` items: `code`, `text`.
- `status`: `draft`, `qualified`, `unqualified`.

Required check IDs, in a constant table in `validate.py`:

| Kind | Required check IDs |
|---|---|
| `bare_board` | `design.erc`, `design.drc`, `design.parity`, `fab.profile_evidence`, `fab.export_inventory`, `fab.layer_order`, `fab.drill_split` |
| `pcba` | the `bare_board` list plus `asm.bom_consistent`, `asm.placement_rotation`, `asm.variant_agreement`, `asm.stock_dated`, `asm.test_record` |

This batch checks the table and the statuses. Later batches produce the results.

| Check ID | Defect |
|---|---|
| `pkg.path_invalid` | An absolute path, a `.` or `..` segment, a backslash, or an empty segment |
| `pkg.duplicate_path` | A path occurs two times in `inputs`, or two times in `outputs` |
| `pkg.input_output_overlap` | One path is in both lists |
| `pkg.self_reference` | A list names `manifest.json` |
| `pkg.required_input_missing` | A necessary input role is absent. Necessary roles: `board`, `variants`, `supplier_profile`, `toolchain`, `board_interface`, `export_settings`. The role `waivers` is also necessary if `waivers_sha256` is not null. |
| `pkg.no_outputs` | `outputs` is empty |
| `pkg.check_missing` | A required check ID is absent from `checks` |
| `pkg.check_duplicate` | A check ID occurs two times |
| `pkg.reasons_required` | `unqualified` with no reason, or `qualified` with a reason |
| `pkg.false_qualification` | `qualified` while a required check is not `pass` |

**3.3 `cad-skills/board-interface`**

Fields: `board_revision`, `board_sha256`, `units` (`mm`), `origin_mm` (`x`, `y`), `thickness_mm`, `geometry_tolerance_mm`, `outline`, `cutouts` (may be empty), `holes`, `connector_frames` (may be empty), `height_limits` (`top_mm`, `bottom_mm`), `enclosure_clearance_mm`, `dimension_owners`.

- `outline` and each cutout: a list of `{x, y}` points. The last point does not repeat the first.
- Hole: `id`, `x`, `y`, `diameter_mm`, `plated`.
- Connector frame: `id`, `side` (`top` or `bottom`), `x`, `y`, `rotation_deg` (0 up to but not including 360), `insertion_depth_mm`.
- `dimension_owners`: the keys `outline`, `holes`, `connector_frames`, `thickness`, `height_limits`. Each value is `electrical` or `mechanical`.

| Check ID | Defect |
|---|---|
| `iface.outline_invalid` | Fewer than 3 points, a repeated consecutive point, a repeated closing point, zero area, or crossing segments |
| `iface.cutout_invalid` | The same tests for a cutout |
| `iface.duplicate_id` | A hole or frame ID occurs two times (one ID space for both lists) |
| `iface.hole_outside_outline` | A hole center is outside the outline, or inside a cutout |
| `schema.invalid` | A non-positive thickness, tolerance, diameter or insertion depth, a negative height or clearance, an unsupported unit, or a side that is not `top` or `bottom` |

The checks use small functions on point lists. They add no geometry library.

**3.4 `cad-skills/toolchain-lock`**

Fields: `python`, `execution` (`container` or `native`), `container` (`image`, `digest`), `tools`, `libraries`, `models`, `java` (optional).

- Every version is an exact string. The pattern excludes ranges and wildcards (`^ ~ * < > , space`). The values `latest` and `auto` fail.
- If `execution` is `container`, the record has `container`. If `execution` is `native`, the record has no `container`. The `digest` matches `^sha256:[0-9a-f]{64}$`. The `image` does not end with `:latest`.
- `tools` keys: `kicad` (required), `kibot`, `kiauto`, `skidl`, `ngspice`, `freerouting`. Each entry has `used`. If `used` is `true`, it has `version`, `source_url` and `license`. If `used` is `false`, it has no other field (an explicit unused tool).
- `libraries` and `models`: lists of `name`, `version`, `source_url`, `license`, `notes` (optional), `sha256` (for redistributed bytes).
- `license` may be `unknown` only when `notes` is not blank.

| Check ID | Defect |
|---|---|
| `toolchain.unknown_license_no_notes` | `license` is `unknown` with no notes |
| `toolchain.duplicate_item` | A library or model name and version occur two times |
| `schema.invalid` | A range, a mutable image, a bad digest, a missing exact version, or a missing source |

The lock file has no self-hash.

**3.5 `cad-skills/export-settings`**

Fields: `format` (`rs274x`), `units` (`mm`), `x2` (boolean), `gerber` (`decimal_places`, integer 4 to 6), `layers`, `drill`, `origin` (`absolute` or `board`).

- Neutral default: `x2` is `false`. A supplier profile can ask for `true`. The setting is then in the project file, not in the neutral contract.
- `layers`: list of `role`, `kicad_layer`, `suffix`. Roles: `copper_top`, `copper_bottom`, `copper_inner`, `mask_top`, `mask_bottom`, `silk_top`, `silk_bottom`, `paste_top`, `paste_bottom`, `outline`.
- `drill`: `format` (`excellon`), `zero_suppression` (`leading`, `trailing`, `none`), `decimal_places` (integer 3 to 6), `plated_suffix`, `nonplated_suffix`, `separate_files` (`true`).

| Check ID | Defect |
|---|---|
| `export.duplicate_layer` | The pair (`role`, `kicad_layer`) occurs two times |
| `export.layer_missing` | No `outline` layer, or no `copper_top` layer |
| `export.drill_suffix_equal` | The plated and non-plated suffixes are equal |
| `schema.invalid` | `x2` that is not a boolean, `auto` anywhere, or an unknown role |

This is a settings record. B1 to B4 contain no exporter. Real export and supplier acceptance are later tests.

**4. Cross-file checks (Part A)**

The CLI stays one script. B1 behavior does not change when no new flag is present.

```text
uv run contracts/validate.py [--json] [--schemas DIR] [--project DIR] [--package DIR] [FILE ...]
```

- `--project DIR` examines the records at fixed names, then the cross rules. Names: `board.yaml`, `variants.yaml`, `manufacturing/supplier.yaml`, `manufacturing/export.yaml`, `toolchain.lock.json`, optional `manufacturing/waivers.yaml`, optional `mechanical/board-interface.json`. A missing required file gives `cli.input_missing` and exit 2.
- `--package DIR` needs `--project DIR`. It examines `DIR/manifest.json`, then the manifest against the project and the files in `DIR`.
- `FILE` arguments keep the B1 single-record behavior. The tool needs at least one of `FILE`, `--project` or `--package`. Otherwise it gives `cli.argument_error`.
- The tool examines each record first. A cross rule runs only on records that passed. A failed record gives no secondary cross finding.
- Exit codes and report fields are those of B1. Findings give the source file and the field location.
- Hashing reads the original file bytes. The tool reads each file one time and uses the same bytes for the parse and the hash.

| Check ID | Defect |
|---|---|
| `cross.variant_missing` | `board.variant` is not in `variants.yaml` |
| `cross.supplier_mismatch` | `board.supplier` `id` or `service` differs from the profile, or `profile_sha256` differs from the profile `content_sha256` |
| `cross.board_hash_mismatch` | `board_sha256` in the interface, waivers or manifest is not the SHA-256 of the bytes of `board.yaml` |
| `cross.revision_mismatch` | `release_revision` differs from the interface `board_revision`, a waiver `revision`, or the manifest `board_revision` |
| `cross.coordinate_convention` | `board.coordinate_system` is not `x_axis: right`, `y_axis: up`, `units: mm` |
| `cross.dimension_mismatch` | The interface thickness differs from `board.mechanical.thickness_mm`, or the outline box differs from `width_mm` and `height_mm`, by more than `geometry_tolerance_mm` |
| `cross.kind_mismatch` | `board.assembly` differs from `manifest.kind` |
| `cross.variant_mismatch` | `manifest.variant` differs from `board.variant` |
| `cross.profile_hash_mismatch` | `manifest.supplier` differs from `board.supplier` |
| `cross.toolchain_hash_mismatch` | `toolchain_sha256` is not the hash of the bytes of `toolchain.lock.json` |
| `cross.export_hash_mismatch` | `export_settings_sha256` is not the hash of the bytes of `manufacturing/export.yaml` |
| `cross.waivers_hash_mismatch` | `waivers_sha256` is not the hash of the waiver file bytes, or is null while the file exists, or is not null while the file is absent |
| `cross.input_hash_mismatch` | An input item hash differs from the file bytes, or the file is absent |
| `cross.output_hash_mismatch` | An output item hash differs from the file bytes |
| `cross.output_missing` | An output file is absent from the package directory |
| `cross.path_escape` | A listed path resolves outside its root (including through a symbolic link) |

Deferred: coverage of references by the part list (B9), waiver-to-tool-finding match (B7, B8), tools used by a package (B5 and later).

**5. One coordinate convention**

`contracts/README.md` and the schema descriptions state this convention. All lengths are in millimeters. Board coordinates are right-handed. Seen from the top side, +X is right and +Y is up. +Z points from the bottom surface to the top surface. Angles are in degrees, counter-clockwise when seen from +Z. The interface origin `origin_mm` is a point in board coordinates. A consumer subtracts it to get interface coordinates. The top height limit starts at the top surface. The bottom height limit starts at the bottom surface. The KiCad editor uses +Y down. The exporter, not the record, converts it (B11). The mirror and axis tests use an asymmetric fixture in B11.

**6. Safety module (Part B): `contracts/project_io.py`**

PEP 723, no dependencies. Used by import and by a small command line.

```python
class LockHeld(Exception): ...        # has .owner (dict, or None if unreadable)
class LockMalformed(Exception): ...
class PathEscape(Exception): ...

def acquire_lock(project: Path, task: str) -> dict       # returns the lock record
def release_lock(project: Path, token: str) -> bool      # False if the token differs
def read_lock(project: Path) -> dict | None
def confine(project: Path, candidate, *, must_exist=False) -> Path
def atomic_write(project: Path, target, data: bytes, *, _before_replace=None) -> None
def publish_dir(project: Path, staging: Path, dest: Path) -> None
```

- The lock file is `<project>/.cad-skills.lock`. It is a JSON object with `schema_version` `"1.0"`, `pid`, `host`, `start_ticks` (Linux process start time, or null), `started_at` (UTC, ISO 8601), `task`, and `token` (32 hexadecimal characters from `secrets`).
- Acquire creates the file with `O_CREAT | O_EXCL`, writes, and flushes. If the file exists, acquire raises `LockHeld` with the owner data, or `LockMalformed`. Code never removes an existing lock.
- Release reads the file and removes it only if the token matches.
- `confine` resolves the real path and requires it to be under the real project root. It rejects an absolute path outside the root, a `..` escape, and a symbolic link to an outside directory. For a path that does not exist, it resolves the nearest existing parent.
- `atomic_write` does these steps in order:
  1. It calls `confine`.
  2. It rejects a target that is a symbolic link.
  3. It writes a temporary file in the target directory, then flushes and synchronizes it.
  4. It calls `os.replace`, then synchronizes the directory.

  After a handled failure, it removes the temporary file and keeps the old file. `_before_replace` lets a test cause a failure.
- `publish_dir` moves a complete staging directory to a new name with `os.rename` on the same file system. It refuses an existing destination. The manifest is already in the staging directory. A package therefore appears whole or not at all.
- The module claims protection for ordinary cooperating processes on one local file system. It does not claim protection from a hostile process, a network file system, a power loss, or a multi-file rollback.

Command line, for tests and for later scripts:

```text
uv run contracts/project_io.py hold    --project DIR --task ID [--seconds N]   # acquire, print the lock JSON, wait, release
uv run contracts/project_io.py try     --project DIR --task ID                 # acquire once, print the lock JSON
uv run contracts/project_io.py status  --project DIR                          # read-only, print the lock JSON or "none"
uv run contracts/project_io.py release --project DIR --token T                # release with a token
```

Exit codes: 0 success, 1 refused (`lock.held`, `lock.malformed`, `lock.token_mismatch`, `path.escape`), 2 incorrect arguments, 3 tool failure. A refusal prints one JSON finding to standard output. Read-only commands (`status`, the validator) never take the lock.

Tests (`tests/test_project_io.py`, real OS processes):

| Test | Expected result |
|---|---|
| Two processes compete | One `hold` succeeds. A `try` during the hold exits 1 with `lock.held`. The project files do not change. |
| Read-only while held | `status` and `validate.py --project` pass while a `hold` runs |
| Interrupted owner | `SIGKILL` the holder. The lock stays. `try` exits 1 and prints the owner. The test removes the file by hand. The next `try` succeeds. |
| Wrong token | `release --token WRONG` exits 1 with `lock.token_mismatch`. The file stays. |
| Malformed lock | A lock with invalid JSON blocks `try` with `lock.malformed`. The code does not change it. |
| Release on failure | A handled exception in a context that holds the lock releases it |
| Atomic write failure | `_before_replace` raises. The old bytes stay and no temporary file stays. |
| Atomic write success | The new bytes are present. The directory has no extra file. |
| Symbolic link target | `atomic_write` to a symbolic link exits with `path.symlink` |
| Confinement | `../x`, `/etc/x`, a link to an outside directory, and a new leaf under that link give `path.escape`. A normal nested new file passes. |
| Publish | A new destination succeeds. An existing destination raises. A staging directory outside the project raises. |
| Ignore rules | Git ignores `.cad-skills.lock`, `.cad-skills-tmp-*`, `*.kicad_prl`, `fp-info-cache`, `*-backups/`, `_autosave-*` and `*.lck`. Git does not ignore `board.kicad_pcb`, `board.kicad_sch`, `components/x.kicad_mod`, and `tests/fixtures/pcb/x.yaml`. The test also finds a deliberately incorrect rule. |

**7. Packaging checks (Part C): `tests/test_skill_packages.py`**

The test file holds the checker functions and the test runner. The release gate imports them later.

```python
def check_skill(skill_dir: Path) -> list[dict]           # findings
def check_copies(skill_dir: Path, contracts_dir: Path) -> list[dict]
```

| Check ID | Defect |
|---|---|
| `skill.name_mismatch` | The directory name differs from `name` in `SKILL.md`, or the name is blank |
| `skill.description_empty` | `description` is blank |
| `skill.too_long` | `SKILL.md` has 500 lines or more |
| `skill.reference_escape` | A relative Markdown link or a backticked relative path resolves outside the skill directory |
| `skill.reference_missing` | A relative reference resolves inside the skill directory to a file that does not exist |
| `skill.absolute_path` | A reference starts with `/` or `~/` and is not in a code block marked as an example |
| `skill.copy_missing` | A file of the copy set is absent |
| `skill.copy_extra` | The skill schema copy has a file that the registry does not name |
| `skill.copy_changed` | A copy differs from the file in `contracts/` |

- A local reference with `../` is valid when the resolved path stays in the skill directory. The checker resolves each reference against the file that holds it.
- The copy set is `registry.json`, each schema that it names, and `contracts/README.md`, in the skill folder `contracts/`. A skill with no `contracts/` folder is not a failure in this batch. The PCB skills must add the copy from B6.
- The four existing skills run through `check_skill`. If one fails, the test reports the finding and does not edit the skill.
- The test builds fixture skills in a temporary directory:
  - one good skill
  - one with a reference that leaves the directory
  - one with a missing reference
  - one with a `../` reference that stays in the skill
  - three copy defects: missing, extra, and changed
- Copy-run test: a minimal fixture skill with a script runs from an unrelated directory with `python -I`, a cleaned environment, and a temporary `HOME`. It writes only in its work directory.
- Stated limit, printed by the test: this run does not stop the process from reading the repository. It shows that the fixture needs no repository path. It is not a sandbox. B12 runs real isolated tool tasks with the original paths unavailable. A passing static scan is not a portability result.

**8. Snippet routing (Part C)**

New file `tests/snippet_envs.json`:

```json
{"envs": {"cadquery": {"command": null}, "pcb": {"command": null, "available": false}},
 "skills": {"cadquery": "cadquery", "print-prep": "cadquery", "prusaslicer": "cadquery", "structural-analysis": "cadquery"}}
```

- `command: null` means that the block runs in this process, as now. A non-null command is a list. The test runs it as a subprocess, sends `{"label", "code"}` on standard input, and reads `{"status", "stdout", "stderr"}` from standard output. It uses a timeout.
- `available: false` makes each non-skipped block of that environment fail with `snippet.env_unavailable`. It is a failure, not a skip.
- A skill directory with no entry fails with `snippet.unrouted`. An entry that names a missing environment fails with `snippet.env_missing`.
- A `# notest` first line needs a reason: `# notest: <text>`. A bare marker fails with `snippet.notest_reason`. The batch adds a reason to the five existing markers. These are the only edits to existing skill files:
  `skills/structural-analysis/references/materials.md:51`, `skills/cadquery/references/assemblies.md:171`, `skills/cadquery/references/sketch.md:184`, `skills/cadquery/references/import-export.md:44` and `:115`.
- The result check for a CadQuery shape applies only to the `cadquery` environment.
- A run compares `git status --porcelain` before and after. A change fails with `snippet.tree_changed`.
- New flags: `--list-envs` (print the table) and `--dry-run` (print the environment of each block and its skip reason, without execution). The existing command line does not change. The final report gives counts for each environment and the skipped blocks with their reasons.
- Tests (in `tests/test_skill_packages.py`):
  - an unrouted skill and a missing environment
  - a bare marker, a failing block, and a timeout
  - a worker that returns invalid JSON
  - a PCB block that fails as unavailable
  - a temporary worker that runs a block (the report says "temporary worker", not PCB execution)
  - an unchanged tree

**9. CI and ignore rules (Part C)**

Changes to `.github/workflows/test.yml`:

- Keep `permissions: contents: read` at workflow level.
- Add `timeout-minutes: 15` to every job.
- Extend job `pcb-contracts` with the steps `uv run tests/test_skill_packages.py`, `uv run tests/test_project_io.py`, and `uv run tests/test_snippets.py --dry-run`.
- Add `enable-cache: true` and `cache-dependency-glob` with `contracts/**/*.py` and `tests/**/*.py` to `pcb-contracts`. Add `contracts/**/*.py` to the glob of `snippets`.
- Keep the actions pinned to full commit SHA. Add no secret and no supplier credential.
- Add no container job and no job that always skips.

Workflow tests (in `tests/test_pcb_tools.py`) read the file with the B1 loader. They examine these items:

- permissions, job names, and command strings
- a 40-character SHA on each `uses:` line
- a timeout on each job
- no `continue-on-error` and no `|| true`
- the cache glob

`.gitignore` additions: `.cad-skills.lock`, `.cad-skills-tmp-*`, `*.kicad_prl`, `fp-info-cache`, `*-backups/`, `_autosave-*`, `*.lck`. The existing `parts/` and `out/` rules stay, and the project uses `components/`.

**10. Files and commands**

New: five schema files, `contracts/project_io.py`, `tests/test_project_io.py`, `tests/test_skill_packages.py`, `tests/snippet_envs.json`, `tests/pcb_support.py`. The helpers in this file build a valid project and package tree in a temporary directory. Nothing in the tree is static.

Changed: `contracts/validate.py` (new flags and rules), `contracts/schemas/registry.json`, `contracts/README.md`, `tests/test_pcb_tools.py`, `tests/test_snippets.py`, the five existing skill `# notest` lines, `.github/workflows/test.yml`, `.gitignore`, `AGENTS.md`, `README.md`, `ste-glossary.yaml` (appended terms).

The B1 fixtures stay unchanged. The test helper builds the project tree: it copies the B1 fixtures, sets `board.supplier.profile_sha256` to the profile `content_sha256`, and computes the file-byte hashes.

Acceptance commands, with log files and the exit code of `uv run` itself:

```bash
uv run tests/test_pcb_tools.py
uv run tests/test_project_io.py
uv run tests/test_skill_packages.py
uv run tests/test_snippets.py --dry-run
uv run tests/test_snippets.py
uv run tests/test_print_tools.py
```

Report: exact dependency versions, commands, exit codes, a hash manifest of all changed files, and a list of pending tests. A fixture does not prove KiCad operation.

**11. Questions for the reviewers**

1. The manifest `checks` list and the required-ID table (section 3.2). Are the IDs the right set for a first table?
2. The `x2: false` neutral default (section 3.5).
3. Reasons added to five existing `# notest` lines in existing skill files (section 8).
4. The three frontmatter checks for existing skills (section 7). I limit the scope to name, description and length.
5. `started_at` in the lock file. The lock is not a report, so the time is acceptable there.
6. Adding `timeout-minutes` to the existing `snippets` job.

**12. Scope cuts that I keep**

The batch has none of these items:

- a waiver lifecycle
- a manifest time stamp
- stale-lock removal
- a multi-file transaction
- a geometry library
- an exporter
- a sandbox
- a container job
- a migration engine
- BOM or reference checks before B9

**13. Lessons from the B1 review (Codex C1 to C3), applied to B234**

The frozen B1 files have three accepted defects. A separate B1 correction, after Pi finishes, removes them. B234 must not repeat them in new code.

- Exact strings (C1). In Python, `$` matches before a final newline. Each new schema pattern for a hash, ID, path, or date also has `minLength` and `maxLength` that set the length. New code uses `re.fullmatch`. Each new test has a case with a final newline: a hash, a `release_id`, a manifest path, a lock token, a toolchain digest, and a date.
- Scalar construction (C2). A bad scalar is a record error (`file.parse_error`). B234 reads JSON and YAML only through the corrected `parse_record`. The new modules (`project_io.py`) catch only the exceptions that their own parse step raises. They do not convert unknown exceptions to a record error.
- Integer numbers (C3). New geometry code calls `math.isfinite` only on a `float`. An integer such as `10**400` is a valid number. A new test uses a large integer in the outline, the hole position, and the tolerance. A cross rule converts a value to `float` only after it tests for `int`. It reports an overflow as `cross.dimension_mismatch`. It never reports an overflow as a tool failure.
- Tool failures. A test with a hostile but valid record must never give exit 3. Exit 3 stays for a bad registry, a bad schema, or a real defect of the tool.

The B1 correction is not part of B234. It has these steps:

1. Replace `match` with `fullmatch` in `parse_version`.
2. Add length limits to the hash patterns in the board and supplier-profile schemas.
3. Catch `ValueError`, `KeyError` and `OverflowError` at the YAML scalar-construction step only.
4. Make `_is_number` skip `math.isfinite` for an `int`.
5. Add regression tests with the exact inputs from the review.
6. Change line 50 of `contracts/README.md` to the active voice.

The correction changes `contracts/validate.py`, two schemas, `tests/test_pcb_tools.py`, `contracts/README.md`, and the hash manifest. I wait for the lead's instruction before I edit these files.
