# B6 correction record (claude-skill-dev)

Date: 2026-11-14. Basis: `b6-correction-scope-root.md`, `b6-root-review.md`, the lead's probe findings, and the evidence retention request. This record replaces the final manifest for the corrected files. It does not replace history.

## History kept unchanged

- `b6-final-record.md` (revision of the earlier final record; its summary is superseded where this record differs).
- `b6-final-files.sha256` (154 entries). Some of its files changed in this correction, so their entries no longer match. That is intended.
- The trials in `b6-trials/`: A, A2, A3, A4, B, B2, C, C2 with their transcripts, exit files and stored reports.

## Corrections made

1. Manual review coverage. The review record has a new field `prior_interface_sha256`: a full SHA-256 value, or `null` when no prior exists. Coverage is enforced on write and on read. With a hash, the controller reads the preserved prior interface, checks its bytes against the hash, and computes the changed leaf pointers. With `null`, every top-level key must be covered. A missing or altered preserved prior fails readiness (exit 1). The template ships the preserved bytes of its own interface (`templates/rc-bare-board/out/history/interfaces/`) and writes `prior_interface_sha256: null`.
2. Automatic evidence. The automatic result carries the exact interface hash and the full prior-board and expectation hashes. Readiness reads the preserved prior board and the predeclared expectation, and compares their bytes with the full recorded hashes. A missing or altered file fails readiness (exit 1). A changed interface makes the result stale.
3. Strict parsing on every interface evidence path. The controller parses the interface, the review record, the automatic result, the board-change record and the expectation file with `strict_json`. A duplicate key is an error. A non-finite number is an error. A malformed hash is an error. The controller reports these as `interface.evidence_invalid` or `interface.review_invalid` (exit 1), without a traceback.
4. Staging. A residual per-operation staging directory under `out/staging/` is `staging.residual` (exit 1). An empty `out/staging/` parent is not a finding. The controller removes only the staging directories of the current process. Refused runs keep their logs under `out/history/failures/`.
5. Assertions. `assertions.json` is parsed strictly, so duplicate keys fail (`assertion.malformed`, exit 1). Identifiers and circuit names are matched as whole strings with `fullmatch`, so a trailing newline fails. A number that overflows a float or lies outside the simulation range (`|x| <= 1e12`) fails with `assertion.malformed` (exit 1), without a traceback. The general contract parser (`validate.py`) is unchanged.
6. Prose. The local structural linter (`/tmp/cad-skills-ste-lint.py`) ran through `uv` without network access. Before the correction it reported 42 findings, 7 of them hard (`b6-lint-before.txt`). After the correction it reports 0 (`b6-lint-final.txt`). Each finding was examined individually. Passive constructions with the controller or the operator as actor were made active. The synonym `delete` was replaced by `remove`. The semicolons and the long sentences were split. The linter is a structural check. It is not STE certification.
7. Blind-via statement. The earlier statement that four- and six-layer boards cannot hold blind or buried vias was wrong. Such boards can hold them. The worker refuses a via that does not span F.Cu to B.Cu (exit 2, named object). The slot fixture tests the slot refusal. A blind-via fixture is not yet measured. The blind-via refusal is therefore untested, not impossible.
8. Statement about STE tools. The earlier record said that the STE tools need a network connection or a dictionary download. That was wrong for the local structural linter, which ran without network access. The statement is removed here. No external STE checker was run.
9. Independent RC result. The retained independent measurement is `docs/reviews/b6-rc-review-root.json` and `b6-rc-review-root.log`, and it is recorded in `b6-root-review.md`. The circuit copy changed only the measurement time to 1 ms. The result is 1.298448 V. The predeclared target is 1.2984 V, with absolute tolerance 0.012984 V. The result passes. The A4 project asserts its own value at 2 ms, which is a deviation from the predeclared target. The deviation is recorded, and the 1 ms result closes the numerical assertion.

## Standalone evidence (retained, not rerun for this record)

`b6-standalone-evidence/INDEX.md` lists each command, its exit code and its logs. The commands ran on the rebuilt image `localhost/cad-skills-pcb:b6-rebuild` (ID `032582d4298bfe68b07fde9942c5a92148de90b4a7fe911c095799ffc1eb2285`) in the isolated copy under the scratchpad path named in the index. The logs record:

- `env`, `erc`, `drc`, `sim`, `export`, `check --for ready` and `check --for export`: exit 0.
- `update --adapter gui` on the rebuilt image, with and without an expectation file: exit 2 (`update.adapter_unavailable`, the image is not certified).
- Lock digest mismatch: `env` exits 2 with `lock_mismatch`. `erc` exits 2 with `runtime.image_mismatch`.
- Explicit different image: `env` exits 2 with `lock_mismatch`.

The raw simulation log that the simulation binding names is retained at `b6-standalone-evidence/project-out/reports/raw/`. The bindings and results are retained in the same folder.

## Tests and exits (captured directly, not through a filter)

- Affected B6 focused suite (`tests/test_pcb_design.py`): 41 passed, exit 0. Log: scratchpad `suite-correction.txt`, written by `echo SUITE_EXIT=$?` immediately after the command.
- Package-copy suite (`tests/test_skill_packages.py`): 8 passed, exit 0, run again after the prose change. Log: scratchpad `pkg-final.txt`.
- The new cases include: a manual record with only `/thickness_mm` and no prior (exit 1); a record that omits a changed leaf pointer of the preserved prior (exit 1); full coverage with current hashes (pass); a missing or altered preserved prior interface (exit 1); a missing or altered prior board or expectation file (exit 1); automatic evidence with unchanged files (pass); a residual staging directory (exit 1) and an empty parent (no finding); duplicate assertion keys, a measurement with a final newline and an excessive numeric value (exit 1, no traceback); a duplicate interface-evidence key and a malformed hash (not ready, no traceback).

## Remaining limits

- No agent trial was repeated for this correction, as instructed.
- The blind-via fixture is not measured.
- The local linter is structural. It is not an STE certification.
- The review record remains an acknowledgment, not machine proof.
