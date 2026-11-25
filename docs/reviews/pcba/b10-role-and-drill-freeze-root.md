# B10 role and drill replacement freeze

Date: 2026-11-15 UTC. Author: skill-dev-lead.

This replacement supersedes the 113-file integrity freeze for the listed files.
The previous records and their accepted results remain history.
The correction authority is `b10-role-and-drill-correction-root.md`.

## Corrections

The shared validator, all current main and PCBA copies, `report.py` and interface section 14 include `board_record` for `asm.test_record`.
Their validator hash is `974c38b93d24fc2a53c8aaab814410abbdb86b58bdf966cbec0e5181cbe169f5`.
The shared negative test omits this role and expects `pkg.check_input_role_missing`.
The new retained evidence includes the full `board.yaml` input hash.

The export path refuses drill settings that the drill comparison cannot examine.
It supports absolute origin, inch units, trailing-zero suppression, four decimal places and separate plated/nonplated files.
It refuses other settings before it calls any tool.
The shared schema rejects a combined file first with `schema.invalid`.
The five other unsupported settings give `export.drill_setting_unsupported`.
The regression test records no tool call for all six refusals.

The final publication gate, hole measurement, BOM policy and test-record comparisons remain unchanged.
No shared schema changed. No physical test result changed.

## Results

- The focused suite passes 106 of 106 tests, exit 0.
- The shared validator suite passes 59 of 59 tests, exit 0.
- All 15 copied files match their recorded hashes.
- The standard package and the full copied validator exit 0.
- The manifest remains `unqualified`: ten checks pass, DRC and stock fail, and supplier rules remain unconfirmed.

The current logs are in `b10-role-drill-evidence/`.
`initial-run.log` records the earlier combined-file test expectation failure.
The product refused that invalid input before a tool call. The corrected test preserves the existing schema precedence.
The lead reran the complete focused suite after this test correction.

The initial run used the previous evidence directory by mistake.
The lead retained that failed run in the new directory and restored the previous focused and copy logs.
The restored hashes match the 113-file manifest exactly. The previous freeze file is unchanged.
The current successful logs have separate paths.

The freeze manifest is `b10-role-and-drill-freeze-root.sha256`.
Both reviewers must examine these same bytes. The lead stops product edits during review.
The shared snippet routing entry remains an integration task.
No commit, push or provider evaluation occurred in this worktree.
