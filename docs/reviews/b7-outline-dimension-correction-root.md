# Board dimension correction

The boundary tests found that `GetBoardEdgesBoundingBox()` includes the Edge.Cuts stroke width.
A 406.4 mm rectangle with a 0.05 mm stroke reports 406.45 mm and fails the width limit.
A 6.34 mm rectangle reports 6.39 mm and passes the 6.35 mm minimum incorrectly.
The retained failed log is `b7-completion-evidence/dimensions-before-root.log`.

The B7 inventory worker will measure the Edge.Cuts centerlines.
It will set the Edge.Cuts stroke widths to zero in memory before the bounding-box call.
It will include board drawings and footprint drawings. It will not save the board.
The B6 worker and the hole measurements remain unchanged.
The boundary tests will compare saved rectangle coordinates with the inventory and the supplier rows.
An additional stroke-width test will prove that the source bytes stay unchanged and the dimensions do not depend on the stroke.
The drawing facts use this same inventory. The workflow tests must pass with the corrected dimensions.

## Measured result

The corrected dimensions pass all 18 board boundary checks.
The separate pinned-image proof passes 12 checks for board and footprint graphics.
Stroke widths 0, 0.05 and 1.0 mm all give exactly 406.4 by 6.35 mm.
Each saved source retains its original bytes.
Thus the measured KiCad version does not substitute a default width or retain an inflated cached box in this worker.
Logs: `b7-completion-evidence/dimensions-corrected-root.log` and `b7-completion-evidence/outline-root.log`.
