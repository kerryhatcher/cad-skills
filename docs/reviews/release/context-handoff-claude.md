# Context handoff: claude-release-dev (B12 release)

Date: 2026-11-15 UTC. Author: `claude-release-dev` (Claude, assigned model Haiku 5.5, `claude-haiku-5-5`, unchanged).

## Identity and state

- Working directory: `/mnt/storage/projects/cad-skills-worktrees/release`.
- Branch: `work/release`. Base commit: `75d99da`.
- Git state: 29 changed or untracked paths. Nothing is staged, committed, merged or pushed.
- Current status: frozen. No product edits while the lead has the set frozen. Edits resume only when the lead releases.
- Provider authorization: zero. No provider call, no network call, no supplier contact.
- Herdr: the client on PATH is 0.9.5 and the server speaks protocol 19. Use `/proc/482044/exe` (0.8.0). Do not restart the server. Every Herdr message starts with `[YYYY-MM-DD - HH:MM:SS UTC] To: $agent-name; From: $agent-name - ` using the measured UTC time. Team names: `skill-dev-lead` (`w1P:p3`), `claude-release-dev` (`w1P:p9`), `codex-release-dev` (`w1P:pC`), `pi-release-dev` (`w1P:pF`).

## Current accepted or frozen interface

Latest freeze, the one the reviewers checked last:

- `docs/reviews/b12-final-local-repair-freeze-claude.sha256`
- SHA-256: `efbf8f6144aef87d7cca5f8438ed8f1b94b6a40acbf083d42510ba6e72a1717b`
- 41 entries. Pi reproduced 41 of 41 before and after its review.
- Results at freeze: harness 65 of 65, isolation 29 of 29, packaging 25 of 25, skill packages 8 of 8, project IO 11 of 11.

Earlier freezes, all preserved:

| Freeze file | SHA-256 | Status |
|---|---|---|
| `docs/reviews/b12-harness-freeze-claude.sha256` (33 entries) | `21168df2ef2d1d4902883adae8a27896c401f79728d7f9e096ea20aeb82f6d62` | Superseded. Reviewed record |
| `docs/reviews/b12-harness-freeze-claude-r2.sha256` (33 entries) | `09e77fa0f2d280f23918f1fd02b8afd5fd557e90b6b147932a1cb2a5897c32a6` | Accepted by the lead (harness correction) |
| `docs/reviews/b12-adapter-isolation-freeze-claude.sha256` (41 entries) | `bea9e6d07c71430296cc9a10013a4055941416d704c12e53d7b47ff157930ff3` | Pi accepted. Superseded by the correction freeze |
| `docs/reviews/b12-adapter-correction-freeze-claude.sha256` (41 entries) | `316f392cdb0ddd2ccb5e5b399d1053d0aac0e033d35fca5c016703a0eb5e7bbf` | Superseded by the final repair freeze |
| `docs/reviews/b12-final-local-repair-freeze-claude.sha256` (41 entries) | `efbf8f6144aef87d7cca5f8438ed8f1b94b6a40acbf083d42510ba6e72a1717b` | Current. Pi recommends acceptance |
| `docs/reviews/b12-packaging-freeze-claude.sha256` | `4f7e942dacdf444c000ffbec26232dae91b59eac9e95ea8e84563afeb16bbb64` | Packaging, accepted separately at unchanged hashes |
| `docs/reviews/b12-matrix-freeze-claude.sha256` | `13ca8f6361311a6bcc1a4a7a64445f2452ed0994f7b286f91a56459fd209f24b` | Matrix record (revision 4 inputs) |

Governing documents:

- Matrix, revision 5: `docs/reviews/b12-matrix-revision5-claude.md` (in the current freeze). Superseded in part by the prepared repairs.
- Matrix data: `tests/eval/matrix.yaml`. Harness modules: `tests/eval/{common,isolate,run_case,check_artifacts,score,packaging,sandbox,adapters}.py`. Test files: `tests/test_release_harness.py`, `tests/test_release_packaging.py`, `tests/test_release_isolation.py`.
- Correction record: `docs/reviews/b12-final-local-correction-claude.md`.
- Release and review records: `docs/reviews/release/` (reviewer reports only, plus the lead's release records).

## Pending reviews

- Pi: final local repair review received at 03:01 UTC (`docs/reviews/release/b12-final-local-repair-review-pi.md`). Recommends acceptance. Done.
- Codex: a review of the final local repair is not in this session's record. Confirm before lead acceptance.
- Codex: the OSH Park setup gap report (`docs/reviews/b12-oshpark-setup-gap-claude.md`) has no Codex review in this session. Pending.
- Lead: acceptance of the final local repair freeze. Pending.

## Scratch and evidence paths

- Scratch directory: `/tmp/claude-1000/-mnt-storage-projects-cad-skills-worktrees-release/eaf2167c-7fd4-482f-935e-4f1b42b4cdd7/scratchpad/`.
  - `b12-state-record.md` (the state record from the stop, 02:18 UTC).
  - `packaging-freeze.sha256` (first packaging freeze list, superseded).
  - `test_project_io.log`, `test_skill_packages.log`.
- In-repo evidence, retained:
  - `docs/reviews/b12-adapter-correction-freeze-claude.sha256`, `docs/reviews/b12-final-local-repair-freeze-claude.sha256`.
  - Measured boundary: `bwrap` 0.13.1, probe exit 0. The boundary probe hashes are reproducible with `tests/eval/sandbox.py`.
  - CLI help fixtures: `tests/eval/fixtures/cli-help/` (`codex-exec.txt`, `claude.txt`, `pi.txt`, `versions.txt`).
- Reviewer reports: `docs/reviews/release/`.

## Authorized next step

- Wait for the lead's release of the current freeze, or for the lead's acceptance.
- No product edits while frozen. Report to the lead if work is needed.
- If the lead releases a new scope, the work proceeds only inside that scope.

## Unresolved items

1. Authenticated host configuration and credential preservation: unmeasured. The stub does not test it.
2. Codex sandbox mode: the host default is kept and recorded as unmeasured.
3. Codex baseline: refused for measured evaluation. Its user-level skill set is unmeasured.
4. Claude baseline: `--disable-slash-commands` disables commands and skills. Its effect is disclosed, and the user's real HOME is kept, so the baseline skill set is not empty (lead decision D2, recorded as permitted with disclosure).
5. Provider adapters: none is live. Host output schemas are unmeasured, so discovery, selection and token usage stay unavailable.
6. Artifact fixtures A1, A2 and A3: pending. A1 needs lead confirmation of `skills/pcb-design/examples/rc-edit`. A2 needs a complete valid input project. A3 needs the PCBA implementation.
7. Setup-fetch path for supplier pages: separate work. Zero fetch scripts exist, so the standalone release gate cannot pass yet.
8. OSH Park KiCad reference and its manifest entries: pending lead decision. Retrieval deferred. Pi's corrections R-1 to R-5 are recorded in the gap report (section 6) and not applied.
9. `pcba-design` entry in `tests/snippet_envs.json` (`pcb`): pending integration, to avoid breaking the exact routing-set test.
10. Adapter review minor m3: the listener stub depends on bash. Note it in the CI and docstring, or switch to a portable connect. Not applied.
11. Sentinel isolation and the network checks are accepted at their measured local scope only.
12. Packaging P-6 and P-7: accepted separately at unchanged hashes. The final distribution is not accepted.
13. Provider authorization stays at zero until accepted integrated artifacts and adapters exist.
14. No commit, merge or push belongs to any of this work.
