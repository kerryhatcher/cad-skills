# B7 complete correction review

Date: 2026-11-14 UTC.

All three frozen source and test hashes match `b7-workflow-complete-correction-freeze-claude.md`.
The final log records 92 passing checks and exit 0.
The workflow hash is `05ad9a5ab565d1eb0ef18d6d9a8b0e4575e869c9d9f7cb344de33811e82435d4`.
The lead measured two remaining defects on temporary projects.

## C1: a nested profile path escapes confinement

The package operation calls `profile_from_bytes` before its confinement check.
That helper writes `supplier_dir/captured/profile.yaml` without a check on the child path.
A symbolic link at `captured` therefore sends the write outside the project.
The command then reports missing design inputs and returns exit 1, but the external file remains.

`b7-complete-correction-link-probe-root.json` retains the full command and measured result.
No container ran for this case.
Pi also identified this child-path gap in design and supplier operations.

Confine the full write path before any mutation, or parse the captured profile without a scratch write.
The existing check on the operation's top-level output directory is insufficient.

## C2: package copies do not bind the published bytes

The lead prepared a temporary test project with the existing fixture helpers.
Its baseline package returned exit 0 and status `qualified`.
The manual evidence in this fixture is synthetic test data, not production evidence.

The controlled copy changes the source copper Gerber immediately before `copy2`, then restores it immediately after the copy.
The staged package receives invalid Gerber bytes.
Later checks examine the restored source and pass.
The manifest records a new hash for the invalid package copy.

Measured result:

```text
baseline_exit: 0
baseline_status: qualified
changed_copy_exit: 0
changed_copy_status: qualified
reasons: []
source_restored: true
published_injected_bytes: true
```

The source hash is `d14d20de4337b0451d2ea490811668954af973de1bedf672a723a7b69263629c`.
The published hash is `00964a242ed54123908c6971b8a9164428469d377fe2ae66a81406dcbd5e75d0`.
The retained script and result are `b7-package-copy-probe-root.py` and `b7-package-copy-probe-root.json`.
The script writes new results only in its temporary directory.

The package must compare each copied artifact with the hash from the accepted measurement binding.
Run semantic checks against the staged package artifacts, or prove that those artifacts equal the measured bytes before publication.
Do not attach a new current hash to an old passing result.
This is the existing capture and artifact-binding requirement, not a new security framework.

## Decision

The complete correction is not accepted yet. C1, C2, and C3 block publication integrity.
Keep the accepted KiCad report-key and row-15a results.

## C3: the original manual record can change without refusal

The package freshness comparison hashes `supplier_dir/manual-evidence.json` for the `manual` input.
That is the retained copy. It does not represent the current original manual record.
The supplier result does not retain the original record path for this comparison.

The lead appended one newline to the temporary project's original `out/fab/manual-record.json` after supplier measurement.
The public package command still returned exit 0, `qualified`, and an empty reason list.
The original record was restored after the probe.
`b7-manual-current-probe-root.json` retains the command and before/after hashes.

Retain the original record path with its measured hash.
Compare that current path before publication, in addition to the retained copy and referenced artifact.
The existing agreed correction explicitly includes a changed manual record after measurement.
