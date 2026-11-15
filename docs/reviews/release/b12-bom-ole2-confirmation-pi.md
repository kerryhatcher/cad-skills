# BOM OLE2 correction confirmation from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: confirmation of `docs/reviews/release/b12-bom-ole2-correction-claude.md`. This
report writes no product file. It does not commit. It made no network call.

## 1. Confirmation

I confirm the exact text. K-1 to K-4, K-6 to K-9 are accepted as written. K-5 takes the
`docs/reviews/sierra-source-evidence/` path, as the lead approved. The code change and the
test changes are correct.

## 2. Evidence checked

| Check | Result |
|---|---|
| BOM SHA-256 | `1b486a0a1da968e128cf109bd25e50837c99b5a8f83a490f748a1c1ccb1b769c` matches the PCBA worktree copy |
| BOM magic | The first eight bytes are `d0 cf 11 e0 a1 b1 1a e1` |
| Prior date | The PCBA provenance records the retrieval time as not recorded. `prior_retrieved: unknown` is honest |
| FAQ difference | The release tree FAQ hash is `680bd9c7...`. The GET FAQ hash is `07f7993a...`. The FAQ is not stored |
| OLE2 prefix | `d0cf11e0a1b11ae1` is the correct eight-byte signature |
| Required fields | Both new entries carry `id`, `path`, `retrieved`, `sha256`, `content_type`, `license_state`, `distribution_decision`, and `magic` |
| Exclusion | `docs/reviews/sierra-source-evidence/*.xls` is added. The `*.html` pattern covers the terms file |
| Fixtures | The OLE2 fixture is project-authored. D-7 holds |

## 3. Notes

### N-1 `replaces: none` is ambiguous

PyYAML reads `none` as the string `none`. Use `replaces: []` or omit the field when there
is no replacement. Low.

### N-2 The terms page is an addition beyond the approved scope

The approved scope covers the BOM. The linked terms page is a second GET and a second
stored file. It is consistent with the existing Sierra evidence handling and the K-7
record. The lead should accept the addition. Not a conflict.

### N-3 Confirm the terms markup magic with the test

The `markup` check looks for `<html`, `<!doctype`, or `<head` in the first 4096 bytes. The
stored terms bytes must satisfy it. Run `uv run tests/test_release_packaging.py` and confirm
D-8 does not fire. Low.

## 4. Recommendation

1. Apply N-1 and confirm N-2 with the lead.
2. Implement sections 2 to 5.
3. Run the focused packaging test and the import check.
4. Freeze `docs/reviews/b12-bom-ole2-freeze-claude.sha256` for every changed and new file.
5. Codex and Pi review the freeze. The old P-6 and P-7 freezes stay as history.
6. No model provider call. No network call in a test or CI. Provider authorization stays
   zero.

## Limits

This report reads the correction and the PCBA evidence copy. It made no network call. It
changed no product file.
