# B7/B8 lead design review

Date: 2026-11-14. Basis: proposal revision 3. B6 correction remains the first task.

The independent `pcb-fab-package` skill is the correct scope. A dedicated CLI and bundled copies satisfy the standalone rule. The minor-dimension interpretation for a drilled slot is reasonable. Label it as an interpretation. Do not add a slot-length minimum or a maximum drill diameter.

## Corrections before implementation

1. **Profile meaning.** A schema-valid example is insufficient when its classifications are incorrect. Layer count and prohibited via construction are requirements, not recommendations. Published nominal values and process capabilities are not design margins. Use a small, explicitly validated structure under the existing `extensions` field for these service facts. Keep numeric design limits and recommendations in `limits`. Name all supported extension fields and their evidence. Do not make a generic policy engine.
2. **Complete coverage.** The raw supplier DRC report does not prove the geometric checks or manual conditions. Keep it as an artifact. Add a compact supplier result that lists the applicable conditions, their methods, results, and evidence hashes. Qualification must fail when a mandatory condition lacks a result. Include outline and cutout radii, board dimensions, mask web, conditional silkscreen, via construction, stackup, and quantity. Retain below/at/above tests from the plan.
3. **Effective staged files.** Name the file paths that KiCad actually reads. A generated `supplier.kicad_dru` beside a project named `board` does not establish that KiCad uses it. Hash the effective staged `.kicad_pro` bytes, not only a separate severity summary. Keep generated artifacts as package evidence.
4. **Source review binding.** Bind the review to the release ID, selected profile, and each source page. Include the current review artifact in the package qualification evidence. A stored page match alone is insufficient. The single-layer profile needs both its process statement and the inherited two-layer specification evidence.
5. **Input and output behavior.** Keep invalid records at exit 1, missing prerequisites or unsupported operations at exit 2, and tool failures at exit 3. `review-source` must not contradict the statement that writes stay under `out/`. Define one consistent path policy. Package output must use the accepted atomic publication helper.
6. **Standalone dependencies.** The file list must include the runtime worker and export inspection code that `design` uses. The new skill cannot call the installed PCB skill. A copied recipe can remain identical. Runtime data and instructions must not depend on a repository path.

## Contract decision

The lead accepts an explicit mandatory `fab.supplier_rules` check. Both bare-board and PCBA qualification must include supplier inspection. Keep `design.drc` and `fab.profile_evidence` separate.

The contracts are new, uncommitted development files in this feature. A prior batch acceptance is not a published schema release. The lead authorizes narrow additions to this initial contract and its test builders after reviewer agreement. Retain historical manifests. Update all bundled copies and test them. Do not silently weaken existing qualification tests to make them pass.

The final proposal must show how the new check covers all applicable supplier conditions, not only KiCad DRC. Its input roles must bind the profile, source PCB, effective staged settings, generated rules, toolchain, and applicable release data. The separate source-review evidence must also remain mandatory for qualification.

No implementation starts until the concrete revised interface receives both reviews.

## Source-review clarification

The tool can calculate byte equality and compare structured values. It cannot prove the meaning of arbitrary supplier HTML. Do not add a general website parser.

For unchanged bytes, calculate equality from the retained pages. For changed pages, record the reviewer's observations for each applicable condition, with source, unit, value, and interpretation. Compare those observations with the profile and enforce complete coverage. Keep the reviewer's explicit acknowledgment of unchanged meaning. Label this as manual evidence, not an automatic semantic comparison. A missing observation or a material difference prevents qualification.

This clarification narrows Pi correction 4. The tool determines consistency and completeness. The reviewer supplies the reading of the source.
