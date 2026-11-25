# A1 and A2 artifact freeze review

Date: 2026-11-15 UTC. Author: `codex-release-dev`. Type: read-only review.

## Result

I accept the A1 and A2 fixture freeze at SHA-256 `7b01b363285f96e36ece6be1f74517f62622c9fd13dd29f3b1d21b546752bc26`.
All 155 file hashes match. The replacement freeze changes the A1 README and the focused test.

## A1

The focused test reads the retained ERC, DRC, update, interface, and simulation records.
It checks the pass states, the ready state, the operation names, the exit values, the raw hashes, and the closure hashes.
The after README states that its README copy keeps the template values. It also states the edited values in the fixture README.
Pi reports 16 of 16 focused checks passed. Claude reports the same result. Codex did not rerun the test.

The matrix entry for A1 still lists only the skill and freshness rule. It has no explicit result fields for ERC, DRC, or update.
The focused test covers these records. The matrix stays outside this fixture freeze.

## A2

The fixture owns a copy of the RC template and the selected profile. The profile hash matches the result records.
The independent order rule predicts failure for quantity 5 with a multiple of 3.
The status reports that failure and the pending text condition. The status also records that package and source review did not run.
This fixture remains incomplete. It does not claim a qualified package.

## Limits

This review made no network call and ran no test. It changed no product file.
This acceptance covers the fixture freeze. It does not authorize a provider run.
