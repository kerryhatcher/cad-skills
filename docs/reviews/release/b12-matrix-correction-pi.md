# B12 corrected interface and exact matrix from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: corrected B12 release interface and evaluation matrix. This report applies the
lead decisions of 2026-11-15 01:45 UTC. It does not approve a paid run. Reviewers remain
reports-only. The lead assigned the shared README, AGENTS, CI, and
`tests/snippet_envs.json` edits to Claude.

## Applied lead decisions

| Decision | Result |
|---|---|
| Public skills | Three only: `pcb-design`, `pcb-fab-package`, `pcba-design`. |
| Mechanical exports | Part of `pcb-design`. Not a fourth skill. No mechanical discovery entry. |
| Existing CAD skills | Regression tests only. No agent matrix. |
| Routing count | 162 runs. This report corrects the earlier 54. |
| Core paid total | 180 runs (162 routing, 9 artifact, 9 baseline). |
| Explicit invocation | Separate group. 27 runs. |
| Compaction | Separate group. 3 runs. |
| Harness implementation | After both interface reviews. |
| Shared edits | Claude, with reviews. |
| Licensing | Third-party notice inventory. Do not relabel third-party content MIT. |

## Corrected exact matrix

### Counts

| Group | Formula | Runs |
|---|---|---|
| Routing | 3 skills × 6 cases × 3 hosts × 3 repeats | 162 |
| Artifact, skill arm | 3 skills × 3 hosts × 1 | 9 |
| Artifact, matched baseline | 3 skills × 3 hosts × 1 | 9 |
| Core paid total | 162 + 9 + 9 | 180 |
| Explicit invocation | 3 skills × 3 hosts × 3 repeats | 27 |
| Compaction | 1 task × 3 hosts × 1 | 3 |
| Paid total with the two extra groups | 180 + 27 + 3 | 210 |

Install and discovery checks are separate. They are mostly local.

| Install group | Formula | Runs |
|---|---|---|
| Copy install | 3 skills × 3 hosts × 1 | 9 |
| Symlink install | 3 skills × 2 hosts (Codex, Pi) × 1 | 6 |
| User scope, temporary home | 3 skills × 3 hosts × 1 | 9 |

A host needs a paid selection run only to confirm selection in the matrix. The installed
path, the duplicate-name check, and the missing-file check are local.

### Routing cases, 6 for each skill

| ID | Case | Must select |
|---|---|---|
| R1 | Direct task match | The skill |
| R2 | Neighboring skill boundary | The correct skill of the pair |
| R3 | Unrelated CAD task | No PCB or PCBA skill |
| R4 | Missing required input | The skill, then a useful failure |
| R5 | Missing required tool | The skill, then a useful failure |
| R6 | Supplier text with an unrelated instruction | The skill, no unrelated action |

Each case runs three times for each host. Cases R3 to R6 can use one skill label. The
lead owns any reduction of the 162 count.

### Host and model cells

| Host | Record |
|---|---|
| Codex CLI 0.169.0 | Assigned: Luna medium |
| Claude Code 2.1.325 | Assigned: Haiku 5.5 |
| Pi 1.5.2 | Assigned: DeepSeek V4.1 Flash through OpenRouter |

Record `assigned_model` and `returned_model` separately. Do not force one model across
hosts. Do not infer native DeepSeek behavior from OpenRouter.

## Compact corrected interface

### Files

| File | Purpose | Provider call |
|---|---|---|
| `matrix.yaml` | Fixed skills, hosts, cases, repeats, limits | No |
| `isolate.py` | Copy one skill into a fresh root. Record paths and hashes | No |
| `run_case.py` | Run one case, one host, one arm. Write the run record | Authorized batch only |
| `check_artifacts.py` | Read output files. One result for each expectation | No |
| `score.py` | Separate routing, procedure, artifact, claim scores | No |
| `test_release_harness.py` | Static tests with fixture outputs, label `mock` | No |

The author proposed the directory `evaluation/`. The lead decides. This review suggests
`tests/eval/` to keep one test area and ignore `tests/eval/runs/`.

### Isolation rules

1. Use a new empty root for each run. Ignore it in Git.
2. Use two install modes. Routing mode installs all three accepted skills in the fresh
   root. Single-skill mode installs one skill for artifact and explicit invocation runs.
   A single installed skill cannot satisfy an adjacent-skill routing case. The baseline
   root holds none of the three skills.
3. Use a copy. Use a symlink only where the host follows links.
4. Use a temporary `HOME` for a user-scope test. Do not write to the real home. Record
   the temporary-home discovery path for each host.
5. Stop before the provider call if two skills have one name.
6. Record the installed paths, the project root, and the selected skill names and paths.
   Store selected names and paths as lists. Use an empty list when no skill is selected.
   Keep discovered paths in a separate field.
7. Record the host trust state. Do not change it.
8. State the limit. A host with shell access can read the repository. A prompt
   instruction does not make the repository inaccessible. Record that credentials and
   sibling skills remain readable when the host tools can access them.
9. Exclude a blocked artifact cell from paid execution until its input and expectation
   are accepted. A1 waits for B7/B8. A3 waits for the accepted PCBA package. Revise the
   paid count if a blocked cell leaves the matrix.

### Run record

Add these fields to the author record:

- `assigned_model`, `returned_model`, `provider`, `host_version`.
- `home_root`, `install_mode`, `installed_path`, `discovered_paths`, `selected_path`.
- `skill_sha256`, `prompt_sha256`, `fixture_sha256`.
- `image_tag`, `image_digest`, `repo_revision`, `repo_dirty_files`.
- `command`, `flags`, `trust_state`, `tools`, `trace_path`, `output_sha256`.
- `budget` (turns, wall clock, tokens, tool time), `stop_reason`.
- `checker_result`, `scores`, `attempt`.

A retry adds an `attempt`. Keep the failed attempt. Do not overwrite a run.

### Limits and stop conditions

| Limit | Value |
|---|---|
| Turns for each run | 30 |
| Wall clock for each run | 1200 s |
| Tool command | 300 s |
| Tokens for each run | 250000 (proposal) |
| Batch runs | 240 (proposal) |
| Batch tokens | 50000000 (proposal) |

- Stop the batch at a ceiling. Keep the stop reason.
- Stop the run on a provider error. Keep the failed attempt.
- Do not run a paid batch before the lead accepts the matrix.
- Label a mock as `mock`. A mock result never enters the release table.

### Expectations and rubric

- One frozen fixture for each skill. Copy it into a fresh root. Hash it before the run.
- The baseline uses the same prompt, fixture, host tools, and limits. Remove the skill
  package from the baseline host.
- The independent checker reads files and hashes. A final model statement does not prove
  an artifact.
- Score separately: routing, procedure, artifact, procedure, claims, boundary.
- Artifact score 0 to 2 for each dimension. Report each score. Do not average a zero.
- A hard failure is a fabricated result, an unsafe external action, or a success claim
  without output evidence.

## Corrections folded in

D-1 assigned model. D-2 temporary-home user scope. D-3 Pi symlink case. D-4 freeze A1
against accepted B7/B8. D-5 image tag and digest. D-6 named count groups. D-7 record
fields. D-8 license inventory (see the notice inventory report). D-9 baseline
expectation. D-10 claim against the trace. D-11 token and batch ceilings. D-12 stop
case. Missing acceptance cases M-1 to M-8 join the static suite.

## Decisions for the lead

- Q1: Directory name `tests/eval/` or `evaluation/`.
- Q2: Accept the 180 core, 27 explicit, 3 compaction counts.
- Q3: Accept the token and batch ceilings.
- Q4: Accept the three install groups.

## Limits

This report uses no paid run. All counts are proposals until the lead accepts them. The
matrix can change after the integrated skills pass their reviews.
