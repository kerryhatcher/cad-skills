# B11 interface decisions

Date: 2026-11-15 UTC. These decisions apply to the combined interface before implementation.

1. Use two modules: `skills/pcb-design/scripts/mechanical.py` and `skills/pcb-design/scripts/mechanical_fit.py`. The first owns records and orchestration. The second owns CadQuery geometry and its PEP 723 dependencies. Both belong to `pcb-design`.
2. Use `skills/pcb-design/templates/mech-fit-a/`. Include the source generator, `board.yaml`, the interface, component evidence, enclosure parameters, and export settings. Generate STEP and DXF during tests. Do not change the historical trial.
3. Keep the strict `extensions.transform` shape in revision 3. Do not add a duplicate target origin or a formula string. `origin_mm` is the target origin. Validate finite numbers, exact field types, axes, and scale. Reject booleans as numbers.
4. Treat the outline start and anchor as different points. Declare the outline start explicitly. The drill/place origin must equal the anchor.
5. Measure the exporter frame in the initial fixture trial. Freeze that mapping before acceptance tests. Do not select a new best-fit transform for each input. Such a transform could hide a mirrored export. Keep the expected geometry independent of the measurement. Measure the rotation convention before a general rotation claim.
6. Keep connector dimensions and envelopes outside the shared connector object. Use only its six schema fields. The component evidence declares a local insertion vector and volume. Side alone does not define an edge connector's insertion direction. Transform this vector with the measured frame and side conventions.
7. Include exact export switches and variant behavior in the settings record. Use explicit millimeter DXF units and the same drill/place origin for both formats. Measure the STEP board body without optional surface layers. Keep the Z datum explicit.
8. Export DXF outline and holes as the plan states. The team can use separate files with explicit roles. Compare the hole coordinates and diameters independently. Do not count an Edge.Cuts-only file as hole coverage. Bind drill files if a comparison consumes them.
9. Add a plated hole to the asymmetric fixture. Keep the unequal nonplated holes, chamfer, bottom-side part, and rotated bottom-side connector test.
10. Use one strict mechanical release record outside the shared registry. `mechanical.py` validates it. State a closed output-role list for each produced file. Read the expected release ID from an explicit input record. Bind the electrical release ID and all consumed inputs by exact hashes.
11. Reuse the accepted canonical-hash helper. Keep exact file hashes separate from canonical record hashes. Do not introduce different JSON hash rules.
12. Keep lateral clearance separate from top and bottom height limits. Define the closed cavity polygon and its offset. Compare owner declarations from the electrical interface and mechanical source. Refuse a conflict by dimension name.
13. Keep the proposed tolerances fixed for the first trial. Record repeatability. Do not widen a failed tolerance automatically. Send any proposed change to both reviewers and the lead before another acceptance run.
14. The mechanical team owns narrow `pcb.py` dispatch and readiness integration for this feature. Include that integration in the final interface and tests. Existing interface review behavior remains unchanged. No copied-contract or shared-schema edits.
15. Use captured input bytes, existing project locks, confined paths, atomic report writes, and a final freshness gate before publication. Bind the report to its inputs and result. Reuse the accepted helpers. Do not introduce another framework.

Apply the schema, board-record, export, evidence, and test corrections from both reviewers that agree with these decisions.
Send one consolidated revision for explicit agreement. Bound export trials can run to resolve the measured frame and DXF hole method.
Product implementation follows both reviews and lead acceptance of that revision.

## Measured frame and thickness addendum

Root imported Pi's two STEP files with CadQuery through `uv run /tmp/b11-body-root.py`.
Both imports contain one valid solid. Each solid spans X 100 to 140, Y -125 to -100, and Z 0 to 1.51 mm.
The files are `/tmp/b11-trial/out/board.step` and `/tmp/b11-trial/out/b_nopad.step`.
The retained probe is `b11-body-probe-root.py`. Its command exited 0.
Text control points outside this solid do not define its thickness.

C05 compares the imported substrate solid with the independent fixture stackup.
C05s compares the declared layer sum with the interface total thickness.
Put the explicit stackup in the fixture source and a validated extension if another record carries it.
Do not add unknown top-level fields to `board.yaml`.
Keep the total thickness and substrate thickness separate. Do not derive the expected core thickness from the output under test.
Use an explicit finished-board envelope for enclosure clearance. Label this envelope and bind its stackup source.
Define its Z origin and the component mounting surfaces. A substrate-only solid cannot prove clearance for the finished board.

The [KiCad physical stackup documentation](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html) describes copper, dielectric, and solder mask as separate layers.
The local 10.0.5 trial remains the evidence for these export bytes.

A single DXF can contain the outline and holes when the measured switches produce both.
This agrees with item 8. State `--drill-shape-opt 2` explicitly and reject missing or duplicate hole circles.
The new fixture can use frame-only CN1 and exactly three declared through holes. State this proxy limit.
Compare the complete supported hole set, not only mounting holes. Do not ignore additional footprint holes or drill classes.
The B5 interface remains unchanged. Its two mounting holes do not define the full board drill inventory.

Q7 is approved for a bounded trial with top and rotated bottom-side frames. Freeze the measured vector mapping before acceptance tests.
Q8 is approved with the independent stackup and finished-board envelope rules above. Keep the tolerances unchanged.
