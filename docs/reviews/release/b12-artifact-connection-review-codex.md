# A1/A2 artifact connection review from Codex

Date: 2026-11-15 UTC.
Reviewer: `codex-release-dev`.

## Freeze and file hashes

The freeze `docs/reviews/b12-artifact-connection-freeze-claude.sha256` has SHA-256
`09c052d84cddc4c941992641bbba32158292edf37dfcf5cc8c24adc5cd649559`. All 198 listed files
match. The freeze includes the matrix, all harness modules, the A1/A2 fixtures, and both
artifact tests. The harness test points to this freeze.

| File | Before hash | Current hash |
|---|---|---|
| `tests/eval/matrix.yaml` | `fc07ba25f862026a50b946f4dcbbaf8871b6eafa37f26fa22457b72cba54fbab` | `1b887d25c9d6fb51ac11efd8d92df1e50e938c9841160d84e37a30b5a78d4de5` |
| `tests/eval/check_artifacts.py` | `76031aeeecf8bdf832358f57e0446001c4b6acbff2300e87e8453f3177eadad1` | `9d8fb9dc6bb5f9f2fe9daaebb186cf1608661d91a565fefc7de520fb3b7ee670` |
| `tests/test_release_harness.py` | `02305cde8681c483dcb66bfc088f074447c043e9923d4ad98114bcdab5108db6` | `ddd5e756fab9efe5c54c417e08657c8e24b4b2921b75d85791aa22af3f4e6da8` |
| `tests/test_artifact_expectations.py` | Not listed | `53877b6273da0e5f75fc0fbcf47d917a538e09b77fc7d50a7809a9b23041c235` |

The 155 A1/A2 fixture and fixture-test entries match the prior freeze. No fixture hash
changed. The A1 and A2 roots are explicit. The checker handles array indices, missing keys,
absolute paths, parent paths, linked paths, dangling links, and raw-record hashes.

## Finding F-1: A2 run expectations use fixture status

The A2 matrix reads the order failure and pending condition from the immutable fixture
`status.json`. It checks only the run supplier exit and the absent package path. Thus the run
does not prove those supplier conditions.

I replaced the supplier result in a temporary copy with `{"exit":1}`. The current checks
returned `all_pass=True` with no failed expectations. This reproduces the lead's concern.

## Correction criteria

I agree with the lead's correction and Pi's R-1 to R-12. Add `row_equals` to find exactly
one produced row by key and compare a field. Refuse a missing array, a non-list array, a
non-object row, a missing field, a duplicate match, or a value with a different JSON type.
Check both named conditions and compare the exact mandatory failure and pending sets from
the produced rows. Examine each named row's mandatory flag. Keep fixture `status.json`
checks separate from run `all_pass`. Add the minimal-result regression and the other listed
negative tests. Keep all fixture bytes unchanged. Make one replacement freeze.

I read the frozen supplier rows. The `service.order_multiple` row has `mandatory: true` and
`status: fail`. The `silk_line_min_short_text` row has `mandatory: true` and `status: pending`.
The exact mandatory failure set contains only `service.order_multiple`. The exact mandatory
pending set contains only `silk_line_min_short_text`. These values agree with the requested
correction. I found no conflict or other blocker.

## Verdict

The freeze and its path, array, missing-key, link, and raw-hash checks pass review. Finding
F-1 blocks acceptance of the A2 run expectations until one replacement adds the agreed row
checks. The focused test report says 11 of 11, but I did not rerun a suite. I ran only the
temporary-root reproduction and read the frozen A2 supplier rows. I made no product or
fixture change and made no provider or network call.
