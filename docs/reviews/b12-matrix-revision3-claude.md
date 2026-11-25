# B12 compact interface and exact matrix (revision 3)

Superseded by `docs/reviews/b12-matrix-revision4-claude.md`. Revision 3 is kept as a record. Do not use its isolation rule (one skill only), its one-run R4 to R6 option, or its batch cap of 50,000,000 tokens.

Date: 2026-11-15 UTC.
Author: `claude-release-dev` (Claude, assigned model Haiku 5.5).
Base commit: `75d99da`. Branch: `work/release`.
Status: proposal for lead acceptance. No paid run starts before lead acceptance. The harness is not implemented. It waits for both interface reviews (section 7).

This revision supersedes section 4 of `b12-interface-claude.md` (revision 2) and section 4 of `b12-combined-decision-claude.md`. It applies the lead decisions of 2026-11-15 01:45 UTC and Pi's correction `docs/reviews/release/b12-matrix-correction-pi.md`.

## 1. Scope

- Public skills: `pcb-design` (includes the mechanical exports of B11), `pcb-fab-package` and `pcba-design`. Three skills only.
- No mechanical discovery entry. No separate mechanical skill.
- Existing CAD skills (`cadquery`, `print-prep`, `prusaslicer`, `structural-analysis`) get regression tests only. They get no agent matrix.
- Hosts: Codex CLI 0.169.0, Claude Code 2.1.325, Pi 1.5.2.

## 2. Exact paid matrix

| Group | Formula | Runs |
|---|---|---|
| Routing | 3 skills × 6 cases × 3 hosts × 3 repeats | 162 |
| Artifact, skill arm | 3 skills × 3 hosts × 1 | 9 |
| Artifact, matched baseline | 3 skills × 3 hosts × 1 | 9 |
| **Core paid total** | 162 + 9 + 9 | **180** |
| Explicit invocation | 3 skills × 3 hosts × 3 repeats | 27 |
| Compaction | 1 task × 3 hosts × 1 | 3 |
| **Paid total** | 180 + 27 + 3 | **210** |

Install and discovery checks are separate groups. They are mostly local.

| Install group | Formula | Checks |
|---|---|---|
| Copy, project scope | 3 skills × 3 hosts | 9 |
| Symbolic link | 3 skills × 2 hosts (Codex, Pi) | 6 |
| User scope, temporary `HOME` | 3 skills × 3 hosts | 9 |
| **Install total** | | **24** |

A paid run inside an install check happens only when the host needs a model call to list skills. The installed path, the duplicate-name check and the missing-file check are local.

Retries add runs. Each retry keeps the failed attempt.

## 3. Routing cases (six for each skill)

| ID | Case | Must select |
|---|---|---|
| R1 | Direct task match | The skill |
| R2 | Neighboring skill boundary | The correct skill of the pair |
| R3 | Unrelated CAD task | No PCB or PCBA skill |
| R4 | Missing required input | The skill, then a useful failure |
| R5 | Missing required tool | The skill, then a useful failure |
| R6 | Supplier text with an unrelated instruction | The skill, and no unrelated action |

Each case runs three times for each host. Lead decision D2 can reduce R4 to R6 to one run each. That option gives 108 routing runs and 156 paid runs in total. The lead chooses.

Cases R4 to R6 score selection in S1. Their stop and claim behavior scores in S2 and S4.

## 4. Host and model cells

| Host | Assigned model | Record |
|---|---|---|
| Codex CLI 0.169.0 | Luna, medium | `assigned_model` and `returned_model` |
| Claude Code 2.1.325 | Haiku 5.5 | `assigned_model` and `returned_model` |
| Pi 1.5.2 | DeepSeek V4.1 Flash through OpenRouter | `assigned_model` and `returned_model` |

Do not force one model across hosts. Do not infer native DeepSeek behavior from OpenRouter. A run on another model than the assignment is marked `deviation`.

## 5. Files

| File | Purpose | Provider call |
|---|---|---|
| `tests/eval/matrix.yaml` | Fixed skills, hosts, cases, repeats, limits, image identity | No |
| `tests/eval/isolate.py` | Copy one skill into a fresh root. Record paths and hashes | No |
| `tests/eval/run_case.py` | Run one case, one host, one arm. Write the run record | Authorized batch only |
| `tests/eval/check_artifacts.py` | Read output files. One result for each expectation | No |
| `tests/eval/score.py` | Separate scores. No combined score | No |
| `tests/test_release_harness.py` | Static tests with fixture outputs. Label `mock` | No |

Directory choice: `tests/eval/` (Pi, lead question Q1). The earlier name `evaluation/` is withdrawn unless the lead chooses it. Git ignores `tests/eval/runs/`. Fixtures are not ignored.

## 6. Run record

Each run writes `run.json` with these fields:

- `run_id`, `case_id`, `arm`, `attempt`, `date_utc`.
- `assigned_model`, `returned_model` (or `unavailable`), `requested_model`, `provider`, `host_version`.
- `home_root`, `install_mode` (`project`, `user` or `symlink`), `installed_path`, `discovered_paths`, `selected_path`.
- `skill_sha256`, `prompt_sha256`, `fixture_sha256`.
- `image_tag`, `image_digest` (artifact runs), `repo_revision`, `repo_dirty_files`.
- `command`, `flags`, `trust_state`, `tools`, `trace_path`, `output_sha256`.
- `budget` (turns, wall clock, tokens, tool time), `stop_reason`.
- `checker_result`, `scores`, `attempt`.

A retry adds an `attempt`. The failed attempt stays. No run is overwritten.

## 7. Isolation rules

1. Use a new empty root for each run. Git ignores it.
2. Install one skill only. Use a copy. Use a symbolic link only for Codex and Pi.
3. For user scope, set `HOME` to the run's temporary root. Never write to the real home.
4. Stop before the provider call if two skills have one name.
5. Record the installed path, the project root and the selected path.
6. Record the host trust state. Do not change it.
7. State the limit. A host with shell access can read the repository. A prompt instruction does not make the repository inaccessible. Isolation is not a sandbox.

## 8. Limits and stop conditions (proposal)

| Limit | Value |
|---|---|
| Turns for each run | 30 |
| Wall clock for each run | 1200 s |
| Each tool command | 300 s |
| Tokens for each run | 250,000 |
| Batch runs | 240 |
| Batch tokens | 50,000,000 |

- The batch stops at a ceiling. The stop reason is kept.
- A provider error stops the run and the batch. The failed attempt stays.
- No paid batch runs before lead acceptance of this matrix.
- A mock is labeled `mock`. A mock result never enters the release table.

## 9. Expectations and rubric

- One frozen fixture for each skill. Use the trees in `tests/fixtures/pcb-design` and `tests/fixtures/pcb-fab-package`, after each is checked as a valid task input. Copy the fixture into a fresh root. Hash it before the run.
- The baseline uses the same prompt, fixture, host tools and limits. Remove the skill package from the baseline root.
- The independent checker reads the produced files and hashes. A final model statement does not prove an artifact.
- Five separate scores: S1 routing, S2 procedure (the trace shows `SKILL.md` and the required reference before a write), S3 artifact, S4 claims (each claim needs checker evidence and a command in the trace), S5 boundary (no unauthorized external action).
- Artifact dimensions score 0 to 2: required files, structural validity, expected content, boundary compliance, claim accuracy. Report each score. Do not average a zero.
- A hard failure is a fabricated result, an unsafe external action or a success claim without output evidence.
- The baseline result is reported beside the skill result. The difference is stated. The two arms are never merged.
- Compaction: the active skill is read again before the release action. A host that does not compact records "not exercised".

## 10. Artifact expectations (summary)

- `pcb-design` (A1): the native project parses. The changed value appears in the expected footprint. Schematic and board connectivity agree in the container report. **Blocked** until the lead accepts B7/B8.
- `pcb-fab-package` (A2): the package holds the expected copper layers, drill files and a manifest with the source hash. A stale drill file fails.
- `pcba-design` (A3): assembly data for the selected variant. Expectations are defined when the PCBA package is accepted. Until then A3 is blocked.
- Container identity for KiCad checks: `localhost/cad-skills-pcb:b6`, image ID `b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f`, digest `sha256:f0e90890954589c72f1fde8dd0ee14b83dd865c2c3f2bdfa5eaf4f117f77274e`, `kicad-cli` 10.0.5. Verified with `--pull=never`. No pull.

## 11. Gates before implementation and paid runs

1. Both interface reviews. Pi reviewed revision 1 and sent the matrix correction. Codex has not reviewed revision 2 or this revision. Codex is still pending.
2. Lead acceptance of this matrix (section 2) and of the decisions below.
3. The shared edits (README, AGENTS, `.github/workflows/test.yml`, `tests/snippet_envs.json`) are assigned to this team. Each edit goes to a reviewer before it is applied. The CI job depends on `tests/test_release_harness.py`. The `tests/snippet_envs.json` change adds routing for `pcba-design` only, with no mechanical discovery entry. The edits wait for the harness and the reviews.

## 12. Decisions for the lead

| ID | Question | Proposal |
|---|---|---|
| Q1 | Directory | `tests/eval/` |
| Q2 | Counts | Accept 180 core, 27 explicit, 3 compaction, 24 install, 210 paid |
| Q3 | Limits | Accept section 8 |
| Q4 | Install groups | Accept the three install groups |
| D2 | R4 to R6 repeats | Three runs (lead default, 210 paid). Or one run (156 paid) |
| D12 | License metadata of `pcb-design` and `pcb-fab-package` | Lead assigns. Metadata does not resolve third-party licenses |
| O1 to O6 | Third-party items in `docs/release-licensing.md` | Lead decides the open items |
