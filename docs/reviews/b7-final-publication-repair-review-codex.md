# B7 final publication repair review (codex-skill-dev)

Date: 2026-11-15 UTC. Scope: the frozen C1, C2, and C5 repair.
I changed no product file. I ran no broad suite.

## Freeze and source hashes

The freeze record hash is `bc6b59eac5e0694781a1987ac290a36818af08af22f851e8c182621645244543`.
All five entries in `docs/reviews/b7-workflow-evidence/c1-c2-c5-freeze.sha256` passed before and after this review.
The command `sha256sum -c docs/reviews/b7-workflow-evidence/c1-c2-c5-freeze.sha256` returned exit 0.

| File | Before review | After review |
|---|---|---|
| `skills/pcb-fab-package/scripts/workflow.py` | `ac38b636a748816a530f89f7a951296da4fd140304a66ee74e5b09261f7a48a7` | `ac38b636a748816a530f89f7a951296da4fd140304a66ee74e5b09261f7a48a7` |
| `skills/pcb-fab-package/scripts/fab.py` | `f63e4d581f9d623b6007b7162c760c347370b7d0d32298205059a2e1a05a47be` | `f63e4d581f9d623b6007b7162c760c347370b7d0d32298205059a2e1a05a47be` |
| `tests/test_pcb_fab_workflow.py` | `58b8a45f20e73907b5ca538950189e157f190676f4e67688883732d770276338` | `58b8a45f20e73907b5ca538950189e157f190676f4e67688883732d770276338` |

The accepted workflow log records 124 of 124 checks and exit 0.
Its hash is `fe9d234629587afefac82aed3a25e9c2c1305b786d67c0dabedc43b9ac38f059`.

## Accepted changes

The design, supplier, and package workflow outputs use `write_out` and `PIO.atomic_write`.
The workflow checks complete output paths before mutation.
The worker reports use a private supplier execution directory, then `write_out` publishes their bytes.
The existing directory-link regression remains in the workflow tests.
The new file-link cases cover profile, design, supplier, log, and worker-report destinations.

The supplier reads each measured design output once and compares its bytes with the design binding.
The mask and slot workers read private copies. The supplier result and binding record the measurement hashes.
The package compares copied design outputs with those measured hashes.

The package reads its result files, bindings, review record, observations, and copied artifacts through one `Reader`.
The semantic checks read private copies of the captured design files.
The manifest validator runs before the final gate.
The final gate compares the validated manifest bytes and each staged output hash and dimension.
It rejects links, missing outputs, and unexpected files.
It returns a named failure and keeps staging when a comparison fails.
The code calls `PIO.publish_dir` only after the gate returns no problems.

The author log retains focused tests for a changed staged Gerber and manifest.
Each test requires a nonzero result and no final package.
The command ran no broad suite, as the repair record requires.

## Findings

### C1: standalone drawing commands still write directly

The repair record says `drawing-facts` and `drawing` remain outside the design, supplier, and package commands.
The accepted C1 scope names drawings and all output files in the command inventory.
The two `fab.py` branches still call `Path.write_text` and `Path.write_bytes` on `--out`.
The limit therefore conflicts with the assigned scope.

I ran `uv run docs/reviews/b7-workflow-evidence/b7-codex-result-drawing-probe.py`.
The command returned exit 0. The `drawing` command returned exit 0 and preserved its symbolic link.
It changed the linked outside file from hash `e9551c7fb709ec7c6f159127183a8940635414dd0f3403f6bcd440b72340655a`.
The new PDF hash was `6dadc40cc3293ffa940446dc5a37cec5c0431d51b1fadd5687ac3b5550277a2e`.
The `drawing-facts` branch uses the same direct-write pattern, but this probe exercised `drawing` only.

### C2: the supplier result lacks an integrity check

The package reads `supplier-result.json` once. That prevents a change between its decision read and package copy.
However, the supplier binding does not hash `supplier-result.json`.
The supplier result has a binding hash, but no content hash.
The package checks its exit field. It does not check that each mandatory row agrees with that exit.

The focused probe changed one mandatory supplier row to `fail` and left the binding unchanged.
The package returned exit 0 with status `qualified`.
The published result and manifest both used hash `abd6c1b2c04e20d0e2da97a54e1a544a0ced7c363f735ac2a657e6f50fddcbb1`.
The result hash before the edit was `e829db10c66eb726da7f5c1d4426fcbbb2ac696de1bf7f12a19081696fd98721`.
The probe therefore shows that one-read capture alone does not bind the supplier decision record.
Give the supplier result a checked content hash or bind its exact bytes into the supplier binding.
Add a focused test that changes a mandatory row and requires refusal.

### C5: the final gate does not bind the current binding files

The final gate reads each current binding file and checks the output files named by that binding.
It does not compare the current binding bytes with the binding bytes captured earlier or the result's `binding_sha256`.
A binding change after the package read can replace the output hash map used at the final gate.
Add a focused change after manifest validation. The gate must reject changed binding bytes before publication.

## Acceptance boundary

The staged manifest and output gate meets the assigned C5 checks in the source and focused logs.
The complete-path writes and captured supplier design inputs also meet their focused checks.
C3, C6, C7, geometry, and report-key results remain accepted.

The standalone drawing write and supplier-result integrity findings remain open.
The final gate also needs a check on the current binding bytes.
These findings do not change the frozen source hashes above.

## Probe record

Command: `uv run docs/reviews/b7-workflow-evidence/b7-codex-result-drawing-probe.py`.
Command exit: 0. Package exit: 0. Package status: `qualified`.
The test project and outside file lived in a temporary directory.
The probe uses `test_pcb_fab_workflow.py` setup helpers. It does not run the full suite.
The controlled tests in the author log use in-process hooks. They do not prove a race with another process.
