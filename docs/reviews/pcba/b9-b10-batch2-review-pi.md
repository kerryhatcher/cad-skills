# B9/B10 batch 2 review: Pi

Date: 2026-11-15. Author: pi-pcba-dev.

Subject: `docs/reviews/pcba/b9-b10-batch2-claude.md`, the frozen batch 2 supersession.
Reviewed against `docs/reviews/pcba/b9-b10-remaining-execution-claude.md` at SHA-256
`22afe3344d32c1306060446fc5622bc9bd586c15811e0b96accd3ce6c3607610` and the batch 2
release root. I changed no product file.

## 1. Result

I accept batch 2 in its declared scope, with two concrete gaps and one boundary item.

- `uv run tests/test_pcba_design.py`: 62 passed, 0 failed, exit 0.
- All 36 listed file hashes match.
- `sha256sum -c skills/pcba-design/COPY_SHA256.txt`: 15 of 15 copies OK.
- `uv run tests/test_skill_packages.py`: 7 of 8. The failure is only the release-owned
  snippet route.

## 2. Before and after hashes

The batch changed or added eight files. The other 28 files are unchanged.

| Path | Before | After |
|---|---|---|
| `docs/reviews/sierra-source-evidence/BOM-Sample-and-Demo.xls` | absent | `1b486a0a1da968e128cf109bd25e50837c99b5a8f83a490f748a1c1ccb1b769c` |
| `docs/reviews/sierra-source-evidence/BOM-Sample-and-Demo.provenance.md` | absent | `bda33654ff098881832c746c1586baaa370272eef8d47f210b6cd0c7e0b63d30` |
| `skills/pcba-design/contracts/part-map-1.1.schema.json` | `c61bf95ecdca13d245e90cc6d89e17af3b523aa3630816403c43b46469a9e8ad` | `890a36acfb696c0823b370a33661ea9d7476578433513bf79c5b0007060217ce` |
| `skills/pcba-design/scripts/pcba.py` | `22360ed4344c41cbae008aa15d46788e4dd86307b5c0e4f31223745cdc3e5b55` | `a8f1e0d832444a1820141ec3dafbd5a6fde65fd50cad47c9898ce8dbd82678ab` |
| `skills/pcba-design/scripts/sierra.py` | absent | `13fc4636733498ef568a22d9acb4a881b6aa147a11dd51f4c78604ac46630887` |
| `tests/fixtures/pcba-design/project/board.yaml` | `95901a4b284357c2b6507f7eb4d7dcb39a84228587cb6d759c71743cf7a9257a` | `3137bf4b40e21360c15ad36776f20f9dfda570649197f38a3901ca531019ab4f` |
| `tests/fixtures/pcba-design/project/supplier-profile.yaml` | absent | `29e33a4103eaa6d19c563a6cea52e1b0b25937480edff3a6d127e3428a2deaa4` |
| `tests/test_pcba_design.py` | `ab45b2104feef5318c101193ae86f047962e0372f41dbbefbc4eb7daca288ff6` | `7798a91c507b46e550f331137133c60c6e5a82ff77563b54e96ead88dfdd262b` |

No shared contract file changed.

## 3. C1 and the alternate corrections

- The 1.1 schema now has a mechanical branch that forbids `alternates`: `{required:
  [mechanical], not: {required: [alternates]}}`. The loader also refuses
  `map.alternate_on_mechanical`. C1 is closed in both places.
- Alternate selections are validated before lookup. A non-mapping block, a list-valued
  value and a numeric value each give one `alternate.selection_invalid` finding, no
  traceback. The reference and name patterns are `^[A-Za-z][A-Za-z0-9_.-]{0,31}$` and
  `^[a-z][a-z0-9_-]{0,31}$`.
- The focused tests cover the mechanical entry, the list-valued selection and the unknown
  selection.

## 4. Verified in the Sierra outputs

- The BOM header row equals the retained sample header row at Excel row 7, byte for byte,
  including `Size / Footprint  (optional)` and `Manfacturer (optional)`.
- A DNP group carries `DNI` and forms a separate row from the populated group.
- `Quantity per board` is the reference count. The order quantity is not used.
- `hand_installed_bom`: `include_in_bom` keeps the hand row, `exclude_from_bom` omits it,
  and a missing or unknown value stops only the BOM. The status records the policy.
- A changed supplier profile refuses with `supplier.profile_mismatch`.
- The XY draft uses mil with the 0.0254 factor, `T`/`B` side, and the normalized rotation.
  It holds the automatic populated rows only.
- `reports/sierra-status.json` records `xy_units` as `stated_by_sample`, every other
  convention as `unconfirmed`, and `qualification` as `unqualified`.
- The test record marks every limit and the hand-install step `not measured`, with no
  physical pass.
- Two runs give the same bytes.
- The provenance record honestly states that the retrieval time is not recorded and that
  the page was not fetched. Fresh retrieval and distribution handling are release-owned.

## 5. Concrete gaps

G1. The interface section 9.4 service condition is not recorded. The status record has no
`service`, `fabrication_location` or `assembly_location`. Add them as `turnkey_pro` and
`unconfirmed`.

G2. The interface section 9.4 ITAR and export-control exclusion is not checked. The
`sierra` command ignores `board_record` restrictions. A restricted board still produces
Sierra outputs. Unknown applicability must stay open.

Minor. The neutral rows do not carry `supplier_part_numbers`, so the BOM `Vendor` and
`Vendor Part Number` columns are always blank. If the BOM must fill known vendor data, the
neutral row needs it.

## 6. Boundary item for the publication batch

`build_sierra` re-reads `board.yaml` after `build` captured it, and reads
`supplier-profile.yaml` without binding it as an input. Interface section 14 says to
capture each input once and not reread. The publication batch must capture both files
through `Snapshots` and bind the profile. This does not block batch 2, because batch 2 is
not the package.

## 7. Scope boundary

The fabrication Gerber drawing, the Excellon drill files, the board image and the assembly
drawing are not in this batch. Batch 2 declares only the BOM, the XY draft, the test record
and the status. The snippet route stays an integration task.
