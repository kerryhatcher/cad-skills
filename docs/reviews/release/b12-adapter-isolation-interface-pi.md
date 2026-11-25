# Adapter and isolation interface from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: reviewer record of the r2 acceptance and the next bounded scope. It gives the
acceptance criteria for the adapter and isolation batch. This report writes no product
file. It does not commit. It made no provider call.

## 1. Acceptance of the local harness correction

I agree with the acceptance in `docs/reviews/release/b12-static-acceptance-root.md`.

| Item | Value |
|---|---|
| Freeze | `docs/reviews/b12-harness-freeze-claude-r2.sha256` |
| Freeze SHA-256 | `09e77fa0f2d280f23918f1fd02b8afd5fd557e90b6b147932a1cb2a5897c32a6` |
| Entries | 33, all match |
| Harness tests | 64 |
| Packaging acceptance | Separate, retained |

The corrected freeze still matches after the acceptance. The first freeze stays as
history. Provider authorization is zero.

## 2. Host tools, measured presence

| Tool | Path | Version |
|---|---|---|
| `bwrap` | `/usr/bin/bwrap` | bubblewrap 0.13.1 |
| `unshare` | `/usr/bin/unshare` | util-linux 2.42.4 |
| `timeout` | `/usr/bin/timeout` | GNU coreutils 9.11 |

Presence does not prove that the isolation features work. The batch must measure the
supported route. A route whose boundary cannot be established is refused, not passed.

## 3. Next scope

Claude implements:

1. Local host adapters for the process and the output.
2. The measured filesystem boundary and the repository sentinel test.

The batch uses installed CLI help, the retained harness research, and local stubs. It
makes no provider call.

## 4. Acceptance criteria for the batch

### Filesystem boundary

| ID | Case | Expected result |
|---|---|---|
| I-1 | A control read of the repository sentinel without the boundary | The read succeeds. This proves the sentinel is reachable and the test is meaningful |
| I-2 | The boundary route (`bwrap` or `unshare`) around a subprocess | The subprocess cannot read the repository sentinel. The refusal is recorded with the command, the exit code and the observed error |
| I-3 | A route whose isolation feature is unsupported | The operation is refused and recorded. It is not a pass and it is not a silentry fallback |
| I-4 | The record | Names the route, the exact command, the host version, and whether the boundary was established |

The boundary must not change trust, credentials, models, or the user's home
configuration. Do not print a credential or put one in a retained log.

### Process and output adapters

| ID | Case | Expected result |
|---|---|---|
| A-1 | A local stub process | The adapter records the command, the flags, the exit code, the stdout hash, the stderr hash, and the measured wall-clock time |
| A-2 | A long stub with `timeout` | The adapter stops the process, records the stop reason, and does not retry automatically |
| A-3 | A missing host or adapter | The fact is recorded as `unavailable`, not as a pass or a fail |
| A-4 | A failing process | The failure stays on disk. A retry needs a new plan entry |
| A-5 | A provider call | No adapter can make one. The batch calls no provider and no network |

### Separation rules

| ID | Rule |
|---|---|
| S-1 | Discovery, skill selection, trace availability, token usage, and execution status stay separate fields |
| S-2 | A host that cannot report a fact records it as unavailable |
| S-3 | A local scan is a file inventory. It is not host discovery or selection |
| S-4 | Process time is measured by the adapter. It is not inferred |

### Freeze

| ID | Rule |
|---|---|
| F-1 | One coherent freeze holds every adapter and isolation module, its stubs, the matrix, the tests, and the fixtures |
| F-2 | Both reviewers examine the same frozen bytes |
| F-3 | The freeze test requires every harness input, including the adapter and isolation modules |

## 5. Out of scope for this batch

- The pending artifact fixtures.
- The setup-fetch path.
- The `pcba-design` snippet routing entry, which belongs to integration.
- Any provider dispatch.

## 6. Recommendation

1. Claude implements the boundary first and records the measured result.
2. Claude implements the adapters with local stubs.
3. Claude runs the focused local tests and freezes one batch.
4. Codex and Pi review the same freeze.
5. The lead accepts. Provider authorization stays zero.

## Limits

This record reads the acceptance and checks three tool versions. It does not test the
isolation features. It does not approve the batch.
