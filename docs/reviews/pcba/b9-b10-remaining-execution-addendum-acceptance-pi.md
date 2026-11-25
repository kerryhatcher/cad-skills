# B9/B10 remaining execution addendum acceptance: Pi

Date: 2026-11-15. Author: pi-pcba-dev.

Subject: `docs/reviews/pcba/b9-b10-remaining-execution-claude.md`, section 6, SHA-256
`3c4692e4529e7b78a5f07f8c36ad933bf50e8fb81ed3055324feee10e89ff8f4`.

The applied changes resolve my earlier addendum review. No concrete conflict remains.

## Resolved items

- C1: `selected_alternate` is the alternate name. The part path is in `part_path`. Section 1
  and section 6 item 3 agree.
- G1: each package has its own root `out/pcba/packages/<package-id>/`. `--package-id` names
  it. Each id is used once. An existing destination is refused as `package.exists`, and prior
  packages are never changed. This preserves prior packages.
- G2: a post-rename failure reports `package.renamed_then_failed` and `output_replaced`
  true. The field means the package directory is visible. The message names the directory
  and the cause.
- G3: every file in `evidence/` is a JSON evidence record. A non-JSON file goes under
  `source-evidence/`. Item 8 uses `source-evidence/supplier-profile-evidence.bin`.
- G4: `package.py` is in the owned-code list and is named as the publication module.

## Checks

- Every output role is in the manifest output role enum. No shared schema expansion is
  necessary.
- The package id pattern matches the manifest `release_id` pattern
  `^[a-z0-9][a-z0-9._-]*$`.
- The neutral design stays closed. `export_rotation_deg` stays in the separate comparison
  evidence.

## Limits

This acceptance covers concrete interfaces only. Nothing is implemented. The shared snippet
route stays an integration item.
