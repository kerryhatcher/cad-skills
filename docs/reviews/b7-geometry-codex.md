# B7 geometry correction scope

Date: 2026-11-14 UTC

I agree with the narrow correction scope in `b7-geometry-draft-root.md`.

The inspector must refuse interior overlap for supported shapes. Add focused tests for overlapping and coincident rectangles, mixed rectangle and rounded shapes, and contact without interior overlap. Zero core distance alone must not pass the web check.

The inspector must validate the measured macro definition and its supported parameters. A matching macro name is not sufficient.

The inspector must keep linear storage and meet the accepted two-second limit. Do not retain all nearby pairs in a dense column.

These points define the focused review of the frozen geometry modules and tests. This report does not assess changing files or suite results.
