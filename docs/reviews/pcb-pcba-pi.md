# PCB and PCBA plan review

## Reviewer identity

- Harness: Pi coding agent (`AI_AGENT=pi`, `PI_CODING_AGENT=true`).
- Model: DeepSeek V4.1 Flash (`deepseek/deepseek-v4.1-flash`, provider `openrouter`).
- Reasoning level: `high`.
- Session: `01a1d80d-253d-7760-b95d-3d54d1134af3`.
- Pane: `w1P:p6`.

I did not prompt the lead pane. I made no file changes before this report.

## Review scope

I reviewed `docs/pcb-pcba-plan.md` (311 lines), the repository instructions in `AGENTS.md`, issue 1, and the repository files that the plan touches. I examined technical accuracy, missing requirements, skill independence, integration risks, supplier assumptions, tests, and phase order.

This report gives each finding as a confirmed defect, a suggested refinement, or work that the plan already includes. Each finding gives the plan line, the problem, the effect, and a proposed correction.

## Severity levels

- High: the defect can make the release incorrect or can stop the release.
- Medium: the defect can cause rework or a disagreement between skills.
- Low: the defect is small but causes a warning or a manual repair.
- Open question: the plan states a risk correctly. The outcome is not known.

## Method and evidence

The `web_search` and `web_fetch` tools failed with a billing error. I read the primary sources through `curl` instead. I used these sources:

- Issue 1: https://github.com/kerryhatcher/cad-skills/issues/1
- SKiDL on PyPI: https://pypi.org/project/skidl/
- SKiDL manual: https://devbisme.github.io/skidl/
- atopile on PyPI: https://pypi.org/project/atopile/
- KiCad 10 CLI: https://docs.kicad.org/10.0/en/cli/cli.html
- KiCad IPC API: https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/
- KiBot releases: https://github.com/INTI-CMNB/KiBot/releases
- KiBot imports: https://kibot.readthedocs.io/en/latest/configuration/imports.html
- OSH Park two-layer: https://docs.oshpark.com/services/two-layer/
- OSH Park two-layer HHDC: https://docs.oshpark.com/services/two-layer-hhdc/
- OSH Park four-layer: https://docs.oshpark.com/services/four-layer/
- OSH Park six-layer: https://docs.oshpark.com/services/six-layer/
- OSH Park single-layer: https://docs.oshpark.com/services/single-layer/
- OSH Park KiCad guide: https://docs.oshpark.com/design-tools/kicad/
- Sierra Circuits Turnkey PRO: https://www.protoexpress.com/products/turnkey-pro/
- tscircuit build: https://docs.tscircuit.com/command-line/tsci-build

I verified these plan citations as correct:

- PyPI lists `skidl` 3.0.0, dated 2026-10-16.
- PyPI lists `atopile` 0.15.9, Python `>=3.14,<3.15`.
- KiCad 10 CLI documents `sch erc`, `pcb drc`, `--schematic-parity`, `--exit-code-violations`, and `--refill-zones`.
- KiBot 1.9.1 exists and has KiCad 10 support.
- OSH Park shows 10 mil (2-layer and 4-layer) and 8 mil (6-layer) minimum drills, 5 mil and 4 mil annular rings, 10 mil drill-to-internal-copper clearance, a 15 mil edge keepout, and a 20 mil drilled slot.
- Sierra Turnkey PRO states "In-house assembly" and excludes ITAR orders.
- OSH Park still lists KiCad 9.x.
- tscircuit documents `differentialpair` and `copperpour`.
- The KiCad IPC API is in KiCad 9.0 and up. Headless mode came in KiCad 11.

## High-severity confirmed defects

### H1. The repository `.gitignore` ignores the proposed `parts/` directory

- Plan lines: 99 and 114.
- Problem: `.gitignore` line 19 contains `parts/`. This pattern matches a directory with that name at any depth. `git check-ignore -v board/parts/x.yaml` returns `.gitignore:19:parts/`.
- Effect: The part records are not committed. The BOM and the placement source data are absent from Git and CI. This breaks the plan rule to commit the source and supplier evidence.
- Correction: Rename the directory to `components/` or `bom/`. Rename is more safe than a negation rule. Add a CI check with `git check-ignore` on the board tree.
- Status: Confirmed defect.

### H2. The OSH Park profiles omit the via restrictions

- Plan lines: 175-191.
- Problem: The OSH Park service pages state "Buried Via No", "Blind Via No", and "Filled+Plated Vias (via-in-pad) No". Section 7 does not record these limits. Plan line 191 also lists blind vias in the test-board set, but no rule makes them fail.
- Effect: A `.kicad_dru` profile and DRC can pass a board that OSH Park cannot make. The board fails at supplier review.
- Correction: Add the three restrictions to each profile. Add via-type checks in `.kicad_dru` where KiCad can express them. Add a geometry or manual check for via-in-pad. Make line 191 test these as reject cases.
- Status: Confirmed defect.

### H3. The OSH Park profiles omit the internal-plane polarity rule

- Plan lines: 187 and 189.
- Problem: The 4-layer and 6-layer pages require "positive" internal planes. The data must show copper, not the absence of copper.
- Effect: Negative inner-layer data causes a wrong or non-manufacturable board. OSH Park can auto-correct it in an unpredictable way.
- Correction: Add the polarity rule to the 4-layer and 6-layer profiles. Validate the inner-layer Gerber polarity in the export check. Record manual evidence for the check.
- Status: Confirmed defect.

### H4. Manufacturing export logic is duplicated across three skills

- Plan lines: 54, 56, and 72-78.
- Problem: `pcb-design` exports neutral manufacturing files. `pcb-fab-package` builds supplier packages. `pcba-design` includes its own manufacturing export configuration. Line 54 forbids a cross-skill import. Line 56 tests only that schema copies agree. It does not test that the scripts agree.
- Effect: Three copies of Gerber, drill, and placement logic drift apart. Two skills can produce different files for one board. This defeats the independence goal in a different way.
- Correction: Define one neutral dataset contract. Add a conformance test that runs each skill export on the same KiCad project and compares the normalized outputs. Or let `pcba-design` consume the neutral dataset. Do not duplicate the exporter.
- Status: Confirmed defect.

### H5. The PCBA and fabrication boundary is not defined

- Plan lines: 73, 74, 78, and 207-219.
- Problem: Section 8 gives `pcba-design` the full package: Gerbers, drill, IPC-356, and a BOM. `pcb-fab-package` is the fabrication skill. The plan never states which skill builds the fabrication files for a PCBA project.
- Effect: A user can run both skills and get two different fabrication packages. Or a user can run neither.
- Correction: State the ownership. For a PCBA project, the single supplier package from `pcba-design` includes the fabrication data. `pcb-fab-package` serves bare-board projects. Add a test for this rule.
- Status: Confirmed defect.

### H6. The generated-schematic CI comparison is not normalized

- Plan line: 112.
- Problem: The plan says "Compare a fresh generated schematic with the committed version in CI." Generated KiCad schematics contain UUIDs, ordering, and possibly timestamps.
- Effect: A byte or text diff gives false failures on each run. The team will disable the check.
- Correction: Compare normalized pin-to-net and reference sets, as line 155 already does. Remove volatile fields before the comparison. Make the generation deterministic.
- Status: Confirmed defect.

### H7. The snippet runner cannot run PCB blocks as the plan implies

- Plan lines: 255 and 267.
- Problem: `tests/test_snippets.py` has a fixed PEP 723 header with `dependencies = ["cadquery"]`. The repository has no `pyproject.toml`. The plan says "Add explicit dependency groups for PCB examples" and "Do not hide executable examples behind `# notest`".
- Effect: A `SKiDL` or `kicad-cli` block in a PCB `SKILL.md` file fails the existing runner. There is no defined dependency group to add.
- Correction: State how PCB blocks run. For example, put them in `test_pcb_tools.py` with a KiCad container. Or extend the runner to select an environment by block marker. Do not claim that the existing runner supports them.
- Status: Confirmed defect.

## Medium-severity confirmed defects

### M1. The plan omits the minimum milling radius

- Plan lines: 185, 189, and 191.
- Problem: OSH Park outline milling uses a 0.068 in tool. Interior cutout milling uses a 0.040 in tool. These values set the minimum inside-corner radius. The plan mentions geometric tests for outlines and slots, but not the tool radii.
- Effect: A board with sharp inside corners cannot be milled. DRC can pass it.
- Correction: Add the minimum inside-corner radius to each profile. Add a geometry check for it.
- Status: Confirmed defect.

### M2. Mechanical exports are ignored by `.gitignore`

- Plan lines: 135 and 227.
- Problem: `.gitignore` ignores `*.step` and `*.dxf`. No such file is tracked in the repository.
- Effect: The board-to-enclosure handoff is not versioned. The CadQuery test cannot use a committed export.
- Correction: Decide which mechanical files to commit. Add a scoped negation, or force-add them. Record the source hash in the package manifest.
- Status: Confirmed defect.

### M3. KiCad editor state and backups are not ignored

- Plan line: 112.
- Problem: The plan says to ignore "local editor state, caches, and backups". `.gitignore` has no KiCad patterns.
- Effect: `fp-info-cache`, `*.kicad_prl`, `*.kicad_pcb-bak`, and `*-backups` can enter Git.
- Correction: Add the KiCad ignore patterns to `.gitignore`. Add a test that a board tree stays clean after a KiCad save.
- Status: Confirmed defect.

### M4. The variant and DNP model has no defined home or filter rule

- Plan lines: 110, 114, and 216.
- Problem: `board.yaml` states a variant. Each part record states a variant and a DNP flag. Section 8 requires DNP and variant records to agree across all files. No variants file and no filter rule exist.
- Effect: Two skills can interpret a variant differently. The BOM and the placement files disagree.
- Correction: Add a variants file to the board tree. Define the DNP set for each variant. Define how the BOM and placement generators filter by variant. Add a test with two variants.
- Status: Confirmed defect.

### M5. Shared project files have no owner map

- Plan lines: 61 and 110.
- Problem: The plan limits each board file to one writer. It does not state the writer of `board.yaml`, `manufacturing/supplier.yaml`, `manufacturing/kibot.yaml`, or the mechanical JSON.
- Effect: Two skills can write one configuration file. The plan rule then fails.
- Correction: Add an owner for each shared file. Make the read-only skills explicit.
- Status: Confirmed defect.

### M6. Schema version negotiation is undefined

- Plan lines: 55, 56, and 116.
- Problem: The plan says "Exchange project files through a versioned schema" and "If two skills contain the same schema, test that their copies agree." It does not define a canonical name, a version field, or a mismatch rule.
- Effect: A mismatch is silent. A skill can read a file that it does not understand.
- Correction: Define the canonical schema name and version. Reject a different major version with a clear message. Record the schema version in the JSON report, as line 80 already proposes.
- Status: Confirmed defect.

### M7. Component availability and lifecycle are not checked

- Plan lines: 114, 123, and 201.
- Problem: The plan records an MPN and a supplier part number. It says "Do not silently replace unavailable parts." It has no stock field, no lifecycle field, and no test.
- Effect: A PCBA order stops when a part is not available. An agent can select an obsolete part.
- Correction: Add a stock field and a lifecycle field to the part record. Add a test for an unavailable part. Keep the no-silent-replacement rule.
- Status: Confirmed defect.

### M8. The shared versioning and release workflow with the mechanical skills is not defined

- Plan lines: 110 and 233.
- Problem: Issue 1 asks for one versioning scheme and one release workflow for the case and the board. The plan mentions a release revision and different owners. It does not define the shared scheme.
- Effect: The board and its enclosure release apart. Their revisions disagree.
- Correction: Define one revision scheme. Record it in `board.yaml` and in the case metadata. Use one release job for both.
- Status: Confirmed defect.

### M9. The P2 and P5 mechanical deliverables overlap

- Plan lines: 72, 243, and 246.
- Problem: P2 (`pcb-design`) lists "mechanical exports" as a result. P5 lists "STEP/DXF/JSON export" as its work.
- Effect: Two phases own one deliverable. The schedule counts the work twice.
- Correction: Assign the mechanical export implementation to one phase. For example, P2 emits raw STEP and DXF. P5 owns `board-interface.json` and the CadQuery example.
- Status: Confirmed defect.

### M10. The supplier profile file is singular

- Plan lines: 103 and 116.
- Problem: The tree has one `manufacturing/supplier.yaml`, but the plan describes multiple supplier profiles with IDs.
- Effect: The file format is ambiguous. A reader cannot tell if the file holds one profile or many.
- Correction: Use a `suppliers/` directory with one file for each supplier. Or state that `supplier.yaml` holds a list with stable profile IDs.
- Status: Confirmed defect.

## Low-severity confirmed defects

### L1. The quantity rule is not checked

- Plan lines: 175-191.
- Problem: OSH Park orders are in multiples of three. The plan records the quantity in `board.yaml` but does not make sure the value is a multiple.
- Effect: A quote or an order fails at upload.
- Correction: Add a quantity rule for each service. Warn or fail when the quantity is not a multiple of three for OSH Park.
- Status: Confirmed defect.

### L2. Extra OSH Park limits are not recorded

- Plan lines: 175-191.
- Problem: The pages also give via tenting, via plating thickness (1 mil), overlapping-drill clearance (5 mil), and a maximum drill size (250 mil). The plan records none of them.
- Effect: Some boards fail at supplier review.
- Correction: Add these limits to the profiles. Mark the limits that KiCad cannot measure as manual evidence.
- Status: Confirmed defect.

## Suggested refinements

### R1. Define the neutral Gerber dialect

- Plan lines: 78 and 207-221.
- Problem: The plan says "neutral manufacturing files" and "Gerber". It does not define the dialect, the units, the drill format, the zero suppression, or the layer names.
- Effect: A neutral export can still be rejected. OSH Park detects the layer order through Gerber X2 metadata.
- Correction: Define the neutral export contract. For example, use RS-274X with X2 attributes, mm units, an Excellon drill file with plated and non-plated holes split, and a layer-name map.
- Status: Suggested refinement.

### R2. Add panelization and stencil data

- Plan lines: 207-221.
- Problem: PCBA suppliers frequently require panelization, panel-level fiducials, and a stencil file. The plan covers board-level fiducials and paste layers, but not panelization.
- Effect: An assembly order can be rejected or need repair.
- Correction: Add panelization and stencil data when the selected supplier requires them. Treat this as a supplier-specific item.
- Status: Suggested refinement.

### R3. Test the waiver behavior

- Plan line: 167.
- Problem: The plan says "Do not use broad suppression to pass CI." No test makes sure that a waiver has a reviewer and a reason.
- Effect: A broad suppression can enter the release.
- Correction: Add a test that rejects a waiver without a rule, an object, a reason, a reviewer, and a revision.
- Status: Suggested refinement.

### R4. Test the schema agreement between skills

- Plan lines: 56 and 286.
- Problem: The test table has an independence row. It has no row for the schema agreement between two skills.
- Effect: Two copies of one schema can diverge with no test failure.
- Correction: Add a schema conformance test. Add a multi-skill project test.
- Status: Suggested refinement.

## Work that the plan already includes

These items are correct. I list them to prevent a duplicate correction.

- The plan keeps supplier submission, uploads, and orders outside the initial software release.
- The plan treats datasheets and supplier pages as data, not as agent instructions (line 64).
- The plan separates missing prerequisites from design failures. It returns a nonzero status for each condition (line 80).
- The plan says "Never report an omitted test as a pass" (line 80).
- The plan keeps the tool versions pinned and the container digest pinned (lines 21 and 274).
- The plan keeps ODB++ and IPC-2581 optional (line 221).
- The plan records the owner of each constrained mechanical dimension (line 233).
- The plan states that an ERC or DRC pass does not prove correct operation (line 144).
- The plan requires the SKiDL-to-KiCad identity trial before the main instructions depend on it (line 148).

## Open questions

### O1. Sierra in-house bare-board fabrication is not confirmed

- Plan line: 199.
- Problem: The Turnkey PRO page states "In-house assembly" and "In-house CAM engineers". It does not clearly state in-house bare-board fabrication. The page mentions "integrated suppliers".
- Effect: The issue condition "one supplier performs fabrication and assembly in-house" can fail.
- Correction: Get a supplier statement for bare-board fabrication. Do not mark this condition confirmed before the statement.
- Status: Open question.

### O2. The headless schematic-to-board update operation is not proven

- Plan lines: 156, 157, and 311.
- Problem: The KiCad 10 CLI has no documented update-board-from-schematic command. The plan correctly does not invent one. P1 still depends on this operation.
- Effect: The identity trial can need manual steps. The P1 completion criterion can be unreachable.
- Correction: Prove the exact supported operation before P1. If none exists, change P1 to a documented manual procedure.
- Status: Open question.

### O3. The KiCad and KiBot container is not selected

- Plan lines: 21, 274, and 311.
- Problem: The plan says to use a fixed container and to pin the digest. It does not name the image or the digest. The current CI has no container step.
- Effect: The integration tests cannot run. Or they run against an unpinned KiCad. The version record in `toolchain.lock.json` is empty.
- Correction: Name one release-candidate image and digest in P0. Add the CI job. Record the value in `toolchain.lock.json`.
- Status: Open question.

### O4. The KiBot supplier template accuracy is not confirmed

- Plan line: 22.
- Problem: The plan says to "Test their columns and rotations against supplier specifications." The KiBot import files exist for JLCPCB, PCBWay, and MacroFab. The column and rotation correctness is not confirmed.
- Effect: A BOM or placement file can be rejected by the supplier.
- Correction: Keep the templates as starting files. Add a column and rotation test against the supplier specification.
- Status: Open question. The plan already states this test.

### O5. Native KiCad 10 upload acceptance is not confirmed

- Plan line: 25.
- Problem: The OSH Park KiCad guide says the service uses "the latest stable Kicad version (currently Kicad 9.x)".
- Effect: A native KiCad 10 upload can fail.
- Correction: Use the Gerber path for KiCad 10 until the supplier confirms native-file acceptance. The plan already states this correction.
- Status: Open question. The plan already states the mitigation.

### O6. The phase order can change after the identity trial

- Plan lines: 242 and 249.
- Problem: P1 owns the identity trial. P2, P3, P4, and P5 depend on P1. The plan says "A failed identity trial can change the estimate."
- Effect: A failed trial can remove the SKiDL path and change the schedule.
- Correction: Make the P1 exit criterion a hard gate. Record the fallback to a native KiCad schematic as a named outcome.
- Status: Open question. The plan already states the fallback on line 163.

## Language check

The plan's language follows the STE rules that I checked. I found no semicolons, no Latin abbreviations, and no phrasal verbs in the prose.

This report uses the same rules. I kept the sentences short and the words simple.

## Summary

- High-severity confirmed defects: 7.
- Medium-severity confirmed defects: 10.
- Low-severity confirmed defects: 2.
- Suggested refinements: 4.
- Open questions: 6.

The plan is careful and honest about its evidence. The most important corrections are H1 to H7. H1 is the most urgent, because it silently removes the part records from Git.
