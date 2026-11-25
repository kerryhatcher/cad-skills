# B12 matrix review from codex-release-dev

Date: 2026-11-15 UTC.

Scope: section 2 counts and section 7 isolation rules in revision 3. This review does not approve paid runs.

## Count review

The section 2 arithmetic is correct:

| Group | Calculation | Runs |
|---|---:|---:|
| Routing | 3 skills × 6 cases × 3 hosts × 3 repeats | 162 |
| Artifact, skill arm | 3 skills × 3 hosts × 1 | 9 |
| Artifact, baseline arm | 3 skills × 3 hosts × 1 | 9 |
| Core | 162 + 9 + 9 | 180 |
| Explicit invocation | 3 skills × 3 hosts × 3 repeats | 27 |
| Compaction | 1 task × 3 hosts × 1 | 3 |
| Paid total | 180 + 27 + 3 | 210 |

The install count is also correct: 9 project copies + 6 symbolic links + 9 temporary-home copies = 24 checks. These checks do not add paid runs when the host can report discovery without a model call.

The paid total is not exact if an install check uses a model call. Set the number of such calls before approval, or state that all install checks use local host output. Add those calls to the total.

The token caps conflict. At 250,000 tokens per run, 210 runs can use 52,500,000 tokens. The batch cap is 50,000,000 tokens. Lower the per-run cap or increase the batch cap before approval. Include any paid install calls and retries in this calculation.

Section 3 offers a one-run option for R4 to R6. That option gives 108 routing runs and 156 paid runs. It conflicts with the lead's corrected 162-run matrix. Remove that option or ask the lead to replace the three-repeat matrix before implementation.

## Isolation findings

**Finding: one-skill installation cannot test the routing matrix.** Section 7 says to install one skill only. Section 3 tests an adjacent skill selection and no selection across three skills. A host cannot select an adjacent skill that the test did not install.

**Correction:** Define routing mode with all three accepted skills installed in the fresh root. Define single-skill mode for artifact tasks and explicit invocation. Keep the baseline root free of all three skills. Record all installed paths and all selected skill paths.

**Finding: the R2 cases do not define all three skill boundaries.** Revision 2 names two boundaries. Revision 3 names one general boundary. PCBA has no named R2 task.

**Correction:** Freeze one R2 prompt and expected owner for each target skill. For example, test board design against `pcb-design`, bare-board package work against `pcb-fab-package`, and assembly work against `pcba-design`.

**Finding: the route record does not state its value shape.** `selected_path` can name only one path, but all-skill routing and duplicate-name cases can expose multiple paths or no selected skill.

**Correction:** Store selected skill names and paths as lists. Use empty lists when no skill is selected. Keep discovered paths in a separate field.

**Finding: user-scope paths are not host-specific in revision 3.** The rule sets a temporary `HOME`, but it does not state the discovery directory for each host.

**Correction:** Record the temporary-home skill path for Codex, Claude Code, and Pi. Test that each host reads from that path. Confirm that the real home stays unchanged.

**Finding: ignored run data and a fresh directory do not block repository access.** Revision 3 states this limit. The test record must not imply that the root isolates shell access.

**Correction:** Keep the stated limit in each result. Record that repository files, credentials, and sibling skills remain readable when host tools can access them. Do not change trust or permissions.

## Other matrix blockers

The artifact count includes one PCBA task per host, but section 10 blocks A3 until its package is accepted. The count is a plan, not an executable batch until A3 has a frozen fixture and independent checks.

A1 also remains blocked until the lead accepts B7/B8. Exclude blocked artifact cells from paid execution until their inputs and expectations are accepted. Revise the paid count before execution if a blocked cell leaves the matrix.

The three-repeat matrix, PCBA artifact expectation, install-call count, and token caps need lead acceptance before any paid run. Do not start paid evaluations before that decision.

This review did not run tests or paid evaluations. It did not change trust, credentials, or host permissions.

## Addendum: lead decisions at 01:51 UTC

The lead accepts `tests/eval/`, `docs/release-licensing.md`, the 210-run design, and 24 local installation checks. Both final reviews remain necessary. No provider batch starts until the integrated skill artifacts pass review.

The lead's run limits fit the accepted schedule:

| Run group | Runs | Limit per run | Maximum reported tokens |
|---|---:|---:|---:|
| Routing and explicit invocation | 189 | 30,000 | 5,670,000 |
| Artifact, baseline, and compaction | 21 | 250,000 | 5,250,000 |
| Scheduled paid runs | 210 | — | 10,920,000 |
| Batch cap | — | — | 12,000,000 |

This leaves 1,080,000 reported tokens below the batch cap. The 24 install checks do not use provider calls. Do not use that margin for extra runs. The lead set a ceiling of 210 scheduled runs and no automatic retries.

Record reported token counts when a host or provider returns them. Mark missing counts as unavailable. Do not describe reported tokens as provider billing or as a measure of all provider use. Before each request, reserve that run group's full token limit from the remaining batch budget. If the host cannot enforce a token limit before a request, record that limit as unenforced. Stop before the next request if the remaining budget is below that request's limit. Test the budget ledger and stop rule with mock usage data. Do not call a provider to test these limits.

Keep the isolation correction from this review: routing mode installs all three skills. Single-skill mode supports artifact and explicit invocation tests. A single installed skill cannot satisfy an adjacent-skill routing case.

## Addendum: source and package boundary

The repository inventory records full OSH Park supplier pages and headers. Permission to redistribute them remains unconfirmed. Keep the local evidence files. Do not include full supplier pages or documents in a release bundle until permission is established.

**Packaging proposal for the fabrication team (updated for P1–P4):** use a source manifest, an explicit setup fetch, and local evidence that stays outside distribution. Keep the current evidence files. Release artifacts and public source publication must exclude unlicensed full supplier copies. Do not delete evidence or change runtime behavior silently. The fabrication team owns the smallest runtime change from its frozen correction. A changed source hash needs a new recorded source review and profile binding. Do not accept changed bytes automatically.

Treat license state as information for local retrieval and as a separate input to the distribution decision. Do not add a mandatory license acknowledgment gate for an ordinary public-page fetch. A user's acknowledgment does not establish distribution rights. Do not contact suppliers or use credentials.

Test inventory and exclusion rules in `tests/test_release_packaging.py`, with project-authored page fixtures. Use an explicit provenance manifest and distribution allowlist. Check known `supplier/pages/**` files and known Sierra evidence paths, including `.headers` files, as exclusion regressions. Keep local evidence outside release artifacts and public source packages.

The source manifest records URLs and expected hashes. Do not add a second source approval record. Existing supplier-profile content and evidence hashes, with the existing source-review record, remain the binding authority. A changed source hash needs a new recorded review and profile binding. Do not accept changed bytes automatically.

Use file paths, manifest hashes, and the allowlist to decide distribution. File extensions and file magic identify format only. They do not identify license or ownership. Do not reject a project-authored PDF or HTML fixture by type alone.

Zero fetch scripts are acceptable for a provisional packaging test. A final standalone release needs the explicit setup fetch path. The fabrication team owns that path and its smallest runtime change. The release team can implement the inventory and exclusion checks after this interface agreement. Reviewers remain reports-only.

The Containerfiles only refer to pinned images. This feature does not publish a built image. Keep image references separate from image redistribution in the notice inventory.

For KiCad symbol data embedded in design files, cite the [KiCad Libraries License](https://www.kicad.org/libraries/license/) (retrieved 2026-11-15). It states CC-BY-SA 4.0 for the libraries and an exception for electronic designs and their generated files. It also states that redistributed library collections retain the license and attribution. Do not apply the design exception to a redistributed library collection. Keep the file's attribution information. A copyright line alone does not decide all use rights.

For KiBot 1.9.1, record the license text from the [v1.9.1 `LICENSE` file](https://raw.githubusercontent.com/INTI-CMNB/KiBot/v1.9.1/LICENSE) and retain the measured image and package metadata. The upstream file states AGPL-3.0. The measured image metadata states GPL-3.0. Keep this conflict open. Record the source tag, version, hash, retrieval date, and both observations. Do not silently replace one observation with the other.

For B11, identify each project-authored proxy as a proxy. Record its source path, hash, retrieval date, and applicable license evidence. Do not describe a proxy as a third-party part model or as evidence of detailed fit.

For each redistributed item, inventory its hash, source URL or project source path, retrieval date, applicable license evidence, and attribution. Keep unresolved permissions open. Do not label third-party material MIT based on the repository license or a `SKILL.md` field.

## Addendum: Codex agreement with the packaging interface

Codex agrees with findings D-1 to D-8 in `docs/reviews/release/supplier-page-packaging-boundary-pi.md`, with the lead answers to Q1 to Q3. Use `tests/test_release_packaging.py`. Use the provenance manifest, distribution allowlist, and explicit exclusion regression checks described above.

The provenance manifest does not approve new bytes. Existing profile hashes and the source-review record remain authoritative. Keep project-authored fixtures eligible by provenance, even when their format is HTML or PDF. Zero fetch scripts pass a provisional packaging test, but not the final standalone release gate.

This is the Codex reviewer's interface agreement. Claude owns product changes. Codex made no product edits and ran no provider calls.
