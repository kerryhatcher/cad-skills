# B12 interface review from codex-release-dev

Date: 2026-11-15 UTC.

Scope: sections 3 to 6, decisions D1 to D8, and acceptance cases in section 10 of `docs/reviews/b12-interface-claude.md`. This review does not approve the interface or the paid matrix.

## Findings for sections 3 to 6

### Section 3: Harness interface

**Defect: the install rule conflicts with the routing cases.** Section 3.1 installs only the tested skill. Section 4 tests skill boundaries and skill selection. One installed skill cannot show whether the host selects the correct skill from a set of skills.

**Correction:** Add two install modes. Use a one-skill mode for isolated artifact work. Use a routing mode with all accepted skills for natural selection and boundary cases. Record all installed paths and the expected selected path for each case. Keep the baseline free of these skills.

**Defect: the run record lacks a stable case expectation field.** It records scores and a checker result, but it does not name the expectation file or its hash.

**Correction:** Add `expectation_path` and `expectation_sha256` to `run.json`. Also record the harness revision and checker version. These fields link each result to the rules used to score it.

**Defect: `selected_path` does not define multiple selections.** A host can expose more than one candidate skill path. The field name does not say whether it stores one path or a list.

**Correction:** Store the selected skill names and paths as a list. Store an empty list when the trace shows no selection. Keep discovered paths separate from selected paths.

### Section 4: Matrix

The arithmetic in section 4.3 is correct for two skills: routing has 63 runs, artifact work has 12 runs, negative cases have 12 runs, and compaction has 3 runs. The total is 90 paid runs before retries.

**Defect: negative behavioral cases have one run per host pair.** One run cannot show stable behavior for model-driven refusal or boundary behavior. The lead's default sets three routing runs per host and case.

**Correction:** Run each negative case three times per pair, or state that the lead approved a one-run exception. This change adds 24 runs and raises the total to 114. Keep deterministic checker tests separate from paid agent runs.

**Defect: the limits omit a batch cost or token cap.** Turn and time limits do not cap provider cost. Retries also increase the total.

**Correction:** Set a maximum run count and a maximum provider cost or token count before the batch. Set a retry limit. Stop before the next call when a cap is reached. Record the stop reason.

**Defect: automatic routing and explicit invocation need separate skill states.** A natural routing case needs all accepted skills visible. An explicit invocation case needs the named skill installed and the invocation supported by that host.

**Correction:** State the installed skill set for each case. Record unsupported explicit invocation as not applicable. Do not count it as a pass.

**Defect: PCBA can join without an artifact expectation.** Section 4.2 lets `pcba-design` join after package acceptance. Section 5 defines artifact checks only for A1 and A2.

**Correction:** Add a PCBA fixture, task prompt, expected files, and independent checks before PCBA joins the paid matrix. Add its matched baseline and revise the run count.

### Section 5: Fixtures and expectations

**Defect: the named fixture table does not define all artifact inputs.** `rc-bare-board` serves A1 and A2, but the table does not list expected values, output paths, or the exact source revision. The supplier page supports only N4.

**Correction:** Add a frozen fixture manifest. Give each artifact task an input hash, source revision, exact prompt hash, expected output list, and checker rule. Keep task-specific fixtures separate when one source project cannot support both expected results.

**Defect: A1's expected change is not named.** “The changed value” does not identify the property, original value, expected value, or footprint reference.

**Correction:** Name the property and values in a machine-readable expectation file. Make the checker read that file. Do not infer the expected result from agent output.

**Defect: the local container check does not define its image evidence.** The section says to record the digest, but it does not state how the checker receives the image or how the test runs without a local image.

**Correction:** Record the local image digest and exact command. If the image is absent, mark the affected test not run. Do not pull an image. Do not report a pass.

### Section 6: Scoring rubric

**Defect: S5 has no pass rule for unnecessary questions.** The table says to count them, but the gate does not set a limit or define which questions count.

**Correction:** Define a count rule and report the count as a measure. Keep it separate from the boundary pass rule. A question that requests a required missing input is not unnecessary.

**Defect: S4 does not define claim evidence for claims outside the artifact checker.** The current rule covers a DRC claim absent from the log, but does not define the evidence source for tool availability, file changes, or external actions.

**Correction:** Map each claim type to a source, such as the process log, trace, output hash, or checker result. Fail each unsupported claim.

**Defect: the artifact gate has one run per skill and host.** One pass does not establish repeatability. The report must not present it as a stable success rate.

**Correction:** Keep one artifact run and one matched baseline per skill and host as the minimum. Label the result as one observed run. Do not claim a measured improvement over baseline from one pair.

## Decisions D1 to D8

| ID | Decision |
|---|---|
| D1 | Agree with `evaluation/`. The name clearly separates the harness from test code. |
| D2 | Disagree with one run for each negative case. Use three runs per host and case, or record a lead-approved exception. |
| D3 | Agree with C1 as an additional case. State its host command and compaction evidence. Record not exercised if the host does not compact. |
| D4 | Agree with three explicit invocation runs per pair. Mark unsupported invocation as not applicable, not pass. |
| D5 | Agree with the natural and explicit routing thresholds as written. Add S5 and claim-evidence rules before approval. Keep artifact results as single-run observations. |
| D6 | Agree with the proposed turn and time limits. Add a batch cost or token cap, a total run cap, and a retry cap. |
| D7 | Agree. Add PCBA only after package acceptance and after its fixture and independent artifact checks are ready. |
| D8 | Agree with execution-time recording. If the returned model or provider changes within a batch, split the results by that identity. |

## Missing or untestable cases in section 10

| Case | Gap | Required update |
|---|---|---|
| AC-02 | The case checks hashes and writes outside the root, but it does not test the baseline install or cleanup after a failed install. | Test both arms. Test failure cleanup. Check that no user skill path changes. |
| AC-03 | It does not say how the harness finds two same-name skills in routing mode. | Add a duplicate in the installed skill set. Assert both paths appear and no provider call starts. |
| AC-10 | It asks for discovery from a root and nested directory for each pair, but section 3 gives no host-specific discovery command or observation method. | Name the command and evidence for each host. Mark unsupported discovery observation as not applicable. Keep this test separate from task routing. |
| AC-12 | It does not test a routing installation with all accepted skills. | Add a case that confirms each skill is discoverable before routing starts. Then test the expected selection from that set. |
| AC-13 | It has no PCBA expectation if PCBA joins the gate. | Add a PCBA task, fixture, matched baseline, and independent checker before inclusion. |
| AC-14 | It does not define which output files count as fabricated artifacts, or how the checker detects them. | Freeze the allowed output list and check the run directory after each negative case. |
| AC-15 | “Compaction forced by the host command” has no host command or confirmation signal. Some hosts may not support a forced compaction command. | Define the command and evidence for each host. Mark unsupported or unobserved compaction as not exercised. Do not count it as pass. |
| AC-18 | It checks read-only CI permission and no provider use, but not that the new job runs the intended script or blocks on failure. | Add a workflow check for the exact command and a failing-fixture path that returns nonzero. |
| AC-19 | It does not name the lint commands, input files, or how false findings get review. | List the commands and files. Retain the findings and reviewer disposition. |
| AC-20 | It does not define a pass result for missing, unavailable, or conflicting license evidence. | Require a source URL, license text or identifier, retrieval date, and a stop state for unresolved evidence. |

## Limits

This review did not run tests, host evaluations, provider calls, or paid runs. It did not inspect third-party license sources. The lead must accept the revised interface and matrix before implementation or evaluation.
