# B10 role and drill freeze review: Pi

Date: 2026-11-15. Author: pi-pcba-dev.

Subject: `docs/reviews/pcba/b10-role-and-drill-freeze-root.md` and
`b10-role-and-drill-freeze-root.sha256`. Reviewed against
`b10-role-and-drill-correction-root.md`. I changed no product file.

## 1. Result

I accept the two narrow corrections. No executable blocker remains. One text-only
documentation defect remains, which the lead confirmed and will correct.

- 124 of 124 manifest hashes match.
- The freeze record is `ea61f15d810c974aa4703f249c8e55ca5d29352a6208177f46896093de7e32b6`.
- The manifest is `8210ec10b93a34695c3ef7a8b998117ab541937fad0702856876698d883f65aa`.
- `uv run tests/test_pcba_design.py`: 106 passed, 0 failed, exit 0.
- `uv run tests/test_pcb_tools.py`: 59 passed, 0 failed, exit 0.
- Copies: 15 of 15.
- The retained package passes the full copied validator: exit 0, no finding, status
  `unqualified`.

## 2. Hashes before and after

| Path | Before | After |
|---|---|---|
| `contracts/validate.py` | `31af5f8764f7e3027cbaeb1fee3c0523ec7f9745f2b23e1ad1670ed28a7a4f41` | `974c38b93d24fc2a53c8aaab814410abbdb86b58bdf966cbec0e5181cbe169f5` |
| `skills/pcba-design/contracts/validate.py` | `31af5f8764f7e3027cbaeb1fee3c0523ec7f9745f2b23e1ad1670ed28a7a4f41` | `974c38b93d24fc2a53c8aaab814410abbdb86b58bdf966cbec0e5181cbe169f5` |
| `skills/pcb-design/scripts/validate.py` | `31af5f8764f7e3027cbaeb1fee3c0523ec7f9745f2b23e1ad1670ed28a7a4f41` | `974c38b93d24fc2a53c8aaab814410abbdb86b58bdf966cbec0e5181cbe169f5` |
| `skills/pcb-fab-package/scripts/validate.py` | `31af5f8764f7e3027cbaeb1fee3c0523ec7f9745f2b23e1ad1670ed28a7a4f41` | `974c38b93d24fc2a53c8aaab814410abbdb86b58bdf966cbec0e5181cbe169f5` |
| `skills/pcba-design/COPY_SHA256.txt` | `301385987b79d75e99c45abd0c1cd615ac81840dab851ddd8845fe4582bc1297` | `3f9383d4e88e525ac0fe445a1ddf42a29ce9f4b7c0cb6cc4fe2dc086832c8aab` |
| `skills/pcba-design/SKILL.md` | `4166fbffa1f4f60be870eef50dd4368940257b8ea4aa9462576c23eda464fa04` | `8d03d3b957c2532eb8f09c551c4bab2027b54c3073f5af095ff1629d461e64d0` |
| `skills/pcba-design/scripts/export.py` | `028ec641676afb47a4a1f653ae6f3f2ca70c37aa3b38ff21872aaada7c67cadf` | `2a04fc6c042ba88c08368cc36914a31810bfac531325aa29555ebf3ff600e230` |
| `skills/pcba-design/scripts/package.py` | `935a9105ecea929aac00cb9210c354593593ec351190662a2696737661d3df07` | `90179772a8224e9c1a009a154e99bdc46b019ba765eff0e3a58dabd5e2ec3a68` |
| `skills/pcba-design/scripts/report.py` | `e7768558a4c533ae55022d1c111396c7208dcafdcde8f956d7afe9f8ce0ae1bd` | `259d53d20dcae760f84e0a6a2c318dba2361b4f1570dc14efc95575090cd1fd6` |
| `tests/test_pcb_tools.py` | `037256854d6cc3fbdd3af69e0d83ebcf9db188e0b5edfb7e0dbc342b54e44746` | `ad669cfa3383eadd9ff3e68c08b64575f6c4df1651906f55ded44ebf246d7db2` |
| `tests/test_pcba_design.py` | `4f31bbea0c2c0fc5cab1b0b4da2fa95549cfdce4dfce172789206dfb85e763c7` | `38b5f33a35d2790d1d96ad54321a5cd39f8483030428a719fbb435765125b0a3` |

The interface is `5d24a4ec7f04d935f479bb62ef52d5e5317c88f98893434d25264979e381814b`. The
retained package files were regenerated, so their hashes changed with the KiCad timestamps.
The new evidence directory `b10-role-drill-evidence/` is in the manifest.

## 3. Correction 1: `asm.test_record` role

- `report.py` now has `asm.test_record: ("board", "parts", "variants", "board_record")`.
- Interface section 14 names `board`, `parts`, `variants`, `board_record`.
- The shared validator and all copies are `974c38b9...`.
- The retained `asm.test_record` evidence binds `board.yaml`, the part files,
  `kicad/board.kicad_pcb` and `variants.yaml`. The expected limits now have a bound source.
- The shared negative test omits the role and expects `pkg.check_input_role_missing`
  (`tests/test_pcb_tools.py`).

## 4. Correction 2: drill settings before export

`export.validate_drill_settings` checks the captured drill settings before any tool call:

- origin `absolute`,
- drill units `in`,
- zero suppression `trailing`,
- decimal places `4`,
- separate files `true`.

An unsupported value raises `export.drill_setting_unsupported`. A combined file is refused
first by the shared export-settings schema with `schema.invalid`, because the schema
precedes the new check.

`test_package_refuses_unexamined_drill_settings_before_tools` covers board origin,
leading-zero suppression, no zero suppression, millimeter units, another precision and a
combined file. It replaces `export.resolve_image` with a function that raises if any tool is
called, and it expects no call. The combined-file case expects `schema.invalid`; the other
five expect `export.drill_setting_unsupported`.

## 5. Text-only defect: README role tables

The four README role tables are behind the validator:

- `contracts/README.md`
- `skills/pcb-design/contracts/README.md`
- `skills/pcb-fab-package/contracts/README.md`
- `skills/pcba-design/contracts/README.md`

Line 157 lists `asm.bom_consistent` roles as `parts`, `variants`, `board_record`, without
`supplier_profile`. Line 161 lists `asm.test_record` roles as `board`, `parts`, `variants`,
without `board_record`.

The lead confirmed this defect and will correct both rows in the source README and the
skill copies, update the copy hash and issue a text-only replacement. No executable code
changes, so this does not block the executable acceptance.

## 6. Confirmed unchanged

- The final publication gate, the measured hole inventory, the BOM policy comparison and the
  assembly comparisons are unchanged.
- The shared schema is unchanged.
- The retained package remains `unqualified`: ten checks pass, `design.drc` and
  `asm.stock_dated` fail, `fab.supplier_rules` is `unconfirmed`.
- The initial-run log records the earlier combined-file expectation failure. The corrected
  test keeps the schema precedence, and the restored historical logs match the 113-file
  manifest.

## 7. Limits

The accepted integrity and geometry scope stays closed. The snippet routing entry remains an
integration task. This review covers the frozen bytes only.