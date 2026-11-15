# B9 drill export probe

Date: 2026-11-14 UTC.

The existing B6 image exported separate inch drill files from a temporary copy of the accepted B5 board.
The command exited 0. No source file changed.
The [record](sierra-source-evidence/drill-probe.json) contains the full command, image identity, paths, outputs, and hashes.
The [probe script](sierra-source-evidence/drill-probe.py) runs through `uv`.

The command uses these explicit options:

```text
--format excellon
--drill-origin absolute
--excellon-units in
--excellon-zeros-format suppresstrailing
--excellon-separate-th
```

The two generated files state `2:4/ absolute / inch / suppress trailing zeros` in the format comment.
They contain `INCH,LZ`, `G90`, and separate plated and non-plated file-function comments.
Do not infer the suppression rule from the letters `LZ` alone. The selected CLI setting and coordinate behavior control the test.

This probe establishes export availability and the measured header. It does not prove coordinate fidelity or supplier acceptance.
The implementation must compare the exported holes with the independent board inventory.
Its tests must include coordinates with trailing zeros, negative coordinates, tool dimensions, multiplicity, and plating.
The inch format has a 0.0001 in coordinate increment. Derive its comparison bound separately from the B7 millimeter bound.

The existing export contract supports inch units, four decimal places, and trailing-zero suppression.
The B6 and B7 runtime subsets remain unchanged. A Sierra adapter must own and test its additional export subset.
