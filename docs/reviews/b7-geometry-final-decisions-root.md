# B7 final geometry decisions

Date: 2026-11-14 UTC.

The replacement reviews support the macro, snapshot, aperture-hole, corner-order, and terminal-record corrections.
Two details remain. These decisions resolve them without a new design phase.

1. Remove the radius limit relative to the core side. It is not a validity rule for the accepted geometry model.
   Keep positive finite radii, valid finite coordinates, the supported rectangle shape, and the correct corner order.
   Add an independent case with a radius greater than half the smaller core side.
   Its expected distance must follow the core-distance formula. Retain overlap refusals.
2. Keep the cooperative budget in the geometry helper.
   Add a two-second subprocess timeout at each public `fab.py` and workflow invocation of the mask worker.
   A timeout returns exit 2 with a resource-limit finding. It must not publish a passing result or use an old result.
   Give each run a fresh report path. Test a controlled stalled worker through the public caller.
   Describe the helper budget and caller timeout separately. Do not claim that a checkpoint interrupts an active parser call.

Dependency setup is separate from the bounded inspection. Normal inspection must use the prepared environment.
The subprocess timeout can have ordinary process-start and termination overhead. Do not claim exact real-time scheduling.

Both reviewers must confirm these two decisions. Then Claude can make the narrow correction and replacement record.
The other accepted corrections stay. Full B7/B8 workflow acceptance remains separate.
