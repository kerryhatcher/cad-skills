# B12 combined decision after the reviews

Superseded in part. Section 4 (matrix counts) is replaced by `docs/reviews/b12-matrix-revision3-claude.md`. Sections 1 to 3 and 6 stay valid as records.

Date: 2026-11-15 UTC.
Author: `claude-release-dev` (Claude, model `claude-haiku-5-5`).
Worktree: `/mnt/storage/projects/cad-skills-worktrees/release`. Branch: `work/release`. Base commit: `75d99da`.
Inputs:

- `docs/reviews/b12-interface-claude.md` (this team's interface and acceptance cases).
- `docs/reviews/release/b12-harness-review-codex.md` (Codex, written before the interface request).
- `docs/reviews/release/b12-harness-review-pi.md` (Pi, written in response to the interface request).

Codex has not yet answered the interface request. Its report at `docs/reviews/release/` covers the preparation only. The Codex answer is still pending.

Status: combined decision for the lead. No implementation and no paid run starts before lead acceptance.

## 1. Verified facts

| Claim | Check | Result |
|---|---|---|
| The four accepted CAD skills have `license` and `metadata` | `grep` on `skills/*/SKILL.md` | Confirmed for `cadquery`, `print-prep`, `prusaslicer` and `structural-analysis` |
| `pcb-design` and `pcb-fab-package` lack `license` and `metadata` | Same `grep` | Confirmed |
| Codex version | `codex --version` | `codex-cli 0.169.0` |
| Claude Code version | `claude --version` | `2.1.325 (Claude Code)` |
| Pi version | `pi --version` | `1.5.2` |
| Baseline tests | `tests/test_skill_packages.py`, `tests/test_project_io.py` | 8 of 8 and 11 of 11 passed |
| Pi ran `tests/test_pcb_tools.py` | Pi report | 59 of 59 passed. This team did not run it. It is not part of the baseline above |
| Fixtures exist | `tests/fixtures/pcb-design`, `tests/fixtures/pcb-fab-package` | Confirmed. The `pcb-fab-package` tree holds `inventory`, `mask`, `slot` and a PNG. It is not a complete KiCad project |

## 2. Arithmetic error in both reviews

Both reviews state 54 routing runs for 3 skills, 6 cases and 3 hosts. That number is one run for each cell. The lead's default is three routing runs for each host and case. The correct count with three repeats is:

3 skills × 6 cases × 3 hosts × 3 repeats = **162** routing runs.

Pi and Codex both state 72 total runs. The same error carries into that total. This team corrects the count in section 4.

## 3. Agreements

| Topic | Agreed decision |
|---|---|
| Three separate host and model pairs | Codex, Claude Code and Pi with DeepSeek. Record the requested name, the returned identifier and the host version. Do not pin a model name from prior research |
| Pi route | OpenRouter, not the direct DeepSeek API. No transfer of results to the direct route |
| No provider success from mocks | Mocks carry the label `mock` or `fixture`. They never enter the release result table |
| Separate scores | Routing, procedure, artifact and claims are scored apart. No combined score |
| Artifact score | Each dimension scores 0, 1 or 2. Dimensions: required files, structural validity, expected content, boundary compliance and claim accuracy. No average hides a zero |
| Hard failure | A fabricated result, an unsafe external action or a success claim without output evidence |
| Independent check | The checker reads produced files and hashes. A final statement or a trace alone does not prove an artifact |
| Retained evidence | Prompts, commands, flags, host versions, requested and returned model identifiers, provider route, trace, selected path, outputs, return codes, hashes, checker output, repository revision, dirty state. Failed runs stay |
| Frozen inputs | Hash the prompt, fixture, skill package, host configuration and expectation file before each run |
| Baseline | Same prompt, fixture, host tools and limits. The skill package is removed from the baseline host |
| Compaction | Define the task and the trigger before the run. After compaction, the release action requires a reread of the active skill. If the host does not compact, the case is recorded as not exercised |
| Install modes | Copy for each host. Symbolic link for Codex only. Install only the target skill. Use a temporary home and a separate project root |
| Isolation limit | A prompt does not hide the repository, `AGENTS.md`, plans, credentials or sibling skills. Isolation is not a sandbox |
| Stop on provider error | The batch stops. The failure record stays |
| Run and token ceilings | Both are required in the matrix before the batch (section 5) |
| No trust change | No trust or permission change during any run |
| Stable batch handoff | Each stable batch goes to the reviewers with its paths, hashes, install command, isolated root, host version, prompt, expected files, check method and observed failure output. This matches Pi C3 |
| Frozen fixture per skill | One frozen fixture for each skill with a hash and an expectation file. This matches Pi C4 |
| Wait for matrix acceptance | No paid run before lead acceptance. This matches Pi C5 |
| No explicit Codex or Claude fields in portable `SKILL.md` | Pi C2 and this team agree. `agents/openai.yaml` is added only when a Codex discovery test requires it |
| `allowed-tools` is not a permission boundary | Agreed |
| Keep the three host-specific discovery paths | Pi and Codex give the same paths for Codex and Pi. The release report records the installed path and the selected path |
| Script resolution from an unrelated directory | Separate case. Agreed |
| Explicit invocation recorded separately | Agreed. An unsupported mode is recorded as not applicable |

## 4. Corrected fixed matrix (proposal for lead acceptance)

### 4.1 Routing cases

Both reviews give the same six cases. This team adopts them:

1. Direct task match.
2. Neighboring skill boundary.
3. Unrelated CAD task.
4. Missing required input.
5. Missing required tool.
6. Supplier text with an unrelated instruction.

For cases 4 to 6, the expected routing result is a selection of the correct skill followed by a stop of the dependent work. The procedure score and the claim score then decide the outcome. Case 3 expects no PCB skill.

### 4.2 Option A (default, follows the lead's three-repeat rule)

Two skills in the first gate: `pcb-design` and `pcb-fab-package`.

| Group | Count | Calculation |
|---|---|---|
| Routing | 108 | 6 cases × 3 repeats × 3 hosts × 2 skills |
| Artifact runs | 12 | 2 skills × 3 hosts × 2 arms (skill, baseline) |
| Explicit invocation | 6 | 2 skills × 3 hosts × 1 run. Unsupported mode is not applicable |
| Compaction | 3 | 1 task × 3 hosts. Pi proposed 2 (see D3) |
| **Paid total** | **129** | |
| Install checks | 8 | 2 skills × (3 copy installs + 1 Codex symbolic link). Paid only where the host needs a model call to list skills |

Explicit invocation changes from three repeats to one run. Pi and Codex both use one run for it. Explicit naming does not test a model choice, so one run is enough to show support or non-support.

### 4.3 Option B (cost option)

Negative cases (4, 5, 6) run once for each pair. Cases 1 to 3 keep three repeats.

| Group | Count | Calculation |
|---|---|---|
| Routing | 72 | (3 × 3 + 3 × 1) × 2 skills × 3 hosts |
| Artifact, explicit, compaction, install | As in 4.2 | No change |
| **Paid total** | **93** | |

### 4.4 Adding the third skill

When `pcba-design` is accepted, both options grow by one skill. Option A becomes 162 routing runs. Option B becomes 108. The mechanical skill and the four accepted CAD skills join only on a lead assignment.

### 4.5 Limits for every paid run

Proposal for lead confirmation:

- At most 30 agent turns.
- At most 1200 seconds of wall-clock time.
- At most 300 seconds for each tool command.
- A token ceiling of 400,000 input and output tokens per run. Stop the run at the ceiling and record the stop.
- A provider error stops the batch.

## 5. Changes to the interface document

- Section 4.3 of `b12-interface-claude.md` is superseded by section 4 here.
- AC-01 counts become 129 (Option A) or 93 (Option B), not 90.
- The routing case set in section 4 of the interface is replaced by the six cases in section 4.1 here.
- The fixture source changes. See section 6.

## 6. Disagreements and resolutions

| Item | Source | This team's decision |
|---|---|---|
| C1: add `license: MIT` and `metadata` to `pcb-design/SKILL.md` and `pcb-fab-package/SKILL.md` | Pi | **Not done by this team.** The skill files belong to the skill owners. Their content is outside release scope. The lead must assign this change. The verified fact in section 1 supports it. Pi also says to keep the body unchanged. This team agrees with that condition |
| Fixture source | This team proposed a copy of the native RC template. Pi proposes `tests/fixtures/pcb-design` and `tests/fixtures/pcb-fab-package` | **Adopt Pi.** The fixture must be checked before freezing. The `pcb-fab-package` tree is not a complete KiCad project, so this may need a lead decision. Recorded as D9 |
| Matrix size for three skills | Pi and Codex say 72 total runs | Corrected. See section 2 |
| Skill scope | Pi R4 asks for all six current skills plus `pcba-design` and the mechanical skill | First gate is two skills. The other skills join on lead assignment (D7) |
| Licensing scope for Containerfiles and supplier pages | Pi R3 | Adopt as a licensing item. The third-party notice file is a lead decision (D10) |
| CI jobs for tests not in CI | Pi section 4 lists `test_pcb_design.py`, `test_pcb_fab_package.py`, `test_pcb_fab_workflow.py` and the trial tests | Correct. Adding them is a shared CI change. The lead decides the timing after B7 to B11 acceptance (D11) |
| Model names | Pi table says Codex `Luna medium`, Claude `Haiku 5.5`, Pi DeepSeek. Codex says it cannot confirm the active Codex model from the launcher path | Record the assigned name, then the returned identifier at run time. The model is not forced. Codex's caution stands |
| Herdr | Codex warns not to restart the server | Agreed. The server was not restarted |

## 7. Decisions requested from the lead

| ID | Question | This team's proposal |
|---|---|---|
| D1 | Harness directory | `evaluation/` |
| D2 | Negative cases (4, 5, 6) | Option A: three repeats. Option B: one run |
| D3 | Compaction runs | Three runs, one for each host (this team). Pi proposed two. Lead chooses |
| D4 | Explicit invocation | One run for each skill and host |
| D5 | Gate thresholds | Explicit routing: 3 of 3. Natural positive routing: at least 2 of 3. Negative routing: 3 of 3. Artifact: every expectation passes in the skill arm |
| D6 | Run limits | Section 4.5 |
| D7 | Skill scope | Two skills now. `pcba-design` after its acceptance. The mechanical skill and the four accepted CAD skills on assignment |
| D8 | Model and host versions | Assigned names recorded. Returned identifiers and versions recorded at run time. Current host versions: Codex `0.169.0`, Claude Code `2.1.325`, Pi `1.5.2` |
| D9 | Fixture source and suitability | Use `tests/fixtures/pcb-design` and `tests/fixtures/pcb-fab-package`. Verify that each is a valid task input before freezing it |
| D10 | Third-party notice file | Lead decides whether `docs/release-licensing.md` is enough, or a root `NOTICE` file is needed |
| D11 | Timing of CI jobs for other tests | After B7 to B11 acceptance |
| D12 | License and metadata for `pcb-design` and `pcb-fab-package` | Lead assigns the owner of this skill-content change. Release does not edit the skills |

## 8. Shared changes proposed for lead acceptance

These changes come from section 7 of the interface and from Pi R2. None is applied yet.

- `.github/workflows/test.yml`: add a `release-harness` job for mock-only tests. Add `licenses` and `isolation` jobs (Pi R2). Keep `contents: read`.
- `AGENTS.md`: add the release test command and the isolation limit. State that paid evaluation runs are manual.
- `README.md`: add the PCB skill rows, the install paths for each host, the supported host versions, the isolation limit and the license statement.
- `.gitignore`: ignore `evaluation/runs/`. Do not ignore fixtures.
- `tests/snippet_envs.json`: Pi R2 proposes routing for `pcba-design` and the mechanical skill. This is outside release scope until the lead assigns it.

## 9. Next steps after acceptance

1. Freeze the fixtures and the expectation files for the two skills (D9).
2. Write `evaluation/isolate.py`, `evaluation/check_artifacts.py`, `evaluation/score.py` and `tests/test_release_harness.py`. Run the static tests.
3. Send each stable batch to both reviewers with the hashes and the install command (Pi C3).
4. Run no paid batch until the lead accepts the matrix.
