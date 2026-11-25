# Codex review: B10 final integrity replacement

Date: 2026-11-15 UTC. Reviewer: codex-pcba-dev. Branch: `work/pcba`.

The freeze record hash is `a2ec2383bbb365cf7a6d4a1423e0dc036356351fae007c9c0403126137db3019`. The hash-list file hash is `72e1569a2c3211576cb2077f3f4102f2a7d764be5364b5bf054106699768d71c`. All 113 listed file hashes match before and after this review.

I reviewed the five released corrections and the BOM input-role change. I did not run tests. The frozen log reports 105 focused tests passed. The copy log reports 15 of 15 files passed.

## Confirmed corrections

The final gate runs full validation, then checks the manifest and staged files again. It checks hashes, byte counts, file counts, and links. It also checks the captured inputs before publication. The CLI does not expose the test hooks.

The board worker measures drilled pads and through vias from captured board bytes. It records transformed positions, drill dimensions, plating, and duplicate holes. Unsupported drill shapes refuse the package.

The Sierra command uses `manufacturing/supplier.yaml` and the canonical profile hash. Its status record binds full input file hashes.

The BOM check uses the captured policy. It compares the manufacturer, MPN, references, quantity, and DNI value. The test-record check compares the variant, limits, hand-install instructions, and physical-result claim. It refuses duplicate item IDs.

The shared validator and the skill copy have the same hash, `31af5f8764f7e3027cbaeb1fee3c0523ec7f9745f2b23e1ad1670ed28a7a4f41`. Both name `supplier_profile` for `asm.bom_consistent`. The evidence builder and interface section 14 use the same role.

## Finding

1. **The drill check does not apply all accepted export settings.** `export.py` maps the board origin to KiCad's plot origin. It also supports leading-zero suppression and decimal coordinates. `checks_fab.parse_excellon` assumes an absolute coordinate frame, a fixed Y sign, and the `INCH,LZ` header. `package.py` passes the decimal count to `drill_split`, but it does not pass the origin or zero-suppression setting. A valid export with a board origin or another supported zero format can fail the drill check. Pass the captured settings to the parser and apply their coordinate transform. Refuse a setting that the check cannot examine.

2. **The test-record evidence omits its board-record binding.** `package.py` supplies electrical limits from `board.yaml` to `checks_asm.test_record`. That file has the role `board_record`. The report and validator role tables list `board`, `parts`, and `variants` for this check. They do not bind `board_record`. Thus the evidence does not hash-bind the source of the limits that it checks. Add `board_record` to `report.py`, both validator role tables, and interface section 14. Add a validator case that refuses evidence without this role.

## Review result

The final integrity gate, complete board drill inventory, Sierra profile compatibility, BOM comparison, and test-record content checks match the released correction. The drill-settings and test-record input-role findings remain open.

This report changes no product file or shared contract. The accepted neutral and Sierra behavior stays closed outside the required profile compatibility correction.
