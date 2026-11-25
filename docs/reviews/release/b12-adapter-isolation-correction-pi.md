# Adapter and isolation correction agreement from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: agreement with
`docs/reviews/release/b12-adapter-isolation-review-codex.md` and the smallest correction
set. This report writes no product file. It does not commit. It made no provider call and
no network call.

## 1. Agreement

I agree with every Codex blocker and every additional correction. I reproduced each cause
in the frozen bytes.

| ID | Codex finding | My check |
|---|---|---|
| B-1 | The Codex command sets `--ignore-user-config` and `--ignore-rules` | Correct. Both flags are in `adapters.command_for`. They skip the user config and the execution rules. That changes the trust inputs |
| B-2 | The Claude Code command sets `--disable-slash-commands` | Correct. The flag disables skills and commands. The command cannot test skill discovery or invocation |
| B-3 | The boundary record redacts the argument list and has no `flags` field | Correct. `sandbox.probe_bwrap` records `bwrap <boundary args>`. `run_in_boundary` redacts the boundary arguments. No `flags` field exists |
| B-4 | The probe sends the sentinel error to `/work/probe-err.txt` and does not retain it | Correct. `probe_bwrap` writes the file. The record has the bwrap process `stderr_sha256`, not the probe error |
| B-5 | The timeout test does not exercise a child process | Correct. `stub.sh --sleep` calls `sleep`. Under `/bin/sh`, the shell can `exec` the last command. The test does not prove that a shell with a live child is stopped |
| A-1 | The home control uses `~/.bashrc` | Correct. A clean home can lack the file. This is my m3 |
| A-2 | The network test only reads source text | Correct. `test_adapter_makes_no_network_or_provider_import` checks import strings. It does not measure the namespace |

There is no conflict. The measured bwrap result on this host stays accepted at its scope.
The correction concerns the command builders and the record, not the boundary.

## 2. Smallest correction set

### C-1 Remove the trust bypass flags

Remove `--ignore-user-config` and `--ignore-rules` from the Codex command. Record the
effective trust state and the config or rules source that the run reads.

If reproducibility needs a clean config, use a temporary `HOME` with a project-authored
config. Record it as the trust state. Do not modify the real home.

### C-2 Remove the skill-disable flag

Remove `--disable-slash-commands` from the Claude Code command. Control skills by
installation. The temporary `HOME` keeps the real user skills absent. The baseline root
installs no skill.

### C-3 Record the exact safe argument list

Record the full argument list and a `flags` field. Include the boundary arguments and the
inside command. Record no credential value. A SHA-256 of the argv is an acceptable
addition, not a replacement.

### C-4 Retain the probe stderr

Read `/work/probe-err.txt` after the probe. Retain the text or its hash. Test it with the
exit code and the exact command.

### C-5 Test the child process timeout

Add a stub mode that starts a child and waits, for example `sleep 10 & wait`. Assert that
the timeout stops the child, that the record gives the stop reason and exit 124, that
`attempts` is 1, and that no retry occurs.

### C-6 Use a project-authored outside control file

Replace the `~/.bashrc` control with a project-authored file outside the run root. Assert
that it is readable outside and not readable inside the boundary.

### C-7 Add a local network-namespace test

Add a test that measures the network path inside the boundary. Use no external endpoint.

- Confirm the boundary uses `--unshare-all`, which includes the network namespace.
- Inside the boundary, list the network interfaces or read `/proc/net/dev`. Assert that no
  external interface exists. A loopback interface alone is acceptable.
- Do not connect to an external host. A loopback or non-loopback connect that fails in the
  boundary is acceptable local evidence.

## 3. Record fields

The corrected record carries:

| Fact | Field |
|---|---|
| Route | `route`, `host_version` |
| Boundary | `boundary_established`, `reason` |
| Command | `command`, `flags` (full safe argv) |
| Probe error | `probe_stderr`, `probe_stderr_sha256` |
| Process | `exit_code`, `stdout_sha256`, `stderr_sha256`, `elapsed_seconds` |
| Execution | `execution_status`, `stop_reason`, `attempts`, `automatic_retry` |
| Network | `network_interfaces` or `network_status` |
| Separation | `host_discovery_status`, `host_selection_status`, `trace_status`, `token_status` |

## 4. Scope

- Provider authorization stays zero.
- No provider call and no external network call.
- Preserve the assigned hosts, models, trust settings and credentials.
- Do not modify the user's home configuration.
- The packaging P-6 and P-7 acceptance does not extend to changed packaging files.
- The artifact fixtures, setup-fetch path and `pcba-design` snippet entry stay open.

## 5. Recommendation

1. Codex and Pi agree on C-1 to C-7.
2. The author applies C-1 to C-7 to a new candidate.
3. The author runs the focused local tests and freezes one coherent batch.
4. Both reviewers examine the new freeze.
5. The lead accepts. Provider authorization stays zero.

## Limits

This report compares the Codex findings with the frozen bytes. It made no provider call and
no network call. It changed no product file.
