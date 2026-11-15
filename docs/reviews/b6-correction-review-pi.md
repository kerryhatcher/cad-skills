# B6 correction review: Pi

Date: 2026-11-14.

**Decision: the correction resolves the agreed readiness, parser, staging and prose scope. Two stated items remain for the final narrow repair: the native version-probe gap and the template packaging finding. Accept the corrected scope with those two items.**

## 1. Reviewed bytes

| Item | Value |
|---|---|
| Correction manifest | `docs/reviews/b6-correction-files.sha256`, 210 entries, `ab6a32f676fb66ae28ccf7d1ff47e619e4f83506bf6210bc3fe7fd98e16e4b3d` |
| Manifest check | 210 of 210 `OK` before and after this review |
| Correction record | `docs/reviews/b6-correction-record.md`, `d021a48200f0cd0857697bf5effa64da03caa877f19daaaaff48316edbaf782b` |
| Controller | `skills/pcb-design/scripts/pcb.py`, `98c7b1f5c01a807eac34d4e46032be7759c7aa2f15b71e356926aa2f183aaa3d` |
| Workers | `board_inventory.py` `a3c2174936b1e59a...b7fe`; `gui_update.py` `7e953fead679f3e6...a18c` (unchanged) |
| Tests | `tests/test_pcb_design.py`, `c9a4d7faffb9956c6a85150f9ae5b0140918eb7fe36f03f5355afb7a234ca7fc` |
| Standalone index | `docs/reviews/b6-standalone-evidence/INDEX.md`, `71c897fc98279e514e1da437c7836b798a270924cf28b0e9a820807c39f5b79c` |
| History | `b6-final-files.sha256` `d700afd7...`; `b6-final-record.md` `7d198aff...` |

I did not rerun the 41-test suite or the GUI. The root readiness, assertion and STE probes pass at this revision. I ran the focused regressions below with the existing images and temporary copies.

## 2. Corrections verified

- **Manual review coverage.** `review_problems` enforces coverage on read. The record has `prior_interface_sha256` (a full hash or `null`). With a hash, it reads `out/history/interfaces/<hash>.json` through `preserved_interface`, checks the bytes, parses with `strict_json`, computes `pointers_differing` and requires `examined` to cover the changed pointers. With `null`, it requires every top-level key. A missing or altered preserved file fails. The template ships `prior_interface_sha256: null` and all 15 top-level keys.
- **Automatic evidence.** `automatic_problems` checks the seven result fields, the hashes, the preserved prior board bytes, the strict `board-changes.json` record, and the `expect_file` bytes against `expect_sha256`. A missing or altered file fails. The `interface_sha256` binding stays.
- **Strict parsing.** `strict_json` rejects a duplicate key and a non-finite number. It parses the interface, the review record, the automatic result, the board-change record and the expectation file. Failures are `interface.evidence_invalid` or `interface.review_invalid`, exit 1, with no traceback.
- **Staging.** `cmd_check` adds `staging.residual` (exit 1) for each residual directory under `out/staging/`. An empty parent is not a finding. `cleanup_staging` removes only the current process's staging dirs. A refused run keeps its logs under `out/history/failures/`.
- **Assertions.** `load_assertions` uses `strict_json`, `fullmatch` for `circuit` and `measurement`, and `finite_number`. `finite_number` catches `OverflowError` and requires `abs(number) <= 1e12`. The general contract parser is unchanged.
- **Prose and records.** `b6-lint-final.txt` shows 0 findings after 42 before. The blind-via statement is corrected; the slot fixture covers the slot-or-blind-via request; a blind-via fixture is untested, not impossible. The STE-tool claim is removed. The retained 1 ms RC result is 1.298448 V against 1.2984 V.

## 3. Focused independent regressions

| Probe | Result |
|---|---|
| Root readiness probe re-run (`/tmp/cad-skills-b6-final-probe.py`) | Both cases now exit 1: `interface.review_stale` and `interface.geometry_stale`. |
| Root assertion probe re-run (`/tmp/cad-skills-b6-assertion-probe.py`) | All three cases give `assertion.malformed`, exit 1: duplicate key, measurement with a final newline, `expected = 10**400`. |
| Staging residual | A residual `out/staging/residual/` gives exit 1 and `staging.residual`. An empty `out/staging/` gives no `staging.residual`. |
| Template no-prior | Remove `out/history/interfaces/`; `interface_ready` returns `(True, "review")`. The `null` prior plus full coverage works. |
| Native publication caller | `tool_versions_of(None)` raises an uncaught `FileNotFoundError` on `kicad-cli`. |

## 4. Retained standalone evidence

`b6-standalone-evidence/INDEX.md` names each command, exit code and log. The rebuilt image `localhost/cad-skills-pcb:b6-rebuild` (`032582d4298bfe68...2285`) ran `env`, `erc`, `drc`, `sim`, `export`, `check --for ready` and `check --for export` with exit 0. A GUI update on the rebuilt image exits 2 with `update.adapter_unavailable`. A lock digest mismatch gives exit 2. The raw simulation log and the bindings are retained. I read the index and logs; I did not rerun them.

## 5. Remaining item 1: native version-probe gap

The lead accepted my finding and extended it to the publication callers. Confirmed by a focused stub probe:

- Native `sim`, ngspice present, kicad-cli absent: `native_check("sim")` passes; `native_versions_ok(lock, "sim")` raises an uncaught `FileNotFoundError`.
- `tool_versions_of(None)` also raises an uncaught `FileNotFoundError`. It is called in the publication path of `erc`, `drc`, `sim`, `export` and the GUI update.

Cause: `native_versions_ok` and `tool_versions_of`/`measure_tools` run every tool, and `measure_tools` runs `kicad-cli version` first. Narrow correction: make the version probes operation-specific. A missing tool gives `Refusal` `runtime.native_unavailable`, exit 2, never `FileNotFoundError`. Add focused tests for native `sim` without `kicad-cli` and native `erc` without `ngspice`.

## 6. Remaining item 2: template packaging

The manifest lists `skills/pcb-design/templates/rc-bare-board/out/history/interfaces/5254508d3d203f0870b57b611cc70b47dfe4fb4d4c23aaee8287e2fe73a3b4bc.json`. `git check-ignore -v` returns `.gitignore:229:out/` for this path. The correction record says "The template ships the preserved bytes of its own interface." That claim is inaccurate. The file cannot be shipped under the current ignore rule, and the template does not need it: the review record has `prior_interface_sha256: null` and covers all top-level keys, and my probe confirms `interface_ready` returns `("review")` without the preserved file.

Narrow solution: remove the generated template artifact and prove the no-prior initialization works, or add an exact template-only source exception plus a git-inclusion regression. Do not broadly unignore `out/`. Correct the record claim.

## 7. Manifest and history

The correction manifest is current and verifies 210 of 210. The final manifest `d700afd7...` is stale for the 11 changed files and stays as history. The final record and the agent trials stay unchanged.

## 8. Limits

- I did not rerun the 41-test suite, the standalone suite or the GUI, as instructed.
- The 41-test result is the record's captured log. The two worker files are unchanged from the accepted worker review.
- The blind-via fixture is not measured.
- No implementation edit was made. All reviewed hashes are unchanged.

## 9. Verdict

The corrected scope resolves the agreed readiness, parser, staging and prose corrections. The native version-probe gap and the template packaging finding remain. I accept the corrected scope and the two narrow repairs. No implementation edit was made.
