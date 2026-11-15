# B12 BOM provenance: public GET record

Date: 2026-11-15 UTC. Author: `claude-release-dev`. Type: source review record (metadata only).

## Scope and authority

The lead approved a public GET of official source pages at 03:11 UTC. The lead accepted the terms and FAQ GETs as public source research at 03:18 UTC.

The author ran three public GET requests with `curl` on 2026-11-15, between 03:12:26Z and 03:12:29Z. Each request was one `GET`.

The requests used no login or cookie. The author sent no message to supplier personnel. No test or CI run made these requests.

The author did not assess reuse permission. The record claims no permission.

Only the BOM bytes enter this batch. The repository does not store the terms and FAQ bytes. They are not part of the freeze.

## Measured records

| Item | URL | Resolved URL | UTC request time | Bytes | SHA-256 | Server content type | Stored in repository |
|---|---|---|---|---|---|---|---|
| Sierra BOM sample | `https://media.protoexpress.com/BOM-Sample-and-Demo.xls` | same | 2026-11-15T03:12:26Z | 37376 | `1b486a0a1da968e128cf109bd25e50837c99b5a8f83a490f748a1c1ccb1b769c` | `application/vnd.ms-excel` | yes, `docs/reviews/sierra-source-evidence/BOM-Sample-and-Demo.xls` |
| Sierra terms and conditions | `https://www.protoexpress.com/terms-and-conditions/` | same | 2026-11-15T03:12:28Z | 158941 | `7b1c103a0a38395b9d819e0ef9b2c9fd07f2caf5d742cf731f44813def66e0fd` | `text/html; charset=UTF-8` | no |
| Sierra turnkey FAQ | `https://www.protoexpress.com/faq/turnkey-pro-pcbs/` | same | 2026-11-15T03:12:27Z | 157858 | `07f7993a2019567c6342bb60697685da49bcb5be2f081c3018e0a9d4a896caf7` | `text/html; charset=UTF-8` | no |

## Notes

- **BOM prior date:** The PCBA author did not record a retrieval time for the earlier sample. The file time of the earlier `/tmp` copy is not a retrieval time. This record does not use it. The entry carries `prior_retrieved: unknown`.
- **BOM identity:** The bytes match the earlier sample by size and SHA-256. The OLE2 magic `d0cf11e0a1b11ae1` is present.
- **FAQ hash difference:** The FAQ byte count is 157858. This matches the retained copy in the PCBA worktree. The SHA-256 of the FAQ is `07f7993a...`. The SHA-256 of the retained copy is `680bd9c7...`. The two hashes differ.
- **Terms:** The author did not assess reuse permission. The record claims no permission.
- **No claim:** This record claims no license, no redistribution permission and no reuse right for any of the three items.
