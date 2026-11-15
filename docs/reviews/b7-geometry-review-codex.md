# B7 geometry checkpoint review

Date: 2026-11-14 UTC

## Scope

I reviewed the six frozen files listed in `b7-geometry-checkpoint-claude.md`. I did not inspect changing `fab.py` or profile files. I did not run the full suite.

## Hash measurements

The six hashes matched the checkpoint before and after this review.

| File | SHA-256 before and after |
|---|---|
| `skills/pcb-fab-package/scripts/inspect_mask.py` | `ade74723a60442ced804686e8784526c283f619064cccf17f842116cad0af328` |
| `skills/pcb-fab-package/scripts/macro_defs.py` | `c91d475f92bc676780a7fa8a3e9af5991e728f02128eab187ea9699db4e1958d` |
| `skills/pcb-fab-package/scripts/export_inspect.py` | `4b1b87dcbb00d69eba86b7192683466e851443dde59a6b78f5cf823bd8ce1f20` |
| `skills/pcb-fab-package/scripts/inspect_slots.py` | `9b543eb20390cde8f4811e805b4498bc6ac50dea2140076197f29dda9e3e39dc` |
| `skills/pcb-fab-package/scripts/board_inventory_slots.py` | `ed8a9d74520420255f789c49c5b4464af67e312ca53e4d9f538291ec87870838` |
| `tests/test_pcb_fab_package.py` | `182ca9e52faa55cc557e67f57462192b7d36ce2d22e8ec35c1ab44584ae72341` |

## Focused results

I ran 18 focused checks through `uv`. They covered the mask geometry cases, the measured board and drill fixtures, and the measured Excellon subset. All 18 passed. The measured 0-degree and 45-degree board fixtures agree with their exported slot records. The tests also confirm endpoint reversal, plating class, multiplicity, and the 501 nm tolerance cases.

An independent Gerber input with two overlapping 2 mm rectangles returns the expected unsupported result. The mask boundary function returns `fail` below the lower bound, `uncertain` at the lower bound and at the nominal limit, and `pass` at the upper bound. The parser retains only the specified circle, rectangle, and `RoundRect` shape classes. It refuses regions, unsupported apertures, clear polarity, and interior overlap in the tested cases.

## Corrections required

I agree with the three findings in `b7-geometry-review-root.md`.

1. The raw macro scan misses inline and space-prefixed `%AM` blocks. The Gerber parser accepts both forms. Root probes show a changed `RoundRect` definition that draws two overlapping 10 mm circles can return `pass`. Validate the macro definition that the parser uses. Add both retained probes as regressions.
2. The inspector reads the Gerber bytes for geometry, then reads the path again for the reported hash. A controlled file change can bind a passing result to failing bytes. Hash and parse one byte snapshot. Return that hash with the measurement. Add the retained change-during-read regression.
3. The code limits candidate pairs, but it does not enforce the accepted two-second bound. Root measured 1.432 seconds for its retained 2,200-flash probe, below two seconds. This result does not show a time failure. Add elapsed-time enforcement across parsing and inspection, in the worker or its caller.

The inspector also ignores `CircleAperture.hole_dia`. I measured `%ADD10C,2X1.9*%` as a circle with a 1.9 mm hole. `shape_of` treats it as a solid 2 mm circle. Refuse apertures with holes until the inspector measures their geometry. This finding does not claim a failed 4 mil web.

The inspector also accepts non-rectangular `RoundRect` parameter points. I changed the four corner points while retaining the measured macro definition. The parser accepted the aperture, and `shape_of` reduced the points to a bounding box. Validate the supported point order and rectangle geometry. Refuse other parameter geometry. Add a malformed-parameter regression.

The Excellon reader accepts a missing `M30` and coordinate records after `M30`. I measured both cases with an independent input. An empty board and empty drill files without `M30` return slot-inspection exit 0. Require the terminal record and refuse all records after it. Add missing-end and trailing-record regressions.

## Verdict

The focused tests support the measured geometry cases, board slot coordinates, plating classes, multiplicity, and declared Excellon units and precision rules. I do not accept this checkpoint for implementation freeze. The macro bypass, file-hash binding, unsupported aperture geometry, malformed `RoundRect` parameters, elapsed-time enforcement, and Excellon command order need correction and focused regressions first.
