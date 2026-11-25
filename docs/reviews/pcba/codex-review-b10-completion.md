# Codex review: B10 completion batch

Date: 2026-11-15 UTC. Reviewer: codex-pcba-dev. Branch: `work/pcba`.

I checked all 42 file hashes in `b10-completion-claude.md`. All hashes match. I reviewed the batch against `b10-completion-scope-root.md` and interface section 14. I did not run tests. The author reports 77 focused tests passed and 7 of 8 package tests passed.

## Review result

The batch does not meet the frozen B10 scope. These findings apply to the listed bytes.

1. **Full package validation does not run.** `package.py` calls `validate_record` for evidence and the manifest. That call checks each record schema. It does not run the project and package checks in `validate.py`. The package can miss input hashes, required check IDs, evidence links, and package cross-checks. Run full validation on the staged package before publication.

2. **Required inputs and executable checks are missing.** The package captures no `schematic`, `export_settings`, `board_interface`, `toolchain`, `supplier_rules`, or `supplier_settings` input. `design.erc`, `design.parity`, and `fab.profile_evidence` always return `pending`. `fab.supplier_rules` always returns `unconfirmed`. The accepted interface requires executable checks when their inputs exist. Capture each required input and run its check.

3. **Export inventory and drill checks do not use independent data.** `package.py` builds the expected export list from files that KiCad returned. `export_inventory` does not compare that list with `export_settings`. It does not fail when `not_packaged` contains an extra file. `drill_split` checks only text in each drill header. It does not compare hole coordinates, counts, or plating with `board_interface`. Missing and extra exports can pass this inventory check. A drill file with incorrect hole data can pass the drill check.

4. **Input freshness runs before staging.** `snap.check_unchanged()` runs before the staged writes. It does not run again after staged validation and before `publish_dir`. A source input can change during staging and still reach publication. Repeat the freshness check after `_verify_staged` and immediately before publication.

5. **The toolchain and export settings are not bound.** `export.py` uses the mutable image tag `localhost/cad-skills-pcb:b6`. It does not read a toolchain lock or export settings. The manifest records the reported KiCad version, but it does not bind the image digest or the settings used for export. Use the captured toolchain and settings inputs for export, and bind their hashes in the manifest and evidence.

6. **Assembly checks do not cover all declared steps.** `checks_asm.test_record` accepts an empty `items` list because `all([])` is true. It does not compare the record with board limits, part data, or variant data. The assembly PDF comes directly from KiCad layers `F.Fab`, `B.Fab`, and `Edge.Cuts`. The batch does not add the selected variant, DNP marks, or hand-install instructions. Compare the record and drawing with the captured inputs.

The status remains `unqualified`, and the test record claims no physical pass. These limits are correct. They do not close the findings above.

This report changes no product file or shared contract. The accepted neutral and Sierra scopes stay closed.
