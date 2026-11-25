# BOM OLE2 narrow text review from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: narrow text-only review of
`docs/reviews/b12-bom-ole2-freeze-r2-claude.sha256`. This report writes no product file. It
does not commit and it does not use `git add`. It made no network call.

## 1. Freeze

| Item | Value |
|---|---|
| Freeze file | `docs/reviews/b12-bom-ole2-freeze-r2-claude.sha256` |
| Freeze SHA-256 | `f90b73f928755f1b8ca0bc1d6605b5ed8213c0d65bbef6c84a4d72e8d394d841` |
| Entries | 13, all match |
| Supersedes | `07b6eed7...` |

## 2. Text diff reviewed

| File | Change | Result |
|---|---|---|
| `tests/eval/packaging.py` | The OLE2 comment is three complete active sentences | Pass. No semicolon |
| `tests/test_release_packaging.py` | The three OLE2 docstrings and the D-1 docstring are complete sentences | Pass |
| `tests/eval/distribution.yaml` | `url_state` and `license_state` are complete active sentences | Pass. No semicolon |
| `docs/release-licensing.md` | The new BOM row names local evidence, the exclusion, and the missing reuse right | Pass |
| `docs/reviews/release/b12-bom-public-get-record-claude.md` | Rewritten in active voice with the same measured values | Pass, with n2 |

## 3. Technical scope unchanged

| Item | Value |
|---|---|
| BOM SHA-256 | `1b486a0a1da968e128cf109bd25e50837c99b5a8f83a490f748a1c1ccb1b769c` |
| Byte count | 37376 |
| Content type | `application/vnd.ms-excel` |
| Magic | `OLE2` |
| Prior date | `unknown` |
| Distribution decision | `exclude-full-copy` |
| Exclusion | `docs/reviews/sierra-source-evidence/*.xls` |

The OLE2 token, the byte prefix `d0cf11e0a1b11ae1`, the `_magic_ok` branch, and the
`application/vnd.ms-excel` required-magic entry are unchanged. `py_compile` passes for the
two changed Python files. The file hash changed from the comment text only.

No functional suite was rerun, per the lead.

## 4. Notes

### n1 The r2 proposal text is in the freeze and is not STE

`docs/reviews/release/b12-bom-ole2-correction-r2-claude.md` is in the freeze and is not yet
STE. The lead decides whether it stays in the freeze. It is a review record, not a harness
input. Options: rewrite it in STE and freeze again, or remove it from the freeze and keep it
as history.

### n2 One passive sentence remains in the GET record

The GET record says "No login, cookie or supplier contact was used." The agent is unknown,
so STE allows the passive form. An active rewrite is possible: "No request used a login,
cookie or supplier contact." Low.

### n3 Table cells keep fragments

The notice BOM row and the GET record tables use short cell fragments. A table entry is a
vertical list. The fragments are acceptable in that form.

## 5. Verdict

The F-1 text correction is applied. The new text uses complete active sentences. The
technical scope and the measured values are unchanged. The freeze has 13 entries and all
match.

I recommend acceptance of the text-only change, with the lead decision on n1. Provider
authorization stays zero.

I made no edit during this review.

## Limits

This review read the narrow text diff and compiled two files. It made no network call. It
changed no product file and did not use `git add`.
