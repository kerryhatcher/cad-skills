# Context handoff: Claude (claude-mechanical-dev)

Date: 2026-11-15 UTC. Model: claude-haiku-5-5 (unchanged). No model change was made.

## Identity and location

- Team: mechanical (B11). Lead: skill-dev-lead, pane `w1P:p3`. Codex: codex-mechanical-dev, pane `w1P:pB`. Pi: pi-mechanical-dev, pane `w1P:pE`. Claude (this agent): claude-mechanical-dev, pane `w1P:p8`.
- Working directory: `/mnt/storage/projects/cad-skills-worktrees/mechanical`
- Branch: `work/mechanical`. Base commit: `75d99da`. Not committed. Nothing merged or pushed.

## Accepted interface

- Revision 8 of the B11 combined interface is accepted by the lead and both reviewers.
- File: `docs/reviews/mechanical/b11-interface-claude.md`
- SHA-256: `5a0b4850aa57c11973560ca2551ead734b7fcfd3cc70a168d8ec3f25495966f5`

## Freeze status and paths

No product edits are allowed while the residual batch is frozen. The next product change needs the lead's release.

Current frozen set: residual correction batch.
- Manifest: `docs/reviews/mechanical/b11-residual-batch.sha256`
- Manifest SHA-256: `2f264b6790010a58e5771fbb62ee2542c725528ac05bc344baa002fd31a82204`
- Covers 21 files: `skills/pcb-design/scripts/mechanical.py`, `skills/pcb-design/scripts/mechanical_fit.py`, `skills/pcb-design/scripts/pcb.py`, `skills/pcb-design/templates/mech-fit-a/*` (make_fixture.py, fixture-source.json, component-evidence.json, export-settings.json), `skills/pcb-design/references/mechanical-fit.md`, `tests/test_mechanical.py`, `tests/test_mechanical_fit.py`, `tests/fixtures/mech-fit-a/*`, and `docs/reviews/mechanical/b11-residual-evidence/*`.

Superseded (historical, kept as evidence):
- Repair batch manifest `docs/reviews/mechanical/b11-repair-batch.sha256`, SHA-256 `f618d854b1b44f2a16af7baa9625380b3e1d5761d8737730802b49844373dfdb`, evidence `docs/reviews/mechanical/b11-repair-evidence/`.
- Completion batch manifest `docs/reviews/mechanical/b11-completion-batch.sha256`, SHA-256 `f6d69c03847689592a716006f1c2048bd069b0698fe1a4d60a71406c8d013417`, evidence `docs/reviews/mechanical/b11-e2e-evidence/`.

## Pending reviews

- Pi and Codex: review of the residual correction batch. Both were asked to check the manifest, the tests and the corrected positive flow.
- Lead: release of the residual batch. Nothing proceeds until the lead releases it.

## Scratch and evidence paths

- Scratchpad root: `/tmp/claude-1000/-mnt-storage-projects-cad-skills-worktrees-mechanical/3cdd52be-0def-47cb-b9ba-8d59fff2a7a5/scratchpad/`
- End-to-end fixtures and drivers: `scratchpad/e2e/` (flow4 and flow5 are the latest fixtures; `neg_run2.py` is the negative driver; `repair_negatives.json` holds the repair negatives).
- The scratchpad is not product. It is read-only evidence. Do not maintain a second implementation there.
- Retained evidence in the repository: `docs/reviews/mechanical/b11-residual-evidence/` (current), `b11-repair-evidence/` (historical), `b11-e2e-evidence/` (historical).

## Authorized next step

1. Wait for the Pi and Codex reviews of the residual batch.
2. If both accept, wait for the lead's release. If a finding remains, the lead decides whether it is a new correction batch.
3. After release only, commit the scoped change if the lead asks. No merge and no push without acceptance.

## Unresolved items

- Pi N1 (connector side and depth) is corrected in the residual batch. Pi and Codex confirmed the fix is pending their review of the frozen set.
- The residual evidence log is corrected. The historical repair log still shows the old `pcb.py --project` line. That is kept on purpose.
- The slot refusal is measured through the DXF arc form. The Excellon `G85` form is covered by a unit test only.
- The C09 cavity rule and the connector body length are project-authored test rules. They make no datasheet or detailed component-fit claim.
- The mixed drill role is resolved by separate `board-PTH.drl` and `board-NPTH.drl` files, measured in the local image.

## Rules that still apply

- No product edits while frozen. A review finding alone does not release a frozen set.
- No commits, merges or pushes before the lead's acceptance.
- Use the pinned local image ID. No pull.
- Use `uv` for Python. Write text in ASD-STE100 Simplified Technical English.
- Herdr messages: prefix `[$date - $time] To: $agent; From: $agent - ` with the UTC date as `YYYY-MM-DD` and the time as `HH:MM:SS UTC`. Use `/proc/482044/exe agent prompt <pane or name> "<text>"`. Use the team names given above.
- Keep retained evidence. Do not overwrite historical evidence folders.
