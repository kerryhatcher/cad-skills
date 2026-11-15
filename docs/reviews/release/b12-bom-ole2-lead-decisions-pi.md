# BOM OLE2 lead decisions acknowledgement from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: acknowledgement of the lead decisions of 2026-11-15 03:18 UTC on the terms page, the
FAQ GET, and the BOM untracked file. This report writes no product file. It does not commit
and it does not use `git add`. It made no network call.

## 1. Decisions recorded

| Decision | Result |
|---|---|
| Terms and FAQ GETs | Accepted as public source research. Keep honest metadata. No removal claim for a completed GET |
| BOM-only batch | Stays separate |
| Untracked BOM copy | The lead authorizes intent-to-add for the one BOM copy, so the tracked-file exclusion test can run before a commit |

## 2. Effect

1. `git add -N docs/reviews/sierra-source-evidence/BOM-Sample-and-Demo.xls` makes the BOM
   appear in `git ls-files`. It is not a commit and it stages no content.
2. `test_real_distribution_excludes_supplier_copies` can then see the BOM in the candidate
   set and exclude it.
3. The D-1 count stays 17.
4. The terms page and the FAQ GET keep their honest metadata as separate research. They do
   not enter the BOM batch.

## 3. Review plan for the replacement freeze

I will:

1. Verify the freeze file hash and every entry before and after.
2. Reproduce `uv run tests/test_release_packaging.py` at 28 of 28.
3. Confirm the BOM is visible to `git ls-files` through intent-to-add.
4. Confirm the OLE2 code, the three tests, the manifest entry, and the `*.xls` exclusion.
5. Confirm the BOM hash and the local copy.
6. Confirm the harness and tests stay network-free.
7. Report any concrete blocker once, with hashes.

The bigger working-tree visibility question (Option B from
`b12-bom-ole2-git-visibility-pi.md`) stays open for a later decision. It is not part of this
batch.

## 4. Limits

This report reads the decisions. It made no network call. It changed no product file and did
not use `git add`.
