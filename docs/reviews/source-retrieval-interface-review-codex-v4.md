# Source retrieval proposal review (codex-skill-dev)

Date: 2026-11-15 UTC. This review covers the revised proposal and tests 1–37. It does not approve implementation.

Proposal hash: `d91247a96767e61396246a00856ce389489ca2cf28792397f0e1f2950cc96de2`.

## Finding

### Gap: the entry outcome order is not defined

The proposal says each entry gets one outcome. A response can have a hash that differs from the manifest and fail the magic check. A null hash can also have a magic mismatch. The proposal does not say which outcome the command reports in either case.

Define an evaluation order or report both conditions. Add tests for a changed hash with invalid magic and a null hash with invalid magic. Keep the reported outcome and exit contribution clear.

## Changes confirmed

The proposal now defines schema and field validation before fetch. It rejects invalid calendar dates. It defines local write failures and post-replace failures. It also defines skipped and check-only results, non-2xx responses, and `exclude-full-copy` behavior.

Tests 29–30 cover pre-replace failure and a successful write followed by fetch failure. Test 33 covers a post-replace durability failure. Test 35 covers a separate check-only destination. Test 36 covers an impossible date. These changes address my previous findings.

## Review result

Define the outcome for responses that fail more than one content check. Add the two focused tests above. No code or tests were changed or run for this review.
