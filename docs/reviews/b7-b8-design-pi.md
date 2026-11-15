# B7/B8 design review: Pi

Date: 2026-11-14.

**Decision: the independent `pcb-fab-package` boundary is sound. The proposal is not ready for implementation. Nine corrections are necessary. I agree with Codex corrections 1 to 5 and add four points.**

I read the proposal and the profile example on paper. I ran one host check: `contracts/validate.py` on the example (status pass), and the canonical content hash equals the stored `632546c36b3a0647210a1de813cac340ee8a265527ef8ef5b761a292bde773eb`. No implementation, container run or broad research was done.

## 1. Reviewed bytes

| Item | Value |
|---|---|
| Proposal r3 | `docs/reviews/b7-b8-proposal-claude-r3.md`, `bfddf334dde597425542efb1fb458244013c874277e90625be5423eb187d4676` |
| Profile example | `docs/reviews/b7-b8-two-layer-profile-example.yaml`, `f7f1b55bc34485c0994ed58c359827cc18a3aa15ca3ed59f46fca7c5f9ab5c1b` |
| Supplier schema | `contracts/schemas/supplier-profile.schema.json` |
| Codex review | `docs/reviews/b7-b8-design-codex.md` |

## 2. Independent skill and cross-batch effects

The skill owns supplier-specific rules and the package. It reads the shared record layout without importing `pcb-design`. This is the correct boundary. The profile uses the accepted schema and the example hash verifies.

The cross-copy change is large. Adding a check and two roles changes `contracts/validate.py`, the manifest schema and README, and every skill that carries a copy. The B6 copy test requires equality, so `skills/pcb-design/contracts/` and `skills/pcb-design/scripts/validate.py` change. The B6 final manifest `b6-final-files.sha256` is then stale. The B6 reviewers must accept a B6 replacement manifest before B7 lands. The B234 builders and `tests/test_pcb_tools.py` expectations change. The B234 qualification behavior changes: a package without `fab.supplier_rules` becomes unqualified. This is a deliberate behavior change and must be tested with an old manifest.

## 3. Schema, roles and version

- Add `supplier_rules` and `supplier_settings` to the **inputs** role enum in `manifest.schema.json`. The outputs enum is separate and must not change. The evidence schema has no role enum, so it needs no change.
- `fab.supplier_rules` in `BARE_CHECKS` changes qualification. Test an old qualified manifest without the check: it must now be unqualified, not a silent pass.
- Version: the contracts are new uncommitted feature files, not a released compatibility promise. A narrow addition to this initial contract is authorized under review. Do not require a new version solely because an earlier batch was accepted. Keep the old-manifest behavior test: a package without `fab.supplier_rules` is unqualified, not a silent pass. Update every bundled copy and test it.
- The `fab.supplier_rules` evidence inputs are `board`, `supplier_profile`, `export_settings`, `supplier_rules`, `supplier_settings`. Confirm the validator's evidence rule enforces them.

## 4. Evidence and source-review binding

- The profile `evidence_sha256`/`content_sha256` bind the stored page. Good.
- Retain the live page bytes so the tool can compare the stored and live bytes. The tool computes the page byte equality. A hash alone is not evidence.
- For a changed page, the reviewer supplies a structured observation for each checked limit: the observed value, unit and condition, with the source, reviewer and acknowledgment. The tool compares each observation with the profile value, unit and condition. A missing observation or a material difference blocks qualification. No general HTML semantic parser.
- The changed-page meaning stays explicit manual evidence. It is not machine proof.
- Do not impose a universal age limit. State the project or profile policy.
- **Single-layer provenance.** The single-layer limits come from the two-layer page, but the profile `evidence_sha256` is the single-layer page. The single-layer page has no table. Bind the two-layer page as the value source and the single-layer page as the process statement, or point the limit `source_url` to the two-layer page with its hash. State the inference.

## 5. Exact qualification completeness

Name the exact required artifacts and roles for a bare-board qualified package: every enabled copper, mask, silk, outline and drill output; the `design.*` and `fab.*` checks; `fab.supplier_rules`; the profile evidence; the current source review; the manifest. A `pending` check never qualifies. The schematic PDF and fabrication drawing commands are not measured. Classify them as measured prerequisites or unsupported until the commands pass. The `NECESSARY_INPUTS` set does not include the two new roles, so the `fab.supplier_rules` evidence must carry them; confirm this in the validator.

## 6. Full boundary coverage

The matrix covers trace, space, annular ring, drill, slot and internal clearance. It omits mask web, edge keepout, board minimum and maximum dimensions, and the short-text silkscreen limit. Add below, at and above fixtures for every rule the skill claims to enforce, including the same-net and unconnected internal-copper cases. The root accepts the slot minor-width reading as a stated inference with the 20 mil value. Keep that inference in the profile and name it in the test. Do not treat the 250 mil note as a maximum diameter.

## 7. Rule interpretation and staged filenames

- KiCad finds project custom rules by the project basename. The proposal writes `out/fab/supplier/rules/supplier.kicad_dru`. Name the staged project basename and the exact `.kicad_dru` filename that the CLI reads, or place the generated rules at that name. Prove with a mandatory below-limit fixture that the generated rule took effect. A passing run alone does not prove it.
- The severity mapping is in the `.kicad_pro`. Name the exact field and prove that a project `ignore` severity and a source exclusion cannot hide the supplier rule. The `supplier-settings.json` is a record, not the effective setting.
- State the exact KiCad mechanism for each `kicad_dru` entry. `mask_web_min` may be a board setup setting, not a custom rule. Move it if the custom rule cannot enforce it.
- The `hole_clearance` and `inner` selectors are correct. Do not use `physical_hole_clearance` where a same-net connection must pass.

## 8. Profile metadata and units

The example uses `kind: recommendation` and `scope: margin` for nominal and process metadata:

| Key | Current kind/scope | Correct treatment |
|---|---|---|
| `nominal_board_thickness`, `copper_layers`, `copper_weight`, `substrate` | recommendation / fabrication | Nominal stackup metadata. Put in `extensions`, not `limits`. |
| `mask_alignment_max`, `drill_size_tolerance_*`, `drill_position_tolerance_*` | maximum or recommendation / margin | Process capability. Put in `extensions` as documented evidence, not a CAD-measured limit. |
| `via_construction` | recommendation / fabrication | Hard supplier refusal. Not a recommendation. |
| `order_multiple` | recommendation / fabrication | Hard order rule. Not a manufacturing recommendation. |
| `max_drill` | recommendation / fabrication (text) | Tolerance note. Put in `extensions`. |

Keep the true recommendations (the 5 mil silkscreen and the 5 mil overlapping-drill clearance) and the hard design limits in `limits`. Do not use `recommendation` or `margin` to disguise nominal or process metadata. The schema `extensions` object is the correct place for the clearly separate metadata.

**Units and source nominal.** The example stores the board dimensions and the thickness in the rounded mm only. It loses the source nominal (0.25 in or 250 mil, 16 in by 22 in, 63 mil). Keep the source nominal and the rounded metric label separately, as the earlier preparation correction requires.

## 9. Corrections

1. Prove the staged rule filename and severity are active with a below-limit fixture (Codex 1).
2. Move nominal and process metadata to `extensions`; keep only actionable recommendations (Codex 2, strengthened).
3. Complete the boundary matrix: mask web, edge keepout, board min/max, short-text silk, internal clearance (Codex 3).
4. Retain the live page bytes; compute the stored/live page byte equality and compare the complete structured reviewer observations (value, unit, condition) with the profile. A missing observation or a material difference blocks. The changed-page meaning is manual evidence, never machine proof. No HTML semantic parser. Bind the single-layer value source (Codex 4, narrowed).
5. Name the exact qualified artifacts and roles; a pending check never qualifies; classify the unmeasured PDFs (Codex 5).
6. Keep the old-manifest behavior test. The narrow contract addition is authorized; no version bump is required for the uncommitted feature files.
7. Accept the B6 replacement manifest that the copy change requires.
8. Keep the source nominal and the rounded metric label for the dimensions and the thickness.
9. State the slot minor-width inference in the profile and the test.

## 10. Limits and verdict

This is a paper review. The fixed-image KiCad runs and the staged-rule proof are not done. The proposal is not ready. With corrections 1 to 9, the boundary is sound. No implementation or container run was made.

## 11. Root review reconciliation

Date: 2026-11-14.

I read `docs/reviews/b7-b8-design-root.md`, SHA-256 `43f54cac66a16a2a183f2335c103696f42fb5ce64092ee1c10ad4ba89e50aac6`. I agree with its contract decision and its six corrections. They overlap my corrections and add three points.

**Contract decision.** The mandatory `fab.supplier_rules` check is accepted for bare-board and PCBA qualification. Keep `design.drc` and `fab.profile_evidence` separate. The contracts are new uncommitted feature files. The narrow additions are authorized under review. Retain historical manifests. Update every bundled copy and test it. Do not weaken an existing qualification test to make it pass. I withdraw the version-bump recommendation in section 3 and correction 6. Keep the old-manifest behavior test.

**Root 1, profile meaning.** I agree. Requirements such as the copper-layer count and the prohibited via construction are not recommendations. Published nominal values and process capabilities are not design margins. Use a small, explicitly validated structure under the existing `extensions` field. Keep the numeric design limits and the true recommendations in `limits`. Name every supported extension field and its evidence. No generic policy engine.

**Root 2, complete coverage.** I agree. The raw supplier DRC report is an artifact, not a proof of the geometric and manual conditions. Add one compact supplier result that lists each applicable condition, its method, its result and its evidence hash. Qualification fails when a mandatory condition lacks a result. Include the outline and cutout radii, the board dimensions, the mask web, the conditional silkscreen, the via construction, the stackup and the quantity. Retain the below/at/above tests. This extends my section 6.

**Root 3, effective staged files.** I agree. Name the exact file paths that KiCad reads. Hash the effective staged `.kicad_pro` bytes, not only a separate severity summary. Keep the generated artifacts as package evidence. This extends my section 7.

**Root 4, source-review binding.** I agree, with the narrowing. The tool computes the stored/live page byte equality and compares complete structured reviewer observations with the profile values, units and conditions. A changed-page meaning stays explicit manual evidence with source, reviewer and acknowledgment. It is never machine proof. A missing observation or a material difference blocks. No general HTML semantic parser. Bind the review to the release ID, the selected profile and each source page. Include the review artifact in the qualification evidence. The single-layer profile needs both its process statement and the inherited two-layer specification evidence.

**Root 5, input and output behavior.** I agree. Keep invalid records at exit 1, missing prerequisites or unsupported operations at exit 2, and tool failures at exit 3. `review-source` must not contradict the statement that writes stay under `out/`. Define one consistent path policy. The package output uses the accepted atomic publication helper. I add this to my sections 4 and 5.

**Root 6, standalone dependencies.** I agree. The bundled file list must include the runtime worker and the export inspection code that `design` uses. The new skill must not call the installed PCB skill. The copied recipe may stay identical. Runtime data and instructions must not depend on a repository path. I add this to my section 2.

B6 repair remains the first priority. No implementation was done.

## 12. Revision 4 addendum assessment

Date: 2026-11-14.

I read `docs/reviews/b7-b8-r4-addendum-claude.md`, SHA-256 `bdb3fb38127ec17c2b41015c74014a150a4e9072845d38fd658bd878c8a39783`. I agree with the three notes, with one concrete addition for the slot export inspection.

1. **Slot-capable derivative.** I agree. One separately owned worker version, a byte copy of the B6 worker with the one owned change (slot and oval drills are read, not refused), named in the skill manifest. The B6 worker stays unchanged and keeps refusing slots. The derivative has a slot fixture and the 19.9/20/20.1 mil minor-dimension matrix. Support needs a fixed-image run of the derivative.
2. **Mask web is not mask geometry.** I agree. The saved setting is a parameter, not the actual geometry. The supplier result gives the mask-web condition the method `geometric_test`, not `setup_read`. Until the geometric method is measured, the row is `pending` and a package that needs it stays unqualified (exit 1). The acceptance matrix row applies to the measured method. Add: name the geometric method (the mask openings, the minimum web distance, the tolerance) before the row can pass.
3. **Git inclusion.** I agree with the negation chain and the scratch-repo test. The table covers the required template file, a sibling non-json, a nested path, the repository `out/`, and another project `out/`. Confirm the real `.gitignore` change and the real-repository check in the replacement manifest.

**Addition: slot support must reach the export inspection.** The B6 `excellon` parser in `pcb.py` accepts only `T<d>C<dia>`, `T<d>` and `X<int>Y<int>`. It does not parse a slot route or the slot endpoints and orientation. The B7/B8 package must validate the slot in the drill file: the count, the minor and major dimensions, the endpoints, the orientation and the plated class. Require one real slot export fixture from the fixed image that reaches the package inspection (`supplier`, `design`, `package`), not only the inventory or the minor-width check. The inventory derivative handles the slot; the export inspection then needs the bounded slot parsing. No general Excellon parser. This is missing from the addendum.

**Source review.** Confirm that the source review stays mandatory in the qualification evidence, with an omission test and a tamper test. The addendum does not change it.

No implementation, container run or broad research was done.

## 13. Revision 5 verdict: mask raster and slot export

Date: 2026-11-14.

I read `docs/reviews/b7-b8-proposal-claude-r5.md`, SHA-256 `32c77100a31010be95d2d84ad5165ac8c5481e140a4f3c6612bc73f5693cd045`. I agree with the overall structure: the independent skill, the owned slot-capable derivative, the mask geometry inspection beyond the saved setting, the mandatory source review, and the path and exit policy. Five bounded corrections are necessary. The proposal is not ready for implementation until they are made and the prerequisite trial passes.

### C1. The 0.25 mil raster cannot decide the boundary cases

The mask web limit is 4 mil. The boundary cases are 3.9, 4.0 and 4.1 mil, a 0.1 mil separation. A 0.25 mil cell plus one cell for the boundary has an error of about 0.25 to 0.5 mil, larger than the separation. The method cannot reliably decide 3.9 against 4.0 against 4.1.

Correction: measure the exact minimum distance between the two opening contours (vector geometry), or use a raster cell and a proven error bound smaller than 0.05 mil. State the error bound. If neither is practical, test only the 4.0 mil limit with a stated tolerance band and do not claim the 3.9 and 4.1 decisions.

### C2. Bound the whole-board raster cost

A 0.25 mil raster over a 40 by 25 mm board is about 24 million cells per layer. A larger board grows without limit. Correction: restrict the computation to the neighborhoods of the openings (their bounding boxes) or use the vector distance. State the cost budget and the maximum supported board.

### C3. State the supported Gerber constructs and refuse the rest

The method covers flashes (`D03`) and regions (`G36`/`G37`). It omits draw strokes (`D01`), aperture macros (`%AM` and a flash that uses the macro), and clear polarity (`%LPC`). I checked the retained B6 mask export `examples/pcb-trial/results/final_r2/export/trial-F_Mask.gbr`: it has one `%AMRoundRect` macro and `RoundRect` apertures with `D03` flashes, and no `D01`, `%LPC` or `G36`/`G37`. The macro shape is already needed, so the parser must resolve the macro aperture or refuse it.

Correction: name the supported aperture forms (`C`, `R`, `O` and the measured macro form) and refuse an unsupported aperture, a `D01` stroke, a `%LPC` clear polarity or an unhandled region with a named finding. Add one negative fixture for each unsupported form. Do not silently ignore a construct.

### C4. The slot endpoint tolerance is too large for the export quantum

The Excellon export is 3:3 mm, so the endpoint quantum is 0.001 mm, about 0.03937 mil. The proposed 0.5 mil endpoint tolerance is about 12.7 quanta. Correction: set the endpoint tolerance to one or two export quanta (about 0.04 to 0.08 mil) and state it in both units. Test the endpoint boundary at the quantum. Keep the orientation tolerance and test it at 0, 45 and 90 degrees.

### C5. Invalid records stay exit 1

The r5 exits give `inspect-slots` and `inspect-mask` "2 invalid". The agreed table gives exit 1 for an invalid record and exit 2 for incorrect invocation, a missing prerequisite or an unsupported runtime. Correction: a malformed board, drill file, mask file or profile is exit 1. Exit 2 stays for the invocation and prerequisite cases. Align both inspections with the agreed table.

### Practical prerequisite trial

Before implementation, run one focused fixed-image trial with temporary copies. Do not repeat a B6 test.

1. Export a mask Gerber from a small board with two known pads. List the exact constructs used: apertures, macros, flashes, regions, strokes and polarity. Measure the minimum web vectorially from the exported geometry.
2. Export an Excellon file from a slot board. Read the `G85` records, the tool records and the measured export quantum.
3. Read the KiCad `.kicad_pro` field names for the rule severities and the solder-mask web setting.

The trial decides the vector or raster method, the supported constructs and the slot tolerance. Record the board, the commands, the outputs and the hashes.

### Agreement on the rest

I agree with the `merged_opening` distinction: the inspection sees the export, so a merged opening is not a manufacturing web failure unless an explicit supplier rule requires separate openings. I agree the source review stays mandatory. I agree the metadata belongs in `extensions`. No implementation, container run or broad research was done for this verdict.

## 14. Root r5 findings reconciliation

Date: 2026-11-14.

I read `docs/reviews/b7-b8-r5-review-root.md`, SHA-256 `d1ed871ffa4f86053c071b8fe1d00fc9ab49652248a4e6251e5f2ab37cca81c5`. I agree with the root's five corrections. They match my C1 to C5, with four additions. The r5 proposal is not ready for implementation until the combined corrections and the prerequisite trial pass.

- **Root 1, exit codes.** Agree. An invalid record stays exit 1. Exit 2 is only for an absent prerequisite or an unsupported operation. The two new command rows that say `2 invalid` are wrong. This is my C5.
- **Root 2, interval uncertainty and resource bounds.** Agree. Add: the inspection must state the measurement error bound, and a result whose interval crosses the limit must not claim a pass. It must not allocate a full-board fine raster without a resource bound. Prefer vector geometry or a bounded local refinement near the openings. This extends my C1 and C2.
- **Root 3, constructs and the renderer.** Agree. Add: a measured existing renderer is preferable to an incomplete new parser. If no renderer is measured, report an explicit unsupported or manual result, never a partial parse. The supported aperture forms, strokes, macros, polarity and regions must each be named, and an unsupported construct refused with a named finding. This extends my C3.
- **Root 4, slot tolerance, multiplicity and plating.** Agree. Add: derive the slot tolerance from the measured export units and coordinate precision. The current 3:3 mm output has 0.001 mm increments. Compare the endpoint pairs as an unordered set, so the endpoint order does not matter. Preserve the slot multiplicity and the plated class (plated or non-plated) in the match. Define the angle behavior for a near-circular slot, where the orientation is ambiguous. This extends my C4.
- **Root 5, byte-copy sources.** Agree. The file list must name an existing source for each byte copy. The B6 export checks live in `pcb.py`. A new `export_inspect.py` extracted from `pcb.py` is an owned derivative, not a byte copy of a separate file. Record its source and its owned changes, like the slot-capable inventory derivative. This is a new correction.

**Prerequisite trials.** Agree. Use temporary fixtures and the existing image. Keep the accepted B6 files unchanged. Measure the active rule filename, the severity settings, the source exclusions, the slot records, the mask geometry and the PDF commands. Record the commands, the exits, the input hashes, the output hashes and each explicit unsupported case. The trials do not establish package qualification. Full implementation follows the combined interface agreement.

No implementation, container run or broad research was done for this reconciliation.

## 15. Revision 6 verdict and combined narrow correction list

Date: 2026-11-14.

I read `docs/reviews/b7-b8-proposal-claude-r6.md` (`ac16757204992f5fb61110232ffc252c8b38d71160eeeeeaf3a40854409502f5`) and `docs/reviews/b7-prereq-trials-claude.md` (`312ec6ea3fb6b00e8992aa4d8f3f0fb75cce24e88093717e6ccb43b291e84814`). I agree with the root contradictions. One combined narrow correction list follows.

1. **Invalid profile exit code.** The `fab.py supplier` row says `2 invalid profile`. The r6 exit table itself gives exit 1 for an invalid record, and `fab.py profile` already uses 1. Correct `supplier` to exit 1 for an invalid profile. Exit 2 stays for a missing page or argument, an unsupported selector or construct, and a runtime or image mismatch.
2. **`RoundRect` error bound.** The retained `RoundRect` macro is not a single polygon. It combines the outline primitive (4), four circle primitives (1) and four vector-line primitives (20). The macro geometry is exact. The error bound concern is the inspector's own approximation: if the inspector converts the rounded corners to a polygon, it must bound the resulting chord error. Prefer the exact primitive decomposition (circles and vectors), or state the polygon approximation error and prove it is below the resolution the mask limit needs. Do not attribute an inherent segmentation error to the macro. State the bound for each supported aperture form. The prerequisite trial uses a pinned existing Gerber parser in a temporary environment; record its version, source and measured error bound.
3. **At-limit mask row.** Under the r6 rule, a pass needs the exact distance to exceed the limit by more than the error bound. A web exactly at 4.0 mil does not, so it is `uncertain`, not pass. Correct acceptance row 10: 3.9 fails, 4.0 is `uncertain` and blocks, 4.1 passes. Row 11 already states the uncertain rule. Keep the two rows consistent.
4. **Board maxima.** The source is 16 in by 22 in, so the maxima are 406.4 mm and 558.8 mm. Acceptance row 7 gives 406.4 for both. Split it: width at 406.3 / 406.4 / 406.5 mm, height at 558.7 / 558.8 / 558.9 mm.
5. **Restore the concrete r4 cases.** The r6 matrix omits the plated-drill-to-internal-copper cases (same-net at 0 mil passes, unconnected at 9.9 fails and 10 passes), the edge keepout 15 mil, the short-text silkscreen 3 mil and recommended 5 mil, the outline and cutout concave radii, the via construction refusals (blind, buried, filled-and-plated), the order quantity multiple of three, the maximum drill above 250 mil (no maximum), the board minimum 6.35 mm, and the overlapping-drill recommendation. Restore these rows with below, at and above where a numeric limit applies. Keep the section 4 limits and extensions. No new features.
6. **Trial record as evidence.** The trial record gives only first-16-character hashes and abbreviated commands. Replace them with the full 64-character SHA-256 of each input and output and the full command line with every flag and path. Freeze the output files with a manifest. The record alone is not a frozen evidence set.
7. **Source and exclusion override proof.** Add one measured fixture with a real source `drc_exclusions` entry. Confirm that the staged `board.kicad_pro` clears the exclusion, that the supplier rule still applies, and that the source file keeps its exclusion. Record the command, the exits and the full hashes. The trial measured the basename and severity but not the exclusion format.

The retained concrete cases are otherwise correct: the slot unordered endpoint pairs, multiplicity and plated class, the near-circular rule, the unsupported mask constructs (`G36`/`G37`, `D01`, `%LP C`, other macros and apertures), the `merged_opening` distinction, the mandatory source review, and the qualification gate. No implementation, container run or broad research was done for this verdict.

## 16. Revision 7 verdict and bounded remaining corrections

Date: 2026-11-14.

I read `docs/reviews/b7-b8-proposal-claude-r7.md` (`fd5eac361a941f19fcbbef57a2ac4f9546797de07b6798cacb0659936379135e`) and `docs/reviews/b7-prereq-evidence.sha256` (`b87e6f328462fc653e77ddb08cb316283ec258a845c8a219c5682a9506b79219`, 78 entries, 78 of 78 `OK`). The r7 addresses my earlier combined corrections: the `supplier` invalid-profile exit is 1, the board width and height maxima are split, the at-limit mask row is `uncertain`, the restored rows 23 to 32 are present, the `RoundRect` method is the exact Minkowski form, and the source-exclusion behaviour is correctly measured negative and not claimed. Six bounded corrections remain. No new features.

1. **Title and history.** The title says "revision 6". It must say "revision 7". The first paragraph says the paper replaces revisions 4 and 5. It also consolidates revision 6. Correct the title and the replaced list to name r6, r5 and r4 (and the addendum).
2. **`review-source` exit codes.** An unknown record key and a path escape are invalid records. They must be exit 1, not exit 2. The section 3 row says `2 invalid arguments or unknown key`. Section 13 says `A path outside its root is exit 2`. Change both to exit 1 for the invalid record, the unknown key and the path escape. Exit 2 stays for invalid arguments, such as a missing flag, and for a missing prerequisite.
3. **Mask Gerber as an evidence input.** Section 14 lists the mask Gerber in the `inputs` of an `evidence` record. The mask Gerber is a manifest output, and the evidence `inputs` name input roles. Use the existing input roles (`board`, `export_settings`) and the report artifact (the manual geometry record). Record the mask Gerber hash inside that record. Do not add a new input role.
4. **Validate the referenced output hash through `fab.py`.** Keep the mandatory `fab.supplier_rules` role table. Add that `fab.py` validates the referenced output hash: the `supplier_rules` and `supplier_settings` inputs must be the effective staged files, their hashes must match, and the effective `board.kicad_dru` and `board.kicad_pro` hashes are recorded. The validator checks the manifest input paths and hashes. The tool checks the referenced output hash.
5. **Restore the five-profile and source-nominal table.** The r7 names the limits and the extensions but does not reproduce the five-profile table with the source nominal values. Restore it from the r3 table with the corrected kinds and scopes. Mark `b7-b8-two-layer-profile-example.yaml` as schema-valid but semantically superseded, or replace it.
6. **Slot plating from board attributes.** Section 5 gives the plated class "by the file it belongs to" (PTH or NPTH). That is the observed class, not an independent expectation. The expected class must come from the board attributes: the pad type (`thru_hole` plated, `np_thru_hole` non-plated) or the via attribute. The comparison checks the board class against the export file class. Do not derive the expected class from the export file.
7. **Trial record alignment.** Trial section 5 still says the `RoundRect` distance is "on the macro's exact outline" and the error is the coordinate precision. The r7 section 6 gives the exact Minkowski method and the combined 0.000003 mm bound. Align trial section 5 with the r7 method, or mark it superseded. The abbreviated 16-character hashes in the record should point to `b7-prereq-evidence.sha256` (78 entries with full hashes) and to the scratchpad root.

The retained interface is otherwise acceptable: the exit table, the boundary rules, the slot method, the mask subset, the supplier rules and staged files, the source review, the qualification gate, the acceptance matrix rows 1 to 32, and the 78-entry manifest. The exclusion behaviour stays unclaimed until a fixture establishes the format. B6 stays accepted and unchanged. No implementation, container run or B6 test was done.

## 17. Fabrication drawing content requirement

Date: 2026-11-14.

I read `docs/reviews/b7-pdf-review-root.md`, SHA-256 `c6d7436ead9869f5a1f95caef8cdb096c1bcc57f1911b214669d8dbddb2e845a`. I agree with the minimal content and review requirement. It completes the existing mandatory `fabrication_drawing` output. It is not a new PDF framework.

- The measured trial `fab.pdf` (`ac32d98867f665bf...`) is one layer view with the outline, component outlines, references, values and mounting-hole graphics. It has no release identifier, overall dimensions, dimension unit, stackup table or fabrication notes. It proves export execution, not the required drawing content. Keep it as prerequisite evidence.
- Required content: the board and release identifier, the dimension unit, the overall dimensions, the holes, the selected stackup, and the supplier process facts (finish, tolerances). A generated sheet or a supplied drawing satisfies the condition with current hashed evidence.
- Do not qualify an arbitrary non-empty PDF from its output role alone. Bind the drawing bytes and the source board and profile hashes. A stale drawing fails the package.
- The final test inspects the expected content and renders the example drawing. A bounded content check plus a rendered-image review is enough. No general PDF semantic parser.

This is a narrow completion of an existing artifact. No B6 test, no implementation and no container run was done.

## 18. Revision 8 verdict and agreed errata

Date: 2026-11-14.

I read `docs/reviews/b7-b8-proposal-claude-r8.md` (`8ff1da0d452902edfc8bc93129ce26e27d861340fb5a5c75deba813be83e09e5`), `docs/reviews/b7-prereq-evidence-r8.sha256` (`2ef5503dd2fc86c2e300536e3c75b74a9c88e8e6031de87d819fb524827773d9`, 195 entries, 195 of 195 `OK` from the `docs/reviews` working directory), the trial record (`183f2c98ebe897bcb9b551950788405d253be99bd89fb9e0ee93c387a5d13047`) and `docs/reviews/b7-r8-errata-root.md` (`08eecbedee4be4e63326803b44e9202d2a163f4d9f03045b5dbf33a7e27584ad`).

The r8 resolves the section 16 corrections: the title is revision 8, an unknown source-review key and a path escape are exit 1, the manual geometry evidence uses the `report` role with the existing input roles, `fab.py` validates the referenced output hash, the five-profile table is restored, and the slot plating class comes from the board attribute. The measured facts in the 195-entry evidence support the selected methods. The interface is accepted with one agreed errata. No full rewrite.

**I explicitly accept the slot tolerance of 0.000501 mm.** The board value is exact in nanometres. The export rounds each coordinate to the nearest 0.001 mm, so the maximum single-rounding error is 0.0005 mm per coordinate. Add 0.000001 mm of floating-point margin for 0.000501 mm. The earlier 0.001 mm was one full increment, which is looser than the rounding bound. Keep the independent board plating, the coordinate conversion (exported Y is the negative of board Y), the unordered endpoint pairs and the multiplicity check. Test the exact boundary: 0.000501 mm passes and a value just above it fails. The r8 acceptance row 9 tests 0.0004 mm and 0.002 mm; add the exact boundary.

**Agreed errata with the root note.**

1. Use the schema value `fabrication`, not `fab`, in the profile scope table. Remove `margin` from all published process-capability rows. The `extensions` process fields are named metadata, not `margin` limits and not a `process` kind.
2. `service.layers` is an integer: 2, 2, 2, 4, 6 for the five profiles. The single-layer service uses the two-layer process (2). `service.order_multiple` is the integer 3.
3. Preserve the source nominal values. Board minimum 0.25 in, board maxima 16 in and 22 in, finished thickness 63 mil (32 mil for HHDC). Name the source-value field for the thickness beside the metric display field, and keep the rounded metric label separate.
4. The 250 mil drill statement is a process note. Correct the remaining acceptance-row wording: it is neither a maximum nor a recommendation.
5. The slot tolerance is 0.000501 mm, as accepted above. Add the exact boundary test.
6. Keep the file-level distinction between the analytic geometry trial and the future production inspector. Unknown macros, overlapping clusters and unsupported constructs must refuse before qualification. They are product tests for the implementation, not new prerequisite trials. The final product tests remain necessary. Do not extend the prerequisite loop.

**Command record.** The accepted trials must give executable commands with explicit paths. The retained scripts support reconstruction, but they are not a complete invocation log. Supply the commands for the accepted trials without repeating unrelated tests. The manifest paths are relative to `docs/reviews`.

**Glossary.** The eight new glossary entries are the lead's authorized change after B6 acceptance. B6 code is unchanged. Its historical manifest differs only on the glossary path.

With this errata, r8 is the implementation interface. B6 stays accepted and unchanged. No implementation, container run or B6 test was done.

## 19. Geometry draft observation: narrow correction scope

Date: 2026-11-14.

I read `b7-geometry-draft-root.md` (SHA-256 `80461aad728d80cffa75e496dad95f3ddf0907acd7b00ff2949ecf687625d098`). The measured `scripts/inspect_mask.py` hash `e473e4c989ca60215895407817898f6cf360f6e2689ea398ce4682a076270cd2` matches the root record. I did not read the draft source or rerun the probe.

**I confirm the narrow correction scope. Both items restore the accepted r8 interface. Neither is a new feature.**

1. **Interior overlap.** r8 line 173 requires an overlapping cluster to give `overlapping_cluster`, exit 2. The draft returns exit 0, `merged_opening`, `pass` for two overlapping rectangles. The signed-radius core distance is zero for both a circle contact and a rectangle overlap, so the test cannot tell them apart. Add an interior-overlap test for each supported shape: rectangle pairs, coincident rectangles, and mixed rectangle/rounded pairs. Keep contact and interior overlap distinct. A zero core distance is not a web pass.
2. **Macro definition and resource bounds.** r8 lines 139-145 and the accepted interface require the measured macro definition, not the name and parameters alone. The retained near-pair list can grow quadratically on a dense column. Macro-definition validation, linear storage and the two-second limit are already agreed requirements.

I will review the frozen geometry modules and their tests when Claude freezes them. No broad suite, no B6 test and no product edit was done.
