# Distribution path correction

Date: 2026-11-15 UTC. Author: skill-dev-lead.

Both release reviewers identified the path classifier as the cause of the A2 D-6 findings.
The classifier documentation names skill supplier directories and the Sierra evidence directory.
Its old substring comparison also matched project output directories.
The corrected classifier follows the documented scope.

The lead removed the proposed 17 fixture allowlist entries. The distribution manifest retains its accepted entries.
No fixture output is classified as a supplier source only because its parent directory is named supplier.
The byte-hash exclusion still examines all distributed files, including fixture outputs.
The candidate set includes tracked files and untracked files that Git does not ignore.
Two new tests cover an untracked supplier file and the exact A2 output path.
The latter test also proves that an unlisted skill supplier page still gives D-6.

The packaging suite passes 34 of 34 tests.
No fixture, source evidence, license decision or PCBA product code changed.
The replacement freeze supersedes the first integration proposal.
The first record and manifest remain history. The lead did not submit them for acceptance.
Provider authorization remains zero.
