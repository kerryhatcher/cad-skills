# B6 correction review by the lead

Date: 2026-11-14. Manifest: `b6-correction-files.sha256`, 210 entries, hash `ab6a32f676fb66ae28ccf7d1ff47e619e4f83506bf6210bc3fe7fd98e16e4b3d`.

All 210 entries matched before this review. No implementation file changed during the lead's probes.

The independent readiness probes now return exit 1 for insufficient manual coverage and a missing automatic expectation file. The manual probe includes the new `prior_interface_sha256: null` field. It exercises coverage, not only rejection of an obsolete record shape.

The assertion parser now rejects duplicate keys, a final newline in the measurement identifier, and an excessive integer. Each gives `assertion.malformed`, exit 1. The earlier uncaught exception is absent.

Evidence: `b6-correction-readiness-root.json` and `b6-correction-assertions-root.json`. The local structural STE linter reports zero findings for the new skill documents. The standalone index now retains commands, exits, isolated paths, and the simulation raw log.

Two items still prevent final acceptance:

1. Pi reproduced the native simulation prerequisite defect. Version measurement must not call missing KiCad tools for an ngspice-only operation. Report publication uses the same measurement helper and needs the same correction.
2. The template history file appears in the manifest, but `.gitignore` excludes it under `out/`. Remove the unnecessary template history and test initialization without it, or add an exact source exception. Do not broadly include generated output directories.

Both reviewers agree to these narrow corrections. The accepted interface, parser, staging, and prose corrections remain valid within this review scope. Final acceptance waits for replacement hashes and the focused runtime and package tests.
