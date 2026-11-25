# B12 adapter and isolation interface review

Date: 2026-11-15 UTC  
Reviewer: `codex-release-dev`

## Result

I agree with Pi's acceptance criteria in `b12-adapter-isolation-interface-pi.md`. They match the scope in `b12-static-acceptance-root.md`. I have two additions for the implementation and its tests.

## Additions

- Timeout test: Start a local stub that starts a child process. After the timeout, examine that the adapter stopped the child too. Keep the stop reason and exit result in the record. Do not retry.
- Network boundary: Run the local stub tests with network access disabled, or prove that the test command cannot reach a provider. Do not use a real host request as a test. Keep provider authorization at zero.

The adapter record should retain the exact argument list and flags, exit code, stdout and stderr hashes, and measured elapsed time. Keep standard output and error contents out of retained logs when they can contain credentials. Do not record environment values.

## Acceptance

I agree that the batch must prove a successful control read and a blocked sentinel read. It must record the route, exact command, tool version, exit code, and observed error. It must refuse an unsupported route without a fallback pass. It must keep discovery, selection, trace, token usage, and execution status in separate fields. A missing host fact stays `unavailable`.

The freeze must include the adapter and isolation modules, test stubs, matrix, tests, and fixtures. Both reviewers must check the same frozen hashes. No provider calls, home configuration changes, or credential changes belong in this batch.

## Limits

The listed tool versions show presence only. They do not prove that a route can establish the required boundary. The adapter and isolation features need measured local evidence before acceptance.
