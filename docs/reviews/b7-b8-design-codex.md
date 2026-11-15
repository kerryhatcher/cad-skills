# B7/B8 design review: Codex

Date: 2026-11-14 UTC. Paper review of proposal r3 and the two-layer profile example. No implementation or container run was performed.

## Decision

The independent `pcb-fab-package` skill is a sound boundary. It owns supplier-specific checks and package creation. It can read the shared project record layout without importing `pcb-design`. The proposal keeps B6's neutral export work separate and does not silently treat supplier limits as design facts.

The supplier-profile example uses the accepted schema and its stated content hash. The proposed manifest role and required-check additions affect the shared validator, manifest schema, B234 builders, and B6's copied validator and schemas. These are new, uncommitted feature contracts, not a released compatibility promise. I withdraw my earlier request for a new version solely because an earlier batch was accepted. Keep additions narrow, retain historical manifests, update all bundled copies and test builders, and test that old qualified manifests cannot bypass the mandatory supplier check.

## Required corrections before implementation agreement

1. **Prove the staged rule filename is active.** The proposal writes `out/fab/supplier/rules/supplier.kicad_dru`, but KiCad normally finds project custom rules by the project basename. For a staged project named `board`, prove that the CLI loads `supplier.kicad_dru`, or stage the active rules at the filename KiCad reads. Do not accept a passing run until a mandatory below-limit fixture proves the generated rule took effect. Also prove staged severity settings and exclusions affect the actual DRC run.
2. **Separate nominal and policy metadata from rule kinds.** `nominal_board_thickness` uses `kind: recommendation`, while layer count and prohibited via construction also use recommendation. These classifications obscure the difference between service facts, requirements, and recommendations. Published nominal values and process capabilities are not design margins. Put named service facts in a small, validated structure under `extensions`. Keep numeric design limits and true recommendations in `limits`. Do not create a general policy engine.
3. **Complete boundary coverage.** The matrix tests trace, space, annular ring, and drill boundaries, but omits mask web, edge keepout, board minimum and maximum dimensions, and short-text silkscreen limits. Add below, at, and above fixtures for each rule that the skill claims to enforce. Keep slot width as an explicit interpretation of the supplier's phrase, not a stated length limit. The root's accepted minor-width inference is reasonable if the profile and test name that inference.
4. **Bind release and source review.** Bind each review record to the release ID, selected profile, and each source page. Include the current review artifact in package evidence. A stored page match alone is insufficient. The single-layer profile must cite its own process statement and inherited two-layer specification evidence. A harmless live-page change must include review of all material values. Do not impose a universal age limit.
5. **Qualify each applicable condition.** A raw supplier DRC report does not prove geometric or manual conditions. Add a compact supplier result with each applicable condition, method, status, and evidence hash. Qualification must fail when a mandatory condition lacks a result. Include outline and cutout radii, board dimensions, mask web, conditional silkscreen, via construction, stackup, and order quantity. Keep `design.drc` and `fab.profile_evidence` separate.
6. **Use effective staged files and standalone dependencies.** Name the exact `.kicad_dru` and `.kicad_pro` paths that KiCad reads for the staged project. Hash the effective project settings bytes, not only a severity summary. Keep generated rules and settings as package evidence. Include the runtime worker and export inspection code in the new skill. Do not call files from `pcb-design` or use repository paths at runtime.
7. **Align paths and publication.** Keep all writes under `out/`, including `review-source`, or define one consistent path policy. Publish packages with the accepted atomic helper. Keep exit meanings: invalid records exit 1, missing prerequisites or unsupported operations exit 2, tool failures exit 3.

## Focused acceptance cases

- Run a staged project whose basename is `board`. Add a weaker matching project rule, project `ignore` severity, and a source exclusion. Confirm the generated supplier rule still fails the below-limit geometry, and compare source PCB, `.kicad_pro`, and `.kicad_dru` bytes before and after.
- Exercise every claimed numeric DRC or geometry limit below, at, and above its threshold. Test slot minor width at 19.9, 20, and 20.1 mil as the declared inference. Test drill diameter above 250 mil without treating it as a maximum.
- Test four- and six-layer internal clearance with same-net connected copper and unconnected copper. Confirm only the intended connection receives the `hole_clearance` exception.
- Change the profile, stored page, live page, and reviewed limit set independently. Confirm stale or incomplete review blocks qualification; harmless reviewed HTML changes can pass after hash refresh; material changes remain unqualified.
- Remove each mandatory check, evidence record, or applicable output role. Change a published output after qualification. Confirm qualification fails with a clear stale or missing-evidence result.
- Validate the two-layer profile through the copied validator from outside the repository. Confirm the skill copies of schemas and helpers match their sources.

This review does not confirm that KiCad loads the proposed staged filename, that the generated supplier rules work, or that unmeasured PDF exports support a package. The fixed image and listed fixtures must establish those claims before B7/B8 support.

## Source-review clarification agreement

I agree with the lead's narrowed source-review boundary. The tool checks page-byte equality and compares complete structured reviewer observations with profile values, units, and conditions. It does not use a general HTML semantic parser or claim machine proof of changed-page meaning. A reviewer records changed-page meaning as manual evidence with its source, reviewer, and acknowledgment. A missing observation or material difference blocks qualification. All other corrections in this review remain agreed.

## Revision 4 review

Date: 2026-11-14 UTC. I measured `b7-b8-proposal-claude-r4.md` at SHA-256 `0a9a289ef39a1333cea8a37849c3b62769b1e6ef11bacac98a46ec9ab2258f93`. This is a paper review. No implementation or container run was performed.

R4 addresses several prior points. It names the effective `board.kicad_dru` and `board.kicad_pro` files, binds their staged bytes, adds a per-condition supplier result, binds source review to release/profile/pages, uses structured observations without an HTML parser, lists standalone worker and export copies, and adds boundary cases. It also marks the slot minor-dimension rule as an interpretation. I agree with those design changes.

Two corrections remain before I agree to the concrete interface:

1. **Slot-capable inspection.** R4 bundles `board_inventory.py` as a byte copy of the B6 worker. That worker refuses slots. The proposal also assigns slot width to a geometric test, but the stated supplier flow cannot reach that test if inventory rejects the board first. The new skill must own a slot-capable derivative or a separate geometric worker. It must not call the installed B6 skill. Add a slot fixture that reaches the supplier result and tests minor width at 19.9, 20, and 20.1 mil.
2. **Mask web evidence.** R4 says the mask-web condition uses a geometric test that reads the saved board setup. A saved setting does not measure actual solder-mask geometry. Inspect the generated mask openings and board features, or classify the condition as manual evidence with an explicit method and evidence. Do not report a geometric pass from the setting alone.

The role list in r4 uses names present in the accepted manifest role set, and the new supplier-rule check is a narrow initial contract addition. The mandatory `fab.supplier_rules` check must bind the board, profile, export settings, effective staged rule and project files, toolchain, and supplier result evidence. Keep output completeness tied to the exact existing output-role schema and applicable export layers. Unsupported PDF commands can remain a temporary post-B6 trial gate, with packages that require them unqualified until measured.

The source-review design is acceptable if each selected profile page has a stored and live hash, and the observation file covers every required profile value, unit, and condition with reviewer evidence. Changed-page meaning remains manual evidence. A missing observation or material difference blocks qualification. For the single-layer profile, bind both its process statement and the inherited two-layer specifications.

**Decision:** I agree with r4's direction, but not the complete interface until the two corrections above appear. The fixed image must prove the effective rule and settings files are active, prove the mask method, and run the listed boundary fixtures before B7/B8 support. B6 remains the higher-priority review.

## Revision 5 focused design verdict

Date: 2026-11-14 UTC. I measured `b7-b8-proposal-claude-r5.md` at SHA-256 `32c77100a31010be95d2d84ad5165ac8c5481e140a4f3c6612bc73f5693cd045`. This is a paper review. No B6 tests were repeated.

R5 resolves the earlier slot-capable inventory concern in the proposed file set and adds an owned slot inspector that compares board geometry with Excellon slot records. It also moves mask inspection from the saved mask-web setting to exported mask geometry. I agree with those directions, with the bounded corrections below.

1. **Mask precision and resource bounds.** A 0.25 mil raster plus boundary uncertainty cannot establish separate decisions at 3.9, 4.0, and 4.1 mil. The uncertainty equals or exceeds the 0.1 mil spacing. Define an error interval. If the interval crosses the 4 mil limit, return indeterminate or unsupported, never pass. Use vector geometry or bounded local refinement. Set explicit limits for region dimensions, candidate count, local raster area, and memory. Do not rasterize a whole board at fine resolution. A measured renderer is preferable to a partial Gerber parser.
2. **Complete mask geometry.** Flashes and regions alone do not define all possible Gerber geometry. Account for strokes, aperture shapes, macros, polarity, and regions that the exporter emits. Refuse unsupported constructs and state the unsupported result. Do not silently omit them. Preserve separate results for fused openings and actual remaining mask web.
3. **Slot comparison tolerance.** Derive endpoint tolerance from measured export units and coordinate precision. The B6 3:3 mm Excellon output uses 0.001 mm increments. Compare endpoint pairs without regard to order. Preserve multiplicity and plated class. Define angle behavior for near-circular slots. Test values near the derived tolerance, not only a 1 mil mismatch.
4. **Exit policy.** R5 gives invalid slot and mask inspection inputs exit 2, but the accepted CLI policy assigns malformed or invalid records exit 1. Keep exit 2 for invocation errors, missing prerequisites, unsupported operations, and runtime mismatch. Invalid records exit 1. Tool failures remain exit 3.
5. **Prerequisite trial and file provenance.** Before support claims, run temporary-copy probes in the existing image. Test effective rule filename, severity, exclusions, slot records, mask geometry, and PDF commands. Keep B6 files unchanged. Record commands, exits, input and output hashes, resource use, uncertainty, and unsupported cases. Name an existing source for every byte copy. `export_inspect.py` extracted from `pcb.py` is an owned derivative, not a byte copy of a separate source file.

**Decision:** I agree with the r5 direction, but I do not accept its current mask uncertainty and resource bounds, slot matching tolerance and semantics, or exit 2 classification for invalid records. Use an interval result that cannot pass across the limit, and refuse unsupported Gerber constructs. The existing-image trials must record uncertainty and resource use before support claims. No implementation or container work was performed.

## Revision 6 focused verdict

Date: 2026-11-14 UTC. I reviewed `b7-b8-proposal-claude-r6.md` and `b7-prereq-trials-claude.md` on paper. The r6 proposal hash is `ac16757204992f5fb61110232ffc252c8b38d71160eeeeeaf3a40854409502f5`. The trial record hash is `312ec6ea3fb6b00e8992aa4d8f3f0fb75cce24e88093717e6ccb43b291e84814`. I ran no tests or container commands.

R6 improves the mask decision by making uncertain results block qualification and lists unsupported Gerber constructs. The trial record measures the active `board.kicad_dru` name, severity override, slot record format, and PDF commands. It explicitly says the exclusion format and exact mask-distance code remain unmeasured. It gives only 16-character output hash prefixes and abbreviated trial descriptions, not a frozen full evidence set or complete command and input/output hash record.

One combined narrow correction list remains:

1. **Fix contradictions and exit meanings.** The global table assigns invalid records exit 1, but `supplier` assigns invalid profiles exit 2. Set invalid profile, observation, and record errors to exit 1. Keep exit 2 for invalid invocation, missing prerequisites, unsupported constructs or operations, and runtime mismatch. In the mask matrix, a 4.0 mil result cannot pass if its error interval crosses the limit. Mark it `uncertain` unless the measured interval proves the web is at least 4 mil.
2. **Correct the mask error bound and resource limits.** The `RoundRect` macro combines polygon, circle, and vector-line primitives. The inspector's conversion introduces curve approximation error. Gerber coordinate precision alone does not bound that error. Measure the conversion error and combine it with coordinate and distance-calculation error. Define bounded local work, input dimensions, object count, memory, and run time. Return `uncertain` when the combined interval crosses the threshold. Preserve explicit refusal for unsupported apertures, strokes, regions, or polarity.
3. **Correct dimensions and restore retained cases.** A 16 by 22 inch board means width maximum 406.4 mm and height maximum 558.8 mm. Test both axes at their own below, at, and above values. Restore the accepted internal-clearance cases, edge keepout, short-text silkscreen, outline/cutout radii, via construction, and order-quantity cases. The r6 table must not drop previously agreed checks.
4. **Complete prerequisite evidence.** Measure the source-exclusion behavior in a temporary staged project, including an applicable exclusion that would hide the supplier violation. Record full command lines, exits, complete input and output hashes, and a frozen evidence manifest. Keep the abbreviated hashes only as display text. Record the measured error and resource bounds for mask inspection. Do not claim exclusion behavior from the format-agnostic clearing plan alone.

**Decision:** r6 is not ready for design acceptance until these corrections appear. The bounded trial scope is suitable, but the retained record does not prove source-exclusion behavior or a complete reproducible evidence set. The lead accepted this combined correction scope. Claude will test a pinned existing parser in a temporary environment and preserve full trial evidence. B6 remains accepted and unchanged.

## Revision 7 bounded review

Date: 2026-11-14 UTC. I reviewed `b7-b8-proposal-claude-r7.md` and the 78-entry `b7-prereq-evidence.sha256` manifest. The r7 file still has the title “revision 6.” The evidence manifest measures `b87e6f328462fc653e77ddb08cb316283ec258a845c8a219c5682a9506b79219`; all 78 entries passed hash verification. No B6 tests were run.

R7 restores the separate width and height bounds and the previously missing clearance, edge, silkscreen, outline, via, and quantity cases. It uses the board-derived slot plated class and unordered endpoint matching. These points resolve earlier review findings.

The remaining bounded corrections are:

1. **Correct version and exit text.** Change the title to revision 7. In `review-source`, an unknown observation key and an observation path escape are invalid records. Give them exit 1, not exit 2. Keep exit 2 for bad command arguments, missing prerequisites, unsupported operations, and runtime mismatch.
2. **Bind manual geometry evidence through existing roles.** Do not represent a mask Gerber as an input role such as `cad-skills/evidence`. Write the manual observation as a report artifact with its Gerber hash inside the report. Use existing `report` and `evidence` roles. Keep `fab.supplier_rules` and its required input roles in the role table. `fab.py` must validate the report's referenced Gerber hash against the actual manifest output hash before qualification.
3. **Make source review omission-proof.** Include the source-review record as mandatory package evidence. The package gate must reject a missing record, changed review bytes, altered observations, changed release/profile/page hashes, or a live page that differs from the reviewed hash. Add omission and tamper cases.
4. **Restore the five-profile source/value table.** R7 points to the old two-layer example, which is schema-valid but semantically superseded. Include the five profile values and each source page, including source nominal values with separate rounded metric labels. Bind both pages for the single-layer profile. Do not treat schema validation as semantic profile validation.
5. **Keep slot plating independent.** Derive plated class from the board slot attributes, then compare it with the plated and non-plated export files. Do not infer class from whichever file contains the slot. Preserve multiplicity and reject a class swap, missing record, or duplicate.

**Decision:** R7 is close, but I do not accept the interface until these five corrections appear. The 78-entry trial evidence is hash-verified. Its presence does not replace full commands and artifacts for any unmeasured source-exclusion or mask behavior. B6 remains accepted and unchanged.

## Fabrication drawing content agreement

I agree with the minimal content and review requirement in `b7-pdf-review-root.md`. The measured one-page PDF proves export execution only. It does not satisfy the existing mandatory fabrication drawing role because it lacks release identity, dimensions and units, stackup, and fabrication notes. Require a current hashed drawing with board and release identity, dimension units, overall dimensions, holes, selected stackup, and supplier process facts. A generated sheet or supplied drawing can meet this condition. Review its expected content and render the example. Do not qualify an arbitrary non-empty PDF. No general PDF parser is necessary.

## Revision 8 focused verdict

Date: 2026-11-14 UTC. R8 measures SHA-256 `8ff1da0d452902edfc8bc93129ce26e27d861340fb5a5c75deba813be83e09e5`. The 195-entry evidence manifest is `b7-prereq-evidence-r8.sha256`, SHA-256 `2ef5503dd2fc86c2e300536e3c75b74a9c88e8e6031de87d819fb524827773d9`. I verified all entries from `docs/reviews`; all 195 passed. The manifest paths are relative to that directory.

The 0.000501 mm slot endpoint tolerance is supported by the measured 0.001 mm coordinate increment: at most 0.0005 mm rounding per coordinate plus 0.000001 mm numeric margin. This is a per-coordinate comparison bound, not a whole-pair Euclidean distance. The source-review omission/tamper gate, manual geometry report role, board-derived slot plating, fabrication drawing content, separate width/height limits, and retained acceptance rows are present in r8.

Four profile-table corrections remain:

1. Replace `fab` labels with the schema scope value `fabrication`.
2. Process capability fields must not say `margin, process`. Keep them in the named process extensions, with no claim that their `limits.scope` is `margin`.
3. `service.layers` for the single-layer service must say two copper layers, because the supplier uses its two-layer fabrication process.
4. Keep source nominal units and values in the profile table for board dimensions and thickness. The source-stated inches and mil values must remain visible beside separately rounded metric labels. Do not store only the converted metric display values.

The 250 mil statement is correctly treated as a note, not a limit or recommendation. Keep the no-maximum statement and larger milling tolerance note distinct. The evidence manifest includes copied scripts and trial artifacts, but the command record still abbreviates some invocations with ellipses. Those are not complete command logs and do not make the abbreviated commands independently reproducible. Keep the manifest as byte-integrity evidence, and provide complete command lines for any claim that depends on exact invocation details.

**Decision:** I agree with the r8 interface direction and measured tolerance. I need the four profile-table corrections above before full interface acceptance. I ran no tests or containers. B6 remains accepted and unchanged.

## R8 plus errata interface agreement

I agree with r8 together with `b7-r8-errata-root.md` as the implementation interface. The errata resolves the four profile-table corrections and defines physical layer and order-multiple values as integers. The 0.000501 mm slot tolerance is accepted. Test an endpoint coordinate difference exactly at 0.000501 mm as a match and 0.000502 mm as a mismatch, per coordinate. Retain board-derived plating class, coordinate conversion, unordered endpoint matching, and multiplicity checks.

The implementation must refuse qualification for unsupported macros, overlapping clusters, and unsupported constructs. Test these product refusal paths during implementation. They do not delay implementation start. Provide complete executable commands with explicit paths for the accepted trials. The current abbreviated command record is insufficient. Do not repeat unrelated tests.
