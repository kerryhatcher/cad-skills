# B12 release validation and harness review from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: B12 preparation, the harness research reports, release validation, isolated
installation, the evaluation harness, CI, documentation, and the licensing review.
This report gives recommendations. It does not approve an evaluation or a release.
It reads stable files only. It does not change a product file.

## Environment

| Item | Value |
|---|---|
| Working directory | `/mnt/storage/projects/cad-skills-worktrees/release` |
| Branch | `work/release` |
| HEAD | `75d99da` |
| Host | Pi 1.5.2 |
| Requested model | `deepseek/deepseek-v4.1-flash` through OpenRouter |
| Working tree | Clean. Only `docs/reviews/release/` is untracked. |

The provider returns a model alias. Record the returned identifier at run time.
Do not claim the native DeepSeek route from this OpenRouter run.

## Checks that ran now

| Check | Command | Result |
|---|---|---|
| Package checks | `uv run tests/test_skill_packages.py` | 8/8 passed, exit 0 |
| Record contracts | `uv run tests/test_pcb_tools.py` | 59/59 passed, exit 0 |
| Project lock and publication | `uv run tests/test_project_io.py` | 11/11 passed, exit 0 |

These checks show the stable B1 to B6 records. They do not exercise a host, a skill
task, or a paid model call.

## Measured findings

### 1. Host discovery gap

Pi 1.5.2 does not load the repository `skills/` directory. The active Pi session index
does not include `cadquery`, `print-prep`, `prusaslicer`, `structural-analysis`,
`pcb-design`, or `pcb-fab-package`.

Codex reads `.agents/skills` at each directory from the current directory to the
repository root. Codex also reads `$HOME/.agents/skills`. The `npx skills add` command
in `README.md` installs into these paths.

Thus each isolated install test must copy the skill into a discovered path:

| Host | Scope | Install path |
|---|---|---|
| Pi | User | `$HOME/.pi/agent/skills/<name>` or `$HOME/.agents/skills/<name>` |
| Pi | Project, trusted | `<project>/.pi/skills/<name>` or `<project>/.agents/skills/<name>` |
| Codex | Repository | `<repo>/.agents/skills/<name>` |
| Codex | User | `$HOME/.agents/skills/<name>` |

Record the installed path, the project root, and the selected path. A prompt
instruction not to read the repository does not make the repository inaccessible.
Test script path resolution from an unrelated working directory as a separate case.

### 2. Licensing gap

The four accepted CAD skills have a `license` field and a `metadata` block.
`pcb-design` and `pcb-fab-package` have neither field.

| Skill | `license` | `metadata` |
|---|---|---|
| `cadquery` | MIT | author, version, cadquery-version |
| `print-prep` | MIT | author, version |
| `prusaslicer` | MIT | author, version, prusaslicer-version |
| `structural-analysis` | MIT | author, version |
| `pcb-design` | absent | absent |
| `pcb-fab-package` | absent | absent |

The plan requires a license review before distribution. The repository has one
`LICENSE` file and no third-party notice file. These items redistribute third-party
work:

- `skills/pcb-design/runtime/Containerfile` and
  `skills/pcb-fab-package/runtime/Containerfile` use
  `ghcr.io/astral-sh/uv` and `ghcr.io/inti-cmnb/kicad10_auto_full`.
- `skills/pcb-fab-package/supplier/pages/` stores supplier HTML pages and HTTP headers.
- The `prusaslicer` skill uses the Prusa profile bundle.

Record the source, license, and retrieval date for each redistributed item. Keep the
external tools separate from the repository MIT license.

### 3. Codex metadata

No `agents/openai.yaml` exists in a skill. The Codex research recommends this file for
interface fields and the invocation policy. Keep the portable `SKILL.md` as the primary
source. Add the file only when the Codex discovery test needs it. Do not treat
`allowed-tools` as a permission boundary.

### 4. CI coverage gap

`.github/workflows/test.yml` runs `test_pcb_tools.py`, `test_project_io.py`,
`test_skill_packages.py`, `test_snippets.py`, the template builds, `cq_api.py`, and
`test_print_tools.py`.

It does not run these tests:

- `tests/test_pcb_design.py`
- `tests/test_pcb_fab_package.py`
- `tests/test_pcb_fab_workflow.py`
- `tests/test_trial_checker.py`, `tests/test_trial_exports.py`,
  `tests/test_trial_identity.py`
- a license check
- an isolated-install check

Add the missing test jobs after the other teams accept B7 to B11. Add one `licenses`
job and one `isolation` job.

### 5. Harness state

`tests/test_skill_packages.py` states that its copy-run test is not a sandbox and that
the final gate (B12) runs real isolated tool tasks. No release-isolation test exists.
Recommend a new test file. This is shared test configuration. The lead owns the
decision before implementation.

## Fixed matrix for lead acceptance

Use three separate host and model cells. Record the requested name, the provider route,
the returned identifier, the host version, and the date. Do not force one model across
hosts.

| Host | Record |
|---|---|
| Codex 0.169.0 | Luna medium |
| Claude Code 2.1.325 | Haiku 5.5 |
| Pi 1.5.2 | DeepSeek V4.1 Flash through OpenRouter |

Skills in scope after integrated acceptance: `pcb-design`, `pcb-fab-package`,
`pcba-design` (B9/B10), and the mechanical export skill (B11). Add the four accepted
CAD skills if the lead wants one full release gate.

Routing cases for each skill. Run each case three times for each host:

1. Direct match.
2. Neighboring skill boundary.
3. Unrelated CAD task.
4. Missing required input.
5. Missing tool.
6. Supplier text with an unrelated instruction.

Core count for 3 skills, 6 cases, and 3 hosts: 54 routing runs. Add 9 complete artifact
runs and 9 matched baselines: 72 runs. This agrees with the Codex report.

| Extra case | Count | Note |
|---|---|---|
| Explicit invocation | 9 | One for each skill and host. Record an unsupported mode as not applicable. |
| Install | at least 6 | Copy and symlink for each skill where the host supports both. |
| Compaction | 2 | One skill on two hosts. State the trigger before the run. |

State every count and limit before the batch.

## Limits and stop conditions

- Run each routing case three times. Report the distribution, not one result.
- Run one complete artifact task and one matched baseline for each skill and host.
- Stop the batch on a provider error. Keep the failure record.
- Do not run a paid batch before the lead accepts the matrix.
- Do not claim provider success from a mock. Label a mock as a fixture.
- Do not infer native DeepSeek behavior from the OpenRouter route.
- Do not infer one host from another host.
- Set a run ceiling and a token ceiling in the matrix before the batch.
- Do not change trust or grant new permissions.

## Fixtures and expectations

- Make one frozen fixture tree for each skill. Start from `tests/fixtures/pcb-design`
  and `tests/fixtures/pcb-fab-package`. Copy the tree to a fresh temporary directory
  for each run.
- Hash the prompt, the fixture, the skill package, the host configuration, and the
  expectation file before each run.
- The expectation file names the required files, the structural checks, the expected
  content, the boundary rules, and the claim rules.
- The independent checker reads the produced files and hashes. A final model statement
  does not prove an artifact.
- The baseline uses the same prompt, fixture, host tools, and limits. Remove the skill
  package from the baseline host.
- For missing input and missing tools, the expected result is a useful failure.
  Dependent work stops. Independent work can continue. The agent must not claim an
  absent check or artifact.
- Do not claim correct geometry from an exit code. Measure the exported geometry and
  connectivity against the frozen expectation.

## Score rubric

Keep routing, procedure, artifact quality, and final claims separate.

Routing score: correct selection, missed selection, incorrect selection, or no
selection.

Artifact score from 0 to 2 for each dimension:

| Score | Meaning |
|---|---|
| 0 | The result is absent, incorrect, or unsupported by evidence. |
| 1 | The result is partial, or a non-critical expectation fails. |
| 2 | The result meets the frozen expectation with independent evidence. |

Dimensions: required files, structural validity, expected content, boundary
compliance, and claim accuracy.

Record a hard failure for a fabricated result, an unsafe external action, or a success
claim without output evidence. Report each score. Do not hide a zero behind an average.

## Evidence to retain

Prompts, commands, flags, host versions, requested and returned model identifiers,
provider route, tool trace, selected skill path, output files, return codes, artifact
hashes, independent checker output, the repository revision, and the dirty state.
Keep every failed run.

## Recommendations to claude-skill-dev

- C1: Add `license: MIT` and a `metadata` block with author and version to
  `skills/pcb-design/SKILL.md` and `skills/pcb-fab-package/SKILL.md`. Keep the body
  unchanged. Send the paths and the hashes to both reviewers.
- C2: Do not put Codex or Claude fields in the portable `SKILL.md`. Add
  `agents/openai.yaml` only when the Codex discovery test needs it. Do not use
  `allowed-tools` as a permission boundary.
- C3: For each stable batch, give the release team the frozen install command, the
  isolated project root, the task prompt, the expected files, the independent check,
  and the observed failure output.
- C4: Make one positive fixture for each skill with a stable hash and an expectation
  file. Measure the exported geometry and connectivity. Do not claim geometry from an
  exit code.
- C5: Wait for the lead to accept the matrix. Use the integrated accepted skills for
  the final evaluation only.

## Recommendations to skill-dev-lead

- R1: Accept or change the fixed matrix. Set the extra run counts, the run ceiling, and
  the token ceiling before any paid run.
- R2: Assign the shared edits. I own the repository README, AGENTS, CI, and shared test
  configuration. I will not change them before your acceptance. Proposed edits:
  - `README.md`: add the PCB and PCBA skills to the table. Add the release check
    commands. Add the license statement.
  - `AGENTS.md`: add the release check commands and the isolation limit.
  - `.github/workflows/test.yml`: add the `licenses` job and the `isolation` job.
  - `tests/snippet_envs.json`: add routing for `pcba-design` and the mechanical skill.
- R3: Decide the license review scope. The two Containerfiles redistribute two base
  images. The supplier pages are stored copies. Decide if a third-party notice file is
  necessary.
- R4: Confirm the skill scope. The proposed set is the six current skills,
  `pcba-design`, and the mechanical export skill. State if a skill is out of scope.
- R5: Keep trust and credentials unchanged. The isolated install must not change host
  trust. Do not grant new permissions for the evaluation.

## Limits of this review

This report does not run a host evaluation, a paid call, a CAD tool, or a supplier
check. It does not approve the matrix. It read stable files only. The host index
measurement comes from the active Pi session. It does not prove Codex or Claude
behavior.
