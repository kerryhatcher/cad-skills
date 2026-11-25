# B11 completion review: Codex

Date: 2026-11-15. Reviewer: codex-mechanical-dev.

Scope: the 26 files in `docs/reviews/mechanical/b11-completion-batch.sha256`, the retained run evidence, interface revision 8, and the lead resolutions.

**Decision: not accepted.** The positive flow works. The batch still violates accepted hole, cavity, release, and path rules. The lead resolutions are clear. The frozen implementation does not meet them.

## Manifest and focused runs

The manifest SHA-256 starts with `f6d69c0384768959`. `sha256sum -c` reports 26 matching files.

I ran these suites:

- `uv run tests/test_mechanical.py`: 55 tests pass.
- `uv run tests/test_mechanical_fit.py`: 38 tests pass.
- `uv run tests/test_pcb_design.py`: 43 reported checks pass, and the command exited 0.

I generated a fresh fixture and ran `mechanical.py export`, `fit`, and `release`. All three commands exited 0. The report gave geometry and fit status `pass`. `mechanical.py check` and the accepted board validator also passed.

The direct `mechanical.py` flow works. `pcb.py mechanical --help` exposes only `check` and `readiness`. It does not expose `export`, `fit`, or `release`.

## Required corrections

### R1. Refuse slots and validate the full excluded-hole record

The accepted interface requires a refusal for a slot, an oval, or another unsupported drill class. The Excellon reader accepts only a full line that matches `X<num>Y<num>`. It silently skips a routed `G85` hit.

Pi added an oval to a fresh fixture and measured a real KiCad line in the Excellon file. The parser returned three round hits for a board with four drill objects. It did not refuse or name the slot. My focused parser probe also added a `G85` line to the retained drill file. The parser still returned only the three round hits.

The accepted interface also requires each `excluded_through_holes` entry to have a position, diameter, and reason. `check_fixture` does not examine that field. I added an excluded hole without a reason to a temporary fixture. `M.check_fixture` accepted it.

`closed_hole_set` only rejects found holes that are absent from the allowed list. It does not compare each output with the complete expected set. The fit also passes only `src["holes"]` to C02, C03, and C04. It does not add excluded holes to those expected sets.

Refuse each unsupported drill class with its object name. Validate the excluded-hole fields and reason. Compare the STEP, DXF, and both drill outputs with the complete declared hole set.

### R2. Export separate PTH and NPTH files

The lead resolution requires `--excellon-separate-th`, `board-PTH.drl`, and `board-NPTH.drl`. The frozen command omits that switch. It creates one mixed file and assigns it the `drill_pth` role.

The retained Excellon header says `MixedPlating`. The release record contains no `drill_npth` output. The release helper does not require each closed role to appear.

Use the measured file names from the local image. Bind each file to its matching accepted role. Reject a missing role.

### R3. Apply the outward cavity and the declared connector body length

The lead resolution defines the cavity as the board outline offset outward by `clearance_mm`, with the chamfer. A point on the board edge lies in that cavity. No mating-edge exemption applies.

The frozen `c09_lateral` instead tests distance from an inward keepout at the board edge. It also exempts the nearest connector edge. The reference records both rules as unreviewed. This behavior conflicts with the lead resolution and with the accepted C09 cavity rule.

The frozen `proxy_plan` uses `insertion_depth_mm` as connector body length. The component evidence has no `body_length_mm`. The lead resolution requires a separate project-authored `body_length_mm: 4.0`. The body extends inward from its mating face, opposite the transformed insertion vector, with zero overhang. This proxy makes no datasheet or detailed-fit claim.

Use outward cavity containment with the fixed 0.01 mm tolerance and no exemption. Use the declared body length and placement rule. The positive evidence from the frozen run is historical after these changes.

### R4. Refuse a missing required component

The accepted cases require a missing part to fail by name. `check_fixture` does not compare the component evidence records with the source `parts` and connector frames.

I removed B1 from a temporary fixture before export. The full export and fit then reported geometry and fit status `pass`. C08 also passed with no B1 result. A missing required part therefore passes the flow.

Require a component record and comparison result for each source part and connector frame. Name each missing reference. Do not treat an empty part set as a pass.

### R5. Add the accepted public command route

The lead resolution requires thin dispatch for `pcb.py mechanical export`, `fit`, and `release`. The frozen route exposes only `check` and `readiness`.

Add the three accepted actions as thin calls to the local mechanical module. Keep the direct module commands if the reference documents them.

### R6. Bind and consume captured bytes

`capture` stores only hashes and byte counts. `run_export` then copies the live board file. It does not export the captured board bytes. It inspects the image ID once, then runs the mutable image reference.

`run_fit` hashes each output, then `evaluate_project` reopens the live project files. No final input freshness check runs before the report write. `run_release` reads the inputs at the start and does not make a final freshness read before publication.

The lead resolution requires the flow to consume captured bytes or private copies of those bytes. It also requires the exporter to run the measured image ID. Use those bytes for each calculation. Make the final freshness and output-integrity gate before publication.

### R7. Confine paths from the export record

`run_fit` uses `export_dir / rel` for each path from `export.json`. It does not pass the path through `project_io.confine`.

I added an absolute path to a temporary export record. The path named a file outside the project. `run_fit` read it and returned a complete pass. This is a measured path escape.

Confine each record path before any read or write. Apply this rule in fit and release. Keep the accepted closed path and role lists.

### R8. Recompute report status before release

`run_release` trusts `report["status"]`. It does not recompute comparison completeness or status from `report["results"]`.

I changed a temporary report to contain no results and a passing status. `run_release` published the release. This is a measured release of an empty report.

Recompute the required results and status. Reject missing IDs, duplicate IDs, failed results, and status values that do not match the results. Check each connector result separately. The current `overall_status` uses a dictionary by comparison ID, so later C06 or C07 results can replace earlier results for another connector.

### R9. Match the revision 8 release record and mismatch order

The accepted record requires explicit electrical inputs, interface, evidence, fixture source, settings, board hash, toolchain image ID, output paths, roles, hashes, and byte counts. The frozen record stores a five-file `inputs` map. It has no `electrical_inputs` or `toolchain_image_id` field. Its output entries omit byte counts. It gives the mixed drill file the `drill_pth` role and omits `drill_npth`.

`first_stale` compares only the `CAPTURED` list. It does not use the accepted mismatch order. `release_first_mismatch` exists but the release flow does not call it. The release also lacks the accepted `first_mismatch` field.

Write the explicit revision 8 fields. Compare the accepted inputs in the accepted order. Bind the exact output byte counts and both separate drill files.

## Lead resolutions

I agree with the lead resolutions:

- Export `board-PTH.drl` and `board-NPTH.drl` with `--excellon-separate-th`.
- Define the cavity as the outline offset outward by clearance, with the chamfer and no edge exemption.
- Declare `body_length_mm: 4.0` separately from insertion depth. Place the body inward from the mating face with zero overhang.
- Keep the positive evidence as historical and rerun the corrected cases.
- Consume captured bytes or private copies. Run the measured image ID.
- Keep the revision 8 release fields and mismatch order. Confine paths and recompute status before release.
- Add thin export, fit, and release actions under `pcb.py mechanical`.

Claude described the cavity as “inward-cavity.” That wording conflicts with the lead resolution. The lead's outward-offset rule is precise and removes the conflict. The frozen code still implements the inward rule.

## Limits of this review

I changed no batch file. The focused probes used temporary fixture copies. The new review file is outside the 26-entry manifest.

The positive flow passes, but the negative and integrity probes above show that this batch cannot publish a release that meets revision 8. The next review must use one new frozen batch after the lead releases these files.
