# B12 final local repair freeze review

Date: 2026-11-15 UTC  
Reviewer: `codex-release-dev`  
Freeze: `docs/reviews/b12-final-local-repair-freeze-claude.sha256`  
Freeze SHA-256: `efbf8f6144aef87d7cca5f8438ed8f1b94b6a40acbf083d42510ba6e72a1717b`

## Result

I recommend acceptance of the released local repair. All 41 frozen file hashes matched before and after the focused tests. I found no blocker in the corrected baseline policy, Pi baseline path handling, or child timeout proof.

## Findings

- The Codex baseline policy refuses measured runs at planning. The dispatch path refuses the planned run before it reaches the adapter or reserves budget.
- The all-gates-open test verifies that all three Codex baseline entries stay refused. It uses a failing provider stub and checks that the ledger stays unused.
- The Pi baseline rejects a nonempty skill path list. Skill paths appear only in skill mode.
- The child test samples increasing tick counts while the stub runs. It takes the first post-return count before the 1.5 second observation interval. The later count stays equal. The record has one attempt, no automatic retry, and a timeout reason.
- The earlier review sentence now states the correct order for the post-return count.

## Focused local checks

- `uv run tests/test_release_harness.py`: 65/65 passed.
- `uv run tests/test_release_isolation.py`: 29/29 passed.
- `uv run tests/test_release_packaging.py`: 25/25 passed.
- `uv run tests/test_skill_packages.py`: 8/8 passed.
- `uv run tests/test_project_io.py`: 11/11 passed.
- `sha256sum -c docs/reviews/b12-final-local-repair-freeze-claude.sha256`: 41/41 matched after the checks.

These tests use local stubs and a local listener. They make no provider call and use no external endpoint. Provider authorization stays zero.

## Limits

The temporary `HOME` applies only to local stubs and installation checks. The tests do not establish authenticated host behavior, user configuration behavior, or credential preservation for a future host run. The measured filesystem and network boundary stays accepted only for the tested local route on this host.

Packaging P-6 and P-7 remain separately accepted at their unchanged hashes. This review does not extend that acceptance to changed packaging files. Artifact fixtures and the setup-fetch path remain open.
