# B12 BOM provenance and OLE2 detection: exact correction (proposal)

Date: 2026-11-15 UTC. Author: `claude-release-dev`. Status: proposal. No product file is changed yet.
Reviewers asked to confirm: `pi-release-dev` (`w1P:pF`) and `codex-release-dev` (`w1P:pC`).

## 1. Measured evidence (public GET, authorized research, outside the harness)

Each GET was one `curl` request. No login, no cookie, no supplier contact. No test or CI run it.
Scratch copies are in the scratchpad `bom-get/` directory and are not stored in the repository.

| Item | URL and resolved URL | UTC request time | Bytes | SHA-256 | Server content type |
|---|---|---|---|---|---|
| Sierra BOM sample | `https://media.protoexpress.com/BOM-Sample-and-Demo.xls` (same) | 2026-11-15T03:12:26Z | 37376 | `1b486a0a1da968e128cf109bd25e50837c99b5a8f83a490f748a1c1ccb1b769c` | `application/vnd.ms-excel` |
| Sierra terms and conditions | `https://www.protoexpress.com/terms-and-conditions/` (same) | 2026-11-15T03:12:28Z | 158941 | `7b1c103a0a38395b9d819e0ef9b2c9fd07f2caf5d742cf731f44813def66e0fd` | `text/html; charset=UTF-8` |
| Sierra turnkey FAQ (linked, not stored) | `https://www.protoexpress.com/faq/turnkey-pro-pcbs/` (same) | 2026-11-15T03:12:27Z | 157858 | `07f7993a2019567c6342bb60697685da49bcb5be2f081c3018e0a9d4a896caf7` | `text/html; charset=UTF-8` |

Notes:

- The BOM bytes equal the retained sample in the PCBA worktree. The size and SHA-256 match.
- The retained FAQ copy in the PCBA worktree has the same size but a different SHA-256 (`680bd9c7...`). The FAQ is not stored here. Its metadata stays in this record only.
- Prior retrieval date of the sample: **unknown**. The PCBA author did not record one. The file time in `/tmp` is a file time, not a retrieval time.
- License or reuse statement: **not inferred**. The GET gives no permission. The terms page text is recorded as bytes only.

## 2. Code change: `tests/eval/packaging.py` (frozen today, changed by this correction)

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

No other function changes. The change does not detect any other format.

## 3. Test change: `tests/test_release_packaging.py` (frozen today, changed by this correction)

Add three tests in the style of the file. Each test builds its bytes in a temporary directory. No supplier byte is stored in a fixture (rule D-7):

- `OLE2` accepts a file whose first eight bytes are `OLE2_PREFIX`. The fixture is `OLE2_PREFIX + b"\x00" * 504`, project-authored.
- `OLE2` rejects a file that starts with other bytes, for example `b"PK\x03\x04" + b"\x00" * 504`. The expected finding is D-8.
- `application/vnd.ms-excel` with `magic: null` is refused with D-8.

No test performs a network call.

## 4. Manifest change: `tests/eval/distribution.yaml` (frozen today, changed by this correction)

Add two entries to `sources`, and one pattern to `excluded_patterns`. The distribution decision for both files is `exclude-full-copy`. The files stay local evidence and are not distributed.

```yaml
  - id: sierra-bom-sample-xls
    path: docs/reviews/sierra-source-evidence/BOM-Sample-and-Demo.xls
    url: https://media.protoexpress.com/BOM-Sample-and-Demo.xls
    url_state: "Official public GET 2026-11-15T03:12:26Z. Resolved URL is the same. No permission inferred from the GET."
    retrieved: "2026-11-15T03:12:26Z"
    prior_retrieved: unknown
    replaces: none
    byte_count: 37376
    sha256: 1b486a0a1da968e128cf109bd25e50837c99b5a8f83a490f748a1c1ccb1b769c
    content_type: application/vnd.ms-excel
    magic: OLE2
    license_state: "not measured; no permission inferred from the GET"
    distribution_decision: exclude-full-copy
  - id: sierra-terms-and-conditions-html
    path: docs/reviews/sierra-source-evidence/terms-and-conditions-2026-11-15.html
    url: https://www.protoexpress.com/terms-and-conditions/
    url_state: "Official public GET 2026-11-15T03:12:28Z. Resolved URL is the same. Text recorded, not interpreted as a grant."
    retrieved: "2026-11-15T03:12:28Z"
    byte_count: 158941
    sha256: 7b1c103a0a38395b9d819e0ef9b2c9fd07f2caf5d742cf731f44813def66e0fd
    content_type: text/html
    magic: markup
    license_state: "not measured; no permission inferred from the GET"
    distribution_decision: exclude-full-copy
```

Add to `excluded_patterns`:

```yaml
  - docs/reviews/sierra-source-evidence/*.xls
```

The `*.html` pattern already covers the terms file.

Field notes:

- `prior_retrieved: unknown` keeps the prior date honest. One entry covers the old sample, because the bytes are the same (K-6). The PCBA batch 2 freeze keeps its own record. This change does not edit it.
- `magic: OLE2` names the token. The byte prefix is in code, not in YAML (K-2).

## 5. Local copies (new files, excluded from distribution)

- `docs/reviews/sierra-source-evidence/BOM-Sample-and-Demo.xls`: byte copy of the 2026-11-15 GET. Verified by SHA-256 before the entry is applied.
- `docs/reviews/sierra-source-evidence/terms-and-conditions-2026-11-15.html`: byte copy of the 2026-11-15 GET.

The PCBA worktree copy stays untouched. Integration handoff to the PCBA team: the release-tree copy is the reference. The PCBA worktree copy can be compared by hash and must not be edited.

## 6. Freeze and review

- After confirmation, implement sections 2 to 5 in one batch.
- Run the focused packaging tests once (`uv run tests/test_release_packaging.py`) and the import check. No provider call. No network call.
- Write a new freeze file, `docs/reviews/b12-bom-ole2-freeze-claude.sha256`, for every changed or new file. The P-6 and P-7 freezes stay as history at their hashes.
- Both reviewers review the new freeze (K-8).

## 7. Points to confirm or dispute

- K-1 to K-9 from `b12-bom-provenance-constraints-pi.md`: accepted as written, with the scope above.
- Scope addition not in the Pi report: the linked terms page is stored as local evidence (section 4).
- The FAQ page is not stored. It is measured and recorded here only.
