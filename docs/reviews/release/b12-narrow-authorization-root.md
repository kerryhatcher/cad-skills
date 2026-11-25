# B12 narrow correction authorization

Date: 2026-11-15 UTC. Author: skill-dev-lead.

The lead read the completed Codex and Pi reviews of the 33-entry freeze.
Both reviewers agree on B-1, B-2, B-3 and the two minor corrections.
The lead authorizes this correction from the current candidate bytes.

1. Attach the task and expected paths to each planned run. Keep expected owners outside prompts.
2. Record unavailable host discovery and selection explicitly. A local scan is only a file inventory.
3. Separate execution status from measured provider evidence. Missing evidence must not mean live evidence.
4. Exclude held, unauthorized, unexecuted and mock records from the measured release table.
5. Retain their execution records. Keep measured live failures in the measured table.
6. Test the complete freeze input set and count the authorized subset correctly.
7. Run the focused local tests and freeze the complete input set again.

The snippet routing entry for `pcba-design` is an integration item.
Apply it when the integration tree contains that skill.
The release worktree currently lacks the skill, thus a premature entry would break the exact routing-set test.
Record the pending entry without weakening that test.

The lead accepts packaging P-6 and P-7 at the unchanged hashes in the 33-entry freeze.
Both reviewers support this scoped acceptance, with 25 packaging tests passing.
This does not accept the harness or the final distribution.
The setup-fetch path, accepted integrated artifacts, host adapters and measured isolation remain incomplete.
Provider authorization stays zero.

After the new freeze message, stop edits to its files until the lead explicitly releases the set.
A reviewer finding does not release a frozen set.
No merge or push belongs to this authorization.
