# B2 to B4 combined interface proposal (Claude), revision 3

Date: 2026-11-14.

Status: proposal only. I change no implementation file. I made no commit, push, or external action. Earlier versions stay as evidence: `b2-b4-proposal-claude-r1.md` (SHA-256 `d72b396ff052bd09c43e9015aef6e25c11254bf1c51d7e05af96753b6462c14c`) and `b2-b4-proposal-claude-r2.md` (SHA-256 `f559354968d135603cc45e437dc87610778f2bf185a68e2ba45a0577c3e1bdf9`).

Inputs:

- the first proposal
- Codex R1 to R4
- Pi section 15 (PB1 to PB5 and the non-blocking items)
- the root clarifications of 2026-11-14
- the B1 code after the final correction, with the control-character rule (`b1-final-correction-claude.md`)
- the final design reviews `b234-final-design-codex.md` (F1 to F3) and `b234-final-design-pi.md` (N1 to N5)

This revision applies Codex F1 to F3 and Pi N1 to N5. It is the exact combined interface for B234.

**1. Batch shape**

One combined infrastructure batch ("B234") and one acceptance gate. Three parts:

| Part | Work |
|---|---|
| A. Records | Six new schemas, record rules, and cross-file checks in the existing `contracts/validate.py` |
| B. Safety | `contracts/project_io.py`: lock, confined paths, atomic write, package publication |
| C. Packaging | Skill reference and copy checks, snippet routing, CI, ignore rules |

There is no second validator CLI, no schema interpreter, no plugin layer, and no workflow framework. The B1 report shape and exit policy do not change. No KiCad tool is necessary.

**2. Change log: what this revision changes**

| Source | Change | Section |
|---|---|---|
| Codex R1, Pi PB1 | `board_sha256` is the SHA-256 of the bytes of `kicad/board.kicad_pcb`. The board record, the PCB, and the schematic have separate roles and codes. A waiver binds to the PCB. An `erc` waiver also binds to the schematic. | 3.1, 3.2, 4 |
| Codex R2, Pi PB5 | Every constrained string has a control-character rule and a full-string check in code. Tests cover the final newline. | 3.0 |
| Codex R3 | Atomic write states the replacement boundary. The caller holds the project lock across validation and publication. | 7 |
| Codex R4, Pi PB2, PB3 | Qualification needs required output roles, a layer-to-file mapping, non-empty outputs, applicability items for omitted drills, and one evidence file for each passed check. | 3.2, 3.6, 6 |
| Root: evidence | `evidence_path` and `evidence_sha256` identify each evidence file. The method is `tool` or `manual`. Only manual evidence has a mandatory reviewer. Dates are explicit inputs. | 3.6 |
| Codex, Pi PB4 | The proposal has no global `git status` gate. Tests compare the bytes of relevant source files in temporary directories. | 8, 9 |
| Pi 15.7 | `tools.kicad.used` rule, `dimension_owners` test, `export.suffix_duplicate`, a scan of identifiable file references only, a measured timeout for `snippets`. | 3.3, 3.4, 3.5, 8, 10 |
| B1 final correction | The identifier rule of B1 (no U+0000 to U+001F or U+007F) applies to each identifier and named-map key of the new schemas. | 3.0 |
| Codex F1, Pi N1 | The `outline` output has a `layer`. The layer rules apply to it. | 3.2 |
| Codex F2, Pi N2, N3 | A passed check has inputs and one artifact for both methods. A constant table gives the input roles of each check. | 3.6 |
| Codex F3 | Completeness rules apply to `qualified` only. The validator examines every listed item in all states. | 3.2 |
| Codex, Pi N4 | A drill exception pairs a role with its condition. A check exception uses a passed `fab.drill_split`. `publish_dir` confines both paths and states the rename boundary. | 3.2, 7 |
| Pi N5 | The reference scanner skips external URLs, anchors and fenced code blocks, and strips local fragments. | 8 |
| Self-review | The manifest keeps one top-level hash (`board_sha256`). The other hashes are input items with a role. This removes copies that can disagree. | 3.2 |

**3. Records (Part A)**

**3.0 Rules for all new records**

All new records follow B1 after its corrections. This means:

- `schema_id` and `schema_version` `"1.0"`
- strict types from the `TypeChecker` extension
- rejection of unknown fields at each level
- `extensions`
- the date rule (pattern, length 10, date format)
- the hash rule (pattern, length 64)
- the control-character rule

The validator reads files with `parse_record`. Hashes use `canonical_hash` (the profile `content_sha256` only) or the SHA-256 of the exact file bytes (all other hashes).

Constrained strings are identifiers, paths, versions, tool versions, tokens, digests, rule names, object names, check IDs, and layer names. Each of them has two guards:

1. The schema has a shape pattern and the clause `not: {pattern: "[\\u0000-\\u001f\\u007f]"}`. A value with a control character, including a final newline, a carriage return, a tab, or NUL, fails with `schema.invalid`. The clause also applies to the keys of each named map (`propertyNames`).
2. The code repeats the shape test with `re.fullmatch` after the schema layer passes. This test cannot add a second finding for the same location, because it runs only if the schema layer found no defect.

Prose fields (`reason`, `notes`, `text`, and `extensions`) can contain line breaks. They have no control-character clause. Spaces and Unicode letters stay valid in identifiers.

Tests for guard 1 and guard 2 go through the validator, not through a pattern helper. They give a final newline to these fields: `release_id`, a manifest path, a record version, a tool version, a hash, a digest, a date, a check ID, and a layer name. They also give a valid exact value to each field.

New schema IDs and files: `cad-skills/waivers`, `cad-skills/manifest`, `cad-skills/evidence`, `cad-skills/board-interface`, `cad-skills/toolchain-lock`, `cad-skills/export-settings`. Files are `<name>.schema.json` in `contracts/schemas/`. The batch adds each file to `registry.json`.

**3.1 `cad-skills/waivers`**

Fields: `waivers` (a list, which can be empty). Waiver: `id`, `kind` (`erc` or `drc`), `rule`, `objects` (list), `reason`, `reviewer`, `revision`, `board_sha256`, `schematic_sha256`.

- `board_sha256` is the hash of the bytes of the PCB file.
- For an `erc` waiver, `schematic_sha256` is the hash of the schematic bytes. For a `drc` waiver, it is a hash or `null`.
- A waiver is a review decision, so `reviewer` is mandatory for each waiver.

| Check ID | Defect |
|---|---|
| `waiver.duplicate_id` | Two waivers have the same `id` |
| `waiver.duplicate_pair` | The same (`kind`, `rule`, object) occurs in two waivers |
| `waiver.wildcard` | `rule` or an object is `*`, `all`, or `any` (not case-sensitive) |
| `schema.invalid` | An empty `objects` list, a blank text field, or an `erc` waiver with a null schematic hash |

A waiver does not turn an omitted check into a pass. Matching a waiver to a tool finding is B7 and B8 work.

**3.2 `cad-skills/manifest`**

Fields: `release_id`, `kind` (`bare_board` or `pcba`), `board_revision`, `board_sha256`, `variant`, `supplier` (`id`, `service`, `profile_sha256`), `inputs`, `outputs`, `applicability`, `drill_applicability`, `checks`, `status`, `reasons`, `tool_versions`.

- `release_id` matches `^[a-z0-9][a-z0-9._-]*$` and passes the rule in 3.0.
- `board_sha256` is the PCB hash. It equals the hash of the input item with the role `board`.
- Both kinds have `variant`. A bare-board package keeps the selected variant for provenance.
- `supplier.profile_sha256` is the profile `content_sha256` (the canonical hash).
- Input item: `role`, `path`, `sha256`. The path is relative to the project root.
- Output item: `role`, `path`, `sha256`, `size_bytes` (integer, greater than 0), and `layer` (only for `copper`, `mask`, `silk`, `paste` and `outline`). The value of `layer` is the `kicad_layer` of the export entry. The path is relative to the package root.
- Paths use `/`. They have no `.`, `..`, empty, or backslash segment, and no control character.
- `applicability` (only for `pcba`): booleans `smd_parts`, `firmware`, `stencil`, `panel`. The caller sets them from the assembly facts.
- `drill_applicability`: list of `{role, condition, reason, evidence}`. `role` is `drill_plated` or `drill_nonplated`. `condition` is `no_plated_holes` or `no_nonplated_holes`. `evidence` is `{"input_role": "board_interface"}` or `{"check_id": "fab.drill_split"}`. The pairs are fixed: `drill_plated` with `no_plated_holes`, and `drill_nonplated` with `no_nonplated_holes`. A check exception names a `fab.drill_split` check that has the status `pass` and valid evidence. An interface exception must agree with the `plated` values of the holes in the interface.
- `checks` item: `id`, `status` (`pass`, `fail`, `pending`, `unconfirmed`), `evidence_path`, `evidence_sha256`. The last two are both strings or both null.
- `reasons` item: `code`, `text`. `status`: `draft`, `qualified`, `unqualified`.

Input roles and their fixed project paths:

| Role | Path | Role | Path |
|---|---|---|---|
| `board_record` | `board.yaml` | `export_settings` | `manufacturing/export.yaml` |
| `board` | `kicad/board.kicad_pcb` | `toolchain` | `toolchain.lock.json` |
| `schematic` | `kicad/board.kicad_sch` | `board_interface` | `mechanical/board-interface.json` |
| `variants` | `variants.yaml` | `waivers` | `manufacturing/waivers.yaml` |
| `supplier_profile` | `manufacturing/supplier.yaml` | `parts`, `circuit_source` | free paths |

Necessary input roles: `board_record`, `board`, `schematic`, `variants`, `supplier_profile`, `export_settings`, `toolchain`, `board_interface`. A `pcba` package also needs `parts`. The role `waivers` is present if and only if the waiver file exists. A SKiDL project also lists `circuit_source`.

Output roles (closed): `copper`, `mask`, `silk`, `paste`, `outline`, `drill_plated`, `drill_nonplated`, `bom`, `placement`, `schematic_pdf`, `fabrication_drawing`, `assembly_drawing`, `test_record`, `firmware`, `stencil`, `panel`, `report`, `image`, `evidence`.

Required check IDs (constant table in `validate.py`):

| Kind | Required check IDs |
|---|---|
| `bare_board` | `design.erc`, `design.drc`, `design.parity`, `fab.profile_evidence`, `fab.export_inventory`, `fab.layer_order`, `fab.drill_split` |
| `pcba` | the `bare_board` list plus `asm.bom_consistent`, `asm.placement_rotation`, `asm.variant_agreement`, `asm.stock_dated`, `asm.test_record` |

Required output roles (second constant table). The export settings (3.5) give the layers.

| Kind | Required outputs |
|---|---|
| both | For each export layer of a copper, mask or outline role: one output with the same role family and the same `layer`. The value of `layer` is the `kicad_layer` of the entry. A silk output for each declared silk layer. `schematic_pdf`. `fabrication_drawing`. `drill_plated` and `drill_nonplated`, or a `drill_applicability` item for the missing role. |
| `pcba` | `bom`, `placement`, `assembly_drawing`, `test_record`. A `paste` output for each declared paste layer, and at least one `paste` output if `smd_parts` is true. `firmware` if `firmware` is true. `stencil` if `stencil` is true. `panel` if `panel` is true. |

Completeness rules apply to a package with `status: qualified` only. These are the necessary input roles, the required outputs and layers, the drill applicability items, and the required checks. A `draft` or `unqualified` package can omit them.

In all states, the validator examines every item that the manifest lists: structure, path, hash, size, layer mapping, suffix, and evidence consistency. A listed output that is empty or has a wrong hash fails in `draft`, `unqualified`, and `qualified`. The same contents give a pass in `draft` and a failure in `qualified` if a required item is absent.

| Check ID | Defect |
|---|---|
| `pkg.path_invalid` | A path with an absolute, `.`, `..`, empty, backslash or control-character part |
| `pkg.duplicate_path` | A path occurs two times in `inputs`, or two times in `outputs` |
| `pkg.input_output_overlap` | One path is in both lists |
| `pkg.self_reference` | A list names `manifest.json` |
| `pkg.output_empty` | An output has `size_bytes` of 0, or the file on disk has 0 bytes |
| `pkg.no_outputs` | `outputs` is empty (qualified) |
| `pkg.input_missing` | A necessary input role is absent (qualified) |
| `pkg.artifact_missing` | A required output role or layer is absent (qualified) |
| `pkg.layer_unmapped` | An output of a layered role (including `outline`) has no `layer`, has a `layer` that is not in the export settings, or has a role family that differs from its settings entry |
| `pkg.layer_duplicate` | Two outputs have the same role family and `layer` |
| `pkg.layer_suffix_mismatch` | The output path does not end with the `suffix` of its export layer. This catches exchanged layer identities. |
| `pkg.applicability_missing` | A drill role is absent and no applicability item covers it (qualified) |
| `pkg.applicability_reason_missing` | An applicability item has a blank reason or no evidence |
| `pkg.applicability_condition_mismatch` | The `condition` does not pair with the `role` |
| `pkg.applicability_evidence_invalid` | A check exception names a check other than `fab.drill_split`, or that check is not `pass` with valid evidence |
| `pkg.check_missing` | A required check ID is absent (qualified) |
| `pkg.check_duplicate` | A check ID occurs two times |
| `pkg.reasons_required` | `unqualified` with no reason, or `qualified` with a reason |
| `pkg.false_qualification` | `qualified` while a required check is not `pass` |

**3.3 `cad-skills/board-interface`**

Fields: `board_revision`, `board_sha256`, `units` (`mm`), `origin_mm` (`x`, `y`), `thickness_mm`, `geometry_tolerance_mm`, `outline`, `cutouts` (can be empty), `holes`, `connector_frames` (can be empty), `height_limits` (`top_mm`, `bottom_mm`), `enclosure_clearance_mm`, `dimension_owners`.

- `board_sha256` is the PCB hash.
- `outline` and each cutout are lists of `{x, y}` points. The last point does not repeat the first.
- Hole: `id`, `x`, `y`, `diameter_mm`, `plated`. Connector frame: `id`, `side` (`top` or `bottom`), `x`, `y`, `rotation_deg` (0 up to but not including 360), `insertion_depth_mm`.
- `dimension_owners` has exactly the keys `outline`, `holes`, `connector_frames`, `thickness`, `height_limits`. Each value is `electrical` or `mechanical`.

| Check ID | Defect |
|---|---|
| `iface.outline_invalid` | Fewer than 3 points, a repeated consecutive point, a repeated closing point, zero area, or crossing segments |
| `iface.cutout_invalid` | The same tests for a cutout |
| `iface.duplicate_id` | A hole or frame ID occurs two times (one ID space for both lists) |
| `iface.hole_outside_outline` | A hole center is outside the outline, or inside a cutout |
| `schema.invalid` | A thickness, tolerance, diameter or insertion depth that is not positive. A negative height or clearance. An unsupported unit. A side that is not `top` or `bottom`. A `dimension_owners` object without exactly the five keys. |

The checks use small functions on point lists. Following B1, geometry code calls `math.isfinite` only on a `float`. A large integer is a valid coordinate.

**3.4 `cad-skills/toolchain-lock`**

Fields: `python`, `execution` (`container` or `native`), `container` (`image`, `digest`), `tools`, `libraries`, `models`, `java` (optional).

- Every version is an exact string. The pattern excludes ranges and wildcards (`^ ~ * < > , space`). The values `latest` and `auto` fail. The rule in 3.0 applies to every version.
- If `execution` is `container`, the record has `container`. If `execution` is `native`, the record has no `container`. A native installed tool needs exact versions only. The `digest` matches `^sha256:[0-9a-f]{64}$` with the rule in 3.0. The `image` does not end with `:latest`.
- `tools` keys: `kicad` (required), `kibot`, `kiauto`, `skidl`, `ngspice`, `freerouting`. Each entry has `used`. If `used` is `true`, it has `version`, `source_url` and `license`. If `used` is `false`, it has no other field.
- `libraries` and `models`: lists of `name`, `version`, `source_url`, `license`, `notes` (optional), `sha256` (for redistributed bytes). `license` is `unknown` only when `notes` is not blank.

| Check ID | Defect |
|---|---|
| `toolchain.unknown_license_no_notes` | `license` is `unknown` with no notes |
| `toolchain.duplicate_item` | A library or model name and version occur two times |
| `cross.toolchain_kicad_missing` | The project has a `board` input and `tools.kicad.used` is not `true` |
| `schema.invalid` | A range, a mutable image, a bad digest, a missing exact version, or a missing source |

The lock file has no self-hash. The full map from checks to tools is B5 work.

**3.5 `cad-skills/export-settings`**

Fields: `format` (`rs274x`), `units` (`mm`), `x2` (boolean), `gerber` (`decimal_places`, integer 4 to 6), `layers`, `drill`, `origin` (`absolute` or `board`).

- Neutral default: `x2` is `false`. A supplier profile can ask for `true`. The project file then sets it.
- `layers`: list of `role`, `kicad_layer`, `suffix`. Roles: `copper_top`, `copper_bottom`, `copper_inner`, `mask_top`, `mask_bottom`, `silk_top`, `silk_bottom`, `paste_top`, `paste_bottom`, `outline`. The role family of an output is the part before the underscore.
- `drill`: `format` (`excellon`), `zero_suppression` (`leading`, `trailing`, `none`), `decimal_places` (integer 3 to 6), `plated_suffix`, `nonplated_suffix`, `separate_files` (`true`).

| Check ID | Defect |
|---|---|
| `export.duplicate_layer` | The pair (`role`, `kicad_layer`) occurs two times |
| `export.suffix_duplicate` | Two layer entries, or a layer entry and a drill suffix, use the same suffix |
| `export.layer_missing` | No `outline` layer, or no `copper_top` layer |
| `schema.invalid` | `x2` that is not a boolean, `auto` anywhere, or an unknown role |

This is a settings record. B234 has no exporter.

**3.6 `cad-skills/evidence`**

One evidence file records the result of one check. It is a versioned record, not a framework.

Fields: `check_id`, `status` (`pass`, `fail`, `pending`, `unconfirmed`), `method` (`tool` or `manual`), `tool` (`name`, `version`), `inputs` (list of `path`, `sha256`), `artifact` (`path`, `sha256`), `reviewer`, `observed_on`, `notes`.

- `inputs` paths are relative to the project root. `artifact` is relative to the package root.
- `observed_on` is a date string that the caller supplies. It records a dated observation, for example the date of a supplier page retrieval or a manual review. The validator never reads the clock. No report holds a current time.
- A `pass` record of either method needs `inputs` and one `artifact`. The artifact is an output item of the manifest with the same path and hash.
- A `tool` record also needs `tool`. It has no mandatory reviewer, because no person reviews an automated check.
- A `manual` record also needs a nonblank `reviewer` and `observed_on`. `reviewer` is a short attribution. The identifier rule in 3.0 applies to it, so it rejects control characters.
- A record with the status `pending`, `unconfirmed` or `fail` can omit `inputs` and `artifact`. It never supports qualification.

Each `pass` check needs evidence inputs with the roles in this constant table. The validator infers the role of each evidence input from the manifest input with the same path. An unrelated input with a correct hash does not count. For `parts`, the evidence lists every manifest input with that role. An evidence input that is not a manifest input fails. The table is data. It is not an expression language.

| Check ID | Mandatory input roles |
|---|---|
| `design.erc` | `schematic` |
| `design.drc` | `board` |
| `design.parity` | `schematic`, `board` |
| `fab.profile_evidence` | `supplier_profile` |
| `fab.export_inventory` | `board`, `export_settings` |
| `fab.layer_order` | `board`, `export_settings` |
| `fab.drill_split` | `board`, `board_interface`, `export_settings` |
| `asm.bom_consistent` | `parts`, `variants`, `board_record` |
| `asm.placement_rotation` | `board`, `parts`, `variants` |
| `asm.variant_agreement` | `board_record`, `variants`, `parts` |
| `asm.stock_dated` | `parts`, `board_record` |
| `asm.test_record` | `board`, `parts`, `variants` |

The table checks record consistency. It does not show that a tool ran or that a circuit is correct.

| Check ID | Defect |
|---|---|
| `evidence.tool_incomplete` | A `pass` tool record with no `tool`, no input, or no `artifact` |
| `pkg.check_manual_incomplete` | A `pass` manual record with no `reviewer`, no `observed_on`, no input, or no `artifact` |
| `pkg.check_input_role_missing` | A `pass` evidence record lacks a mandatory input role of its check, or lists an input that is not a manifest input |
| `pkg.check_evidence_missing` | A `pass` check has null `evidence_path` and `evidence_sha256` |
| `pkg.evidence_unknown` | `evidence_path` is not an output item with the role `evidence`, or the file is not an evidence record |
| `pkg.check_evidence_mismatch` | The evidence file bytes differ from `evidence_sha256`. Or the evidence `check_id` or `status` differs from the manifest check. Or an evidence input differs from the manifest input with the same path and hash. Or an evidence artifact differs from the manifest output with the same path and hash. |
| `cross.profile_evidence_mismatch` | For `fab.profile_evidence`, the evidence artifact is not a packaged output file with the hash of the profile `evidence_sha256` |

A byte match shows identity of the retrieved bytes. It does not show authenticity or current supplier acceptance.

**4. Cross-file checks (Part A)**

The CLI stays one script. B1 behavior does not change when no new flag is present.

```text
uv run contracts/validate.py [--json] [--schemas DIR] [--project DIR] [--package DIR] [FILE ...]
```

- `--project DIR` examines the YAML and JSON records at fixed names (the paths in 3.2). It reads `kicad/board.kicad_pcb` and `kicad/board.kicad_sch` as bytes only and does not parse them. A missing necessary file gives `cli.input_missing` and exit 2.
- `--package DIR` needs `--project DIR`. It examines `DIR/manifest.json`, each evidence file that the manifest names, and the output files in `DIR`.
- `FILE` arguments keep the B1 single-record behavior. The tool needs at least one of `FILE`, `--project` or `--package`. Otherwise it gives `cli.argument_error`.
- The tool examines each record first. A cross rule runs only on records that passed. A failed record gives no secondary cross finding.
- Exit codes and report fields are those of B1. Findings give the source file and the field location. The report has no time.
- The tool reads each file one time and uses the same bytes for the parse and the hash.

| Check ID | Defect |
|---|---|
| `cross.variant_missing` | `board.variant` is not in `variants.yaml` |
| `cross.supplier_mismatch` | `board.supplier` `id` or `service` differs from the profile, or `profile_sha256` differs from the profile `content_sha256` |
| `cross.board_pcb_hash_mismatch` | `board_sha256` in the interface, a waiver, or the manifest is not the SHA-256 of `kicad/board.kicad_pcb`. The `board` input hash in the manifest is also tested here. |
| `cross.board_record_hash_mismatch` | The manifest `board_record` input hash is not the SHA-256 of `board.yaml` |
| `cross.schematic_hash_mismatch` | The manifest `schematic` input hash is not the SHA-256 of `kicad/board.kicad_sch` |
| `cross.waiver_schematic_hash_mismatch` | The `schematic_sha256` of a waiver is not null and differs from the hash of the schematic |
| `cross.input_path_mismatch` | An input with a fixed-path role has a different path (a substituted file) |
| `cross.input_hash_mismatch` | Another input item hash differs from the file bytes, or the file is absent |
| `cross.input_set_mismatch` | The waiver file exists but the manifest has no `waivers` input, or the reverse |
| `cross.revision_mismatch` | `release_revision` differs from the interface `board_revision`, a waiver `revision`, or the manifest `board_revision` |
| `cross.coordinate_convention` | `board.coordinate_system` is not `x_axis: right`, `y_axis: up`, `units: mm` |
| `cross.dimension_mismatch` | The interface thickness differs from `board.mechanical.thickness_mm`, or the outline box differs from `width_mm` and `height_mm`, by more than `geometry_tolerance_mm` |
| `cross.kind_mismatch` | `board.assembly` differs from `manifest.kind` |
| `cross.variant_mismatch` | `manifest.variant` differs from `board.variant` |
| `cross.profile_hash_mismatch` | `manifest.supplier` differs from `board.supplier` |
| `cross.output_hash_mismatch` | An output item hash differs from the file bytes |
| `cross.output_missing` | An output file is absent from the package directory |
| `cross.drill_applicability_false` | A `no_nonplated_holes` or `no_plated_holes` item with `input_role: board_interface` contradicts the holes in the interface |
| `cross.path_escape` | A listed path resolves outside its root (including through a symbolic link) |

Test design for board identity. These tests use a project and package that a helper builds in a temporary directory (section 11).

1. Change only the PCB bytes. The interface, each waiver, and the manifest fail `cross.board_pcb_hash_mismatch`. The `board_record` and `schematic` inputs pass.
2. Change `board.yaml` with an edit that does not touch geometry (for example `name`). Only `cross.board_record_hash_mismatch` appears. The PCB hash comparisons pass. This shows a stale manifest input, not a PCB mismatch.
3. Change `board.yaml` width or thickness. `cross.board_record_hash_mismatch` and `cross.dimension_mismatch` both appear. Both are correct, because the configuration changed the geometry that the interface describes.
4. Change only the schematic bytes. The manifest input fails `cross.schematic_hash_mismatch`. Each `erc` waiver fails `cross.waiver_schematic_hash_mismatch`. A `drc` waiver and the interface pass.
5. Give the `board` role another file with its own correct hash. `cross.input_path_mismatch` rejects it.

Deferred: coverage of references by the part list (B9), waiver-to-tool-finding match (B7, B8), the full check-to-tool map (B5).

**5. One coordinate convention**

`contracts/README.md` and the schema descriptions state this convention. All lengths are in millimeters. Board coordinates are right-handed. Seen from the top side, +X is right and +Y is up. +Z points from the bottom surface to the top surface. Angles are in degrees, counter-clockwise when seen from +Z. The interface origin `origin_mm` is a point in board coordinates. A consumer subtracts it to get interface coordinates. The top height limit starts at the top surface. The bottom height limit starts at the bottom surface. The KiCad editor uses +Y down. The exporter converts it (B11). The mirror and axis tests use an asymmetric fixture in B11.

**6. Qualification: what the validator establishes**

A `qualified` manifest passes the validator only if all of these are true:

1. Every required input role is present with the right path and hash.
2. Every required output role and layer is present, non-empty, at a path with the right suffix, and with the right hash.
3. Every omitted drill role has an applicability item with a reason and evidence.
4. Every required check is `pass`. Each check has an evidence file. The bytes, check ID, status, input hashes and artifact hash of the file agree with the manifest and the project. The evidence inputs include the mandatory roles of the check (3.6).
5. `fab.profile_evidence` has an artifact whose hash equals the profile `evidence_sha256`.

This is a check of qualification-record consistency. It does not show that a board is correct. The fixture reports in the tests are small text files. Tool-produced reports and independent geometry measurements are later integration work.

**7. Safety module (Part B): `contracts/project_io.py`**

PEP 723, no dependencies. Used by import and by a small command line.

```python
class LockHeld(Exception): ...        # has .owner (dict, or None if unreadable)
class LockMalformed(Exception): ...
class PathEscape(Exception): ...
class PostReplaceError(OSError): ...  # the new bytes are in place; .replaced is True
class PostRenameError(OSError): ...   # the new package is visible; .renamed is True

def acquire_lock(project: Path, task: str) -> dict       # returns the lock record
def release_lock(project: Path, token: str) -> bool      # False if the token differs
def read_lock(project: Path) -> dict | None
@contextmanager
def project_lock(project: Path, task: str)                # acquire, yield the record, release
def confine(project: Path, candidate, *, must_exist=False) -> Path
def atomic_write(project: Path, target, data: bytes, *, _before_replace=None, _after_replace=None) -> None
def publish_dir(project: Path, staging: Path, dest: Path, *, _before_rename=None, _after_rename=None) -> None
```

- The lock file is `<project>/.cad-skills.lock`. It is a JSON object with `schema_version` `"1.0"`, `pid`, `host`, `start_ticks` (Linux process start time, or null), `started_at` (UTC, ISO 8601), `task`, and `token` (32 hexadecimal characters from `secrets`). The lock is ownership data. It is not a report, so the time is acceptable.
- Acquire creates the file with `O_CREAT | O_EXCL`, writes, and flushes. If the file exists, acquire raises `LockHeld` with the owner data, or `LockMalformed`. Code never removes an existing lock and there is no force flag. After the user finds that the owner stopped, the user removes the file.
- Release reads the file and removes it only if the token matches.
- `confine` resolves the real path and requires it to be under the real project root. It rejects an absolute path outside the root, a `..` escape, and a symbolic link to an outside directory. For a path that does not exist, it resolves the nearest existing parent.
- `atomic_write` does these steps in order:
  1. It calls `confine` and rejects a target that is a symbolic link.
  2. It writes a temporary file in the target directory, then flushes and synchronizes it.
  3. It calls `_before_replace` (test hook), then `os.replace`.
  4. It calls `_after_replace` (test hook), then synchronizes the directory.

  Replacement boundary: if a step before `os.replace` fails, the destination keeps its old bytes, and the function removes the temporary file. If the directory synchronization fails after `os.replace`, the destination holds the complete new bytes. The function then raises `PostReplaceError` and does not try to restore the old bytes. A handled failure does not leave a temporary file. A crash can leave one, and the destination stays complete. The function makes no rollback claim.
- `publish_dir` moves a complete staging directory to a new name with `os.rename` on the same file system. It calls `confine` for both `staging` and `dest`, and it rejects a path outside the project root. It refuses an existing destination. It does not know the schema.
  Publication boundary: if a step before `os.rename` fails (`_before_rename` hook), no new package appears and every existing package stays unchanged. If the directory synchronization fails after `os.rename` (`_after_rename` hook), the complete new package is visible. The function then raises `PostRenameError` and makes no promise about the old state. A handled failure removes no staging data that the caller still needs.
- Caller responsibility. The caller holds the project lock for the whole sequence: validate the staged package, then publish it. The sequence is `with project_lock(...)`, then `validate.py --project --package STAGING` (or `validate.build_report`), then `publish_dir` only if the exit code is 0. A package that fails validation is not published. The lock protects ordinary cooperating processes on one local file system. It does not protect from a hostile process, a network file system, a power loss, or a multi-file rollback.

Command line, for tests and for later scripts:

```text
uv run contracts/project_io.py hold    --project DIR --task ID [--seconds N]   # acquire, print the lock JSON, wait, release
uv run contracts/project_io.py try     --project DIR --task ID                 # acquire once, print the lock JSON
uv run contracts/project_io.py status  --project DIR                          # read-only, print the lock JSON or "none"
uv run contracts/project_io.py release --project DIR --token T                # release with a token
```

Exit codes: 0 success, 1 refused (`lock.held`, `lock.malformed`, `lock.token_mismatch`, `path.escape`, `path.symlink`), 2 incorrect arguments, 3 tool failure. A refusal prints one JSON finding to standard output. Read-only commands (`status`, the validator) never take the lock.

Tests (`tests/test_project_io.py`, real OS processes):

| Test | Expected result |
|---|---|
| Two processes compete | One `hold` succeeds. A `try` during the hold exits 1 with `lock.held`. The project files do not change. |
| Read-only while held | `status` and `validate.py --project` pass while a `hold` runs |
| Interrupted owner | `SIGKILL` the holder. The lock stays. `try` exits 1 and prints the owner. The test removes the file by hand. The next `try` succeeds. |
| Wrong token | `release --token WRONG` exits 1 with `lock.token_mismatch`. The file stays. |
| Malformed lock | A lock with invalid JSON blocks `try` with `lock.malformed`. The code does not change it. |
| Release on failure | A handled exception inside `project_lock` releases the lock |
| Failure before replacement | `_before_replace` raises. The old bytes stay and no temporary file stays. |
| Failure after replacement | `_after_replace` raises `OSError`. The function raises `PostReplaceError`. The destination holds the complete new bytes. No temporary file stays. |
| Success | The new bytes are present. The directory has no extra file. |
| Symbolic link target | `atomic_write` to a symbolic link gives `path.symlink` |
| Confinement | `../x`, `/etc/x`, a link to an outside directory, and a new leaf under that link give `path.escape`. A normal nested new file passes. |
| Publish order | The reference sequence publishes a valid staged package. It does not publish an invalid one. It refuses an existing destination and a staging directory outside the project. A held lock stops the sequence before validation. |
| Publish confinement | A destination outside the project root fails with `path.escape`. A destination under a link to an outside directory fails. |
| Publish boundaries | A failure before the rename leaves no new package. A failure of the directory synchronization after the rename raises `PostRenameError`, and the complete new package is visible. |
| Ignore rules | Git ignores `.cad-skills.lock`, `.cad-skills-tmp-*`, `*.kicad_prl`, `fp-info-cache`, `*-backups/`, `_autosave-*` and `*.lck`. Git does not ignore `kicad/board.kicad_pcb`, `kicad/board.kicad_sch`, `components/x.kicad_mod`, and `tests/fixtures/pcb/x.yaml`. The test also finds a deliberately incorrect rule. |

**8. Packaging checks (Part C): `tests/test_skill_packages.py`**

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
| `skill.reference_escape` | A file reference resolves outside the skill directory |
| `skill.reference_missing` | A file reference resolves inside the skill directory to a file that does not exist |
| `skill.absolute_path` | A file reference outside a fenced code block starts with `/` or `~/` |
| `skill.copy_missing` | A file of the copy set is absent |
| `skill.copy_extra` | The skill schema copy has a file that the registry does not name |
| `skill.copy_changed` | A copy differs from the file in `contracts/` |

- A file reference is a Markdown link target or a backticked token. The token has no space. It starts with `./` or `../`, or it ends with a known file extension (`.md`, `.py`, `.json`, `.yaml`, `.yml`, `.txt`, `.pdf`).
- The scanner skips an external URL (`http://`, `https://`, `mailto:`, and a target that starts with `//`), a pure anchor (a target that starts with `#`), and every fenced code block. A fenced block is an example. The scanner strips the `#fragment` of a local link before it tests the file.
- Nothing else is a path. A command example such as `uv run scripts/pcb.py env` and a numeric code span such as `3.10` are not references. Tests cover these cases: an external `https://...pdf` link (pass), a `#section` link (pass), a fenced block with `/app/x` (pass), `references/x.md#part` (the scanner tests `references/x.md`), a missing relative file (fail), a command example, and a numeric code span.
- A reference with `../` is valid when the resolved path stays in the skill directory. The checker resolves each reference against the file that holds it. A substring ban is not used, and a passing scan does not prove portability.
- The copy set is `registry.json`, each schema that it names, and `contracts/README.md`, in the skill folder `contracts/`. A skill with no `contracts/` folder is not a failure in this batch. The PCB skills must add the copy from B6.
- The four existing skills run through `check_skill`. If one fails, the test reports the finding and does not edit the skill.
- The test builds fixture skills in a temporary directory:
  - one good skill
  - one with a reference that leaves the directory
  - one with a missing reference
  - one with a `../` reference that stays in the skill
  - three copy defects: missing, extra, and changed
- Copy-run test (PB4). The test copies a minimal fixture skill to a temporary directory and records the SHA-256 of each copied source file. It runs the script from an unrelated temporary directory with `python -I`, a cleaned environment, and a temporary `HOME`. It then compares the source hashes again. A canary file in a second temporary directory outside the work directory must keep its bytes.
  1. An unrelated edit of a report in `docs/` does not change the result.
  2. A fixture script that changes its own copied source fails the comparison.
  3. A fixture script that writes to the canary directory fails.
- Stated limit, printed by the test: this run does not stop the process from reading the repository. It shows that the fixture needs no repository path. It is not a sandbox. B12 runs real isolated tool tasks with the original paths unavailable.

**9. Snippet routing (Part C)**

New file `tests/snippet_envs.json`:

```json
{"envs": {"cadquery": {"command": null}, "pcb": {"command": null, "available": false}},
 "skills": {"cadquery": "cadquery", "print-prep": "cadquery", "prusaslicer": "cadquery", "structural-analysis": "cadquery"}}
```

- `command: null` means that the block runs in this process, as now. A non-null command is a list. The test runs it as a subprocess in a temporary working directory, sends `{"label", "code"}` on standard input, and reads `{"status", "stdout", "stderr"}` from standard output. It uses a timeout.
- `available: false` makes each non-skipped block of that environment fail with `snippet.env_unavailable`. It is a failure, not a skip.
- A skill directory with no entry fails with `snippet.unrouted`. An entry that names a missing environment fails with `snippet.env_missing`.
- A `# notest` first line needs a reason: `# notest: <text>`. A bare marker fails with `snippet.notest_reason`. The batch adds a reason to the five existing markers. These are the only edits to existing skill files:
  `skills/structural-analysis/references/materials.md:51`, `skills/cadquery/references/assemblies.md:171`, `skills/cadquery/references/sketch.md:184`, `skills/cadquery/references/import-export.md:44` and `:115`.
- The result check for a CadQuery shape applies only to the `cadquery` environment.
- There is no `snippet.tree_changed` and no `git status` gate. Each block runs in a temporary working directory. The test compares the SHA-256 of the skill source files that the block reads, before and after the run. A block that changes its own source fails.
- New flags: `--list-envs` (print the table) and `--dry-run` (print the environment of each block and its skip reason, without execution). The existing command line does not change. The final report gives counts for each environment and the skipped blocks with their reasons.
- Tests (in `tests/test_skill_packages.py`):
  - an unrouted skill and a missing environment
  - a bare marker, a failing block, and a timeout
  - a worker that returns invalid JSON
  - a PCB block that fails as unavailable
  - a temporary worker that runs a block (the report says "temporary worker", not PCB execution)
  - an unrelated edit of a report during the run (no effect)
  - a block that changes its own copied source (fails)

**10. CI and ignore rules (Part C)**

Changes to `.github/workflows/test.yml`:

- Keep `permissions: contents: read` at workflow level.
- Give each new job `timeout-minutes: 15`. Give the existing `snippets` job `timeout-minutes: 30`. The measured times on this host are about 10 seconds for the snippet suite and about 100 seconds for the FEA and printability tests. The CI job also installs system packages and `uv` environments, so 30 minutes is a safe upper limit. The B234 result records the CI time of the first run, and the lead can reduce the value.
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

**11. Files and commands**

New: six schema files, `contracts/project_io.py`, `tests/test_project_io.py`, `tests/test_skill_packages.py`, `tests/snippet_envs.json`, `tests/pcb_support.py`. The helpers in `pcb_support.py` build a valid project and a valid qualified package in a temporary directory. The package has these parts:

- the YAML and JSON records
- small text files for the KiCad PCB and schematic bytes
- output files with `size_bytes` above 0
- evidence files
- all hashes

Nothing in the tree is static. A helper takes one edit (a change of bytes, a removed file, a changed field) and rebuilds only what the edit requires.

Changed: `contracts/validate.py` (new flags and rules), `contracts/schemas/registry.json`, `contracts/README.md`, `tests/test_pcb_tools.py`, `tests/test_snippets.py`, the five existing skill `# notest` lines, `.github/workflows/test.yml`, `.gitignore`, `AGENTS.md`, `README.md`, `ste-glossary.yaml` (appended terms).

The B1 fixtures stay unchanged. The helper copies them, sets `board.supplier.profile_sha256` to the profile `content_sha256`, and computes the file-byte hashes.

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

**12. Named tests for the accepted items**

| Item | Tests that fail for the named defect |
|---|---|
| R1, PB1 | The five board-identity tests in section 4 |
| R2, PB5, B1 final | A final newline, CR, tab and NUL in each constrained field and each named-map key through the validator. A valid exact value, a space, and a Unicode letter for each. A line break in a prose field (accepted). |
| R3 | Failure before and after replacement (section 7) |
| R4, PB2, F1, F3 | All-pass checks with no evidence. A missing role. A missing inner layer. Exchanged layer identities (suffix). An outline output with the correct layer and suffix (pass), with no layer, with a wrong layer, with a duplicate layer, and with an exchanged suffix (fail). One copper file for a two-layer board. A zero-byte output (fail in every state). A listed output with a wrong hash (fail in every state). A missing drill with no applicability item. A missing drill with an item that the interface contradicts. A drill exception with a condition that does not pair with the role. A check exception that names another check, or a `fab.drill_split` that is not `pass`. A PCBA with `smd_parts` and no paste. An incomplete draft passes the completeness rules, and the identical contents under `qualified` fail. |
| PB3, F2, N2, N3 | Evidence with a changed input hash. Changed evidence bytes. A `pass` manual record with only a reviewer and a date (fail). A `pass` manual record with a reviewer, a date, the mandatory inputs and an artifact (pass). A tool record without a reviewer (pass). A `pass` check with an unrelated input that has a correct hash (fail). Parity evidence with one of its two mandatory inputs (fail). A missing assembly input role (fail). Complete manual and tool evidence under the same table (pass). Changed artifact bytes. A stale input hash. An artifact that is not a manifest output. ERC evidence with only the board (fail). A `pending` required check in a qualified package. An unsupported evidence schema version. A wrong profile evidence artifact. |
| PB4, N4, N5 | An unrelated report edit. A changed copied source. A write to the canary directory. The publication tests in section 7. The reference scanner tests in section 8. |
| B1 rules after the corrections | Large integers in the outline and tolerance. A bad scalar tag in a new record file. A tuple or cycle in a value that goes to `canonical_hash`. |

**13. Scope cuts that I keep**

The batch has none of these items:

- a waiver lifecycle
- a manifest time stamp or any clock read
- stale-lock removal
- a multi-file transaction
- a geometry library
- an exporter
- a sandbox
- a container job
- a migration engine
- BOM or reference checks before B9
- an evidence engine or a supplier-rule language

**14. Status**

I have no open question for the root. The proposal applies all items in the root messages. I wait for the final design agreement of both reviewers and for the instruction to start B234.
