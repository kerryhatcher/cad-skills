# Codex handoff: B10 review

Date: 2026-11-15 03:34 UTC.

## Work location and team

- Role: `codex-pcba-dev`.
- Branch: `work/pcba`.
- Working directory: `/mnt/storage/projects/cad-skills-worktrees/pcba`.
- Model for restore: GPT-6-Luna, medium.
- Herdr panes: lead `w1P:p3`, Claude `w1P:p7`, Codex `w1P:pA`, Pi `w1P:pD`.

## Accepted records

- Neutral B9: `docs/reviews/pcba/b9-neutral-complete-acceptance-root.md`.
- Sierra acceptance and B10 release: `docs/reviews/pcba/b9-sierra-acceptance-b10-release-root.md`.
- Accepted interface: `docs/reviews/b9-b10-interface-claude.md`.
- B10 execution note: `docs/reviews/pcba/b9-b10-remaining-execution-claude.md`.
- Sierra sample provenance: `docs/reviews/sierra-source-evidence/BOM-Sample-and-Demo.provenance.md`. Retrieval time and reuse terms remain unknown. The record does not claim a page fetch.

Neutral mapping, variants, rows, BOM, stock, and Sierra draft design stay accepted and closed. The current neutral/Sierra implementation remains unqualified. It does not claim a physical test pass. Supplier conventions remain unconfirmed.

## Latest stable author boundary

The latest frozen correction is `docs/reviews/pcba/b9-b10-overlap-correction-claude.md`. It lists 36 files. Codex verified all hashes and accepted its narrow scope in `docs/reviews/pcba/codex-review-b9-b10-overlap-correction.md`.

The lead now says to hold for a complete stable B10 batch. Claude owns implementation from pane `w1P:p7`. The lead's latest instruction says not to inspect changing implementation files. Wait for a complete freeze record before review.

## B10 reviewer scope

Review only a complete, frozen batch against the root release and the accepted execution note. Keep the accepted neutral and Sierra scopes closed. Verify each listed hash before code review. Do not edit product files. Do not commit, merge, or push. The snippet-routing failure remains a release-owned integration item. The author last reported 71 focused tests passing and 7 of 8 package tests passing. Do not rerun tests unless the reviewer is asked to verify them.

The B10 gate includes all eight bare-board checks and five assembly checks, their input roles, evidence files, and independent checks. The execution note requires captured inputs under the project lock, confined staging, manifest and evidence validation, final input freshness, staged output inventory and hash checks, then atomic directory publication. Unknown supplier conditions remain unqualified.
