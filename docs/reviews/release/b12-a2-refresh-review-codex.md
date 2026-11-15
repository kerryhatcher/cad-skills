# A2 refresh freeze review

Date: 2026-11-15 UTC.
Author: codex-release-dev, reviewer.

## Scope

I reviewed the frozen A2 refresh against the accepted scope. I read the checker, matrix,
fixture tests, artifact tests, retained run records and retained test logs. I did not edit a
product file or run a test suite. I made no provider call.

## Freeze and hashes

The current freeze has SHA-256
`a95a094741386a1091e22afa554cd213bd00112edae16a243dd6208a82af689c`.
All 502 of 502 entries match. The previous A3 freeze had SHA-256
`7ae60dedf3ca70de0fcb79b4fef9f96a58bf764905fbc9d5d314ea51b116290a`.

| File | Before | After |
|---|---|---|
| `tests/eval/check_artifacts.py` | `cce4810dac35bb80fa9204188088530e41e980cca5495f81c9c229ce7acf9040` | `e71801870ce9d770be42590489cf421428cbe2baf2ca0384912028eaee4700a9` |
| `tests/eval/matrix.yaml` | `f45b261120ea4820dfef3c9f14db41609504299bf40b9d6e4616540460e42fe1` | `7df860ad995b9f401401d352b7f7b1b6eaf0a05cbf62c17d216a7b3c905c5e9a` |
| `tests/test_artifact_expectations.py` | `2c044da8dedf4a1411894f5f1e8a64fb137acb1ef0de91e375228bd1289f26d1` | `cd3ac79cc8e2b44a4f63605be0094318c3fcb1be98c69634c52a7705a9569d4e` |
| `tests/test_artifact_fixtures.py` | `00bac7012eb89ff9140d67806de3e943e60602082a2350c5ea519177cfbac966` | `6a399e28347ecaa59976459c65e3d04e6356cc39775a0657afbf4e87e8e9e367` |
| `tests/test_release_harness.py` | `cdf07c88cc6d65fe5bde01510566484b178d5879e1b8ae97f3e378144e7c5ba1` | `26590dcdb0cc4e699f6ce457a0f627e4d44aef5a30e641595f0fd24660cdafb0` |

The A1 and A3 fixture entries match the prior freeze across 124 entries. The harness
`FREEZE` pointer names the A2 refresh freeze.

## Scope review

The checker accepts exactly one hash selector. It preserves the top-level `key` form. The
nested `json_path` form accepts nonempty string keys and nonnegative integer indices. It
rejects booleans as indices. Missing fields and invalid hash values fail the comparison.
Invalid selectors return a failed comparison without an exception. Focused tests cover both
valid forms, missing and duplicate selectors, invalid types, boolean and negative indices,
missing fields, links and escaping paths.

The A2 project comparison permits only `board.yaml` and `manufacturing/supplier.yaml` to
differ from the template. The test compares the full board text with the specified profile,
service, hash and `via_process` changes. It compares the project profile bytes with the
selected profile copy. It also compares the board hash with the profile's `content_sha256`
field. The shared template remains unchanged.

The A2 matrix has 17 run expectations and five separate fixture expectations. Each run
expectation uses `base: run`. The matrix checks the exact mandatory failure and pending sets,
the absent package, and the three new mandatory rows. Each new row must occur once and pass.
The supplier result binds to `supplier-binding.json`. The nested bindings compare
`via-report.json` and `corner-report.json` with their recorded hashes. Both corner rows use
the one corner report.

The retained supplier result has 18 mandatory conditions. Sixteen pass. The only failure is
`service.order_multiple`. The only pending condition is `silk_line_min_short_text`. The A2
status remains incomplete. The source review and package commands did not run. The retained
test logs report 35 of 35 artifact expectations, 16 of 16 fixture tests, 65 of 65 harness
tests and 34 of 34 packaging tests. I did not rerun them.

## Verdict

I found no concrete blocker. The replacement follows the accepted A2 scope. A1 and A3 stay
unchanged. A2 stays incomplete. Provider authorization remains zero. A3 remains held.
