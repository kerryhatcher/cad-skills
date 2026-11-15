# B5 native checkpoint correction review: Codex

Date: 2026-11-14.

**Decision: correction accepted for this checkpoint**

I accept the agreed A–E and I1–I3 corrections within this checkpoint's stated limits. No blocking correction remains in that scope. This is not final B5 acceptance.

Manifest: `docs/reviews/b5-native-files-v2.sha256`.

Manifest SHA-256: `6a755b367a709ecbdf3d4c59403de5270bac5f8ac4a22da9b39372179cbd450a`.

All 199 entries passed before and after review. The manifest hash remained unchanged. U3 files share this manifest, but this review does not assess U3 support.

**Measured correction results**

`uv run tests/test_trial_identity.py` passed: 17/17, exit 0.

| Item | Result |
|---|---|
| A | The supported runner returns the comparison result. The exploratory runner has an explicit kind and also returns that result. Existing run directories receive no replacement. |
| B | Nine retained DRC records include full findings, exit codes, and source hashes. I measured agreement between those records, their indexes, and their board and schematic bytes. |
| C | Focused tests exercise reading, changes, and named removals for the saved arc, via, and zone fixture. This establishes reader coverage only. |
| D | The expectation generator now writes the replace-off empty expectation. The runner accepts an explicit expected file. The corrected replace-off comparison is equal. |
| E | The three invalid attempts have explicit markers. Their original result bytes remain. |
| I1 | Added-footprint differences include the value. C2's expected value comes from baseline C1. The wrong-value negative test fails as intended. |
| I2 | Duplicate expected differences give `identity.duplicate_expectation` and exit 2. |
| I3 | Duplicate and missing UUID tests give explicit input errors. A duplicate segment no longer hides another segment. |

I independently regenerated all eight corrected expectation files from the baseline only. All match. The generator does not read the after-boards.

I recomputed the snapshots and comparisons for all 12 saved boards. They match the stored snapshots and corrected comparison files. The index board hashes also match.

The six supported gate observations remain equal. The replace-off option experiment has its correct empty expectation. The relink-on rename probe remains different. The three invalid attempts retain their explicit invalid status.

I tested the shell runner with stubbed commands and comparison results. A supported pass returned 0. A supported failure returned 1. An exploratory failure also returned 1 and recorded its explicit expected-file name. No GUI ran in that test.

**Retained diagnostics and history**

All nine DRC runs record exit 5. The six supported gate observations have empty parity sections. The replace-off experiment retains two parity findings. The relink-on rename probe retains one extra-footprint finding.

These boards still have violations and unconnected items. They remain phase-A evidence, not clean reference boards.

I compared the original 67-entry checkpoint manifest with the current files. Only the four authorized source/test files differ: `identity.py`, `gate_expect.py`, `trial_env.sh`, and `test_trial_identity.py`. The other 63 entries retain their original hashes. Historical boards, snapshots, comparisons, and expectations remain unchanged.

**Limits of this acceptance**

The via/zone/arc fixture passed through KiCad upgrade, not a GUI update. Its tests establish that the reader detects those objects and their changes. They do not establish preservation through an update.

Repeat gates, remaining source paths and limit probes, the final clean board, exports, analytical simulation and negative case, and the draft package remain later B5 evidence. This review makes no U3 support decision.

I did not run a new trial, repeat a GUI operation, rebuild or pull an image, or run unrelated suites. I changed only this report.
