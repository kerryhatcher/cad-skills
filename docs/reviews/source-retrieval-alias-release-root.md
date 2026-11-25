# Source retrieval input protection

Date: 2026-11-15 UTC. Author: skill-dev-lead.

Both reviewers reproduced the manifest overwrite. Pi and Codex also reproduced a profile overwrite.
The lead releases one narrow correction to the frozen retrieval implementation.

1. Before any fetch, compare each resolved destination with the resolved manifest path and all profile input paths.
2. Refuse a matching destination with exit 2. Include normalized aliases such as `./sources.yaml`.
3. Refuse all destinations under `supplier/profiles`. Retrieval must never replace a profile, including an unbound profile.
4. If existing paths identify the same file through a hard link, refuse that input/output alias too.
5. Apply the same validation to `--check-only`. The command must identify the invalid entry before a fetch.
6. Add focused tests for the manifest, its normalized alias, the profile, its alias, and a normal guidance destination.
7. Keep the accepted link, outcome and exit-precedence behavior unchanged.

Run the focused retrieval suite. Freeze the replacement code, tests and report for both reviewers.
Keep the earlier freeze as history. Do not edit source bytes or supplier profiles.
