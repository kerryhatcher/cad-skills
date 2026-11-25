# A1/A2 artifact connection scope from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: the next compact implementation scope, to connect the accepted A1/A2 fixtures to the
matrix and the artifact checker. This report writes no product file. It does not commit. It
made no provider call.

## 1. Current state

- `tests/eval/matrix.yaml` holds `artifact_checks.A1` and `A2` with only `skill` and
  `freshness`.
- `tests/eval/check_artifacts.py` implements `exists`, `sha256`, `json_equals`, and
  `sha256_binding`.
- `tests/test_artifact_fixtures.py` checks the fixtures directly. It does not use the matrix
  expectations or the artifact checker.
- The A1/A2 fixture freeze r2 is 155 entries. The harness freeze r2 holds the matrix and the
  checker.

## 2. Proposed scope

| ID | Item |
|---|---|
| S-1 | Add `expectations` under `artifact_checks.A1` and `A2` in `tests/eval/matrix.yaml`. Each item has an `id`, a `kind`, a `path`, and the kind fields. The expectation data lives with the matrix |
| S-2 | Extend `tests/eval/check_artifacts.py` with two kinds: `json_path_equals` (a dotted key path) and `absent` (the path does not exist). Keep the existing kinds |
| S-3 | Add `tests/test_artifact_expectations.py`. It runs the matrix expectations against the frozen A1 and A2 fixture roots with the artifact checker. It calls no provider |
| S-4 | Keep A2 deliberately incomplete. The A2 expectations assert `overall == incomplete`, `commands.package == not run`, `commands.review-source == not run`, `supplier.exit == 1`, `mandatory_fail == [service.order_multiple]`, and `mandatory_pending == [silk_line_min_short_text]`. An `absent` item asserts that no package output exists |
| S-5 | Do not change any A1/A2 fixture file, any model, the trust state, or a credential |
| S-6 | Freeze the changed matrix, checker, and test. The A1/A2 fixture freeze stays at its hashes |
| S-7 | Codex and Pi review the new freeze |

## 3. A1 expectations

| Kind | Target | Check |
|---|---|---|
| `exists` | `mechanical/board-interface.json`, `expect/r2-value.json`, the four result records and their bindings | Present |
| `sha256_binding` | `out/reports/interface.result.json` key `prior_board_sha256`, reference `before/kicad/board.kicad_pcb` | The prior board hash equals the recorded value |
| `sha256_binding` | `out/reports/interface.result.json` key `expect_sha256`, reference `expect/r2-value.json` | The expectation hash equals the recorded value |
| `json_equals` | `out/reports/erc.result.json` key `status` value `pass` | ERC passes |
| `json_equals` | `out/reports/drc.result.json` key `status` value `pass` | DRC passes |
| `json_equals` | `out/reports/update.result.json` key `state` value `ready` | The update is ready |
| `json_equals` | `out/reports/update.result.json` key `identity` value `equal` | The identity compares equal |
| `sha256` | each raw file named by a binding | The bytes match the recorded hash |
| `json_equals` | `simulations/assertions.json` item 0 key `expected` value `1.298` | The independent value |

The identity reader check stays in `tests/test_artifact_fixtures.py`. The artifact checker
does not run a subprocess.

## 4. A2 expectations

| Kind | Target | Check |
|---|---|---|
| `json_equals` | `status.json` key `overall` value `incomplete` | The status is incomplete |
| `json_path_equals` | `status.json` path `commands.package` value `not run` | The package did not run |
| `json_path_equals` | `status.json` path `commands.review-source` value `not run` | The review-source did not run |
| `json_equals` | `project/out/fab/supplier/supplier-result.json` key `exit` value `1` | The supplier step exits 1 |
| `json_path_equals` | `status.json` path `supplier.mandatory_fail` value `["service.order_multiple"]` | The one mandatory failure |
| `json_path_equals` | `status.json` path `supplier.mandatory_pending` value `["silk_line_min_short_text"]` | The one pending condition |
| `absent` | `project/out/fab/package` or the package output directory | No package exists |

A2 is a valid negative fixture. It must not be changed to pass a complete package.

## 5. Acceptance criteria

| ID | Criterion |
|---|---|
| T-1 | The A1 expectation set passes against the frozen A1 after root |
| T-2 | The A2 expectation set passes and records the incomplete state |
| T-3 | A synthetic changed byte fails the matching expectation |
| T-4 | A synthetic "complete" A2 claim fails, because the package is absent and the status is incomplete |
| T-5 | No test makes a provider or network call |
| T-6 | The A1/A2 fixture hashes are unchanged from freeze r2 |
| T-7 | The new freeze holds the matrix, the checker, the test, and the fixture hashes |

## 6. Limits and non-goals

- No live artifact run. The provider authorization stays zero.
- No change to the A1/A2 frozen files.
- The `check --for ready` command exit stays a supplement, not an expectation.
- A3 waits for the PCBA skill.

## 7. Recommendation

1. The lead accepts this scope.
2. The author implements S-1 to S-6 and runs the focused test.
3. The author freezes the changed files.
4. Codex and Pi review the new freeze.
5. Provider authorization stays zero.

## Limits

This scope report reads the matrix, the checker, and the fixture test. It made no provider
call. It changed no product file.
