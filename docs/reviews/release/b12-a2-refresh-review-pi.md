# A2 refresh review (Pi)

Date: 2026-11-15. Reviewer: pi-release-dev.

## Verdict

No concrete blocker. The A2 replacement agrees with the accepted scope and the reviewer clarifications.
I kept the frozen files unchanged. I made no product edit and no provider call.

## Freeze check

- `docs/reviews/b12-a2-refresh-freeze-root.sha256` has 502 entries.
- The manifest file hash is `a95a094741386a1091e22afa554cd213bd00112edae16a243dd6208a82af689c`.
- All 502 files hold the recorded bytes. I rechecked the files after the focused suites.
- The B7 source freeze `docs/reviews/b7-completion-freeze-root.sha256` has hash `3f5904c28ba21ee8f09f4c480ff02a439741d59cceacff300ca9925ed0e4a411`.
- The manifest lists the A2 run expectations, the new tests, the evidence logs and all fixture files.

## Nested selector

`tests/eval/check_artifacts.py` `sha256_binding` accepts exactly one selector.

- `key` alone selects a top-level field. The field must be a nonempty string.
- `json_path` alone selects a nested field. The path must be a nonempty list of string keys or nonnegative integer indices. A boolean is not an index.
- Both selectors give an ambiguity failure. No selector gives a missing-selector failure.
- An invalid selector, an absent field or a non-hash value gives a failed comparison. It does not raise.
- The `key` form stays compatible with the A1 expectations and the harness tests.

## Produced report bindings

- `A2-supplier-binding` binds `supplier-result.json` to `supplier-binding.json`.
- `A2-via-binding` binds `via-report.json` to its hash in `supplier-binding.json` `outputs`.
- `A2-corner-binding` binds `corner-report.json` to its hash in `supplier-binding.json` `outputs`.
- The two corner rows share `corner-report.json`.
- All eight `outputs` hashes equal the produced report bytes.

## Three new mandatory rows

The supplier result holds 18 mandatory rows and two recommendations.

- `service.via_construction_prohibited` passes and is mandatory.
- `process.outline_tool_compatibility` passes and is mandatory.
- `process.cutout_tool_compatibility` passes and is mandatory.
- The only mandatory failure is `service.order_multiple`. The quantity stays 5.
- The only mandatory pending row is `silk_line_min_short_text`.
- `status.json` counts 18 mandatory rows and 16 passes.

## Two input replacements

The A2 project differs from the shared template at exactly two input files.

- `board.yaml` selects `oshpark-two-layer` and declares `extensions.fabrication.via_process: standard_through`.
- `manufacturing/supplier.yaml` is a byte copy of the selected profile.
- The external profile copy, the project profile and the skill profile hold the same bytes.
- The profile content hash is `e3f2789d1033aa284750002b6d71798ca2931d079a5fc0d989938bf9d8b172b9`.
- All other input files equal the template.

## A1 and A3

The A1 and A3 fixture bytes agree with the prior accepted freezes.
The shared template is unchanged. The A1 and A3 expectations pass.

## Focused suites

I reproduced the four suites in the integration worktree. The counts agree with the retained results.

- `tests/test_artifact_expectations.py`: 35 of 35 pass.
- `tests/test_artifact_fixtures.py`: 16 of 16 pass.
- `tests/test_release_harness.py`: 65 of 65 pass.
- `tests/test_release_packaging.py`: 34 of 34 pass.

The retained logs in `docs/reviews/release/a2-refresh-evidence/` show the same counts.
The command record shows profile exit 0, design exit 0 and supplier exit 1. The image identity matches the B6 image.

## Notes

- The integrated `AGENTS.md` differs from the B7 freeze. The root record states the separate documentation acceptance. This is not a blocker.
- The A2 matrix section holds 17 run expectations and five fixture expectations.
- Provider authorization stays zero. A3 stays held.

## Handoff

State: the A2 review is complete with no blocker. The frozen files stay unchanged.
The lead commits this batch only after acceptance.
