# Source retrieval proposal review (codex-skill-dev)

Date: 2026-11-15 UTC. This review covers the revised proposal and tests 1–41. It does not approve implementation.

Proposal hash: `1c744e1d569954bae8006d4f69592902449f676c2e42ab0c1e402a5c806cc430`.

## Finding

### Clarify the accepted `none` status

The proposal defines `none` as a magic status when the entry uses `magic: none`. It says this status can write when the hash matches. Test 34 also expects a successful write.

The next sentence says the exit contribution is 1 when either status is “not ok.” This wording can make `none` fail, even though the proposal accepts it. State the rule with exact values: exit contribution 1 when the hash status is `candidate` or `changed`, or when the magic status is `mismatch`. A hash status of `match` with magic status `ok` or `none` can write and contributes 0.

Also replace “Each selected entry gets one outcome” with wording that says the command reports both the hash status and the magic status. The proposal now defines both statuses, and tests 40–41 cover the combined cases.

## Changes confirmed

The current proposal hash matches the hash in the author message. Tests 40–41 require both statuses for changed or candidate bytes with invalid magic. These tests address my prior finding about multiple content failures.

## Review result

Clarify the accepted status formula and the report fields. No code or tests were changed or run for this review.
