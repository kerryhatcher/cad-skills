# Lead continuation state

Updated: 2026-11-15, approximately 02:39 UTC.

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
