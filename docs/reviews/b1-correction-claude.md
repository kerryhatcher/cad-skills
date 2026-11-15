# B1 correction record (Claude)

Date: 2026-11-14.

Scope: one correction to B1, as the lead instructed after `b1-review-codex.md` (C1 to C3) and `b1-review-pi.md` (P1 to P3). I did not start B2 to B4. I made no commit, push, or external action.

The first record `b1-implementation-claude.md` and the first manifest `b1-files.sha256` stay unchanged as evidence. This record and `b1-correction-files.sha256` replace them for review.

State: ready for both reviews. I stop implementation edits here.

**1. Findings and changes**

| Finding | Change | Location |
|---|---|---|
| C1: `"1.0\n"` gave `KeyError` and exit 3. A hash with a final newline passed. | The version pattern has no `$` and the parser uses `fullmatch`. Each hash string has `minLength` and `maxLength` of 64. Each date has a length of 10. A URL pattern is `^https?://[^\s]` with a `not` clause for any white space. The `$` boundary is no longer the only guard. | `parse_version`, `VERSION_RE`; board, part and supplier-profile schemas |
| C2: `!!int bad`, `!!float bad` and `!!bool maybe` gave exit 3. | `construct_document` catches `ValueError`, `KeyError` and `OverflowError`. The finding is `file.parse_error`. No other exception becomes a record error. | `parse_record` |
| C3: `10**400` in a number field gave `OverflowError` and exit 3. | `_is_number` accepts a non-boolean `int` without a float conversion. It applies `math.isfinite` only to a `float`. | `_is_number` |
| P1: `canonical_hash` accepted a non-string key, a tuple, and other types. | A recursive check runs before `json.dumps`. It accepts `dict` with `str` keys, `list`, `str`, `bool`, `None`, `int`, and finite `float`. It rejects the rest and a cycle. The finding is `file.not_json_compatible` with a JSON pointer. A deep tree gives the same finding, not `RecursionError`. The bytes for valid data do not change. | `_json_tree_problems`, `canonical_bytes` |
| P2: no scope on a supplier limit. | Each limit has a required `scope`: `fabrication`, `assembly`, or `margin`. The fixture has two new limits (`min_pad_spacing`, `trace_margin`), so each scope occurs. | supplier-profile schema, fixture |
| P3: variant data in the part record. | Decision: `variants.yaml` is the only owner of assembly variants and DNP data. The part record has no such field. B2 checks that the selected variant exists. B9 checks that each variant covers each component reference. The README states this. A test proves that the part schema rejects `assembly_variants`. | `contracts/README.md`, `test_text_limit_unit_and_part_variants` |
| Root: README and limits | Active voice in the hash section. The README states that a text limit omits `unit` and that an empty `unit` is rejected. It states that a plain scalar uses the JSON grammar and that an explicit tag uses the YAML lexical form. It states the binary-float underflow limit (`1e-999` becomes `0.0`). | `contracts/README.md`, `test_documented_limits` |

Not changed, on instruction: the non-blocking observations of the Pi review (temperature range order, unknown stock source, left-handed board axes, duplicate input paths, the code name for a non-string MPN, `patternProperties`, and the two untested codes `file.too_complex` and the CLI outcome of `tool.validator_failure`). I added no advisory feature.

**2. New and changed tests**

`tests/test_pcb_tools.py` now has 32 test functions (24 before). The new functions:

| Test | Cases |
|---|---|
| `test_version_exact_boundaries` | `"1.0\n"`, `"\n1.0"`, `"1.0\r"`, `"1.0\n\n"`, `"1\n.0"`. Each gives `schema.version_malformed` at `/schema_version` and exit 1. |
| `test_fixed_strings_reject_final_newline` | A hash, a date, and a URL, each with a final newline. A URL with a space and a URL with no host. One finding at the exact location each time. A valid hash passes. |
| `test_scalar_tag_values` | The three inputs of C2 and one more, through the CLI. Exit 1, `file.parse_error`, no tool failure. A valid file in the same run is still processed. The accepted explicit forms are fixed (`!!bool yes` is `true`). |
| `test_number_type_checker` | The type checker on `10**400`, booleans, strings, non-finite floats. A record with `10**400` in `width_mm` and `quantity` passes. `-10**400` fails the minimum rule as a record defect. A 401-digit YAML integer does not cause a tool failure. |
| `test_hash_tree_check` | An all-integer key, a boolean key, a null key, a nested integer key, a tuple at the root, a nested tuple, a tuple that equals a list in content, a set, bytes, a date, NaN, a self-referencing dict, a list cycle, a 5000-level tree. A shared (non-cyclic) part is accepted. The fixed digest is unchanged. |
| `test_limit_scope` | A missing scope, seven wrong values, one valid limit of each scope, and a fixture that has all three. |
| `test_text_limit_unit_and_part_variants` | A text limit with no unit passes. An empty, blank or `mil` unit fails. The part record rejects `assembly_variants`. |
| `test_documented_limits` | Underflow gives `0.0` for YAML and JSON. The README contains the documented statements. |

I derived the new regression inputs from the review text: the exact inputs of C1, C2 and C3, and the P1 cases.

**3. Environment and versions**

| Item | Value |
|---|---|
| `uv` | 0.12.5 |
| Python selected by `uv` | 3.13.15 |
| `jsonschema` | 4.26.0 |
| `PyYAML` | 6.0.3 |
| `referencing` | 0.37.0 |
| `rpds-py` | 2026.9.1 |

The PEP 723 pins are unchanged.

**4. Commands and results**

I ran each command with its output in a log file and read the exit code of `uv run` itself.

| Command | Exit code | Result |
|---|---:|---|
| `uv run tests/test_pcb_tools.py` | 0 | 32/32 passed |
| `uv run tests/test_snippets.py` | 0 | 52/52 blocks passed, 5 skipped |
| `uv run tests/test_print_tools.py` | not repeated | The lead stated that the mechanical tests passed twice and that this correction does not change their code. The correction changes the contract files only. |

The first run of the new tests had one failure. It was an error in my test (the cycle location is `/self/self` because the hash function copies the root first). I corrected the test, not the validator. I saved the log files in the session scratchpad. A reboot can clear them.

**5. STE lint**

I ran `uv run /tmp/cad-skills-ste-lint.py` on `contracts/README.md`. Two passive sentences remained after my first edit. I changed both to active voice. Two findings remain. Both are synonym flags for technical terms: `retrieved` against `get` (a field name), and `check` against `validate` (the schema and the validator are different actions). The root lead already judged this kind of flag as not an error.

I also lint-checked the strings that `validate.py` writes (messages, help text, comments, docstrings). I extracted them with an `ast` script and linted the text. The first run found one passive sentence ("The record is nested too deeply."). I changed it to "The record has too many levels." I also changed "needs" to "must have" in a limit message. The second run had zero findings. I read the message list by hand. I kept "Cannot read the file" because the lint does not flag it. The reviewers can decide if "Cannot" needs another form. This check is not an ASD certification.

**6. Process**

All Python ran through `uv run` in this correction, including the schema patch script and the test insertion script. I used `sed` and the edit tool for plain text edits. I regenerated the four schema files with a `uv` script that reads and writes JSON. The variants schema and the registry have the same bytes as before.

**7. Limits**

- The tests run on one host with one Python version.
- The `not` clause for white space in a URL is a JSON Schema rule that Python evaluates with `re.search`. Another JSON Schema engine can behave differently for `$`. Copies of the schemas in other tools need their own test.
- The tag-value fix catches three exception types at the document level. Another exception type from a tag constructor would still give exit 3. I found no such case in the tag set that the loader allows.
- The depth limit of the hash check is the Python recursion limit. The YAML tree walk has the same limit and can still raise `RecursionError` for a very deep file. That case is not in the review findings, and I did not test it.
- `scope` is required for all limits, including `unconfirmed` limits.

**8. Hash manifest**

`docs/reviews/b1-correction-files.sha256` lists the same 17 paths as the first manifest. Verify it with:

```bash
cd /mnt/storage/projects/cad-skills && sha256sum -c docs/reviews/b1-correction-files.sha256
```

The check printed no failure when I made the manifest. Changed files (compared with `b1-files.sha256`):

```text
23f2c750827c3655c6788593c52b8d43e1bf4b38463926cf5e4128eb34761ae5  contracts/README.md
742d90d9cde5b978ddeb627063bfaf91e6aafbac887837009c74fda6c15e9857  contracts/validate.py
c592fa0188a104ff17cd5d75518780164b73eefb1ac264e15bcad94b0cf0589c  contracts/schemas/board.schema.json
a362af28225851449323a95b06ad8e86a389f1b126303760d30ede7d1e804445  contracts/schemas/part.schema.json
702f0f78b8b84fdb2c03b1fafff7004b4fb1fbaf406a26e9c613743ba65f3f38  contracts/schemas/supplier-profile.schema.json
67b3d930227c802ae6ab77ff9daf35ce3681df23e84b2209197551f7bab5404f  tests/test_pcb_tools.py
ad1753aca394240f2a65b71e543a9bbb296cda909d452a1b30bf776341f5dbe5  tests/fixtures/pcb/supplier-profile.yaml
```

Unchanged files (same hash as the first manifest): `.github/workflows/test.yml`, `AGENTS.md`, `README.md`, `ste-glossary.yaml`, `contracts/schemas/registry.json`, `contracts/schemas/variants.schema.json`, `tests/fixtures/pcb/board.yaml`, `part.yaml`, `variants.yaml`, and `docs/reviews/implementation-proposal-claude.md`.

The content hash of the supplier-profile fixture changed from `6232b19b...` to `772c6583...`, because the fixture changed. Digests of the fixed-byte hash test did not change.

**9. For the reviewers**

Examine these points first:

1. `_json_tree_problems` and `canonical_bytes`: a type or a shape that the check accepts but the agreed rules reject.
2. The `not` and length clauses in the three schemas: a fixed-format field that still accepts a final newline.
3. The `construct_document` handler: whether the three exception types are the right set.
4. The new supplier-profile fixture and the `scope` rule.
5. Whether the README states each documented limit that you asked for.

I will not change an implementation file until both reviews arrive.
