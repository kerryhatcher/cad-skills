# A2 result acceptance

Date: 2026-11-15 UTC. Author: skill-dev-lead.

The lead accepts freeze `4d250e0a163bdd514b4051fc3e909752c0ae7dcade5f8ddf10ba4b652e170c40`.
Both reviewers accept the same 199 entries. The lead measured all entries and reproduced the 23 focused tests.
Pi also reproduced the 65 harness tests. Both reviewers measured the unchanged 155 fixture entries.

The run outcome now uses the produced supplier rows. It compares the mandatory flags and exact failure and pending sets.
The fixture description stays separate. The minimal exit-only result fails.
This decision closes F-1 and R-1 to R-12.

A1 and A2 remain accepted fixtures. A2 remains deliberately incomplete.
Provider authorization stays zero. The authenticated route, A3, and final integration remain open.
