# BOM OLE2 freeze review from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: review of `docs/reviews/b12-bom-ole2-freeze-claude.sha256`. This report writes no
product file. It does not commit and it does not use `git add`. It made no network call.

## 1. Freeze and hashes

The freeze file `docs/reviews/b12-bom-ole2-freeze-claude.sha256` has SHA-256
`07b6eed7db60fd1f9738e6dfc05a1c0ae17f15c8751305f9d4e3691a855e7ac5`. It matches the author
message.

| Item | Before | After |
|---|---|---|
| Entries | 12 | 12 |
| `sha256sum -c` | 12 of 12 OK | 12 of 12 OK |
| Freeze file hash | `07b6eed7...` | `07b6eed7...` |

The P-6 and P-7 freezes stay as history at their hashes.

## 2. Intent-to-add

The BOM copy is visible to `git ls-files`:

```text
docs/reviews/sierra-source-evidence/BOM-Sample-and-Demo.xls
```

`git status --short` shows ` A` (intent to add). No content is staged. No commit occurred.
This is the lead-authorized route.

## 3. Tests reproduced

| Command | Result |
|---|---|
| `uv run tests/test_release_packaging.py` | 28 of 28 passed, exit 0 |
| `uv run tests/test_release_isolation.py` | 29 of 29 passed, exit 0 |
| `uv run tests/test_release_harness.py` | 65 of 65 passed, exit 0 |

The failing test `test_real_distribution_excludes_supplier_copies` now passes. The D-1 count
is 17.

## 4. Content check

| Item | Result |
|---|---|
| OLE2 token | `OLE2_PREFIX = bytes.fromhex("d0cf11e0a1b11ae1")` and the `_magic_ok` branch are correct |
| Required magic | `application/vnd.ms-excel` is in `MAGIC_REQUIRED_TYPES` |
| Tests | The three OLE2 tests pass. The bytes are project-authored |
| Manifest entry | `sierra-bom-sample-xls` carries the required fields, `magic: OLE2`, and `prior_retrieved: unknown`. `replaces` is absent |
| Exclusion | `docs/reviews/sierra-source-evidence/*.xls` is in `excluded_patterns` |
| BOM copy | SHA-256 `1b486a0a...`, byte count 37376, matching the entry |
| Network | No test, CI or harness call was made. The isolation import check passes |

## 5. Public GET record

`docs/reviews/b12-bom-public-get-record-claude.md` is metadata only.

- The BOM row names the URL, resolved URL, request time, byte count, hash, server content
  type, and the stored path.
- The terms and FAQ rows are recorded. Their bytes are not stored and not in the freeze.
- The record claims no license, no permission to redistribute, and no reuse right.
- The FAQ difference note is honest. It does not say which of the two bodies is current.
- The BOM prior date is unknown. The `/tmp` file time is not used as a retrieval time.

## 6. Note

### N-1 Add the BOM to the third-party notice inventory

`docs/release-licensing.md` lists the redistributed Sierra evidence. The new BOM is local
evidence and is excluded from distribution. It belongs in the notice inventory when the
notice is next updated.

Correction: add one row with the URL, retrieval date, hash, content type, exclusion
decision, and the "no reuse claim" note. Low. It is not part of this batch.

## 7. Verdict

The freeze has 12 entries and all match. The BOM is visible through intent-to-add. The
packaging suite passes 28 of 28. The OLE2 code, the tests, the manifest entry and the
exclusion are correct. The public GET record is honest.

I recommend the lead accept the BOM-only batch at freeze
`07b6eed7db60fd1f9738e6dfc05a1c0ae17f15c8751305f9d4e3691a855e7ac5`. Provider
authorization stays zero.

I made no edit during this review.

## Limits

This review ran focused local checks. It made no network call and no CAD call. It changed
no product file and did not use `git add`. It does not approve a release.
