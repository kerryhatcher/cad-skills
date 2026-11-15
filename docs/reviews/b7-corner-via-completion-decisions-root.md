# Corner and via completion decisions

Date: 2026-11-15 UTC. Author: skill-dev-lead.

The remaining fixture work is released. A fixture with no zone is not a blocker.
Make an owned four-layer fixture, fill its internal zone, and measure the accepted clearance cases.
Continue the silk, order, omission, source-drift, and standalone cases in parallel with these two corrections.

## Corner compatibility

The retained page gives cutter diameters, not supplier minimum corner radii.
Do not label the inferred radii as quoted supplier limits. Do not add these values to `limits` as supplier minima.

Record the published cutter diameters as process facts with their source hashes and original inch values.
For a circular cutter, derive the tool radius as half its diameter.
Label the comparison as derived tool compatibility. It is not a supplier statement or a general manufacturing guarantee.
Compare concave outline corners and internal cutout corners with the appropriate tool radius.
The r8 boundary cases exercise this derived comparison at 0.034 in and 0.020 in.
Do not apply the concave-corner test to convex outer corners.
Refuse unsupported outline geometry by name. Do not approximate an unrecognized curve and report a pass.

Use the existing process-evidence route and profile extensions for the published facts.
Keep the source fact, the derivation, and the measured board geometry separate in the evidence.
No shared schema change is necessary.

## Via construction

Blind and buried spans are board facts. A named supplier prohibition gives a failed condition and exit 1.
The generic unsupported-geometry path remains exit 2.
Add the narrow construction check from captured board bytes or pcbnew inventory before the generic span refusal prevents that diagnosis.
Do not change the B6 worker. Preserve all other unsupported-geometry refusals.

Use a skill-owned board extension for the requested fabrication process:
`extensions.fabrication.via_process`.
Its values are `standard_through`, `filled_plated_via_in_pad`, and `unconfirmed`.
This field declares the requested process. It does not prove physical construction.
The existing board capture and hash bind the field to the supplier result.

A board with no vias can report this condition as not applicable, with its measured zero count.
A board with vias and a missing or `unconfirmed` declaration retains a mandatory pending condition.
A declared `filled_plated_via_in_pad` process fails the existing supplier prohibition with exit 1.
A `standard_through` declaration can pass only when the measured spans are through spans.
An unknown value is an invalid record. Do not infer the process from the position of a via.

Document the field and add focused cases for missing, unconfirmed, invalid, prohibited, and supported declarations.
Retain the ordinary exit precedence. A pending mandatory condition prevents qualification.

## Review boundary

The author can continue the independent tests now.
Both reviewers will identify any concrete conflict in these two decisions before their product changes start.
Do not start another general design review. Preserve the accepted publication, slot, and mask algorithms.
The complete replacement freeze must include the new process facts, documentation, fixtures, code, and evidence.
