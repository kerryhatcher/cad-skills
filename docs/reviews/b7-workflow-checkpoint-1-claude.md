# B7 workflow checkpoint: runtime, snapshots, confined publication (claude-skill-dev)

Date: 2026-11-14 UTC. Scope: runtime identity, input snapshots with absence, stage marker, confined writes, freshness at package time, and row 15a. Supplier and evidence completeness work continues after this checkpoint.

## Concrete measures and their regressions

- Runtime: every container run uses the measured image identity (`sha256:` identity matches the lock digest; the KiCad version is measured as 10.0.5). Regression: design result records the identity (pipeline rules test).
- Snapshots: every consumed input is hashed; an absent optional source rule is recorded as `absent`. Regression: absent kicad/board.kicad_dru recorded as absent; a source changed after design makes the package unqualified and stale (pipeline rules test).
- Stage marker: a stage without the marker is refused, not removed (exit 2). Regression: unmarked stage refused (pipeline rules test).
- Confined writes: a package destination outside out/fab is refused with exit 2 and creates nothing. Measured command record: `docs/reviews/b7-workflow-evidence/confinement-exit2.log`.
- Row 15a (ignore severity, source exclusion, thin tracks): the supplier trace row fails; the staged project clears the exclusion and sets the severity to error; source bytes unchanged. Regression: test_row_15a (6 checks).

## Measured results

- `uv run tests/test_pcb_fab_workflow.py`: 65 of 65 passed, exit 0. Log: `docs/reviews/b7-workflow-evidence/workflow-run-65of65-15a.log`.
- Earlier 59 of 59 run before row 15a: `docs/reviews/b7-workflow-evidence/workflow-run-59of59-rules.log`.

## Not yet covered

- Supplier and evidence completeness (process rows, manual route for region masks), the standalone test, and the mapping update. These are open.

```text
517e266c6f012191ad65b3cf95b1267dd995d5161ed23794792e331f36267fb3  skills/pcb-fab-package/scripts/workflow.py
d410a64ac7c3e5477c8a4ae6c1258aff3b7f3324fca145cbb0966cb55821c255  skills/pcb-fab-package/scripts/fab.py
93d8625f46ba0fab90312a833d431a5dfe9a3e63019c7964de8fae330d73232a  tests/test_pcb_fab_workflow.py
```
