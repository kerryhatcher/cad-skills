# Distribution correction after integration

Date: 2026-11-15 UTC. Author: skill-dev-lead.

The accepted A2 fixture contains 17 project-authored files under its supplier output directory.
The distribution test did not see these files before Git tracked them.
After integration, the test reported D-6 for all 17 paths.
The earlier packaging pass did not cover the complete tracked fixture.

The distribution allowlist now names those exact 17 paths from the accepted A2 freeze.
A comment labels them as project-authored outputs.
The supplier path classifier remains unchanged. No broad directory pattern was added.
The full-copy byte-hash exclusions still apply to each distributed file, including each listed fixture.
The candidate set now includes tracked files and untracked files that Git does not ignore.
A new isolated Git test proves that an untracked supplier file reaches the distribution check and gives D-6.

The packaging suite passes 33 of 33 tests after this correction.
No A1 or A2 fixture byte changed. No PCBA product code changed.
The harness points to the replacement manifest. The previous manifest remains history.
The provider authorization remains zero.
