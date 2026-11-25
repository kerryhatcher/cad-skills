# B10 completion batch review: Pi

Date: 2026-11-15. Author: pi-pcba-dev.

Subject: `docs/reviews/pcba/b10-completion-claude.md`, the frozen B10 completion batch.
Reviewed against the accepted note and `docs/reviews/pcba/b10-completion-scope-root.md`.
I changed no product file.

## 1. Result

The 42 hashes match and the focused suite reports 77 passes. The batch is not complete
against interface section 14. The six scope-root points are real. I confirm each with the
same frozen bytes.

## 2. Before and after hashes

The batch changed or added nine files. The other 33 files are unchanged.

| Path | Before | After |
|---|---|---|
| `skills/pcba-design/SKILL.md` | `69c20a38848a6616d53f84982b0e808c3dab6287d4edbe3e997fb4e589a2777a` | `4025e5cecc5868c6e01bafc13616adf761fa1c277fbeebbf192cbbbeefc20315` |
| `skills/pcba-design/scripts/checks_asm.py` | absent | `bb4df3b6619c5f321f99f9d5a13edf7c546853208ccdb9cc853b888f6c9c2133` |
| `skills/pcba-design/scripts/checks_design.py` | absent | `4f1f006e5edf4d32b7a08e2566239e5e59fabaf460b1fa9ef3212fd3e7052858` |
| `skills/pcba-design/scripts/checks_fab.py` | absent | `8e656ae2eae06842a063a5037a3885ff5503f5b3336aad59ac46a520c8b993f4` |
| `skills/pcba-design/scripts/export.py` | absent | `cc1cc26ca6d31b84bb6f45f74b5edec92c655cf2000c053e4bf92885abaa03af` |
| `skills/pcba-design/scripts/package.py` | absent | `89547a618f120d902535d7c7df3899dc830620b6d6b4af3dc493dc62746d2754` |
| `skills/pcba-design/scripts/pcba.py` | `6a7034e4fec3b9815dc23bd8e5c1dd15ac3c0f1226620203910b2443228511a3` | `9ced5a78c73d09482a9a237e14eb2fbcf6660486eaf850e84035da1f742b753b` |
| `skills/pcba-design/scripts/report.py` | absent | `07ecb36ad20743c0dacbbe84c6d12100a4086001523e1f95a9075d57ed67a1f8` |
| `tests/test_pcba_design.py` | `910b12d8c36fdad40a832f636fb02d5f5fa90a2770ab39737df6c1bc61b0fe0f` | `c6c9759d7d77f7fa955e5c2f391d8a5d706867b21330f9c48423cf85efaeb1a9` |

No shared contract file changed. No product file changed by
me.

## 3. Concrete defects

### D1. Mandatory input roles are not captured and not validated

The package manifest binds only `board`, `board_record`, `parts`, `supplier_profile` and
`variants`. It omits `export_settings`, `board_interface`, `toolchain`, `schematic`,
`supplier_rules` and `supplier_settings`.

Probe on an empty-restriction copy:

- `fab.export_inventory` evidence inputs: `board.kicad_pcb` only.
- `fab.layer_order` evidence inputs: `board.kicad_pcb` only.
- `fab.drill_split` evidence inputs: `board.kicad_pcb` only.
- `fab.supplier_rules` evidence inputs: `board.kicad_pcb` and `supplier-profile.yaml`.

The first three checks report `pass`, but the interface section 14 table requires
`export_settings`, and `fab.drill_split` also requires `board_interface`.

`package.py` calls `validate.validate_record` for the manifest and each evidence record. It
does not run the copied validator package rules. `contracts/validate.py`
`_evidence_rules` line 1094 enforces `pkg.check_input_role_missing` for a passed check, and
`_rules_manifest` enforces `pkg.false_qualification` and `pkg.check_missing`. None of those
rules run here.

Fix: capture the settings and toolchain inputs that the interface section 2a names, and run
the package level validation. A passed check without its mandatory roles is not
acceptable, even at `unqualified`.

### D2. The pending checks are hard-coded

`checks_design.erc_pending`, `checks_design.parity_pending` and
`checks_fab.profile_evidence_pending` always return `pending`. They never examine an input.
The interface requires an executable check when the input exists. A missing input may give
`pending`. It cannot replace the implementation for a supplied input.

Fix: implement `design.erc` (the ERC JSON), `design.parity` (the netlist comparison from
schematic and board) and `fab.profile_evidence` (the retained evidence byte hash against
the profile `evidence_sha256`). Bind the schematic and the retained evidence.

### D3. The inventory and drill checks are not independent

`checks_fab.export_inventory` receives the expected file list from the export loop in
`package.py`. It does not derive the list from `export_settings`. A missing or extra export
setting cannot change the result.

`checks_fab.drill_split` reads header text only. It checks the format line and the
`TF.FileFunction` line. It does not compare hole coordinates, counts or plating against an
independent inventory, although it reports `pass`.

Fix: derive the expected set from the captured `export_settings`, and compare the drill
holes against an independent inventory from the captured `board` and `board_interface`.

### D4. The export does not bind the toolchain, settings or image identity

`export.py` copies only the captured board bytes into the work directory and runs the
mutable tag `localhost/cad-skills-pcb:b6`. It does not read the toolchain lock, the project
settings or the export settings. A different local image with the same tag changes the
result without a record.

Fix: pin the image from the captured toolchain lock, copy the project and export settings
that the export needs, and bind those files as manifest inputs.

### D5. Source freshness is not repeated after staged validation

`package.py` runs `snap.check_unchanged()` before the staged writes. It then writes every
file and runs `_verify_staged`. A source change during the staged writes passes the staged
gate, because the gate compares the staged files with the bytes already captured.

Fix: repeat `snap.check_unchanged()` immediately before `publish_dir`, after
`_verify_staged`.

### D6. Assembly evidence is incomplete

- `checks_asm.test_record` passes an empty item list. Probe: a record with
  `{"physical_test_passed": false, "items": []}` returns `pass items=0`. The check does
  not compare the record items with the board electrical limits or the hand-install steps.
- The assembly drawing is the raw KiCad PDF of `F.Fab,B.Fab,Edge.Cuts`. It does not express
  the selected variant or the DNP marks, as interface section 6 states.
- The record says "the other checks pass", but the manifest shows `asm.stock_dated` as
  `fail`. The record text is inaccurate.

Fix: compare every declared limit and hand-install step with the captured inputs, and fail
when a necessary step is absent or extra. Add the variant and DNP marks to the assembly
drawing. Correct the record text.

## 4. Confirmed correct

- The manifest and evidence records are structurally valid, and the 13 check IDs are
  present with one evidence file each.
- The status is `unqualified` with reasons for the open conditions.
- The staged gate refuses links, extra files, missing files and changed bytes, and the
  publication preserves prior packages.
- The `drill_applicability` empty list is accepted because both drill files are present.
- The neutral, alternate and Sierra draft behavior is unchanged and stays accepted.

## 5. Limits

This review is against the frozen bytes. It does not ask for a supplier qualification
claim. The shared snippet route remains an integration item.
