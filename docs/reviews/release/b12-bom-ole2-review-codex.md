# B12 BOM provenance and OLE2 correction review

Date: 2026-11-15 UTC. Author: `codex-release-dev`. Type: review of the proposed correction.

## Decision

Revision 1 did not meet the approved scope. I confirm revision 2 for the BOM-only batch.

## Revision 2 review

- The proposal limits this batch to one BOM GET, one manifest entry, one local copy, and the OLE2 code and tests.
- The terms page and the FAQ GET remain open for the lead. They do not enter this batch.
- The manifest omits `replaces` and records `prior_retrieved: unknown`.
- The release-tree BOM copy does not exist yet.

## Confirmed BOM items

- The OLE2 token maps to the eight-byte prefix `D0 CF 11 E0 A1 B1 1A E1`.
- The proposed `application/vnd.ms-excel` required-magic entry matches the measured response type.
- The three project-authored tests cover a matching prefix, a rejected prefix, and null magic refusal.
- The BOM entry records the URL, resolved URL, request time, byte count, hash, content type, prior date state, and exclusion decision.
- The `.xls` exclusion pattern matches the repository-level source evidence path.
- The recorded BOM hash matches the retained PCBA worktree copy. I measured the prefix as `d0 cf 11 e0 a1 b1 1a e1`.

## Freeze conditions

Add the BOM copy to the release tree and confirm its hash before the new freeze. Keep the harness and tests network-free.
The new freeze must cover the changed packaging code, tests, manifest, source copy, and review records.
Codex and Pi must review the new freeze. Provider authorization remains zero.

## Limits

This review made no network call and ran no suite. It changed no product file.
