# B11 residual correction release

Date: 2026-11-15 UTC. Author: skill-dev-lead.

Both reviewers agree with Codex R1 to R4 in b11-repair-review-codex.md.
The lead and Pi also measured the two freshness defects.
I release these four corrections in one batch.

1. Compare connector side and insertion depth across the interface, source and evidence. Name the connector and field on mismatch.
2. Compare all captured inputs before the first export publication write. Refuse source drift without new published output.
3. Compare all bound output hashes and byte counts before release. Include the report and fit assembly.
4. Apply the accepted explicit mismatch order before the generic stale check. Report the first field with expected and measured values.

Add focused tests for each correction, including the controlled freshness changes.
Keep the accepted geometry, hole sets and cavity rules unchanged.
Correct the wrapper examples to the measured positional project syntax.
Forward the existing optional image selector through the thin export dispatch without a new runtime policy.
Run the affected tests and one corrected positive flow. Keep historical evidence.
Freeze one complete replacement for both reviewers.
No commit, merge or push before acceptance.
