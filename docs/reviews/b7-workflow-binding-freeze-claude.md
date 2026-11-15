# B7 workflow binding correction freeze (claude-skill-dev)

Date: 2026-11-14 UTC. Complete four-part correction (b7-workflow-correction-decisions-root.md). Earlier records and failed logs are kept.

Command: `uv run tests/test_pcb_fab_workflow.py`. Exit 0. Result: 78 of 78. Log: `docs/reviews/b7-workflow-evidence/workflow-run-78of78-binding.log`.

Focused cases in the log: unchanged project qualifies; changed raw export refused; tampered binding refused; changed manual artifact refused; held lock refused (exit 2); nested output link refused (exit 2) with nothing written outside.

## Limits

- Single lock per operation: project_lock around design, supplier and package. LockHeld and LockMalformed are exit 2.
- Binding files written atomically before their results; results carry the binding hash; package refuses missing or mismatched bindings and any changed bound output or manual artifact.
- Captured bytes: each consumed input read once; staging and digests use the same bytes.
- Container runs use the measured image identity; stage marker required before removal.
- Mask worker: 2-second caller timeout, 2-second in-process budget, 2,000,000 pair cap, 10,000 flashes, 5 MB input, 100 listed pairs.

## Not claimed

- Export settings and profile are still parsed from live files in some paths.
- review-source and review-gate in fab.py use write_text, not atomic_write.
- Supplier condition completeness (process rows), manual region-mask route, and standalone acceptance remain open.

## SHA-256 (frozen code and test)

```text
209d1c23dc1dcc5bcb2725c58087a1385657ad1b68bf6902180891b60b483e86  skills/pcb-fab-package/scripts/workflow.py
28a507e4bf9e65d2e34f4dce9e0bc2567dedeeb9be3e29fd81c67ca272eac455  tests/test_pcb_fab_workflow.py
```
