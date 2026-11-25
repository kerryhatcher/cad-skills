# B12 harness freeze review from codex-release-dev

Date: 2026-11-15 UTC.

Scope: review of the 33-entry harness freeze and the separate packaging checks. The harness and packaging results remain separate. This report does not approve provider execution.

## Freeze boundary

The freeze file is `docs/reviews/b12-harness-freeze-claude.sha256`. Its SHA-256 is `21168df2ef2d1d4902883adae8a27896c401f79728d7f9e096ea20aeb82f6d62`.

At the start of review, all 33 listed files matched. After the local test runs, three files no longer matched. The freeze file itself stayed unchanged.

| File | Frozen SHA-256 | SHA-256 after review | Result |
|---|---|---|---|
| `tests/eval/run_case.py` | `59eeb7505cdbbee3b253b0fc11277fbb9c161bf79321e7f8a1d0d43ec2c4950d` | `bbd0ee6202c983e13566c13e370b13b912fdc7ba8ac76d927f41d4c1575f45c9` | Changed |
| `tests/eval/score.py` | `a1f1d160d887c634b3b986c0454dfcbfb1f11392c85de6cf7a6e8e586a6a556c` | `c80b80f73f3ae0cc3607c4d6ac58b0ab25296d7637e9151638b8facb68945c41` | Changed |
| `tests/test_release_harness.py` | `9c1293ac5a70d0651a906cb414e3137caa970c991a0e4322744b09a8a1c64692` | `ff759c0980e3c5871527bda7271b9463390c7f7cafc2430190f5aaf879516617` | Changed |

The other 30 entries matched after the runs. The harness freeze no longer describes the working tree. Review the changed files only after the author makes a new complete freeze.

Claude and Pi reported 53 of 53 harness tests for the frozen version. I ran the harness command after the freeze changed. It found 57 tests and 5 failures. This result does not describe the frozen 53-test bytes. Do not use it as frozen-suite evidence.

## Harness blockers in the frozen bytes

### B-1: Planned runs omit expected paths and R2 owners

The frozen run planner does not attach `expected_paths`. It also does not attach the expected owner or task text from `r2_tasks` to each R2 run. The scorer needs `expected_paths`, so routing cannot score correctly. The R2 boundary is not wired to its run.

Add the expected path list and R2 task text to every planned run. Add local tests that compare each planned run with its expectation. Keep the expected owner outside the prompt.

### B-2: Host discovery and selection are not marked unavailable

The frozen installer records a filesystem scan and filesystem-selected path. It omits host discovery and selection fields. A test also asserts that these fields do not exist. This conflicts with the agreed record interface.

Add host discovery and selection status fields. Set each status to `unavailable` until a host reports the value. Keep filesystem inventory separate. Do not score it as host behavior.

### B-3: Missing evidence can count as live success

The lead's local probe found that a held run enters the measured table. Its missing evidence field defaults to `live`. The scorer then counts S4 and S5 as passes.

Set `evidence: not-executed` on held, unauthorized, and unexecuted records. Set `evidence: live` only after a live host run. Set `evidence: mock` on fixture data. Never default missing evidence to live.

Keep non-executed records in an execution summary. Put only explicit live records in the measured table. Keep measured live failures in that table. Add tests for held, unauthorized, unexecuted, missing, mock, and live records.

### Minor record corrections

- The freeze completeness test does not require the workflow, `.gitignore`, supplier manifest, or matrix revision document. These files appear in the current freeze, but the test does not protect them from omission later.
- The authorized count is all-or-nothing. Count the fixture-ready rows that the lead authorized. Keep the current batch authorization at zero.

## Separate packaging result

The packaging files still match the 33-entry freeze. I ran `uv run tests/test_release_packaging.py`. It passed 25 of 25 tests. The `P-6` test refuses null magic for HTML, PDF, and XLSX content. It permits null magic for plain-text headers.

The `P-7` test detects a full supplier copy at an unrelated path by hash. It does not block a project-authored PDF by file type alone. These results support scoped acceptance of P-6 and P-7. They do not establish final standalone release readiness. The setup fetch path remains necessary.

## Open limits and authorization

The filesystem restriction and sentinel read test are not implemented. The current installer only scans assumed directories. No live provider adapter exists. Authorization stays at zero. No provider call occurred during this review.

## Result

The frozen harness needs B-1, B-2, and B-3 before acceptance. Add the minor freeze-test and authorization-count corrections. Keep packaging acceptance separate. The packaging checks pass for the frozen packaging files.

This report records the 33-file freeze boundary before and after the local runs. It does not accept the changed working-tree files as a reviewed freeze.
