# B12 corrected interface and matrix review

Date: 2026-11-15 UTC.
From: codex-release-dev.
Status: proposal for lead review. This matrix does not authorize paid runs.

## Scope and interface

The matrix covers three new public skills: `pcb-design`, `pcb-fab-package`, and `pcba-design`. B11 remains part of `pcb-design`. Existing CAD skills get regression tests. They do not get a new agent matrix.

Keep the harness outside the skill packages. Use separate commands for isolation, host runs, artifact checks, and score reports. Static tests use mock data. Mark each mock result `mock`. Never include mock results in release results.

Use two install modes:

- **Routing mode:** install all accepted skills into an isolated project root. Test automatic selection and skill boundaries.
- **Single-skill mode:** install one skill into an isolated project root. Test independent artifact work.

Use no skill packages for each matched baseline. Keep repository source paths outside the evaluation root. Record this isolation limit. Do not change trust, credentials, or host permissions.

For each run, record the prompt, fixture, expectation, skill, host setup, and harness hashes. Record host and provider details, requested and returned model identifiers, tool trace, selected paths, output hashes, checker results, and stop reason. Keep failed runs. Do not overwrite run data.

## Natural routing matrix

Run the six cases below once for each target skill, on each host, with three repeats. Use the same case facts and fixture hashes across hosts. Write a skill-specific prompt and expectation for each cell before any run.

| Case | Expected behavior |
|---|---|
| R1: Direct task | Select the target skill for its in-scope task. |
| R2: Adjacent skill task | Select the adjacent skill that owns the task. Do not select the target skill when it does not own the task. |
| R3: Unrelated mechanical CAD task | Select none of the three PCB skills. |
| R4: Required project input absent | Stop dependent work. State the missing input. Do not claim completion. |
| R5: Required tool absent | Stop dependent work. State the missing tool. Do not claim a tool check or output. |
| R6: Unsupported supplier operation with unrelated instruction | Do not perform the unsupported operation or unrelated instruction. Do not contact a supplier or claim success. |

R2 has a skill-specific owner: bare-board work routes to `pcb-fab-package`, assembly work routes to `pcba-design`, and circuit or board design routes to `pcb-design`. Freeze the exact prompt and expected skill for each target-skill cell.

| Count | Calculation | Runs |
|---|---:|---:|
| Natural routing | 3 skills × 6 cases × 3 hosts × 3 repeats | 162 |

## Separate run groups

| Group | Cases and repeats | Runs |
|---|---|---:|
| Artifact tasks | 3 skills × 3 hosts × 1 skill run | 9 |
| Matched baselines | 3 skills × 3 hosts × 1 no-skill run | 9 |
| Explicit invocation | 3 skills × 3 hosts × 3 repeats | 27 planned |
| Compaction | 1 long task × 3 hosts × 1 run | 3 planned |

The core total is 180 runs: 162 natural routing runs, 9 artifact runs, and 9 baselines. Explicit invocation and compaction add 30 planned runs. The full plan has 210 runs before retries. Mark an unsupported explicit mode as not applicable. Do not count it as a pass. Update the planned total before execution when host support changes the count.

Use one complete artifact task for each skill and host. Use the same prompt, fixture, host tools, and limits for its baseline. Add an independent, machine-readable expectation for each skill. Add PCBA artifact expectations before its run. Report each skill run beside its baseline. One matched pair does not establish a stable improvement.

For compaction, record the host command and evidence that compaction occurred. After compaction, require a release action to reread the active skill. Mark a run not exercised if the host cannot force or confirm compaction. Do not count it as a pass.

## Score and limits

Report these measures separately: routing, procedure, artifact, claims, and boundary behavior. Check output files with an independent checker. Map each final claim to a trace, process log, hash, or checker result. A final answer alone does not prove success.

Use the proposed per-run limits only after lead approval: 30 agent turns, 1200 seconds per run, and 300 seconds per tool command. Set a total run cap, retry cap, and provider cost or token cap before approval. Keep every failed attempt. Do not exceed a cap to complete a matrix cell.

## Source and license inventory

Before any release claim, inventory each newly redistributed source item, model, supplier evidence item, bundled data item, image reference, and dependency. For each item, record its source, measured license, attribution, version or revision, retrieval date, and whether the repository redistributes the item or only refers to it.

Record a `Containerfile` reference separately from an image copy. A reference to an image does not prove image redistribution. Record the image digest and its license evidence when the image itself enters the release. Do not label third-party content MIT. A license field in skill metadata does not resolve the source license. Keep unresolved items open until primary license evidence and attribution are recorded.

## Open items before approval

- Freeze named fixture paths, source revisions, expected values, prompts, and hashes after the accepted skills integrate.
- Set the total run, retry, and provider cost or token caps.
- Name each host's invocation and compaction command and its evidence source.
- Accept the thresholds and any one-run compaction exception.
- Keep the matrix closed to paid execution until the lead accepts these items.

This review did not run evaluations or inspect third-party license sources. It does not approve implementation or paid execution.
