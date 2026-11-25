# B11 residual batch review: Codex

Date: 2026-11-15. Reviewer: codex-mechanical-dev.

Scope: the 21 files in `docs/reviews/mechanical/b11-residual-batch.sha256` and the residual run log.

**Decision: I agree. The batch resolves N1 and R1 to R4.**

## Manifest and tests

The manifest SHA-256 is `2f264b6790010a58e5771fbb62ee2542c725528ac05bc344baa002fd31a82204`. All 21 files match.

I ran these focused suites:

- `uv run tests/test_mechanical.py`: 55 tests pass.
- `uv run tests/test_mechanical_fit.py`: 43 tests pass.
- `uv run tests/test_skill_packages.py`: 8 tests pass.
- `uv run tests/test_project_io.py`: 11 tests pass.

The public command help shows a positional `path` and an optional `--image` argument.
Pi reports a fresh export, fit and release through the public command. Each command exited 0.

## Residual corrections

- Connector side and insertion depth now match across the interface, source and evidence. The focused tests name `CN1` and the mismatched field.
- Export compares captured inputs before its first publication write. Its controlled drift test refuses and publishes no output.
- Release compares bound output hashes and byte counts before publication. The gate includes the report and fit assembly.
- Release compares explicit fields in the accepted order before the generic stale check. Pi's probes name `release_id` and `board_sha256`.
- The wrapper takes a positional project path and forwards `--image` to export. The reference documents the command form.

The geometry, hole sets and cavity rules remain unchanged. The test count is 55, which restores the prior accepted contract coverage and adds the residual cases.

## Minor run-log note

The run log says a changed `release_id` names `mechanical/fixture-source.json`. The measured refusal names `release_id`. The test `test_release_id_change_names_fixture_source_first` also has a misleading name. The tested behavior follows the accepted order. Correct these descriptions in a later released batch.

I made no changes to the frozen files. My review report is outside the manifest.
