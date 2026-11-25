# B11 repair review: Codex

Date: 2026-11-15. Reviewer: codex-mechanical-dev.

Scope: the 28 files in `docs/reviews/mechanical/b11-repair-batch.sha256`, the retained repair run, the accepted interface, and the lead resolutions.

**Decision: not accepted.** The manifest and positive flow pass. The accepted repair rules still have connector-frame and publication gaps.

## Manifest, tests, and positive flow

The manifest SHA-256 is `f618d854b1b44f2a16af7baa9625380b3e1d5761d8737730802b49844373dfdb`. All 28 listed files match.

I ran the four announced suites:

- `uv run tests/test_mechanical.py`: 46 tests pass.
- `uv run tests/test_mechanical_fit.py`: 43 tests pass.
- `uv run tests/test_skill_packages.py`: 8 tests pass.
- `uv run tests/test_project_io.py`: 11 tests pass.

I generated a fresh fixture and ran export, fit, and release through `pcb.py mechanical`. All commands exited 0. Geometry and fit passed.

The lower contract test count does not by itself show that accepted coverage disappeared. The current tests cover transform, stackup, evidence, exclusions, missing references, path escape, stale input, report status, roles, comparison completeness, unsupported drill records, real exports, and route actions. The controlled freshness cases and connector-frame consistency remain uncovered.

## Required corrections

### R1. Check the interface connector side and insertion depth

The interface connector frame has `side` and `insertion_depth_mm`. The source frame and component evidence also have these values. The code uses source and evidence values for the proxy and insertion box. It does not compare them with the interface frame.

I changed the interface frame to `side: bottom` and `insertion_depth_mm: 8.0`. The source and evidence stayed `top` and `4.0`. Export and fit both passed. C06 and C07 also passed.

This is the side and insertion-depth gap that Pi reported. Compare the interface frame with the source and evidence before export. Refuse a mismatch and name the connector and field.

### R2. Recheck captured inputs before export publication

`run_export` uses captured bytes for the export. It does not compare the live inputs with the captured hashes before it publishes the files and export record.

I changed the live board after the first KiCad export command. `run_export` returned success. Its recorded board hash did not match the live board hash. The lead and Pi reproduced this gap with a change after the drill command.

Compare every consumed input with the captured hashes before the first output write. If an input changed, refuse and name it. The lead evidence is in `docs/reviews/mechanical/b11-freshness-review-root.md`.

### R3. Recheck the report and fit assembly before release publication

`run_release` checks the report and fit assembly, then makes another input capture. Its final output loop checks the export files only. It does not check the report or fit assembly again before it writes the release record.

I changed both files during the final capture call. `run_release` returned success. The live hashes did not match the report and release hashes. The lead measured the same gap. The lead report lists the recorded and current hashes in `b11-freshness-review-root.md`.

Before release publication, recheck every bound output and its byte count. Include the report and fit assembly. Refuse a mismatch and name the output.

### R4. Apply the accepted mismatch order before the generic stale check

`run_release` runs `first_stale` before `release_first_mismatch`. The first helper uses the `CAPTURED` order, which starts with the board. It can prevent the accepted release-field order from running.

I changed both the board and `release_id` in a temporary fixture. The refusal named `board.kicad_pcb`. The accepted order compares `electrical_release_id`, then `release_id`, then the board hash.

Compare the explicit expected fields in the accepted order first. Then report the first mismatch with its field name and expected and measured values.

## Dispatch documentation

The `pcb.py mechanical` route works with a positional project path. Direct `mechanical.py check` uses `--fixture DIR`. Its other commands use `--project DIR`. The reference prose says each command uses `--project`, but its wrapper example uses a positional path. The run log also describes the wrapper with `--project DIR`.

Keep the working wrapper syntax. State that the direct module uses `--project DIR`, and that `pcb.py mechanical` takes a positional path.

## Resolved items

I confirm these accepted corrections in the frozen batch:

- The Excellon export uses separate PTH and NPTH files with the accepted roles.
- The real slot and oval cases refuse. Excluded holes require a position, positive diameter, plated flag, and nonblank reason.
- The C09 cavity uses the outward offset and has no mating-edge exemption.
- The connector body length is separate from insertion depth and comes from project-authored evidence.
- The required component set, duplicate-result rules, and empty-report refusal work.
- Captured bytes, image ID use, confined record paths, release fields, and output byte counts match the accepted rules.
- Export, fit, and release run through the `pcb.py mechanical` wrapper.

I did not change a file in the 28-file batch. My probes used temporary fixture copies. The review file is outside the manifest.
