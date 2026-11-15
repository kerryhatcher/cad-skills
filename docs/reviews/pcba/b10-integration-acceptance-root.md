# PCBA integration acceptance

Date: 2026-11-15 UTC. Author: skill-dev-lead.

Both reviewers accept the executable 124-file replacement and the 128-file documentation replacement.
The latter manifest hash is `d419688f2e4b5b30a35209985f619c2fc46ae2d58c2a1d949feb9ab24079ca64`.
The lead copied those files to the integration branch after the accepted mechanical and release commits.
The source worktree remains unchanged.

## Integration changes

The snippet routing table now maps `pcba-design` to `pcb`.
The exact-set package test now passes with the new skill present.
The guide names the supplier file and its project directory separately, because the reference scanner treats a combined path as a skill file.
The guide also states the existing schema-first refusal for a combined drill file.
Both PCBA reviewers accept this narrow text correction.

The shared CI test now expects the accepted `release-static` job in addition to `pcb-contracts` and `snippets`.
It also asserts the two release test commands.
The permission, pinned-action, timeout and no-container assertions remain unchanged.

## Results

The PCBA suite passes 106 of 106 tests.
The skill package suite passes 8 of 8 tests, including copy equality and snippet routing.
The shared suite passed 58 of 59 before the CI expectation correction.
The corrected CI function passes 1 of 1. No other shared test changed.
The release harness passes 65 of 65 tests.
The packaging suite passes 34 of 34 after the integration path correction.
Both release reviewers accept that correction in the separate 200-file freeze.
The snippets pass 52 of 52 blocks with five declared skips.
The print tools pass 6 of 6 tests.
The logs are in `integration-evidence/`.

## Limits

The retained package remains unqualified. Ten checks pass, DRC and stock fail, and supplier rules remain unconfirmed.
No physical test occurred. No supplier convention changed.
KiCad output timestamps can differ between runs. Each package binds its own output bytes.
A3 release expectations and live provider evaluation remain separate work.
Provider authorization remains zero. No push occurred.
