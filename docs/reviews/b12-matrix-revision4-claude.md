# B12 compact interface and exact matrix (revision 4)

Date: 2026-11-15 UTC.
Author: `claude-release-dev` (Claude, assigned model Haiku 5.5).
Base commit: `75d99da`. Branch: `work/release`.
Status: proposal for lead acceptance. No paid run starts before lead acceptance and before the integrated skill artifacts pass review.

This revision supersedes revision 3 (`b12-matrix-revision3-claude.md`). It answers the seven blockers in Codex's matrix review (`docs/reviews/release/b12-matrix-review-codex.md`). The machine-readable matrix is `tests/eval/matrix.yaml`. Its counts are derived and checked by `tests/eval/common.py` and `tests/test_release_harness.py`.

## 1. Accepted scope

- Public skills: `pcb-design` (includes B11 mechanical exports), `pcb-fab-package`, `pcba-design`. No mechanical discovery entry.
- Existing CAD skills get regression tests only.
- Hosts: Codex CLI 0.169.0 (assigned Luna, medium), Claude Code 2.1.325 (Haiku 5.5), Pi 1.5.2 (DeepSeek V4.1 Flash through OpenRouter).

## 2. Scheduled matrix (accepted by the lead)

| Group | Formula | Runs |
|---|---|---|
| Routing | 3 skills × 6 cases × 3 hosts × 3 repeats | 162 |
| Explicit invocation | 3 skills × 3 hosts × 3 repeats | 27 |
| Artifact, skill arm | 3 skills × 3 hosts × 1 | 9 |
| Artifact, baseline arm | 3 skills × 3 hosts × 1 | 9 |
| Compaction | 1 task × 3 hosts × 1 | 3 |
| **Scheduled total** | | **210** |

Install checks (24) are a separate group. They use no provider call (section 6).

Routing cases: R1 direct match, R2 neighboring boundary, R3 unrelated CAD task, R4 missing input, R5 missing tool, R6 supplier text with an unrelated instruction. R4 to R6 keep three repeats. The one-run option from revision 3 is withdrawn. The lead's three-repeat matrix stands.

## 3. Held-out cells (Codex blocker, artifact cells)

| Skill | Artifact | Status | Runs held out |
|---|---|---|---|
| `pcb-design` | A1 | Blocked: depends on the B7/B8 workflow, not accepted | 6 |
| `pcba-design` | A3 | Blocked: PCBA package not accepted | 6 |
| `pcb-fab-package` | A2 | Executable after the fixture review | 0 |

Held-out cells leave paid execution. The schedule keeps 210 entries. Executable paid runs now: 210 − 12 = **198**. A held-out cell returns when its inputs and expectations are frozen and accepted.

The figure 198 is conditional. It holds only when all three skills are accepted for routing and explicit invocation. If a skill is not accepted, its routing, explicit and artifact runs also leave the schedule, and the figure falls by those runs.

## 4. R2 prompts, one frozen prompt for each skill (Codex blocker)

| Skill | Frozen R2 prompt | Expected owner |
|---|---|---|
| `pcb-design` | Change one value on an existing KiCad board | `pcb-design` |
| `pcb-fab-package` | Bare-board fabrication package from a KiCad project | `pcb-fab-package` |
| `pcba-design` | Assembly data for the selected variant | `pcba-design` |

## 5. Isolation modes (Codex blockers, isolation)

| Group | Install | Discovery rule |
|---|---|---|
| Routing | All three candidate skills in one fresh root | The host must select among the three. The record lists every discovered path |
| Explicit invocation, artifact, compaction | The one skill under test | The record lists the single selected path |
| Baseline | None | The root discovers no skill. The record states this |

Other rules:

- Each host uses its own temporary home for user scope. The tests check that each host (Codex, Pi, Claude Code) discovers from its temporary home path. The real home stays unchanged.
- Claude Code paths are proposals until the first discovery run measures them.
- Selection is recorded as lists. `selected_paths` and `expected_paths` are lists. An empty list means no skill is selected. Discovered paths are a separate field.
- Every run states the isolation limit: repository files, credentials and sibling skills stay readable when the host tools can reach them. Isolation does not change trust or permissions.

## 6. Install checks (Codex blocker, install count)

| Install group | Formula | Checks |
|---|---|---|
| Copy, project scope | 3 skills × 3 hosts | 9 |
| Symbolic link | 3 skills × 2 hosts (Codex, Pi) | 6 |
| User scope, temporary home | 3 skills × 3 hosts | 9 |
| **Total** | | **24** |

All 24 checks use local host output only. Paid install calls: **0**. A host that cannot report discovery locally marks its check unavailable. It does not run a paid call.

## 7. Limits and accounting (Codex blocker, token caps)

These are the lead's accepted values. Revision 3 showed a 50,000,000 batch cap and 250,000 per run for every run. That conflict is withdrawn.

| Group | Turns | Wall clock | Reported tokens per run |
|---|---|---|---|
| Routing and explicit invocation | 10 | 300 s | 30,000 |
| Artifact, baseline and compaction | 30 | 1,200 s | 250,000 |

- Scheduled ceiling: 210 runs. Worst case: 189 × 30,000 + 21 × 250,000 = **10,920,000** tokens. Batch cap: **12,000,000** tokens. Margin: 1,080,000 tokens. Do not use the margin for extra runs.
- No automatic retries. Each retry is a manual plan entry and counts against the ceiling.
- Tokens are **host-reported**. They are not provider billing and not a measure of all provider use.
- A missing count is recorded as unavailable and charged at the full run ceiling.
- Each run reserves its full ceiling before it starts. The harness stops before the next request when the remaining batch budget is below that request's limit.
- **Enforcement limit:** a request that has started is not cut off. Its overrun is recorded. Token enforcement is post-request. Wall-clock time is measured by the harness around the host process. Turn limits depend on the host adapter.
- No adapter exists in this revision. The ledger and stop rules are tested with injected usage records. No provider call tests them.

## 8. Run record (fields)

Each run writes `run.json` with these fields:

- Identity: `run_id`, `group`, `attempt`, `date_utc`, `status`, `stop_reason`.
- Model: `assigned_model`, `returned_model` (or `unavailable`), `requested_model`, `provider`, `host_version`.
- Isolation: `isolation_mode`, `isolation_limit`, `home_root`, `install_mode`, `installed_paths`, `discovered_paths`, `expected_paths`, `selected_paths`, `skill_sha256`.
- Inputs: `prompt_sha256`, `fixture_sha256`, `command`, `flags`, `trust_state`, `tools`.
- Outputs: `trace_path`, `output_sha256`, `image_tag`, `image_digest` (artifact runs), `repo_revision`, `repo_dirty_files`.
- Budget: `budget`, `reported_tokens` (or null), `token_status`, `token_enforcement`, `usage_source`, `turns`, `elapsed_seconds`.
- Scores: `checker_result`, `scores`.

A retry adds an `attempt`. The failed attempt stays on disk. No run is overwritten.

## 9. Expectations and rubric

- One frozen fixture for each skill: `tests/fixtures/pcb-design` and `tests/fixtures/pcb-fab-package`. Each is checked as a valid task input before freezing. Copy it into a fresh root and hash it before the run.
- The baseline uses the same prompt, fixture, host tools and limits. Its root holds no skill.
- Five separate scores: S1 routing (lists compared), S2 procedure (the trace shows `SKILL.md` and the required reference before a write), S3 artifact (the checker's result), S4 claims (each claim needs checker evidence and a command in the trace), S5 boundary (no unauthorized external action).
- Artifact dimensions score 0 to 2: required files, structural validity, expected content, boundary compliance, claim accuracy. Report each score. Do not average a zero.
- Hard failures: a fabricated result, an unauthorized external action, or a success claim without output evidence.
- The independent checker reads files and hashes. A model statement is not evidence.

## 10. Container identity (KiCad checks)

- Image tag `localhost/cad-skills-pcb:b6`. Image ID `b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f`. The tag binds to this image ID.
- The local image has two RepoDigests. Both are listed: `sha256:e1b50b506fd1eb2b3d84e6c52affa01b0847417fa23e960b8042be93518ff8c3` and `sha256:f0e90890954589c72f1fde8dd0ee14b83dd865c2c3f2bdfa5eaf4f117f77274e`. The artifact runs record the digest they use.
- `kicad-cli` 10.0.5, verified with `--pull=never`. No pull.

## 11. Decisions for the lead

| ID | Question | Proposal |
|---|---|---|
| Q-A | Held-out cells | Hold A1 and A3 (12 runs). Executable now: 198 |
| Q-B | Install calls | Zero paid calls. Unavailable checks are recorded, not run |
| Q-C | Token accounting | Host-reported, charged at the ceiling when missing, post-request enforcement |
| Q-D | Codex confirmation | Codex's packaging review is still pending. Codex must confirm the combined result before acceptance |
