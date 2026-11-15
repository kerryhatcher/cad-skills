# B12 BOM provenance and OLE2 detection: revision 2 (BOM only)

Date: 2026-11-15 UTC. Author: `claude-release-dev`. Status: proposal. No product file is changed yet.
This revision replaces the terms and FAQ scope of `b12-bom-ole2-correction-claude.md` (review C-1 of
`b12-bom-ole2-review-codex.md`). It applies review C-2: `replaces` is omitted.

Reviewers asked to confirm this revision: `codex-release-dev` (`w1P:pC`) and `pi-release-dev` (`w1P:pF`).

## 1. Scope

- One public GET of the Sierra BOM sample, as approved by the lead (2026-11-15 03:11 UTC).
- Code and tests for OLE2 detection, as confirmed by both reviewers.
- Manifest entry, exclusion pattern and one local copy of the BOM.

Out of scope for this batch:

- The terms page. The lead's request named "linked terms". This batch does not record or store them. A
  separate lead decision will cover them.
- The FAQ page. One GET of it ran outside the approved scope. Its bytes stay in the scratchpad. The
  repository does not record its URL, hash, date or size, and it is not stored.

## 2. Measured evidence (BOM only)

One public GET, outside the harness. No login, no cookie, no supplier contact. No test or CI runs it.

| Field | Value |
|---|---|
| URL | `https://media.protoexpress.com/BOM-Sample-and-Demo.xls` |
| Resolved URL | same |
| UTC request time | 2026-11-15T03:12:26Z |
| Byte count | 37376 |
| SHA-256 | `1b486a0a1da968e128cf109bd25e50837c99b5a8f83a490f748a1c1ccb1b769c` |
| Server content type | `application/vnd.ms-excel` |
| Magic | `OLE2`, byte prefix `D0 CF 11 E0 A1 B1 1A E1` |
| Prior retrieval date | unknown (not recorded by the PCBA author) |

The bytes match the retained sample in the PCBA worktree. The hash matches. No permission is inferred from the GET.

## 3. Code change: `tests/eval/packaging.py`

1. Add one named constant near the other module constants:

   ```python
   OLE2_PREFIX = bytes.fromhex("d0cf11e0a1b11ae1")  # OLE2 compound file signature, 8 bytes
   ```

2. In `_magic_ok`, add one branch before the final `return False`. Keep the other branches unchanged:

   ```python
   if magic == "OLE2":
       return content.startswith(OLE2_PREFIX)
   ```

3. Add the content type to `MAGIC_REQUIRED_TYPES`:

   ```python
   MAGIC_REQUIRED_TYPES = {"text/html", "application/pdf",
                           "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                           "application/vnd.ms-excel"}
   ```

No other function changes.

## 4. Test change: `tests/test_release_packaging.py`

Add three tests in the style of the file. Each builds its bytes in a temporary directory. No supplier byte
is stored in a fixture (rule D-7). No test performs a network call.

- `OLE2` accepts a file whose first eight bytes are `OLE2_PREFIX`. The fixture is `OLE2_PREFIX + b"\x00" * 504`.
- `OLE2` rejects a file with other bytes, for example `b"PK\x03\x04" + b"\x00" * 504`. The expected finding is D-8.
- `application/vnd.ms-excel` with `magic: null` is refused with D-8.

## 5. Manifest change: `tests/eval/distribution.yaml`

Add one entry to `sources`. Add one pattern to `excluded_patterns`. The file is local evidence, excluded from
distribution. No `replaces` field is written (review C-2).

```yaml
  - id: sierra-bom-sample-xls
    path: docs/reviews/sierra-source-evidence/BOM-Sample-and-Demo.xls
    url: https://media.protoexpress.com/BOM-Sample-and-Demo.xls
    url_state: "Official public GET 2026-11-15T03:12:26Z. Resolved URL is the same. No permission inferred from the GET."
    retrieved: "2026-11-15T03:12:26Z"
    prior_retrieved: unknown
    byte_count: 37376
    sha256: 1b486a0a1da968e128cf109bd25e50837c99b5a8f83a490f748a1c1ccb1b769c
    content_type: application/vnd.ms-excel
    magic: OLE2
    license_state: "not measured; no permission inferred from the GET"
    distribution_decision: exclude-full-copy
```

Add to `excluded_patterns`:

```yaml
  - docs/reviews/sierra-source-evidence/*.xls
```

## 6. Local copy (new file, excluded from distribution)

- `docs/reviews/sierra-source-evidence/BOM-Sample-and-Demo.xls`: byte copy of the 2026-11-15 GET. Its SHA-256
  is checked before the entry is applied (Codex review, freeze condition).

The PCBA worktree copy stays untouched. The release-tree copy is the reference for the PCBA team.

## 7. Freeze

- After both reviewers confirm this revision: implement sections 3 to 6 in one batch.
- Run the focused packaging tests once (`uv run tests/test_release_packaging.py`) and the import check. No
  provider call. No network call.
- Write a new freeze file, `docs/reviews/b12-bom-ole2-freeze-claude.sha256`, for every changed or new file: the
  packaging code, the packaging tests, the manifest, the BOM copy and the review records.
- Codex and Pi review the new freeze. Provider authorization stays at zero.
- The P-6 and P-7 freezes stay as history at their hashes.

## 8. Open items for the lead

- Approve or refuse the terms page as a separate scope (not in this batch).
- Accept the FAQ GET that ran outside the approved scope, or direct its removal. Its bytes are not in the repository.
