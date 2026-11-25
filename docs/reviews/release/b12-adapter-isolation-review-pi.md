# Adapter and isolation batch review from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: review of `docs/reviews/b12-adapter-isolation-freeze-claude.sha256` against the
criteria I-1 to I-4, A-1 to A-5, S-1 to S-4 and F-1 to F-3 in
`docs/reviews/release/b12-adapter-isolation-interface-pi.md`. This report writes no
product file. It does not commit. It made no provider call and no network call.

## 1. Freeze and hashes

The freeze file `docs/reviews/b12-adapter-isolation-freeze-claude.sha256` has SHA-256
`bea9e6d07c71430296cc9a10013a4055941416d704c12e53d7b47ff157930ff3`. It matches the
author message.

| Item | Before | After |
|---|---|---|
| Entries | 41 | 41 |
| `sha256sum -c` | 41 of 41 OK | 41 of 41 OK |
| Freeze file hash | `bea9e6d0...` | `bea9e6d0...` |

The new modules and fixtures are in the freeze:

| File | SHA-256 |
|---|---|
| `tests/eval/sandbox.py` | `af9be75323ea15437b737a13b3e3d330b96e1708a01fd7504c82b8d09d6f3809` |
| `tests/eval/adapters.py` | `0b70c58661445af2b3da24e53fc0e5ea800808c05df403b512e94238097f3a93` |
| `tests/test_release_isolation.py` | `f1083601bd09c60b5bebcb8daca00ca246aa3c6c98f20880809f1da151954f1e` |

## 2. Tests reproduced

| Command | Result |
|---|---|
| `uv run tests/test_release_isolation.py` | 18 of 18 passed, exit 0 |
| `uv run tests/test_release_harness.py` | 64 of 64 passed, exit 0 |
| `uv run tests/test_release_packaging.py` | 25 of 25 passed, exit 0 |
| `uv run tests/test_skill_packages.py` | 8 of 8 passed, exit 0 |
| `uv run tests/test_project_io.py` | 11 of 11 passed, exit 0 |

No provider call and no network call was made.

## 3. Criterion check

### Filesystem boundary

| ID | Result |
|---|---|
| I-1 | Pass. The control reads `README.md` outside the boundary |
| I-2 | Pass. The measured probe establishes the bwrap boundary. The sentinel is hidden inside and the run root is readable |
| I-3 | Pass. `unshare` alone is refused with a reason. A failed probe refuses the operation before the subprocess starts. A refused run is not a pass |
| I-4 | Pass in part. The route, the host version, the exit code, the output hashes and the elapsed time are recorded. The boundary arguments are redacted. See m1 |

Measured boundary on this host: bwrap 0.13.1. The repository is not mounted. The user
home configuration is not visible inside.

### Process and output adapters

| ID | Result |
|---|---|
| A-1 | Pass. Command, exit code, stdout and stderr hashes, and measured time are recorded |
| A-2 | Pass. The timeout utility stops a long stub with exit 124 and a stop reason. One attempt. No automatic retry |
| A-3 | Pass. A missing host binary is `unavailable`, not a pass |
| A-4 | Pass. A failing process keeps its output and is not retried |
| A-5 | Pass. `adapters.py` and `sandbox.py` import no network library and no provider SDK. The boundary uses `--unshare-all` |

I checked the command flags against the real installed CLI help:

| Host | Flags in the argv that appear in the installed help |
|---|---|
| Codex 0.169.0 | `--json`, `--ephemeral`, `--ignore-user-config`, `--ignore-rules`, `--skip-git-repo-check`, `-s` |
| Claude Code 2.1.325 | `-p`, `--output-format`, `stream-json`, `--no-session-persistence`, `--disable-slash-commands`, `--add-dir` |
| Pi 1.5.2 | `-p`, `--mode`, `--no-session`, `--offline`, `--no-skills`, `--skill` |

No model flag and no credential is set.

### Separation rules

| ID | Result |
|---|---|
| S-1 | Pass. Discovery, selection, trace, token usage and execution status are separate fields |
| S-2 | Pass. A fact without measured output is `unavailable` |
| S-3 | Pass. A local scan is not scored as host selection |
| S-4 | Pass. Process time is measured by the adapter |

### Freeze

| ID | Result |
|---|---|
| F-1 | Pass. The freeze holds every module, the matrix files, the tests, the CLI help fixtures and the stub |
| F-2 | Pass. Both reviewers examine the same frozen bytes |
| F-3 | Pass. `test_mock_freeze_lists_every_harness_input` requires `tests/eval/*.py`, `tests/eval/*.yaml`, `tests/eval/fixtures/**`, the three release test files, and the shared files |

## 4. Minor findings

### m1 The boundary arguments are redacted in the command record

`sandbox.probe_bwrap` and `sandbox.run_in_boundary` record a command of the form
`bwrap <boundary args> ...`. The exact argv is not retained. The boundary arguments
contain only paths, so no secret is exposed.

Correction: record the full argv, or a SHA-256 of the argv, in the record.

### m2 The isolation suite is host-specific

`test_boundary_bwrap_route_is_established_on_this_host` requires a working bwrap. On a
host without bwrap or without the needed kernel feature, the test fails. This matches the
refuse rule, but it makes the suite host-dependent.

Correction: record the host requirement in the suite docstring and in the CI note. Do not
weaken the assertion.

### m3 The home control uses a real user file

`test_boundary_home_configuration_is_not_visible` uses `~/.bashrc` as the control. A host
without that file fails the control.

Correction: write a project-authored control file in the run root and read it outside and
inside the boundary, instead of the user's file.

## 5. Open items

- No live provider adapter exists. Dispatch stays refused.
- The artifact fixtures are not frozen.
- The setup-fetch path is not implemented.
- The `pcba-design` snippet routing entry remains pending for integration.
- Provider authorization is zero.

## 6. Verdict

I-1 to I-4, A-1 to A-5, S-1 to S-4 and F-1 to F-3 pass. The measured boundary is
established on this host. The adapter records the required facts and refuses a failed
route. The minor findings m1 to m3 do not block acceptance.

I recommend the lead accept the adapter and isolation batch at freeze
`bea9e6d07c71430296cc9a10013a4055941416d704c12e53d7b47ff157930ff3`. Provider dispatch
stays unauthorized.

I made no edit during this review.

## Limits

This review ran focused local checks and read the installed CLI help. It made no provider
call and no CAD call. It changed no product file. It does not approve a release.
