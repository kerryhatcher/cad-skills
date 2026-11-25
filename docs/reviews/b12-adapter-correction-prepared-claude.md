# B12 adapter and isolation narrow correction (prepared, not applied)

Date: 2026-11-15 UTC.
Author: `claude-release-dev` (Claude, assigned model Haiku 5.5).
Status: prepared plan. No product file is changed. The frozen set `docs/reviews/b12-adapter-isolation-freeze-claude.sha256` (41 entries, SHA-256 `bea9e6d0…ff157930ff3`) stays as it is until Pi's conflict check and the lead's release.

Source blockers: Codex `docs/reviews/release/b12-adapter-isolation-review-codex.md`. Accepted by the lead at 02:45 UTC. Pi's review of the same batch: `docs/reviews/release/b12-adapter-isolation-review-pi.md` (minors m1 to m3).

## 1. Items and exact changes

### C-1 Preserve host rules and configuration (blocker)

- `tests/eval/adapters.py`, Codex branch of `command_for`: remove `--ignore-user-config` and `--ignore-rules`. The installed help says these skip user configuration and execution rules. Both change the trust input.
- The same branch sets `-s workspace-write`. That flag sets the sandbox permission mode. It is a permission input, so it is removed too. The host default stays. (Decision D-1 for the lead: keep the host default, the proposal.)
- `--ephemeral` controls only session persistence. It stays. Record it as a persistence setting, not a trust setting.

### C-2 Skills enabled for skill runs; separate empty baseline (blocker)

- Claude Code branch: remove `--disable-slash-commands` from skill mode. Skill mode keeps all skills and commands available.
- Claude Code baseline mode (new `mode="none"`): add `--disable-slash-commands`. It is the only installed flag that disables all skills and commands. The baseline root also holds none of the three skills. Limit: user-level skills in the host's own configuration are disabled by this flag, not removed. The configuration is not changed (Decision D-2 for the lead).
- Pi: already correct. Skill mode attaches `--skill` only. Baseline mode adds `--no-skills`.
- Codex: no skill-disable flag is measured in the installed help. The baseline root is empty. The limit is recorded: the host's own user-level skills, if any, are not disabled by this batch.

### C-3 Exact safe argument list and flags in the record (blocker)

- The boundary record stops using the placeholder `<boundary args>`. It records the full bwrap argument list, the host argument list, and their SHA-256 hashes.
- Add `flags`: the tokens of the host argument list that start with `-`.
- Credentials cannot appear: the environment is cleared (`--clearenv`), only `PATH` and `HOME` are set, and no credential variable is passed. The record names those variables, never their values (Codex, adapter record note).

### C-4 Probe error evidence (blocker)

- The boundary probe writes the sentinel read error to `/work/probe-err.txt`. The probe script then prints that file to stdout, so the error reaches the record.
- The record gains `probe_error_text` and `probe_error_sha256`.
- The test asserts the exit code, the exact command, and that the observed error text names the missing sentinel path.

### C-5 Child-process timeout (blocker)

- New stub mode `--spawn-child N` (in `tests/eval/fixtures/stub/stub.sh`): starts a background child that appends one tick to `proc/child-ticks.txt` every 0.2 s, then the parent sleeps N seconds.
- The test runs the stub with a timeout shorter than N. After the adapter returns, it records the stop reason (exit 124), and waits 1 s. It then asserts the tick file no longer grows. A stopped child does not write ticks. The test does not depend on a PID, because PIDs are not visible across the boundary.
- No retry. `attempts` stays 1.

### C-6 Owned control file in place of `~/.bashrc` (minor m3)

- The home-visibility test creates its own control file in a temporary directory outside the run root, with a unique marker. It asserts the file reads outside the boundary, and that the stub reads `read=no` inside.
- The test no longer depends on any file in the user's home.

### C-7 Local network isolation (Codex)

- New test: the test opens a listener on `127.0.0.1` on an ephemeral port. A stub inside the boundary tries to connect to that port. The control is the same connect outside the boundary, which must succeed.
- The boundary uses `--unshare-all`, which includes the network namespace. The expected result inside is a refused or failed connection.
- Local only. No external host is contacted and no provider is called.

### C-8 Full record of the boundary argument list (minor m1)

- Covered by C-3. The bwrap argument list is recorded in full, not redacted.

### C-9 Host bwrap requirement in the docstring (minor m2)

- The suite docstring and the CI note state that the boundary tests need the host `bwrap` (bubblewrap 0.13.1 measured). The assertions do not change.

## 2. Tests to add or change

| Test | Change |
|---|---|
| `test_adapter_command_flags_come_from_installed_help` | Also assert the forbidden flags are absent: `--ignore-user-config`, `--ignore-rules`, `-s`, and `--disable-slash-commands` in skill mode |
| `test_adapter_baseline_mode_disables_skills_for_claude_only_in_baseline` (new) | Skill mode has no disable flag. Baseline mode has `--disable-slash-commands` |
| `test_boundary_probe_retains_the_error` (new) | Probe record holds `probe_error_text` and its hash. Text names the sentinel |
| `test_adapter_timeout_stops_a_child_process` (new, C-5) | Tick file stops growing after the timeout |
| `test_boundary_home_configuration_is_not_visible` | Uses the owned control file, not `~/.bashrc` (C-6) |
| `test_boundary_local_network_is_isolated` (new, C-7) | Connect fails inside, succeeds outside, to a local listener |
| `test_adapter_record_holds_the_full_argument_list` (new, C-3) | Record has `argv`, `flags`, `argv_sha256`, and the full bwrap argument list |

## 3. Frozen-set effect

Changing `tests/eval/adapters.py`, `tests/eval/sandbox.py`, `tests/eval/fixtures/stub/stub.sh`, `tests/test_release_isolation.py`, and the freeze test changes the frozen hashes. The correction needs a new freeze file after its focused tests pass. The 41-entry freeze stays as the reviewed record.

## 4. Decisions for the lead

- **D-1:** keep the host default for the Codex sandbox (proposal), or name a permission mode explicitly after review.
- **D-2:** accept that the Claude baseline disables all skills with `--disable-slash-commands`, and that Codex has no measured skill-disable flag.
- **D-3:** accept the child-process proof by tick file rather than PID.

## 5. Not in this correction

- No live dispatch. Provider authorization stays zero.
- No change to home configuration, trust settings, or credentials.
- The artifact fixtures, the setup-fetch path, the OSH Park reference, and the `pcba-design` snippet entry stay separate.
