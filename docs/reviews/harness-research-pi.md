# Agent Skills in Pi with DeepSeek: harness research

Date: 2026-11-14.

Scope: this report examines Agent Skills behavior in Pi 1.5.2 with a DeepSeek model. It uses installed Pi documentation and code, plus primary Pi and DeepSeek sources. It does not examine the Claude implementation. The repository owner will request that review after architecture agreement.

Result: Pi owns skill discovery, validation, prompt injection and tool execution. The model only selects a skill, reads files and requests tool calls. The model does not load skills by itself. Test the host and model as one pair, and report both versions.

## 1. Sources

| Source | What it shows |
|---|---|
| [Agent Skills specification](https://agentskills.io/specification) | Portable directory format, required fields, progressive disclosure, relative file references. |
| [Pi skills documentation](https://docs.pi.dev/latest/skills) | Discovery, invocation, frontmatter, validation behavior. |
| [Pi packages documentation](https://docs.pi.dev/latest/packages) | Distribution of skills through npm or git. |
| [Pi source, `skills.ts`](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/src/core/skills.ts) | Exact loader rules and prompt format. |
| [Pi source, `system-prompt.ts`](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/src/core/system-prompt.ts) | Skill index assembly and tool dependency. |
| [Pi source, `package-manager.ts`](https://github.com/earendil-works/pi/blob/main/packages/coding-agent/src/core/package-manager.ts) | Automatic discovery paths and project trust. |
| [DeepSeek API, tool calls](https://api-docs.deepseek.com/guides/tool_calls) | Function calling format and the statement that the model does not execute functions. |
| [DeepSeek API, thinking mode](https://api-docs.deepseek.com/guides/thinking_mode) | Reasoning content passback with tools. |
| [DeepSeek API, context caching](https://api-docs.deepseek.com/guides/kv_cache) | Prefix cache behavior and cache usage fields. |
| [DeepSeek API, first call](https://api-docs.deepseek.com/) | Current model names and OpenAI-compatible endpoint. |
| [DeepSeek integration with Claude Code](https://api-docs.deepseek.com/quick_start/agent_integrations/claude_code) | DeepSeek supplies the model, the other product supplies the harness. |
| [DeepSeek Harness](https://deepseek-harness.github.io/deepseek-harness/en/guide/quickstart) | A separate harness product. Do not confuse it with the model. |
| [Anthropic skills research](https://www.anthropic.com/research/equipping-agents-for-the-real-world-with-agent-skills) | Published guidance on progressive disclosure and evaluation. |

Local sources:

- `/home/kwhatcher/.pi/agent/install/releases/1.5.2/node_modules/@earendil-works/pi-coding-agent/docs/`
- The same package under `dist/core/`, especially `skills.js`, `system-prompt.js`, `agent-session.js`, `resource-loader.js` and `package-manager.js`.
- The bundled model catalog in `@earendil-works/pi-ai/dist/providers/data/`.

## 2. Discovery paths

Pi discovers skills at startup and after `/reload`.

| Scope | Path | Condition |
|---|---|---|
| User | `~/.pi/agent/skills/` | Always scanned. |
| User | `~/.agents/skills/` | Always scanned. |
| Project | `<cwd>/.pi/skills/` | Project must be trusted. |
| Project | `<cwd>/.agents/skills/` and each parent directory to the repository root | Project must be trusted. |
| Configuration | Each path in the `skills` setting | Path can be a file or a directory. |
| Package | Skill directories declared by a Pi package | Package must be installed. |

Rules from the loader:

- A directory with `SKILL.md` is a skill root. Pi does not recurse below it.
- If a directory has no `SKILL.md`, Pi reads direct `.md` children and recurses into subdirectories.
- Hidden directories, `node_modules`, and paths that match `.gitignore`, `.ignore` or `.fdignore` do not load.
- Symbolic links are followed.
- Name collisions keep the first skill found and write a warning. Project entries load before user entries.
- A missing description prevents loading. A malformed `SKILL.md` prevents loading and writes a warning.
- An invalid name writes a warning but does not stop loading.

Consequence for this repository: Pi does not scan `skills/` at the repository root. The four CAD skills did not appear in this session's skill index. Installation must copy them into a discovered path. The `npx skills add` command in `README.md` does this for supported hosts. A direct Pi user must install to `~/.pi/agent/skills/`, `~/.agents/skills/`, a project `.agents/skills/`, or a configured path.

## 3. Invocation

Pi has two invocation paths.

1. Automatic selection. The system prompt gives the model a list of skill names, descriptions, and `SKILL.md` paths. The model reads a file when it decides that the task matches. This step can fail. The Pi documentation states this limit and gives the manual command as the fallback.
2. Explicit command. `/skill:name` makes the harness read the file, remove the frontmatter, and insert the body into a user message. Arguments after the name become a user request. This path does not depend on model selection.

Related controls:

- `disable-model-invocation: true` removes the skill from the system prompt index. The explicit command still works.
- `enableSkillCommands: false` hides skill commands from interactive completion. A manually typed `/skill:name` still works.
- `--no-skills` (`-ns`) disables discovery and loading.
- `/reload` reloads skills, prompts, extensions and context files during a session.

Consequence: a test that uses only `/skill:name` measures the quality of the skill content. It does not measure routing. A test that uses only automatic selection mixes routing failures with content failures. Measure both.

## 4. Frontmatter support

Pi parses YAML frontmatter. It uses these fields:

| Field | Pi behavior |
|---|---|
| `name` | Display name and command name. Validated against the Agent Skills pattern and length. Falls back to the parent directory name. Pi does not warn when the name and directory differ. |
| `description` | Required. This is the routing text in the system prompt. Maximum 1024 characters. |
| `disable-model-invocation` | When `true`, Pi removes the skill from the index. |

Pi parses but does not use these specification fields:

| Field | Result in Pi 1.5.2 |
|---|---|
| `license` | No effect. |
| `compatibility` | No effect. Pi does not examine host or package requirements. |
| `metadata` | No effect. Pi keeps no metadata for routing. |
| `allowed-tools` | No effect. The field is not an access control. Tool access comes from the Pi session configuration. |

Unknown fields do not stop loading. Thus a skill can carry portable metadata and still load in Pi. Do not claim that Pi enforces that metadata.

Validation findings go to startup diagnostics. They do not stop startup. A team must read the diagnostics. A silent invalid field can change routing behavior.

## 5. Context use

Pi uses three levels, as the specification recommends.

1. Index. Each request carries the name, description, and absolute `SKILL.md` path for each visible skill. Pi adds about five lines of instruction around the list.
2. Skill body. The full `SKILL.md` body enters the context only after a read or an explicit command. Pi removes frontmatter on the explicit path.
3. References and assets. The model reads these files only when the instructions or the task require them. Pi gives the skill directory so the model can resolve relative paths.

The index has a real cost. This environment discovers 96 skills in the two user directories. Their frontmatter and paths total about 43,600 characters, or approximately 11,000 tokens by a characters-divided-by-four estimate. The estimate is not a tokenizer measurement. A repository that teaches many skills must examine this cost.

Two context effects need tests:

- Compaction. Pi rebuilds the system prompt for each request, so the skill index survives compaction. The loaded `SKILL.md` body is an ordinary message and can be summarized away. Pi does not automatically read the skill again. Put rules that must survive in short, repeated instructions or in project context, and test a long task that crosses compaction.
- Prompt cache. DeepSeek caches matching input prefixes. A stable system prompt and a stable skill index help cache hits. `/reload` after a skill edit changes the prefix. DeepSeek reports `prompt_cache_hit_tokens` and `prompt_cache_miss_tokens`, so a test can measure this effect.

## 6. Model versus harness

Keep these responsibilities separate.

| Function | Owner |
|---|---|
| Find directories, parse YAML, validate fields | Pi |
| Build the skill index and insert it into the system prompt | Pi |
| Select a skill for a task | Model |
| Read `SKILL.md` and reference files | Model requests, Pi executes |
| Provide `read` and `bash` tools | Pi |
| Expand `/skill:name` | Pi |
| Enforce project trust and tool permissions | Pi |
| Generate text and tool calls | Model |
| Execute a tool call | Pi, not the model |

DeepSeek states this limit directly: "The model itself does not execute specific functions." Pi maps tool schemas to the provider API, sends the request, receives tool calls, runs them, and returns the results. The model has no file system and no skill registry.

Provider details that affect the test:

- The current DeepSeek API model name `deepseek-flash` is served by DeepSeek-V4.1-Flash-1017. The legacy names `deepseek-v4-flash` and `deepseek-v4-flash-vision-exp` are also accepted but map to the same model. A test report must record the requested name, the provider, and the date.
- The Pi catalog entry for `openrouter/deepseek-v4.1-flash` lists a 1,048,576-token context window and a 943,718-token output limit. The entry also requires reasoning content on assistant messages.
- DeepSeek thinking mode with tools requires the client to send `reasoning_content` back in later requests. Pi sets this compatibility flag in the model catalog. A different harness can fail this requirement.
- DeepSeek offers a separate harness named DeepSeek Harness. It is not the model. Do not use its behavior as evidence about Pi.

Consequence: "DeepSeek loaded the skill" is an incorrect statement. The correct statement is "Pi put the skill in the index, and the DeepSeek model selected it and read the file."

## 7. Evaluation recommendations

Use a small, repeatable evaluation. Do not build a large benchmark before the basic routing test passes.

1. Record the pair. Write the Pi version, the provider, the requested model name, the model alias that the provider reports, the thinking level, and the date.
2. Measure the index. Count skills, index characters, and tokens with the provider tokenizer when possible. Set a budget, for example less than 2 percent of the context window for the full index.
3. Test routing. Use 15 to 20 realistic requests for the repository skills. Include direct matches, near misses, and requests that must not load a skill. Score correct selection, incorrect selection, and no selection.
4. Separate content from routing. Run the same tasks with `/skill:name` and with automatic selection. Compare the results. A large difference identifies a description problem.
5. Examine the tool trace. Confirm that the model read `SKILL.md`, and the necessary references, before it acted. Do not score only the final text.
6. Use a no-skill baseline. The same model without the skill shows the value of the skill. Report the difference.
7. Test negative cases. Use a missing description, an invalid name, two skills with one name, and `disable-model-invocation: true`. Make sure that the diagnostics and the command behavior are correct.
8. Test compaction. Run a task long enough to compact. Then examine if the agent still follows the skill procedure, or reads the skill again. Record the failure mode.
9. Test a second host. Keep skill files the same. Compare Pi with one other host. Do not transfer routing results between hosts.
10. Repeat each run at least three times. Model output is not deterministic. Report the distribution, not one result.
11. Score behavior that matters: task completion, missed defects, unnecessary questions, unauthorized external actions, turns, and tokens.
12. Keep the evaluation inputs in the repository. Record the commit and the exact commands. A result without these data is not reproducible.

Proportional scope for the first pass: one skill, one board task, one routing set, one forced-command set, and one compaction case. Add the other skills after the method is stable.

## 8. Limitations

- Direct access to `api-docs.deepseek.com` timed out from this host. The DeepSeek pages were read through the `r.jina.ai` text mirror. The URLs are primary, but the mirror can lag or alter formatting.
- Pi behavior comes from version 1.5.2. The loader and prompt format can change. Recheck the source after an update.
- The 11,000-token index estimate uses characters divided by four. It is not a tokenizer result.
- This research did not run a controlled skill evaluation. The recommendations are a test design, not measured results.
- The environment had 96 installed skills. That number changes the index cost and can change routing.
- The Claude implementation is not reviewed here. Its loader and invocation behavior can differ from Pi.
- The report does not test DeepSeek through the native DeepSeek API. The active session uses OpenRouter. Provider routing and caching can differ.
- No supplier, CAD, KiCad or fabrication tool was exercised. This report covers the harness only.
