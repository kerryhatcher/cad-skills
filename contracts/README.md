# Record contracts

This directory holds the development sources of the record contracts. It is not a skill. Each installed skill later gets its own copy of the files listed below. A skill must not read this directory at run time.

Copy set: `registry.json`, each schema file that the registry names, and this file.

## Records

| Schema ID | File | Content |
|---|---|---|
| `cad-skills/board` | `board.schema.json` | Board name, circuit source, supplier, quantity, limits, dimensions |
| `cad-skills/variants` | `variants.schema.json` | Variants and the population state of each reference |
| `cad-skills/part` | `part.schema.json` | Part data, lifecycle and stock |
| `cad-skills/supplier-profile` | `supplier-profile.schema.json` | Supplier limits with evidence |

Each record has `schema_id` and `schema_version`. The version is a string of the form `MAJOR.MINOR`. The registry lists each supported version with its schema file. The validator uses the schema for the exact version of the record.

## Validate

```bash
uv run contracts/validate.py [--json] [--schemas DIR] FILE [FILE ...]
```

Exit codes, with the highest priority first:

| Code | Cause |
|---:|---|
| 3 | Invalid registry, missing or invalid schema, or validator failure |
| 2 | Incorrect arguments, missing input file, or missing schema directory |
| 1 | Unreadable file, parse error, or invalid record |
| 0 | All records pass |

With `--json`, the tool writes one JSON report to standard output. The report has no time and no random value. A file that the tool did not process is in `unprocessed`. It is never a pass.

## Accepted data

The loader accepts JSON-compatible data only. It rejects these items:

- A duplicate key at any depth (`file.duplicate_key`).
- A key that is not a string.
- A YAML merge key, a recursive alias, a timestamp tag, and any other tag.
- A number that is not finite, such as `.nan`, `.inf`, or `1e999`.

A plain scalar has no tag. The loader reads a plain scalar with the JSON grammar:

- A plain date such as `2026-11-13` stays a string.
- The text `yes`, `no`, `on` and `off` stays a string.
- Text that only looks like a number, such as `0o17` or `1_000`, stays a string.

An explicit tag such as `!!int`, `!!float`, `!!bool`, `!!str` or `!!null` selects the YAML lexical form of the tag. For example, `!!bool yes` is `true`, and `!!int 0x10` is `16`. A value that the tag does not accept, such as `!!int bad`, is a parse error (`file.parse_error`). The validator rejects an explicit `!!timestamp` tag and every other tag.

A decimal number that is too small for a binary float becomes `0.0`. This is underflow. The validator does not reject it. Write a value that a binary float can hold.

Put a hash in quotes in YAML. A hash that has only digits, or digits and one `e`, is a number if it has no quotes. The validator then rejects it.

An identifier field and a key of a named map cannot hold a control character. The rejected characters are U+0000 to U+001F (this includes a tab, a line feed and a carriage return) and U+007F. Identifier fields are names, IDs, revisions, MPNs, packages, symbols, footprints, units, services, references, and similar short labels. Named maps are `pin_map`, `ratings`, `electrical_limits`, `limits`, and the `references` of a variant. The validator accepts a normal space and any Unicode letter. The validator does not normalize Unicode.

Prose fields can hold line breaks. They are `restrictions` (`text` and `source`), `hand_installed` `reason`, the `stock` `source`, the text `value` of a limit, and the content of `extensions`.

Each fixed-format string (version, hash, date) must match its whole value. A final newline is not accepted. A URL has no space character.

## Hashes

The validator calculates the content hash of a record in these steps:

1. Copy the record and remove only the root field `content_sha256`.
2. Make sure that the copy has JSON-compatible data only. The function rejects a non-string key, a tuple, a set, bytes, a date, a number that is not finite, and a cycle (`file.not_json_compatible`).
3. Encode it with `json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)`.
4. Encode the text as UTF-8 with no byte-order mark and no final newline.
5. Calculate the SHA-256 of the bytes. Write it as lowercase hexadecimal text.

The hash has these properties:

- `1` and `1.0` give different hashes.
- `-0.0` and `0.0` give different hashes.
- Text in NFC and NFD form gives different hashes.
- Key order and comments do not change the hash.
- The hash of an input file covers the exact bytes of the file. It is a different value.
- `evidence_sha256` identifies the exact bytes that the project retrieved. It does not show that the source is authentic.

## Rules

- The schema checks structure and types. The validator checks the relation between fields. A defect gives one finding.
- `minimum` and `maximum` limits have a numeric value and a `unit`. A text value is only for a `recommendation`. A text limit omits `unit`. The validator rejects an empty `unit`.
- Each supplier limit has a `scope`. The value `fabrication` is for a bare-board limit. The value `assembly` is for an assembly limit. The value `margin` is for a project margin. A consumer selects the limits for its package from `scope`. The field `division` shows where the project enforces a limit. It does not show the scope.
- `variants.yaml` is the only owner of assembly variants and DNP data. A part record does not repeat them. The check that the selected variant exists is in B2. The check that each variant covers each component reference is in B9.
- `extensions` holds data that does not affect manufacturing. It cannot replace a mandatory field.
- The validator redefines the JSON Schema types `integer` and `number`. An integer is not a boolean and not `1.0`. A number is finite and is not a boolean.

## Records for a project and a package

| Schema ID | File | Content |
|---|---|---|
| `cad-skills/waivers` | `waivers.schema.json` | Review decisions for ERC and DRC findings |
| `cad-skills/manifest` | `manifest.schema.json` | The inputs, outputs, checks and status of one package |
| `cad-skills/evidence` | `evidence.schema.json` | The result of one check, with its inputs and one artifact |
| `cad-skills/board-interface` | `board-interface.schema.json` | Board geometry for an enclosure |
| `cad-skills/toolchain-lock` | `toolchain-lock.schema.json` | Exact tool versions, libraries and licenses |
| `cad-skills/export-settings` | `export-settings.schema.json` | Gerber and drill settings and the layer map |

A project has these files:

| Role | Path |
|---|---|
| `board_record` | `${PROJECT}/board.yaml` |
| `board` | `${PROJECT}/kicad/board.kicad_pcb` |
| `schematic` | `${PROJECT}/kicad/board.kicad_sch` |
| `variants` | `${PROJECT}/variants.yaml` |
| `supplier_profile` | `${PROJECT}/manufacturing/supplier.yaml` |
| `export_settings` | `${PROJECT}/manufacturing/export.yaml` |
| `toolchain` | `${PROJECT}/toolchain.lock.json` |
| `board_interface` | `${PROJECT}/mechanical/board-interface.json` |
| `waivers` | `${PROJECT}/manufacturing/waivers.yaml` (optional) |

## Validate a project and a package

```bash
uv run contracts/validate.py [--json] [--schemas DIR] [--project DIR] [--package DIR] [FILE ...]
```

- `--project DIR` examines each record of the project and the relations between them. It reads the PCB and the schematic as bytes only.
- `--package DIR` needs `--project DIR`. It examines `${PACKAGE}/manifest.json`, each evidence file, and the output files.
- A record that has a defect gives no secondary cross-file finding.
- A missing necessary file gives `cli.input_missing` and exit 2.

The hash `board_sha256` is the SHA-256 of the bytes of `${PROJECT}/kicad/board.kicad_pcb`. The records of the board, the PCB and the schematic have separate hashes and separate finding codes. A change of `board.yaml` alone does not change `board_sha256`. A change of the PCB makes every waiver, the interface and the manifest stale.

Every hash in a manifest, an interface, a waiver, or an evidence file covers the exact bytes of one file. The only canonical hash is `content_sha256` of a supplier profile.

## Coordinate convention

All lengths are in millimeters. Board coordinates are right-handed. Seen from the top side, +X is right and +Y is up. +Z points from the bottom surface to the top surface. Angles are in degrees, counter-clockwise when seen from +Z. The board record must have `x_axis: right`, `y_axis: up` and `units: mm`. The interface origin `origin_mm` is a point in board coordinates. A consumer subtracts it to get interface coordinates. The top height limit starts at the top surface. The bottom height limit starts at the bottom surface. `geometry_tolerance_mm` is the largest distance between an arc and its polygon. The checks compare dimensions within this value.

## Qualification

The completeness rules apply to a package with the status `qualified` only. These are the necessary input roles, the required outputs and layers, the drill applicability items, and the required checks. A `draft` or `unqualified` package can omit them. In all states, the validator examines each item that the manifest lists: structure, path, hash, size, layer mapping, suffix, and evidence.

A qualified package has all of these:

- every necessary input role, with the right path and hash
- every required output role and layer, with a non-empty file, the right suffix, and the right hash
- a `drill_applicability` item (a reason and evidence) for each omitted drill role
- every required check with the status `pass`, and one evidence file for each check

An evidence file for a passed check has `inputs` and one `artifact`. The inputs must include every manifest input with the roles in this table. The artifact is a manifest output.

| Check ID | Mandatory input roles |
|---|---|
| `design.erc` | `schematic` |
| `design.drc` | `board` |
| `design.parity` | `schematic`, `board` |
| `fab.profile_evidence` | `supplier_profile` |
| `fab.export_inventory` | `board`, `export_settings` |
| `fab.layer_order` | `board`, `export_settings` |
| `fab.drill_split` | `board`, `board_interface`, `export_settings` |
| `fab.supplier_rules` | `board`, `supplier_profile`, `export_settings`, `supplier_rules`, `supplier_settings`, `toolchain` |
| `asm.bom_consistent` | `parts`, `variants`, `board_record` |
| `asm.placement_rotation` | `board`, `parts`, `variants` |
| `asm.variant_agreement` | `board_record`, `variants`, `parts` |
| `asm.stock_dated` | `parts`, `board_record` |
| `asm.test_record` | `board`, `parts`, `variants` |

A manual record also has a `reviewer` and a date `observed_on`. A tool record has a `tool` and no mandatory reviewer. The date is an input that the caller supplies. The validator never reads the clock. For `fab.profile_evidence`, the artifact is a packaged file with the hash of the supplier profile `evidence_sha256`. A byte match shows identity of the retrieved bytes. It does not show authenticity or current supplier acceptance.

This is a check of qualification-record consistency. It does not show that a tool ran, that a circuit works, or that a board works.
