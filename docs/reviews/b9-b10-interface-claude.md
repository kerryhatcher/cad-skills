# B9/B10 implementation interface: pcba-design (Claude)

Date: 2026-11-15 UTC. Author: claude-pcba-dev (w1P:p7), product author for `skills/pcba-design`.
Status: proposal. No product file is changed. Implementation waits for the Codex and Pi reviews and lead acceptance.

This interface uses the Codex request of 2026-11-15 01:40:30 UTC, the Pi preparation report, the Codex preparation report, and the B9 source records.

## 1. Scope

- Make `skills/pcba-design` independent. It owns its scripts, contract copies, templates, supplier profile, and retained evidence.
- Output one neutral assembly dataset. Derive all supplier files from that dataset.
- First supplier adapter: Sierra Turnkey PRO. First placement candidate: the PDF sample (`xy.pdf`).
- Sierra XYRS workbook (`xyrs.xlsx`) is Web PCB evidence. It is not a Turnkey PRO format. It is not a second adapter.
- Supplier submission, upload, payment, and physical test are out of scope.

## 2. Copied helpers

Each copy is recorded with its source path and SHA-256 at copy time. The skill never imports another skill at run time.

| Copy | Source | Use |
|---|---|---|
| `contracts/validate.py` | `contracts/validate.py` (shared validator) | Record and manifest validation, including the five `asm.*` checks |
| `contracts/registry.json` | `contracts/schemas/registry.json` | Schema registry |
| Schema `cad-skills/board` 1.0 | `contracts/schemas/board.schema.json` | Board record |
| Schema `cad-skills/board-interface` 1.0 | `contracts/schemas/board-interface.schema.json` | Board interface |
| Schema `cad-skills/evidence` 1.0 | `contracts/schemas/evidence.schema.json` | Check evidence |
| Schema `cad-skills/export-settings` 1.0 | `contracts/schemas/export-settings.schema.json` | Export settings |
| Schema `cad-skills/manifest` 1.0 | `contracts/schemas/manifest.schema.json` | Package manifest |
| Schema `cad-skills/part` 1.0 | `contracts/schemas/part.schema.json` | Part record |
| Schema `cad-skills/supplier-profile` 1.0 | `contracts/schemas/supplier-profile.schema.json` | Supplier profile |
| Schema `cad-skills/toolchain-lock` 1.0 | `contracts/schemas/toolchain-lock.schema.json` | Toolchain lock |
| Schema `cad-skills/variants` 1.0 | `contracts/schemas/variants.schema.json` | Variants |
| Schema `cad-skills/waivers` 1.0 | `contracts/schemas/waivers.schema.json` | Waivers |
| Registry | `contracts/schemas/registry.json` | Maps each schema ID and version to its file |
| `cad-skills/part-map` 1.0 | `skills/pcba-design/contracts/part-map.schema.json` | Skill-owned map schema, outside the shared registry, loaded directly by the skill and listed in the copy record |
| `contracts/README.md` | `contracts/README.md` | Copy set record |
| `scripts/project_io.py` | `skills/pcb-design/scripts/project_io.py` | Confined paths and project lock |
| `scripts/sexp.py` | `skills/pcb-design/scripts/sexp.py` | KiCad board parsing |

Copied from `pcb-design`: only `scripts/project_io.py` and `scripts/sexp.py`, as listed above. Not copied: `pcb.py` and the remaining `pcb-design` modules. The skill needs no B1 to B6 export code beyond its own export configuration.

## 2a. Bound inputs

Each input has a path and a SHA-256 hash in the manifest. Each role uses an existing manifest role.

| Input | Role | Source |
|---|---|---|
| KiCad board | `board` | Project board file |
| Board record | `board_record` | Project board record |
| Schematic | `schematic` | Circuit schematic of the project. Path set by the board record, confined to the project |
| Export settings | `export_settings` | Export settings record. Path set by the board record, confined to the project |
| Toolchain lock | `toolchain` | Toolchain lock record. Path set by the board record, confined to the project |
| Board interface | `board_interface` | Board interface record. Path set by the board record, confined to the project |
| Supplier rules | `supplier_rules` | Supplier rule record for `fab.supplier_rules`. Path set by the supplier profile, confined to the project |
| Supplier settings | `supplier_settings` | Supplier settings record for `fab.supplier_rules`. Path set by the supplier profile, confined to the project |
| Waivers | `waivers` | Included only when the package uses waivers. Path set by the board record, confined to the project |
| Component map | `parts` | `components/parts-map.yaml`, skill-owned, schema `cad-skills/part-map` 1.0. The skill validates the map itself. The shared validator binds only its bytes (section 4) |
| Selected part records | `parts` | `components/*.yaml`, confined paths |
| Variant record | `variants` | `variants.yaml`, sole population owner |
| Stock policy | `board.yaml.extensions.pcba.stock` | Explicit field (section 8) |
| Supplier profile | `supplier_profile` | `manufacturing/supplier.yaml`. Both commands compare `content_sha256` with `board.supplier.profile_sha256`. Input bindings retain the full file hash |
| Placement convention | `supplier_settings` | Declared status fields (section 9) |
| Board image | `image` output | One image file |

## 3. Command sequence

Before implementation, measure the KiCad placement behavior (Pi point 3a):

0. Run `kicad-cli pcb export pos` in the accepted local image (no pull) with `--format csv --units mm` and both sides. Use a fixture with an offset footprint origin and a bottom-side part. Record the exact origin and rotation in an evidence file. This measures KiCad output only. It does not resolve the Sierra convention.

Measured KiCad transform (Pi review, accepted image `localhost/cad-skills-pcb:b6`, `--pull=never`, no network). Fixture expectations are written by hand from this transform:

- `X_export = X_board`
- `Y_export = -Y_board`
- `Rotation_export = ((Rotation_board + 180) mod 360) - 180`
- The side does not change the transform. A bottom-side part is not mirrored.
- The drill-file origin option does not change top-side values.

This transform describes the KiCad exporter only. It is not a Sierra convention.

Source project to Sierra candidate package:

1. `uv run skills/pcba-design/scripts/pcba.py export` runs the local KiCad image (no pull) with the fabrication and drill settings of section 9. It writes outputs into a new empty package directory.
2. `uv run skills/pcba-design/scripts/pcba.py neutral` reads the board, the component map, the parts, and `variants.yaml`. It writes `assembly-neutral.json`. It stops on any join error (section 4).
3. `uv run skills/pcba-design/scripts/pcba.py sierra` reads `assembly-neutral.json` and the Sierra profile. It writes the BOM workbook, the XY draft, the assembly drawing marks, and the test record.
4. `uv run skills/pcba-design/scripts/pcba.py package` writes `manifest.yaml`. It binds every input and output by hash and sets the exit status (section 10).
5. `uv run skills/pcba-design/scripts/pcba.py check` validates the package with the copied validator.

No step reads the current time. The stock check takes an explicit `--as-of YYYY-MM-DD` date.

## 4. Reference mapping

Each reference of a declared variant has one population state: `populate`, `dnp`, or `exclude_from_assembly`.

- Decided by the lead (R7 closed): the map is the skill-owned file `components/parts-map.yaml`. Its schema is `cad-skills/part-map` version `1.0`. It is outside the shared registry and strict: unknown keys fail. The skill's `neutral` and `check` steps validate the map against `cad-skills/part-map` 1.0. The shared validator reads `parts` only as bytes and cannot enforce map rules. The skill loads its own map schema directly. It is bound as a `parts` input, and each referenced part file is also a `parts` input.
- The map maps each populated or DNP board reference to one part file. Mechanical-reference exclusions are listed explicitly in the map. Implicit exclusions are rejected.
- A map value is a confined relative path below `components/`. Reject absolute paths, `..`, and symlinks that leave `components/`.
- The part schema has no reference field. Do not add one.
- The map covers all declared variants. A map entry is valid when some declared variant uses its reference. Do not reject a valid entry only because another variant uses it or because the selected variant does not.
- Reject:
  - a board reference that a declared variant uses and that has no map entry. This includes a mechanical exclusion. A mechanical exclusion needs an explicit map entry with `mechanical: true` and no part path. No exception applies to a missing entry.
  - a map entry whose reference is not on the board;
  - a map entry whose reference no declared variant uses;
  - a duplicate map key.
- Do not infer a join from file names, MPNs, or footprint names.
- A part path is confined by its resolved real path. The resolved file must lie inside the components directory, so a link that leaves it is refused (`map.path_escape`). Each resolved file has one snapshot.
- An exclusion needs an explicit map entry. Do not infer an exclusion from a footprint name.

## 5. Variant semantics

`variants.yaml` is the sole owner of population state. Part records carry no DNP field.

- `populate`: the reference enters the BOM, placement, and drawing as populated. Its part record is required.
- `dnp`: the reference enters the BOM as a DNI row and the drawing as DNP. It is absent from placement. Its part record is required.
- `exclude_from_assembly`: the reference is absent from BOM, placement, and drawing. Its part record may be omitted only with an explicit map entry marked `mechanical: true`. Footprint names never decide this.
- `hand_installed` (list of reference and reason), decided by the lead:
  - the reference must have state `populate` in `references`. Otherwise reject.
  - A populated hand-installed reference counts in the neutral per-board BOM and in test coverage.
  - It appears on the assembly drawing and in the hand-install instructions.
  - It stays out of automatic placement (no XY row).
  - Its supplier BOM treatment follows the explicit service policy (section 9.1). An unknown policy blocks qualification, not neutral output. Do not invent customer-supplied or supplier-procured treatment.
- Stop on a missing or duplicate reference, a missing MPN, a footprint mismatch, or a quantity disagreement. The shared validator does not enforce these variant rules. The skill's `neutral` step enforces them.

## 6. Neutral rows

`assembly-neutral.json` holds one row for each reference of the selected variant. Fields:

- `reference`
- `variant_state`: exactly one of the three `variants.yaml` states: `populate`, `dnp`, `exclude_from_assembly`
- `installation_method`: `automatic` or `hand_installed`. Set from the `hand_installed` list. A `hand_installed` reference keeps `variant_state` `populate`.
- `source_rotation_deg`: the board-file rotation, unchanged. The pos-export value is not stored in neutral rows. It appears only in the separate comparison evidence as `export_rotation_deg`.
- `rotation_deg` = `((source_rotation_deg mod 360) + 360) mod 360`. A source value of `360` gives `0`. A source value of `-90` gives `270`. Both values are kept.
- `part_path`: the resolved project-relative path that the inputs record names. It is the same value as the input record. `part_sha256` is the hash of that one snapshot.
- `manufacturer`, `mpn`, `footprint`, `value`
- `selected_alternate`: empty string, because alternates are not supported in this batch (section 7).
- `board_quantity`: the number of boards in the order
- `per_board_quantity`: 1 for each `populate` or `dnp` row. It is 0 for each `exclude_from_assembly` row. Excluded rows never count toward supplier quantities.
- `side`: `top` or `bottom`
- `source_tokens`: the raw token strings `x`, `y` and `angle` from the board file. `angle` is null when the file has no angle token.
- `angle_source`: `token` when the file has an angle token, or `implicit_zero` when it has none. An implicit angle gives `source_rotation_deg` 0.0.
- `x_mm`, `y_mm`, `source_rotation_deg`: numbers derived from `source_tokens` with the float conversion. They are finite values, not exact decimal values. A malformed or non-finite token refuses the run with one named finding and no traceback. The `pos` export comparison is a separate measured check. It never replaces these values.
- `datum`: `kicad_footprint_origin`
- `board_quantity`: the board quantity, on each row.
- `assembly_instruction`: the `hand_installed` reason, copied exactly. It is an empty string on automatic rows. The reason is not a shared schema field.
- `midpoint_mapping`: `unconfirmed` unless an explicit per-footprint mapping has evidence.
- `midpoint_estimate_mm`: an optional anchor-to-midpoint estimate derived from footprint geometry (Pi point 3b, review point R6). It is always `unconfirmed`. Geometry does not establish the supplier's requested midpoint. The estimate can be applied in a draft output only. It cannot qualify placement. It is never a universal offset. It never enters the Sierra XY column. The Sierra XY draft carries the KiCad footprint position with `midpoint_mapping: unconfirmed`. The estimate appears only in a separate draft field or draft output.
- Neutral exclusion row: an explicitly excluded mechanical reference, with an explicit map entry (`mechanical: true`) and no part record, has a row with `variant_state` `exclude_from_assembly`, `part_path` empty, `installation_method` `automatic`, and `reason` `mechanical`. The row exists only in neutral data. No supplier output uses it.
- Stock order quantity: `order_quantity = per_board_quantity * board_quantity`, stored in a separate field.

A populated `hand_installed` row has these exact values: `variant_state` `populate`, `installation_method` `hand_installed`, `per_board_quantity` 1. It is in the neutral BOM group and the test reference list. It is absent from automatic placement rows. It is never grouped with a DNP row.

Derivations use these rows only:

- BOM: group by manufacturer, MPN, population state, `installation_method`, and `assembly_instruction`. Split populated and DNP references into separate rows.
- Placement: rows with `variant_state` `populate` and `installation_method` `automatic` only. A `hand_installed` row is excluded from automatic placement even when its state is `populate`. Unit and convention fields come from section 9.
- DNP drawing marks: rows with state `dnp`.
- Test references: all rows, with `hand_installed` rows as manual steps.

## 7. Alternates

- An alternate is a separate part file named in the component map or an explicit `alternates` list. It is never chosen by a name match.
- It must pass the same electrical, footprint, polarity, process, and evidence checks as the primary part.
- Stock demand is aggregated for each part across all populated references. Board quantity and per-board quantity stay separate fields.

## 8. Stock policy

- Field `board.yaml.extensions.pcba.stock.max_age_days`: a positive integer, or the explicit text `no_age_limit`. No shared schema change.
- A missing field is an error. The package cannot be made without a stock policy choice.
- Comparison: `as_of_date - retrieved_date` in days. Stale when the value is above `max_age_days`. Not evaluated when `no_age_limit` is set.
- Stock below assembly demand blocks the qualified stock claim. Stock data is a dated observation, not a reservation.
- Unknown lifecycle or stock blocks the qualified claim.
- Conflicting stock or lifecycle records for one manufacturer and MPN refuse the run (`stock.conflicting_records`). Identical repeated records share one stock result. Demand counts each populated reference once, and repeated stock quantities are never added.

## 9. Sierra adapter

### 9.1 BOM

- Header strings are exact, copied from the sample. They include two spaces in `Size / Footprint  (optional)` and the spelling `Manfacturer (optional)`.
- Retention action before implementation: the sample `/tmp/cad-skills-sierra-bom.xls` is not in the repository. Copy it to `docs/reviews/sierra-source-evidence/` with its hash, and bind the header fixture to that copy.
- Supplier policy field `supplier_profile.extensions.pcba.hand_installed_bom` (not a top-level key; the supplier profile schema forbids one): explicit values `include_in_bom` or `exclude_from_bom`. A missing or unknown value blocks qualification. Neutral output is still generated. No shared schema change.
- DNI follows the sample row note. The whole row is DNI. A DNP row carries the sample's `DNI` value in `Do Not Install`. A populated row leaves it blank. A guessed `DNP` label fails.
- `Quantity per board` is the count of references in the row.
- The order quantity is not used in the BOM.
- Optional fields are filled only from known part data. Unknown fields stay blank.
- Output is a workbook, not a renamed CSV.

### 9.2 Placement (PDF sample, named candidate)

- Columns: designator, footprint, midpoint X, midpoint Y, side, rotation. Side values: `T` and `B`. Units: mil.
- Conversion: neutral mm to mil with the exact factor 0.0254 mm per mil. No cumulative rounding.
- The sample states mil units. This is the sample's stated unit, not supplier confirmation of its coordinate convention. Record it as `stated_by_sample`.
- Status fields, all `unconfirmed` for Sierra: units confirmation, origin, axes, side view, rotation direction, zero orientation, midpoint mapping.
- The file is a draft. Unconfirmed conventions block qualification.
- A rotation of `360` is normalized to `0` in `rotation_deg`. The source value stays in `source_rotation_deg`. This is a review point R2.
- Reject duplicate placement references.
- No supplier example row is an oracle. Expected values come from independent fixtures (section 11).
- Do not copy the KiCad `pos` file.

### 9.3 Fabrication

- Settings from the Turnkey PRO FAQ: inch RS-274X Gerber, Excellon absolute inch drill, trailing-zero suppression, 2.4 format, separate plated and non-plated drill files.
- The supplier Gerber fabrication drawing is one output (role `fabrication_drawing`, Gerber file). The local PDF documentation is a separate output (role `report`).
- Plane interpretation: `unconfirmed`. It is a release condition.
- Do not reuse the OSH Park positive-plane rule.
- One board image. No array. The assembly drawing notes that Sierra arrays the boards.

### 9.4 Service condition

- Record service `turnkey_pro`, the fabrication location and assembly location as `unconfirmed` until service-specific evidence (URL, retrieval date, reviewer) is recorded.
- ITAR and export-controlled exclusion is checked against `board_record` restrictions. Unknown applicability stays open.

## 10. Manifest and exit states

- `kind: pcba`.
- Exit states, from the lowest:
  - `draft`: outputs generated but not yet validated by `check`.
  - `unqualified`: outputs validated, but a qualification condition is open. An `unconfirmed` convention gives this status (Pi point 3b). This changes my earlier draft rule.
  - `qualified`: all conditions met and all supplier conventions confirmed with evidence.
- `unconfirmed` is used only for a condition or finding, never as a status.
- An `unqualified` package makes no unsupported success claim. Every listed artifact is structurally valid and hash-bound. The five `asm` checks are present with truthful evidence status from the existing enum: `pass`, `fail`, `pending`, or `unconfirmed`. No check is forced to `pass`. Package status stays one of `draft`, `unqualified`, `qualified`. No schema value is added.
- Check IDs: `asm.bom_consistent`, `asm.placement_rotation`, `asm.variant_agreement`, `asm.stock_dated`, `asm.test_record`. These exist in `contracts/validate.py`. Each check writes one evidence file. The `asm.placement_rotation` artifact is the neutral placement dataset.
- Recompute derived outputs in dependency order. Refuse a stale result. A variant, part, or board change marks dependent outputs stale.
- Qualified requires: confirmed placement conventions, resolved plane interpretation, service evidence, stock policy decision and passing stock check, and all required roles and checks.
- Firmware instructions are required only when the board record declares firmware. Do not invent firmware.
- Electrical test steps carry executable checks and limits. The test record states `not measured`. It never claims a physical pass.

## 11. Acceptance cases (first set)

| ID | Case | Expected result |
|---|---|---|
| AC-01 | Two variants | BOM quantity, placement inclusion, and DNP marks follow the selected variant from the same rows |
| AC-02 | `populate`, `dnp`, `exclude_from_assembly` in one set | DNP absent from placement; DNP in the DNI row; excluded mechanical reference appears only in neutral data, not in any supplier output |
| AC-03 | Missing mapping, duplicate reference, missing MPN, footprint mismatch, quantity conflict | Each stops generation with a named error |
| AC-04 | Variant change after output | Manifest inputs stale; qualification fails |
| AC-05 | Part or board reference change after manifest | Hash check detects it |
| AC-06 | Stock below demand; stale date under explicit max age; unknown lifecycle; `no_age_limit` | Each blocks or passes exactly as section 8 states |
| AC-07 | Top and bottom asymmetric polarized parts at 0, 90, 180, 270 | Neutral placement matches independent fixture expectations; no universal offset |
| AC-08 | Offset-origin board fixture | Output keeps board datum; no origin-to-midpoint assumption without a mapping |
| AC-09 | Exact-header Sierra BOM fixture | Header bytes unchanged; DNI from the row note only |
| AC-10 | Unconfirmed Sierra origin and rotation | The XY file remains a draft. Package validation then sets manifest status to `unqualified`. Qualification refused. |
| AC-11 | Remove each required output role or check in turn | Validator rejects qualified status |
| AC-12 | Alternate part | Same checks as primary; fails on footprint, polarity, or evidence mismatch |
| AC-13 | Populated `hand_installed` reference | Counted in neutral per-board BOM and test coverage; on drawing and hand-install instructions; no XY row |
| AC-21 | Map path outside `components/`, `..`, or symlink escape | Rejected |
| AC-22 | Map with unknown key or wrong schema version | Rejected (strict `cad-skills/part-map` 1.0) |
| AC-23 | `hand_installed` reference with state `dnp` or `exclude_from_assembly` | Rejected |
| AC-24 | Unknown `hand_installed_bom` service policy | Neutral output generated; qualification blocked |
| AC-25 | Mechanical exclusion without an explicit map entry | Rejected. No exception and no implicit exclusion. |
| AC-14 | Rotation 360 in sample | `rotation_deg` is 0; `source_rotation_deg` stays 360 |
| AC-26 | Midpoint estimate present, Sierra mapping unconfirmed | Draft output only; placement cannot qualify |
| AC-27 | Populated `hand_installed` reference | `variant_state` stays `populate`; `installation_method` is `hand_installed`; no automatic placement row |
| AC-28 | Excluded mechanical reference without part record | Neutral exclusion row present; no supplier row |
| AC-15 | One board image | Package has one image; arrayed input fails |
| AC-16 | Sierra Gerber and local PDF | Distinct outputs with distinct roles |
| AC-17 | Plane interpretation | Stays unconfirmed; release condition in manifest |
| AC-18 | ITAR-flagged restriction | Turnkey PRO selection blocked |
| AC-19 | Profile hash change | Qualification repeats; old package keeps its hashes |
| AC-20 | Drill export of the probe board | Exit 0; coordinates compared with independent inventory, including trailing zeros, negatives, and plating |

Each fixture is independent. Expected coordinates are written by hand from the fixture definition. They are not computed by the adapter under test.

## 12. Review points

- R1: Closed. A `hand_installed` reference must have state `populate` in `references`. Otherwise it is rejected.
- R2: Closed. Rotation `360` becomes `0` in `rotation_deg`. The source value stays in `source_rotation_deg`.
- R3: Are the BOM headers and the DNI value correct against the sample file? Proposed: retain the sample and bind a fixture before implementation.
- R4: Is a `draft` XY file with `unconfirmed` conventions acceptable as an output? Proposed: yes, with no qualification.
- R5: Tests in `tests/test_pcba_design.py` with fixtures in `tests/fixtures/pcba-design/`. Shared-file changes stay with the lead.
- R6: Is a geometry-derived `midpoint_estimate_mm`, always `unconfirmed` and unable to qualify placement, acceptable? Proposed: yes, for draft output only (Codex point 4).
- R7: closed by the lead. The map is `components/parts-map.yaml` (`cad-skills/part-map` 1.0, skill-owned).
- R8: closed by the lead. `hand_installed` counts in neutral BOM and test coverage, stays out of placement, and follows the explicit supplier policy `hand_installed_bom`.
- R9: Bounded start. Core B9 neutral mapping, variants, BOM and stock work (sections 4 to 8) starts only after Codex and Pi explicitly agree to this bounded interface and the helper correction. B10 publication (section 14) stays outside that start until its inherited gate is concrete and reviewed.
- Tests and fixtures establish implementation behavior only. Coordinate conventions stay unconfirmed until authoritative evidence exists.

## 14. B10 inherited gate

Qualified PCBA inherits every `BARE_CHECKS` entry in `contracts/validate.py`, then adds the five `asm.*` checks. A qualified package needs 13 checks. Each check needs status `pass`, one evidence file, and every mandatory input role in the table below. This interface does not implement only the five `asm` checks.

| Check | Mandatory input roles | Owned code (`skills/pcba-design/scripts/`) | Independent check |
|---|---|---|---|
| `design.erc` | `schematic` | `checks_design.py`: runs local `kicad-cli sch erc` (no pull), captures JSON bytes | Seeded fixture with one known violation must fail |
| `design.drc` | `board` | `checks_design.py`: runs local `kicad-cli pcb drc`, captures JSON bytes | Seeded fixture with one known clearance violation must fail |
| `design.parity` | `schematic`, `board` | `checks_design.py`: compares netlists exported from schematic and board | Seeded fixture with one mismatched pad must fail |
| `fab.profile_evidence` | `supplier_profile` | `checks_fab.py`: byte hash of retained supplier evidence | Changed byte in evidence must fail |
| `fab.export_inventory` | `board`, `export_settings` | `checks_fab.py`: compares written file set with export settings | Missing and extra file fixtures must fail |
| `fab.layer_order` | `board`, `export_settings` | `checks_fab.py`: reads Gerber layer function from file content, not from file name | Renamed-but-correct file passes; wrong layer content fails |
| `fab.drill_split` | `board`, `board_interface`, `export_settings` | `checks_fab.py`: Excellon header and coordinate check against independent hole inventory | Trailing-zero, negative, multiplicity and plating fixtures |
| `fab.supplier_rules` | `board`, `supplier_profile`, `export_settings`, `supplier_rules`, `supplier_settings`, `toolchain` | `checks_fab.py`: applies Sierra rules from the profile | Cannot pass while the plane interpretation or XY convention is `unconfirmed` (AC-17) |
| `asm.bom_consistent` | `parts`, `variants`, `board_record`, `supplier_profile` | `checks_asm.py` | AC-01 to AC-05 |
| `asm.placement_rotation` | `board`, `parts`, `variants` | `checks_asm.py` | AC-07, AC-08 |
| `asm.variant_agreement` | `board_record`, `variants`, `parts` | `checks_asm.py` | AC-01, AC-02, AC-04 |
| `asm.stock_dated` | `parts`, `board_record` | `checks_asm.py` | AC-06 |
| `asm.test_record` | `board`, `parts`, `variants`, `board_record` | `checks_asm.py` | Record consistency only. No physical pass is created. |

Owned code for all checks:

- `export.py`: runs local `kicad-cli` only. It writes outputs into a new empty package directory with temporary files and `os.replace`. It captures bytes and hashes them at capture time.
- `report.py`: writes the manifest and one evidence file per check. Evidence files record inputs, the artifact, the tool, and no clock value. The caller supplies `observed_on`.
- `checks_*.py`: rule validation, as listed above.
- `project_io.py` (copied): project lock, confined paths.
- Final freshness: before publication, the tool rehashes every input. It refuses to publish when a hash differs from the captured bytes.

B10 capture and publication rule (Codex follow-up):

1. Capture every input once, as bytes, and hash those bytes.
2. Derive all outputs and evidence only from the captured bytes. Do not reread a project file after capture.
3. Hold the project lock from capture through staged validation and final freshness.
4. Stage every output in a temporary directory inside the package. Validate the staged set.
5. Publish atomically with `os.replace` inside confined package paths. Preserve prior packages.
6. Release the lock after publication or refusal.

`checks_fab.py` reads the bound captured bytes of `supplier_rules`, `supplier_settings`, `supplier_profile`, `export_settings`, and `toolchain`. It never reads a live project path during checks.

Qualified status also needs: service evidence with URL, retrieval date and reviewer (section 9.4); a confirmed placement convention with evidence; a resolved plane interpretation; and a stock policy decision (section 8). Unknown supplier conditions keep the package `unqualified`. B10 qualification also inherits all bare-board checks (section 14).

Without a physical trial, no package claims a measured pass. The test record states `not measured`.

## 13. Open items

- Sierra placement origin, axes, side view, rotation direction, zero orientation, and units remain unconfirmed. No supplier contact is allowed to resolve them.
- Plane interpretation for the current exporter remains unconfirmed.
- In-house evidence for MacroFab and Ninja remains absent. Their profiles stay provisional.
