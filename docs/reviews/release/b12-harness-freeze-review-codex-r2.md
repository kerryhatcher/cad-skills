# B12 corrected harness freeze review

Date: 2026-11-15 UTC  
Reviewer: `codex-release-dev`  
Branch: `work/release`  
Freeze: `docs/reviews/b12-harness-freeze-claude-r2.sha256`  
Freeze SHA-256: `09e77fa0f2d280f23918f1fd02b8afd5fd557e90b6b147932a1cb2a5897c32a6`

## Result

I recommend acceptance of the corrected harness scope for B-1, B-2, B-3, M-A, and M-B. All 33 listed file hashes matched before and after the focused tests. I found no blocker in this scope.

## Findings

- B-1: Each planned run carries `expected_paths`. R2 runs also carry the task text and its expected owner. Tests examine R1 to R6, explicit, artifact, baseline, and R2 records.
- B-2: Each planned run marks host discovery and host selection as `unavailable`. The host path fields stay null. Scored selection uses host output only. A local file scan does not count as host evidence.
- B-3: Held, unauthorized, and unexecuted records carry `not-executed`. Missing evidence does not become live evidence. Only live records enter the measured table. The execution summary keeps non-executed records separate, and live failures remain in the table.
- M-A: The freeze test requires the workflow, `.gitignore`, source manifest, revision 5 report, harness files, test files, and fixture files. The full 33-entry freeze also includes these required files.
- M-B: The authorized count includes only fixture-ready runs with authorization. A mixed held and ready plan test checks this rule.
- The revision 5 report records the pending `pcba-design` snippet entry for integration. It does not add that entry to the release worktree.

## Local checks

- `uv run tests/test_release_harness.py`: 64/64 passed.
- `uv run tests/test_release_packaging.py`: 25/25 passed.
- `uv run tests/test_skill_packages.py`: 8/8 passed.
- `uv run tests/test_project_io.py`: 11/11 passed.
- `sha256sum -c docs/reviews/b12-harness-freeze-claude-r2.sha256`: 33/33 matched after the tests.

The checks used local fixtures and test stubs. They made no provider calls. Provider authorization stays zero.

## Limits that stay open

The harness has no live provider adapter and no measured filesystem restriction or sentinel read test. Host discovery and selection remain unavailable. The matrix records zero fixture-ready runs and zero authorized runs. These limits do not block acceptance of the corrections reviewed here.

Packaging P-6 and P-7 remain separately accepted at their unchanged hashes, as recorded by the lead. This review does not extend that acceptance to changed packaging bytes.
