# Adapter correction review from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: review of the replacement freeze
`docs/reviews/b12-adapter-correction-freeze-claude.sha256` against the release
`docs/reviews/release/b12-adapter-correction-release-root.md`. This report writes no
product file. It does not commit. It made no provider call and no network call beyond the
local listener in the suite.

## 1. Freeze and hashes

The freeze file `docs/reviews/b12-adapter-correction-freeze-claude.sha256` has SHA-256
`316f392cdb0ddd2ccb5e5b399d1053d0aac0e033d35fca5c016703a0eb5e7bbf`. It matches the author
message.

| Item | Before | After |
|---|---|---|
| Entries | 41 | 41 |
| `sha256sum -c` | 41 of 41 OK | 41 of 41 OK |
| Freeze file hash | `316f392c...` | `316f392c...` |

The earlier 41-entry freeze stays as history.

Key file hashes:

| File | SHA-256 |
|---|---|
| `tests/eval/sandbox.py` | `b2fc1c4c362f66ad97bbee3aa138574abeb6a7d6c0a632115ebdfd06e35b38c5` |
| `tests/eval/adapters.py` | `c34cc7c03c1f66f4bd85547c94c8093df4a73ff02d83c0740297302d978f1aa1` |
| `tests/eval/fixtures/stub/stub.sh` | `d6b999b6ddea1e81e0e553d49481c15b46d65df117558e5041380ef4664976ea` |
| `tests/test_release_isolation.py` | `048c790393f84f383e031c537fbf1d6a4d4d261cc1fd1122faad29f31f3c2241` |
| `tests/test_release_harness.py` | `c7d6029e56222052edfd3d937c191465a2293158ff2b9e5652ec6da99f344b74` |

## 2. Tests reproduced

| Command | Result |
|---|---|
| `uv run tests/test_release_isolation.py` | 27 of 27 passed, exit 0 |
| `uv run tests/test_release_harness.py` | 64 of 64 passed, exit 0 |
| `uv run tests/test_release_packaging.py` | 25 of 25 passed, exit 0 |
| `uv run tests/test_skill_packages.py` | 8 of 8 passed, exit 0 |
| `uv run tests/test_project_io.py` | 11 of 11 passed, exit 0 |

## 3. Release item check

| Item | Result |
|---|---|
| Remove the Codex trust flags | Pass. No `--ignore-user-config` and no `--ignore-rules` |
| Remove the workspace permission override | Pass. No `-s workspace-write`. The host default is recorded as unmeasured |
| Keep skills enabled for skill runs | Pass. The Claude skill command has no disable flag |
| Claude baseline disclosure | Pass. `--disable-slash-commands` appears only in baseline mode. The policy states that it disables and does not remove |
| Codex baseline | Pass. The policy is `refused-for-measured-evaluation` |
| Temporary HOME | Pass. It exists only inside the stub boundary. No real `HOME` is mounted |
| No HOME or config override | Pass. No host command sets `HOME` or `--setenv` |
| Full safe argv, flags and hashes | Pass. `argv`, `flags`, `argv_sha256` and `command` are recorded |
| Probe stderr | Pass. `probe_stderr` and `probe_stderr_sha256` are recorded |
| Owned outside control file | Pass. `test_boundary_owned_outside_control_file_is_hidden_inside` |
| Network interfaces | Pass. Inside the boundary only `lo` is visible |
| Local listener | Pass. The listener is reachable outside and unreachable inside. No external endpoint |
| Child tick proof | Pass. Ticks appear before the timeout, the count stops after, the interval is 1.5 s, the stop reason is exit 124, one attempt and no retry |
| One replacement freeze | Pass. The earlier freeze is preserved |

The measured boundary stays accepted at its scope: bwrap 0.13.1, sentinel hidden inside,
readable outside, run root readable.

## 4. Minor findings

### m1 The Pi baseline still attaches a skill

`adapters.command_for` adds `--skill <path>` for each `skill_paths` entry in every mode. A
baseline call that passes `skill_paths` gets `--no-skills` and `--skill` together. The real
caller passes no paths, so the current behavior is safe. The test
`test_adapter_command_flags_come_from_installed_help` passes paths in baseline mode.

Correction: attach `--skill` only in skill mode. Add a test that the baseline argv has no
`--skill`.

### m2 The Codex baseline refusal is a policy record

`baseline_policy` states the refusal. The plan and the dispatch path do not yet consult it.
A future measured baseline could build the Codex command without the gate.

Correction: before any measured baseline, the dispatch path reads `baseline_policy` and
refuses the Codex baseline with a recorded reason. No provider run exists now, so this is a
wiring note.

### m3 The listener test needs bash inside the boundary

The stub uses `/bin/bash` and `/dev/tcp` for the listener connect. The host has bash. A
boundary host without bash fails the test.

Correction: note the bash requirement in the suite docstring, or use a portable connect
inside the stub.

## 5. Open items

- No live provider adapter exists. Dispatch stays refused.
- The authenticated host route is not established. Credential and configuration
  preservation is unmeasured for that route.
- The artifact fixtures are not frozen.
- The setup-fetch path is not implemented.
- The `pcba-design` snippet entry stays pending for integration.
- Provider authorization is zero.

## 6. Verdict

The release items are applied and verified. The freeze has 41 entries and all match. The
local suites pass. The minor findings m1 to m3 do not block acceptance.

I recommend the lead accept the replacement freeze at
`316f392cdb0ddd2ccb5e5b399d1053d0aac0e033d35fca5c016703a0eb5e7bbf`. Provider dispatch
stays unauthorized.

I made no edit during this review.

## Limits

This review ran focused local checks. It made no provider call and no CAD call. It changed
no product file. It does not approve a release.
