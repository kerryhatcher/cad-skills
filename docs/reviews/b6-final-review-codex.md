# B6 final review: Codex

Date: 2026-11-14 UTC. Scope: final frozen files, focused negative review, and selected agent records. This review does not cover Pi's runtime, export, GUI, or standalone assessment.

## Frozen bytes

The manifest `docs/reviews/b6-final-files.sha256` measures `d700afd728a13cd42948058cb6b1386bab8b69de0b6a15bcb409bf251160aebe`. The final record measures `7d198aff5a8b8a24d362ec165365386fc6ea40805db8de8ebe2306c1b3f9a758`. All 154 manifest entries passed before and after review. `pcb.py` measured `05e5b12db0af405151f2c23a0d2115a4cbe5fd4c3d6d7a5398f47fb671d79c07` after review. No implementation file changed during this review.

## Focused review and probes

Simulation now stages the closure before parsing assertions. The parser rejects empty and malformed assertion records, and the simulation path refuses unsupported dependency directives. Local project libraries enter the closure; unsupported external libraries refuse. Report checks bind result to binding, binding to raw bytes, and the closure to current inputs. `check --for export` checks published output files against result hashes. The automatic interface result binds the resulting interface bytes and required history and expectation records. Manual review validation checks record fields, pointers, and changed-pointer coverage.

I ran focused existing tests through `uv`: assertion failure outside tolerance, malformed duplicate assertions, manual review rejection, automatic interface rebind freshness, binding/result interruption mismatch, staged closure bytes, and changed/missing export outputs. Tests that call `pcb.py` use the existing container image. Therefore these were focused container-backed tests, not host-only tests. The selected tests passed: `test_sim_assertion_fails_outside_tolerance`, `test_review_with_string_examined_is_not_a_review`, `test_refill_matches_accepted_board_and_rebinds_interface`, and `test_check_export_detects_missing_and_changed_files`. I did not run a broad suite.

## Agent evidence and record accuracy

The final record names A4, B2, and C2 as the final Task A, Task B, and Task C outcomes. It preserves the failed A and A2 attempts and A3 as earlier evidence. A4 records GUI readiness with an identity-equal result and a saved trace. B2 records the manual route as not ready. C2 records refusal to move the part to another sheet. This matches the artifact and transcript names in the manifest. The trials are one run each and support only smoke-test claims.

One record correction: the final record says the supplier's requested V(1 ms) target appears in the test but does not include the target value in the trial summary. This does not change the artifact result, but the summary alone is not enough to reproduce the independent numerical assertion. The frozen example and test must carry that expected value.

## Decision

**I accept B6 within the frozen r3 scope, subject to Pi's separate runtime/export/GUI and standalone review.** The focused checks support the reviewed freshness, interface evidence, strict assertion records, and export-output integrity. This acceptance does not claim a native KiCad host test, broad repeated agent evaluation, or supplier qualification.

## Lead follow-up: RC and interface records

The root's independent RC probe uses the final A4 20 kohm circuit, changes only the measurement time to 1 ms in a temporary copy, and measures 1.298448 V against 1.2984 V with 0.012984 V tolerance. This supports the agreed independent target. It does not require another agent run.

I agree with the two interface concerns. `review_problems` validates that each listed pointer exists, but it does not compare `examined` with the changed pointers in the preserved prior interface. A matching-hash record can therefore omit a changed field and still pass readiness. Add read-time coverage validation using the preserved prior interface, with the all-top-level-key rule when no prior interface exists.

`automatic_problems` checks the result hashes and matching board-change record strings. It does not load and verify the prior board bytes or the predeclared expectation bytes. `interface_ready` must verify those preserved files against their full hashes and validate the expectation record before it accepts automatic readiness. A result with matching strings alone is incomplete evidence. Add focused tamper tests for a missing or altered prior board and expectation, and for a changed interface pointer omitted from `examined`.

The lead reproduced both false-ready cases with `uv run /tmp/cad-skills-b6-final-probe.py` on A4 copies. Case one uses a current manual review with only `/thickness_mm`, no prior interface, and no automatic result. `check` returned ready with exit 0. Case two removes the manual review and `out/reports/update.expect.json`; the automatic result still returned ready with exit 0. Probe output: `/tmp/cad-skills-b6-final-probe.json`.

These are concrete remaining defects in the final implementation. My earlier statement that manual pointer coverage and automatic expectation validation existed described code paths that do not establish the required read-time checks. The focused tests I ran did not cover these two cases. My acceptance is withdrawn pending the narrow corrections and focused regressions. The final frozen hashes will need a new review after correction.

## Assertion parser correction agreement

I agree with the complete root findings and the proposed narrow repair. The retained probe `docs/reviews/b6-assertion-probe-root.json` shows that `load_assertions` accepts duplicate JSON keys, accepts `vtau` followed by a newline as a measurement identifier, and raises an uncaught `OverflowError` for `expected=10**400`. These violate the agreed strict-record and identifier behavior and can produce a traceback instead of exit 1.

Reject duplicate JSON keys while parsing. Validate identifiers against the full string. Convert numeric range and type failures into `assertion.malformed` with exit 1 and no traceback. Preserve general integer acceptance from B1. Add CLI regressions for all three measured cases. Claude can make this repair with the interface evidence corrections in one pass. My blockers remain the two false-ready cases above and these assertion parser defects.

## Final correction-scope agreement

I agree with `b6-correction-scope-root.md` and have no conflict. For manual reviews, add `prior_interface_sha256` as a full hash or `null`. Preserve and hash-check the prior interface. Require changed-pointer coverage when a prior exists, and all top-level keys when the hash is `null`. Do not add a contracts-registry schema.

For automatic readiness, verify the prior PCB and predeclared expectation bytes against their full hashes and validate the expectation record. Keep exact resulting-interface-byte binding. Apply strict duplicate-key parsing and full-string hash rules to both interface evidence paths. Keep the agreed exit-1 policy for the accepted missing or stale evidence cases.

Also agree with the scope's staging, assertion, and prose corrections. A residual staging directory fails with exit 1, but an empty staging parent is valid. Remove only operation-owned temporary staging and preserve failure records. Reject duplicate assertion keys, invalid identifiers, and excessive numbers as `assertion.malformed`, exit 1, without traceback. Preserve B1 integer semantics. Include the retained independent 1 ms RC result. This remains a scoped agreement, not acceptance of corrected files.
