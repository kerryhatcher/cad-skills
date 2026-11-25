# B7 final publication repair

Date: 2026-11-15 UTC.
Basis: `b7-complete-correction-freeze-review-codex.md` and `b7-complete-correction-freeze-review-pi.md`.
Both reviewers agree on the defects and corrections below. Root accepts this repair scope.
Claude can change the frozen workflow, callers, and focused tests for this repair.
Keep the old freeze as history. Do not change accepted geometry algorithms.

## C1: complete destination paths

Use the existing confinement and `PIO.atomic_write` helpers for all output file writes in the command inventory.
Include profile scratch files, logs, copied reports, exported files, manual evidence, drawings, and package files.
Do not treat a directory check as a file check.
For external workers, write into a fresh private execution directory, then capture the output and publish it with the helper.
Keep worker geometry code unchanged when the caller can supply this boundary.
Refuse preexisting symbolic links at complete destinations before mutation.
Add focused cases for a profile file, design output, supplier output, log, and worker report.
Keep the directory-link case. Confirm that links and outside targets remain unchanged on refusal.

## C2: one byte set for decisions and copies

Capture result files, bindings, review records, observations, and all copied artifacts once per operation.
Use those captured bytes for semantic decisions and package copies. Use their exact hashes.
Do not compute a new hash from a second read and give it an earlier pass.
Keep explicit current-source reads only for freshness comparisons.

Before supplier measurements, capture each consumed design output and compare its hash with the accepted design binding.
This includes inventory, drills, and both mask Gerbers. Refuse a mismatch before the dependent measurement.
Use these bytes in the worker execution directory.
Bind the measurement inputs to those hashes. Compare them with the corresponding staged package artifacts.
Add a controlled result-file change and a transient supplier-input change regression.

## C5: validated bytes at publication

Record the validated staged manifest bytes and the complete output inventory.
Immediately before `PIO.publish_dir`, compare the staged manifest and each output with the validated hashes and dimensions in bytes.
Include generated evidence and reports. Reject links, missing outputs, and unexpected files that the publication would include.
Keep the source freshness gate.
If this final gate fails, do not rename the staging directory into the final destination.
Retain a named failure and the staging path. Do not claim rollback after a successful rename.
Add controlled changes to a staged Gerber and the staged manifest after validation.
The tests must show a nonzero result and an absent final package.

## Acceptance boundary

C3, C6, and C7 remain accepted. Preserve their behavior.
Run the affected workflow suite after the correction. Run another suite only if its files or behavior change.
Freeze the complete correction with a repository record, source hashes, retained commands, exits, and test logs.
Send the freeze to root. Both reviewers will examine the same stable files.
Supplier condition completeness, manual region-mask support, setup retrieval, and standalone release remain later work.
