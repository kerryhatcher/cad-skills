# B11 interface review: Codex

Date: 2026-11-15. Reviewer: codex-mechanical-dev.

Subject: `docs/reviews/mechanical/b11-interface-claude.md`, revision 3. SHA-256: `76c38cbca682800482e61607bbe208eb9eef51ece1772c726d457b3f0b22b115`.

## Decision

The proposal follows the lead decisions for the transform, release record, export origin, and `pcb.py` ownership. Keep its overall design. Revision 3 needs the corrections below before review agreement.

I agree with Pi's review in `b11-interface-review-claude-pi.md`. I add the input-integrity, geometry, and readiness cases below.

## Required corrections

1. Use the lead paths. Keep `mechanical.py` and `mechanical_fit.py`. Put the fixture in `skills/pcb-design/templates/mech-fit-a/`. Include `board.yaml`, the source generator, the interface, evidence, enclosure parameters, and export settings.
2. State the board outline start `(100, 100)`. Keep it separate from the anchor `(103.7, 118.2)`. Keep `origin_mm` as the target origin. Do not add a target origin to `extensions.transform`.
3. Keep only the six allowed fields in each `connector_frames` item. Put connector width, height, envelope, insertion vector, and insertion volume in the component evidence or fixture source. Define the connector angle datum and positive direction.
4. Add the required fixture `board.yaml`. Set its dimensions to 60 by 36 by 1.6 mm. Set its coordinate axes to right and up. Match `release_revision` with the interface `board_revision`.
5. Record the full export switches. Set DXF units to millimeters and state the contour setting. Disable extra STEP pad thickness and soldermask. Record variant behavior and the settings hash.
6. Export DXF outline and hole geometry. Add a plated hole while keeping both unequal nonplated holes. Bind drill files by role and hash if C04 reads them.
7. Read the drill/place origin from the source board. Compare it with the anchor. Measure and freeze the exporter frame from the asymmetric geometry. Do not derive a new transform for each input. Measure the STEP Z datum from the board body.
8. Define `release_id` and `electrical_release_id` in named input records. Use the accepted canonical-hash helper. Keep canonical record hashes separate from exact file hashes. Define a closed role list for all outputs.
9. Name both dimension-owner records. Compare the electrical interface owner with the mechanical fixture owner. Define the enclosure cavity polygon and lateral offset. Keep lateral clearance separate from top and bottom limits.
10. Keep the first-trial tolerances fixed. Record export repeatability. Do not widen a failed tolerance without review from both reviewers and the lead.
11. Mark all fault-injection board variants as test-only. Refuse release output when a test variant changes the board hash.
12. Include narrow `pcb.py` dispatch and readiness wiring. Keep existing interface behavior unchanged. Test each new route.
13. Reuse the project lock and confined-path helpers. Capture input bytes, write reports atomically, and make a final freshness check before publication. Bind the report to its input hashes and result.
14. Compare outline geometry within tolerance without depending on vertex order or a selected start vertex. Add a same-geometry, different-order case. Do not use best-fit alignment to hide a mirror or axis error.
15. Define collision membership for C07. Exclude the connector's own proxy from its insertion volume. Name any other solid that intersects the volume.
16. Give C10 separate geometry and evidence statuses. An unconfirmed height must not turn a geometry pass into a detailed-fit claim.

## Acceptance additions

- The source board's auxiliary origin equals the declared anchor. A mismatch names the file and action.
- A fixture with incorrect `board.yaml` dimensions or revision fails with a named finding.
- A connector item with an extra field fails interface validation.
- A DXF with inch units, omitted holes, or an unset contour option fails the settings or geometry check.
- A STEP with extra pad thickness or soldermask fails the Z extent check.
- A plated hole appears in the DXF and in the plated drill output.
- Reordered DXF vertices with identical geometry pass. A mirrored outline fails.
- A test variant cannot write a release record.
- Input changes during export stop the final freshness check. The report names the changed input.
- A connector does not collide with its own insertion volume. Another part in that volume fails with its reference.
- Readiness reports the mechanical route and its CadQuery dependency. Existing routes keep their current result.

## Scope

No product file changed in this review. The frozen proposal is not an implementation acceptance. Review the next consolidated revision against these corrections and the lead decision record.

## Review of consolidated revision 6

Reviewed snapshot SHA-256: `ffb091ed25707677c93f8072cbcbdcf401dd2594c37e667897c352f507d1273d`.

Decision: I agree with the design after the corrections below. Do not accept this snapshot yet. It still conflicts with the lead thickness addendum and leaves unclear collision and status rules.

1. Replace the open Q8 text with the lead addendum. The imported STEP body has one valid substrate solid from Z 0 to 1.51 mm. The text span 1.556 mm includes points outside that solid. Label it as invalid for thickness. C05 compares the imported solid with the independent `fixture-source.json` stackup. C05s compares the declared layer sum with total thickness. Do not leave Q8 open after the lead decision.
2. Keep the finished-board envelope for enclosure clearance. Bind its stackup source in the release record. Use the finished-board envelope for component and enclosure clearance. Use the substrate solid for C05 only.
3. Complete Q7 with connector vectors. The trial reports pad offsets for top and bottom footprints. Add the local insertion vector, measured target vector for CN1 and CN2, and the resulting rotation and side rule. Keep the trial as a gate before acceptance tests.
4. Exclude the CN1 proxy from its own insertion-volume collision set. State that C07 tests other solids only. Add a case where the CN1 proxy overlaps its insertion box without a collision finding.
5. Clarify T1 status. Geometry comparisons can pass while evidence returns `unconfirmed`. State separate geometry and fit statuses. Do not call C01 to C12 all `pass` when C10 returns `unconfirmed`.
6. State `--board-only` in the STEP settings for `board.step`, or name the exact component switches that give the same board-only result. The settings record must identify the exact export command.
7. Replace T46 and the open Q8 note with the corrected solid result. Do not describe 1.556 mm as a STEP body span.

After these edits, I agree with the combined interface. Pi's final agreement and the lead addendum support this scope. No product file changed.

## Review of Q7 in revision 8

Reviewed snapshot SHA-256: `70733762d1d7d5814aa0b1531b891c0f221b15f6b99aecf455b4970061e86f3d`.

Decision: the CN1 and CN2 insertion vectors at local `(1, 0)` agree with the measured frame. I do not agree with the angle claims for the asymmetric vector yet.

For local vector `(2.0, 0.5)` at source angle `+30°`, the measured board vector is `(1.982, -0.567)`. The contract vector is `(1.982, +0.567)`. Its angle is `atan2(0.567, 1.982)`, or about `15.96°`. It is not `30°`.

Apply this transform to each local vector: `v_target = (v_board.x, -v_board.y)`, where `v_board = [[cos θ, sin θ], [-sin θ, cos θ]] · v_local`. Then derive the target angle with `atan2(v_target.y, v_target.x)`. State that the target angle equals the source angle only when the local vector points along local `+x`. Correct the asymmetric rows in the table, or remove their angle values. Keep the CN1 and CN2 local and target vectors.

The proposed `placed-file` condition handles the file-stored frame. Keep the refusal for undeclared or unsupported `pad_frame` values. Do not use edit history as a test input.

The arithmetic correction resolves the Q7 objection in this snapshot. The final review below records two remaining text conflicts. No product file changed.

## Final review of the corrected Q7 snapshot

Reviewed snapshot SHA-256: `295239507c9a2f12b171049209941862d19d2f6ec08c995f0923332e507fc47e`.

The Q7 arithmetic now agrees. The asymmetric vector has target `(1.982, 0.567)` and angle `15.96°`. The file-frame limit also states that the file does not expose editor history.

Two conflicting statements remain:

1. Section 5 says to mirror the target vector for the side. Section 9.3 says the side does not add a second mirror for file-stored footprints. Replace the section 5 sentence with the measured frame transform in section 9.3.
2. Section 10 lists Q8 under “Open for both reviewers,” then lists Q8 as resolved. Remove the stale open item. The lead addendum resolves Q8.

I do not agree with this snapshot until these two statements agree with the reviewed rules. After correction, I agree with revision 8. No product file changed.

## Review of the final revision 8 snapshot

Reviewed snapshot SHA-256: `5292c61521ff089b1735b45107c04366adc1f310da8512b0cc0be68302643eed`.

The explicit matrices and Q7 vectors agree. Two text conflicts remain in this snapshot:

1. Section 5 says to mirror the target vector for the side. Section 9.3 says that the side does not add a second mirror for file-stored footprints. Use the measured matrix rule in both sections.
2. Section 10 lists Q8 as open, then lists Q8 as resolved. Remove the stale open item. The lead addendum resolves Q8.

I do not agree with this snapshot until these conflicts are corrected. No product file changed.

## Final agreement

I agree with B11 consolidated interface revision 8 at SHA-256 `5a0b4850aa57c11973560ca2551ead734b7fcfd3cc70a168d8ec3f25495966f5`.

The target vector rule uses the measured matrices. The target angle comes from `atan2` of the transformed vector. The asymmetric vector gives `(1.982, 0.567)` and `15.96°`. The document also separates file-stored geometry from an unflipped library frame. It does not claim to detect editor history.

The section 10 heading now marks Q6, Q7, and Q8 as resolved. Pi's review covers the same transform rule. The lead can accept this consolidated interface. No product file changed.
