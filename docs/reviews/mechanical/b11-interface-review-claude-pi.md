# B11 interface review: Pi (Claude revision 8)

Date: 2026-11-15. Reviewer: pi-mechanical-dev, pane w1P:pE.

Subject: `docs/reviews/mechanical/b11-interface-claude.md`, final revision 8 snapshot `5a0b4850aa57c11973560ca2551ead734b7fcfd3cc70a168d8ec3f25495966f5`, with the measured frame and thickness addendum in `b11-decisions-root.md`.

This review covers the final revision 8 snapshot. Earlier sections record the review history from revision 6 through the Q7 corrections.

## Decision: final explicit agreement

All corrections O1 to O9 are applied. The addendum approves Q7 and Q8 and adds the measured solid rule and the finished-board envelope rule. I give final explicit agreement to the consolidated interface on snapshot `5a0b4850aa57c11973560ca2551ead734b7fcfd3cc70a168d8ec3f25495966f5`.

Codex gives final agreement on the same hash. The lead accepted this snapshot on 2026-11-15. Product implementation proceeds in `work/mechanical`. No product file changed.

No further paper revision is expected unless a measured conflict changes the interface. I will examine the frozen implementation batches and independent results.

## 1. Corrections resolved

| Item | State in the corrected revision 6 |
|---|---|
| O1 electrical owners | Resolved. The electrical owners come from `board-interface.json` `dimension_owners`. `board.yaml` holds no owner field. T47 covers the validator failure. |
| O2 excluded-hole name | Resolved. `extensions.excluded_through_holes`. `mechanical.py` examines each entry. T49 covers it. |
| O3 through-hole set | Resolved. `CN1` is frame-only. The fixture has `H1`, `H2`, `H3`. The exclusion list is empty. C02d count 3 is correct. T48 covers it. |
| O4 `core_mm` | Resolved. `core_mm` comes from the fixture stackup and the fixture stackup trial. T50 covers it. |
| O5 fixture-source hash | Resolved. The record names `fixture_source_sha256`. The stale order uses the same name. |
| O6 C05s sum | Resolved. C05s states the five-term sum against `thickness_mm`. |

## 2. Addendum folded

| Addendum item | Effect on the interface |
|---|---|
| Q8 approved | The independent explicit fixture stackup is the authority. C05 compares the imported substrate solid with the fixture `core_mm`. C05s compares the declared layer sum with the interface total. |
| Expected core | `core_mm` must not come from the tested output. It comes from the fixture stackup record. |
| C05 measured solid | C05 uses the imported STEP solid, not the text control points. The CadQuery probe holds one valid solid with Z `0..1.51`. |
| Finished-board envelope | The enclosure clearance compares a labelled finished-board envelope, not the substrate-only solid. The envelope binds its stackup source and states its Z origin and the component mounting surfaces. |
| One DXF | One DXF can hold the outline and the complete supported hole set. State `--drill-shape-opt 2` explicitly. Refuse missing or duplicate hole circles. |
| Proxy limit | State that frame-only `CN1` and the three declared holes are a proxy limit. |
| Complete hole set | Compare the complete supported hole set, not only mounting holes. Do not ignore extra footprint holes or unsupported drill classes. |
| Q7 approved | A bounded trial with top `CN1` and rotated bottom `CN2` freezes the insertion vector before acceptance. |
| Tolerances | Unchanged. 0.01 mm, 0.1°, 1e-6 mm³. |

## 3. Text items for the frozen interface

Three items from the addendum must appear in the frozen interface text. The lead already approved each one. I do not object to them.

1. C05 imports the STEP solid with CadQuery and compares its Z span with the fixture `core_mm`. Replace the text-point method.
2. Add one labelled finished-board envelope to C08 and C09. State its Z origin, its stackup source and the component mounting surfaces.
3. State the proxy limit for frame-only `CN1` and the three declared holes, and state that the hole comparison covers the complete supported hole set.

## 3a. Codex final clarifications

I agree with the seven clarifications in the Codex review of consolidated revision 6:

1. Replace the open Q8 text with the addendum. C05 uses the imported solid and the fixture stackup. This matches my items 1 and 7.
2. Use the finished-board envelope for clearance. Use the substrate solid for C05 only. This matches my item 2.
3. Complete Q7 with the measured top and bottom connector vectors, and keep the trial as a gate. This matches my Q7 answer.
4. Exclude the `CN1` proxy from its own insertion-volume collision set. C07 tests other solids only. This matches the C07 membership rule.
5. Separate the geometry status from the fit status. A geometry pass with C10 `unconfirmed` is not a fit `pass`.
6. State `--board-only` for `board.step` in the settings record, or name the exact switches.
7. Remove T46 and the open Q8 note. Do not call 1.556 mm a STEP body span.

I have no objection to any of the seven items.

## 3b. Q7 frame check (revision 8) — objections, resolved in section 3c

Revision 8 applies the lead Q7 check. I agree with the method and the frame definitions:

- The target angle comes from the transformed direction vector through `atan2`. The sign is not copied from the Y flip.
- The local frame, the board frame and the contract frame are defined.
- `pad_frame` `placed-file` is the only accepted value. `library-unflipped` refuses. A `B.Cu` footprint without `pad_frame` refuses.
- The GUI-flip limit is stated. The file does not record edit history, so the interface does not claim to detect a GUI flip.

Three objections follow.

### O7. The asymmetric target-angle column is wrong

Section 9.3 lists the asymmetric pad `(2.0, 0.5)` at `θ = 30°` with target angle `30°`. The transformed direction vector is `(1.982, 0.567)`. Its `atan2` angle is `+15.96°`, not `30°`. The value `30°` is the footprint rotation. The table mixes the two meanings. Correct the two asymmetric rows, or add a separate column for the footprint rotation.

### O8. The general `target angle equals θ` claim

The statement holds only for `insertion_vector_local = (1, 0)`. For a general local vector at angle `φ`, the target angle is `θ − φ` mod 360. Replace the general statement with the `atan2` rule. Keep `θ` as the special case for local `(1, 0)`.

### O9. The GUI-flip refusal conflicts with the limit

Section 9.3 still says an editor-flipped footprint "refuses until measured". The later frame-condition limit says the interface does not claim to detect GUI flips. The two statements conflict. Remove or align the first one. The lead requires a detectable input condition for a refusal. `pad_frame` is the detectable condition. An editor flip is not observable.

Minor. Define `connector_frames[].rotation_deg` as the target angle of the connector local `+x` axis, that is the `atan2` angle of `contract(R(θ)·(1,0))`. Then the insertion direction is the separate local vector.

### Independent computation

I computed the rule with `uv run` on the host. The values:

| Local vector | `φ` | `θ` | Board vector | Target vector | `atan2` target | `θ − φ` |
|---|---:|---:|---|---|---:|---:|
| `(1, 0)` | 0.000 | 30 | `(0.866, −0.5)` | `(0.866, 0.5)` | +30.00 | 30.00 |
| `(2.0, 0.5)` | 14.036 | 30 | `(1.982, −0.567)` | `(1.982, 0.567)` | +15.96 | 15.96 |
| `(0, 1)` | 90.000 | 30 | `(0.5, 0.866)` | `(0.5, −0.866)` | −60.00 (300) | −60.00 |

Row two gives the corrected target angle for the asymmetric pad. It proves O7 and O8.

## 3c. Q7 correction confirmation (revision 8, corrected)

Reviewed snapshot SHA-256: `295239507c9a2f12b171049209941862d19d2f6ec08c995f0923332e507fc47e`. It matches the hash in Claude's message.

- O7 resolved. The two asymmetric rows give `15.96° = θ − φ`.
- O8 resolved. Line 64 gives the general rule `θ − φ` and states that it equals `θ` only for `φ = 0`.
- O9 resolved. Section 9.3 no longer claims to refuse an editor-flipped footprint. It states that the only enforced condition is the declared `pad_frame`. T55 refuses a `B.Cu` footprint with no `pad_frame` declaration, which is a detectable condition.

I give explicit agreement on the Q7 frame text in this snapshot.

Optional, not an objection. State the `R(θ)` matrix explicitly as `[[cos θ, −sin θ], [sin θ, cos θ]]`, or write `target = [[cos θ, sin θ], [sin θ, −cos θ]] · local`. The text calls `R(θ)` "the standard rotation", while the board rule uses the other matrix. The check holds with the standard counterclockwise matrix. The explicit form prevents a wrong convention.

## 3d. Post-Q7 stale text check

Reviewed snapshot SHA-256: `676de1bba855e36f9c0604773f81106cab88f6a6d980e16414731361dc46c287`.

Codex found two stale text conflicts. I checked the current snapshot.

- Codex item 1 resolved. Section 5 line 110 now gives the measured matrix rule `target = [[cos θ, sin θ], [sin θ, −cos θ]] · local` and states that the side sets only the Z range. It agrees with section 9.3. No second mirror.
- Codex item 2 partly resolved. The duplicate Q8 entry is gone. The heading "Open for both reviewers" still lists Q7, Q8 and Q6, and each item says resolved or confirmed. Rename the heading, or move the three items to the resolved lists. The heading is stale.

No other Q7 conflict remains. The section 5 and section 9.3 matrices agree.

## 3e. Final Q7 confirmation (revision 8 snapshot 5a0b4850)

Reviewed snapshot SHA-256: `5a0b4850aa57c11973560ca2551ead734b7fcfd3cc70a168d8ec3f25495966f5`. It matches Codex's final agreement hash.

- O7, O8 and O9 resolved (section 3c).
- Codex item 1 resolved. Section 5 gives the measured target matrix and states the side sets only the Z range (section 3d).
- Codex item 2 resolved. The stale heading is gone. Section 10 now reads "Resolved in this revision (all three are closed)".
- The section 5 and section 9.3 matrices agree with my independent computation.

The optional `R(θ)` note is covered by the explicit target matrix in section 5.

I give final explicit agreement.

## 4. Independent evidence

### O1

I ran the accepted validator on a board record with a `dimension_owners` field:

```text
uv run contracts/validate.py --schemas contracts/schemas /tmp/board-owners.yaml
/tmp/board-owners.yaml/dimension_owners: schema.unknown_field: The field 'dimension_owners' is not in the schema.
status: fail (1 files read)
exit=1
```

The corrected revision removes the field. The correction is correct.

### Measured solid and frame

My bounded trial `b11-export-trial-pi.md` and the Claude trial agree. The frame is X unchanged and Y negated relative to the drill/place origin. Root imported `board.step` and `b_nopad.step` with CadQuery. Each file holds one valid solid with Z `0..1.51`. My first text parse reported `1.556` because the text holds points outside the solid. The imported substrate is 1.51 mm. C05 uses the imported solid. The addendum is correct, and I correct my earlier note.

## 5. Agreement

I agree to the corrected revision 6 with the addendum as the consolidated interface for B11:

- The strict transform and the two modules.
- The template `skills/pcb-design/templates/mech-fit-a/`.
- The separate `mech-release/1` record with exact file hashes and canonical record hashes.
- The drill/place origin equal to the anchor.
- The export switch set, one DXF with `--drill-shape-opt 2`, and the drill-hole coverage.
- C01 to C12 with the closed complete hole set and the order-independent comparison.
- The imported-solid C05 and the stackup C05s.
- The finished-board envelope for clearance.
- The fixed tolerances, the input capture and the freshness gate.
- The narrow `pcb.py` mechanical dispatch and readiness, with the existing interface behavior unchanged.
- The unchanged B5 history and the unused draft interface.

The next steps are the Codex agreement, the lead acceptance, and then product implementation.

## 6. Limits

- This review covers the proposal only. No product file changed.
- I did not run the fixture or the new tests.
- I ran the O1 validator check and the bounded export trial. Both are recorded.
- I will review the frozen B11 files when Claude publishes them.
