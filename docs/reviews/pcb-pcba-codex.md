# PCB and PCBA plan review

## Review record

- Reviewer harness: Codex through Herdr.
- Model: GPT-6-Luna high, as shown in the terminal.
- Review scope: `AGENTS.md`, `docs/pcb-pcba-plan.md`, repository structure, `README.md`, and `tests/test_snippets.py`.
- Source review: I examined the primary KiCad, SKiDL, and OSH Park pages listed below.
- Change status: This report records a review only. It does not change the plan or implementation.

This review separates confirmed defects from suggested refinements and open questions. A confirmed defect identifies a gap or contradiction in the plan. A refinement can improve the plan, but it does not block the stated design by itself. Open questions require a trial or evidence before a decision.

## Findings in severity order

### Medium: The isolation test does not test all skill dependencies

**Type:** Confirmed defect in the proposed test definition.

**Plan lines:** 40–46, 53–56, 76–80, 286.

**Problem:** The plan says that each skill must operate alone and must not use a file from another skill. The test at line 286 only says to install one skill in an empty directory. It does not state that the test must install only that skill and its declared dependencies, nor that it must run the skill scripts and one complete task.

**Effect:** A skill can pass a basic installation test while a script, template, or reference still depends on a file or undeclared tool from another skill. The release criteria can then report independence without testing the full condition.

**Proposed correction:** Define one isolated test for each skill. Install only that skill and its declared dependencies. Run its environment report and one complete task. Check that all files and tools come from that skill or its declared dependencies.

### Medium: The native KiCad circuit-source path has no trial gate

**Type:** Confirmed phase gap.

**Plan lines:** 148–163, 241–243.

**Problem:** P1 centers on the SKiDL-to-KiCad identity trial. Line 163 says the project can retain a native KiCad schematic if generated schematics fail. The plan does not assign a trial or acceptance criterion to that native path.

**Effect:** If the SKiDL trial fails, P2 can lack a tested circuit-source workflow. This can delay the PCB skill or leave its supported source format unclear.

**Proposed correction:** Add a native KiCad circuit-source trial and its acceptance criteria to P1. Make P2 depend on a tested source choice: SKiDL or native KiCad.

### Low: Assembly variant mapping needs a defined contract

**Type:** Suggested refinement.

**Plan lines:** 110, 114, 203–205, 276–284.

**Problem:** The plan lists board variants, assembly variants, DNP status, BOM data, and placement data. It does not define the keys or rules that connect a board variant to the matching BOM and placement records.

**Effect:** Different files can describe different populations of parts while each file passes its own schema checks. This can cause assembly or test errors.

**Proposed correction:** Define the variant identifiers and part-state rules in the project contract. Add tests that compare each board variant with its BOM, placement data, DNP records, and assembly files.

### Low: The supplier qualification gate should state how evidence is accepted

**Type:** Suggested refinement. The plan already identifies supplier evidence as an open gate.

**Plan lines:** 27–28, 116, 197–201, 311.

**Problem:** The plan requires evidence for the condition that one supplier performs fabrication and assembly in-house. It does not state what form of evidence qualifies or who records its approval.

**Effect:** A profile can become qualified based on a general company statement that does not apply to the selected service or order.

**Proposed correction:** Require a dated source that names the selected service and confirms both fabrication and assembly locations. Record the source, retrieval date, and reviewer in the supplier profile. Keep the profile unqualified until the evidence meets that rule.

### Low: The KiBot and KiCad compatibility test should cover actual outputs

**Type:** Suggested refinement. The plan already calls for a released KiBot version, a pinned container, and integration tests.

**Plan lines:** 21–22, 242–245, 274, 284.

**Problem:** The plan does not list a required comparison between KiBot outputs and outputs from `kicad-cli` for the same board and configuration.

**Effect:** A working KiBot job can produce files with incorrect layer selection, drill settings, or supplier-specific table fields. A successful process exit alone would not show this error.

**Proposed correction:** For the trial board, compare the generated layer set, drill files, BOM fields, and placement fields with expected files or values. Record the exact KiBot and KiCad versions and test each supplier adapter against its current specification.

### Low: Profile updates can leave a previously qualified package stale

**Type:** Suggested refinement. The plan already requires live-page comparison before release.

**Plan lines:** 116, 185–193, 287, 302.

**Problem:** The plan says to stop qualification if a material limit changes or lacks evidence. It does not say whether a changed profile invalidates prior package results or which profile revision each result used.

**Effect:** A report or export can appear qualified under a newer supplier profile even though the test used older limits.

**Proposed correction:** Give each supplier profile a revision or content hash. Store that value in each test report and package manifest. Require requalification when the profile hash changes.

## Open questions and evidence gates

### Sierra Circuits in-house condition

**Plan lines:** 27, 199–201.

The cited Sierra page identifies Turnkey PRO as a fabrication and assembly service. This review did not confirm that the selected order condition uses in-house facilities for both steps. Keep this as an open supplier evidence gate. Obtain service-specific confirmation before qualification.

Source: [Sierra Circuits Turnkey PRO](https://www.protoexpress.com/products/turnkey-pro/)

### KiBot release and container digest

**Plan lines:** 21, 242, 244.

The plan correctly leaves the exact KiBot release and container digest for a trial. Select them only after a board package passes the output checks in the trial environment. The current KiBot documentation includes unreleased work, so the plan should retain its rule against selecting `latest`.

Source: [KiBot documentation](https://kibot.readthedocs.io/en/latest/)

### OSH Park service limits and file set

**Plan lines:** 171–193.

The single-layer service page states that the supplier uses its two-layer process. It also states that the automated upload service expects Gerber data for a two-layer design. This supports the plan's two-layer file-set requirement. Confirm the current limits and file set for each service during profile qualification.

Source: [OSH Park 1 Layer Prototype Service](https://docs.oshpark.com/services/single-layer/)

### SKiDL identity and generated schematic behavior

**Plan lines:** 17–18, 148–165, 242.

The SKiDL manual documents KiCad schematic generation and tags. This does not establish that this repository's planned editing and regeneration sequence preserves the required board identity. The plan correctly treats that behavior as an open trial.

Source: [SKiDL manual](https://devbisme.github.io/skidl/)

### KiCad command compatibility

**Plan lines:** 19, 167, 242.

KiCad 10 documentation includes PCB DRC schematic parity and the violation exit-code option. The plan correctly requires command compatibility tests before it relies on these options. The selected KiCad patch version and fixed container still require a trial.

Source: [KiCad 10 command-line reference](https://docs.kicad.org/10.0/en/cli/cli.html)

## Repository evidence

The repository has separate skill directories under `skills/`. The current snippet runner searches Markdown files in those directories and executes eligible Python blocks. Its PEP 723 header declares CadQuery. This supports the plan's statement that PCB-specific dependencies need explicit test setup. The proposed isolation test should also cover scripts and templates, not only Markdown examples.

Sources inspected: `README.md`, `tests/test_snippets.py`, and the file list under `skills/`.

## Review summary

The plan identifies important technical risks and correctly labels several claims as untested. The main release risks in this review are the incomplete independence test and the lack of a native KiCad fallback trial. Define the variant contract and evidence rules before implementation. Keep the KiBot, supplier, and SKiDL decisions behind the listed tests.
