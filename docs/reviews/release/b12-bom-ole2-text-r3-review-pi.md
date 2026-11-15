# BOM OLE2 text freeze r3 review from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: single narrow text-only review of
`docs/reviews/b12-bom-ole2-freeze-r3-claude.sha256`. This report writes no product file. It
does not commit and it does not use `git add`. It made no network call.

## 1. Freeze

| Item | Value |
|---|---|
| Freeze file | `docs/reviews/b12-bom-ole2-freeze-r3-claude.sha256` |
| Freeze SHA-256 | `ff67bca674b75a01ff66428c6465677cdc07733d8e57cb9ce099f5483112520c` |
| Entries | 13, all match |
| Supersedes | r2 `f90b73f9...` |

## 2. Text diff

| File | Text | Result |
|---|---|---|
| `tests/eval/packaging.py` | "The OLE2 signature contains eight bytes. The parser compares the file prefix with this signature." | Pass. Two complete active sentences |
| `tests/test_release_packaging.py` | The D-1 docstring and the three D-8 docstrings are complete active sentences | Pass |
| `tests/eval/distribution.yaml` | `license_state` is "The author did not assess reuse permission. The record claims no permission." | Pass. No semicolon |
| `docs/release-licensing.md` | The BOM row uses the same active sentence | Pass |
| `docs/reviews/release/b12-bom-public-get-record-claude.md` | Active voice. The FAQ explanation is removed. Only the measured hash difference is stated | Pass |

The previous passive sentence "No login, cookie or supplier contact was used" is gone.

## 3. Technical scope unchanged

| Item | Value |
|---|---|
| BOM SHA-256 | `1b486a0a...` |
| Byte count | 37376 |
| Content type | `application/vnd.ms-excel` |
| Magic | `OLE2` |
| Prior date | `unknown` |
| Distribution decision | `exclude-full-copy` |
| Exclusion | `docs/reviews/sierra-source-evidence/*.xls` |

The OLE2 prefix, the `_magic_ok` branch, and the required-magic entry are unchanged.
`py_compile` passes. No functional suite ran, per the lead.

## 4. Very low observations

### o1 The D-1 docstring drops its label

`test_real_coverage_every_supplier_source_has_an_entry` now starts "The test compares
seventeen supplier sources with the manifest." Other tests keep a `D-1.` or `P-2.` label.
The label is optional. No change is necessary.

### o2 The word "parser"

The new docstrings say "The parser reports D-8". The module calls the check
`check_entries`. Consider "the check" for one term. No change is necessary.

## 5. Verdict

The r3 text is correct and active. The technical scope and the measured values are
unchanged. The freeze has 13 entries and all match. I accept the narrow text.

Functional acceptance stays unchanged. Provider authorization stays zero.

I made no edit during this review.

## 6. Separate scope noted

The A2 test binding correction to the tool content hash and the A1 and A2 fixture freeze are
a separate batch. I will review that freeze when it lands.

## Limits

This review read the narrow text and compiled one file. It made no network call. It changed
no product file and did not use `git add`.
