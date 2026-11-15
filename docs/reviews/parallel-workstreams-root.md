# Parallel workstreams

The user authorized these teams, separate worktrees, and integration by the lead on 2026-11-15 UTC.

The common snapshot includes accepted B1 to B6 and incomplete B7/B8 work. It is not a release.
The original worktree stays at `/mnt/storage/projects/cad-skills`. The fabrication team continues there.
The lead keeps its index and HEAD unchanged when the lead makes the common snapshot.

## Teams and ownership

| Team | Branch | Worktree | Scope |
|---|---|---|---|
| PCBA | `work/pcba` | `/mnt/storage/projects/cad-skills-worktrees/pcba` | B9/B10, `skills/pcba-design`, dedicated tests and fixtures |
| Mechanical | `work/mechanical` | `/mnt/storage/projects/cad-skills-worktrees/mechanical` | B11, mechanical exports, asymmetric fit example, dedicated tests |
| Release | `work/release` | `/mnt/storage/projects/cad-skills-worktrees/release` | B12, evaluations, CI, installation tests, repository documentation |

Each team has Claude with Haiku, Codex with Luna, and Pi with DeepSeek.
Claude writes product files. Codex and Pi write separate review reports. Both reviewers examine each stable change.
The lead resolves conflicts and accepts changes before integration. Agents do not merge branches or push changes.
Agents can make scoped commits after both reviews and lead acceptance. This replaces the earlier no-commit rule for these branches.

## Shared files

The release team owns repository README, AGENTS, CI, and shared test configuration changes.
The lead owns contract changes and their distribution to skill copies.
Other teams propose shared changes in their reports. They do not change shared files without a lead assignment.
The mechanical team owns new mechanical modules and references in `pcb-design`.
Changes to existing `pcb.py` or copied contracts need a lead assignment before implementation.
Each skill must operate alone. A skill cannot import another skill at runtime.

## Start procedure

1. Read `AGENTS.md` and `docs/pcb-pcba-plan.md`.
2. Read the preparation reports for your batch.
3. Write a compact implementation interface and acceptance cases.
4. Ask both reviewers for concrete corrections and agreement.
5. Send the combined interface to `skill-dev-lead` at `w1P:p3`.
6. Implement agreed work in small batches after the lead accepts the interface.
7. Freeze each review batch with exact paths and hashes.
8. Retain commands, exit codes, and independent results.

Use `/proc/482044/exe` for Herdr. Do not restart its server.
Prefix each Herdr message with `[YYYY-MM-DD - HH:MM:SS UTC] To: AGENT; From: AGENT - `.
Use the measured UTC time. Use explicit pane IDs from the lead assignment.
Do not change the assigned model. Use `uv` for Python and STE for text.
Do not contact suppliers, place orders, or upload designs.

## Scope inputs

PCBA reads `b9-proposal-inputs-root.md`, `b9-source-addendum-root.md`, and `b9-drill-probe-root.md` in this directory.
Use the retained Sierra source evidence. Resolve coordinate conventions with independent fixtures before a supplier qualification claim.

Mechanical reads `b11-preparation-pi.md`. The accepted B5 STEP contains only the board.
Use licensed models or labeled conservative proxies. Do not claim detailed component fit from a proxy.
Keep the accepted trial history unchanged. Use an asymmetric fixture with an explicit transform and a bottom-side part.

Release reads `b12-preparation-codex.md` and the harness research reports.
Prepare the evaluation harness and CI now. Final evaluations use the integrated skill files after their reviews.
Use filesystem isolation, fixed task expectations, retained failures, and independent artifact checks.
Do not count a draft skill test as final release acceptance.

## Integration

The lead integrates accepted branch commits in a separate integration worktree.
The lead resolves shared changes and runs the affected tests before acceptance.
Final integration includes the fabrication changes from the original worktree.
The lead does not overwrite uncommitted files in the original worktree.
The final release runs the repository tests and all applicable skill acceptance tests.
