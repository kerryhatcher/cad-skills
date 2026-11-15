# B234 final design review: Codex

Date: 2026-11-13.

Proposal: `docs/reviews/b2-b4-proposal-claude.md`, revision 2.

Proposal SHA-256: `f559354968d135603cc45e437dc87610778f2bf185a68e2ba45a0577c3e1bdf9`.

**Decision: narrow corrections remain**

I agree with the combined batch structure and the earlier repairs. Three small interface corrections remain below. They need no evidence engine or other framework.

**F1: outline outputs need a layer**

Section 3.2 permits `layer` only for copper, mask, silk, and paste. The mandatory-output table also maps outline by layer. These rules contradict each other.

Permit and require `layer` for `outline` as well. Define its value as the export entry's `kicad_layer`. Apply the same mapping, suffix, and duplicate rules as other layer outputs.

Test a valid outline mapping, an absent outline layer value, and an incorrect outline layer value. Preserve the missing-inner-layer and exchanged-layer tests.

**F2: passed manual evidence needs inputs and an artifact**

Section 3.6 makes inputs and an artifact mandatory for tool evidence only. Reviewer and date alone cannot support a passed manual check. Section 6 already expects both input hashes and an artifact hash for qualification.

For either method, a passed evidence record must identify the applicable inputs and one artifact. Match their paths and exact-byte hashes against the manifest and project. Keep reviewer and date mandatory for manual evidence. Tool evidence still needs its tool identity.

Use this minimum constant table for passed checks:

| Check ID | Mandatory input roles |
|---|---|
| `design.erc` | `schematic` |
| `design.drc` | `board` |
| `design.parity` | `schematic`, `board` |
| `fab.profile_evidence` | `supplier_profile` |
| `fab.export_inventory` | `board`, `export_settings` |
| `fab.layer_order` | `board`, `export_settings` |
| `fab.drill_split` | `board`, `board_interface`, `export_settings` |
| `asm.bom_consistent` | `parts`, `variants`, `board_record` |
| `asm.placement_rotation` | `board`, `parts`, `variants` |
| `asm.variant_agreement` | `board_record`, `variants`, `parts` |
| `asm.stock_dated` | `parts`, `board_record` |
| `asm.test_record` | `board`, `parts`, `variants` |

Infer each evidence input's role from its matching manifest path. Do not accept an unrelated input because its hash is correct. For `parts`, include all selected manifest inputs with that role. Other mandatory fixed-path roles identify one project file each.

For `fab.profile_evidence`, retain the comparison between the artifact bytes and the supplier profile's `evidence_sha256`. A byte match establishes identity only.

Minimum tests:

- Reject passed manual evidence with only reviewer and date.
- Reject a passed check with an unrelated, correctly hashed input.
- Reject parity evidence that identifies only one of its two mandatory inputs.
- Reject a missing mandatory assembly input role.
- Accept complete manual and tool evidence under the same input-role table.
- Reject changed artifact bytes and stale applicable input hashes.

This table establishes record consistency. It does not establish tool execution or circuit correctness. Keep those limits explicit.

**F3: reconcile incomplete-package rules**

Section 3.2 permits incomplete draft and unqualified packages. Its finding table still lists `pkg.no_outputs` and necessary-input absence without a qualification condition. The named tests expect a draft with those gaps to pass.

Apply mandatory-input, mandatory-output, and mandatory-check completeness rules to `qualified` only. Draft and unqualified records can omit them. Validate the structure, paths, hashes, sizes, and evidence consistency of all items that a record lists.

Test an incomplete draft and its identical contents under `qualified`. The draft passes these completeness rules. The qualified record fails. An empty or incorrectly hashed listed output fails in either state.

**Agreed remainder and scope**

The revised PCB hash ownership, separate schematic and board-record hashes, control-character rules, replacement boundary, and source-scoped tests address the earlier findings. The copy-run limitation and deferred container job are explicit.

For drill omission, pair each role with its matching condition. A check-based exception must reference passed `fab.drill_split` evidence. An interface-based exception must agree with the plated-hole classification. This is a direct condition check.

Keep these corrections as constant tables and ordinary validation functions. Preserve B1 behavior and its fixed-byte hashes. Component-reference coverage, tool execution, and physical acceptance remain later work.

I changed only this report. Final design agreement remains pending incorporation of F1–F3.

**Combined final interface — explicit agreement**

I agree with the root's combined interface: Codex F1–F3 plus Pi N4–N5, with the clarifications below.

- Use the Codex required-input-role table above exactly.
- Permit and require `layer` for outline outputs.
- Require applicable inputs and an artifact for passed manual and tool evidence.
- Keep reviewer and date mandatory for manual evidence.
- Apply completeness rules only to qualified packages. Validate listed items in all statuses.
- Bind drill-check exceptions to passed `fab.drill_split` evidence and matching conditions.
- State failure boundaries before and after rename for `publish_dir`. Limit cleanup promises to handled failures.
- Skip external URLs, anchors, and fenced examples in the reference scanner. Remove fragments from local link targets before path validation.

These choices settle the earlier corrections. No design conflict remains. Claude can apply these exact changes to the proposal before implementation. No other design change or framework is necessary.

This agreement concerns the interface. Implementation acceptance still needs frozen hashes, code review, and test results. I changed no implementation files.
