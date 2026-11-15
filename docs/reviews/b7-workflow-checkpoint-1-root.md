# B7 workflow checkpoint 1 review

Date: 2026-11-14 UTC.

The reviewed `workflow.py` hash is `517e266c6f012191ad65b3cf95b1267dd995d5161ed23794792e331f36267fb3`.
The scope is the runtime, snapshots, and publication checkpoint.
Supplier condition completeness remains separate.

## W1: the snapshot can name different bytes

`stage_project` copies a source file, then reads that source again for its hash.
After all copies, `snapshot` reads the source files again.
Thus, the returned snapshot does not necessarily describe the staged files.

The controlled probe changes the temporary PCB source immediately after `copy2` returns.
The staged file keeps the old bytes. The returned snapshot contains the new source hash.
The later source comparison passes because the source keeps the new bytes.

Measured result:

```text
before_equals_after: true
recorded_hash_matches_staged_bytes: false
```

The retained probe is `b7-snapshot-probe-root.py`.
Run it with `uv run docs/reviews/b7-snapshot-probe-root.py`.
Its result is `b7-snapshot-probe-root.json`.
The probe uses temporary files and does not run KiCad or claim a qualified package result.

An author rerun replaced the retained JSON with a result from a later module.
The lead kept that result as `b7-snapshot-probe-author-rerun.json` and restored the original measured result from the tool output.
The probe now writes new results only in its temporary directory.
The copy hook no longer applies after the staging repair. A new probe must act on the corrected capture step.

The correction must hash and stage the same captured bytes.
All operations must consume that snapshot, including the selected profile, settings, rules, and manual evidence.
Compare current source bytes before publication, but do not substitute current bytes for the consumed snapshot.
This restores the accepted input-binding rule.

## Other scope checks

The source includes a fixed path list, but the optional `extra` snapshot argument has no caller.
The selected external profile and manual record therefore do not enter this complete snapshot through that mechanism.
The product still writes shared result files directly and has no call to `project_lock` or `atomic_write`.
The record does not yet implement the agreed raw report, binding, and result publication sequence.
Codex examines these binding and publication details. Pi examines runtime and supplier-rule behavior.

## W2: separate constraint names from report types

The severity repair must not use all `RULE_CONSTRAINT` values as report types.
KiCad 10.0.5 uses different names for two relevant findings.
The tagged [DRC item source](https://raw.githubusercontent.com/KiCad/kicad-source-mirror/10.0.5/pcbnew/drc/drc_item.cpp) defines these settings keys:

| Constraint | Violation and severity key |
|---|---|
| `track_width` | `track_width` |
| `clearance` | `clearance` |
| `annular_width` | `annular_width` |
| `hole_size` | `drill_out_of_range` |
| `hole_clearance` | `hole_clearance` |
| `edge_clearance` | `copper_edge_clearance` |

Use an explicit mapping for severity settings and report counts.
Keep the constraint names for rule generation.
The current supplier loop counts findings by constraint name, which misses the drill and edge report types.
Tests must use the measured KiCad report types. The declared board-boundary tests can establish that behavior.

## Decision

This checkpoint is not accepted yet. W1 blocks its snapshot claim.
Keep the correction within the accepted runtime, evidence, and publication interface.
