# B1 design review: Codex

Date: 2026-11-13.

Reviewed sources: `docs/reviews/implementation-proposal-claude.md` and sections 14–15 of `docs/pcb-pcba-plan.md`.

Scope: B1 interfaces and tests only. This report does not review an implementation or approve later batches.

**Decision**

I agree with D1, D4, and D5. D2 and D3 have blocking corrections below. The B1 test scope also needs these corrections before implementation.

These corrections concern data acceptance and report consistency. They do not call for another library, a new framework, or a larger batch.

**D1: repository contracts — agree**

Keep the primary contracts in `contracts/`. Give each skill its own standalone copies later. The root accepts this arrangement.

B1 can test the primary contracts without skill directories. Keep copy agreement and isolated skill operation in B4 and subsequent batches.

**D2: schema versions — blocking correction**

The direction is acceptable: reject unsupported major versions and newer minor versions. Accept older minor versions only under an explicit compatibility rule.

A comparison of version numbers alone does not establish compatibility. A schema with `schema_version` fixed to `"1.0"` also contradicts the proposed older-minor test.

Use these B1 rules:

- Accept only a string with the form `MAJOR.MINOR`.
- Use nonnegative decimal integers without unnecessary initial zeros.
- Reject numeric values, booleans, null values, patch versions, and extra text.
- Keep the original version string in the record.
- Select an explicitly supported schema for the record version.
- Report an unsupported older minor version as a failure.

For B1, support only `1.0`. For the older-minor test, supply a temporary registry with explicit schemas for `1.1` and `1.2`. Let `1.2` be the highest supported version. Validate the `1.1` record against its declared schema.

Make the schemas observably different. A field mandatory only in `1.2` must not invalidate a valid `1.1` record. Also test a field that `1.1` forbids. A changed registry number alone is insufficient evidence.

A later batch can define migrations if necessary. B1 does not need them.

**D3: content hash — blocking correction**

The proposed Python JSON encoding is acceptable as a project contract. It is not a universal JSON canonicalization standard.

Define its accepted data before the hash function runs:

- Accept mappings with string keys, lists, strings, booleans, null values, integers, and finite numbers.
- Reject duplicate keys before a parser replaces them.
- Reject non-finite numbers at all depths.
- Reject dates, binary values, sets, custom tags, and recursive YAML aliases.
- Reject non-string YAML keys before JSON conversion.

Use a safe YAML loader with duplicate-key detection. For B1, reject YAML merge keys. This prevents merge precedence from changing a supplier limit silently. Accept ordinary repeated aliases only if the resulting data passes all rules.

Apply duplicate-key detection to JSON as well. A duplicate reference in the proposed map disappears before semantic validation unless the loader rejects it.

For duplicate references, retain the finding `variants.duplicate_reference` if practical. Otherwise use `file.parse_error` with the duplicate key and file location. Do not claim semantic detection after a normal dictionary load.

State the complete hash procedure:

1. Remove only the root `content_sha256` field from a copy.
2. Preserve nested fields with that name.
3. Encode with the proposed JSON settings and `allow_nan=False`.
4. Encode the JSON text as UTF-8 without a byte-order mark or final newline.
5. Calculate SHA-256 of those bytes.
6. Return lowercase hexadecimal text.

Do not change the input record. Preserve array order and Unicode text. State that `1` and `1.0` can produce different hashes. State the same rule for negative zero. Do not silently normalize these values.

A hash identifies the accepted record representation. It does not prove that two differently represented limits mean the same thing.

Use one fixed record with independently specified JSON bytes and an expected digest. Do not derive the expected digest through `canonical_hash` itself.

Keep the input-file hash separate. It covers the original file bytes, including comments and whitespace. A content hash covers the parsed record under the rules above.

**D4: test file — agree**

Use `tests/test_pcb_tools.py`. Keep the proposed CI job and workflow permission. No new test framework is necessary.

The number 16 is not an acceptance criterion. Use parameterized cases or additional test functions for the corrections below.

**D5: dependencies — agree**

Use `jsonschema` and `pyyaml`. Small loader extensions are necessary for duplicate detection and JSON-compatible data. They do not constitute a custom schema checker.

Keep PEP 723. Record the tested dependency versions with B1 results. A dependency range alone does not identify the tested environment.

**Strict field types — blocking correction**

Define exact types for all nested fields in the four schemas. Do not rely on Python truth tests or automatic conversions.

In particular:

- Reject `true`, `"1"`, and `1.0` for integer quantities.
- Reject numeric strings and booleans for measured limits.
- Reject empty identifiers, MPNs, units, and mandatory evidence strings.
- Use explicit alternatives for stock quantities and the string `unknown`.
- Require population states to be strings from the stated set.
- Require date fields to use explicit strings with the agreed date format.
- Apply unknown-field rejection to nested objects as well as root objects.

JSON Schema can treat `1.0` as an integer by mathematical value. If exact integer types are the contract, use a narrow type extension. Test the behavior directly.

Configure format tests explicitly if the schemas use `format`. A `format` annotation alone does not establish URL or date acceptance.

Treat `extensions` as nonfunctional data in B1. No field there can replace a mandatory manufacturing field or change a limit. Hash its contents normally.

**Exit codes and reports — blocking correction**

Keep the four exit codes. Define this precedence for multiple findings:

| Priority | Exit code | Cause |
|---|---:|---|
| First | 3 | Invalid registry, invalid schema, or validator failure |
| Second | 2 | Incorrect arguments, missing input file, or missing schema directory |
| Third | 1 | Malformed or unreadable existing record, or invalid record content |
| Last | 0 | All supplied records pass |

A corrupt schema is a tool failure, not an invalid board. A nonexistent input path is exit 2. An existing file that the tool cannot read is exit 1, consistent with the proposal.

Continue independent input files when practical. If a tool failure stops processing, report the unprocessed paths explicitly. Do not report them as passes.

Under `--json`, emit one JSON object without ordinary status text on standard output. Include input hashes for all files whose bytes the tool read. Do not invent a hash for a missing file.

Define `--json` behavior for argument errors, including no `FILE`. Either emit the stated error report or document the parser exception. Prefer the error report for the proposed helper.

Do not let a later error overwrite a higher-priority exit code. Keep all available findings.

**B1 acceptance tests**

Retain the useful proposed tests. Add these cases before acceptance:

| Area | Minimum cases |
|---|---|
| Duplicate keys | Root and nested duplicates in YAML and JSON, including a repeated variant reference |
| YAML forms | Non-string key, timestamp value, merge key, recursive alias, custom tag |
| Non-finite numbers | NaN, positive infinity, negative infinity, and an overflowing JSON exponent |
| Field types | Boolean, numeric string, fractional value, and `1.0` in integer fields |
| Nested fields | Unknown nested field, empty mandatory string, invalid date |
| Versions | Malformed versions, declared older schema, newer-only mandatory field, unsupported older minor |
| Hash | Fixed bytes and digest, key order, comments, nested hash field, array order, numeric representation |
| Exit precedence | Mixed exit-1 and exit-2 inputs, plus a corrupt schema that gives exit 3 |
| Report | JSON argument error, good and bad inputs together, missing file without a false hash |

For the overflow case, a parser can turn `1e999` into infinity. Test the resulting value as well as explicit non-finite tokens.

Use a malformed temporary schema to test exit 3. No live tool or artificial failure mechanism is necessary.

Run the commands in proposal section 6.6 after implementation. Supply the results and final file hashes for review under plan section 15.

**Scope and root decisions**

The root accepts X2 disk cost up to 15 GB. No user cleanup is necessary. Remove X2 as a pending user prerequisite in the next status record. B1 does not pull an image.

Container selection, GUI operation, supplier formats, package isolation, and release qualification belong to later reviews. They do not block these B1 interfaces.

This report changes no implementation files or plan sections. B1 design agreement remains conditional on the blocking corrections above.

**Combined B1 interface — explicit agreement**

Decision date: 2026-11-13.

I agree with the combined B1 interface: my corrections, Pi P1–P6, and the root clarifications below. No design conflict remains.

- Keep plain, untagged ISO dates as strings. Validate their date format. Reject explicit `!!timestamp` tags.
- Use `jsonschema.TypeChecker` redefinition for exact types. Do not add a separate schema interpreter.
- Permit text limits only as explicit recommendations. Require numeric values for minimum and maximum limits.
- Treat evidence hashes as identifiers of exact retrieved bytes. They do not establish authenticity.

These clarifications replace conflicting wording in the earlier reports. The combined test scope includes tests for these rules.

This agreement permits B1 implementation under the review procedure. It does not approve implementation results or later batches. I changed no implementation files.
