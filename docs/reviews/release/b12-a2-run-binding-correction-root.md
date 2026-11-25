# A2 result correction

Date: 2026-11-15 UTC. Author: skill-dev-lead.

The current artifact connection does not establish the expected A2 result.
Pi measured `all_pass: true` for a run that contains only `{"exit": 1}`.
The immutable fixture description cannot prove the behavior of a new run.

## Correction scope

1. Read the order failure and the pending silk condition from the produced supplier result under the run root.
2. Keep the fixture description in separate fixture tests. Do not include it in the run outcome.
3. Add `row_equals` with explicit array path components, a named selector, and a field comparison.
4. Refuse a missing array, an incorrect array type, a missing match, or more than one matching row.
5. A missing field fails even when the expected value is null. Preserve JSON types in comparisons.
6. Compare the mandatory failure and pending sets from the produced rows with the expected named sets.
   The order condition is the only mandatory failure. The short-text silk condition is the only mandatory pending condition.
7. Examine the mandatory flag for both named conditions. Do not infer the flag from the condition name.
8. Keep the exit-1 and exact package-absence expectations.

The focused regressions cover the minimal result, missing and duplicate rows, incorrect status or mandatory flags, and an unexpected mandatory failure.
The retained A2 result must pass. Use temporary copies for negative cases.
Preserve A1 and all fixture bytes. Keep the accepted path and link refusals.

The author can implement this correction after Codex completes its current frozen review.
Include any concrete finding from that review in one combined replacement.
Do not start another review of changing files. Retain the old freeze and make one complete replacement freeze.
Provider authorization stays zero.
