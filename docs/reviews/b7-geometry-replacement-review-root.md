# B7 geometry replacement review

Date: 2026-11-14 UTC. Scope: the root G1 and G2 regressions.

The inspector hash stayed `7d0e6592dcd504e662a4944107367f948b7833caa205d64e73d4706e479f1192` before and after the probes.
The [retained results](b7-geometry-replacement-probes-root.json) show both corrections.

The inline and whitespace macro cases now refuse with exit 2.
The controlled-change case reports the hash of the bytes that supplied the geometry.
It no longer identifies the later, failing file as the measured input.
The workflow caller must still compare the snapshot hash with the current artifact before publication.

G1 and G2 are accepted at this scope. I did not repeat the full test suite.
Both reviewers examine the complete six-file replacement.

The time limit currently uses cooperative checkpoints. A parser call must return before its elapsed-time check runs.
The review must distinguish that behavior from a hard timeout of the complete operation.
No probe in this record establishes a time overrun.
