# Adapter correction release acknowledgement from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: acknowledgement of `docs/reviews/release/b12-adapter-correction-release-root.md`.
This report writes no product file. It does not commit. It made no provider call.

## 1. Release read and agreed

I read the release and agree with every item. The release resolves the two conflicts and
the three decisions.

| Item | Result |
|---|---|
| Codex trust flags | Remove the flags that ignore rules or configuration |
| Workspace permission override | Remove the explicit workspace-write flag. Record the host default as unmeasured where necessary |
| Skill runs | Keep skills enabled |
| Claude baseline | `--disable-slash-commands` only in the declared baseline mode. Record that it disables commands and skills |
| Codex baseline | A baseline with unmeasured user skills cannot claim an empty skill set. Refuse it for measured evaluation until the skill set is established |
| Stub HOME | Keep the temporary credential-free HOME for the stub tests and the local installation tests |
| Real HOME | Do not mount it. Do not expose a credential to make a stub test pass |
| Host command construction | Do not override `HOME` and do not ignore the host configuration |
| Authenticated host route | Not established by a stub test. Record credential and configuration preservation as unmeasured for that future route |
| Provider | No authorization and no call |
| Record | Full safe argv, flags, probe errors, exits and hashes |
| Control file | An owned control file outside the run root |
| Network | The namespace interfaces and a local listener, with no external endpoint |
| Child timeout | Prove the child writes ticks before the timeout, then prove the tick file stops. Record the observation interval and the stop reason. An unchanged empty file does not prove termination |
| Attempts | One attempt. No automatic retry |
| Freeze | One complete replacement. Preserve the earlier freeze and the separate packaging acceptance |
| Merge | No merge, commit or push before acceptance |

## 2. Effect on my earlier conflict position

The release gives the missing distinction. My withdrawal of the temporary `HOME` applied to
a future authenticated host run. The current batch runs local stubs only, so a
credential-free HOME is correct for the stub tests. The two are separate:

| Route | HOME | Status |
|---|---|---|
| Local stub tests | Temporary, credential-free | In this batch |
| Authenticated host runs | The real `HOME` and configuration | Not established. Preservation is unmeasured |

## 3. Review of the next freeze

I will review the next complete replacement freeze. The review covers:

1. The removed Codex flags and the removed workspace permission override.
2. The skill and baseline modes, with the Codex baseline refused.
3. The full safe argv, flags, probe error, exit and hashes.
4. The owned control file.
5. The network interface check and the local listener.
6. The active-child tick proof with a measured interval and stop reason.
7. One attempt and no retry.
8. The complete freeze set.

I will report hashes before and after and any concrete blocker once.

## 4. Limits

This report reads the release. It made no provider call and no network call. It changed no
product file.
