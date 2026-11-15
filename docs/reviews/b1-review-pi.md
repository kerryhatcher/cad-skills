# B1 review: Pi

Date: 2026-11-14.

Reviewed state: frozen B1. `docs/reviews/b1-files.sha256` identifies the reviewed files. `sha256sum -c docs/reviews/b1-files.sha256` passed for all 17 entries. No file changed during this review.

Reviewed sources: `docs/reviews/b1-implementation-claude.md`, `docs/reviews/b1-files.sha256`, `docs/reviews/b1-design-pi.md`, `docs/reviews/b1-design-codex.md`, `contracts/`, `tests/test_pcb_tools.py`, the fixtures, and the changed documentation.

Scope: B1 only. This review does not examine B2, B3, B4, or a later batch.

**Decision**

B1 is not accepted yet. Six concrete corrections are necessary. P1, P2, P4, P5 and P6 need a code change. P3 needs a recorded design decision. P4 to P6 are the Codex C1 to C3 items. I reproduced them independently.

The rest of B1 passes. The loader, version registry, schema types, exit precedence, report format, tests, and CI change agree with the agreed design.

**1. Commands and results**

| Command | Result |
|---|---|
| `sha256sum -c docs/reviews/b1-files.sha256` | All 17 files OK. |
| `uv run tests/test_pcb_tools.py` | 24/24 passed, exit 0. |
| `uv run tests/test_snippets.py` | 52/52 blocks passed, 5 skipped, exit 0. |
| `uv run tests/test_print_tools.py` | 6/6 passed, exit 0. |
| Independent fixed-digest check with `printf ... \| sha256sum` | The two expected digests match the test values. |
| Workflow check | `permissions: contents: read` is at workflow level. The `pcb-contracts` job runs the contract test. Actions are pinned by SHA. |

The five skipped snippet blocks are the existing `# notest` markers in the skill references. B1 did not add or remove them.

**2. Independent adversarial checks**

| Check | Result |
|---|---|
| Duplicate key in an anchored YAML mapping, used through an alias | Rejected with two findings at `/a/b` and `/c/b`. This is noisy but safe. |
| Alias to a non-string key | Rejected at both locations. |
| Alias to a non-finite value | Rejected at both locations. |
| `!!bool yes` | Accepted as `True`. |
| `!!int 0x10`, `!!int 1_000`, `!!float 1_000.5` | Accepted as `16`, `1000`, `1000.5`. |
| `1e-999` | Accepted as `0.0`. |
| YAML byte-order mark | Accepted. |
| `file.too_complex` with more than 200,000 nodes | Rejected as `file.too_complex`. |
| Forced exception inside `validate_record` | Report gives exit 3, `tool.validator_failure`, and the file in `unprocessed`. |
| `canonical_hash({1: "x"})` against `canonical_hash({"1": "x"})` | Same hash. |
| `canonical_hash({True: "x"})` against `canonical_hash({"true": "x"})` | Same hash. |
| `canonical_hash({"a": (1, 2)})` against `canonical_hash({"a": [1, 2]})` | Same hash. |
| Text limit with `unit: ""` | Rejected with `schema.invalid` at `/limits/silkscreen_width/unit`. |
| Board coordinate pair `x_axis: right`, `y_axis: down` | Accepted. |
| Same input file passed two times | Exit 0 and two input hash entries. |
| `profile_sha256` of 64 hex characters plus a final newline | Accepted with no finding. |
| `datasheet_url` with a final newline | Accepted. |
| `parse_version("1.0\n")` | Returns `(1, 0)`. |
| YAML `!!int 0x` | Uncaught `ValueError`. The CLI reports `tool.validator_failure` and exit 3. |
| Huge integer `10**400` in a number field | Uncaught `OverflowError`. Exit 3, not a record finding. |

The first three loader checks are safe. The hash checks are a blocking defect. The other results are observations.

**3. Blocking corrections**

**P1: `canonical_hash` accepts data that is not JSON-compatible**

Location: `contracts/validate.py`, `canonical_bytes` at lines 227 to 234.

The function sends the record to `json.dumps` without a value-tree check. `json.dumps` silently converts an integer key to a string, a boolean key to `"true"`, and a tuple to a list. Thus these values give the same hash as a different JSON value:

- `{1: "x"}` and `{"1": "x"}`
- `{True: "x"}` and `{"true": "x"}`
- `{"a": (1, 2)}` and `{"a": [1, 2]}`

The agreed design P1 and P2 accept only mappings with string keys, lists, strings, booleans, null values, integers, and finite numbers. The current tests catch a mixed int and string key only because `sort_keys` cannot compare the two key types. They do not catch an all-integer key set, a boolean key, or a tuple. A later skill that copies this function can therefore calculate a hash for data that the B1 loader would reject.

The input-file path does not reach this defect, because `parse_record` rejects non-string keys and YAML has no tuples. The defect is in an exported function and in the hash contract.

Minimum correction:

1. Add a recursive check before `json.dumps`. Accept only `dict` with `str` keys, `list`, `str`, `bool`, `None`, `int`, and finite `float`.
2. Reject every other type, including `tuple`, `set`, `bytes`, date values, and non-string keys.
3. Raise `RecordError` with `file.not_json_compatible` and a JSON pointer.
4. Keep the root-only `content_sha256` removal and the current byte encoding.
5. Add tests for an all-integer key, a boolean key, a tuple at the root, a nested tuple, and a tuple that is equal in content to a list.

Do not change the hash bytes for valid data. The fixed-digest test must keep its current expected values.

**P2: The supplier profile does not separate fabrication, assembly, and margin limits**

Plan section 4, line 131: "Separate fabrication limits from assembly limits and project margins."

The supplier profile schema has `limits` and `division`. `division` separates limits by enforcement method (`kicad_dru`, `project_settings`, `geometric_tests`, `manual_evidence`). It does not identify a fabrication limit, an assembly limit, or a project margin. The fixture has four limits and no such classification. A consumer cannot select the assembly limits for a PCBA package or the fabrication limits for a bare board.

The agreed proposal summary did not name this field. The plan does. B1 is the schema batch, so the omission must be corrected here or recorded as an explicit design decision with a machine-checked alternative.

Recommended minimum correction:

1. Add a required `scope` field to each limit. The value is `fabrication`, `assembly`, or `margin`.
2. Keep `division` as the enforcement location.
3. Update the fixture so at least one limit has each scope, or document why the fixture has no assembly limit.
4. Add a test for a missing scope, an unknown scope, and one valid limit of each scope.
5. Update `contracts/README.md` with the scope meaning.

A naming prefix such as `fabrication.min_trace` is an alternative only if a rule and a test enforce the prefix. A name convention without a check does not satisfy the plan.

**P3: The part record does not record an assembly variant**

Plan section 4, line 125 names "assembly variant" in the part record. The part schema required list has no variant field. The `variants.yaml` record has per-reference population states for each variant. It can own the data, but the plan assigns a field to the part record, and the implementation record does not state a decision to move that ownership.

This is a blocking clarification, not necessarily a schema addition. Use one of these resolutions:

1. Add an optional `assembly_variants` array of variant IDs to the part schema. Test an unknown variant ID later in B2 or B9.
2. Record in `contracts/README.md` and the B1 correction record that `variants.yaml` is the sole owner of assembly variant and DNP data. The part record does not repeat it. Add the cross-file check in B2.

I recommend option 2. It prevents duplicate ownership. The decision must be explicit before B1 is accepted.

**P4: End-anchored patterns accept a final newline**

Location: `contracts/validate.py`, `VERSION_RE` and `parse_version`, and every schema pattern that uses `$`.

`re.match` and `re.search` with `$` match before a final newline. `parse_version("1.0\n")` returns `(1, 0)`. A `profile_sha256` of 64 hexadecimal characters plus a newline passes the schema. The board record has no semantic hash check for that field. A `datasheet_url` plus a newline also passes. The test suite has no final-newline case.

Minimum correction:

1. Use `re.fullmatch` in Python. Use `\Z` where a pattern is necessary.
2. Keep `minLength` and `maxLength` for a fixed-length or bounded string.
3. Add one semantic whole-string check for every constrained string. The schema pattern is not the only check.
4. Reject control characters in identifiers, paths, hashes, versions, dates, and URLs. A newline is a control character.
5. Add tests that pass a final newline through the validator for a hash, URL, version, date, and ID. Test the exact accepted string also.

This is Codex C1 and root finding 2.

**P5: YAML scalar construction can raise an uncaught error**

Location: `contracts/validate.py`, `parse_record`, the `construct_document` call.

`!!int 0x` raises `ValueError`. `!!int 0b2` and `!!int 1e` also raise `ValueError`. `parse_record` catches only `yaml.YAMLError`. `build_report` then catches the broad `Exception` and reports `tool.validator_failure` with exit 3. A hostile record must give `file.parse_error` with exit 1.

Minimum correction:

1. Catch `ValueError`, `KeyError`, and `OverflowError` around the YAML construction step.
2. Convert each to `file.parse_error` with the record location.
3. Add tests for `!!int 0x`, `!!int 0b2`, and `!!int 1e`. Each must give exit 1.

This is Codex C2.

**P6: A large integer in a number field causes a tool failure**

Location: `contracts/validate.py`, `_is_number` and the number validation path.

`_is_number` calls `math.isfinite(value)` for an `int`. `math.isfinite(10**400)` raises `OverflowError`. A valid JSON integer in `mechanical.width_mm` gives `tool.validator_failure` and exit 3. The record is valid JSON. It must pass or give a record finding, never exit 3.

Minimum correction:

1. Skip `math.isfinite` for an `int`.
2. Convert a value to `float` only after an `int` test in later geometry rules.
3. Add a test with a large integer in a number field. The result must not be exit 3.

This is Codex C3.

**4. Non-blocking observations**

These items do not block B1. Record them for a later correction or batch.

| Item | Observation |
|---|---|
| Temperature range | `part.temperature_range_c` does not check `min <= max`. A reversed range is accepted. A small part rule can correct this later. |
| Unknown stock | `stock.status: unknown` uses `maxProperties: 1`. It cannot record the source or the retrieval date that showed the unknown value. Examine the plan intent before B9. |
| Text limit unit | A text recommendation with `unit: ""` is rejected. The B1 design said "omitted or empty." The stricter form is clear, but the README should state that text limits omit `unit`, or the schema should accept an empty string. |
| Explicit tags | `!!bool yes`, `!!int 0x10`, and `!!int 1_000` are accepted. The revised proposal allows the int, float and bool tags. The README says that numbers follow the JSON grammar and that `yes` stays a string. State that explicit tags use the YAML lexical forms, or enforce the JSON grammar for explicit tags. |
| Underflow | `1e-999` becomes `0.0`. The design rejected overflow and non-finite values, not underflow. Reject a nonzero literal that becomes zero, or record this as a known limit. |
| Coordinate axes | The board record accepts a left-handed pair (`right` and `down`). B2 or the mechanical batch must reject it or define it. |
| Duplicate input | The same file passed two times gives two input entries. This is harmless. Deduplicate if a later report consumer needs unique paths. |
| Test gaps | No test for `file.too_complex`, alias duplicate findings, explicit scalar tags, underflow, or the P1, P4, P5 and P6 cases. The forced failure check passed, so the code path works. |
| MPN diagnosis | A non-string MPN gets `part.missing_mpn`, not `schema.invalid`. The record is rejected, but the code name is less precise. |
| Future schema risk | `_schema_findings` does not account for `patternProperties` when it lists allowed keys. No current B1 schema uses it. A later schema must not add it without a code change. |
| Process | The implementation record discloses earlier `python3` runs. This is a process deviation, not a code defect. The hashes and tests are the reviewed evidence. |
| STE | The STE tools did not run on the new prose. This review does not certify the STE status. |

**5. Reviewed hashes**

The manifest check passed. These are the reviewed hashes.

| File | SHA-256 |
|---|---|
| `.github/workflows/test.yml` | `cff2b7454554dfe8886f30c46b4646034842f0204f20fa09b2c4128ef730912e` |
| `AGENTS.md` | `fb9ae245c827aa88162e0c4a7bcf4b336a06f46c45fcf4ce9f97a536e3a08f6f` |
| `README.md` | `95f6528c941a54010aca2e36fdf7e80675f14804221f213b84b44c9c5bd493ad` |
| `ste-glossary.yaml` | `bf27f15bcecca96a57779f36574bef7070ced560767e24a57b6901a44758e77d` |
| `contracts/README.md` | `8b4fc7fc4d915fb4c9d57e67901a2d7de060c568cdd8972c930c73736d219304` |
| `contracts/validate.py` | `dec8456da0953187ffdfd1b423f435920c1aa1fa28ee6718b558a19914deb4da` |
| `contracts/schemas/registry.json` | `0569f758f83b0e3f3e1652e40eea8e373780993b1f65ecaeaef902a88aab0121` |
| `contracts/schemas/board.schema.json` | `812c58cc52f5c43d50524eb71f80abd31dbf5e6298c5ecd88c5cd58af5b940c9` |
| `contracts/schemas/part.schema.json` | `6db486543952c62e8bd8f732696db1229fec7b1a8943610dbc21c9234d2941e0` |
| `contracts/schemas/supplier-profile.schema.json` | `ceaf2e7d61c538a4e0cc8e859276c72f540dbc15c627052ec017e3a285eef988` |
| `contracts/schemas/variants.schema.json` | `53755cd7d4f79e604329b1e8369bce34fa4f9d820b6002bff3ff9e34b9755901` |
| `tests/test_pcb_tools.py` | `fdd057e5e6cfe987cdb83f3a476e919ccb1f5dafca48b5e468167e2d920be163` |
| `tests/fixtures/pcb/board.yaml` | `91b45de6c27e9bf7aa1b374804fda06759fa0c9f8efd2b4cb74e372ee9aba164` |
| `tests/fixtures/pcb/part.yaml` | `d0ed30f2a583cd50d280db68b2cc0d24dd98f0f8e6749167a2feb88b25ccd0a2` |
| `tests/fixtures/pcb/supplier-profile.yaml` | `e6054d96ac64aeb17c2ed538e3b7883b15061d4a18046c60adeec461ade08c9c` |
| `tests/fixtures/pcb/variants.yaml` | `3ee364f38d83f1a9a8671d719e003474c5da170096c2ca4c72d8b03a9f895ac5` |
| `docs/reviews/implementation-proposal-claude.md` | `6b1c8dd331ea3d365e0188322e6d76937e002c6a496c006e09b3667d903aa729` |

Other reviewed records:

| File | SHA-256 |
|---|---|
| `docs/reviews/b1-files.sha256` | `04a8ef4f4a05f4adf1303c6d33eaa23683c49305f2d1c8128499e9490d179b31` |
| `docs/reviews/b1-implementation-claude.md` | `5ae60100a82b256bca4d35abf52dcd69646850f287ffa842b09264dbe5bea3ab` |
| `docs/reviews/b1-design-pi.md` | `9af63496da79f4db5ab9759b75408e57316a97086a54eee8098e27817ab080da` |
| `docs/reviews/b1-design-codex.md` | `f12950018251beb5bcd51d5915fbebddee7dd5a199a26d1e686b9afb79a6f821` |

**6. Next step**

Claude corrects P1 to P6 and records the P3 decision. Claude then supplies a correction record and a new hash manifest for the changed files. Both reviewers examine the changed hashes and rerun the contract tests. B2 to B4 work does not start against B1 until this review accepts the correction. The B234 proposal already names P4 to P6 as C1 to C3. It must add P1 to P3. The B234 shared validator must start from the corrected B1 code.

This review changes no implementation file, no plan section, and no other review report. It does not request a commit.
