# B6 interim code review: Codex

Date: 2026-11-14 UTC. This review covers the interim snapshot only. It is not final B6 acceptance.

## Measured boundary

The 65-file manifest `docs/reviews/b6-interim-files-root.sha256` has SHA-256 `a13f9295b2e630e076bf2727854ff7a1f8d8de6bafae3be1d2f4e76dd4cc8576`. All 65 entries passed `sha256sum -c` before review. `skills/pcb-design/scripts/pcb.py` measured `c57de5b825ae03bb32f9132d3ebf2a1e088338f0216c3534286b9738c5f87621` before review. I made no implementation changes and ran no tests or probes. I did not use the image.

## Concrete findings

| Finding | Evidence and risk | Focused regression |
|---|---|---|
| Simulation assertions do not come from the bound snapshot. | `cmd_sim` calls `load_assertions(project)` before `stage_snapshot`. It then binds the staged assertion bytes but calculates circuits and expected values from the earlier live parse. A change between these reads can make the result decision use bytes that the binding does not describe. | In a temporary project, change `assertions.json` after the live parse and before staging. Confirm the command refuses or evaluates the staged assertions. Confirm no result can pass with a decision derived from different assertion bytes. |
| Assertion records are incomplete. | `load_assertions` accepts an empty list and does not validate the types of `circuit`, `measurement`, or `expected`. A list-valued circuit can also make the duplicate-pair key unhashable and raise `TypeError`. | Test empty list, missing/empty strings, wrong field types, boolean and non-finite expected values, and a list-valued circuit. Each malformed record must produce a stable finding and exit 1, not a traceback or empty pass. |
| Circuit dependency closure is narrower than general ngspice input. | `closure_paths` includes only top-level `simulations/*.cir`. It does not traverse referenced `.include` or `.inc` files. The current supported scope must refuse such dependencies or include and hash their confined paths. Silent omission can make a simulation result stale without detection. | Use a circuit with a relative included model. Change only the included file after simulation. The operation must refuse unsupported dependency syntax or bind the included file and make `check` stale after the change. |
| Library closure uses shallow globs. | The closure includes top-level KiCad symbol files and one-level footprint module paths. It does not recursively discover nested local library files. If nested local libraries are supported, their edits can escape freshness checks. If they are outside the supported scope, reject them explicitly. | Add a nested local symbol or footprint dependency and change its bytes. Confirm explicit refusal or a closure hash change. |
| Interface review readiness checks only a subset of the record contract. | `interface_ready` accepts matching board and interface hashes plus any non-empty `examined` value. It does not validate the review schema, pointer existence, changed-pointer coverage, reviewer, or statement. A hand-written incomplete record can therefore satisfy readiness. | Write a record with current hashes and a bogus non-empty pointer or missing required fields. `check --for ready` must reject it. Test changed interface pointers omitted from `examined`. |

## Known incomplete items, not new findings

The lead lists unresolved native-route coverage, update geometry gating, exact GUI image identity, worker caller conditions, inventory docstring correction, standalone runtime tests, agent trials, and final documentation. Pi also reports two-layer-only export against the r3 layer-function promise, unreported staging leftovers, direct worker invocation instead of the r3 `uv run` form, and missing byte-copy checks for the installed skill. These remain separate from the findings above and require reconciliation against the accepted r3 interface.

## Limited assessment

The report publication chain writes raw data, binding, then a result containing the binding hash. `check_report` verifies that hash, the raw hash, the current closure, and a passing result status. This covers the named interruption between binding and result publication when the result is stale. Exit precedence for tool exits and finding violations is explicit in `judge`.

This is static source review. I did not test interruption behavior, concurrent edits, malformed saved reports, or the image. The report does not establish readiness of the complete B6 implementation. Final review must remeasure the frozen file manifest and verify each correction with focused tests.

## Combined correction agreement

Date: 2026-11-14 UTC. I read `b6-resume-root.md` and agree with its combined correction scope. I have no conflict with the five Codex findings or Pi F1-F4. The lead's reproduced helper results strengthen the manual-review, automatic-interface, and empty-assertion findings. They remain helper-level measurements, not a full CLI readiness test.

I agree with the two added corrections. The automatic interface result must bind the exact resulting interface bytes and validate required fields plus prior-board and expectation records. A change to `height_limits.top_mm` must make that result stale. Add `check --for export` and compare current published output files with their bound hashes. Test a missing output and a changed output after successful export. Do not require a prior export to run the export command.

This agreement is limited to the accepted r3 interface. It does not accept the interim implementation or replace the required focused regressions and final frozen-file review.
