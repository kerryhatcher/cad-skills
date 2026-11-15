# B1 design review: Pi

Date: 2026-11-14.

Reviewed sources: `docs/reviews/implementation-proposal-claude.md`, sections 14 and 15 of `docs/pcb-pcba-plan.md`, and `docs/reviews/b1-design-codex.md`.

Scope: B1 interfaces D1 to D5 and the B1 test scope. This report does not review an implementation and does not approve later batches. It changes no implementation file and no plan section.

**Decision**

I agree with D1 and D4. I agree with the direction of D2, D3 and D5, but they need the blocking corrections below. The B1 test scope needs the same corrections before implementation.

I agree with the Codex corrections on the strict loader, the explicit version registry, the hash procedure, exact field types, and exit-code precedence. This report adds the concrete loader rule, the finding codes, and the report fields that B1 needs to make those corrections testable.

B1 can start when P1 to P6 are part of the agreed interface and the test scope. Without them, I object to B1.

**D1: repository contracts — agree**

Keep the primary contracts in `contracts/`. Each skill gets a standalone copy later. The root accepts this arrangement. X5 is closed.

Add these details to the interface:

- The copy set is `registry.json`, every schema file that the registry names, and `README.md`.
- A skill copy must not read `contracts/` at runtime. B4 compares the copies byte for byte.
- B1 does not create a skill directory. B1 tests the primary contracts only.

**D2: schema versions — blocking correction P3**

The proposed rule "an older minor version passes" is not sufficient. A record must select a schema that the registry explicitly supports for its declared version. A comparison of numbers alone does not show compatibility.

Use these rules:

- `schema_version` is a string with the form `MAJOR.MINOR`.
- Each part is a nonnegative decimal integer. Reject leading zeros, a patch part, whitespace, and extra text.
- Reject numbers, booleans, and null values. A YAML value `1.0` is a number, not a string, and must fail.
- Compare minor parts as integers. `1.10` is newer than `1.9`.
- The registry names the supported versions and one schema file for each version. For example: `{"cad-skills/board": {"latest": "1.0", "schemas": {"1.0": "board.schema.json"}}}`.
- Validate a record against the schema for its declared version. Do not validate an older record against the latest schema.
- A newer minor version gives `schema.minor_newer` and exit 1.
- An older minor version that the registry does not list gives `schema.version_unsupported` and exit 1.
- A different major version gives `schema.major_unsupported` and exit 1.
- Each versioned schema fixes `schema_version` to its own version with `const`.

B1 supports `1.0` only. The older-minor test uses a temporary registry with explicit schemas for `1.1` and `1.2`. Make the schemas observably different:

- A field mandatory only in `1.2` must not invalidate a valid `1.1` record.
- A field that `1.1` forbids must fail on a `1.1` record.
- A `1.1` record must not load under the `1.2` schema.
- A `1.0` record must not load under the `1.1` schema.

Do not add migrations in B1.

**D3: content hash — blocking correction P1 and P2**

The proposed JSON encoding is an acceptable project contract. It is not a general canonicalization standard. The proposal does not define the accepted input data or the exact byte sequence, so two correct implementations can give different hashes.

**P1: accept only JSON-compatible data**

Use a small safe YAML loader and a JSON loader with these rules. Apply the same rules to `.yaml`, `.yml` and `.json`.

- Reject a duplicate key at any depth with `file.duplicate_key` and a JSON pointer. PyYAML and `json.loads` otherwise keep the last value and hide the defect.
- Reject a non-string key. This includes a YAML key such as `1:`.
- Reject merge keys (`<<`). Merge precedence must not change a supplier limit without a visible edit.
- Reject recursive aliases. Accept an acyclic alias only if the resulting data obeys all rules.
- Reject timestamps, binary values, sets, and custom tags. Resolve dates as strings with an explicit `YYYY-MM-DD` check.
- Resolve only `true` and `false` as booleans. Do not resolve `yes`, `no`, `on` or `off` as booleans. They stay strings and then fail a boolean check where a boolean is necessary.
- Reject `NaN`, `Infinity`, `-Infinity`, `.nan`, `.inf`, and `-.inf` at any depth.
- Reject a JSON exponent that overflows to infinity, for example `1e999`.
- Reject an unreadable file as a record error. Do not convert a read failure into a missing file.

This JSON-compatible YAML subset removes most hash ambiguity. It also prevents the `on:` key in a GitHub Actions file from becoming the boolean `True`.

**P2: state the complete hash procedure**

1. Copy the parsed record.
2. Remove only the root `content_sha256` field. Keep a nested field with the same name.
3. Encode with `json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)`.
4. Encode the JSON text as UTF-8 without a byte-order mark and without a final newline.
5. Calculate SHA-256 of those bytes.
6. Return lowercase hexadecimal text.
7. Do not change the input record. Preserve array order and Unicode text.

State these representation rules in `contracts/README.md`:

- `1` and `1.0` can give different hashes. Do not normalize them.
- `-0.0` can give a different hash from `0.0`. Do not normalize it.
- NFC and NFD text can give different hashes. Do not normalize Unicode.
- Key order and comments do not change the content hash.
- The input-file hash covers the original bytes, including comments and whitespace. It is separate from the content hash.
- `evidence_sha256` covers the exact evidence bytes that the project retrieved. It is not a canonical record hash. Record the source URL and retrieval date with it.

Use one fixed record whose JSON byte sequence is written in the test source, with an expected digest that is written in the test source. Do not calculate the expected digest with `canonical_hash` itself. Add a second test for the root-only removal rule and a nested `content_sha256` field.

**D4: test file — agree**

Use `tests/test_pcb_tools.py`. Keep the proposed CI job and `permissions: contents: read`. The count 16 is not an acceptance criterion. Use parameterized cases where one rule has several inputs.

**D5: dependencies — agree with a blocking correction**

Use `jsonschema` and `pyyaml` only. The small loader and type checks do not constitute a custom schema checker.

Pin exact versions in the PEP 723 header for B1. Use the versions that pass on this host. Record the installed versions in the B1 result. Exact integer and format behavior can differ between library versions, so a range is not enough for a contract test. Define the version bump as a reviewed change.

**Strict field types — blocking correction P4**

The schemas must give an exact type for every field, including nested fields. Do not rely on Python truth tests.

- Add a type walk before or after JSON Schema validation. An `integer` must be a Python `int` and not a `bool`. A `number` must be an `int` or a finite `float`, and not a `bool`. A `string` must be a `str`, a `boolean` must be a `bool`, an object must be a `dict`, an array must be a `list`, and null must be `None`.
- Reject `true`, `"1"`, and `1.0` for an integer field such as `quantity`.
- Reject a boolean or a numeric string for a numeric limit.
- Reject an empty or whitespace-only string for an identifier, MPN, unit, URL, or evidence text. `minLength` alone does not catch spaces.
- Require `retrieved` to be a valid `YYYY-MM-DD` string. Enable the format checker. Reject an impossible date such as `2026-02-30`.
- Require `source_url` and `datasheet_url` to start with `http://` or `https://`. Do not accept a bare `uri`.
- Apply `additionalProperties: false` to nested objects, not only to the root.
- Emit one finding for one defect. When a missing MPN produces both a schema error and `part.missing_mpn`, keep `part.missing_mpn` and suppress the generic error for that pointer. A test must assert one finding, not two.
- Treat `extensions` as nonfunctional data. It cannot replace a mandatory field or change a limit. Hash it normally.

Add a discriminator for supplier limits. A limit can be numeric or text, and one untyped `value` field cannot enforce either type.

- `value_kind` is `number` or `text`.
- For `number`, `value` is a finite JSON number and `unit` is a nonblank string.
- For `text`, `value` is a nonblank string and `unit` is omitted or empty.
- `kind` remains `minimum`, `maximum`, `recommendation`, or `unconfirmed`.
- An `unconfirmed` limit has no value.
- A numeric `minimum`, `maximum`, or `recommendation` has a source URL and a retrieval date.

**Exit codes and report — blocking correction P5**

Keep four exit codes. Define this precedence when several findings occur:

| Priority | Exit | Cause |
|---:|---:|---|
| 1 | 3 | Invalid or missing registry, missing schema file named by the registry, invalid schema, or validator failure |
| 2 | 2 | Incorrect arguments, missing input file, or missing schema directory |
| 3 | 1 | Unreadable existing input file, parse error, duplicate key, or invalid record content |
| 4 | 0 | All supplied records pass |

A missing `--schemas` directory is exit 2. A registry that names an absent schema file is exit 3. A corrupt schema is a tool failure, not an invalid board.

Add these report rules:

- Include `exit_code` in the JSON report. `status` alone cannot separate exit 2 from exit 3.
- Keep `status` as `pass`, `fail` or `error`.
- Under `--json`, write only one JSON object to standard output. Write diagnostics to standard error.
- A `--json` argument error, including no `FILE`, emits the error report with `exit_code: 2`, `findings: [{"code": "cli.argument_error", ...}]`, and `inputs: []`.
- Continue with independent files after a record error when practical. Report an unprocessed path explicitly. Never report it as a pass.
- Include an input hash for each file whose bytes the tool read. Do not invent a hash for a missing file.
- Do not put a current time or a random value in the report. Sort findings by file, location and code. Two runs on the same inputs must give the same standard output.
- A later error must not replace a higher-priority exit code. Keep all findings.

**B1 test scope — blocking correction P6**

Keep the useful proposed tests. Change these items:

- Test 10 expects `variants.duplicate_reference`. The `references` field is a map, so a repeated reference is a duplicate key. Expect `file.duplicate_key` with the reference path. Remove `variants.duplicate_reference`, or define it only for a future list form.
- Test 16 parses the workflow with `yaml.safe_load`. PyYAML can read the GitHub Actions `on:` key as a boolean. Use the JSON-compatible loader from P1 or a textual check of the `permissions:` block. Do not use default PyYAML for this file.

Add these cases before acceptance:

| Area | Minimum cases |
|---|---|
| Duplicate keys | Root and nested duplicates in YAML and JSON, including `schema_version` and a repeated variant reference |
| YAML forms | Non-string key, timestamp, merge key, recursive alias, custom tag, binary value, `yes` as a key or value |
| Non-finite | `.nan`, `.inf`, `-.inf`, JSON `NaN`, JSON `Infinity`, `1e999` |
| Exact types | `true`, `"1"`, `1.0`, and `null` in integer fields. Boolean in a limit. Blank string. Impossible date. Non-http URL. |
| Nested fields | Unknown nested field. `extensions` accepted. `extensions` cannot replace `quantity`. |
| Versions | `"1"`, `"1.0.0"`, `"01.0"`, `"1.00"`, `"1.a"`, and `"1.10"` against `"1.9"`. A `1.1` record under a `1.2` registry with a newer-only field. Unsupported older minor. Newer minor. Other major. |
| Hash | Fixed byte sequence and digest. Key order. Comments. Nested `content_sha256`. Array order. `1` against `1.0`. `-0.0` against `0.0`. NFC against NFD. |
| Exit precedence | Missing input plus invalid input gives 2. Corrupt schema gives 3. Unreadable existing file gives 1. No arguments gives 2 with a JSON report. |
| Report | One JSON object on standard output. `exit_code` present. Missing file has no hash. Good and bad inputs together. Two identical runs. |
| Workflow | `permissions: contents: read` is present, without a YAML boolean-key defect |
| Fixtures | No fixture or schema path matches `.gitignore` |

The fixed digest test is mandatory. A hash test that uses `canonical_hash` to make its own expected value proves only that the function agrees with itself.

Acceptance: all groups pass, the fixed digest matches the written bytes, each defect gives the named code and one finding, and the exit code follows P5. Run the commands in proposal section 6.6 and supply the results and file hashes for review under plan section 15.

**Root decisions**

- X5 is closed. Use repository-level `contracts/` with standalone skill copies.
- X2 is closed. The root accepts image disk cost up to 15 GB. No user cleanup is necessary. Remove X2 from the prerequisite table in the next status record.
- B1 does not pull an image. Container selection, the GUI update, supplier formats, package isolation, and release qualification stay in later reviews.

**Limitations**

- I did not run the proposed validator. This review examines the interface and the test design, not an implementation.
- I did not examine a Claude loader or a Codex loader for this batch.
- Library behavior claims for `jsonschema` and `pyyaml` need a direct test on the installed versions. The strict type test is the authority, not this report.
- The B1 test list is a minimum. A later defect can add a test without a new interface decision.
