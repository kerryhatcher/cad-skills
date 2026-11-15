# B7 report-link replacement record (claude-skill-dev)

Date: 2026-11-14 UTC. Applies b7-report-link-root.md, agreed by both reviewers. Changes: run_mask_worker refuses a report path that is a symbolic link, including a dangling one; the docstring semicolon in inspect_mask.py is now a period. Regression added: a dangling report link is refused (exit 2), the link is unchanged, and its target is not created. Prior records stay unchanged.

Command: `uv run tests/test_pcb_fab_package.py`
Exit: 0. Result: 101 of 101 passed. Log: `docs/reviews/b7-workflow-evidence/geometry-run-101of101-link.log`.

Changed files (sha256):

```text
d410a64ac7c3e5477c8a4ae6c1258aff3b7f3324fca145cbb0966cb55821c255  skills/pcb-fab-package/scripts/fab.py
f676539a29417add821785ec81918d0c2240fbf2b8993f0f7a2fa6a0090ced24  skills/pcb-fab-package/scripts/inspect_mask.py
886ec2307efcd52fe976ba0bd2c9344db74dab081f066f2900fbc0d1ca8526af  tests/test_pcb_fab_package.py
```
