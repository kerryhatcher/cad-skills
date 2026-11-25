# Source retrieval proposal review (codex-skill-dev)

Date: 2026-11-15 UTC. This review covers the revised proposal with tests 1–31. It does not approve implementation.

Proposal hash: `fb9b478a1a817d20c99b5f4383a9119c8fff5f4f9d3df529b8fc23177ebf7b97`.

## Findings

### Blocker: the write failure has no defined exit class

Test 29 injects a local failure before atomic replace and expects exit 3. The exit rules define 3 only for a network error or timeout. They do not define a write failure outcome.

Add a `write failure` outcome and state its exit code. Keep it distinct from a fetch failure, or define exit 3 as a general operation failure and update its name and rule. Test the selected rule. Keep the old-byte and temporary-file assertions.

### Gap: entry outcome priority is not defined

Each entry gets one outcome, but the rules do not define the outcome when multiple conditions apply. A null hash can also have a magic mismatch. A changed hash can also fail the magic check.

Define the evaluation order or report both conditions. Add tests for a candidate with invalid magic and a changed hash with invalid magic. Keep the result and exit code unambiguous.

### Gap: check-only destination validation conflicts with the unused destination rule

The proposal says `--dest` is unused in check-only mode. It also requires a link check on each component of `DIR/<path>`. If a caller gives an arbitrary `--dest` with a linked path, the command can refuse a path that it does not use.

State that check-only mode does not inspect destination paths, while it still validates manifest-relative paths. Add a check-only test with a different destination that contains a symbolic link. Confirm no fetch writes occur and report the expected result.

### Gap: the date check accepts impossible dates

The schema checks that `retrieved` has the `YYYY-MM-DD` form. That form alone accepts values such as `2026-02-30`.

Require a valid calendar date. Add an invalid-date test before any fetch.

## Changes confirmed

The proposal now defines the manifest schema check, skipped-entry results, check-only results, and `exclude-full-copy`. Tests 26–28 cover schema and field defects. Tests 30–31 cover a match with a fetch failure and an all-skipped selection.

The exit precedence covers validation failures, fetch failures, content mismatches, and successful matches. Test 16 pins fetch-failure precedence over a changed result. The proposal also states that the command validates all selected entries before the first fetch.

## Review result

Define the write-failure exit and entry outcome order. Clarify destination checks in check-only mode. Validate calendar dates. Add the focused tests above. No code or tests were changed or run for this review.
