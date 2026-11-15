# Test-record role and drill settings correction

Date: 2026-11-15 UTC. Author: skill-dev-lead.

Both reviewers accept the five integrity corrections. Two findings remain.
The lead releases this narrow correction. Keep the 113-file record as history.

1. Add `board_record` to `asm.test_record` in the shared validator, all current copies, `report.py` and interface section 14.
   Add a shared negative test that omits this role from the evidence.
   The expected finding is `pkg.check_input_role_missing`. No schema changes.
2. Refuse drill settings outside the accepted Sierra format before any export.
   The supported format uses absolute origin, inch units, trailing-zero suppression, four decimal places and separate plated/nonplated files.
   This is the existing accepted export contract. Do not claim another origin or zero format works with the current drill comparison.
   Name the unsupported setting with `export.drill_setting_unsupported`.
   Add focused refusals for board origin, leading-zero suppression, decimal coordinates, millimeter units, another precision and a combined drill file.

The package gate, measured hole inventory and accepted assembly comparisons stay unchanged.
Regenerate the retained evidence to bind `board.yaml` to the test-record check.
Run the affected tests. Freeze one replacement for both reviewers.

## Existing schema precedence

The shared schema already sets `drill.separate_files` to `true`.
Thus a combined file refuses first with `schema.invalid`. Keep this existing validation order.
The five other unsupported settings use `export.drill_setting_unsupported`.
All six refusals occur before a tool call. No shared schema change is necessary.
