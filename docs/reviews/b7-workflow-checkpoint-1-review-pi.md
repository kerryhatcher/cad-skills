# B7 workflow checkpoint 1 review (pi-skill-dev)

Date: 2026-11-14 UTC. Scope: `b7-workflow-checkpoint-1-claude.md`
(SHA-256 `b85c8bb852881e4bd3af9d63506ed4806fc67bcd3e835b24083bc306daf1562a`), combined with
`b7-workflow-checkpoint-1-root.md` (SHA-256
`26acd0099566515f528554a57a59e19c63b4c238a00cc1faa42022f05206d596`). My focus is the measured image use,
row 15a, stage and source preservation, and current evidence against package qualification. I did not repeat
the 65 checks.

## Hashes

The checkpoint hashes match before and after this review.

```text
517e266c6f012191ad65b3cf95b1267dd995d5161ed23794792e331f36267fb3 skills/pcb-fab-package/scripts/workflow.py
d410a64ac7c3e5477c8a4ae6c1258aff3b7f3324fca145cbb0966cb55821c255 skills/pcb-fab-package/scripts/fab.py
93d8625f46ba0fab90312a833d431a5dfe9a3e63019c7964de8fae330d73232a tests/test_pcb_fab_workflow.py
```

## Measured image use: accepted

`runtime_identity` reads the lock, inspects the mutable tag, requires the measured ID to equal the lock
digest, sets `RUN_IMAGE` to that ID, and measures the KiCad version in the image. Every `podman` call in
`design` and `supplier` runs after `runtime_identity` and uses `RUN_IMAGE`. `package` runs no container. The
design result records `runtime.image_id`. The focused regression and the 65/65 log confirm this.

## Row 15a: concrete blocker

The test and the product use the wrong severity key. The accepted requirement says to set the KiCad
violation-type severities to `error` and that a generated rule name is not the `rule_severities` key
(`b7-workflow-draft-root.md` point 4, r8 section 7.1). The measured case C key for track width is
`track_width`.

- `effective_pro` sets `severities[f"supplier_{key}"] = "error"`. That is a generated rule name, not the
  violation type. The staged project therefore does not override a source `track_width` severity. It also
  does not remove a source violation-type severity.
- `test_row_15a` sets `rule_severities.supplier_min_trace = "ignore"` at line 337. That is the generated
  rule name, not `track_width`. The source does not hide the target violation with this key.
- The test exclusion is `track_width|1000000|1000000|<nil>|<nil>`. The retained positive fixture uses
  `track_width|120025000|118000000|9024f436-90ab-541e-847d-e2efb7de6a0d|00000000-0000-0000-0000-000000000000`
  (`b7-prereq-trials-claude.md` section 10, variant I). The nil main UUID and the arbitrary point do not
  match the target marker, so the exclusion excludes nothing.
- Result: the test does not establish that the source first hides the target violation. The thin tracks may
  fail because the violation was never hidden. The six checks pass for the wrong reason.

Required correction: set the violation-type severity to `error` in the staged project, clear a source
violation-type `ignore`, and make `test_row_15a` use the retained variant I exclusion and the `track_width`
severity key. Show that the source first hides the target violation, then the staged project exposes it.

### W2: constraint names are not report types

I confirm the root W2 finding. The repair must not use all `RULE_CONSTRAINT` values as report types. The
tagged KiCad 10.0.5 `drc_item.cpp` keys are:

| Constraint | Violation and severity key |
|---|---|
| `track_width` | `track_width` |
| `clearance` | `clearance` |
| `annular_width` | `annular_width` |
| `hole_size` | `drill_out_of_range` |
| `hole_clearance` | `hole_clearance` |
| `edge_clearance` | `copper_edge_clearance` |

Use an explicit mapping for the severity settings and the report counts. Keep the constraint names for rule
generation. The current supplier loop uses `typ = RULE_CONSTRAINT[key]` and `counts.get(typ, 0)`. For
`min_drill` it looks for `hole_size` and misses `drill_out_of_range`. For `edge_keepout` it looks for
`edge_clearance` and misses `copper_edge_clearance`. Those rows can pass with active findings.

Required correction for the drill and edge rows: use `drill_out_of_range` and `copper_edge_clearance` in the
severity and count tables, and test those measured report types through the product path.

## Stage and source preservation: W1 confirmed

`stage_project` copies a file with `shutil.copy2`, then reads the source again with `sha_file(src)`. It then
returns `snapshot(project)`, which reads the source files again. A source change between the copy and the
read leaves the old bytes in the stage while the snapshot records the new bytes. I confirm this from the code
and from the root probe. The returned snapshot does not describe the staged files.

Required correction: capture the bytes one time, hash those bytes, write those bytes to the stage, and build
the snapshot from those hashes. Every later step consumes that snapshot. Compare current bytes before
publication, but do not substitute current bytes for the consumed snapshot.

## Current evidence against package qualification

- W1 blocks the snapshot claim.
- The optional `extra` snapshot argument has no caller. I confirm this from the code: `snapshot(project,
  extra=None)` and the three call sites pass no `extra`. The selected external profile and the manual record
  therefore do not enter the complete snapshot through that path.
- The package binds the profile through `manufacturing/supplier.yaml`, but it does not re-check the manual
  artifact at package time. It copies `supplier_result["manual"]["artifact_path"]` and records the current
  hash. It does not compare that hash with `supplier_result["manual"]["artifact_sha256"]`. A manual artifact
  changed after the supplier run is not caught. This is the same class as W1.
- The product writes shared result files with `write_result` (`path.write_text`). It does not call
  `project_io.project_lock` or `project_io.atomic_write`, which exist in `project_io.py`. The record does not
  yet implement the agreed raw report, binding and result publication sequence. Codex examines these binding
  and publication details.

## Combined correction scope

Keep the accepted interface. No new framework and no broad redesign.

1. Capture one snapshot. Hash and stage the same bytes. Consume that snapshot for the profile, settings,
   rules and manual evidence. Compare current bytes before publication only.
2. Set the KiCad violation-type severity to `error` in the staged supplier project. Clear a source
   violation-type `ignore`. Use an explicit constraint-to-report mapping for the severity and the counts
   (`drill_out_of_range` for `hole_size`, `copper_edge_clearance` for `edge_clearance`). Use the retained
   positive exclusion fixture in `test_row_15a` and the measured report types in the tests.
3. Call `project_lock` and `atomic_write` for shared records, and implement the raw report, binding and
   result publication sequence. Codex owns this item.

## Verdict

The measured image use is accepted. Row 15a is not accepted: the severity key, the exclusion, and the
constraint-to-report mapping do not match the retained fixture and the accepted requirement. The snapshot
claim is blocked by W1 and by the uncalled `extra` path. I confirm the root W1 and W2 findings. This
checkpoint is not accepted yet. No full qualification claim and no 65-check repeat.
