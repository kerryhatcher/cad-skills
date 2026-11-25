# B12 current state: correction of the authenticated-route checklist

Date: 2026-11-15 UTC. Author: `claude-release-dev`. Type: current-state record. This record changes no test, fixture or freeze.

## Corrections to the earlier checklist

1. Source-path normalization and its handoff are accepted and installed. The earlier checklist item that listed them as open is stale. The current freeze is `docs/reviews/b12-source-path-normalization-freeze-r3-claude.sha256` (text r3, `ffdfd389`). The normalized manifest `skills/pcb-fab-package/sources.yaml` has SHA-256 `fd415dc58ab60455c022112105905ede674ce389ba26b025ead80651dbee488f`. The handoff went to `w1P:p4`, with a copy to `w1P:p3`.
2. The local stub filesystem and sentinel boundary is implemented and accepted. The earlier "prototype limit" wording is stale for the local stub. `tests/eval/sandbox.py` probes the repository sentinel from inside the boundary, and `tests/test_release_isolation.py` tests it. The boundary covers the sentinel, the owned outside file and loopback-only networking. The authenticated route remains unmeasured.

## Live-provider functions missing from current source

Checked against `tests/eval/run_case.py`, `tests/eval/adapters.py` and `tests/eval/sandbox.py`:

- `run_case.live_provider(run)`: the only live entry point. It raises `ProviderNotAuthorized`. It makes no call.
- `run_case.execute(plan, ledger, root, provider=None)`: with no provider, every run is recorded as `not-executed`.
- Per-host live adapter: no function. `adapters.command_for` builds argv for Codex, Claude Code and Pi. It takes no model or credential argument, by design.
- Model selection: no function. The matrix pins a model per host, and no code passes it.
- Credential or authentication route: no function, by design. No real HOME is mounted.
- Provider egress route: no function. `sandbox._bwrap_args` uses `--unshare-all`, so the network is removed.
- Usage and token extraction: no function. `adapters.parse_output` returns `token_status` as unavailable. `run_case.USAGE_SOURCE` is host-reported.
- Discovery and selection parsing: no function. `parse_output` marks both unavailable.
- Host trace schema parser: no function. Trace lines are kept raw.

## Still open

- Authenticated host route: unmeasured.
- A3 PCBA: a 99-file batch is under review. It is not accepted.
- Final integrated skill inputs: pending.
- Provider authorization: zero.

## Limits

This record reads source and records only. It calls no provider, opens no credential file, prints no credential value and changes no trust setting.
