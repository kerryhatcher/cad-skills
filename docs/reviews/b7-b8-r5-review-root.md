# B7/B8 revision 5 review

Date: 2026-11-14. This is a paper review. Proposal SHA-256: `32c77100a31010be95d2d84ad5165ac8c5481e140a4f3c6612bc73f5693cd045`.

The independent skill boundary and the slot export inspection address the earlier gaps. The following corrections remain necessary.

1. Keep invalid records at exit 1. Use exit 2 for absent prerequisites or unsupported operations. The two new command rows incorrectly say `2 invalid`.
2. A 0.25 mil raster with boundary uncertainty cannot establish separate decisions at 3.9, 4.0, and 4.1 mil. Define an error bound. A result whose interval crosses the limit must not claim a pass. Measure the selected method before support. Consider vector geometry or bounded local refinement. Do not allocate a full-board fine raster without a resource bound.
3. Flashes and regions alone do not define all possible Gerber geometry. Account for strokes, aperture shapes, macros, polarity, and regions that the exporter emits. Refuse unsupported constructs. Do not silently omit them. A measured existing renderer is preferable to an incomplete new parser.
4. Derive the slot tolerance from the measured export units and coordinate precision. The existing 3:3 mm output has 0.001 mm coordinate increments. A 0.5 mil tolerance is not that precision. Compare endpoint pairs without dependence on endpoint order. Preserve multiplicity and plated class. Define angle behavior for near-circular slots.
5. The file list must name an existing source for each byte copy. The B6 export checks reside in `pcb.py`. A new `export_inspect.py` extracted from that file is an owned derivative, not a byte copy of a separate file.

Use temporary fixtures and the existing image for the prerequisite trials. Measure the active rule filename, severity settings, source exclusions, slot records, mask geometry, and PDF commands. Keep the accepted B6 files unchanged during these trials. Record commands, exits, input hashes, output hashes, and explicit unsupported cases.

The trials do not establish package qualification. Full implementation follows the combined interface agreement. The narrow shared-contract changes remain authorized under that review.

The final proposal must replace contradictory inherited text. Align all command exits, not only the two new inspection rows. A maximum limit passes below and at the threshold, then fails above it. A minimum limit has the opposite boundary results. Published process capability is not a design margin. Keep these distinctions in the final profile and test tables.
