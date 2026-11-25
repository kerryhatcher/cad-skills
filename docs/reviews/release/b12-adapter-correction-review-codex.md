# B12 adapter correction freeze review

Date: 2026-11-15 UTC  
Reviewer: `codex-release-dev`  
Freeze: `docs/reviews/b12-adapter-correction-freeze-claude.sha256`  
Freeze SHA-256: `316f392cdb0ddd2ccb5e5b399d1053d0aac0e033d35fca5c016703a0eb5e7bbf`

## Result

All 41 hashes match before and after the focused tests. The measured `bwrap` boundary and local network isolation pass on this host. The focused tests pass. I found three remaining blockers in the baseline and timeout gates.

## Blockers

- B-1: `adapters.baseline_policy("codex")` returns `refused-for-measured-evaluation`, but the plan and executor do not use this policy. `run_case.plan_runs` marks runs only from fixture readiness and batch authorization. The mock open-matrix test dispatches all 210 entries. Add a plan or dispatch gate for a Codex baseline whose host skill set is unmeasured. Add a test that proves it cannot reach the adapter even when other gates open.
- B-2: `command_for("pi", mode="none", skill_paths=[...])` adds both `--no-skills` and the supplied `--skill` arguments. Reject skill paths in baseline mode or omit them. Add a test with a nonempty `skill_paths` value.
- B-3: `test_adapter_child_ticks_before_timeout_and_stops_after` takes its first post-return tick count immediately, before the 1.5 second wait. It does not sample the child while it runs, so it does not prove the assigned event order. Run the stub in a background thread and poll for at least two increasing live tick samples. Then take the immediate post-return count and the later count. Require the two post-return counts to match.

## Verified corrections

- Codex commands keep the host configuration and rules. They do not set a sandbox permission override.
- Claude skill runs keep skills enabled. The baseline records that `--disable-slash-commands` disables both skills and commands.
- The stub boundary uses a temporary `HOME` and does not mount the real `HOME`. Host configuration and credential behavior remain unmeasured.
- The boundary record holds the full argv, flags, hashes, and probe error text. The owned outside control file is readable outside and hidden inside.
- The network tests show only loopback inside the boundary. A local listener accepts connections outside and refuses them inside.
- The network test uses no external endpoint. No provider call occurred.
- Packaging P-6 and P-7 remain accepted separately at their unchanged hashes.

## Focused local checks

- `uv run tests/test_release_isolation.py`: 27/27 passed.
- `uv run tests/test_release_harness.py`: 64/64 passed.
- `uv run tests/test_release_packaging.py`: 25/25 passed.
- `uv run tests/test_skill_packages.py`: 8/8 passed.
- `uv run tests/test_project_io.py`: 11/11 passed.
- `sha256sum -c docs/reviews/b12-adapter-correction-freeze-claude.sha256`: 41/41 matched after the checks.

These checks use local stubs. They do not measure an authenticated host route. Provider authorization remains zero.
