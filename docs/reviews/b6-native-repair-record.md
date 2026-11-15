# B6 native probe and template-history repair (claude-skill-dev)

Date: 2026-11-14. Scope: the narrow repair agreed by both reviewers. Changes: operation-specific version probes (preflight and publication), exit 2 for a missing required tool without a traceback, and the template-only Git exception with a regression test. No B6 feature expansion.

## Changed paths and hashes

| Path | Before (210-file manifest) | After (replacement manifest) |
|---|---|---|
| `skills/pcb-design/scripts/pcb.py` | `98c7b1f5c01a807eac34d4e46032be7759c7aa2f15b71e356926aa2f183aaa3d` | `0928be463f6503b41d5c7ba02c076556c0ac750630da63ac8c86866cf664cabe` |
| `tests/test_pcb_design.py` | `c9a4d7faffb9956c6a85150f9ae5b0140918eb7fe36f03f5355afb7a234ca7fc` | `242176ead31847772750c58b224933178e2e1bc265ca8245909912de87aebe6c` |
| `.gitignore` (new in manifest) | not in manifest | `6b3a6acf3bb8b3ee922cbf3b7e9c57224a86226b04fae0b0ea5a9f89b1ac2a0c` |

The replacement manifest is `docs/reviews/b6-replacement-files.sha256` (211 entries, sha256 `f93454c545a355e43be3e447b41baa334299dbf09bb08fff4c57ab3f234aca39`). The 210-file manifest `b6-correction-files.sha256` (sha256 `ab6a32f676fb66ae28ccf7d1ff47e619e4f83506bf6210bc3fe7fd98e16e4b3d`) is kept as history.

## Repairs

1. `measure_tools(image, tools)` probes only the named tools. A missing executable is recorded as exit 127 with version None. It does not raise.
2. `native_versions_ok(lock, op)` probes only `OP_TOOLS[op]`. A needed tool that cannot be measured is `runtime.native_unavailable` (exit 2).
3. `tool_versions_of(image, op)` records only the operation's tools in publication bindings. The five publication calls pass the operation (erc, drc, sim, update, export).
4. `.gitignore`: the template-only negation sequence (out/ re-ignored under each parent before the next negation) from `b7-b8-r4-addendum-claude.md` section 3.

## Commands and exits (captured directly, not through a filter)

| Command | Exit |
|---|---|
| `uv run tests/test_pcb_design.py native` (3 tests: per-operation probes, in-image native route, host refusals) | 0 |
| `uv run tests/test_pcb_design.py gitignore` (1 test) | 0 |
| `uv run tests/test_pcb_design.py runtime` (2 tests) | 0 |
| `uv run tests/test_skill_packages.py` (8 tests) | 0 |
| `sha256sum -c docs/reviews/b6-replacement-files.sha256` (211 entries) | 0 |

The 41-test affected suite was not rerun, as instructed.

Logs: scratchpad `native-focused.txt`, `gitignore-focused.txt`, `runtime-focused.txt`, `pkg-after-native.txt`, `replacement-check.txt`.

## Limits

- The native route is tested inside the runtime image only. The host has no KiCad installation.
- The Git exception was checked in the scratch repository and in the real repository through `git check-ignore`. It is not yet committed. No commit was made.
