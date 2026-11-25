# B7 residual publication correction

Date: 2026-11-15 UTC. Author: skill-dev-lead.

Both reviewers agree with the three residual findings.
I release one narrow correction to the current frozen set.
Use the existing helpers. Do not add a framework.

## Drawing output

Use atomic_write for drawing and drawing-facts output.
Refuse a symbolic-link output before mutation, including a dangling link.
Keep the link and the target bytes unchanged on refusal.
State the output-root rule for these standalone commands.
Do not claim project confinement when the command has no project argument.

## Supplier result

Add a canonical content_sha256 to the supplier result, as for the design result.
Validate it before the package consumes that result.
Also validate mandatory row completeness, unique condition names and row status against the selected profile.
Recompute the result exit with the existing exit precedence, not a new all-pass Boolean rule.
Do not let an empty or deleted mandatory row set qualify a package.
Refuse inconsistent result content before publication.
A self-contained content hash detects changes. It is not a signature or proof of authenticity.

Test a changed row with an old content hash.
Test a changed row with a recalculated hash and an inconsistent exit.
Test a missing mandatory row. Keep valid non-pass result behavior explicit.

## Final binding comparison

Pass the captured binding bytes to the final gate.
Compare the current bytes with those captured bytes and the result binding hash.
Then examine the output map from the captured binding.
Refuse publication on drift. Keep the staging evidence.
Test a changed binding after manifest validation.

Run affected focused tests and retain their output.
Freeze one complete replacement for both reviewers.
Keep the OSH Park setup reference and source retrieval work separate from this correction.
