# Implementation proposal for issue 1 (Claude)

Date: 2026-11-13.

Scope: this file proposes batches for `docs/pcb-pcba-plan.md` (revised). It does not change any implementation file. No commit, push, order, or supplier contact occurred.

Claude is the only writer of implementation files. Codex and Pi review each batch.

**1. Inputs that I read**

- `docs/pcb-pcba-plan.md` (424 lines, revised).
- `AGENTS.md`, `CLAUDE.md`, `.github/workflows/test.yml`, `.gitignore`.
- `tests/test_snippets.py` and `tests/test_print_tools.py`.
- `skills/print-prep/SKILL.md` and `skills/print-prep/scripts/printability.py` (the style reference for a skill CLI).

I did not read the three older review reports. The plan section 13 summarizes them.

**2. Tools and environment on this host**

| Item | State | Effect |
|---|---|---|
| `kicad-cli`, `kicad`, `pcbnew` | Missing | ERC, DRC, exports, and rendering cannot run on the host. |
| `ngspice` | Missing | Simulation tests cannot run on the host. |
| `podman` 6.1.3 | Installed, rootless, `overlay` storage | The host can run the fixed KiCad container. `docker` is only a podman emulation. Use `podman` in all scripts and documents. |
| Local images | No KiCad or KiBot image | P1 must pull and pin an image. |
| Registry access | `podman manifest inspect ghcr.io/inti-cmnb/kicad10_auto_full:latest` succeeded. `podman search kicad` lists `docker.io/kicad/kicad` and `registry.fedoraproject.org/kicad`. | The network works. I did not pull any image. The lead must select the image (see section 7). |
| Disk | `/mnt/storage` is 98% full, 47 GB free | A full KiBot image can be several GB. Pull only after the lead accepts the cost. |
| `uv` 0.12.5, `python3` 3.15.2 | Installed | PEP 723 scripts work. Existing skills limit Python with `<3.14` for CadQuery. New PCB scripts use `>=3.10`. |
| `java` 25 | Installed | Freerouting can run later. It stays optional. |
| X server (`Xvfb`, `xvfb-run`) | Missing | The GUI operation `Update PCB from Schematic` cannot run unattended here. |
| `inkscape` | Missing | Not necessary. Do not add it. |
| CadQuery | Available through `uv` | The mechanical batch (B11) can run on the host. |
| `git`, `gh` | Installed | Git-ignore tests can run. I will not use `gh` to contact any supplier. |

Repository facts that affect the batches:

- `.gitignore` ignores `out/`, `*.step`, `*.stl`, `*.dxf`, `*.3mf`, and `parts/`. Test fixtures with these names or paths must use other names.
- `ste-glossary.yaml` has 73 uncommitted lines from the plan work. I will only append to it, in each batch that adds a term.
- `docs/` is untracked. I do not commit it.
- The CI file has one job and no `permissions:` key. B1 adds `permissions: contents: read`.
- Test files are `uv run` scripts with a `test_*` function convention and a small `main`. New test files follow this pattern.

**3. What can run on this host**

Runs here without KiCad:

- Schema validation, hash rules, version rules, and variant rules.
- BOM and placement transformations, rotation and mirror math, and supplier column mapping on fixture data.
- Project lock, atomic write, and path confinement.
- Git-ignore tests, skill-package isolation tests, schema-copy agreement tests.
- Snippet-runner routing and CI file edits.
- CadQuery import and fit tests from a fixture `board-interface.json`.
- Parsing of fixture Gerber and Excellon text with pure Python, for package inspection.

Needs the container (not available yet):

- ERC, DRC, schematic parity, zone refill, all `kicad-cli` exports, KiBot, and SKiDL runs that read KiCad symbol libraries.
- ngspice batch runs.
- Generation of real `.kicad_sch`, `.kicad_pcb`, STEP, and DXF files.

Needs a person or outside evidence:

- The board update from the schematic (GUI operation). A person must do it once for each trial path.
- Sierra Turnkey PRO BOM, XY, and drawing templates. The plan marks these as open. The lead or the user must obtain sample files from the supplier pages. I will not contact the supplier.
- Native KiCad 10 acceptance by OSH Park. The plan keeps this open.
- Evidence of in-house fabrication and assembly for MacroFab and Ninja Circuits. Both stay provisional.

**4. Missing integration prerequisites**

| ID | Prerequisite | Blocks | Owner |
|---|---|---|---|
| X1 | A released KiCad 10 container image with a recorded digest, including KiBot, ngspice, and the KiCad libraries | B5 and all later batches that run KiCad | Lead decision, then Claude |
| X2 | Disk space for the image (47 GB free now) | X1 | User |
| X3 | A person to do the GUI board update for each trial path | B5 | User or lead |
| X4 | Sample Sierra BOM, XY, and drawing templates (dated evidence) | B10 | Lead |
| X5 | A decision on the `contracts/` location (see D1) | B1 | Lead and reviewers |
| X6 | License review of KiCad libraries, footprints, and models that the skills redistribute | B12 | Lead |

B1 to B4 have no outside prerequisite.

**5. Batches**

Each batch is one reviewable change. Claude writes it. Codex and Pi review it before the next batch starts. Each batch lists what it touches, what runs here, and its exit condition.

| Batch | Plan phase | Work | Runs here | Exit condition |
|---|---|---|---|---|
| B1 | P0 | `contracts/` with a validator and four schemas: board, variants, part, supplier profile. Test file `tests/test_pcb_tools.py`. CI permissions. | Yes, fully | The tests in section 6.5 pass. Reviewers agree on D1 to D4. |
| B2 | P0 | Schemas for waivers, package manifest, board interface, and toolchain lock. The neutral export contract. Cross-file rules (board to variants, board to profile hash). | Yes, fully | Each defect in the plan table "Schema", "Waivers", "Variants", "Evidence" fails for the named reason. |
| B3 | P0 | Project safety: `.cad-skills.lock`, atomic write, path confinement, KiCad ignore patterns, Git-inclusion test for `components/`. | Yes, fully | Simultaneous writer and interrupted write tests pass. Ignored-source test fails on a deliberate bad pattern. |
| B4 | P0 | `tests/test_skill_packages.py` (isolation, schema-copy agreement). Snippet runner routing by skill. Empty PCB CI job with pinned actions. | Partly. The container job cannot run here. | A skill with no assigned environment fails. A changed schema copy fails. |
| B5 | P1 | Tool trial. Pin the container. Native KiCad path first, then SKiDL path. Trial board, RC simulation, reference exports, expected-geometry fixtures, `toolchain.lock.json`. A written trial record. | No. Needs X1 to X3. | At least one source path passes. The record lists commands, versions, manual steps, and unsupported paths. |
| B6 | P2 | Skill `pcb-design`: `SKILL.md`, `scripts/pcb.py` (`env`, `check`, `erc`, `drc`, `sim`, `export`), templates, references. | Partly. Wrapper logic and exit codes run here against fake tool output. KiCad calls need the container. | A clean agent run completes the trial board. A deliberate ERC error gives exit 1. |
| B7 | P3 | Skill `pcb-fab-package`, part 1: profile engine, five OSH Park profiles, `.kicad_dru` templates, hash and evidence rules. | Yes for the profile engine. Rule files need the container for DRC tests. | Profiles validate. Each profile hash is stable. A changed limit marks the package unqualified. |
| B8 | P3 | `pcb-fab-package`, part 2: boundary boards (below, at, above each limit), Gerber and drill inspection, package manifest, draft status. | Partly. Parsers run here. Boards and DRC need the container. | Each profile passes boundary tests. A missing layer or stale drill file fails. |
| B9 | P4 | Skill `pcba-design`, part 1: neutral assembly dataset, variant selection, DNP, quantity rules, rotation and mirror tests, part records. | Yes for the data code. Real placement files need the container. | Top and bottom parts at 0, 90, 180, 270 degrees agree with fixtures. Two variants and a missing reference fail as expected. |
| B10 | P4 | `pcba-design`, part 2: Sierra adapter, assembly drawing, test records, firmware record, own fabrication export, package manifest. | Blocked by X4 for the adapter columns. | Reference, quantity, rotation, and variant agree across all files. |
| B11 | P5 | Mechanical export: STEP, DXF, `board-interface.json`, CadQuery fit example, joint release ID. | Yes for CadQuery with fixture JSON. Real STEP and DXF need the container. | The asymmetric board fits the enclosure within the stated tolerance. Mirror and axis errors fail. |
| B12 | P6 | Agent evaluations, isolated installation tests, export agreement tests, CI, README, `AGENTS.md`, glossary, STE pass. | Partly | All release criteria in plan section 12 pass. Open limits stay visible. |

Order: B1, B2, B3, B4, B5. Then B6 first. B7 and B9 can start after B5 and run in parallel on paper, but I write one at a time. B8 follows B7, B10 follows B9 and X4. B11 follows B6. B12 is last.

Planning rule for reviewers: if B5 shows that neither source path works, I stop at B5 and write a correction proposal. B6 to B12 do not start.

**6. First batch: B1 (revised after design review)**

Revision: 2026-11-14. This section replaces the first version. It includes the Codex corrections, Pi P1 to P6, and the root clarifications. The implementation is in `contracts/`, `tests/test_pcb_tools.py` and `tests/fixtures/pcb/`. `docs/reviews/b1-implementation-claude.md` records the results.

**6.1 Aim**

Give the project one machine-checked contract for four records: board, variants, part, supplier profile. Set the exit-code and report format for all later tools. Use no KiCad dependency.

**6.2 Files**

New: `contracts/validate.py`, `contracts/README.md`, `contracts/schemas/registry.json`, four schema files, `tests/test_pcb_tools.py`, and four fixtures in `tests/fixtures/pcb/`.

Changed: `.github/workflows/test.yml` (workflow permission `contents: read` and job `pcb-contracts`), `AGENTS.md`, `README.md`, and `ste-glossary.yaml` (appended terms only).

**6.3 Interface**

```text
uv run contracts/validate.py [--json] [--schemas DIR] FILE [FILE ...]
```

The PEP 723 header pins `jsonschema==4.26.0` and `pyyaml==6.0.3`. A change of a pin is a reviewed change.

| Exit code | Cause (highest priority first) |
|---:|---|
| 3 | Invalid or missing registry, missing or invalid schema file, or validator failure |
| 2 | Incorrect arguments, missing input file, or missing schema directory |
| 1 | Unreadable file, parse error, duplicate key, or invalid record |
| 0 | All records pass |

The `--json` report is the only standard output. Its fields are `report_schema_version`, `status` (`pass`, `fail`, `error`), `exit_code`, `tool_versions`, `inputs` (path and SHA-256 of the bytes read), `findings` (sorted by file, location, code), `unprocessed`, and `outputs`. The report holds no time and no random value. An argument error under `--json` gives `cli.argument_error` and `exit_code` 2.

Functions: `load_record`, `parse_record`, `canonical_bytes`, `canonical_hash`, `load_registry`, `check_version`, `validate_record`, `build_report`, `main`.

**6.4 Rules**

- Loader (P1): JSON-compatible data only. Reject duplicate keys at any depth, non-string keys, merge keys, recursive aliases, non-finite numbers (including `1e999`), and every tag except str, int, float, bool, null, seq and map. Plain untagged ISO dates stay strings. An explicit `!!timestamp` fails. The text `yes`, `no`, `on` and `off` stays a string.
- Versions (D2, P3): `schema_version` is a string `MAJOR.MINOR`. The registry names one schema file for each supported version. A record uses the schema for its exact version. Findings: `schema.version_malformed`, `schema.major_unsupported`, `schema.minor_newer`, `schema.version_unsupported`.
- Hash (D3, P2): remove only the root `content_sha256`, encode with `sort_keys`, compact separators, `ensure_ascii=False`, `allow_nan=False`, UTF-8, no final newline, then SHA-256. The input-file hash is separate and covers the bytes.
- Types (P4): the validator redefines the `integer` and `number` types of one `jsonschema` validator class. It adds no second schema interpreter. Dates use a pattern and the date format. Strings must have a character that is not a space. URLs start with `http://` or `https://`. Nested objects reject unknown fields.
- One finding for one defect: the schema checks structure and types. The validator checks relations between fields after the schema passes. At most one schema finding for each location.
- Limits (root): `minimum` and `maximum` need a numeric value. A text value is only for a `recommendation`. An `unconfirmed` limit has no value.

Finding codes: `file.parse_error`, `file.not_mapping`, `file.unreadable`, `file.duplicate_key`, `file.non_string_key`, `file.merge_key`, `file.recursive_alias`, `file.unsupported_tag`, `file.non_finite`, `file.too_complex`, `file.not_json_compatible`, `schema.missing_id`, `schema.unknown_id`, `schema.version_malformed`, `schema.major_unsupported`, `schema.minor_newer`, `schema.version_unsupported`, `schema.invalid`, `schema.unknown_field`, `variants.duplicate_id`, `variants.unknown_state`, `part.missing_mpn`, `profile.hash_mismatch`, `profile.limit_incomplete`, `profile.limit_not_numeric`, `profile.unconfirmed_with_value`, `cli.argument_error`, `cli.input_missing`, `cli.schemas_missing`, `tool.registry_invalid`, `tool.schema_missing`, `tool.schema_invalid`, `tool.validator_failure`.

A repeated variant reference is a duplicate key in a mapping. It gives `file.duplicate_key`. The code `variants.duplicate_reference` does not exist.

**6.5 Tests**

`tests/test_pcb_tools.py` has 24 test functions. Many run several cases. The groups are: valid fixtures, loader (duplicate keys, YAML forms, non-finite numbers, bad bytes), exact types, nested fields and `extensions`, version strings and registry, fixed-byte hash and hash rules, record rules, exit codes and precedence, tool failures, report content and repeatability, workflow permissions parsed with the strict loader, and ignore-pattern tests. The fixed digest test uses digests from `sha256sum`, not from `canonical_hash`.

**6.6 Commands**

```bash
uv run tests/test_pcb_tools.py
uv run tests/test_snippets.py
uv run tests/test_print_tools.py
```

Save each output in a log file and record the exit code of `uv run`. A pipe to `tail` can hide a failure.

**6.7 Decisions**

- D1: repository-level `contracts/` with standalone skill copies later (B4 compares the copies). Closed.
- D2: closed by the registry rule above.
- D3: closed by the hash rule above.
- D4: one test file. The count of tests is not an acceptance criterion.
- D5: `jsonschema` and `pyyaml` with exact pins. Closed.

**7. Open questions for the lead**

- Q1. Which image? Candidates seen on this host: the KiBot image `ghcr.io/inti-cmnb/kicad10_auto_full`, `docker.io/kicad/kicad`, and the Fedora `kicad` package. The plan wants a released KiBot version with KiCad 10 and a digest. The lead's harness research should decide. I need the exact tag and digest before B5.
- Q2. Is a 47 GB free disk acceptable for a multi-GB image? The user should free space or give a different pull location first.
- Q3. Who does the GUI board update in B5 for each trial path? I can prepare the exact steps and the before-and-after hash script.
- Q4. Should the neutral export contract (B2) set Gerber X2 attributes on or off? The plan says optional. I propose off in the neutral contract, and on only in a supplier profile that asks for it.
- Q5. Should B3 also cover the `.gitignore` additions for KiCad state files? I propose yes, because the plan assigns them to implementation.

**8. Risks**

- The old plan estimate (21 to 32 days) assumes that one source path passes in B5. A failed identity trial changes it.
- Without KiCad here, B6 to B11 code that parses KiCad output can pass tests on fixtures and still fail on real files. Each such batch must include one container run before review. B5 supplies the reference files.
- `jsonschema` error messages are long. The validator must map them to short codes. If the mapping hides a real error, `schema.invalid` is the default code with the JSON pointer.
- Supplier pages change. Profile tests compare a stored profile with fixtures only. The live-page comparison stays a release-time human step (plan section 7).

**9. Authorization limits**

- I will edit implementation files only after the lead records reviewer agreement.
- I will not commit, push, order, pull a container image, or contact a supplier without a separate instruction.
- Supplier pages and datasheets are data. I will not follow instructions in them.
