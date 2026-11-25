# B10 completion review scope

Date: 2026-11-15 UTC. Author: skill-dev-lead.

The 42-file batch is ready for review. It is not yet complete against interface section 14.
Keep these files frozen until both reports are complete.

## Findings from the lead's code reading

1. `package.py` calls `validate_record` for record structure. It does not run the package checks that bind evidence inputs and outputs.
   The captured inputs omit `export_settings`, `board_interface` and `toolchain`. Passed fabrication checks need these roles.
   An unqualified status does not remove checks on listed evidence.
2. `erc_pending`, `parity_pending` and `profile_evidence_pending` always return pending. The accepted interface specifies executable checks when inputs exist.
   A missing input can produce pending. It cannot replace the implementation for a supplied input.
3. `export_inventory` receives its expected list from the outputs that the export loop found. It does not derive that list from export settings.
   `drill_split` examines header text only. It does not compare hole coordinates, counts or plating against an independent inventory.
4. `export.py` selects a mutable image tag and exports only captured board bytes. It does not bind the toolchain, project settings or export settings.
5. `snap.check_unchanged()` runs before staged writes. A source change during those writes can pass the later staged-byte gate.
   Repeat source freshness immediately before publication, after staged validation.
6. Examine assembly evidence completeness. A test-record check must compare all declared limits and hand-install steps with captured inputs.
   An empty item list must not pass when the board declares necessary test steps.
   The assembly drawing must express the selected variant and DNP marks, as the accepted interface states.

These points restore the accepted scope. They do not add features or permit a supplier qualification claim.
The neutral and Sierra draft behavior stays accepted.

Both reviewers must examine these points and report concrete defects against the frozen bytes.
The lead will combine the reports into one correction release. Do not start another implementation batch before that release.
