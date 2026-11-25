# B12 adapter and isolation freeze review

Date: 2026-11-15 UTC  
Reviewer: `codex-release-dev`  
Freeze: `docs/reviews/b12-adapter-isolation-freeze-claude.sha256`  
Freeze SHA-256: `bea9e6d07c71430296cc9a10013a4055941416d704c12e53d7b47ff157930ff3`

## Result

The measured `bwrap` boundary works on this host. All 41 frozen hashes match before and after the focused tests. The focused suites pass. I do not recommend acceptance of the adapter batch yet. The command builders conflict with the lead's trust and skill requirements. The records also omit evidence that the interface requires.

## Blockers

- The Codex command in `tests/eval/adapters.py` sets `--ignore-user-config` and `--ignore-rules`. The installed help says these flags skip Codex configuration and user or project execution rules. This changes the trust and permission inputs. Remove these flags or do not build a command that skips them.
- The Claude Code command sets `--disable-slash-commands`. The installed help says this disables all skills and commands. This command cannot test skill discovery or invocation. Remove this flag for skill runs, and add a separate baseline mode that keeps the skill set empty.
- The boundary records replace the argument list with `<boundary args>`. The adapter record also has no `flags` field. This does not meet the exact-command and flag record criteria. Record the full safe argument list. Do not record credential values.
- The boundary probe sends the sentinel read error to `/work/probe-err.txt`, but it does not retain or report that error. The test checks only `read=no`. Retain the observed error or its hash and test it with the exit code and exact command.
- The timeout test sleeps in one shell process. It does not test a child process. Add a stub that starts a child, then check that timeout stops the child and records the stop reason without a retry.

## Additional corrections

- `test_boundary_home_configuration_is_not_visible` depends on `~/.bashrc`. A clean home can lack that file. Use a project-authored control file outside the run root, and confirm it reads outside and not inside the boundary.
- The network test searches module text for selected import strings. The stub tests do not make a network call, and `bwrap` uses `--unshare-all`. Add a local test that confirms the subprocess has no network path, without contacting a provider or an external host.

## Focused local checks

- `uv run tests/test_release_isolation.py`: 18/18 passed.
- `uv run tests/test_release_harness.py`: 64/64 passed.
- `uv run tests/test_release_packaging.py`: 25/25 passed.
- `uv run tests/test_skill_packages.py`: 8/8 passed.
- `uv run tests/test_project_io.py`: 11/11 passed.
- `sha256sum -c docs/reviews/b12-adapter-isolation-freeze-claude.sha256`: 41/41 matched after the checks.

The `bwrap` probe on this host reads `README.md` outside the boundary and hides it inside. It keeps the run root readable. The tests use a local stub. They make no provider call.

## Scope limits

No provider authorization exists. No provider call occurred. Packaging P-6 and P-7 stay separately accepted at their unchanged hashes. This review does not extend that acceptance to changed packaging files. The artifact fixtures, setup-fetch path, and `pcba-design` snippet integration remain open.
