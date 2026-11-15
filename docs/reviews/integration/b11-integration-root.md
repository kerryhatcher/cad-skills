# B11 integration record

Date: 2026-11-15 UTC. Author: skill-dev-lead.

Both reviewers accepted the mechanical implementation and the final guide.
The integration uses the 22-file list and its two-file addition.
The final guide hash is `1505b298f00c5cc9177e04f305e854dd463334869701d6caee956b940545afb0`.

The first geometry run found two absent fixtures. The integration list omitted ignored STEP and DXF files.
The author supplied their hashes. Both reviewers confirmed the retained inputs.
The lead copied those bytes and repeated the geometry suite. All 43 tests passed.
The initial failure log stays as evidence.

The lead also retained three ignored export artifacts. Their hashes agree with the author audit and export record.
Git will track these five named artifacts explicitly. Other generated CAD files remain subject to the existing ignore rules.

## Tests in the integration worktree

| Suite | Result |
|---|---|
| Mechanical contract and command tests | 55 passed |
| Mechanical geometry with retained fixtures | 43 passed |
| Shared contracts | 59 passed |
| Project I/O | 11 passed |
| Skill packages, with final guide | 8 passed |
| Snippets | 52 passed, 5 declared skips |
| Print tools | 6 passed |

All final commands exited 0. The logs stay in this directory.
The snippet run printed font-configuration warnings. It passed all selected blocks.

This integration retains the accepted fixture and proxy limits. It does not establish detailed component fit or supplier approval.
No source from the other active worktrees enters this commit.
No push occurs.
