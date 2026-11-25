# B10 final integrity replacement review: Pi

Date: 2026-11-15. Author: pi-pcba-dev.

Subject: `docs/reviews/pcba/b10-final-integrity-replacement-root.md` and
`b10-final-integrity-replacement-root.sha256`. Reviewed against
`b10-final-integrity-correction-root.md`, interface section 14, and the BOM role correction.
I changed no product file.

## 1. Result

I accept the replacement for the five released corrections and the BOM role table. Those
are correct and no blocker remains in them. One additional role-binding finding (F1)
remains: `asm.test_record` reads the board record but does not bind `board_record`.

- 113 of 113 manifest hashes match.
- `docs/reviews/pcba/b10-final-integrity-replacement-root.md` is
  `a2ec2383bbb365cf7a6d4a1423e0dc036356351fae007c9c0403126137db3019`.
- `b10-final-integrity-replacement-root.sha256` is
  `72e1569a2c3211576cb2077f3f4102f2a7d764be5364b5bf054106699768d71c`.
- `uv run tests/test_pcba_design.py`: 105 passed, 0 failed, exit 0.
- Copies: 15 of 15.
- Retained package: full validator exit 0, no finding, status `unqualified`, 10 checks pass,
  `design.drc` and `asm.stock_dated` fail, `fab.supplier_rules` is `unconfirmed`.

## 2. Hashes before and after

The replacement changed 34 files, added 15 and removed 1, relative to the 99-file record.

| Path | Before | After |
|---|---|---|
| `skills/pcba-design/SKILL.md` | `49f9019712efb0da8632bfbdd85a10b2ccf30965fccf376ae52e1a8136f07cb2` | `4166fbffa1f4f60be870eef50dd4368940257b8ea4aa9462576c23eda464fa04` |
| `contracts/validate.py` | `102e252c211bab973adc4e5ae97c051ad4b35dfb59e53916d8b8099144731d9e` | `31af5f8764f7e3027cbaeb1fee3c0523ec7f9745f2b23e1ad1670ed28a7a4f41` |
| `skills/pcba-design/scripts/checks_asm.py` | `826dabdda919f6261a9bb45830b8c7ecd37a46ae4c1efc53845036964ea39a10` | `9f2c41c3f2bb4e9869b7f8e7841ee1a5af1acbbd87e930f73faf651b2eaf422f` |
| `skills/pcba-design/scripts/checks_fab.py` | `57246c9db87707080e977932af771752eea6719911cfc2b31a09803fa973cbf0` | `3e7ed25aaae0b88d65138e6af50baf3db0e84ae28c2fc821d4b0a0ddecae4e4b` |
| `skills/pcba-design/scripts/export.py` | `bcb32c16e336693a50d3203e4c49f22f54e6681bfdf75491134101430aae5504` | `028ec641676afb47a4a1f653ae6f3f2ca70c37aa3b38ff21872aaada7c67cadf` |
| `skills/pcba-design/scripts/package.py` | `c3d768f97babdeba952a619ba8935fd77ef5766bfe510ac80e9286cd46f53a97` | `935a9105ecea929aac00cb9210c354593593ec351190662a2696737661d3df07` |
| `skills/pcba-design/scripts/pcba.py` | `a0a5290b0e3132e32e377a4d67eb6f1587a8b326ddd1a59546915dafcab2fc8f` | `c622e3267fa52a5430d34ddd941858c7559a030ad39827eb1156a582a944f802` |
| `skills/pcba-design/scripts/report.py` | `6b38efc4cce801df1b26586cc52de6ace133b7d6a9dfc4903da7fad366948543` | `e7768558a4c533ae55022d1c111396c7208dcafdcde8f956d7afe9f8ce0ae1bd` |
| `tests/test_pcba_design.py` | `44dc570447d01f2d006ede1db83b3873a6bee4dc6ce21a4b8b900c76ce69ed8f` | `4f31bbea0c2c0fc5cab1b0b4da2fa95549cfdce4dfce172789206dfb85e763c7` |

Added: `skills/pcba-design/scripts/board_inventory_worker.py`
`e8a0ed7e2ffcfcf339afce656a38c72015f50204f3616be9fe99751f7ec81014`, the updated
interface `60047a43a0515bb136486b8baaedb0a940f79d80f21fca9781712cca77652455`, the shared
validator copies at `31af5f87...`, `tests/test_pcb_tools.py`
`037256854d6cc3fbdd3af69e0d83ebcf9db188e0b5edfb7e0dbc342b54e44746`, and the old fixture
`manufacturing/supplier.yaml` `29e33a41...`. Removed:
`tests/fixtures/pcba-design/project/supplier-profile.yaml`.

## 3. The five corrections and the role table

### D1. Final publication gate

`package.py` now runs `_verify_staged`, the full copied validator, the private
`after_validate` test hook, `snap.check_unchanged`, a second `_verify_staged`, and then
`publish_dir`. The second gate is immediately before publication.

`_verify_staged` compares the manifest and every staged file by SHA-256 and byte count,
plus extra files, missing files, the file count, symlinks and hard links.

Probe: the root after-validation probe changes `fab/gerber/board-B_Cu.gbl`. The result is
`Refused`, error `package.hash_mismatch`, and `published: false`. The root probe result now
matches the fixed code.

### D2. Complete drill reference

`board_inventory_worker.py` runs with pcbnew in the locked image. It measures all drilled
pads and through vias in global coordinates with diameter and plating. It refuses an oval
drill, a non-through via, a non-positive diameter and an unsupported pad type. The package
refuses unsupported geometry with `drill.unsupported`.

`package.py` feeds the measured inventory to `drill_split`. The report
`reports/board-hole-inventory.json` binds `board_sha256`
`3bda15fa26f711a5647dc6cdd2f074786095e272062bd4737a3773664240f14e`, `worker_sha256`
`e8a0ed7e...` and `image_identity` `sha256:b273...`. The interface hole list is no longer
the drill reference.

Probe: empty the interface holes on the standard fixture. The package still writes and
`fab.drill_split` is `pass`, because the check uses the measured board inventory.

### D3. Sierra compatibility

Both commands now read `manufacturing/supplier.yaml` and compare the profile
`content_sha256` with `board.supplier.profile_sha256`. The status record and the input
bindings keep the full file hash. The old fixture moved its profile to
`manufacturing/supplier.yaml`; `supplier-profile.yaml` is removed.

Probe: the Sierra command on the standard fixture exits 0. The focused test
`test_sierra_standard_layout_content_hash_and_byte_binding` checks the content hash and the
full-file input binding.

### BOM policy and manufacturer

`checks_asm.bom_consistent` takes the captured policy and compares manufacturer, MPN,
references, quantity and DNI. Under `exclude_from_bom` it omits hand-installed groups from
the expected supplier rows. The neutral data, drawing and test instructions keep those
references.

The focused test `test_bom_policy_and_manufacturer_comparison` covers the exclusion pass,
the include failure, the matching row and a changed manufacturer.

### Test record

`checks_asm.test_record` refuses a duplicate item ID before it builds the item dictionary.
It compares the selected variant, each hand-install instruction and reference, the board
limits, the `not measured` status and the physical claim. The focused test
`test_test_record_variant_instruction_and_duplicate_refused` covers the variant, instruction,
missing instruction and duplicate ID cases.

### BOM role table

`report.py`, interface section 14 and the shared `CHECK_INPUT_ROLES` now name
`supplier_profile` for `asm.bom_consistent`. The shared and copied validators are
`31af5f87...`. The retained `asm.bom_consistent` evidence binds
`manufacturing/supplier.yaml`. The shared negative test is in `tests/test_pcb_tools.py`.

### F1. Additional role binding: `asm.test_record` misses `board_record`

This is the same class as the BOM policy role.

- `package.py` line 297 calls
  `checks_asm.test_record(outputs["test/test-record.json"][2], board["electrical_limits"], ...)`.
  The limits come from `board.yaml`, whose role is `board_record`.
- `report.py`, `contracts/validate.py` `CHECK_INPUT_ROLES` and interface section 14 list
  the `asm.test_record` roles as `board`, `parts`, `variants`. `board_record` is absent.
- The retained `asm.test_record` evidence binds `kicad/board.kicad_pcb`, the part files
  and `variants.yaml`. It does not bind `board.yaml`.
- The manifest does carry `board.yaml` as a `board_record` input, so the binding is
  available.

Why it matters: the check derives the expected electrical limits from the board record. A
changed board record changes the expected limits. Without the binding, the evidence does
not show which board record produced the expected limits.

Fix, matching the BOM policy correction:

- Add `board_record` to `asm.test_record` in the interface section 14 table, the shared
  `CHECK_INPUT_ROLES` and `report.py`.
- Add a shared negative test that removes the board record from the test-record evidence
  and expects `pkg.check_input_role_missing`.
- This is a shared table change, not a schema change. The validator hash will change, and
  the lead owns that change. The evidence then binds `board.yaml` because the package
  already captures it.

## 4. Minor observations

- The private `_hooks` argument stays in `build_package`. The CLI does not pass it. The
  regression tests use it.
- `_verify_staged` runs twice. The first run gives an early refusal; the second run is the
  final gate. The redundancy is harmless.
- The `fab.drill_split` evidence still binds `board_interface` because the mandatory role
  remains. The check reads the measured board inventory, not the interface holes. The
  interface comparison is not performed; the root allowed a separate comparison if useful.

## 5. Disclosed items

- The snippet routing entry for `pcba-design` remains release-owned. The exact-set failure
  remains until the skill and its entry are added together.
- KiCad writes export timestamps, so runs differ in bytes. Each package binds its own
  output bytes.
- No physical test ran. Supplier conventions stay `unconfirmed`.

## 6. Limits

The accepted neutral and Sierra behavior is closed. The shared schema is unchanged. This
review covers the frozen bytes only.