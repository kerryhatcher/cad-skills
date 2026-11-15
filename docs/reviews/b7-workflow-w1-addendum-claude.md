# B7 workflow W1 addendum (claude-skill-dev)

Date: 2026-11-14 UTC. Addendum to `b7-workflow-w1-record-claude.md`. The frozen record and code are not changed.

## Correction

The W1 record says: "The root probe `b7-snapshot-probe-root.py` ... Its printed JSON is a fixed value." That statement is wrong.
The root probe computes its JSON from the measured staged bytes. It does not print a fixed constant.

## Evidence handling

The author rerun of the probe overwrote the original root evidence file. The lead preserved the author rerun as
`b7-snapshot-probe-author-rerun.json` and restored the original from the tool output. The probe now writes only to its
temporary directory. No further rerun is planned.

## What the probe does not show

The probe hooks `shutil.copy2`. The corrected staging no longer calls `copy2`, so the probe hook does not apply to the
corrected code. The W1 regression in the workflow test file covers the corrected behavior instead.

## Process note

Future checkpoints go to the root reviewer first. Root coordinates reviewer scope, so active edits do not invalidate
reviewer reads.
