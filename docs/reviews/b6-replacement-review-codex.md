# B6 replacement review: Codex

Date: 2026-11-14 UTC. Scope: the 211-file replacement, the narrow native measurement and template-history repair, corrected interface/parser evidence, and selected focused tests. No broad suite or GUI repetition was run.

## Frozen hashes

| Item | Measured SHA-256 |
|---|---|
| `b6-replacement-files.sha256` | `f93454c545a355e43be3e447b41baa334299dbf09bb08fff4c57ab3f234aca39` |
| `b6-native-repair-record.md` | `2e8f4e2031a19bbf552ee366f0c5f38ce591890dff416f5f684fe52108f73481` |
| `skills/pcb-design/scripts/pcb.py` | `0928be463f6503b41d5c7ba02c076556c0ac750630da63ac8c86866cf664cabe` |
| `tests/test_pcb_design.py` | `242176ead31847772750c58b224933178e2e1bc265ca8245909912de87aebe6c` |
| `.gitignore` | `6b3a6acf3bb8b3ee922cbf3b7e9c57224a86226b04fae0b0ea5a9f89b1ac2a0c` |

All 211 manifest entries passed before and after review. The repair-record hash matches. No implementation file changed during review.

## Focused verification

I ran these focused commands through `uv`:

- `uv run tests/test_pcb_design.py native`: three tests passed. The tests cover per-operation prerequisites, no-traceback behavior, a native route inside the runtime image, and host refusals.
- `uv run tests/test_pcb_design.py gitignore`: the template-history exception test passed.
- Focused assertion, manual review, automatic evidence, export, and binding filters passed. They cover malformed assertions, duplicate/interface evidence rejection, preserved prior and expectation bytes, all-pointer coverage, export output hashes, and binding/result interruption.
- Residual staging and malformed interface evidence tests passed.

These are focused checks. The tests that invoke KiCad or ngspice use the existing container image through the CLI. The native route test runs inside that image. The host has no KiCad installation. The focused test for a missing tool checks the operation-specific refusal path; it does not install or remove host tools.

## Native tool measurement and publication

`measure_tools(image, tools)` now measures only the named tools and records an absent tool as unavailable. `native_versions_ok` checks the tools required for the requested operation. Publication calls pass the operation to `tool_versions_of`, so a simulation result does not require KiCad CLI merely to record versions. The targeted tests and source path support the narrow repair: native simulation can run with ngspice when KiCad CLI is absent; native ERC does not require ngspice; a missing required tool returns exit 2 without a traceback.

The report bindings retain operation-specific tool versions. This review did not independently alter the host `PATH` or remove system executables. The missing-tool behavior is covered by the focused tests and the repair record, not by a host installation test.

## Corrected interface and assertion evidence

Source inspection confirms that the manual review record carries `prior_interface_sha256`. Readiness checks prior-interface bytes and requires changed-pointer coverage, or all top-level pointers when the prior hash is null. Automatic readiness checks the preserved prior board and expectation bytes against recorded hashes and validates the expectation. Strict JSON parsing rejects duplicate keys. Assertion identifiers use full-string validation, and excessive numeric values map to `assertion.malformed` rather than an uncaught overflow. The focused tests exercise these corrected paths and reject both prior false-ready cases.

The independent RC result remains valid: the temporary 1 ms measurement on the A4 20 kohm circuit produced 1.298448 V against 1.2984 V with 0.012984 V tolerance. No agent rerun was needed.

## Git inclusion and exclusion

The template contains one prior-interface history JSON file under `out/`. The exception in `.gitignore` names only `skills/pcb-design/templates/rc-bare-board/out/history/interfaces/*.json`. `git check-ignore -v` reports that exact exception for the template record. A separate `out/temp/foo` path remains ignored by `.gitignore:229`. The focused Git regression passes. This preserves template initialization data without broadly unignoring `out/`.

## Verdict and limits

**I accept the corrected B6 replacement within the r3 scope.** The native measurement repair, interface and assertion corrections, and template-only Git exception match the agreed scope and pass the focused checks. The prior corrected-scope acceptance remains in force.

This is not a broad regression run. I did not rerun the 41-test suite or GUI integration. I did not independently rebuild the standalone image, repeat agent trials, or validate the full runtime/export evidence. Pi's scoped runtime, export, GUI, and standalone review remains relevant. This acceptance does not establish a native host with KiCad installed or supplier qualification.
