# B7 geometry draft observation

Date: 2026-11-14 UTC. This is an implementation observation before the author freezes the files.

I measured `scripts/inspect_mask.py` in the new fabrication skill.
The SHA-256 before and after the probe was `e473e4c989ca60215895407817898f6cf360f6e2689ea398ce4682a076270cd2`.
The probe used `uv` with cached `gerbonara==1.6.3` and a temporary file.

## R1: overlapping rectangles pass

Two dark rectangular flashes have dimensions 2 mm by 2 mm.
Their centers are (10, 10) mm and (11, 10) mm.
The overlap is 1 mm in X and 2 mm in Y.
The inspector returns exit 0, `merged_opening`, and `result: pass`.

The core distance is zero for intersecting rectangles. Both radii are zero.
Thus, the signed-radius subtraction cannot distinguish contact from rectangle overlap.
This violates the accepted refusal of overlapping clusters.

Add a separate interior-overlap test for the supported shapes.
Test rectangle pairs, coincident rectangles, and mixed rectangle/rounded shapes.
Keep contact and interior overlap distinct. Do not infer a web pass from zero core distance.

The probe input was:

```text
%FSLAX46Y46*%
%MOMM*%
%ADD10R,2X2*%
%LPD*%
D10*
X10000000Y10000000D03*
X11000000Y10000000D03*
M02*
```

## Pending code inspection

The current draft selects a RoundRect by its name and parameters alone. It does not validate the macro definition.
The accepted interface calls for the measured macro definition and supported parameters. A matching name is insufficient.
The draft also retains a list of all nearby pairs. A dense column can produce quadratic storage.
The accepted two-second limit and linear-storage condition remain necessary.
These are draft observations, not statements about the final implementation.
