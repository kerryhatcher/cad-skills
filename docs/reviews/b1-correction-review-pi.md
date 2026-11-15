# B1 correction review: Pi

Date: 2026-11-14.

Reviewed state: frozen B1 correction. `docs/reviews/b1-correction-files.sha256` identifies the reviewed files. `sha256sum -c docs/reviews/b1-correction-files.sha256` passed for all 17 entries. No implementation file changed during this review.

Reviewed sources: `docs/reviews/b1-correction-claude.md`, `docs/reviews/b1-correction-files.sha256`, the changed contract files, `tests/test_pcb_tools.py`, the supplier-profile fixture, and `contracts/README.md`.

Scope: the prior findings P1 to P6, the changed files, and regressions. This review does not repeat the mechanical tests. The correction changes no mechanical code.

**Decision**

The correction is not accepted yet. One concrete blocker remains: P4 is only partly fixed. Every other correction is accepted.

The blocker is small. The fixed-format fields are correct. The free identifier fields and the named-map keys still accept a control character, including a final newline.

**1. Commands and results**

| Command | Result |
|---|---|
| `sha256sum -c docs/reviews/b1-correction-files.sha256` | All 17 files OK. |
| `uv run tests/test_pcb_tools.py` | 32/32 passed, exit 0. |
| Independent fixed-digest check with `printf ... \| sha256sum` | The two expected digests are unchanged: `225bf4f028ae2296b75f18a67cb6adae61f78d2c2f6005866e8de7b3f907c0d4` and `cbab099b9ffd6ef044f8fce49e98d7b42847e3661c255fb1fb10f107b90cdd0f`. |
| `uv run contracts/validate.py` on a board with `name: "board\n"` | Exit 0, status pass. This is the blocker. |

The mechanical tests were not repeated. The correction does not change their files.

**2. Accepted corrections**

| Finding | Result |
|---|---|
| P1 hash value tree | `canonical_hash` rejects an all-integer key, a boolean key, a tuple, a set, and bytes with `file.not_json_compatible`. A cycle and a deep tree give one finding, not a crash. A shared non-cyclic part is accepted. The fixed digests are unchanged. |
| P2 supplier scope | Each limit requires `scope` of `fabrication`, `assembly` or `margin`. The fixture has all three. A missing or wrong scope fails. |
| P3 part variant ownership | The part schema rejects `assembly_variants`. `contracts/README.md` states that `variants.yaml` owns assembly variant and DNP data. |
| P4 fixed formats | A final newline fails for `profile_sha256`, `evidence_sha256`, `content_sha256`, a date, a URL, and a version. `parse_version` uses `fullmatch`. The hash and date fields have exact length bounds. |
| P5 scalar construction | `!!int 0x`, `!!int 0b2` and `!!int 1e` give `file.parse_error` with exit 1. They no longer give `tool.validator_failure` with exit 3. |
| P6 large integer | `10**400` in a number field passes or gives a record finding. It no longer gives an `OverflowError` or exit 3. A large negative integer fails the minimum rule as a record defect. |
| README limits | The README states the text-limit unit rule, the explicit-tag lexical rule, and the binary-float underflow limit. |

The fixed-format part of P4 is correct. The remaining part is below.

**3. Remaining blocker: P4 covers identifiers only in part**

Prior finding P4 asked for a whole-string check for every constrained string, and for control-character rejection in identifiers. The correction applies the rule to hashes, dates, URLs and versions. It does not apply the rule to free identifier fields or to named-map keys.

A free string with `pattern: "\\S"` accepts a trailing newline or tab, because `re.search` finds a non-space character anywhere in the string.

Evidence from this review:

- The CLI accepts a board with `name: "board\n"` and exits 0.
- In-process validation accepts a trailing newline in `name`, `manufacturer`, `mpn`, `package`, `symbol`, `footprint`, `datasheet_revision`, `polarity`, `supplier.id`, `supplier.service`, `release_revision`, `variant`, `profile.id`, `profile.revision`, and `profile.service`.
- A limit name with a newline passes the map-key check.
- The same gap applies to `variants.references` keys, `hand_installed.reference`, `pin_map` keys, `ratings` keys, `electrical_limits` keys, `division` limit names, and `supplier_part_numbers` supplier and number values.

This is a manufacturing-data risk. An MPN, footprint, reference, or limit name with a control character can break later matching, file names, and supplier data. The plan requires exact identifiers.

Minimum correction:

1. Add a control-character rejection to every identifier field and to every named-map key. A JSON Schema clause is sufficient: `"not": {"pattern": "[\\u0000-\\u001f\\u007f]"}`.
2. Keep spaces. A service name such as `Turnkey PRO` must pass.
3. Apply the clause to the identifier fields and map keys listed above.
4. Keep line breaks in prose fields such as `reason`, `text`, `source` and `notes`.
5. Add `propertyNames` to `pin_map`, `ratings`, and `electrical_limits` when it is absent.
6. Update `contracts/README.md`. State that identifiers and map keys reject control characters, and that prose may contain line breaks.

Minimum tests:

1. A trailing newline fails for each identifier field and each named-map key.
2. A tab and a NUL fail for one representative field.
3. A normal space in `service` passes.
4. A newline in a prose field passes.
5. The valid fixtures still pass.

This is a correction to the prior finding, not new scope.

**4. Non-blocking limits**

| Item | Observation |
|---|---|
| Deep YAML tree | A very deep YAML file can raise `RecursionError` before the node limit. `parse_record` catches only `yaml.YAMLError`. Through the CLI this gives `tool.validator_failure` and exit 3. The correction record states this limit. A later correction can catch `RecursionError` around the YAML walk and report `file.parse_error` or `file.too_complex`. |
| Underflow | `1e-999` becomes `0.0`. The README states this limit. The prior review accepted it as a limit. |
| Explicit tags | `!!bool yes` is `true` and `!!int 0x10` is `16`. The README states the lexical rule. The prior review accepted this as a documented choice. |
| Other observations | The prior non-blocking observations (temperature range order, unknown stock source, left-handed board axes, duplicate input paths, the MPN code name, `patternProperties`, and the two untested codes) were not changed on instruction. They do not block the correction. |
| Portability | The URL `not` clause and the `$` behavior of `pattern` can differ in another JSON Schema engine. B234 already states this limit. |
| One host | The tests run on one host and one Python version. |

**5. Reviewed hashes**

Manifest hash:

| File | SHA-256 |
|---|---|
| `docs/reviews/b1-correction-files.sha256` | `1fcfcb003900b0c66b8bbd832d50e7c8b62809d50882586cf7b5c3e49694b8b2` |
| `docs/reviews/b1-correction-claude.md` | `44b96e82e963303651eb5a35c58ca9681a7a4113eccff3b4253a687423adc3d9` |

Reviewed files, all `OK` under the manifest:

| File | SHA-256 |
|---|---|
| `.github/workflows/test.yml` | `cff2b7454554dfe8886f30c46b4646034842f0204f20fa09b2c4128ef730912e` |
| `AGENTS.md` | `fb9ae245c827aa88162e0c4a7bcf4b336a06f46c45fcf4ce9f97a536e3a08f6f` |
| `README.md` | `95f6528c941a54010aca2e36fdf7e80675f14804221f213b84b44c9c5bd493ad` |
| `ste-glossary.yaml` | `bf27f15bcecca96a57779f36574bef7070ced560767e24a57b6901a44758e77d` |
| `contracts/README.md` | `23f2c750827c3655c6788593c52b8d43e1bf4b38463926cf5e4128eb34761ae5` |
| `contracts/validate.py` | `742d90d9cde5b978ddeb627063bfaf91e6aafbac887837009c74fda6c15e9857` |
| `contracts/schemas/registry.json` | `0569f758f83b0e3f3e1652e40eea8e373780993b1f65ecaeaef902a88aab0121` |
| `contracts/schemas/board.schema.json` | `c592fa0188a104ff17cd5d75518780164b73eefb1ac264e15bcad94b0cf0589c` |
| `contracts/schemas/part.schema.json` | `a362af28225851449323a95b06ad8e86a389f1b126303760d30ede7d1e804445` |
| `contracts/schemas/supplier-profile.schema.json` | `702f0f78b8b84fdb2c03b1fafff7004b4fb1fbaf406a26e9c613743ba65f3f38` |
| `contracts/schemas/variants.schema.json` | `53755cd7d4f79e604329b1e8369bce34fa4f9d820b6002bff3ff9e34b9755901` |
| `tests/test_pcb_tools.py` | `67b3d930227c802ae6ab77ff9daf35ce3681df23e84b2209197551f7bab5404f` |
| `tests/fixtures/pcb/board.yaml` | `91b45de6c27e9bf7aa1b374804fda06759fa0c9f8efd2b4cb74e372ee9aba164` |
| `tests/fixtures/pcb/part.yaml` | `d0ed30f2a583cd50d280db68b2cc0d24dd98f0f8e6749167a2feb88b25ccd0a2` |
| `tests/fixtures/pcb/supplier-profile.yaml` | `ad1753aca394240f2a65b71e543a9bbb296cda909d452a1b30bf776341f5dbe5` |
| `tests/fixtures/pcb/variants.yaml` | `3ee364f38d83f1a9a8671d719e003474c5da170096c2ca4c72d8b03a9f895ac5` |
| `docs/reviews/implementation-proposal-claude.md` | `6b1c8dd331ea3d365e0188322e6d76937e002c6a496c006e09b3667d903aa729` |

The first B1 manifest and record stay unchanged as evidence. The first manifest hash is `04a8ef4f4a05f4adf1303c6d33eaa23683c49305f2d1c8128499e9490d179b31`.

**6. Next step**

Claude adds the control-character rejection for the identifier fields and named-map keys, updates the README, and adds the named tests. The fixed hash bytes and the accepted corrections do not change. Claude supplies a new correction manifest. Both reviewers check the new hashes and rerun the contract tests.

B2 to B4 must use the repaired B1 routines. The B234 plan already states that rule.

This review changes no implementation file. It does not request a contract commit.
