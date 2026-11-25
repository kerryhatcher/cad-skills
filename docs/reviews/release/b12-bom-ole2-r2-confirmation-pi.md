# BOM OLE2 revision 2 confirmation from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: confirmation of `docs/reviews/release/b12-bom-ole2-correction-r2-claude.md`. This
report writes no product file. It does not commit. It made no network call.

## 1. Confirmation

I confirm revision 2. It is BOM only. The terms and FAQ scope is removed. `replaces` is
omitted. It answers N-1 and N-2 from
`docs/reviews/release/b12-bom-ole2-confirmation-pi.md`.

## 2. Check

| Item | Result |
|---|---|
| Scope | One BOM GET, the OLE2 code and tests, one manifest entry, one local copy |
| BOM hash | `1b486a0a...` matches the PCBA worktree copy |
| BOM magic | `d0 cf 11 e0 a1 b1 1a e1` |
| Prior date | `prior_retrieved: unknown` is honest |
| OLE2 code | `OLE2_PREFIX` and the `_magic_ok` branch are correct |
| Required magic | `application/vnd.ms-excel` is added to `MAGIC_REQUIRED_TYPES` |
| Tests | Three tests. The OLE2 fixture is project-authored. No network call |
| Manifest | The entry carries the required fields, including `magic: OLE2` |
| Exclusion | `docs/reviews/sierra-source-evidence/*.xls` is added |
| Local copy | The release-tree copy is the reference. The PCBA copy stays untouched |
| Freeze | A new `b12-bom-ole2-freeze-claude.sha256`. The P-6 and P-7 freezes stay as history |

## 3. Notes

### N-4 The freeze list includes the review records

Section 7 adds the review records to the freeze. That is acceptable. The freeze test
requires the harness inputs. Extra entries do not affect it. No change is necessary.

### N-5 The open items stay with the lead

Section 8 correctly leaves the terms page and the out-of-scope FAQ GET for the lead. I
agree. The FAQ bytes are not in the repository.

## 4. Recommendation

1. Implement sections 3 to 6.
2. Run `uv run tests/test_release_packaging.py` and the import check.
3. Freeze `docs/reviews/b12-bom-ole2-freeze-claude.sha256`.
4. Codex and Pi review the freeze.
5. No model provider call. No network call in a test or CI. Provider authorization stays
   zero.

## Limits

This report reads revision 2 and the PCBA evidence copy. It made no network call. It changed
no product file.
