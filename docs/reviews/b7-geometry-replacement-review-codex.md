# B7 geometry replacement review

Date: 2026-11-14 UTC

## Hash measurements

I measured the six frozen files before and after review. The hashes matched the replacement checkpoint both times.

| File | SHA-256 before and after |
|---|---|
| `skills/pcb-fab-package/scripts/inspect_mask.py` | `7d0e6592dcd504e662a4944107367f948b7833caa205d64e73d4706e479f1192` |
| `skills/pcb-fab-package/scripts/macro_defs.py` | `c91d475f92bc676780a7fa8a3e9af5991e728f02128eab187ea9699db4e1958d` |
| `skills/pcb-fab-package/scripts/export_inspect.py` | `5be010bffda38af71ad1fba753d460bb65534d1d6c887999d8a1049d60ce759b` |
| `skills/pcb-fab-package/scripts/inspect_slots.py` | `9b543eb20390cde8f4811e805b4498bc6ac50dea2140076197f29dda9e3e39dc` |
| `skills/pcb-fab-package/scripts/board_inventory_slots.py` | `ed8a9d74520420255f789c49c5b4464af67e312ca53e4d9f538291ec87870838` |
| `tests/test_pcb_fab_package.py` | `070440293e9520dd75999a8acd4daebdf87947b1e547330f49cb7d04c6c3a5bb` |

## Focused review

I did not run the full 93-test suite. Focused probes through `uv` confirm that the inline and space-prefixed macro cases refuse. The inspector refuses circular apertures with holes and malformed `RoundRect` corners. It refuses a missing `M30` and records after `M30`. The retained 0-degree and 45-degree slot fixtures pass.

A controlled file change after the single byte read returns the old byte hash with the old passing result. A separate inspection of the changed bytes returns a failure. A zero-second budget refuses the input. These results support the macro, snapshot, aperture, parameter, and Excellon corrections.

## Remaining geometry and time scope

`roundrect_geometry` refuses a radius greater than half the smaller core side. The accepted distance model defines the macro as the core rectangle plus a disk. That model does not impose this half-side limit. The retained geometry trial also states the Minkowski-sum model without this limit. Treat the limit as an explicit conservative support policy if the implementation retains it. Do not describe it as a geometric validity rule. The report must identify the unsupported parameter range and a regression must cover its refusal. The implementation can also remove the extra restriction and measure all positive radii that the macro definition supports.

The inspector enforces a cooperative elapsed-time budget. It tests the budget after `GerberFile.from_string` returns, so it cannot interrupt a slow or stuck parser call. `workflow.py` invokes the inspector with `subprocess.run` and no timeout for the top and bottom masks. The caller does not enforce a hard two-second wall-clock limit. I measured no production time overrun. If the accepted bound means a hard limit, add a caller timeout and a focused timeout regression.

## Verdict

The focused probes support the listed geometry, snapshot, aperture, parameter, and Excellon corrections. Record the radius bound as an explicit support policy or remove it. Add a caller timeout if the accepted two-second limit must bound wall-clock time. This geometry review does not accept the full B7 workflow.

## Final decision agreement

I agree with both decisions in `b7-geometry-final-decisions-root.md`. Remove the radius-to-core-side cap. Keep positive finite radii and valid finite coordinates, and test a radius above half the smaller core side with the accepted core-distance formula. Keep the helper budget. Add a two-second timeout at each public mask invocation in `fab.py` and `workflow.py`. Give each run a fresh report path. A timeout must return exit 2 and must not use or publish an old passing result. Test a controlled stalled worker through the public caller. Describe the helper budget and caller timeout as separate limits. Do not claim that the helper can interrupt an active parser call.
