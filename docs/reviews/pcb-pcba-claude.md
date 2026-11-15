# Review of the PCB and PCBA plan (Claude)

Reviewer: Claude Code, model Haiku 5.5 (`claude-haiku-5-5`).

Plan reviewed: `docs/pcb-pcba-plan.md` (311 lines, research date 2026-11-13).

Scope: Technical accuracy, missing requirements, skill independence, integration risks, supplier assumptions, tests, and phase order. This review changed no file except this report. It did not change the plan, glossary, implementation, or tests. It made no commits, supplier contacts, comments, or agent starts.

## 1. Evidence and method

Repository files read:

- `AGENTS.md` (STE rules, repository conventions, cross-skill rule).
- `CLAUDE.md` (imports `AGENTS.md`).
- `docs/pcb-pcba-plan.md` (all 311 lines).
- `tests/test_snippets.py` (header and inline dependency list).
- `.github/workflows/test.yml` (CI steps and permissions).
- `skills/` directory layout (cadquery, print-prep, prusaslicer, structural-analysis).
- `README.md` (agent host claims, STE note).

Primary online sources checked:

- OSH Park two-layer service page: https://docs.oshpark.com/services/two-layer/ (fetched during this review).
- Sierra Circuits Turnkey PRO page: https://www.protoexpress.com/products/turnkey-pro/ (fetched during this review).

Primary online sources cited by the plan that I did not check in this review:

- SKiDL on PyPI: https://pypi.org/project/skidl/
- SKiDL manual: https://devbisme.github.io/skidl/
- KiCad 10 CLI reference: https://docs.kicad.org/10.0/en/cli/cli.html
- KiCad IPC API: https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/
- KiBot documentation: https://kibot.readthedocs.io/en/latest/
- OSH Park KiCad design tools: https://docs.oshpark.com/design-tools/kicad/
- OSH Park four-layer, six-layer, single-layer, and two-layer HHDC pages (only the two-layer page was checked).
- JLCPCB BOM and centroid guide: https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad
- TI application notes cited at lines 138, 140, and 142.

Severity labels used in this report:

- **Confirmed defect**: The plan text conflicts with the repository, a primary source, or itself. The fix is required before the plan is used.
- **Refinement**: The plan is consistent but leaves a gap or a choice open. The fix improves the plan.
- **Open question**: I could not settle the point from the material I checked.

## 2. Verified facts

- The OSH Park two-layer row at plan line 178 matches the live page. The page gives:
  - Trace width and spacing: 6 mil (0.1524 mm).
  - Minimum drill: 10 mil (0.254 mm).
  - Minimum annular ring: 5 mil (0.127 mm).
  - Board thickness: 63 mil (1.6 mm) nominal.
  - Copper weight: 1 oz on each of the two layers.
  - Edge clearance: 15 mil from the nominal board edge. The page gives no unit, so the value is presumed to be mil.
  - Minimum drilled slot: 20 mil (0.508 mm), drill slot only.
  - Silkscreen: 5 mil (0.127 mm) recommended for general lines, and 3 mil (0.0762 mm) for short lines, text, and graphics.
  - Source: https://docs.oshpark.com/services/two-layer/
- Plan line 185 correctly separates the recommended silkscreen width from its smaller conditional limit.
- The Sierra Turnkey PRO page states in-house assembly. It lists PCB fabrication and component procurement under "Create your boards entirely online." Source: https://www.protoexpress.com/products/turnkey-pro/
- The Sierra page requires an Excel BOM for quoting. It states that XY data and an assembly drawing are required in the final package. It names no centroid file format. It states, "Arrayed designs are not allowed." Sierra engineers array the board as needed.
- `tests/test_snippets.py` declares only `cadquery` as an inline dependency. The plan at line 255 says this is true.
- `.github/workflows/test.yml` runs only the snippet test and the print-tools test. It contains no `permissions:` block.
- The phase estimates at lines 241–247 sum to 18 to 28 days. The plan total at line 249 is correct.
- The plan contains no semicolons and no contractions. I found no Latin abbreviations or the word "via" in the plan text.

## 3. Confirmed defects

### D1. Phase order conflict: P3 and P4 are not independent (high)

- **Lines:** 244–249, 209, 245.
- **Problem:** Line 249 says P3 and P4 can proceed independently after P1. But the release package at line 209 needs Gerber and Excellon output, and P3 produces those. The P4 completion criterion at line 245 requires that the files agree.
- **Effect:** P4 cannot pass its completion criterion until P3 provides the manufacturing files. The schedule at line 249 is therefore wrong.
- **Correction:** Split P4 into two parts:
  - P4a: BOM, placement, variants, DNP, and assembly records (depends on P1 and supplier evidence).
  - P4b: release package integration, including Gerber, drill, and file agreement checks (depends on P3).
  Update the dependency column and the 18–28 day estimate.

### D2. The schematic-to-board update path is not named (high)

- **Lines:** 156–160, 163.
- **Problem:** Line 156 requires an update operation supported by the selected KiCad version. Line 157 says not to invent a CLI command. The plan names no candidate operation. The fallback at line 163 covers failed generated schematics only. It does not cover a failed board update.
- **Effect:** The P1 criterion at line 242, "layout survives defined edits," cannot be automated without a headless update path. P1 can block the whole plan. Line 160 requires measured retained positions, and that measurement needs a repeatable update.
- **Correction:**
  - Add a P0 task. Test the candidate operations on the pinned KiCad version. Candidates include the KiCad 10 CLI, the IPC API, and the Python scripting API. Record the result.
  - Add a fallback for each outcome. One fallback is a documented manual sync with recorded evidence. Another is the native KiCad schematic path already described at line 163.
  - Keep the rule at line 157 that prohibits an invented command.

### D3. Ownership of the manufacturing export is ambiguous (high)

- **Lines:** 73, 74, 78, 209.
- **Problem:** Line 73 gives `pcb-fab-package` the supplier-specific fabrication package. Line 78 gives `pcb-design` neutral manufacturing exports. Line 78 also requires `pcba-design` to include its own manufacturing export configuration. Line 74 requires `pcba-design` to deliver a complete PCBA package, which includes the Gerber files listed at line 209.
- **Effect:** Three skills contain overlapping export logic. The configurations will drift. An agent cannot tell which skill owns a given Gerber or drill setting. This weakens the independence rule at line 78.
- **Correction:**
  - Make `pcb-design` the sole owner of neutral export logic.
  - Copy the export configuration into `pcba-design` and `pcb-fab-package` under their own `templates/` or `scripts/` directories.
  - Add a test that the copies agree. Extend the copy test beyond schemas, as described in D8.
  - Define the content of `pcba-design`'s "complete PCBA package." State which fabrication files it includes, and which it references by hash.

### D4. The BOM and placement format cites the wrong supplier (medium-high)

- **Lines:** 199, 205.
- **Problem:** Line 205 cites JLCPCB for the BOM and centroid format. Line 199 names Sierra as the first PCBA adapter. The Sierra page states an Excel BOM and XY data. It names no centroid file format. It also states that arrayed designs are not allowed.
- **Effect:** The Sierra adapter would use a format that Sierra has not published. An order with a designer-supplied array could be rejected or reshaped.
- **Correction:**
  - Cite Sierra's own format and panelization rules in the Sierra profile.
  - Ask Sierra in writing for the placement file format. Record the answer as an open item in the profile. Do not contact the supplier without the user's approval.
  - Add a panelization rule to the Sierra profile. State that the designer does not array the board.

### D5. New tests are not wired into CI or the agent instructions (medium)

- **Lines:** 264–272, 257–262.
- **Problem:** The CI workflow runs only the snippet test and the print-tools test. `AGENTS.md` lines 131–133 list only those two commands. The plan adds three test commands but does not say to update CI or `AGENTS.md`.
- **Effect:** The new tests will not run on pull requests. Contributors and agents will not know the commands exist, so they can skip them before a commit.
- **Correction:**
  - Add the three new test commands to `.github/workflows/test.yml`.
  - Add a separate CI job that uses the fixed KiCad container.
  - Update the command list in `AGENTS.md`.
  - Add these changes to the P0 task list.

### D6. The snippet runner cannot run KiCad or SKiDL examples (medium)

- **Lines:** 255, 169, 264.
- **Problem:** `tests/test_snippets.py` declares only `cadquery`. Line 255 forbids hiding executable examples with `# notest`. The plan does not say where KiCad or SKiDL blocks run.
- **Effect:** PCB documentation blocks either fail in the current runner or require a marker the plan forbids.
- **Correction:**
  - Give each new skill its own PEP 723 dependency group, or a separate runner.
  - Run KiCad-dependent blocks only in the container job from D5.
  - State in the plan which blocks run in which job.

### D7. CI does not set read-only permissions (low-medium)

- **Lines:** 274.
- **Problem:** `.github/workflows/test.yml` has no `permissions:` block. Line 274 requires read-only permissions, but the current workflow does not provide them.
- **Effect:** The workflow token has the repository default permissions.
- **Correction:** Add `permissions: contents: read` at the workflow level. Grant more permissions only inside a release job, as line 274 already says.

### D8. Shared schema and script copies cannot drift without a test (low-medium)

- **Lines:** 53, 56, 78.
- **Problem:** Line 56 requires a test that schema copies agree. The plan does not require a test for shared scripts or configuration, even though D3 would create copies of export configuration.
- **Effect:** A script or configuration copy can change in one skill and not in another. The schema test does not detect this.
- **Correction:** Extend the copy-agreement test to every file that exists in more than one skill. Compare file hashes or normalized content.

### D9. Required items are missing from the plan (medium)

These are gaps, not contradictions. Each one should appear in `board.yaml`, a supplier profile, or the release list.

- **Export control.** Line 199 mentions ITAR only as a supplier exclusion. Add an export-control field to `board.yaml`. Add a gate before supplier selection at line 122.
- **Part lifecycle.** The part record at line 114 has no end-of-life or not-recommended-for-new-designs status. Add lifecycle status and a stock check.
- **Licenses.** Line 169 covers simulation model licenses only. Add license records for KiCad libraries, footprints, 3D models, KiBot (GPL), Freerouting, ngspice models, and SKiDL (MIT). The MIT license for this repository is at `LICENSE`.
- **Panelization.** P4 does not include a panel design, tooling holes, or rails. Add these to the assembly records. Link them to the Sierra rule in D4.
- **Stencil output.** The release list at lines 207–219 does not include stencil files. Line 142 requires stencil apertures to be examined. Add stencil output to the package.
- **Surface finish and soldermask color.** The OSH Park profiles at lines 173–183 do not record finish, soldermask color, or thickness tolerance. Add them to each profile.

### D10. Exit codes are not specified (low)

- **Lines:** 80.
- **Problem:** Line 80 requires a nonzero status for missing prerequisites and for design failures. It does not say whether the two conditions use different codes.
- **Effect:** An agent or CI job cannot tell the two conditions apart from the exit status.
- **Correction:** Assign distinct exit codes. Document them in each CLI's `--help` output and in the JSON report.

### D11. The one-writer rule has no mechanism (low)

- **Lines:** 61–62.
- **Problem:** Line 61 says to limit each board file to one writer. The plan names no lock file, lock location, or stale-lock behavior.
- **Effect:** Two agents can write the same board at the same time.
- **Correction:** Specify a lock file in the project root or in `out/`. Define how a stale lock is detected and cleared, and how the user is told.

## 4. Refinements and work already planned

- **R1. Test steps for the trial.** Lines 150–160 describe the trial. Add a step that records the KiCad version, SKiDL version, and container digest for each run. Line 304 requires this for packages, but the trial should record it too.
- **R2. Tool version pinning.** Line 19 requires a fixed patch version. Line 21 requires a pinned KiBot container digest. Add the same rule for SKiDL and ngspice, with hashes recorded in `toolchain.lock.json` (line 91).
- **R3. Supplier data freshness.** Line 116 records a retrieval date and an evidence hash. Line 193 requires a comparison with the live page before release. Add a maximum age for a profile, after which the profile is marked unconfirmed.
- **R4. Evaluation of agent behavior.** Line 291 requires agent evaluations. Add a negative case in which the user asks the agent to contact a supplier or place an order. The agent must refuse without the user's explicit approval. This follows line 66.
- **R5. Prompt injection from supplier pages.** Line 64 says to treat datasheets and supplier pages as data. Add a test that a supplier page containing instruction text does not change the agent's behavior.
- **R6. KiCad library versions.** The plan does not say which KiCad library version the trial uses. Record the library version in `toolchain.lock.json`.
- **R7. Freerouting runtime.** Line 24 keeps Freerouting optional. Freerouting requires Java. Add Java to the container definition if the optional path is used.
- **R8. Reflow and assembly process data.** The release list does not include a reflow profile for PCBA. Add it to the assembly records for Sierra, after the supplier confirms that it accepts the data.
- **R9. Tool licensing for distribution.** The repository is MIT licensed (`LICENSE`). Confirm that KiBot (GPL) and Freerouting (GPL) run as separate tools and are not bundled in the skill files. This avoids a license conflict.

## 5. Open questions

- **Q1. SKiDL version and tags.** Line 17 cites SKiDL 3.0.0 dated 2026-10-16 on PyPI (https://pypi.org/project/skidl/). Line 18 cites a tags feature in the SKiDL manual (https://devbisme.github.io/skidl/). I did not check either claim. Confirm both before P1.
- **Q2. KiCad CLI flags.** Line 167 cites `--exit-code-violations` and `--schematic-parity` for KiCad 10 (https://docs.kicad.org/10.0/en/cli/cli.html). The plan already requires a check of the installed help. Record the result in the P1 report.
- **Q3. KiBot release.** Line 21 says KiBot 1.9.1 gives better KiCad 10 support. I did not check this claim (https://kibot.readthedocs.io/en/latest/).
- **Q4. OSH Park HHDC and other rows.** Line 179 (two-layer HHDC, 0.8 mm, 2 oz) and the four-layer and six-layer rows at lines 180–181 were not checked. Check them against the live pages before P3.
- **Q5. OSH Park edge clearance unit.** The live page gives 15 mil without a unit. Confirm the unit with OSH Park before the profile is marked qualified.
- **Q6. TI citations.** Lines 138, 140, and 142 cite TI application notes. I did not check them.
- **Q7. Scope of tscircuit.** Line 29 gives the current tscircuit capabilities. The plan does not record whether tscircuit is in scope. Record the decision.
- **Q8. The word "should" under STE.** Lines 80 and 207 use "should." Check whether the glossary tool treats it as approved.
- **Q9. Plan file in Git.** `docs/` is untracked. Commit the plan before the review is finalized. This review does not commit it.
- **Q10. Sierra placement format.** Ask Sierra in writing for the placement file format. Do not contact the supplier without the user's approval.

## 6. Summary of defects by severity

| ID | Severity | Lines | Subject |
|---|---|---|---|
| D1 | High | 244–249, 209, 245 | P3 and P4 are not independent |
| D2 | High | 156–160, 163 | The schematic-to-board update path is not named |
| D3 | High | 73, 74, 78, 209 | Export ownership is ambiguous |
| D4 | Medium-high | 199, 205 | BOM and placement format cites the wrong supplier |
| D5 | Medium | 264–272, 257–262 | New tests are not wired into CI or `AGENTS.md` |
| D6 | Medium | 255, 169, 264 | The snippet runner cannot run KiCad or SKiDL examples |
| D7 | Low-medium | 274 | CI permissions are not set |
| D8 | Low-medium | 53, 56, 78 | Shared scripts and configuration can drift |
| D9 | Medium | 114, 122, 142, 169, 173–183, 199, 207–219 | Required items are missing |
| D10 | Low | 80 | Exit codes are not specified |
| D11 | Low | 61–62 | The one-writer rule has no mechanism |

The plan is sound in its direction. Its main risks are the untested board-update path (D2), the phase order (D1), and the export ownership (D3). Resolve these three before P1 starts.
