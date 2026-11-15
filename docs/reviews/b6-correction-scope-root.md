# B6 final correction scope

Date: 2026-11-14. Basis: the final Codex and Pi reviews and `b6-root-review.md`.

Keep the original final manifest and record as history. Claude remains the implementation author. This correction does not expand the supported design tools.

1. **Manual review coverage.** Enforce coverage on read and write. Add `prior_interface_sha256` to the small skill review record. Use a full hash or `null`. Preserve the prior interface bytes before replacement. With a hash, read the preserved file and compare its hash before calculating changed pointers. With `null`, require all top-level keys. A missing or altered named prior file fails. Update the template and the record documentation. Do not add a contracts-registry schema.
2. **Automatic evidence.** Read the prior board and predeclared expectation files. Compare their bytes with the full recorded hashes. Validate the expectation record. Missing or altered evidence makes readiness fail with exit 1. Keep exact interface-byte binding.
3. **Staging.** A residual staging directory is `staging.residual`, exit 1. An empty staging parent is not a defect. Preserve published failure records. Remove only the current operation's disposable staging directory.
4. **Assertions.** Reject duplicate JSON keys and prohibited identifier characters. Use whole-string identifier validation. A number outside the supported simulation measurement range gives `assertion.malformed`, exit 1. Do not let a numeric conversion raise a traceback. Keep the general contract parser's integer behavior unchanged.
5. **Prose and records.** Correct the known-actor passive sentences, semicolon, and long sentences in the new skill prose. Examine technical-term lint findings individually. Correct the blind-via claim and the statement about unavailable STE tools. Include the retained independent 1 ms RC result.

Use the same strict record parsing on both interface evidence paths. Duplicate keys must not silently replace fields. Apply the agreed full-string hash rules to the local records.

## Focused acceptance cases

- Manual record with only `/thickness_mm`, no prior interface: exit 1.
- Manual record omits a changed pointer from the preserved prior interface: exit 1.
- Complete manual coverage with valid current hashes: pass.
- Missing or altered named prior interface: exit 1.
- Missing or altered prior board or expectation file: exit 1.
- Valid automatic evidence with unchanged files: pass.
- Residual staging directory: exit 1. Empty staging parent: no staging finding.
- Duplicate assertion key, measurement with final newline, or excessive numeric value: exit 1 without traceback.
- Duplicate interface-evidence key or malformed hash: exit 1 without a false ready result.

Run the affected B6 tests and package-copy tests. Do not repeat the agent trials or unchanged mechanical suites for these repairs. The retained RC probe already passes the independent target.

Freeze a replacement manifest and correction record. Both reviewers must accept the corrected files before B6 completes.

## Final narrow runtime and package correction

Pi reproduced a remaining native-runtime defect. Codex agrees with the correction. Native simulation must not execute a missing KiCad tool during version measurement. Apply the operation-specific rule to preflight and report publication. A missing required tool gives exit 2 without a traceback. Test native simulation without KiCad and native ERC without ngspice.

Both reviewers agree with the template inclusion correction. The template's preserved interface JSON currently matches the general `out/` ignore rule. Use a template-only exception, or remove the dependency and prove initialization without it. If the exception is selected, re-ignore unrelated children at each parent level. Test the required JSON and unrelated output files. Do not broadly include generated output directories.

The earlier 41-test suite passed. Run the affected runtime and package tests for these final changes. Do not repeat that suite without a new reason.
