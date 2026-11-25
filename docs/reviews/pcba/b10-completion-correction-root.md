# B10 combined correction release

Date: 2026-11-15 UTC. Author: skill-dev-lead.

Both reviewers confirm the six points in `b10-completion-scope-root.md`.
The lead releases one combined correction under the accepted interface section 14.

The retained root probe published an unqualified package with exit 0.
The full copied validator then returned exit 2, with missing inputs, missing evidence roles and path mismatches.
Evidence: `b10-package-validation-probe-root.py` and `b10-package-validation-probe-root.json`.

1. Capture all necessary project records and use the accepted project paths and profile-hash rules.
   Validate the project and the complete staged package, not only individual record structures.
   Missing prerequisites must not produce a package that fails its listed-evidence checks.
2. Implement ERC, parity and profile-evidence checks for supplied inputs. Use pending only for an absent or explicitly unmeasured input.
3. Derive expected exports from captured export settings. Compare missing and extra files independently.
   Compare drill coordinates, multiplicity and plating with a captured board inventory. Header text alone cannot establish this result.
4. Capture the toolchain and settings. Resolve the local image identity, compare it with the lock, and run that identity.
   Never pull an image. Use the necessary captured project settings for tool runs.
5. Validate all staged bytes and counts. Then repeat input freshness immediately before publication.
   Add controlled source drift during staged writes and final staged-output alteration tests.
6. Compare assembly evidence with captured parts, variants and board limits.
   Refuse missing test steps. Generate the selected variant's assembly drawing with DNP marks.
   Keep physical measurements unmeasured and supplier conventions unconfirmed.
7. Correct the record's stock claim. The current fixture has insufficient LED stock and the stock check fails.
8. Retain a complete standard-layout fixture and a full validator result for the generated package.
   Include the listed independent negative cases from section 14. Preserve prior packages on failure.

Use owned code and copied local helpers. Do not import another skill at runtime.
Do not change shared schemas. Keep accepted neutral and Sierra behavior closed except for necessary shared call-site compatibility.

Complete the correction, run focused tests, and freeze one complete batch for both reviewers.
Keep all earlier records. Do not edit the replacement during review.
