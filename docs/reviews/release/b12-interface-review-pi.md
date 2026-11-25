# B12 interface review from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: review of `docs/reviews/b12-interface-claude.md`, sections 3 to 6, the
decisions D1 to D8, and the acceptance cases in section 10. This report gives
concrete corrections. It does not approve the interface. It writes no product file.

The lead restricted reviewer reports to `docs/reviews/release/`. The author asked for
`docs/reviews/b12-interface-review-pi.md`. This file is the reviewer report at the
assigned path.

## Environment

| Item | Value |
|---|---|
| Working directory | `/mnt/storage/projects/cad-skills-worktrees/release` |
| Branch | `work/release` |
| HEAD | `75d99da` |
| Host | Pi 1.5.2 |
| Requested model | `deepseek/deepseek-v4.1-flash` through OpenRouter |

## Summary

The interface is close to the recommendation in `b12-harness-review-pi.md`. The
isolation, retention, rubric, and mock-separation rules are correct in direction. This
review finds twelve concrete defects and eight missing acceptance cases. The counts in
section 4.3 are correct. The count tuple in AC-01 is not.

## Concrete defects

### D-1 Section 4.1 and D8: the assigned model is absent

The matrix says "the model selected at execution time". The team assignment is Codex
Luna medium, Claude Haiku 5.5, and Pi DeepSeek V4.1 Flash. A record of the returned
identifier does not replace the assignment.

Correction: add an `assigned_model` column. Keep the `returned_model` field. A run
records both. A run that uses a different model than the assignment stays, but it is
marked as a deviation.

### D-2 Section 3.1 rule 2: user-scope discovery is untested

The harness writes only a project-scoped path. Pi and Codex also read user scope. The
documented `npx skills add` install is user or global. Thus the harness does not test
the primary install path.

Correction: add an install mode with a temporary home. Set `HOME` to the run root.
Install under `$HOME/.agents/skills/<name>` and `$HOME/.pi/agent/skills/<name>`. This
tests user-scope discovery. It makes no write to the real user home.

### D-3 Section 3.1 rule 4: the symlink case is Codex only

The Pi research shows that Pi follows symbolic links. A Codex-only symlink case leaves
Pi unmeasured.

Correction: run the symlink case for Pi too, or state the limit in section 11. Record
the resolved path and the selected path.

### D-4 Section 5, artifact A1: the parity check needs an incomplete workflow

A1 checks that schematic and board connectivity agree. That check needs the B7/B8
workflow. B7/B8 is not accepted.

Correction: hash and freeze the accepted skill revision before A1. Mark A1 not runnable
until the lead accepts B7/B8. Do not score A1 against a changing skill.

### D-5 Section 5: the container identity is not fixed

The interface names `localhost/cad-skills-pcb:b6`. The host has two related images,
`localhost/cad-skills-pcb:b6` and `localhost/cad-skills-pcb:b6-rebuild`. The digest is
not stated. The host has no `kicad-cli`.

Correction: name the exact image tag and digest in the matrix. State that no pull
happens. Confirm that the image supplies `kicad-cli` and the expected version before A1.

### D-6 Section 10, AC-01: the count tuple does not name its groups

AC-01 writes "(63, 12, 12, 3)". Section 4.3 has five groups: routing natural 45,
routing explicit 18, artifact 12, negative 12, and compaction 3. The total is 90.

Correction: write the five group counts and the total. A bare tuple can pass with
incorrect group counts.

### D-7 Section 3, `run.json`: required record fields are absent

The record has no assigned model, temporary home root, container image digest, budget
limit, or stop reason.

Correction: add these fields:

- `assigned_model`, `home_root`, `image_tag`, `image_digest`.
- `budget` with the turn, time, token, and tool-time limits.
- `stop_reason` for a stopped run.

### D-8 Section 8: two redistributed items are absent

The license list names the KiCad container image. It does not name the `uv` image or
the stored supplier pages. The two Containerfiles use `ghcr.io/astral-sh/uv` and
`ghcr.io/inti-cmnb/kicad10_auto_full`. The skill stores supplier HTML pages under
`skills/pcb-fab-package/supplier/pages/`.

Correction: add each item with its source, license, and retrieval date. Keep the
external tools separate from the repository MIT license.

### D-9 Section 6, S3: the baseline expectation is not defined

S3 says "every expectation in section 5 passes". The baseline arm has no skill. It
cannot pass the same expectations. The baseline shows the value of the skill.

Correction: define a separate baseline expectation. The baseline result is reported
beside the skill result. State the measured difference. Keep the two arms separate.

### D-10 Section 6, S4: the claim check needs the tool trace

S4 compares the final text with the checker evidence. A claim of a completed command
needs a command in the trace.

Correction: compare each claim with the checker evidence and the tool trace. A DRC pass
claim needs a DRC command in the trace and a passing artifact check.

### D-11 Section 4.3: the limits have no token or batch ceiling

The limits give turns, wall-clock time, and a per-tool timeout. The lead asked for
explicit limits. A token budget and a total batch ceiling are absent.

Correction: add `max_tokens` for each run and `max_runs` for the batch. Stop the batch
at the ceiling and keep the record.

### D-12 Section 3.1: the retry path has no stop case

The interface keeps a failed attempt and adds a new attempt. No case tests a run that
stops at a limit.

Correction: add the missing cases M-1 and M-2 below.

## Missing acceptance cases

| ID | Case | Expected result |
|---|---|---|
| M-1 | A run exceeds the turn, wall-clock, token, or tool-time limit | The run stops. The record gives the stop reason. The attempt stays. |
| M-2 | The provider returns an error or a timeout | A failed attempt stays. No success record exists. |
| M-3 | The baseline root has no installed skill package | The check confirms the absence. The baseline does not read a skill. |
| M-4 | The baseline input bytes | The prompt, fixture, tools, and limits equal the skill arm. |
| M-5 | A user-scope install in a temporary home | The host discovers the skill from the temporary home. |
| M-6 | A malformed `SKILL.md` or a missing description | The host writes a diagnostic. The run is recorded. It is not a pass. |
| M-7 | `disable-model-invocation: true` | The skill leaves the automatic index. Explicit invocation still works. |
| M-8 | An unsupported explicit invocation mode | The run is recorded as not applicable. It is not a pass. |

## Agreement with D1 to D8

| ID | Position | Note |
|---|---|---|
| D1 | Disagree | The repository keeps test code in `tests/` and documents in `docs/`. Propose `tests/eval/` for the harness code and the fixtures. Ignore `tests/eval/runs/`. The lead decides. |
| D2 | Agree | One run for each negative case and pair. State the count in the matrix. |
| D3 | Agree with a condition | Run compaction three times only if each host compacts. Record a host that does not compact as not exercised. |
| D4 | Agree | Explicit invocation is a routing case. Three runs for each pair. |
| D5 | Agree with D-9 and D-10 | Keep the thresholds after the two corrections. |
| D6 | Agree with D-11 | Add the token and batch ceilings. |
| D7 | Agree | Add `pcba-design` only after the lead accepts it. |
| D8 | Agree with D-1 | Also state the assigned model. |

## Recommendations to skill-dev-lead

- R1: Accept the matrix after the author applies D-1 to D-12 and adds M-1 to M-8. The
  counts in section 4.3 are correct.
- R2: Decide D1. Suggest `tests/eval/` to keep one test area and one ignored run
  directory.
- R3: Require the assigned model in each matrix row and in each run record. Keep the
  returned identifier as a separate field.
- R4: Confirm the container tag and digest before any artifact run. No new image pull.

## Limits of this review

This review read the interface proposal only. It ran no host, no paid call, and no CAD
tool. It does not approve the interface. The author must apply the corrections and send
the replacement for review.
