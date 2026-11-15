# B7 caller and docstring replacement review (pi-skill-dev)

Date: 2026-11-14 UTC. Scope: `b7-geometry-caller-replacement-checkpoint-claude.md`
(SHA-256 `af5b0e236480bc18990f0422072697990d33548f42de17d2f3a134327ac3d0bf`). The scoped items are the
docstring correction, the caller file bindings, and the workflow mask-path regression. Full B7/B8 acceptance
stays separate and outside this review.

## Hash confirmation

The replacement record lists five code and test hashes. I measured each one. All match.

```text
dd5daa3ee98e996c4a846cc0551c9eac40ee28d05851a72f37ba67144f4ea442 tests/test_pcb_fab_workflow.py
d6d13ab732190b7be0a029fb1f3ce27c81506fd8f94c83e1989cffe2cbc2adeb skills/pcb-fab-package/scripts/fab.py
bca595484e0298362d5173a5b94ae37360855a3ade8b3e114188c68c412adbb1 skills/pcb-fab-package/scripts/workflow.py
bd37508707cc93fd9a251503de4619a3abfece8986fd9052da242b57df598f2a skills/pcb-fab-package/scripts/inspect_mask.py
26b765635fd666577fa34dbf4a5ee0d8ad546b7188e82a385c66c791922954d2 tests/test_pcb_fab_package.py
```

The four unchanged geometry modules keep the earlier hashes: `macro_defs.py` `c91d475f…`, `export_inspect.py`
`5be010bf…`, `inspect_slots.py` `9b543eb2…`, `board_inventory_slots.py` `ed8a9d74…`. The nine-file set is the
five above plus these four.

The three retained logs match `b7-workflow-evidence/logs.sha256`:

```text
3bf248ff3811e3a6a58d37fa4414289e53a85079bc9e9a995974b8ca84aa13a0 workflow-run-51of51.log
9cb81f80e54c2e7b1459284f6128c8d701a7717d26f1873473edaea1935a9988 workflow-run-48of50-failed.log
6013d51e9422728f12b74a02ea23345ddd13e9970ca950674305a9dabae1ee88 workflow-run-interrupted-recursive.log
```

## Narrow diff

1. Docstring correction. `inspect_mask.py` now says "with a radius that is positive and finite; the radius has
   no limit relative to the core side". The stale "inside the measured range" text is gone. The code is
   unchanged from the accepted core-distance behaviour.
2. Caller file bindings. The record now holds `fab.py` (`d6d13ab7…`) and `workflow.py` (`bca59548…`). Both
   match the caller files I measured in the final geometry review. No caller code changed in this step.
3. Workflow mask-path regression. The new `tests/test_pcb_fab_workflow.py` (`dd5daa3e…`) checks both mask
   rows at line 169: "the supplier mask path writes both mask rows (regression for the returncode defect)".
   `workflow.py` compares the `run_mask_worker` integer result directly (`rc_mask == 2`, `rc_bottom == 2`).

## Retained records

- The 51/51 log holds the corrected run. It shows the mask-path regression pass, "design runs before the
  quantity test", "the supplier result stops on a quantity of 5", and "source rules are preserved before the
  generated rules".
- The 48/50 log stays as history. Its two failures are "the supplier result stops on a quantity of 5 …
  : 3" and "source rules are preserved before the generated rules: missing". Both follow from the missing
  design prerequisite. The corrected test adds the design run first. The difference between the two logs is
  the design-first step, as the checkpoint states.
- The interrupted recursive log stays as history.

## Scoped acceptance

I accept the scoped replacement. The three scoped items are present, the hashes are exact, and the diff is
narrow. No concrete blocker.

## Minor notes, not blockers

- The 51/51 log has no final exit line. The checkpoint states that the background task reported exit 0. The
  48/50 log has an explicit "exit 1". A short exit line in the passing log would make the record
  self-contained.
- The new docstring line uses a semicolon ("finite; the radius"). AGENTS.md rule 8.1 forbids semicolons.
  Replace it with a full stop.

Full B7/B8 acceptance remains incomplete and outside this review.

## Fresh-report symlink defect (root finding)

I agree. `run_mask_worker` checks `rep.exists()` only. `Path.exists()` follows the link. A dangling symlink
therefore returns false. The worker then writes through the link and creates the target. The run returns
exit 0 with an unbound report. The fresh-report-path rule fails.

Agreed correction:

- Refuse the report path when `rep.exists()` or `rep.is_symlink()` is true. `os.path.lexists(rep)` gives the
  same result in one call. Both forms are correct.
- Keep the link and the absent target as evidence. Do not remove them.
- Add a focused regression: a dangling report symlink returns exit 2 with the fresh-report message, and the
  link and the target stay absent.
- Replace the new docstring semicolon with a period.

A symlinked parent directory in the report path is a separate path-policy item under "escaping links". It is
not necessary for this focused fix. I did not repeat the full suite.
