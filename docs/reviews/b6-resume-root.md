# B6 continuation instructions

Date: 2026-11-14. Status: combined interim correction list. Final review is pending.

Claude remains the implementation author. The account limit schedules continuation at 10:00 UTC. Do not change the model or billing settings. Preserve the failed trials and the accepted B5 files.

The accepted interface is `b6-consolidated-proposal-claude-r3.md`. The interim manifest is `b6-interim-files-root.sha256`. Neither the interim snapshot nor the earlier 19-pass log constitutes final B6 acceptance.

## Known incomplete work

1. Complete the native route. Compare applicable tool versions with the lock. A missing ngspice must not prevent ERC.
2. Use the staged input bytes for both tool execution and interpretation. The current staging helper addresses the initial separate-read problem. Examine the simulation assertions, which the command reads before staging.
3. Remove `normalized_equal` from GUI update publication. Retain it for automatic interface rebinding. An expected geometry edit can produce an intermediate board that needs routing.
4. Restrict the GUI adapter to the measured image identity. A matching KiCad version is insufficient.
5. Apply the worker caller conditions and focused negative tests. Compare the requested and measured options. Reject an absent or malformed summary, a forced stop, and a nonzero KiCad exit.
6. Do not reject unchanged PCB bytes for a valid no-edit operation. An expected edit that does not occur must fail its identity comparison.
7. Apply one placement filter to both the inventory and placement output. Add a slot or blind-via refusal fixture.
8. Correct the inventory docstring: structured error and refusal records use stdout. Preserve the worker behavior.

## Pi interim findings

The lead accepts F1 to F4, subject to the review agreement.

- F1: Implement copper function declarations from the measured copper order, including inner layers. Add focused four-layer and six-layer fixtures. Keep the accepted interface. Do not add support for blind or buried vias.
- F2: Remove only the wrapper-owned staging directory after successful publication and handled failures. Report residual staging directories during `check`. Preserve published raw evidence and the recorded failure history.
- F3: Use the agreed `uv run --no-project --no-config --offline --python /usr/bin/python3 python WORKER ARGS` form.
- F4: Apply the byte-copy test to the installed skill's README and schemas, not only synthetic fixtures. Retain the four unchanged helper copies.

The source contract README now uses explicit project and package placeholders. Keep its exact skill copy. Do not restore the scanner exception or remove the README.

## Codex interim findings and lead measurements

The lead accepts the five Codex findings in `b6-interim-review-codex.md`.

1. Parse simulation assertions from the staged snapshot. Do not calculate a decision from an earlier live parse.
2. Validate all assertion fields before use. Reject an empty list, incorrect types, duplicate keys, non-finite values, and blank identifiers. Malformed input gives exit 1 without a traceback.
3. Include confined simulation dependencies in the input closure, or refuse unsupported dependency syntax before execution. Never silently omit an input.
4. Include project-local libraries named by the library tables, including nested paths. Refuse unsupported or external dependencies explicitly. Keep the fixed system libraries under the runtime identity.
5. Validate the complete interface-review record on both write and read. Validate JSON pointers and the applicable coverage rule. A nonempty value alone does not constitute a review.

The lead ran `/tmp/cad-skills-b6-interim-probe.py` through `uv` on temporary template copies. No container command ran. The probe reproduced these results:

- A manual review with only matching hashes and a string-valued `examined` returns `(True, 'review')`.
- An automatic result with only the board hash and `status: pass` returns `(True, 'automatic')`.
- An increase of `height_limits.top_mm` leaves that automatic result accepted.
- An empty assertion list passes `load_assertions`.

All 65 interim file hashes still match after the probe. These measurements concern the helper functions, not a complete CLI readiness run.

Extend the interface correction to the automatic path. Bind the exact resulting interface bytes. Validate the result's necessary fields and its prior-board and expectation records. An interface edit must make the automatic result stale. Keep this a small skill record, without a new contracts registry.

The accepted command table includes `check --for export`. The interim parser omits it, and `check_report` does not compare published export bytes. Add the command and compare the current published files with their bound output hashes. Test a missing file and a changed file after a successful export. Do not demand an earlier export before the export command itself.

## Completion evidence

Finish the standalone installation test and one build of the bundled recipe within the existing image budget. Test the applicable commands and worker against the resulting image. Record the actual host and isolated paths. An old image test alone is insufficient. A new image digest does not certify the GUI adapter.

Complete the three agent trials and independently examine their artifacts. Retain the first failed trial and subsequent corrections. Finish the documentation and the focused tests. Then freeze the full file manifest for both reviewers.

Do not repeat unrelated B5 or mechanical suites. Report any remaining unsupported operation explicitly. This continuation record does not authorize a commit or publication.
