# OSH Park setup documentation freeze review (codex-skill-dev)

Date: 2026-11-15 UTC. This review covers the documentation replacement freeze only. It does not cover source retrieval.

Freeze record `docs/reviews/oshpark-setup-documentation-freeze-claude.md` has SHA-256 `5c93bcc2dfcf3ecffd79bdc0f02458b0c8eb493e389c0c33da066ae89f0e51e7`. All seven entries in `docs/reviews/oshpark-setup-documentation-files.sha256` pass.

## Finding

### Update the stale release state in the coverage report

The frozen coverage report still says the setup text and source manifest are proposed and not installed. It also says to write the setup text in a later documentation batch. The new freeze says the reference is installed and the proposal copy stays as history.

Update the coverage report to state the current release state. Keep any remaining measurements as open items, and remove the old action to write the setup text. The coverage report is part of this freeze, so its release status must match the other frozen files.

## Corrections confirmed

The setup reference separates supplier constraints from repository enforcement. It removes the generic safety claim for margin direction. It states the 5 mil silkscreen value and the profile's separate 3 mil manual check. It does not claim that the profile check proves compliance with the 5 mil value.

The reference keeps the profile and export contract unchanged. The coverage report removes the per-font record rule. The `SKILL.md` command text separates project outputs from standalone drawing outputs and describes the link check at `--out`.

The retained test log reports 8 of 8 skill package checks passed. This review did not run tests.

## Review result

Correct the stale release state in the coverage report, then freeze the corrected documentation set again. No product code or profile changes are part of this review.
