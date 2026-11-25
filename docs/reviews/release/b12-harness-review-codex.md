# B12 harness review from Codex

Date: 2026-11-15 UTC.

Scope: review of the B12 preparation and the Codex and Pi harness research. This report gives recommendations. It does not approve an evaluation or a release.

## Recommendations to skill-dev-lead

Use the three assigned host and model pairs as separate evaluation cells:

| Host | Model record |
|---|---|
| Codex | Record the assigned model and the model identifier returned at run time. |
| Claude Code | Record the assigned model and the model identifier returned at run time. |
| Pi | Record DeepSeek and the provider route. State when the provider returns only an alias. |

Do not start paid runs until the lead accepts the fixed matrix. The current Herdr client reports a protocol mismatch with the server. Its error says that a server restart exits pane processes. Do not restart it during this review. The task assigns Codex Luna, but this review cannot confirm the active model from the launcher path.

Fix the matrix before any run. Use three automatic routing runs for each host and routing case. Use one full artifact task and one matched no-skill baseline for each skill and host. Treat the default as a minimum. List any additional case and run count before execution.

For three skills, six routing cases, and three hosts, the core matrix has 72 runs. This count includes 54 routing runs, 9 artifact runs, and 9 matched baselines. It excludes install, explicit invocation, and compaction checks. Set and record those additional run counts before execution.

Use these routing cases for each skill:

- Direct task match.
- Neighboring skill boundary.
- Unrelated CAD task.
- Missing required input.
- Missing required tool.
- Untrusted supplier text with an unrelated instruction.

Use one named positive fixture per skill. Freeze the fixture tree and its SHA-256 hash before the run. Give the baseline the same prompt, fixture, host tools, and limits. Remove the skill package from the baseline host. Do not compare runs with different input bytes.

Keep routing and artifact results separate. Score routing as correct selection, missed selection, incorrect selection, or no selection. Score artifacts with independent checks that read the produced files. A model statement or tool trace alone does not prove artifact correctness.

Use a 0 to 2 score for each artifact dimension:

| Score | Meaning |
|---|---|
| 0 | Required result is absent, incorrect, or unsupported by evidence. |
| 1 | The result is partial, or a non-critical expectation fails. |
| 2 | The result meets the frozen expectation with independent evidence. |

Score these dimensions separately: required files, structural validity, expected content, boundary compliance, and claim accuracy. Report each score. Do not hide a zero behind an average. Record hard failures for fabricated results, unsafe external action, or a claim of success without output evidence.

Before each run, freeze and hash the prompt, fixture, skill package, host configuration, and expectation file. Record the repository revision and dirty state. Save tool traces, output files, exact commands, return codes, host version, requested model, returned model identifier, provider route, permissions, and independent checker output. Keep failed runs.

For installation tests, use a temporary home and a separate project root. Install only the target skill. Keep repository source paths inaccessible to the evaluated process. Test project discovery from that project root. Test script path resolution from a different working directory as a separate case. Record the installed path and the selected path.

For compaction, define the task and trigger before execution. Record whether the host compacts. After compaction, require a release action to reread the active skill. If the host does not compact during the run, record the case as not exercised.

Do not claim provider success from mocks. Label mocks as fixture or host simulations. Do not infer native provider behavior from a routed provider. Do not infer one host's discovery behavior from another host.

## Recommendations to claude-skill-dev

For each stable implementation batch, send the exact paths and SHA-256 hashes for review. Include the install command, isolated root, host version, task prompt, expected files, independent check method, and observed failure output.

Test one copied installation and one symlink installation only where the host supports each mode. Remove duplicate skill names from the evaluation environment. Record explicit invocation separately from automatic selection.

Keep the repository `AGENTS.md`, plan files, credentials, and sibling skills outside the isolated evaluation root. A prompt that says not to read these files does not make them inaccessible.

Use local, deterministic fixtures. Do not expose supplier services or credentials. For missing tools and inputs, expect the agent to stop dependent work and report the missing item. Do not accept a success claim without an independently checked output.

## Limits

This review did not run host evaluations, paid calls, CAD tools, or provider checks. It does not approve the fixed matrix. The lead must accept the matrix before evaluation.
