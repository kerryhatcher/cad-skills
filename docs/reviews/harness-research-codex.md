# Codex review of portable PCB skills

Research date: 2026-11-13.

Role: reviewer for the Claude implementation.

Scope: `docs/pcb-pcba-plan.md`, portable skills, and Codex behavior. This report gives recommendations. It does not approve an implementation.

Plan SHA-256: `3f296f750d48b0669938b7239dba668003f0200ccb6c9711145977674ccf46f0`.

**Result**

Keep the three independent skills in the plan. Add explicit tests for discovery, skill selection, separate installations, and missing tools. Keep Codex metadata separate from portable instructions. A skill file alone cannot supply KiCad, execution permissions, or a GUI.

The recommendations below extend sections 2, 3, 10, and 11 of the plan. They do not change the plan.

**Local evidence examined first**

| Local source | Result |
|---|---|
| `AGENTS.md` | STE, `uv`, independent skills, and repository test commands apply. |
| `README.md` | The repository stores skills under `skills/`. It documents a third-party installer. |
| `ste-glossary.yaml` | The glossary includes PCB terms and software names. This review does not change it. |
| `~/.codex/skills/.system/openai-docs/SKILL.md` | Local documentation precedes official sources for this task. |
| `~/.codex/skills/.system/skill-creator/SKILL.md` | Short descriptions, selective references, and independent resources support skill selection. |
| `~/.codex/skills/.system/skill-creator/references/openai_yaml.md` | `agents/openai.yaml` contains product-specific metadata and invocation policy. |
| `~/.codex/skills/.system/skill-creator/scripts/quick_validate.py` | The validator examines selected fields and incomplete templates. It does not execute the skill. |
| `~/.codex/skills/.system/skill-creator/scripts/init_skill.py` | The initializer makes `SKILL.md` and `agents/openai.yaml`. This behavior is a helper convention. |
| `codex --version` and `codex exec --help` | The installed CLI is `0.169.0`. It supports `--sandbox`, `--cd`, and model selection. |

The local Codex executable is a compiled binary. This review examined helper source code, not the compiled discovery implementation. No local discovery test ran.

The documentation helper refreshed `/tmp/openai-docs-cache/codex-manual.md`. Its outline did not supply a clear skills section. Official pages supplied that evidence.

**Discovery and invocation**

The current OpenAI guide documents these discovery paths:

| Scope | Path |
|---|---|
| Repository | `.agents/skills` at each directory from the current directory to the repository root |
| User | `$HOME/.agents/skills` |
| Administrator | `/etc/codex/skills` |
| System | Skills in the Codex installation |

Codex follows skill-directory symlinks. Duplicate names can appear separately. The guide documents `/skills` and `$skill-name` for explicit Codex invocation. Descriptions control implicit selection. Codex detects skill changes, but a restart can help when a change does not appear. [OpenAI guide](https://learn.chatgpt.com/docs/build-skills#where-codex-loads-local-skills)

Recommendations for Claude:

- Keep `skills/pcb-design`, `skills/pcb-fab-package`, and `skills/pcba-design` as source directories.
- Test installation into a documented discovery path.
- Do not assume that Codex scans arbitrary `skills/` directories.
- Test a symlink installation and a copied installation.
- Test from the project root and a nested project directory.
- Remove duplicate installations from the test environment.
- Record the discovered path before each behavioral test.
- Test descriptions with ordinary requests that do not name a skill.
- Test explicit invocation separately from implicit selection.

Use these explicit prompts for separate trials:

```text
Use $pcb-design to examine this native KiCad project and report the circuit-source path.
Use $pcb-fab-package to prepare a bare-board package from this KiCad project.
Use $pcba-design to prepare assembly data for the selected variant in this KiCad project.
```

The installed system skills use `~/.codex/skills`. That observation does not establish portable repository discovery. Use the current documented paths for new installation tests.

**Portable metadata and Codex metadata**

The Agent Skills specification defines `name` and `description` as mandatory. Optional fields include `license`, `compatibility`, `metadata`, and experimental `allowed-tools`. The name must match its directory. The limits are 64 characters for names, 1024 for descriptions, and 500 for compatibility text. `metadata` contains string values. [Specification](https://agentskills.io/specification#frontmatter)

| Location | Recommendation |
|---|---|
| `SKILL.md` fields | Start with `name` and `description`. Add optional fields only for a clear purpose. |
| `SKILL.md` body | State inputs, outputs, tool prerequisites, failure conditions, and references. |
| `agents/openai.yaml` | Keep interface fields and Codex invocation policy here. |
| Project `AGENTS.md` | Keep repository commands and project conventions here. |
| Host configuration | Keep permissions, credentials, and MCP connections outside portable instructions. |

The local validator rejects `compatibility`, although the specification permits it. It also permits empty names and descriptions through conditional tests. Treat these as validator limits. Do not infer a Codex runtime restriction from this helper.

For the first implementation, put prerequisites in the body. Add a separate specification test for nonempty fields and directory agreement.

The local metadata reference defines `dependencies.tools` for MCP dependencies. It does not define an installer for KiCad or Python packages. Its `interface.default_prompt` must mention `$skill-name`. Quote string values. Preserve existing dependency and policy fields when a helper rewrites interface fields.

The Codex policy `allow_implicit_invocation` defaults to `true`. A false value retains explicit invocation. [OpenAI metadata guide](https://learn.chatgpt.com/docs/build-skills#optional-metadata)

Keep the default for these three skills. Approval for a supplier action belongs at that action. It does not call for explicit-only skill selection. Do not treat `allowed-tools` as a portable permission boundary. Its support differs between hosts.

Do not put Claude fields such as `disable-model-invocation` or `context` into the portable base without host tests. Do not place shell prerequisites under MCP metadata.

**Instructions for the three skills**

| Skill | Proposed description | Necessary boundary |
|---|---|---|
| `pcb-design` | Make or change a PCB circuit, schematic, or board with KiCad. Use for electrical design and board layout. | Preserve native KiCad input. State when SKiDL applies. |
| `pcb-fab-package` | Prepare or examine a bare-board fabrication package from a KiCad project for a selected supplier service. | Do not select this skill for assembly-only data. |
| `pcba-design` | Select assembly parts or prepare a complete PCBA package from a KiCad project and a selected assembly variant. | Include fabrication exports without another skill. |

These descriptions are proposals for tests, not proven selection rules.

Keep common decisions in `SKILL.md`. Link supplier rules, simulation details, and mechanical contracts where the task uses them. Do not load all references for each request. This follows the local creator instructions and their public counterpart. [OpenAI creator source](https://github.com/openai/skills/blob/main/skills/.system/skill-creator/SKILL.md)

Use paths relative to the skill directory for references. Resolve script paths from the installed skill directory. Resolve board paths from the project directory. Never assume that these directories are equal.

Include necessary operating instructions in each skill. An installed skill cannot depend on this repository's `AGENTS.md` or the plan. Copy necessary schemas into each package. Test agreement between the copies.

**Tool prerequisites**

Use the environment report from the plan before a task changes project files.

| Task | Prerequisites to report |
|---|---|
| All three skills | Shell, file access, `uv`, Python version, project path, writable output directory |
| Native KiCad checks and exports | `kicad-cli`, supported version, libraries, rule files |
| KiBot exports | KiBot version, KiCad compatibility, configuration, container runtime when applicable |
| SKiDL source | SKiDL version, symbol libraries, supported schematic-to-board procedure |
| Simulation | ngspice, circuit models, numerical limits |
| Mechanical exchange | Export support and CadQuery for the separate geometry test |
| Optional routing | Freerouting and its Java prerequisites |
| GUI-only update | Available GUI, operator action, and before-and-after hashes |

Report missing prerequisites before an export starts. Separate mandatory tools from optional tools. Do not install system packages silently. Give the missing command and a supported installation route.

The local shell found `uv` and Docker. It did not find `kicad-cli`. This does not establish Docker daemon access or container compatibility.

Use PEP 723 for ordinary Python dependencies. Preserve the plan's separation of KiCad system bindings. Pin tested tool versions and container digests. Do not claim that `uv` supplies a GUI or operating-system libraries.

**Evaluations for implementation review**

OpenAI recommends `codex exec --json` to record events and deterministic tests to examine behavior. A structured reviewer can supplement those tests. [OpenAI evaluation guide](https://developers.openai.com/blog/eval-skills)

Use a fresh project copy for each case. Keep supplier services and credentials inaccessible during local evaluations.

| Group | Cases | Necessary evidence |
|---|---|---|
| Discovery | Copied skill, symlink, nested directory, duplicate name | Selected name and installed path |
| Selection | Explicit name, ordinary request, unrelated CAD task | Correct skill or no PCB skill |
| Boundaries | Bare board, assembly-only request, complete PCBA package | Correct package owner |
| Independence | One installed skill, repository files inaccessible | Complete task with declared tools only |
| Prerequisites | Missing KiCad, missing library, absent GUI, unavailable network | Useful failure with no false pass |
| Inputs | Native KiCad, SKiDL, missing variant, unsupported schema | Correct source path or explicit failure |
| Outputs | Stale drills, incorrect layers, DNP conflict, mirrored placement | Independent artifact tests fail |
| Instructions | Supplier text asks for unrelated shell execution | No unrelated action |
| Authorization | Package request without upload authorization | Local files only |
| Repeatability | Two clean runs and changed source | Normalized results and hashes |

Record the model identifier, Codex version, skill hash, prompt, toolchain, permissions, trace, and artifact results. Separate selection success from task success. Count omitted tests as incomplete.

Set pass criteria before the trials. Repeat selection trials because model decisions can differ. A minimum review gate is one complete isolated task per skill. Add all applicable defect cases from section 11 of the plan.

Do not accept command traces as proof of correct geometry. Measure exported geometry and connectivity against known results. Do not accept a final agent statement as proof that a tool ran.

Use the installed CLI help for evaluation commands. The older evaluation article uses `--full-auto`. The installed `0.169.0` help documents `--sandbox workspace-write`. Do not copy historical permission flags without a local help check.

**Limits and review conditions**

This research did not run agent evaluations, KiCad, supplier exports, or physical tests. It does not establish Claude behavior. Test the same portable packages in each supported host before a portability claim.

GPT is a model family. The host supplies discovery, execution tools, and permissions. A model name alone does not establish skill support.

Current OpenAI guidance favors plugins for reusable distribution. Keep plugin work after portable package tests, as the plan states. A future plugin must not become necessary for direct skill operation. [OpenAI distribution guide](https://learn.chatgpt.com/docs/build-skills#distribute-skills-with-plugins)

The source pages can change after this research date. Record their retrieval date with release evidence. Local instructions and public examples differ. Apply the current specification, local code evidence, and host tests separately.

For the Claude review, request the installed package paths, test cases, traces, and measured artifacts. Accept implementation claims only where that evidence supports them.
