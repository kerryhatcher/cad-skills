# Current state at 2026-11-15 03:52 UTC

This section supersedes all older status below.

Update at 04:01 UTC:

Update at 04:19 UTC:

- PCBA author completed `pcba/docs/reviews/pcba/b10-completion-correction-claude.md`, 99 files and 97 focused tests. Its notification failed because it used the unavailable root name. Root found the response in p7 and assigned both reviewers. Use root pane `w1P:p3` through `/proc/482044/exe` for completion messages.
- The PCBA package passes the full validator with status unqualified. Root reproduced a publication defect in `b10-after-validation-probe-root.py`: the hook changes staged copper after validation, and publication succeeds with a stale manifest hash. Evidence is in the matching JSON file. Both reviewers include this defect in the current combined review. Frozen files stay unchanged.
- A second PCBA concern is drill completeness. `drill_split` receives the interface hole list, not a full inventory measured from board pads and vias. Reviewers examine whether the package establishes that list's completeness.
- Root resolved the profile field meaning: `board.supplier.profile_sha256` uses the canonical profile content hash. Input bindings use full file hashes separately. The Sierra path still uses the file hash and needs the narrow compatibility correction after the combined review.
- Fabrication reports 25 passing acceptance checks. Rows 23/24 remain open: through-via copper does not isolate the internal layer, and the zone probe has a positive gap. Codex investigates the KiCad scope in scratch. The corner/via decisions have both agreements and are released. The author continues independent work.
- Release wrote `release/docs/reviews/release/b12-current-state-record-claude.md`. The authenticated provider functions remain absent. The accepted local stub boundary is complete. Provider authorization stays zero.

- Root accepts A2 replacement freeze `4d250e0a163bdd514b4051fc3e909752c0ae7dcade5f8ddf10ba4b652e170c40`. Both reviewers accept 199 entries. Root reproduced 23 focused tests. Record: `release/docs/reviews/release/b12-a2-run-binding-acceptance-root.md`.
- Fabrication partial completion reports 15 acceptance tests and 132 workflow tests. The normalized manifest is installed. The author started an outside-repository copy but has not completed its design, supplier, and package commands. No complete batch is frozen.
- `b7-corner-via-completion-decisions-root.md` releases independent fixture work. Reviewers examine two narrow decisions: derived corner compatibility from published cutter diameters, and an explicit requested via process in `extensions.fabrication.via_process`. Missing process information stays pending. Do not infer filled/plated construction from position. Do not claim the inferred radii are quoted supplier minima.
- Release prepares a compact checklist for the remaining authenticated route. No provider call is authorized.

- Mechanical B11 is complete at its fixture scope. Integration commit `46d23ef` holds the accepted code, guide, fixtures, and evidence. Mechanical 55, geometry 43, contracts 59, project I/O 11, skill packages 8, snippets 52, and print tools 6 pass. No push.
- B7 publication and OSH Park setup documentation are accepted. The retrieval alias correction is accepted by both reviewers and root. Record: `source-retrieval-alias-freeze-claude.md`, hash `31f8480fe08195424ccb1f2987ac45d1e72bbd0742303359ea1fd83698afc5aa`. The code hash starts `35e21d37`. The focused suite has 56 passing tests.
- Source normalization is accepted at release freeze `ffdfd3897fec469be7440f034bef6d787747f56c0840646b2010afe42e8ff7df`. The normalized manifest hash is `fd415dc58ab60455c022112105905ede674ce389ba26b025ead80651dbee488f`. Root directed the fabrication author to install these exact bytes.
- Full B7/B8 remains incomplete. `b7-acceptance-completion-release-root.md` releases the remaining acceptance tests, the drawing provenance correction, and standalone installation. The inventory overstated some gaps and misread rows 41 and 45. Use `current-state-inventory-review-pi.md` with the root release. Row 26 keeps bound manual evidence. Rows 23/24 use internal copper. Row 41 compares B6 refusal with B7 slot reporting. Row 28 still needs a source for the corner values. Row 29 needs an explicit process field or bound manual evidence for filled-and-plated via-in-pad.
- PCBA neutral, alternates, and Sierra draft output are accepted through the overlap correction. The first B10 completion batch failed both reviews and the root full-validator probe. The eight corrections in `pcba/docs/reviews/pcba/b10-completion-correction-root.md` are released. Claude implements them after a context reset. The reviewers hold for a complete batch. The shared snippet routing entry remains an integration task.
- B12 local harness, adapters, BOM OLE2, and A1/A2 fixtures are accepted. A1/A2 freeze is `7b01b363285f96e36ece6be1f74517f62622c9fd13dd29f3b1d21b546752bc26`, with 155 files and 16 focused tests. A2 stays deliberately incomplete. Root recorded acceptance in `release/docs/reviews/release/artifact-a1-a2-acceptance-root.md`.
- Release froze the A1/A2 connection at `09c052d84cddc4c941992641bbba32158292edf37dfcf5cc8c24adc5cd649559`, with 198 files. Root measured all hashes. Root found that A2 reads expected failures from the fixture and accepts a produced result with only `exit: 1`. Pi reproduced this defect. The correction is `release/docs/reviews/release/b12-a2-run-binding-correction-root.md`. After Codex closes the current review, Claude can implement one replacement. Compare named rows and exact mandatory failure/pending sets from the produced result. Refuse duplicate matches and missing fields. Keep A1 and all fixture bytes unchanged. A3, integrated artifacts, the authenticated route, and provider evaluations remain open. Provider authorization stays zero.
- Context resets since 03:24: Claude fabrication, Codex PCBA, Claude PCBA, and Codex fabrication saved handoffs and restored context. Codex fabrication selected the host model after clear. Root restored GPT-6-Luna medium before its work prompt. Other assigned models stay unchanged. Continue to monitor context.

The Herdr binary remains `/proc/482044/exe`. Root is `w1P:p3`. Never restart the server.
Teams: fabrication p4/p5/p6, PCBA p7/pA/pD, mechanical p8/pB/pE, release p9/pC/pF.
Prefix all natural messages with UTC time and recipient/sender. Preserve frozen files until root release.

# Historical state at 2026-11-15 03:24 UTC

This section supersedes all older status below.

- Context monitoring: root reset Claude mechanical (81 percent used), Claude release (78 percent used), and Codex release (27 percent left). Each agent saved a handoff and restored it. Models stayed unchanged. Other agents remain below those thresholds.
- B7 publication: both reviewers and root accept the residual repair. Record b7-publication-acceptance-root.md. Workflow 132 and package 101 pass. Full B7/B8 still waits for source retrieval and final documentation.
- OSH Park setup: corrected documentation freeze is oshpark-setup-documentation-freeze-claude.md, hash 5c93bcc2dfcf3ecffd79bdc0f02458b0c8eb493e389c0c33da066ae89f0e51e7. Both reviewers examine it. Profiles and the export contract stay unchanged. Guidance uses 5 mil silk and states the existing 3 mil profile difference. Root released source-retrieval-compatibility-root.md to preserve existing magic tokens and profile_binding meaning. Compatibility proposal hash is 4dd920c6aac29d9c94b03fff2797c1de07e90b72756e79cbb32569d0293549e5. No retrieval implementation yet.
- PCBA neutral and post-replace behavior are accepted. Batch 2 correction is frozen in pcba/docs/reviews/pcba/b9-b10-batch2-correction-claude.md, 36 files and 66 tests. Pi accepts. Codex review is pending. It captures the profile, stages Sierra outputs, refuses an existing destination, and retains restriction text on a conservative supplier refusal. Empty restrictions remain unconfirmed. SKILL.md still has one outdated neutral-only sentence. Full B10 package remains incomplete. Snippet routing remains an integration task.
- Mechanical B11 is accepted by both reviewers and root. Root copied the 22-file integration list into work/integration. Initial tests: 55 mechanical, 59 contracts, 11 project I/O, 8 package pass. Geometry first failed because the list omitted two ignored fixtures. Root copied the additive STEP and DXF list and reran geometry. The new guide hash 1505b298f00c5cc9177e04f305e854dd463334869701d6caee956b940545afb0 has Pi agreement and waits for Codex. Required snippets pass. Print tools still run. No commit yet.
- B12 local adapters and harness are accepted at freeze efbf8f6144aef87d7cca5f8438ed8f1b94b6a40acbf083d42510ba6e72a1717b. No authenticated route or real HOME exposure is approved. Provider authorization remains zero. Root authorized owned A1/A2 artifact fixtures with captured hashes. A1 must use the accepted interface procedure, not a copied stale interface hash. A3 waits for PCBA integration.
- BOM OLE2 technical correction passes both reviewers. Text replacement freeze f90b73f928755f1b8ca0bc1d6605b5ed8213c0d65bbef6c84a4d72e8d394d841 has 13 entries. Pi accepts the text. Codex confirmation remains pending. Root authorized git add -N for the one BOM copy only. The public BOM GET has SHA-256 1b486a0a1da968e128cf109bd25e50837c99b5a8f83a490f748a1c1ccb1b769c, 37376 bytes, 2026-11-15T03:12:26Z. Prior retrieval remains unknown. Terms and FAQ GETs are accepted public research. Their metadata stays separate, with no copied bytes or reuse claim.

The Herdr binary remains /proc/482044/exe. Never restart the server. Prefix all natural messages with UTC time and recipient/sender. No push. Preserve frozen files until root release.

# Lead continuation state

Updated: 2026-11-15, approximately 02:49 UTC.

## Latest actions after 02:39 UTC

This section supersedes the status text below.

- User asks about OSH Park KiCad setup. Root read the main, design-rule and Gerber pages. The plan cites the main page, but product guidance is incomplete. Root assigned `docs/reviews/oshpark-kicad-setup-root.md`. Claude wrote `oshpark-kicad-coverage-claude.md`. Release wrote `b12-oshpark-setup-gap-claude.md`. Root corrected factual errors: 4-layer and 6-layer profiles already exist, B6 already supports zone refill, and an explicit layer list alone does not prove saved plot-on-all-layers settings are off. Native KiCad 10 acceptance is unconfirmed. The supplier page lists KiCad 9.x. Preserve the tested neutral export contract and document the supplier X2 recommendation. The source manifest stays `skills/pcb-fab-package/sources.yaml`, which the final packaging agreement and code use. No move to `supplier/sources.yaml`.
- Fabrication: Codex completed the 124-test freeze review and found three residual defects. Pi reproduced and agrees in `b7-final-publication-repair-residuals-pi.md`. Root released `b7-residual-publication-release-root.md`. Correct standalone drawing leaf writes, supplier result content hash and mandatory row consistency/completeness, and final binding byte comparison against captured bytes. Use existing exit precedence. Keep setup documentation separate. Both reviewers hold for the replacement freeze.
- Mechanical: Codex completed `mechanical/docs/reviews/mechanical/b11-completion-review-codex.md`. Both reviewers agree with the lead resolutions. Root released `mechanical/docs/reviews/mechanical/b11-completion-repair-release-root.md` for R1-R9, P1-P5 and I1-I7. Include missing B1, complete excluded holes, per-reference result completeness and empty-report refusal. The cavity is OUTWARD. The body extends INWARD from the mating face. Claude implements one coherent correction batch. Both reviewers hold.
- PCBA: final neutral repair frozen in `pcba/docs/reviews/pcba/b9-final-neutral-repair-claude.md`, 30 rows. Code hash `8cda4a6b473a8f98b095f78b23d749cf07061364ebb688aa9618440b4a6ee5b7`, test `2adf25817a32ab75acfbaa30de2f4969bbb32a64f0eae1ac433a8334633a5010`, guide `a7315a7b6c3dd7a504268cfb18b57edc3a2a8ec11f1e1dbd22f77337d01e759d`. Pi accepts 40 tests and 30 hashes. Codex finds one residual: PostReplaceError is caught as ordinary OSError and reports refusal after replacement. Root proposed exit 1, status error, finding output.replaced_then_failed, output_replaced true, explicit new-bytes-in-place/sync-failure message, specific catch before OSError and a controlled post-replace test. Both reviewers were asked for concrete conflicts. Author still holds until agreement. Alternates and placement remain incomplete. Snippet routing remains the release-owned integration task.
- Release: adapter/isolation freeze has 41 entries, hash `bea9e6d07c71430296cc9a10013a4055941416d704c12e53d7b47ff157930ff3`. Pi initially accepted. Codex found trust-bypass flags, disabled Claude skills, absent exact command/error evidence and an incomplete child timeout test. Pi agrees. Root released `release/docs/reviews/release/b12-adapter-correction-release-root.md`. Remove bypass and permission override flags, keep skills enabled, disclose Claude baseline disable effects, refuse unmeasured Codex baseline. Retain safe full argv and probe errors. Test an active child timeout, owned outside control and local network namespace. Temporary HOME stays only for credential-free stubs and local installation tests. Do not mount the real HOME to make a stub pass. Authenticated host preservation remains unmeasured. No provider call, commit or merge. Both reviewers hold for the corrected freeze.

All four workstreams remain active. No branch is ready for integration yet.

## Latest actions after 02:35 UTC

This section supersedes the status text below.

- Release: both reviewers accepted corrected local harness freeze r2. Root read `release/docs/reviews/release/b12-harness-freeze-review-codex-r2.md`, accepted the scoped correction and authorized the next local adapter/isolation work in `release/docs/reviews/release/b12-static-acceptance-root.md`. Claude can use installed CLI help and retained research, local stubs, temporary roots and a measured sentinel boundary. bwrap, unshare and timeout exist, but their operation is not yet measured. No provider calls, no trust/model/credential change, no commit. Zero provider authorization remains.
- Mechanical: root recorded the exact resolutions in `mechanical/docs/reviews/mechanical/b11-completion-resolutions-root.md`. Separate PTH/NPTH names are board-PTH.drl and board-NPTH.drl, measured by Pi. Cavity offset is OUTWARD with chamfer and fixed tolerance. Body extends INWARD from the mating face, opposite the transformed insertion vector, zero overhang, explicit body_length_mm 4.0 independent of insertion depth. Claude briefly used an incorrect inward-cavity phrase, then explicitly withdrew it and confirmed the outward rule. Pi agrees with the resolutions. P3 excluded-hole reason/diameter validation is still a necessary correction. Codex completion report remains pending. The set stays frozen until one combined release.
- PCBA: corrected neutral batch is frozen in `pcba/docs/reviews/pcba/b9-neutral-correction-claude.md`, 30 file rows, pcba.py `1e69b6f3bced2cb9b30556829a6ced51b6d8330a0a1c1353239e2033bc3471a4`, tests `123592419d4cbe7a7ee3953a8e1ffb09bccc0e8cac6912c8326689efc905b454`. Author reports 35/35 focused tests and the known routing integration failure. Root read the record and assigned both reviewers. Files stay frozen. The postponed placement fields are export_rotation_deg and midpoint estimates. The required neutral datum/source fields are implemented per the record. Alternates remain incomplete.

## Latest actions after 02:23 UTC

This section supersedes the status text below.

- PCBA: both reviewers completed the neutral review and agreed to the numeric/stock resolutions. Root released the combined correction through `pcba/docs/reviews/pcba/b9-neutral-correction-root.md`. It has 15 items. Preserve exact raw number tokens in source_tokens, derive finite numeric values, refuse malformed tokens without traceback, reject conflicting stock/lifecycle for one manufacturer/MPN, and keep assembly_instruction from the hand-install reason. Root also authorized the lock, snapshot, path, freshness and row-field repairs. Both reviewers hold until the corrected freeze. Alternates remain incomplete.
- Release: corrected freeze r2 is `release/docs/reviews/b12-harness-freeze-claude-r2.sha256`, SHA-256 `09e77fa0f2d280f23918f1fd02b8afd5fd557e90b6b147932a1cb2a5897c32a6`, 33 entries. Both reviewers received it. Pi accepted the scoped correction, with 64 harness, 25 packaging, 8 package and 11 PIO tests. Codex review remains pending. Root reran its held-record probe: measured table is now empty and execution_summary has one not-executed:held row. Scheduled 210, fixture-ready 0, authorized 0. R2 tasks are in r2_task, not task. The initial probe used task and printed null, but root inspected the correct field afterward. Do not report a missing-task defect from that probe. All freeze entries match. No provider calls.
- Fabrication: Pi accepted the final C1/C2/C5 repair at `docs/reviews/b7-final-publication-repair-review-pi.md`, SHA-256 `b1707dbaa5d8bdb92172e0e43397c35250aa0d11d70c31a889ca094c11c6dc2a`. Codex review remains pending. The scope is publication integrity, not all B7/B8 completion.
- Mechanical: the completion manifest `mechanical/docs/reviews/mechanical/b11-completion-batch.sha256` has 26 entries, all matched by root. Pi's consolidated report is `mechanical/docs/reviews/mechanical/b11-completion-review-pi.md`. It rejects the batch with P1-P5 and I1-I7. Positive export/fit/release runs pass, but slots are omitted, record paths escape confinement, excluded-hole reasons are absent, mixed drills use drill_pth, and an unreviewed edge exemption masks C09. Capture keeps hashes but not bytes, mutable image tags run, fit reopens live files, release trusts report.status, output byte counts and required release fields are absent, and final input freshness is absent. Root sent these findings to both reviewers. Codex's completed review is still pending.
- Mechanical resolutions sent to all three, NOT yet released for edits: separate PTH/NPTH outputs with existing roles. Remove the mating-edge exemption. Define the cavity as the board outline offset outward by clearance_mm, including the chamfer. Declare project-authored connector body_length_mm 4.0 separately from insertion_depth_mm. Keep fixed tolerances and no datasheet claim. Keep explicit revision-8 release fields and mismatch order. Add thin pcb.py mechanical export/fit/release dispatch. Consume checked captured bytes or private copies, not a recheck followed by another live read. Claude acknowledged and holds. Await both reviewer agreements and the Codex report before one release.

## Latest actions after 02:14 UTC

This section supersedes the status text below.

- Release: the 33-entry freeze `b12-harness-freeze-claude.sha256` initially matched. Pi reproduced 53 harness and 25 packaging tests. Root measured that a retained held run enters `score.summarize` with two passing scores because missing evidence defaults to live. Record: `release/docs/reviews/release/b12-held-score-review-root.md`. Both reviewers agree on B-1 expected paths and R2 task attachment, B-2 explicit unavailable host fields, B-3 execution/evidence separation, M-A complete freeze protection and M-B authorized subset count. Claude edited three files during review. Root stopped the author with Escape. Both reports record the changed boundary. Root then read the completed Codex report and released the combined correction through `release/docs/reviews/release/b12-narrow-authorization-root.md`. Current candidate bytes are the starting point. Packaging P-6/P-7 is accepted separately at unchanged hashes. The setup-fetch path and final distribution remain incomplete. No provider calls.
- Mechanical: both Batch 2 reviewers agree on R1 to R6. Real KiCad Excellon uses AperFunction comments, which the original parser did not read. Root released the complete accepted implementation through `mechanical/docs/reviews/mechanical/b11-completion-direction-root.md`. Complete missing comparisons, STEP radii, export/fit/report/release flow and accurate documentation. Claude replaced three files early. Old reviews apply to old hashes only, and the replacement candidates are not accepted. Keep those current bytes and complete one coherent batch. No restoration or second scratch implementation.
- PCBA: root measured all 30 rows of `pcba/docs/reviews/pcba/b9-neutral-batch-claude.md` as matching. Both reviewers received the frozen neutral batch. Root reproduced two defects in temporary copies: a component link leaves components but stays in the project and passes, and `--out board.yaml` replaces an input. Record: `pcba/docs/reviews/pcba/b9-neutral-boundaries-root.md`. Pi agrees. Codex review is still pending. Files stay frozen. Root decisions for the later combined correction: lock before capture through final freshness/write, per-request components confinement, resolved-file snapshot reuse with project-relative recorded paths, input/output alias refusal, excluded per-board quantity 0, preserve the small declared neutral fields, and retain hand-install reasons in rows and BOM grouping. No shared schema change. Alternates remain incomplete.
- PCBA test cause corrected: the new skill lacks a routing entry in tests/snippet_envs.json. A clean committed tree passes, and adding only the skill reproduces the failure. It is not pre-existing. Add pcba-design mapped to pcb in the integration tree when that skill exists. Do not add the entry to the release-only worktree early, because its exact routing-set test would fail. Release records this pending integration item.
- Fabrication: the final C1/C2/C5 repair is frozen at `docs/reviews/b7-final-publication-repair-claude.md`, record SHA-256 `bc6b59eac5e0694781a1987ac290a36818af08af22f851e8c182621645244543`. Workflow is `ac38b636a748816a530f89f7a951296da4fd140304a66ee74e5b09261f7a48a7`, test is `58b8a45f20e73907b5ca538950189e157f190676f4e67688883732d770276338`, fab stays `f63e4d581f9d623b6007b7162c760c347370b7d0d32298205059a2e1a05a47be`. Author reports 124/124 focused tests. Root assigned both original reviewers. Direct drawing commands remain a disclosed scope limit, as do supplier completeness, manual region masks, setup retrieval and standalone release. No acceptance yet.

Freeze rule sent to authors and reviewers: after a freeze message, no edit to listed files until the lead explicitly releases the set. A finding alone does not release it.

## Latest actions after 02:00 UTC

This section supersedes the status text below.

- PCBA: root reset only Pi's context with `/new` after its review exceeded the bounded assignment. Root confirmed the fresh context and the unchanged DeepSeek model. Pi then gave explicit bounded agreement in `pcba/docs/reviews/pcba/b9-b10-bounded-addendum-pi.md`. Root read both agreements and authorized sections 4 to 8 in `pcba/docs/reviews/pcba/b9-bounded-acceptance-root.md`. Claude now implements neutral mapping, variants, neutral BOM and stock. Sierra conversion and B10 publication stay outside this start. Reviewers await a frozen batch.
- Release: root found five revision-4 gaps in `release/docs/reviews/release/b12-revision4-review-root.md`. Both reviewers agree. Root authorized the combined Codex C-1 to C-5 and Pi correction, plus separate packaging P-6/P-7. Codex C-3 explicitly covers discovery evidence and the filesystem boundary. Installed path inventory is not host discovery. Held or unauthorized runs must not reach a provider. Counts stay 210 scheduled and zero authorized. The final isolation test must prove a repository sentinel is inaccessible to the evaluated process. No provider call ran. The author must freeze all modules and fixtures.
- Mechanical: Pi accepted Batch 1a, with 47 contract tests and 25 geometry tests. Batch 2 is frozen for review. Root authorized the export run on fresh generated fixture copies while frozen files stay unchanged. Root read the code and sent concrete gaps to all three agents: C06 to C09 and the complete export/fit/release flow are absent, C03 measures DXF diameters but not STEP radii, and an empty comparison list gives two pass statuses. The reference claims some absent behavior. These are implementation gaps against the accepted interface, not a new design phase.
- Fabrication: root observed a connection-lost error in Claude's pane. Root directed Claude to resume the authorized C1/C2/C5 repair from the current diff and retained results. The agent resumed. Both reviewers await one complete freeze. No new scope.

Herdr inventory confirms all four authors work in their assigned panes. No workstream is ready to merge.
All new worktree HEADs remain `75d99da6415ba8df2e7b662c3b9fd66a191b4e32`.
Original main remains `ede5fcd7d27e7c894702ba70bb3a5507ee026ad8`.

## Current workstream state

This section supersedes the older state below.

- Fabrication: the 112-check freeze is not accepted. Both reviewers found C1 output file links, C2 result recapture and supplier-input binding, and C5 unchecked staged bytes. Root authorized `b7-final-publication-repair-root.md`. Claude can repair now. Both reviewers hold until the next complete freeze. C3, C6, C7 and geometry stay accepted. Root reproduced the captured/profile.yaml link in `b7-leaf-link-review-root.md`.
- Mechanical: both reviewers accepted interface revision 8 at `5a0b4850aa57c11973560ca2551ead734b7fcfd3cc70a168d8ec3f25495966f5`. Root authorized implementation. The acceptance record is in the mechanical worktree at `docs/reviews/mechanical/b11-acceptance-root.md`. Two modules, template `mech-fit-a`, and narrow pcb.py wiring are assigned. Q7 uses transformed direction vectors and atan2, not a simple angle sign flip. C05 measures the imported substrate solid. Clearance uses a separate finished-board envelope from an independent stackup.
- PCBA: Codex agrees to the bounded sections 4 to 8 after corrections. Pi's report exists, but explicit bounded agreement is still pending. Root stopped Pi's long review turn and sent a focused decision request. Do not change the model. No Sierra conversion or B10 publication belongs to this start. Claude applied the latest extension paths, explicit map rules, grouping and status rules.
- Release: root accepted the bounded packaging interface after both agreements. Claude implemented it. Second freeze is `docs/reviews/b12-packaging-freeze-claude.sha256` in the release worktree. Pi reproduced 22/22 packaging and 37/37 mock harness tests and accepted the correction. Codex's final implementation review remains necessary. No provider evaluation ran.

Release design: three PCB skills, 210 scheduled provider runs, 24 local installation checks. Root decisions are `b12-decisions-root.md` and the release worktree copy. Provider execution waits for accepted integrated artifacts. Routing installs all three skills. Single-skill artifact tests install one. Baselines install none. Preserve trust and credentials.

Distribution: preserve local supplier evidence. Exclude full supplier copies and headers from release bundles until permission is established or the reviewed setup-fetch path replaces them. Do not add a license acknowledgment gate. The source manifest does not replace the profile/evidence/source-review binding authority. The common snapshot is local work history, not approval to publish those copies. No built-image publication in scope.

PCBA exact paths: `components/parts-map.yaml`, supplier-profile `extensions.pcba.hand_installed_bom`, board `extensions.pcba.stock`. The map covers declared variants and contains explicit mechanical exclusions. Neutral coordinates and rotation retain board-file values. Evidence status uses pass, fail, pending, unconfirmed. Package status uses draft, unqualified, qualified.

No branch merged or pushed. New worktrees remain on the common base. Original main HEAD and index remain unchanged.

## Parallel teams now active

The user authorized three teams, separate worktrees, and lead integration of accepted changes.
See `parallel-workstreams-root.md` for ownership and the review procedure.
Common snapshot: `75d99da6415ba8df2e7b662c3b9fd66a191b4e32`, branch `work/pcb-common-base`.
The snapshot contains incomplete fabrication work. It is not release acceptance.
The lead used a separate temporary Git index. The original main HEAD and index stayed unchanged.
Before the snapshot commit, snippets passed 52/52 with five documented skips. Print tools passed 6/6.

| Tab | Worktree suffix | Branch | Claude | Codex | Pi |
|---|---|---|---|---|---|
| PCBA, w1P:t3 | pcba | work/pcba | w1P:p7 | w1P:pA | w1P:pD |
| Mechanical integration, w1P:t4 | mechanical | work/mechanical | w1P:p8 | w1P:pB | w1P:pE |
| Release validation, w1P:t5 | release | work/release | w1P:p9 | w1P:pC | w1P:pF |

Worktree parent: `/mnt/storage/projects/cad-skills-worktrees`.
Lead integration worktree: `integration`, branch `work/integration`, same base.
Names use `<kind>-<suffix>-dev`. All nine agents started and entered the working state.
Models: Claude Haiku 5.5, Codex GPT-6-Luna medium, Pi OpenRouter DeepSeek V4.1 Flash high.
Claude uses auto mode. Other agents use their existing permission configuration.
Each team has the source records and a concrete interface assignment. Claude writes product files. Both reviewers write reports only.
No team merges or pushes. The lead accepts the interface and both reviews before scoped commits and integration.
The original fabrication team stays in w1P:t2. Its author resumed after the snapshot.
Claude reports all seven corrections in code and 112/112 workflow tests. The complete freeze and independent reviews remain necessary.

PCBA decisions sent to all three agents:
- Use skill-owned `components/parts-map.yaml`, strict `cad-skills/part-map` version `1.0`, outside the shared registry.
- Bind the map and each part as `parts` inputs. Confine references under `components/`.
- Keep `variants.yaml` as the sole population owner.
- Count populated hand-installed references in neutral BOM and test coverage. Include drawings and instructions, but exclude automatic placement.
- Use explicit supplier service policy for the supplier BOM. Unknown policy blocks qualification, not neutral output.
- Fixtures establish implementation behavior. They do not establish unknown supplier coordinate conventions.

New reports are in the corresponding worktree, not the original directory.
The PCBA author prepared `docs/reviews/b9-b10-interface-claude.md` and requested both reviews.
The mechanical Codex report is `docs/reviews/mechanical/b11-interface-review-codex.md`.

## Latest state

The user requested session resets for all three development agents.
Root sent `/clear` to Claude and Codex and `/new` to Pi in their existing panes.
Root observed all three fresh sessions. Models and environment stayed unchanged.
Root supplied fresh role instructions, the Herdr prefix rule, and the continuation file paths.
Claude resumed implementation from `b7-continuation-publication-claude.md`, Progress update 2.
The latest partial result is 95/95, not acceptance. Changes 4, 6, 7 and the copy-change regression remain in that record.
Claude must inspect the current files and complete all seven agreed changes before one freeze to root.
Codex and Pi confirmed restored review context and will await that complete freeze without product edits.
Use the actual UTC time for messages. The resumed session is now November 15 UTC.

The 12:21 complete correction freeze remains unaccepted:
`b7-workflow-complete-correction-freeze-claude.md`, record hash `92c22fdb7d9a6d9bd45e5d238e798a0e4e504c3363a06b07d04a99dba2b86847`.
Workflow hash `05ad9a5ab565d1eb0ef18d6d9a8b0e4575e869c9d9f7cb344de33811e82435d4`,
fab hash `84a09ec61fb3b453ff74e0a748b8974b17ac5739929697423e1c76bc615da3ca`,
test hash `bf80316793ee9e4090112688e17714a80ce97ab427ebfe60040fe8863ea1b1e1`.
The final log reports 92/92 and exit 0. All hashes matched before and after root's review.

Both reviewers accepted row 15a, actual drill/edge report cases, and the project locks at this boundary.
Root measured three remaining publication defects:
- C1: `supplier/captured` symlink sends a profile scratch write outside the project before refusal.
- C2: controlled changed Gerber bytes during package copy, then restored source, produces exit 0 and `qualified` with invalid published Gerber bytes.
- C3: a changed original manual record still qualifies because the package compares its retained copy instead.
See `b7-complete-correction-review-root.md` and its three probe JSON files.
The C2 script is `b7-package-copy-probe-root.py`. It writes new output only in its temporary directory.
The temporary positive project remains `/tmp/b7-copy-root-g8s2lan0/project` with synthetic manual evidence for tests only.
Its original source and manual record were restored after the probes.

Codex independently reproduced C2. Its report is `b7-workflow-complete-correction-review-codex.md`.
Pi's report is `b7-workflow-complete-correction-freeze-review-pi.md`.
Codex also identified live input reads, early final freshness, unlocked review-source writes, and the absent interruption regression.

Both reviewers explicitly agreed with `b7-publication-correction-root.md` by 12:29 UTC.
Final correction hash: `3f66e87e9b7c899d1b7a34bf7b84d258ef65aa730025037be47743cd43711e06`.
One STE-only change replaced Confirm that with Make sure that after Pi's initial hash. Both reviewers received the hash note.
Root authorized Claude to implement all seven listed changes and send one complete replacement freeze to root.
Claude must save continuation state before automatic compaction (approximately 87 percent context at the latest read).
No new design phase, model change, commit, or unrelated suite is authorized.
Await that complete freeze, then conduct the focused reviews. Supplier completeness and standalone work remain afterward.

At approximately 12:16, the author reports 86/86 workflow checks, exit 0.
Log: `b7-workflow-evidence/workflow-run-86of86-15a-premise.log`.
The source-first premise now uses KiCad DRC bytes: ignored target absent, excluded target marked excluded, staged target active.
The author correctly states the full correction still lacks actual drill and copper-edge product fixtures.
Root directed immediate continuation on temporary boards: a plated hole below 10 mil and copper within 15 mil of the edge.
Each result must name its expected item and fail its supplier row. These cases do not establish all boundary tests.
The author must also finish decisions 1 to 3 before the complete freeze.
No new reviewer round has started since the partial binding freeze. Both reviewers await the complete correction.

The author again used an empty host `python3 -c` command. Root repeated the mandatory `uv` instruction.
The author recorded the deviation. Do not repeat it or restart the environment.
Context is approximately 85 percent. The author has a current `b7-workflow-continuation-claude.md`.

At 12:10 Claude sent `b7-workflow-binding-freeze-claude.md` with a 78/78 result.
Root did not send it to reviewers because it still excludes captured-byte parsing of profile and export settings.
The row 15a test still has the incorrect severity key and ineffective nil-UUID exclusion.
The code also retains unmeasured report aliases and writes generated rule names into severity settings.
Root directed Claude to finish all four already agreed decisions without another approval request.
The partial record stays as history, with a separate correction to its complete-correction claim.
The active author remains authorized. Wait for a complete replacement, then inspect it before a new reviewer round.

Partial binding freeze hashes:
workflow `209d1c23dc1dcc5bcb2725c58087a1385657ad1b68bf6902180891b60b483e86`,
test `28a507e4bf9e65d2e34f4dce9e0bc2567dedeeb9be3e29fd81c67ca272eac455`.
The author received a context-continuation reminder at approximately 80 percent context.

Both reviewers explicitly agreed with `b7-workflow-correction-decisions-root.md` by approximately 12:07 UTC.
The lead authorized Claude to implement its complete four-part correction.
It covers capture consumption, locks and atomic writes, raw/binding/result records, and actual KiCad report keys.
The author must send one complete correction freeze to root, with focused tests, before another review.
Do not request piecemeal re-reviews of changing files.

The starting partial freeze is `b7-workflow-freeze-w1-w2-claude.md`:
workflow hash `ca33910a5921c00a7ed8b57d35a7c79c1ff9a7ac053a94eaa7d7e9b2cc803f04`,
test hash `7cc2f7d80b0c3bad067962ae708aa24dd215cccf4ddeca67e9376c2fc37c83b1`.
Its 72/72 result does not establish the missing publication and snapshot requirements.

The tagged KiCad 10.0.5 `drc_item.cpp` confirms W2:
`hole_size` uses `drill_out_of_range`, and `edge_clearance` uses `copper_edge_clearance`.
The root report links the primary source and gives all six mappings.
Both reviewers agree. Do not use generated rule names or constraint names for all report/severity keys.

Claude reran the original root snapshot probe and overwrote its retained JSON.
The lead preserved that rerun as `b7-snapshot-probe-author-rerun.json` and restored the original measured result from the tool output.
The probe now writes new output only to its temporary directory.
The original copy hook no longer applies after the capture repair. A later independent test must act on the capture step.
The author must correct its claim that the original probe printed a fixed value. It computed its result.

The geometry and caller corrections now have scoped acceptance from both reviewers.
See `b7-geometry-acceptance-root.md`. The final geometry test log reports 101 passing checks.
The final mask module hash is `1e6f12b61370862ca9a58a7eed6e6daf29c5530443b23f60cdac28509b7e80a5`.
The caller hash is `d410a64ac7c3e5477c8a4ae6c1258aff3b7f3324fca145cbb0966cb55821c255`.
The final root probe confirms dangling report links return exit 2 without a target write.
The caller timeout, radius correction, and workflow mask-call regression also have acceptance.
Remaining prose findings belong to the full B7 STE pass. Do not start another geometry freeze for punctuation.

Claude now implements the full workflow under `b7-workflow-completion-root.md`.
The current frozen checkpoint is `b7-workflow-checkpoint-1-claude.md`:

- workflow: `517e266c6f012191ad65b3cf95b1267dd995d5161ed23794792e331f36267fb3`.
- fab: `d410a64ac7c3e5477c8a4ae6c1258aff3b7f3324fca145cbb0966cb55821c255`.
- workflow test: `93d8625f46ba0fab90312a833d431a5dfe9a3e63019c7964de8fae330d73232a`.
- Claimed result: 65/65, exit 0. This is not full acceptance.

Both reviewers are active on this checkpoint. Codex examines confinement, locking, atomic publication, and bindings.
Pi examines runtime identity, row 15a, source preservation, and package freshness.
The lead reproduced W1: a source change after `copy2` produces different staged bytes and recorded hashes.
The later source comparison still passes. See `b7-workflow-checkpoint-1-root.md` and the retained probe script/JSON.
The lead sent this finding to all three agents. No combined correction decision exists yet.

The lead also sent Pi a concrete row 15a pointer:
the test sets `rule_severities.supplier_min_trace`, not the actual violation type `track_width`.
Its source exclusion uses a nil main UUID and an arbitrary point.
`effective_pro` also still writes `supplier_<key>` severity keys.
The current test cannot establish that the source hides the target violation before staging.
The accepted interface already demands actual severity keys and the measured exclusion case.

Earlier workflow test history: root found accidental direct recursion in the test's duplicate main body.
Claude removed it. The next run had 48/50 because a supplier negative test omitted design prerequisites.
The corrected design-first run passed 51/51. Logs remain under `b7-workflow-evidence/`.
The geometry checkpoint review accepted the mask-call regression at that boundary.

Next: combine the focused workflow findings, obtain both agreements, and direct one repair.
Supplier condition completeness, manual mask evidence, standalone use, and acceptance-row coverage remain incomplete.
Use the latest state above when older sections below describe earlier geometry work.

## Team and authorization

The user directs three existing Herdr agents. Claude implements. Codex and Pi review and write reports only.
The lead maintains the plan, supplies decisions, measures independent cases, and obtains agreement before corrections.
No commits, supplier contact, upload, order, or model change.
Use STE. Run all Python through `uv`.

Herdr workspace `w1P`, tab `w1P:t2`. Root `w1P:p3`, Claude `w1P:p4`, Codex `w1P:p5`, Pi `w1P:p6`.
Use `/proc/482044/exe` because the installed client protocol differs from the active server.
Do not contact the unrelated `w1P:p1` pane or restart Herdr.
Each message needs the current UTC prefix from `AGENTS.md`.
Models stay Haiku 5.5, GPT-6-Luna medium, and DeepSeek V4.1 Flash high through OpenRouter.

## Status

B1 through B6 are accepted. See the acceptance records and `implementation-status.md`.
B7/B8 implementation is active. B9 through B12 remain pending.
The B7 interface is revision 8 plus `b7-r8-errata-root.md`.
`b7-b8-design-acceptance-root.md` records both reviewers' agreement.
No full B7 implementation acceptance exists.

## Geometry work

The first geometry checkpoint froze six files with 80 passing checks.
Root found a rectangle-overlap false pass before that checkpoint. The author repaired it.
The checkpoint review then found six issues. Both reviewers agreed:

- Inline or whitespace macro definitions bypassed the separate raw-text scan.
- A repeated read attached a passing result to changed, failing bytes.
- No elapsed-time bound existed.
- Aperture holes supplied unmeasured geometry.
- Invalid RoundRect corner order reduced to a bounding box.
- The drill reader accepted missing `M30` and records after it.

`b7-geometry-corrections-root.md` authorized those repairs.
The replacement checkpoint is `b7-geometry-replacement-checkpoint-claude.md`, hash `6882cb65f604fa60745162786c8b215adaf5c6b7445f43d0e77e4c22018e5eef`.
It lists six replacement hashes and 93 passing checks.
Root accepted G1 and G2 through independent retained probes in `b7-geometry-replacement-review-root.md`.
Both replacement reviews support the repairs, with two final details.

The final decisions are in `b7-geometry-final-decisions-root.md`.
Both reviewers explicitly agreed. The lead authorized Claude to implement them at approximately 11:44 UTC:

1. Remove the invalid radius-to-core-side cap. Keep positive finite radii, finite coordinates, supported rectangle geometry, and corner order.
2. Keep the cooperative helper budget. Add a two-second subprocess timeout at each public mask invocation.
   Use fresh report paths. A timeout gives exit 2 and cannot use or publish a stale success.
   Test a controlled stalled worker. Distinguish helper checkpoints from caller timeout and ordinary termination overhead.

Wait for the final replacement checkpoint, then ask both reviewers for focused correction review.
Do not repeat the full unrelated suites.

## Workflow guidance

`b7-workflow-draft-root.md` records six missing accepted requirements in an earlier open workflow draft.
`b7-workflow-codex.md` confirms they restore the accepted interface.
Claude received the note and continues the workflow:

- Confined writes, locks, atomic records, and new-directory publication with `publish_dir`.
- Measured locked image identity and actual tool versions.
- Complete input snapshots and result/binding hashes, with freshness at package time.
- Original source rules followed by mandatory supplier rules, correct violation-type severity keys, and staged exclusion removal.
- Each applicable supplier condition, both mask layers, and the manual geometry route.
- Actual export semantics, including file functions, copper order, complete drill multisets, and effective plot settings.

The earlier draft used a mutable image tag, three source hashes, direct package writes, a FileFunction substring, and drill counts.
Do not accept a final package from those weaker checks. Wait for final frozen code before a complete review.
The author has a workflow test process in progress and a known non-plated fixture correction.
New files include `scripts/workflow.py` and `scripts/review.py` in the fabrication skill.

## Reviewer process

Pi compacted automatically during the geometry review. Its harness and model stayed unchanged.
It then repeated probes after their results were available. The lead stopped that turn with Escape and requested the report only.
The report is complete. No further action on that interruption is necessary.
Pi corrected two report errors: its timing fixture was a row, while root used a column, and source exclusions already had positive evidence.
Root used constant X with increasing Y. The X-only window retained all pairs. Pi's first comparison incremented X.
Neither timing result exceeded two seconds. The finding concerned absent enforcement.
Pi also corrected speculative claims about CRLF and distinguished a radius support policy from geometry validity.

## Assembly preparation completed during B7 work

Root retained these Sierra sources under `docs/reviews/sierra-source-evidence/`:

- `xy.pdf`, SHA-256 `eea02acc5362804e76e7586e62b7d8182284d9d35cc9e853103d8d76cc992590`.
- `xyrs.xlsx`, SHA-256 `8b3d93beec8ea96851a62e98f8d26e29f9cb85d0874304e9ab373d1d11c0ed93`.
- HTTP headers and `turnkey-faq.html`.

The Turnkey PRO FAQ links the earlier PDF. The Web PCB FAQ links the workbook.
They use different columns and side labels. The workbook repeats references and contains conflicting example rows.
Neither supplies the complete placement transform. Do not infer supplier geometry from example rows.
The Turnkey PRO FAQ itself confirms inch RS-274X, absolute inch drills, trailing-zero suppression, and 2.4 format.
It requests a fabrication drawing in Gerber format. Keep that separate from local PDF documentation.
Its negative-plane guidance remains unresolved for the current exporter.
Both reviewers agreed with `b9-source-addendum-root.md` after the service-source clarification.
The plan includes these findings.

Root measured the inch drill command with the existing image on a temporary board copy.
See `b9-drill-probe-root.md`, `sierra-source-evidence/drill-probe.json`, and the retained script.
The output has a 2.4 inch format comment and `INCH,LZ`. This proves availability, not full coordinate fidelity or supplier acceptance.
`b9-proposal-inputs-root.md` lists concrete remaining choices for the author's future assembly proposal.
It does not authorize B9 code before agreement.

Root added `XYRS` to the glossary. Older B6 and B7 prerequisite manifest hashes therefore remain historical.
The six geometry files do not include the glossary.

## Next work

Continue the authorized B7/B8 implementation and review. Then have Claude prepare the compact B9/B10 proposal.
Use the existing preparation reports for B11 and B12. Do not restart broad research.
Preserve all failed attempts, explicit unsupported paths, and exact tested hashes.

## 2026-11-15 04:37 UTC continuation

The Claude author reached the provider usage limit. The assigned models stay unchanged.
The lead stopped automatic resume in fabrication pane `w1P:p4` and PCBA pane `w1P:p7`.
The lead owns the PCBA correction until one complete replacement freeze. Both reviewers hold.
Do not edit the PCBA files from another pane. Do not use another account to bypass the limit.

The shared BOM evidence role now includes `supplier_profile`.
The source and PCBA validator hash is `31af5f8764f7e3027cbaeb1fee3c0523ec7f9745f2b23e1ad1670ed28a7a4f41`.
The main tool tests pass 59 of 59. The copy tests pass 2 of 2.
The integration tree must receive the same validator bytes and role regression.
Historical worktrees retain their previous bytes.

The PCBA correction now compares staged hashes and byte counts after full validation.
An owned pcbnew worker measures all drilled pads and vias from captured board bytes.
The Sierra command uses `manufacturing/supplier.yaml` and the canonical content hash.
Its status record binds the full input hashes.
The independent BOM comparison applies the hand-install policy and compares the manufacturer.
The test-record comparison examines the variant, instruction and duplicate step IDs.
Focused probes pass. Full tests and the new retained package remain in progress.
No replacement freeze exists yet. No commit or push occurred.

## 2026-11-15 04:54 UTC continuation

The accepted static release files now have integration commit `cb5d5b0` after B11 commit `46d23ef`.
The release integration passes packaging 32, harness 65, isolation 29, artifact expectations 23 and artifact fixtures 16.
Required checks pass snippets 52 with 5 declared skips, and print tools 6. No push occurred.
The integration record is `docs/reviews/release/b12-integration-acceptance-root.md` in the integration tree.
The main README and AGENTS edits remain outside that commit.

The PCBA replacement has 113 files and passed 105 tests. Both reviewers accepted its five corrections.
Two residual findings have a released correction in `pcba/docs/reviews/pcba/b10-role-and-drill-correction-root.md`.
The test-record evidence must include `board_record`. The new validator hash is `974c38b93d24fc2a53c8aaab814410abbdb86b58bdf966cbec0e5181cbe169f5`.
The source and current main and PCBA copies agree. Integration still holds the previous role table until the PCBA merge.
The drill path now refuses settings outside absolute/inch/trailing/four-decimal/separate-file support before export.
The existing schema refuses a combined drill file first with `schema.invalid`.
The other five unsupported settings use `export.drill_setting_unsupported`.
The retained package and final tests are in progress. Both reviewers hold for the replacement.

The lead diagnosed the B7 internal-track result with two controlled scratch cases.
At a 9.9 mil hole gap with valid copper spacing, the unchanged supplier rules report the expected hole violation.
At the original 0.2 mm hole gap, a relaxed copper-spacing rule reveals the hole violation.
The earlier separate copper-spacing violation suppressed the hole finding for this pair in these runs.
Record: `docs/reviews/b7-internal-clearance-diagnosis-root.md`.
Scratch paths: `/tmp/b7-internal-clearance-root` and `/tmp/b7-internal-spacing-control-root`.
Retain these diagnostic bytes before later cleanup. No B7 product code changed for this diagnosis.

## 2026-11-15 05:19 UTC continuation

Both PCBA reviewers accepted the 128-file replacement at manifest hash d419688f2e4b5b30a35209985f619c2fc46ae2d58c2a1d949feb9ab24079ca64.
Root copied it to integration, added the snippet route, and corrected two guide sentences.
Both reviewers accept those sentences. Guide hash: 6b1d71ae14b503a513328efac46ca0fb1d67dd7ed57b12dffd54fe13ca1730cf.
Integration tests pass PCBA 106, packages 8, snippets 52 with 5 skips, print tools 6, and harness 65.
The shared suite passed 58 before its stale two-job CI expectation failed. The corrected three-job function passes alone.
Codex accepts that test correction. No PCBA integration commit exists yet. Accepted files are staged.
The integration file list is docs/reviews/pcba/b10-integration-files-root.sha256. Refresh its hashes before the commit.

Packaging exposed 17 A2 output paths after Git tracked them. The old substring rule misclassified them as supplier sources.
Both reviewers asked for the documented two-root classifier, not fixture allowlist entries. Root applied that correction.
The candidate list now includes untracked nonignored files. Packaging passes 34 and harness passes 65.
The integration-only replacement freeze is docs/reviews/b12-distribution-integration-freeze-r2-root.sha256.
Its 200-entry hash is 2c92bbe9d79279b65818fd3d91473283525904c230fa48bf7e78dbfef9d8b392. Both release reviewers are examining it.
The earlier integration proposal and record remain history. The distribution manifest itself is unchanged.
A3 proposal has both reviewer agreements. Copy 59 accepted PCBA fixture files to release-local A3 paths.
Add length_equals and row_binding, with all produced-package expectations under base run. A3 stays held.

B7 rows 23 and 24 have both reviews and root acceptance. The 40-entry manifest is c6a417802c5a2ccdb8cf8256fa04e3fe6f8c33a8d1cfd2ef21a7dc1c86f9d8aa.
Root implemented the via measurement worker and supplier row service.via_construction_prohibited.
The route follows b7-via-implementation-root.md. B6 is unchanged.
The focused via suite passes 16 and the workflow suite passes 132.
Logs: docs/reviews/b7-completion-evidence/via-root/. This is not a complete B7 freeze.
Remaining: corner compatibility, manual silk board cases, the other acceptance gaps, and full standalone operation.
The new worker and test are scripts/via_inventory.py and tests/test_pcb_fab_vias.py.
The main and PCBA contract README copies now match d199730d477ae17514d314f1073f4f440d9aff1d0a335b8891c7ee49095d9788.
Claude author panes remain idle under the provider cap. No model changed and no provider evaluation occurred.

## 2026-11-15 05:41 UTC continuation

Integration commits now include PCBA `8d0f509` and A3 `a6816ce` after the accepted mechanical and static release commits.
Both release reviewers accepted A3 freeze `7ae60dedf3ca70de0fcb79b4fef9f96a58bf764905fbc9d5d314ea51b116290a`.
A3 stays held and unqualified. Provider authorization stays zero. No push occurred.
Pi release wrote `b12-release-handoff-pi.md` at 68 percent context. Root issued `/new` and the restore prompt.

B7 corner tests pass 16, via tests pass 16, manual silk tests pass 9, and rule boundaries pass 18.
The updated workflow passes 132 and package geometry passes 101. The acceptance suite passes 35.
The required-evidence test passes 2 with a generated package missing `fab.supplier_rules`.
The dimension test exposed stroke-width inflation in the B7 board inventory. The failed run is retained.
Root corrected only the B7 derivative to measure zero-width Edge.Cuts in memory. The source board remains unchanged.
The corrected dimension run and standalone trial remain in progress. No complete B7 freeze exists.
The standalone runtime record states the native Podman defect and the existing local service route.
Do not run `podman system migrate`. Unrelated user containers remain active.
Use `CONTAINER_HOST=unix:///run/user/1000/podman/podman.sock` for current container tests.

## 2026-11-15 05:53 UTC continuation

B7/B8 complete freeze: `docs/reviews/b7-completion-freeze-root.sha256`, 239 entries.
Manifest hash: `3f5904c28ba21ee8f09f4c480ff02a439741d59cceacff300ca9925ed0e4a411`.
Record hash: `d299cc5517fffd1ad99bbc215d31d999b5ea813f8b1822244bcf87c21f423a30`.
Completion record: `docs/reviews/b7-completion-root.md`.
Codex accepts it in `b7-completion-freeze-review-codex.md`, hash `a4df61c7e8c33f1afa11c6c69c21590ab08d6912d74727b4b1436fb2b38617d7`.
Pi is still examining the same frozen bytes. Do not change any listed file until the review ends.
Pi fabrication restarted from `pi-skill-dev-handoff-2026-11-15.md` and now uses about eight percent context.

New final tests pass: dimensions 18, outline stroke independence 12, large drills 6, required evidence 2.
The workflow after the outline correction passes 132. The standalone trial passes seven commands and the full installed validator.
The retained standalone root is `/tmp/fab-standalone-root-65s7_0zf`.
The complete evidence directory is `docs/reviews/b7-completion-evidence`.
The suite code comparison proves that the standalone runtime code matches the frozen source.
Its synthetic manual and offline source evidence do not establish physical results or a current supplier review.

The release documentation has a separate three-entry freeze in the integration worktree at `docs/reviews/release/repository-docs-root.sha256`.
It adds the PCB catalog and local release tests to README and AGENTS.
Codex found an overbroad local-image sentence. Narrow it to KiCad tool operations after Pi reports.
The documentation is uncommitted. The unrelated integration handoff diff also remains uncommitted.
The next product step after B7 acceptance is B7 integration, then a separate A2 refresh with the new profile and declaration.
The native Podman route remains unavailable. Use the existing local service through CONTAINER_HOST for container tests.
No system migration, container stop, model change or provider evaluation occurred.

## 2026-11-15 05:58 UTC continuation

The native Podman route recovered. It reads the same image and runs KiCad 10.0.5.
Root made no runtime metadata edit, service restart or container migration.
The separate addendum is `b7-native-runtime-recovery-root.md`. The frozen service-route evidence stays unchanged.

Pi fabrication is still examining the complete 239-file freeze.
It repeated several focused suites and then the package and workflow suites despite the narrow-review instruction.
Root told it to finish the active workflow run and give its verdict without more suites.
Codex fabrication already accepts the complete freeze.

Pi release entered a repetitive text loop during the three-file documentation review.
Root sent Esc, then `/new`, and confirmed a fresh session at zero percent.
Its new prompt limits the task to the integration README/AGENTS diff and the known image-sentence correction.
The model and reviewer role remain unchanged. No product file changed during the reset.

The integration tree also has an unfrozen A2 refresh scope at `docs/reviews/release/b12-a2-refresh-scope-root.md`.
It follows B7 acceptance. It keeps A1/A3 and quantity 5 unchanged.
It updates only two project inputs from the RC template: board.yaml profile/declaration and manufacturing/supplier.yaml.
It updates the external profile copy, reruns profile/design/supplier, and retains the exact order-failure and silk-pending sets.
It proposes optional json_path in the existing sha256_binding checker for the new report bindings.
The checker must retain the existing top-level key form. No new kind is necessary.
No A2 product or fixture byte changed yet.
