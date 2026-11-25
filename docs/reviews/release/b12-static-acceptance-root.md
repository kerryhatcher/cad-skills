# B12 local harness acceptance and next work

Date: 2026-11-15 UTC. Author: skill-dev-lead.

The lead accepts B-1, B-2, B-3, M-A and M-B at the corrected freeze.
Both reviewer reports give agreement:

- `b12-harness-freeze-review-codex-r2.md`
- `b12-harness-freeze-r2-review-pi.md`

Freeze: `docs/reviews/b12-harness-freeze-claude-r2.sha256`.
SHA-256: `09e77fa0f2d280f23918f1fd02b8afd5fd557e90b6b147932a1cb2a5897c32a6`.
The 33 entries match. Both reviewers report 64 local harness tests passing.
Root's held-record regression now gives an empty measured table and a separate execution count.
Packaging acceptance remains separate.

## Next bounded work

Claude can implement local host adapters and the filesystem isolation tests.
Use installed CLI help and the retained harness research for exact command interfaces.
Preserve the assigned hosts, models, trust settings and credentials.
Do not change the user's home configuration.
Do not print credentials or put them in retained logs.

First prove the filesystem boundary with a local subprocess and a repository sentinel.
The host has `/usr/bin/bwrap`, `/usr/bin/unshare` and `/usr/bin/timeout`.
Their presence does not prove that their isolation features work.
Measure the supported route. Refuse the operation if the boundary cannot be established.
Use temporary roots and the accepted installation modes.

Implement the process and output adapters with local stubs and retained output fixtures.
Keep discovery, skill selection, trace availability, token usage and execution status separate.
A host that cannot report a fact must record it as unavailable.
Measure process time and retain failures. Do not retry automatically.
No test in this batch can call a provider.

Freeze the coherent adapter and isolation batch for both reviewers.
The pending artifact fixtures and setup-fetch path remain separate work.
All provider authorization remains zero until accepted integrated artifacts and adapters exist.
No commit, merge or push belongs to this acceptance.
