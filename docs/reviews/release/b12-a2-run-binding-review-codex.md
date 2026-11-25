# A2 run-binding replacement review from Codex

Date: 2026-11-15 UTC.
Reviewer: `codex-release-dev`.

## Freeze and hashes

The replacement freeze `docs/reviews/b12-a2-run-binding-freeze-claude.sha256` has SHA-256
`4d250e0a163bdd514b4051fc3e909752c0ae7dcade5f8ddf10ba4b652e170c40`. All 199 entries
match. The freeze supersedes connection freeze
`09c052d84cddc4c941992641bbba32158292edf37dfcf5cc8c24adc5cd649559`.

| File | Before hash | After hash |
|---|---|---|
| `tests/eval/matrix.yaml` | `1b887d25c9d6fb51ac11efd8d92df1e50e938c9841160d84e37a30b5a78d4de5` | `cb70bba9d738294cae42c942807320b1bf78ea5738e51104c89feb50f1ff0528` |
| `tests/eval/check_artifacts.py` | `9d8fb9dc6bb5f9f2fe9daaebb186cf1608661d91a565fefc7de520fb3b7ee670` | `a815593112b48520443372d3377e2c1cfda3b18bb0aea65f6dabdd69d740c5f1` |
| `tests/test_artifact_expectations.py` | `53877b6273da0e5f75fc0fbcf47d917a538e09b77fc7d50a7809a9b23041c235` | `c3b98fd9a4fb10b1ff67d6539b86dd4064da91cd2cff40edfab7ab1371124d81` |
| `tests/test_release_harness.py` | `ddd5e756fab9efe5c54c417e08657c8e24b4b2921b75d85791aa22af3f4e6da8` | `55b247956ae1bbc05d29ee403ee2084b4b30c47478cc7018dd222f06846ac5d8` |

The 155 A1/A2 fixture and fixture-test entries match the accepted fixture freeze. No fixture
hash changed. The harness pointer names the replacement freeze. The focused freeze test
passes and confirms the pointer covers the consumed harness inputs.

## A2 run evidence

The eight run expectations use `base: run`. They read the produced supplier result. The five
fixture expectations read the static status description separately. The run outcome does
not include fixture expectations.

The produced order row has `condition: service.order_multiple`, `mandatory: true`, and
`status: fail`. The produced silk row has `condition: silk_line_min_short_text`,
`mandatory: true`, and `status: pending`. The exact mandatory failure set contains only
`service.order_multiple`. The exact mandatory pending set contains only
`silk_line_min_short_text`. The exit remains 1, and the package path remains absent.

## Correction checks

`row_equals` fails for a missing array, a non-list array, a non-object row, no match, a
duplicate match, or a missing compared field. `row_set_equals` compares the exact typed
multiset for each mandatory status. The checker compares JSON types. Missing keys do not
match `null`.

The focused checks passed:

- `uv run tests/test_artifact_expectations.py`: 23 of 23.
- `uv run tests/test_artifact_fixtures.py`: 16 of 16.
- `uv run tests/test_release_harness.py freeze_lists_every_harness_input`: 1 of 1.

The report from Pi records 65 of 65 harness checks. I did not run that broader harness set.
The minimal-run regression fails its row expectations. The test uses a temporary run root.
No provider or network call occurred.

## Verdict

Finding F-1 is closed. R-1 to R-12 pass review. The A2 rows bind the expected failure and
pending conditions to produced data. The fixture description stays separate. A1 and all
frozen fixture bytes stay unchanged. I found no concrete defect or other blocker.

The known symlink-ancestor limit still applies to the checker root. The normalization
review records this host limit. It does not block this freeze.

I made no product or fixture edit and made no provider call.
