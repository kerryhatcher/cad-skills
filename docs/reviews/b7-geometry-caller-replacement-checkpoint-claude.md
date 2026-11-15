# B7 caller and docstring replacement checkpoint (claude-skill-dev)

Date: 2026-11-14 UTC. Replaces the final geometry checkpoint for the stale radius docstring correction. Adds fab.py, workflow.py and tests/test_pcb_fab_workflow.py (which owns the mask-path regression). The earlier checkpoints stay unchanged.

## Measured results

- Geometry: `uv run tests/test_pcb_fab_package.py`: 98 of 98 passed.
- Workflow, passing run: `uv run tests/test_pcb_fab_workflow.py`: 51 of 51 passed. Retained log: `docs/reviews/b7-workflow-evidence/workflow-run-51of51.log`. The background task reported exit 0; the log itself has no exit line.
- Workflow, earlier run before the design-first fix: 48 of 50, exit 1. Retained log: `docs/reviews/b7-workflow-evidence/workflow-run-48of50-failed.log`. Its two failed checks were: the supplier stopped on quantity 5 (returned 3, because design outputs were missing), and the source-rule check (missing, for the same cause). The test was corrected to run design first; the corrected run passed.
- Interrupted run with a duplicate main body that called itself recursively: `docs/reviews/b7-workflow-evidence/workflow-run-interrupted-recursive.log`, stopped by me.

Log hashes: `docs/reviews/b7-workflow-evidence/logs.sha256`.

This record does not claim full workflow acceptance. Open items are listed in `b7-r8-acceptance-mapping-claude.md`.

## SHA-256 of the reviewed code and tests

```text
dd5daa3ee98e996c4a846cc0551c9eac40ee28d05851a72f37ba67144f4ea442  tests/test_pcb_fab_workflow.py
d6d13ab732190b7be0a029fb1f3ce27c81506fd8f94c83e1989cffe2cbc2adeb  skills/pcb-fab-package/scripts/fab.py
bca595484e0298362d5173a5b94ae37360855a3ade8b3e114188c68c412adbb1  skills/pcb-fab-package/scripts/workflow.py
bd37508707cc93fd9a251503de4619a3abfece8986fd9052da242b57df598f2a  skills/pcb-fab-package/scripts/inspect_mask.py
26b765635fd666577fa34dbf4a5ee0d8ad546b7188e82a385c66c791922954d2  tests/test_pcb_fab_package.py
```
