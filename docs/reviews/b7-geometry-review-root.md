# B7 geometry checkpoint review

Date: 2026-11-14 UTC. Scope: the mask inspector in the six-file geometry checkpoint.
This report does not accept the remaining fabrication implementation.

## G1: a macro can bypass the definition test

The measured inspector hash is `ade74723a60442ced804686e8784526c283f619064cccf17f842116cad0af328`.
The hash stayed equal before and after both probes.
See [the retained inputs and results](b7-macro-probe-root.json).

The macro scanner recognizes `%AM` only at the start of a line.
Gerbonara also accepts an inline macro or leading whitespace before the macro.
A different macro named `RoundRect` then passes the scanner.
The inspector measures its parameters as the accepted rounded rectangle, although the macro draws a different shape.

Both retained probes define two overlapping circles with a 10 mm diameter.
The inspector reports exit 0 and `pass`. The expected result is unsupported geometry, exit 2.

Validate the macro definition that the Gerber parser actually uses.
Do not let a difference between the scanner and parser hide a definition.
Add both retained cases as regressions. Keep the supported subset narrow.

## G2: a report can identify bytes that the inspector did not examine

The inspector reads the file for geometry, then reads it again for its hash.
A controlled change between those reads gives a passing report with the hash of a failing mask.
See [the retained result](b7-binding-probe-root.json).

The original input has a 4.1 mil web. The changed input has a 3.9 mil web.
The first run returns exit 0 with the changed input's hash.
A separate inspection of those changed bytes returns exit 1.
The inspector source hash stayed equal before and after the probe.

Calculate the hash from the same bytes that supply the geometry.
Return that hash with the inspection result. Do not read the file again to identify the measured input.
The caller must bind and compare that hash before publication.
Add the controlled-change regression.

## G3: the pair limit is not the agreed time limit

The frozen implementation has a candidate-pair limit but no elapsed-time limit.
The accepted interface also has a two-second bound.
A retained timing probe uses 2,200 separated circle flashes in one column.
Its input is below the byte and flash limits.
See [the timing result](b7-runtime-probe-root.json).
This probe refused at the pair limit after 1.432 seconds on this host. It did not exceed two seconds.
The finding concerns the absent enforcement, not a measured time violation in this probe.

Enforce the elapsed-time bound, including parsing, through the worker or its caller.
An implementation-specific pair count cannot establish a time bound on all supported hosts.
Keep the pair limit as an additional bound if useful.

The reviewers must agree on the combined correction scope before the author changes the frozen files.
