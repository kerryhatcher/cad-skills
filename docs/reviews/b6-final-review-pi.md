# B6 final review: Pi

Date: 2026-11-14.

**Decision: B6 is not final. The corrected files address most of the resume-root items, but two reproduced CLI false-ready cases block acceptance. The staging boundary needs a decision. The blind-via claim is incorrect.**

## 1. Reviewed bytes

| Item | Value |
|---|---|
| Manifest | `docs/reviews/b6-final-files.sha256`, 154 entries, `d700afd728a13cd42948058cb6b1386bab8b69de0b6a15bcb409bf251160aebe` |
| Manifest check | 154 of 154 `OK` before and after this review |
| Record | `docs/reviews/b6-final-record.md`, `7d198aff5a8b8a24d362ec165365386fc6ea40805db8de8ebe2306c1b3f9a758` |
| Design | `b6-consolidated-proposal-claude-r3.md`, `a46998a5a3f1b72c...c48f`; `b6-resume-root.md`, `110d2f84f98de8da...2cc6` |
| Main script | `skills/pcb-design/scripts/pcb.py`, `05e5b12db0af405151f2c23a0d2115a4cbe5fd4c3d6d7a5398f47fb671d79c07` |
| Workers | `board_inventory.py` `a3c2174936b1e59a...b7fe`; `gui_update.py` `7e953fead679f3e6...a18c` |
| Tests | `tests/test_pcb_design.py` `20c6bad526d63cef...2650` |
| Images | `localhost/cad-skills-pcb:b6` `b2731833...2a5f`; rebuild `localhost/cad-skills-pcb:b6-rebuild` `032582d4298bfe68...2285` |

I read the retained agent transcripts and reports. I did not rerun the 33-test suite, the rebuild isolation suite or the agent trials. I ran focused probes with the existing images and temporary copies. No pull, no implementation edit. `tests/test_pcb_design.py` runs image commands, so it is a container test suite even when invoked through `uv`.

## 2. Two CLI false-ready cases (blocking)

The root probe `/tmp/cad-skills-b6-final-probe.py` reproduced both on A4 copies; the result is `/tmp/cad-skills-b6-final-probe.json`.

| ID | Case | Result |
|---|---|---|
| R1 | A hand-written `mechanical/interface-review.json` with valid fields and current hashes, `examined` only `/thickness_mm`, no prior interface and no automatic result | `check --for ready` returns exit 0, `check: ready`. The coverage rule is not enforced on read. |
| R2 | The manual review and `out/reports/update.expect.json` removed, the automatic result still present | `check --for ready` returns exit 0, `check: ready`. The expectation file is not validated. |

**R1 cause.** `review_problems` validates the field set, the record, the two hashes, the reviewer, the pointers and the statement. It does not compute the required coverage. `record_review` computes the changed pointers and enforces `examined`, but that check runs only on write. A record written by hand or edited after the write is accepted on read. Correct: compute the changed pointers in the read path from the preserved prior interface at `out/history/interfaces/<prior interface_sha256>.json`, or require every top-level key when the prior interface is absent. `interface_ready` then returns `review_stale`.

**R2 cause.** `automatic_problems` validates the seven result fields, the status, the board hash, the interface-byte hash and the matching `board-changes.json` record. It does not read the `expect_file` of the matching record or compare its bytes with `expect_sha256`. Correct: resolve the matching record's `expect_file`, read it, and compare `sha(bytes)` with `expect_sha256`. A missing or changed file makes the automatic result stale.

Both cases contradict Codex finding 5 and the resume-root expectation-file check. Codex's report claims these checks exist and accepts. That claim is not correct for the read path. My review records the reproduced facts.

## 3. Verified corrections

- **F1 inner copper.** `export_subset` maps `copper_top` to `Copper,L1,Top`, each `copper_inner` to `Copper,L{index+1},Inr` and `copper_bottom` to `Copper,L{n},Bot`. A host probe on four- and six-layer synthetic contracts returned `Copper,L1,Top`, `Copper,L2,Inr`, `Copper,L3,Inr`, `Copper,L4,Bot` and the six-layer ladder. The `stack4` and `stack6` worker outputs show the expected `In1.Cu` to `In4.Cu` order.
- **F2 staging cleanup.** A successful `erc` on a temporary template copy left `out/staging` empty. A refused `sim` with an empty assertion list left `out/history/failures/sim-<token>/failure.json` and removed the staging. The wrapper removes only its own directory. See R3 for the residual policy.
- **F3 worker form.** Both workers run as `uv run --no-project --no-config --offline --python /usr/bin/python3 python /worker/...`.
- **F4 copy check.** `test_contract_copies_match_their_sources_byte_for_byte` compares the `contracts/README.md` and every schema byte. `test_copies_are_unchanged` keeps the four helper copies and the schema names.
- **Known items.** `normalized_equal` is removed from the GUI update and kept in `cmd_interface`. `gui_preflight` checks `GUI_IMAGE_IDS`. The simulation assertions load from the staged file and validate every field. A dependency directive is refused. `check --for export` and `export_problems` compare the published files with their bound output hashes; I confirmed a clean pass after `erc`/`drc`/`sim`/`export`.
- **Interface.** The automatic result now holds `interface_sha256`. A host probe shows a `height_limits.top_mm` change makes it stale. A history change makes it stale. The write path validates the review record and the pointers. R1 and R2 are the read-path gaps.

## 4. Export geometry, placement and the slot fixture

- The one `placement_filter` serves the export and the inventory. It preserves multiplicity (probe: a duplicate `R1` stays two rows).
- The slot fixture `tests/fixtures/pcb-design/slot.kicad_pcb` is refused by the worker with `{"object": "pad MH2.", "reason": "slot or oval drill"}` and exit 2. It satisfies the agreed slot-or-blind-via refusal fixture. The fixture hashes are unchanged.
- **Blind and buried vias.** The record says that the two-layer and the four- and six-layer boards cannot hold a blind or buried via. That is incorrect. A four- or six-layer board can hold a blind via (for example F.Cu to In1.Cu) or a buried via (In1.Cu to In2.Cu). The worker refuses any via whose span is not the first-to-last copper layer, so a future blind-via fixture on the four- or six-layer board can be refused. A separate blind-via test remains unmeasured, not impossible. Correct the record and `references/trial-limits.md`.

## 5. GUI caller and edit scope

- The GUI update relies on the identity comparison, not a blanket `pcb_changed` failure. A no-edit update with unchanged bytes is `equal` and passes. An expected edit that does not occur gives a `missing` difference and fails. This preserves the boundary: the unchanged board is valid, and the missing expected edit fails.
- The summary, forced-stop, nonzero-exit and option-mismatch paths are enforced.

## 6. Residual staging assessment (R3)

The final code prints `info staging.residual` for a remaining `out/staging/*` but does not add a problem, so `check` returns 0. `SKILL.md` line 33 says a residual staging directory is information. The accepted interim correction (F2) and the r3 section 9 say a leftover is a finding (exit 1). The wrapper now removes its own staging after success and after a handled failure, so a residual indicates an unhandled event. My assessment: make the residual a problem (`staging.residual`) that makes `check` return 1, keep the detail line, and update `SKILL.md`. If the lead intends information only, the interim correction must be changed explicitly. This preserves the boundary: normal runs are clean, and a residual is a failure.

## 7. Standalone rebuild and isolation

The rebuild image exists with the claimed ID `032582d4298bfe68...2285`. The record reports a `--no-cache` build with KiCad 10.0.5, ngspice 44.2 and uv 0.12.5, and isolated `env`, `erc`, `drc`, `sim`, `export` and `check` passes, with a lock mismatch, a different image and a GUI update each exit 2. I did not rerun that suite. A rebuilt image is not certified for the GUI adapter. The claim is consistent with the code.

## 8. Record and prose

- The record says the STE tools need the network through `uvx` or a dictionary download. The root review shows a local structural linter runs offline. Correct the record.
- The record's blind-via statement needs the correction in section 4.
- The record states the tests as `33 pass`; these are container tests.

## 9. Limits

- Focused probes only. I did not rerun the 33-test suite, the rebuild isolation suite or the agent trials.
- I did not test a true native host.
- I did not test a blind or buried via fixture.
- All reviewed repository hashes are unchanged. No implementation file was edited.

## 10. Verdict

B6 is not final. The corrected files resolve most of the resume-root scope. R1 and R2 are blocking read-path defects. R3 needs a boundary decision. The blind-via claim must be corrected. No implementation edit was made.

## 11. Complete root findings and assertion parser agreement

Date: 2026-11-14.

I read the updated `docs/reviews/b6-root-review.md` (`165295f5c8abda125cb0c2d8d1e80b3059c745fbd464a5957403a3324e33e364`) and `docs/reviews/b6-assertion-probe-root.json`. I agree with the complete root findings.

The root readiness defects match my section 2 and are blocking: the coverage fallback and the expectation-file comparison. The root prose corrections match my sections 4 and 8. The root RC assertion is closed independently.

### Assertion parser defects

The root probe confirms three parser defects in the frozen `load_assertions`.

| ID | Defect | Live cause |
|---|---|---|
| A1 | Duplicate JSON keys are accepted | `load_assertions` calls `json.loads`, which keeps the last duplicate value. The strict record parser rejects a duplicate key. |
| A2 | A `measurement` with a final newline is accepted | `IDENT` ends with `$`, and `re.match` accepts the match before a trailing newline. `CIRCUIT` has the same form. |
| A3 | `expected = 10**400` raises an uncaught `OverflowError` | `finite_number` calls `math.isfinite(10**400)`, which raises `OverflowError`. The `except` clause in `load_assertions` does not catch it. |

### Narrow repair

I agree with the lead's narrow repair:

- Reject a duplicate JSON key. Use the strict record parsing path or an object-pairs check.
- Validate the whole string for `measurement` and `circuit`. Use `fullmatch` or `\Z`.
- Treat a range or type failure of `expected` or `tolerance` as `assertion.malformed`, exit 1, with no traceback.
- Keep the B1 general contract parser's large-integer acceptance unchanged.
- Add CLI regressions for the three cases.

### Combined blockers

My blockers remain: R1 and R2 (blocking read-path false-ready cases), R3 (the staging boundary decision), R4 (the blind-via claim), and R5 (the STE tool claim). A1 to A3 are added to the combined correction scope. I agree that Claude can repair the combined scope once. No implementation edit was made.

## 12. Final combined correction scope agreement

Date: 2026-11-14.

I read `docs/reviews/b6-correction-scope-root.md`, SHA-256 `e1d5a18aec1f0c31676722ca4a2d879b10e2ab5e2fee81f6f8f4624ff7e337e4`. I agree with all five items and the focused acceptance cases. No concrete conflict.

- **1 Manual review coverage.** Enforce coverage on read and write. Add `prior_interface_sha256` (a full hash or `null`) to the local skill review record. Preserve the prior interface bytes before replacement. With a hash, read the preserved file and compare its hash before the changed pointers are calculated. With `null`, require every top-level key. A missing or altered named prior file fails. No contracts-registry schema.
- **2 Automatic evidence.** Read the prior board and the predeclared expectation file. Compare their bytes with the full recorded hashes. Validate the expectation record. Missing or altered evidence is exit 1. Keep the exact interface-byte binding.
- **3 Staging.** A residual staging directory is `staging.residual`, exit 1. An empty staging parent is not a defect. Preserve the published failure records. Remove only the current operation's disposable staging directory. This retains the agreed R3 exit 1 policy.
- **4 Assertions.** Reject duplicate JSON keys and prohibited identifier characters. Use whole-string identifier validation. A number outside the supported simulation measurement range gives `assertion.malformed`, exit 1, with no traceback. Keep the general contract parser's integer behavior unchanged.
- **5 Prose and records.** Correct the known-actor passive sentences, the semicolon and the long sentences in the new skill prose. Examine the technical-term lint findings individually. Correct the blind-via claim and the STE-tool claim. Include the retained independent 1 ms RC result.

Two implementation notes, not conflicts:

1. The prior interface file is `out/history/interfaces/<prior_interface_sha256>.json`. The read path (`interface_ready`) and the write path (`record_review`) must recompute the changed pointers from that preserved file. Do not trust a stored pointer list alone.
2. The strict record parsing (duplicate-key rejection) applies to the assertion file and to both interface evidence paths. Keep the B1 general contract parser's integer semantics unchanged.

I agree that Claude can apply one repair and freeze it. No implementation edit was made.

## 13. Native prerequisite probe (confirmed)

Date: 2026-11-14.

I ran one focused helper/stub probe with `uv` and no container. It confirms a native-prerequisite defect in `native_versions_ok`.

| Case | Result |
|---|---|
| Native `sim`, ngspice present, kicad-cli absent | `native_check("sim")` passes. `native_versions_ok(lock, "sim")` raises an uncaught `FileNotFoundError` on `kicad-cli`. |
| Native `erc`, kicad-cli present, ngspice absent | `native_check("erc")` passes. `native_versions_ok(lock, "erc")` passes; the missing ngspice is ignored. |

**Cause.** `native_versions_ok` calls `measure_tools(None)` for every operation. `measure_tools` always runs `kicad-cli version` first, whatever the operation. On a native host without `kicad-cli`, `subprocess.run(["kicad-cli", "version"])` raises `FileNotFoundError`. The ERC inverse survives because the ngspice probe uses a shell pipeline and its nonzero exit is recorded, not raised, and because `erc` does not check the ngspice version.

**Narrow correction.** Make the version probes operation-specific. `native_versions_ok` must measure only the tools in `OP_TOOLS[op]`, or call a per-tool version probe. A missing tool must give a `Refusal` with `runtime.native_unavailable` (exit 2), never an uncaught `FileNotFoundError`. Keep the per-operation `native_check` rule. Add focused tests for native `sim` without `kicad-cli` and native `erc` without `ngspice`.

This is the agreed per-operation capability rule, not a new feature. It is added to the combined B6 correction scope. No implementation edit was made.
