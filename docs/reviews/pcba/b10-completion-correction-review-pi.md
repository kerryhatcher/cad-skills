# B10 completion correction review: Pi

Date: 2026-11-15. Author: pi-pcba-dev.

Subject: `docs/reviews/pcba/b10-completion-correction-claude.md`, the frozen complete B10
correction. Reviewed against `docs/reviews/pcba/b10-completion-correction-root.md` and
interface section 14. I changed no product file.

## 1. Result

All 99 hashes match. The focused suite passes 97 of 97. The package writes a complete
package on the standard fixture and the copied validator passes it with exit 0. Ten checks
pass, `design.drc` and `asm.stock_dated` fail, and `fab.supplier_rules` is `unconfirmed`.
The eight correction items are implemented. Three concrete defects remain.

## 2. Hashes of the changed code

The batch changed or added 60 files and removed 3. The changed code files are:

| Path | Before | After |
|---|---|---|
| `skills/pcba-design/SKILL.md` | `4025e5cecc5868c6e01bafc13616adf761fa1c277fbeebbf192cbbbeefc20315` | `49f9019712efb0da8632bfbdd85a10b2ccf30965fccf376ae52e1a8136f07cb2` |
| `skills/pcba-design/scripts/checks_asm.py` | `bb4df3b6619c5f321f99f9d5a13edf7c546853208ccdb9cc853b888f6c9c2133` | `826dabdda919f6261a9bb45830b8c7ecd37a46ae4c1efc53845036964ea39a10` |
| `skills/pcba-design/scripts/checks_design.py` | `4f1f006e5edf4d32b7a08e2566239e5e59fabaf460b1fa9ef3212fd3e7052858` | `b5a6de7c684d8973cd1063020dc18d36dd7f8cfc6cb04162d920036a348bf2b3` |
| `skills/pcba-design/scripts/checks_fab.py` | `8e656ae2eae06842a063a5037a3885ff5503f5b3336aad59ac46a520c8b993f4` | `57246c9db87707080e977932af771752eea6719911cfc2b31a09803fa973cbf0` |
| `skills/pcba-design/scripts/export.py` | `cc1cc26ca6d31b84bb6f45f74b5edec92c655cf2000c053e4bf92885abaa03af` | `bcb32c16e336693a50d3203e4c49f22f54e6681bfdf75491134101430aae5504` |
| `skills/pcba-design/scripts/package.py` | `89547a618f120d902535d7c7df3899dc830620b6d6b4af3dc493dc62746d2754` | `c3d768f97babdeba952a619ba8935fd77ef5766bfe510ac80e9286cd46f53a97` |
| `skills/pcba-design/scripts/pcba.py` | `9ced5a78c73d09482a9a237e14eb2fbcf6660486eaf850e84035da1f742b753b` | `a0a5290b0e3132e32e377a4d67eb6f1587a8b326ddd1a59546915dafcab2fc8f` |
| `skills/pcba-design/scripts/report.py` | `07ecb36ad20743c0dacbbe84c6d12100a4086001523e1f95a9075d57ed67a1f8` | `6b38efc4cce801df1b26586cc52de6ace133b7d6a9dfc4903da7fad366948543` |
| `tests/test_pcba_design.py` | `c6c9759d7d77f7fa955e5c2f391d8a5d706867b21330f9c48423cf85efaeb1a9` | `44dc570447d01f2d006ede1db83b3873a6bee4dc6ce21a4b8b900c76ce69ed8f` |

New: `skills/pcba-design/scripts/drawing.py`
`91db2cfa72211958d4a1f98e03f337abaada724491c8a6b2e7420f1b37a11c7d`, the standard fixture
`tests/fixtures/pcba-design/standard-project/` (16 files), and the retained package
`tests/fixtures/pcba-design/retained/` (42 files). No shared contract file changed.

## 3. Concrete defects

### D1. The staged-byte gate runs before the validator and the post-validation hook

`package.py` runs the steps in this order: write the staged files, `_verify_staged` (the
byte, set and count gate), the copied validator, the `after_validate` hook,
`snap.check_unchanged`, and `publish_dir`. `snap.check_unchanged` rehashes only the captured
inputs. It does not rehash the staged outputs. A change after `_verify_staged` is published.

Root probe result (`b10-after-validation-probe-root.json`): the hook changes
`fab/gerber/board-B_Cu.gbl`. `build_package` returns success and publishes. The bound hash
is `61e7a8c0522e5dc3fb4e990a1ec058e9c28ca37fbc359a6325bb902a84ac2494`. The published hash
is `8cb13e4a7c1b84ee39f5253e9bdde1f84c8eea6efeb4d63514abcb5f8bc0a535`.

Fix: after the validator and after any hook, compare the validated manifest bytes and every
staged output path, hash, size and count, plus links, immediately before `publish_dir`,
together with the input freshness. The staged gate must be the last check.

### D2. The drill equivalence is against the interface, not the board

`package.py` calls
`checks_fab.drill_split(fab["drill"], export_record["drill"]["decimal_places"], interface["holes"], ...)`.
The inventory is `interface["holes"]` from `mechanical/board-interface.json`. No code
measures the board pads and vias to establish that the interface list is complete.
`checks_design.board_pads` reads board pads for `design.parity`, but only for net names. It
does not feed `fab.drill_split`.

The shared validator binds the interface to the board file through
`cross.board_pcb_hash_mismatch` (the interface `board_sha256` equals the board file hash
`3bda15fa26f711a5647dc6cdd2f074786095e272062bd4737a3773664240f14e`). The hole list
completeness is only declared. A board drilled hole that is absent from both the interface
and the drill files is not caught. Thus `fab.drill_split` proves drill-versus-interface
agreement, not drill-versus-board equivalence.

Fix: derive a complete hole inventory from the captured board pads and vias, or add a
completeness check that every board drilled pad and via appears in the interface, and then
compare the drill files.

### D3. The profile hash rule is not applied in the Sierra path

Under the lead's decision, `board.supplier.profile_sha256` is the canonical content hash and
the input bindings hash the full bytes. The package follows this: `package.py` compares
`profile["content_sha256"]` with the field. The Sierra path does not. `pcba.py` compares
`sha256(profile_snap["raw"])`, the full file hash, with the field. It also reads the profile
at the fixed name `supplier-profile.yaml`.

Probes on the standard fixture data:

- Full file hash `1c036fc4df5fc0562e419d3a844877f69f319b338dba6179aadaef82220e9813`.
- Content hash `6d643ad08dbbf38bf8eb9139bc5ffd1fe6e8bd9b3bf6152df5a5cf7152946d8d`, equal to
  the board field.
- The Sierra path refuses with `supplier.profile_mismatch`. At the standard layout it also
  refuses with `supplier.profile_missing`, because the profile is at
  `manufacturing/supplier.yaml`, not `supplier-profile.yaml`.

This is the disclosed compatibility defect. Fix: update interface section 2a and the Sierra
path together so both use the content-hash rule and the accepted profile path.

### D4. The test hooks live in the production path

`build_package` accepts `after_stage` and `after_validate` hooks. They are the vector for
D1. Keep them test-only, or remove them, and make the final gate independent of any hook.

## 4. Confirmed fixed

- Capture now binds the mandatory roles: `board`, `board_interface`, `board_record`,
  `export_settings`, `parts`, `schematic`, `supplier_profile`, `supplier_rules`,
  `supplier_settings`, `toolchain`, `variants`.
- The package runs the copied validator on the project and on the staged package before
  publication, and refuses on a finding. A missing mandatory record refuses with
  `package.input_missing`.
- `design.erc`, `design.parity` and `fab.profile_evidence` are executable, with `pending`
  only for absent input.
- `fab.export_inventory` derives the expected names from the captured export settings and
  reports missing and extra files separately. `fab.layer_order` uses the FileFunction line.
- The toolchain image identity and the KiCad version are compared with the lock, and no pull
  is made.
- `_verify_staged` refuses links, extra files, missing files, a count difference and changed
  bytes.
- `asm.test_record` refuses an empty step list and a missing hand-install step. The assembly
  drawing is an SVG with DNP and HAND marks for the selected variant.
- The stock claim is corrected: `asm.stock_dated` fails on the standard fixture.
- The standard fixture and the retained full validator result are present, and the retained
  validator exits 0.

## 5. Disclosed items

- The snippet routing entry is release-owned and unchanged. It is the only failing skill
  package test.
- KiCad writes creation dates into the export files, so two runs differ in bytes. The
  record does not claim byte equality between runs.
- The fixture routing makes `design.drc` fail. The failure is the true fixture state.

## 6. Limits

No physical board is built or tested. No supplier is contacted. The supplier conventions
stay `unconfirmed`. This review covers the frozen bytes only.
