# B7 report-link replacement review (pi-skill-dev)

Date: 2026-11-14 UTC. Scope: `b7-report-link-replacement-claude.md`
(SHA-256 `587bd57ebf1bb1f6186c39d3c062ce3b7bfb6129d684eff9dbfa8e9792c503d6`). The scoped items are the
changed guard, the dangling-link regression, the docstring period, and the hashes. Full B7/B8 acceptance
stays separate.

## Hashes

The three changed files match the checkpoint.

```text
d410a64ac7c3e5477c8a4ae6c1258aff3b7f3324fca145cbb0966cb55821c255 skills/pcb-fab-package/scripts/fab.py
f676539a29417add821785ec81918d0c2240fbf2b8993f0f7a2fa6a0090ced24 skills/pcb-fab-package/scripts/inspect_mask.py
886ec2307efcd52fe976ba0bd2c9344db74dab081f066f2900fbc0d1ca8526af tests/test_pcb_fab_package.py
```

The 101/101 log `docs/reviews/b7-workflow-evidence/geometry-run-101of101-link.log` is
`efd9c46d0650857d5a5fadd6b98bdd934474256ef3b5f27621503f7ff2d1aa88`.

## Guard: accepted

`run_mask_worker` now reads `if rep.exists() or rep.is_symlink():`. This matches the agreement. A dangling
symlink is refused before the worker starts. The message is unchanged.

## Dangling-link regression: accepted

`tests/test_pcb_fab_package.py` function `test_report_link` makes a dangling link, runs the public
`fab.py inspect-mask` command, and checks three items: exit 2, the link is unchanged, and the target is not
created. The 101/101 log shows all three pass. The log also shows the earlier fresh-report and caller-timeout
cases.

## Docstring period: confirmed

The final `inspect_mask.py` is `1e6f12b61370862ca9a58a7eed6e6daf29c5530443b23f60cdac28509b7e80a5`. The
docstring now reads "that is positive and finite. The radius has no limit relative to the core side." The
internal semicolon is a period. The functional code is unchanged, so the 101/101 behaviour evidence still
applies. The record `b7-punctuation-final-record-claude.md` (`b66c1e44…`) states the change, the log hash
`efd9c46d…`, and the remaining list separators for the full B7 STE pass. I confirm the narrow correction.

## Minor record note

The 101/101 log is not in `docs/reviews/b7-workflow-evidence/logs.sha256`, and the checkpoint gives no hash
for it. Add it to the manifest so the record is self-contained.

## Verdict

I give final scoped acceptance. The caller guard, the dangling-link regression, and the docstring period are
present and match the agreement. The earlier geometry corrections stay. Full B7/B8 acceptance remains outside
this review.
