# BOM provenance narrow scope constraints from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: concrete conflicts and constraints for the approved narrow scope. This report
writes no product file. It does not commit. It made no network call.

## 1. Scope read

The approved scope is:

1. An official public GET for BOM provenance. The known public sample is
   `https://media.protoexpress.com/BOM-Sample-and-Demo.xls` (plan line 519). Confirm the
   URL at retrieval.
2. Preserve the old sample. Record the prior date honestly as unknown.
3. Add OLE2 magic detection and require a non-null magic for
   `application/vnd.ms-excel`.
4. Add the distribution manifest delta and a local source copy.

The GET is authorized research. It is not a message to supplier personnel. It is not a
harness or test call.

## 2. Concrete conflicts and constraints

### K-1 The harness and tests stay network-free

The public GET is a one-time research action. It must not enter the harness, a test or CI.
The existing import check must still pass. Record the retrieval outside the harness in the
source review.

### K-2 Name the OLE2 magic token

`_magic_ok` uses literal tokens: `markup`, `%PDF`, `PK\u0003\u0004`. A raw OLE2 byte
string in YAML needs escaping and is not readable.

Correction: add a named token `OLE2` that maps to the byte prefix
`D0 CF 11 E0 A1 B1 1A E1`. Keep the literal tokens for the other types.

### K-3 Add the content type and its aliases

The lead requires a non-null magic for `application/vnd.ms-excel`. Servers can report
`application/msexcel`, `application/x-msexcel`, or `application/octet-stream`.

Correction: add `application/vnd.ms-excel` to `MAGIC_REQUIRED_TYPES`. Record the measured
content type from the response. A server type of `application/octet-stream` with
`magic: OLE2` is acceptable. Do not infer a format from the content type alone.

### K-4 Use a project-authored OLE2 fixture

D-7 rejects a fixture that holds supplier bytes. The real BOM is a full copy.

Correction: the tests use a minimal project-authored fixture whose first eight bytes are
the OLE2 prefix. Do not copy the supplier BOM into a fixture.

### K-5 Name the storage path and the manifest scope

The BOM is a supplier sample for the future `pcba-design` skill. The release worktree has
no `pcba-design`.

Correction: choose one path and state it.

- Under `docs/reviews/sierra-source-evidence/`, the repository manifest
  `tests/eval/distribution.yaml` holds the entry. Add `exclude-full-copy` and an
  `excluded_patterns` rule for `*.xls`.
- Under `skills/pcb-fab-package/supplier/pages/`, the skill manifest holds the entry and
  the existing `supplier/pages/**` pattern covers distribution.

The first path matches the current Sierra evidence location. State the integration handoff
to the PCBA team.

### K-6 Preserve the old sample and the unknown prior date

Keep the old sample entry as history. Do not invent a prior date.

Correction: add a `prior_retrieved: unknown` field (or a `prior_date_state`), and a
`replaces` or `prior_id` link when the new bytes replace the old bytes. If the bytes are
the same, record one entry and state that the prior date is unknown. Keep both hashes when
they differ.

### K-7 Record the retrieval evidence

Correction: record the URL, the resolved URL, the retrieval date, the byte count, the
SHA-256, the measured content type, and the statement that this is an authorized public
GET. Do not record a credential.

### K-8 The packaging acceptance is superseded for the changed files

The new scope changes `tests/eval/packaging.py`, `tests/eval/distribution.yaml`, and
`tests/test_release_packaging.py` (and possibly the skill manifest). The old P-6 and P-7
acceptance stays as history at its hashes. It does not extend to the changed files.

Correction: the new freeze needs both reviews for the changed packaging files.

### K-9 Record the BOM facts, not the file

The BOM proof is the headers, the hash, the retrieval date and the source URL. The file is
a full copy and stays out of distribution. The plan records the sample spelling
`Manfacturer (optional)`. Keep that fact in the source review, not in a copied file.

## 3. Recommendation

1. The author applies K-1 to K-9.
2. The author records the public GET and the local copy.
3. The author runs the focused packaging tests with the project-authored OLE2 fixture.
4. The author freezes one coherent batch.
5. Codex and Pi review the freeze.
6. No model provider call. Provider authorization stays zero.

## Limits

This report reads the plan and the packaging checker. It made no network call. It changed
no product file.
