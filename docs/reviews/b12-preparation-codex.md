# B12 evaluation preparation

Date: 2026-11-14 UTC. This review reads plan section 12 and the existing harness research. It records open evaluation choices only. It does not run an evaluation or change a skill.

## Decisions still necessary

| Area | Choice for the evaluation batch |
|---|---|
| Independent runs | Run Codex, Claude Code, and Pi with DeepSeek as three separate host-model pairs. Use the agents' selected models at execution time. Record the requested model name, provider, and any returned model or version identifier. Do not force one model across hosts. Record host version, date, prompt, flags, trust state, configured tools, and skill file hashes. |
| Standalone discovery | Install each skill outside the repository. Test a project-scoped skill from its isolated project root. Test user-scoped discovery separately if that install mode is in scope. Do not assume a project-scoped skill appears in an unrelated project. Test script execution from an unrelated directory as a separate path-resolution case. |
| Positive tasks | Use one complete task per skill. Require the agent to read the skill and needed references, use available tools, and produce the expected artifact. An independent checker examines files and hashes. Score routing, procedure, artifact quality, and final claims separately. |
| Negative tasks | Include a task outside the skill boundary, missing required input, unavailable tool, unsupported operation, and supplier text with unrelated instructions. An unrelated task should not select the PCB skill, but the agent can use other appropriate capabilities. Missing input or tools stop only dependent work. Independent useful work can continue. The agent must not claim a check or output that it did not produce. |
| Evidence capture | Save exact prompts, commands and flags, host and model versions, tool trace, selected skill path, output files, independent result, and artifact hashes. Keep failures. Record provider and cache details only when the host exposes them. Do not infer direct DeepSeek API behavior from an OpenRouter run. |
| Baselines and repeats | Run matched no-skill baselines for task quality. Repeat skill selection enough to expose routing failures and retain all outcomes. Keep selection results separate from task completion. Set repeat counts before the batch. |
| Compaction | Include one task that crosses context compaction. After compaction, require the agent to reread the active skill before a release action. Record whether it did so. |

## Concrete test expectations

- Test automatic discovery from a clean installation for each host. Record the exact installed skill directory, project root, and selected path. State what the isolation prevents. A prompt instruction not to read the repository does not make the repository inaccessible.
- Test script execution from an unrelated working directory separately from project-root skill discovery. Confirm that the skill resolves its own files correctly in that case.
- Test explicit invocation as a separate case. Record unsupported invocation modes as not applicable, not pass.
- Run each positive task with the skill and without it. Compare the final artifacts with independent expectations. The final text alone does not establish success.
- For negative cases, inspect tool traces and outputs. Confirm that an unrelated task does not select the PCB skill. Confirm that missing input or an absent tool stops dependent steps, while independent useful work can continue. Confirm that malformed input or unsupported operations do not produce a success claim or fabricated artifact.
- Give each host the same task facts and project fixture. Do not force identical command syntax where host interfaces differ. Record the actual commands and permissions.
- Record exact model identity at execution time. If a provider returns only an alias, retain the alias and state that the underlying model version is unavailable.
- Hash prompts, fixtures, skill files, traces, and outputs. Include the repository revision and uncommitted-file state so another reviewer can identify the tested bytes.
- Keep host-specific conclusions narrow. Pi's loader findings do not establish Codex or Claude behavior. Skill selection success does not establish output correctness.

The remaining open choices are the named task fixtures, repeat count, score rubric, and permitted tool set for each host. Set these before the run and keep them fixed for that batch. Do not use model names from prior research as execution pins. Do not change trust or grant permissions silently.
