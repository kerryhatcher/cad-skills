# claude-skill-dev context handoff (2026-11-15, 03:33 UTC)

Model: claude-haiku-5-5 (Haiku 5.5). Environment unchanged. Original worktree: /mnt/storage/projects/cad-skills, branch main, uncommitted. No commit made. Frozen files must not change.

## Herdr panes
- skill-dev-lead (root): w1P:p3
- claude-skill-dev (author, this session): w1P:p4
- codex-skill-dev (reviewer): w1P:p5
- pi-skill-dev (reviewer): w1P:p6
Send with `/proc/482044/exe agent prompt <pane> "<message>"`. Use the prefix `[YYYY-MM-DD - HH:MM:SS UTC] To: NAME; From: NAME - `. Do not wait on a prompt; the call can time out.

## Accepted records
- B7 publication (C1, C2, C3, C5, C6, C7, geometry, report keys): `b7-publication-acceptance-root.md` (accepts `b7-residual-publication-repair-claude.md`, hash 08ec5765fa96e35988a2d08cb70b60a72687aa28bc551bb2a6f64b228ac93b06).
- Residual publication freeze hash: 08ec5765fa96e35988a2d08cb70b60a72687aa28bc551bb2a6f64b228ac93b06
- Workflow suite 132 of 132 and package suite 101 of 101, exit 0 (logs in docs/reviews/b7-workflow-evidence/).

## Frozen documentation set (2)
- Record: `docs/reviews/oshpark-setup-documentation-freeze-2-claude.md`, hash 9caa827162cdaeaddf2039cb8864cc1223af1771e723f32bf8e6780fd35ee268. Accepted by Codex (freeze-2 review). Freeze 1 (`oshpark-setup-documentation-freeze-claude.md`) is history.
- Note: `skills/pcb-fab-package/SKILL.md` changed later (retrieval command row and file entry). Its current hash is in the implementation freeze, so freeze 2 is superseded for that file.
- Reference installed at `skills/pcb-fab-package/references/oshpark-kicad-setup.md` (hash 91bf7ac5ecf5946dd57c1f0e72a11f3958589c69545821becbf006b118b094af, unchanged since freeze 2).

## Retrieval implementation (frozen, both reviews pending)
- Record: `docs/reviews/source-retrieval-implementation-freeze-claude.md`, hash 386106caae33fc9347d6e6cbafe07392aa50763992d6d41f9067d5c4a89448c8.
- Code: `skills/pcb-fab-package/scripts/fetch_sources.py` (33397ab9...). Tests: `tests/test_source_retrieval.py` (48 of 48, exit 0). Hash list: `docs/reviews/source-retrieval-implementation-files.sha256`.
- Compatibility proposal: `docs/reviews/proposals/source-retrieval-interface-claude.md`, hash faa31c20ff804c066600333f3d813db3203bda759048a56d9267056d5627d10e. Reviewer compatibility: Codex accepted revision 63bb2d36 earlier; later revisions (b2cdf367, faa31c20) need review. Pi has not reviewed the compatibility revision.

## Source-normalization dependency (open, release-owned)
- Release worktree `/mnt/storage/projects/cad-skills-worktrees/release/skills/pcb-fab-package/sources.yaml` still holds full repository-relative profile paths. Release is implementing the five normalized `supplier/profiles/<name>.yaml` values under `b12-bom-acceptance-normalization-root.md` and will send the exact manifest hash after review.
- Until the lead confirms that hash, the source manifest is NOT installed. Do not infer installation.
- The retrieval command refuses the unnormalized manifest with exit 2.

## Remaining completion items
1. Compatibility review of the current proposal revision by Codex and Pi.
2. After the normalized manifest hash is confirmed: run `tests/test_source_retrieval.py` and a manifest check against the normalized file. Do not change the frozen code.
3. Setup documentation: the stale coverage-report state was corrected in freeze 2. Remaining items are measurements only (drill mirror, alternate mode, decimal zero format, zone-fill precondition, slot effect).
4. B7/B8 trial command table with explicit paths (inventory item 8, open).
5. Both reviewers' implementation review of the residual freeze (inventory item 9, open).
6. Stale command-status prose in SKILL.md: verify against the code in the final documentation pass.
7. Release provenance and distribution tests: release-owned.
8. Standalone release acceptance: not started.

## Key decisions to keep
- Exit precedence: validation 2, fetch or write failure 3, candidate, changed or magic mismatch 1, otherwise 0.
- Magic tokens: markup, %PDF, PK\u0003\u0004, OLE2, null. pdf, xlsx and none are refused.
- profile_binding names a profile, never a destination. Bound pages sit under supplier/pages and end in .html.
- Full-copy setup pages are local evidence excluded from distribution. Unset hashes are review candidates, not accepted entries.
- No license gate. No changed source is accepted automatically.
