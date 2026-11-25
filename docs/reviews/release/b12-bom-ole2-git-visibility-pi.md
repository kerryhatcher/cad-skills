# BOM OLE2 git visibility from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: check of the D-1 count change and the one failing packaging test. This report
writes no product file. It does not commit and it does not use `git add`. It made no
network call.

## 1. D-1 count change: 16 to 17 is correct

The new BOM copy adds one stored supplier source.

| Source set | Count |
|---|---|
| Supplier page files under `skills/pcb-fab-package/supplier/pages/` | 10 |
| Sierra evidence files under `docs/reviews/sierra-source-evidence/` | 9 |
| Allowlisted probes (`drill-probe.py`, `drill-probe.json`) | -2 |
| Stored supplier sources | 17 |

The previous count was 16. The D-1 test now expects 17. That is correct. The D-1 check
uses a disk glob, so it sees the untracked BOM.

The BOM hash is `1b486a0a1da968e128cf109bd25e50837c99b5a8f83a490f748a1c1ccb1b769c`. It
matches the manifest and the PCBA copy.

## 2. The failing test

`uv run tests/test_release_packaging.py` gives 27 of 28 passed.

The failing test is
`test_real_distribution_excludes_supplier_copies`:

```text
these supplier entries are not excluded: ['docs/reviews/sierra-source-evidence/BOM-Sample-and-Demo.xls']
```

Cause: the test builds the distribution candidate set from `git ls-files`. The new BOM is
untracked. A query confirms it:

```text
error: pathspec 'docs/reviews/sierra-source-evidence/BOM-Sample-and-Demo.xls' did not match any file(s) known to git
```

The manifest entry is correct. The check cannot see the untracked file in the candidate
set.

## 3. Options for the lead

### Option A: intent-to-add the BOM copy

Run `git add -N docs/reviews/sierra-source-evidence/BOM-Sample-and-Demo.xls`. The file then
appears in `git ls-files`. It is not a commit and no content is staged.

Limit: it touches the Git index. The no-commit rule stays intact. A later `git clean` or an
index reset removes the entry.

### Option B: read the working tree in the test

Change `tracked_files()` in `tests/test_release_packaging.py` to include untracked files:

```text
git ls-files --cached --others --exclude-standard
```

The check then reads the working tree minus ignored files. This matches a work snapshot and
covers every future new supplier copy. It is a test change and needs both reviews.

Limit: the candidate set grows with every new working-tree file. The checks only act on
supplier paths, decisions, and patterns, so the other new files stay neutral. Confirm with a
run of the full packaging suite.

### Option C: commit

A commit makes the file tracked. It violates the lead's no-commit rule before acceptance.

## 4. Recommendation

Option B fits the work-snapshot state and fixes the systemic gap for every new supplier copy.
Option A is the smallest change for this one file. The lead decides. Do not commit before
acceptance.

The freeze waits for the decision.

## Limits

This report reads the working tree and runs one local test. It made no network call. It
changed no product file and did not use `git add`.
