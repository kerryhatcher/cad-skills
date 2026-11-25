# B10 combined integrity correction

Date: 2026-11-15 UTC. Author: skill-dev-lead.

Both reviewers completed the 99-file review. The lead releases this combined correction.
Keep the earlier freeze and reviews as history. Preserve accepted behavior outside these defects.

## 1. Final publication gate

Run full validation before the final integrity comparison.
Compare the validated manifest bytes and all staged output paths, hashes, byte counts, file counts, and links immediately before publication.
Repeat input freshness at this boundary. Do not mutate staged files after the final comparison.
The production CLI must not expose the test hooks.
Retain the after-validation copper alteration probe as a regression.
Also exercise manifest alteration, extra or missing output, a staged link, and source drift at this boundary.
Each refusal must preserve prior packages and publish no new package.

## 2. Complete drill reference

Measure all drilled pads and vias from the captured board bytes with an owned worker or the accepted parser.
Include transformed positions, drill dimensions, multiplicity, and plating.
The interface hole list is not proof of a complete board inventory.
Compare the drill exports with the measured board inventory. Keep the interface comparison separate if it remains useful.
Refuse unsupported drilled geometry by its named object. Do not silently omit a slot or a via.
Use the locked image for pcbnew and bind the measured input bytes.
Add cases for an empty or incomplete interface with a drilled board, a missing pad hole, a via hole, and a duplicate drill record.

## 3. Sierra profile compatibility

Use the standard path `manufacturing/supplier.yaml` for the Sierra command.
Use the canonical profile content hash for `board.supplier.profile_sha256`.
Record the full file hash separately in captured input bindings.
Update interface section 2a, command documentation, and owned fixtures to state the same rule.
Do not add a silent fallback to a different profile file.
Demonstrate Sierra and package commands on the same standard-layout project.
Preserve mismatch and freshness refusals.

## 4. Independent BOM comparison

Give the BOM checker the captured supplier policy.
Under `exclude_from_bom`, omit hand-installed references from its expected supplier rows.
Do not remove those references from the neutral dataset, drawing, or test instructions.
Compare the manufacturer as well as the MPN, references, quantity, and DNI value.
Test the valid exclusion policy and a changed manufacturer.
Derive expected rows independently from captured neutral data and policy. Do not call the BOM writer to calculate the expectation.

## 5. Independent test-record comparison

Compare the selected variant and each hand-install instruction with the captured variant data.
Keep the existing comparisons of limits and physical-result claims.
Refuse duplicate item IDs before an item dictionary can discard them.
Test an incorrect variant, changed instruction, missing instruction, and duplicate item ID.
Use named findings. Physical results remain not measured.

## Completion evidence

Run the affected focused tests and retain a full-validator result for the standard project and its new package.
Record the resulting check statuses accurately. An unqualified package can be structurally valid.
Freeze the complete consumed file set once. Both reviewers will examine the same replacement bytes.
The shared snippet routing entry remains an integration task. No shared schema change, commit, push, or provider call.
