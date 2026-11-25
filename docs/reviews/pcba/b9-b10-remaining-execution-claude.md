# B9/B10 remaining execution note (Claude)

Date: 2026-11-15 UTC. Author: claude-pcba-dev (w1P:p7). Source: `docs/reviews/b9-b10-interface-claude.md`, sections 7, 9 and 14.
Status: planning only. Nothing here is implemented. The items below wait for review and lead release.

## 1. Alternates (interface section 7)

Selection rule: an alternate is a separate part file named in the part map, under an explicit `alternates` list. It is never chosen by name match. The part map schema is strict, so `alternates` is not yet a valid key. Adding it is a schema change for a later release.

Neutral field: `selected_alternate` holds the alternate name, the identifier from section 6 item 2. It is an empty string when the primary part is used. The part path is in `part_path`, as section 6 item 3 defines.

Evidence checks, each compared with the primary part record. Any mismatch refuses the alternate:

| Check | Part record fields compared |
|---|---|
| Electrical | `ratings`, `temperature_range_c` |
| Footprint | `footprint` |
| Polarity | `polarity`, `pin_map` |
| Process | `package` |
| Evidence | `datasheet_url`, `datasheet_revision` must be present |

Stock demand for an alternate is counted against the alternate's own part record, once per populated reference.

**Functional substitution needs approval, not only matching records.** The datasheet URL and revision being present, and equal ratings, do not prove that two parts can replace each other. Two resistor values can share those fields. A substitution therefore needs an explicit approval record.

- File: `components/alternate-approvals.yaml`, under the components directory, so the same confinement applies. It is bound as a `parts` input.
- Schema: skill-owned `cad-skills/alternate-approval` version 1.0, outside the shared registry. The skill validates it. No shared schema changes.
- One entry holds: `reference`, `variant` (the variant id), `primary_part_path`, `primary_sha256`, `alternate_name`, `alternate_part_path`, `alternate_sha256`, `application_evidence` (a `source` URL or document name, a `retrieved` date, and a `statement` of the circuit check), `approved_by`, and `approved_on`.
- The hashes bind the approval to the exact bytes of both parts. The neutral step compares each hash with the captured snapshot. A changed part, or a changed reference or variant, makes the approval stale and refuses the alternate (`alternate.approval_stale`).
- The approval key is the reference, the variant and the alternate name together. A duplicate key, or two entries with the same key and different bytes or evidence, refuses the run (`alternate.approval_conflict`).
- An alternate with no matching approval refuses the run (`alternate.unapproved`).
- The primary part and the alternate must both pass the evidence checks above before an approval can be recorded.

## 2. Placement and export (interface sections 9 and 14)

Owned code, all inside `skills/pcba-design/scripts/`. None exists yet:

- `export.py`: runs the local KiCad image only. It captures bytes and writes staged output with atomic replacement.
- `report.py`: writes the manifest and one evidence file for each check. It records no clock value.
- `checks_design.py`: `design.erc`, `design.drc`, `design.parity`.
- `checks_fab.py`: `fab.profile_evidence`, `fab.export_inventory`, `fab.layer_order`, `fab.drill_split`, `fab.supplier_rules`. It reads only the captured input bytes.
- `checks_asm.py`: `asm.bom_consistent`, `asm.placement_rotation`, `asm.variant_agreement`, `asm.stock_dated`, `asm.test_record`.
- `package.py`: stages the package, runs the checks, validates the staged set, runs the final freshness rehash, and publishes. It owns the call order in section 6 item 6.
- `project_io.py`: already copied. Provides the lock, confinement and atomic writes.

Placement fields still to add: `export_rotation_deg` (from the separate pos-export comparison only) and the midpoint estimate. The midpoint estimate stays `unconfirmed` and never enters the Sierra XY column.

## 3. Sierra output artifacts (interface section 9)

Each artifact is a draft until the conventions and service evidence are confirmed.

| Artifact | Source | Status rule |
|---|---|---|
| BOM workbook | neutral BOM groups, exact Sierra header strings | the sample file must first be retained under `docs/reviews/sierra-source-evidence/` with its hash |
| XY placement draft | neutral positions, mil units, `T`/`B` side | origin, axes, side view, rotation direction and zero orientation stay `unconfirmed` |
| Fabrication Gerber drawing | Turnkey PRO FAQ settings | distinct from the local PDF documentation |
| Excellon drill files | inch, absolute, trailing-zero suppressed, 2.4 format | coordinate fidelity is checked against the independent hole inventory |
| Board image | one image | the service arrays the boards, so no array is produced |
| Assembly drawing and test record | neutral rows, hand-install instructions | the test record states `not measured` |
| Manifest | all artifacts, by hash | `draft`, `unqualified` or `qualified`, with no unsupported success claim |

The plane interpretation stays `unconfirmed` and blocks `fab.supplier_rules`.

## 4. Inherited bare-board gate (interface section 14)

A qualified PCBA package needs all eight bare-board checks and the five assembly checks. The thirteen checks each need `pass`, one evidence file, and their listed mandatory input roles.

Bare-board checks: `design.erc`, `design.drc`, `design.parity`, `fab.profile_evidence`, `fab.export_inventory`, `fab.layer_order`, `fab.drill_split`, `fab.supplier_rules`.

Evidence values are only `pass`, `fail`, `pending` or `unconfirmed`. A package without evidence stays `unqualified`.

## 5. Order of work after review

1. Retain the Sierra BOM sample and bind its header fixture.
2. Add `alternates` to the part map schema, then the alternate checks in section 1.
3. Add the placement fields, then the placement export after the convention evidence is confirmed.
4. Implement the owned checks and the manifest. Test each refusal and each `unconfirmed` path.

No step starts before the lead releases it. The shared snippet route stays an integration item.

## 6. Addendum: concrete interfaces (answers to the Pi review)

Each item fixes one choice. The accepted neutral design stays closed. `export_rotation_deg` stays in the separate comparison evidence.

1. **Alternate selection trigger.** The board record names the alternate for each reference, in `board.yaml` under `extensions.pcba.selected_alternates`. The value is a map from reference to alternate name. The map applies to every variant that uses the reference. Refuse an unknown reference, a reference that no variant uses, and an unknown alternate name (`alternate.unknown`). An empty map selects no alternate.
2. **Alternates map shape.** The part map schema version becomes `1.1`. The loader also accepts `1.0`, where `alternates` is absent. Each map entry may hold `alternates`, a list of objects. Each object has `name` (an identifier, unique within the entry) and `part` (a path under `components/`). A mechanical entry holds no `alternates`. Unknown keys still fail.
3. **Alternate identity.** When an alternate is selected, the row takes its `manufacturer`, `mpn`, `part_path` and `part_sha256`. The row keeps `selected_alternate` set to the alternate name. Unselected rows keep `selected_alternate` as an empty string. The BOM group key already contains `manufacturer` and `mpn`, so an alternate forms its own group. Demand counts each populated reference once, under the key of the part actually used.
4. **Sierra `hand_installed_bom`.** The field `supplier_profile.extensions.pcba.hand_installed_bom` takes one of two values. `include_in_bom` puts each `hand_installed` row into the Sierra BOM as a normal populated row. `exclude_from_bom` omits those rows from the BOM workbook, while the assembly drawing and the test record still list them. A missing or unknown value stops the Sierra BOM artifact. The manifest then binds no BOM, and the status is `unqualified`. Neutral output is still written.
5. **Manifest roles and paths.** Each package has its own root, `out/pcba/packages/<package-id>/`. The CLI option `--package-id` names it. The identifier matches `[a-z0-9][a-z0-9._-]*`, as the manifest `release_id` does. Each package id is used once. An existing destination is refused with `package.exists`, and prior packages are never changed. Paths below are relative to the package root.

   | Artifact | Role | Path |
   |---|---|---|
   | Sierra BOM workbook | `bom` | `bom/sierra-bom.xlsx` |
   | Sierra XY draft | `placement` | `placement/sierra-xy-draft.csv` |
   | Plated drill file | `drill_plated` | `drill/plated.drl` |
   | Non-plated drill file | `drill_nonplated` | `drill/nonplated.drl` |
   | Supplier Gerber fabrication drawing | `fabrication_drawing` | `fab/fabrication-drawing.gbr` |
   | Assembly drawing | `assembly_drawing` | `drawings/assembly.pdf` |
   | Test record | `test_record` | `test/test-record.json` |
   | Neutral dataset | `report` | `reports/assembly-neutral.json` |
   | Board image | `image` | `image/board.png` |
   | Evidence files, JSON only | `evidence` | `evidence/<check-id>.json` |
   | Retained supplier evidence, not JSON | `evidence` | `source-evidence/supplier-profile-evidence.bin` |

6. **Staged publication and final freshness.** The new module is `package.py`. It runs these steps in this order, all under the project lock taken in `main`:
   1. Capture each input once, through `Snapshots`.
   2. Write the neutral dataset and every output into a staging directory `out/pcba/.staging-<token>/`.
   3. Run the checks in `checks_*.py`. Each check reads the staged artifact it binds.
   4. Write one evidence file per check, and write the manifest.
   5. Validate the staged manifest and evidence with the copied validator.
   6. Rehash every captured input, and refuse on any change (`input.changed`).
   6a. Immediately before the rename, compare the staging directory with the validated set. Refuse these cases, each with one finding: `package.extra_file` for a file not in the validated set, `package.missing_file` for a validated file that is absent, `package.hash_mismatch` for any file whose SHA-256 differs from the validated value, `package.count_mismatch` when the file count differs, `package.manifest_mismatch` when the staged manifest bytes differ from the validated manifest bytes, and `package.link` for any symbolic link or any file with more than one hard link. This step alone is not enough. It works together with step 6, so an input change and a package change are both caught.
   7. Publish the staging directory with `project_io.publish_dir`, which renames it to `out/pcba/packages/<package-id>/`. An existing destination is refused before the rename, as `package.exists`.

   A failure before step 7 leaves no package. Step 6a runs before step 7, so a changed or extra file never reaches the rename. A refusal before the rename has status `refused`, as in the neutral step. A failure after the rename raises `PostRenameError`. It reports status `failure` with finding `package.renamed_then_failed`, and `output_replaced` true. For a new package, `output_replaced` means that the new package directory is visible. The message names the package directory and the cause.

7. **Evidence file naming and location.** `report.py` writes `evidence/<check-id>.json`, for example `evidence/asm.stock_dated.json`. The check ID keeps its dots. Every file in `evidence/` is a JSON evidence record for one check. Each record is validated by the copied validator, and its `inputs` list holds every manifest input that the check role table names. A non-JSON file never uses a check ID as its name. Retained source evidence that is not JSON goes under `source-evidence/`.
8. **Artifact per check.** The artifact for each check is the staged file it verifies:

   | Check | Artifact |
   |---|---|
   | `design.erc` | `reports/erc.json` |
   | `design.drc` | `reports/drc.json` |
   | `design.parity` | `reports/parity.json` |
   | `fab.profile_evidence` | `source-evidence/supplier-profile-evidence.bin`, the packaged copy whose hash equals `evidence_sha256` |
   | `fab.export_inventory` | `reports/export-inventory.json` |
   | `fab.layer_order` | `reports/layer-order.json` |
   | `fab.drill_split` | `reports/drill-split.json` |
   | `fab.supplier_rules` | `reports/supplier-rules.json` |
   | `asm.bom_consistent` | `bom/sierra-bom.xlsx` |
   | `asm.placement_rotation` | `reports/assembly-neutral.json` |
   | `asm.variant_agreement` | `reports/variant-agreement.json` |
   | `asm.stock_dated` | `reports/stock.json` |
   | `asm.test_record` | `test/test-record.json` |

These choices stay open for review. None is implemented yet.
