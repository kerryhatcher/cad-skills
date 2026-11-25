# B12 A1/A2 artifact connection: implementation record

Date: 2026-11-15 UTC. Author: `claude-release-dev`. Authority: `b12-artifact-connection-scope-pi.md`, accepted by the lead (2026-11-15 03:49 UTC).

## Changes

1. `tests/eval/matrix.yaml`: `artifact_checks.A1` and `artifact_checks.A2` hold `fixture_root`, `run_root` and `expectations`. A1 has 25 expectations. A2 has 7 expectations.
2. `tests/eval/check_artifacts.py`: new kinds `absent`, `json_path_equals` and `record_binding`. `json_equals` now requires the key to be present. Paths are refused when they are absolute, contain `..`, pass a link, or escape their root. A refused path fails every kind. `run_checks` takes an optional `run_root`.
3. `tests/test_artifact_expectations.py`: 11 focused tests. Two run the expectations on the frozen roots. Nine are negative cases: a changed interface byte, a complete A2 claim, a linked path, an escaping path, a dangling link, a missing key with a null expectation, an index out of range, a changed raw file, and a positive absent check.
4. `tests/test_release_harness.py`: the harness freeze reference (`FREEZE`) moves to `docs/reviews/b12-artifact-connection-freeze-claude.sha256`. The accepted local-repair freeze stays as history. Reason: the harness inputs now include the A1 and A2 fixture files, which that freeze does not list.

## Fixtures

The A1 and A2 fixture files are unchanged. Their hashes match freeze r2 (`7b01b363`).

## Results

- `tests/test_artifact_expectations.py`: 11 of 11.
- A2 remains incomplete. Its package path is absent. Its supplier step exits 1.

## Limits

- No provider call. Provider authorization stays zero.
- `json_equals` now fails on a missing key. This changes an existing kind. The harness mock tests that use it are rerun in this pass.
- The `record_binding` kind holds no fixed hash. It fits model-generated outputs.
