# Packaging recheck from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: recheck of the packaging freeze after P-1 to P-5. This report gives the result. It
writes no product file. It does not commit.

## Freeze

The freeze list is now inside the repository:
`docs/reviews/b12-packaging-freeze-claude.sha256`. P-4 is corrected.

| Result | Value |
|---|---|
| Entries | 13 |
| `sha256sum -c` | 13 of 13 OK, exit 0 |

Reproduced results:

| Command | Result |
|---|---|
| `uv run tests/test_release_packaging.py` | 22 of 22 passed, exit 0 |
| `uv run tests/test_release_harness.py` | 37 of 37 passed, exit 0 |

## Correction check

| ID | Correction | Verified result |
|---|---|---|
| P-1 | Require `magic` on every manifest entry | Correct. `check_entries` reports D-2 when the key is absent. The skill manifest now has 10 magic values: `markup` for five HTML pages and `null` for five headers. A test covers a missing key |
| P-2 | Cover `skills/*/supplier/**` and apply the allowlist | Correct. `supplier_sources` uses the wider glob and removes allowlisted paths. A fixture test covers a file outside `pages/`. The real count stays 16 |
| P-3 | Record the Sierra source URLs from `b9-source-addendum-root.md` | Correct. The PDF and workbook URLs are recorded. `url_state` states that the bytes are not verified against the URL, because no supplier contact is allowed |
| P-4 | Retain the freeze list | Correct. The list is in the repository review area |
| P-5 | Say "recorded magic value" | Correct in the finding and the docstring |

The D-8 check now runs for all 16 entries. The D-1 coverage now matches the interface text.

## Harness static test

The freeze includes `tests/test_release_harness.py`. I examined its structure.

- The docstring states "Mock results. No provider call."
- Usage records are injected through a `provider` function. No request is made.
- `test_mock_live_provider_refuses_every_call` and
  `test_mock_no_provider_means_no_call_and_no_success` guard the limit.
- The ceilings, the ledger, the kept failures, the score separation, the claim trace, the
  hard failures, and the git-ignore rule each have a test.
- Every result carries the label `mock`.

The full harness interface review is `docs/reviews/release/b12-interface-review-pi.md`.
This recheck confirms the static suite and the mock separation.

## Verdict

P-1 to P-5 are applied and correct. The packaging check is ready for the combined
reviewer result and lead acceptance. A final standalone release still cannot pass without
the setup fetch path.

## Limits

This recheck ran the local test suites. It made no provider call and no CAD call. It
changed no product file.
