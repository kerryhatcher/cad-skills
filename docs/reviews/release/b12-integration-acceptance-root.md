# Static release integration

Date: 2026-11-15 UTC. Author: skill-dev-lead.

The lead accepts the reviewed static release files and copies them into `work/integration`.
The file list binds 220 files in `b12-integration-files-root.sha256`.
The accepted source manifests are the BOM r3, normalization r3, and A2 result-binding replacement.
The later manifests supersede the earlier file hashes where their paths agree.
The main README and AGENTS edits remain outside this integration because their review is incomplete.

The integration tests give these results:

| Test | Result |
|---|---|
| Release packaging | 32 of 32 pass |
| Local harness | 65 of 65 pass |
| Local isolation | 29 of 29 pass |
| Artifact expectations | 23 of 23 pass |
| Artifact fixtures | 16 of 16 pass |
| Skill snippets | Exit 0, with the declared skips |
| Print tools | 6 of 6 pass |

The logs are in `integration-evidence/`. All commands exit 0.
The BOM copy has the accepted hash. Intent-to-add made it visible to the exclusion test before the commit.
The distribution rules exclude the full supplier copies.

Provider authorization stays zero. The tests make no provider call.
The authenticated route, live adapters, A3 and final three-skill integration remain open.
This commit does not state that B12 is complete.

The Git whitespace check reports spaces in retained tool output and the PDF byte table.
These files keep their accepted bytes. The source-text whitespace check passes with these evidence paths excluded.
