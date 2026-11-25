# BOM source-path normalization r2 review

Date: 2026-11-15 UTC. Author: `codex-release-dev`. Type: read-only review.

## Freeze and N-4

The four-entry r2 freeze has SHA-256 `407e030d809852f9a5a3d4b1d1a98d977431cb4d008464e0b1c8b38bfceaeb32`.
All four file hashes match. The normalized manifest hash remains `fd415dc58ab60455c022112105905ede674ce389ba26b025ead80651dbee488f`.

`confined_profile()` now checks each absolute path prefix for a symbolic link.
It resolves the candidate and the manifest directory before it reads a profile.
It refuses a candidate outside the resolved manifest directory.
The new tests cover a linked manifest directory and a linked parent. I confirm N-4.

The five profile bindings use paths relative to their skill manifest. The outside-repository test covers this use.
The author and Pi report 32 of 32 packaging tests. Codex did not rerun the suite.
The A1/A2 freeze still has 155 of 155 matching hashes.

## Finding F-1: Correct the new test text to STE

The new symlinked-manifest test docstring starts with the fragment `D-9.` and uses passive voice.
The new symlink failure messages say that the paths “were not refused.” These messages also use passive voice.
Rewrite the docstring and the two new messages with active subjects. Then update the compatibility freeze.
The lead does not require a functional test run for this text-only change.

## Note N-3

The repository-binding test loads the skill manifest. The repository manifest has no profile binding, so N-3 lacks a direct test.
The checker uses the supplied `manifest_dir`. This note does not block the compatibility freeze.

## Limits

This review made no network call and ran no test. It changed no product file.
