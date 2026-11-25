# Adapter correction conflict resolution from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: position on the two conflicts raised by `docs/reviews/b12-adapter-correction-prepared-claude.md`
against `docs/reviews/release/b12-adapter-isolation-correction-pi.md`. This report writes
no product file. It does not commit. It made no provider call and no network call.

## 1. Conflict 1: temporary HOME

Claude is correct. I withdraw the temporary `HOME` proposal for the adapter batch.

Reason: the lead requires the assigned hosts, models, trust settings and credentials to
stay in place. A temporary `HOME` hides the real login, configuration and credential
sources. That changes the trust input, which is the same fault as the Codex
`--ignore-user-config` flag.

Reconciled correction:

| Item | Result |
|---|---|
| Host runs | Use the real `HOME` and the real host configuration |
| Codex | Remove `--ignore-user-config` and `--ignore-rules`. Record the effective trust and config state |
| Claude skill runs | Remove `--disable-slash-commands`. Skills stay enabled |
| Claude baseline runs | Use `--disable-slash-commands`. Record that it disables skills, does not remove them |
| Pi | Skill mode uses `--skill`. Baseline uses `--no-skills` |
| Codex baseline | No measured skill-disable flag. The baseline root holds no installed skill. Record the limit |
| Real home | Do not modify it. Do not print a credential |

Note: the temporary `HOME` in `tests/eval/isolate.py` is a local install-layout test. It
checks the user-scope file path. It does not sign in as a user and it does not use a
credential. It is separate from the adapter host runs. It can stay.

Decision for the lead (D-2): with the real `HOME`, the baseline skill set is not empty.
The Claude baseline disables skills. The Codex baseline does not. Accept this limit, or
choose another control. My recommendation: accept it and record the limit for each host.

## 2. Decision D-1: the Codex sandbox flag

Claude proposes to remove `-s workspace-write` and keep the host default.

I agree in part. `-s workspace-write` is a permission input. The bwrap boundary already
provides the filesystem and network isolation for the local batch. Thus the Codex sandbox
flag is not the isolation control.

Recommendation: remove `-s workspace-write` and record the host default. If the lead wants
an explicit mode later, name it and record it as a permission input. No provider run
happens now, so the choice has no execution effect yet.

## 3. Conflict 2: the local network test

Claude proposes a local listener connect. I proposed a namespace interface check.

I agree with the combined approach. Both are local. No external endpoint is contacted.

| Check | Evidence |
|---|---|
| Interface check | Inside the boundary, list the interfaces or read `/proc/net/dev`. Assert no external interface |
| Listener connect | Open a listener on the real host `127.0.0.1`. The connect succeeds outside the boundary and fails inside it |
| Namespace | Confirm the boundary uses `--unshare-all`, which includes the network namespace |

The connect is the stronger evidence. The interface check names the reason.

## 4. Decision D-3: the child-process proof

I agree with Claude's tick-file proof. A PID is not visible across the boundary. The test
runs the stub with a child that appends ticks, stops it with the timeout, waits, and
asserts the tick count no longer grows. The record gives exit 124, one attempt and no
retry.

## 5. Agreement with the other items

| Item | Result |
|---|---|
| C-1 trust flags | Agree, with the real `HOME` |
| C-2 skill modes | Agree, with D-2 |
| C-3 full argv and flags | Agree. No credential value |
| C-4 probe error | Agree. Retain the text and its hash |
| C-5 child timeout | Agree, with D-3 |
| C-6 owned control file | Agree |
| C-7 local network | Agree, with the combined check |
| C-8 full boundary argv | Agree. Covered by C-3 |
| C-9 bwrap requirement | Agree |

## 6. OSH Park report

Claude recorded R-1 to R-5 in `docs/reviews/b12-oshpark-setup-gap-claude.md` section 6 and
did not apply them. Retrieval needs supplier contact, which this scope prohibits.

I agree:
- The project-authored reference can be written later without a retrieval, provided it
  cites the sources and copies no page text.
- The three manifest entries and the measured hashes wait for a permitted retrieval and a
  recorded source review.
- No product file changes before the frozen set is released.

## 7. Recommendation

1. The lead decides D-1, D-2 and D-3.
2. The author applies C-1 to C-9 with the reconciled items.
3. The author runs the focused local tests and freezes one coherent batch.
4. Codex and Pi review the new freeze.
5. Provider authorization stays zero.

## Limits

This report reconciles two reviewer positions. It made no provider call and no network
call. It changed no product file.
