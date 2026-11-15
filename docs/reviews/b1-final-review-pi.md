# B1 final review: Pi

Date: 2026-11-14.

Reviewed state: frozen B1 final correction. `docs/reviews/b1-final-files.sha256` identifies the reviewed files. `sha256sum -c docs/reviews/b1-final-files.sha256` passed for all 17 entries. No implementation file changed during this review.

Reviewed sources: `docs/reviews/b1-final-correction-claude.md`, `docs/reviews/b1-final-files.sha256`, the four schemas, `contracts/validate.py`, `tests/test_pcb_tools.py`, and `contracts/README.md`.

Scope: the identifier and control-character correction, CLI regressions, the prior fixes, and the fixed hash bytes. This review does not repeat the mechanical suites and does not add a B1 feature.

**Decision**

I accept the B1 final correction. No scope-specific blocker remains.

The identifier rule is complete for the four schemas. The prose fields keep line breaks. The prior fixes and the fixed hash bytes remain. The contract tests pass. B234 can use the repaired B1 routines.

**1. Commands and results**

| Command | Result |
|---|---|
| `sha256sum -c docs/reviews/b1-final-files.sha256` | All 17 files OK. |
| `uv run tests/test_pcb_tools.py` | 35/35 passed, exit 0. |
| Independent `printf ... \| sha256sum` fixed-digest check | The two expected digests are unchanged: `225bf4f028ae2296b75f18a67cb6adae61f78d2c2f6005866e8de7b3f907c0d4` and `cbab099b9ffd6ef044f8fce49e98d7b42847e3661c255fb1fb10f107b90cdd0f`. |
| CLI check, board with `name: "board\n"` | Exit 1, `schema.invalid` at `/name`. |
| CLI check, valid fixtures | Exit 0. |

The mechanical suites were not repeated. The correction does not change their files.

**2. Identifier and control-character correction**

The schema clause `not: {pattern: "[\\u0000-\\u001f\\u007f]"}` is present on every identifier field and every named-map key in the four schemas. Independent enumeration found no missed identifier that uses `pattern: "\\S"` without the clause.

Covered identifier fields include board `name`, supplier `id` and `service`, `release_revision`, `variant`, part `manufacturer`, `mpn`, `package`, `symbol`, `footprint`, `datasheet_revision`, `polarity`, supplier part `supplier` and `number`, every `unit`, `pin_map` values, profile `id`, `revision`, `service`, division names, variant `id`, and `hand_installed.reference`.

Covered named-map keys are `electrical_limits`, `pin_map`, `ratings`, supplier `limits`, and variant `references`. The maps that had no `propertyNames` now have it.

Prose fields still accept line breaks: `restrictions` `text` and `source`, `hand_installed.reason`, `stock.source`, the text `value` of a limit, and `extensions`.

Independent checks:

| Input | Result |
|---|---|
| Identifier with a final newline | One `schema.invalid` at the field or map. |
| Identifier with a tab or NUL | Fails on the representative cases. |
| `service: "Turnkey PRO"` | Passes. |
| `name` with Unicode letters and a space | Passes. |
| Prose with a line break | Passes. |
| `U+0080` in a name | Passes. This is outside the requested range. |
| `U+200B` in a name | Passes. This is outside the requested range and is a known limit. |
| A final newline in a hash, date, URL or version | Fails. The fixed-format correction remains. |

**MPN diagnosis**

The incidental code change is correct. A blank MPN `" "` gives `part.missing_mpn`. An MPN with a control character gives `schema.invalid`. A numeric MPN gives `schema.invalid`. An absent MPN gives `part.missing_mpn`. A newline-only MPN can give `schema.invalid` because it has both a blank and a control defect. This is acceptable. The record is rejected.

**3. Regression checks**

| Area | Result |
|---|---|
| P1 hash value tree | An all-integer key, a boolean key, and a tuple give `file.not_json_compatible`. The fixed digest is unchanged. |
| P2 supplier scope | The fixture has all three scopes. A missing or wrong scope fails. |
| P3 part variant ownership | The part schema rejects `assembly_variants`. The README states that `variants.yaml` owns the data. |
| P4 fixed formats | A final newline fails for a hash, date, URL and version. |
| P5 scalar construction | `!!int 0x`, `!!int 0b2` and `!!int 1e` give `file.parse_error`, not a tool failure. |
| P6 large integer | `10**400` in a number field passes or gives a record finding. It does not give exit 3. |
| CLI report and exit codes | The contract suite covers pass, fail, argument error, missing input, tool failure, and independent files. All pass. |
| Valid fixtures | All four pass. |
| Fixed hash bytes | Unchanged. |

**4. Non-blocking limits**

| Item | Observation |
|---|---|
| U+0080 to U+009F | These C1 controls pass. The requested range was U+0000 to U+001F and U+007F. |
| U+200B | A zero-width space passes. The root asked for no generic string ban and no normalization. |
| Deep YAML | A very deep YAML tree can still give `RecursionError` and exit 3. The correction record states this limit. It is outside this narrow correction. |
| Underflow | `1e-999` becomes `0.0`. The README documents this limit. |
| Explicit tags | `!!bool yes` is `true` and `!!int 0x10` is `16`. The README documents the lexical rule. |
| Schema portability | The `not` clause uses `\u` escapes and `pattern` search behavior. Another JSON Schema engine needs its own test. |
| One host | The tests run on one host and one Python version. |

These limits do not block acceptance.

**5. Reviewed hashes**

Manifest and record:

| File | SHA-256 |
|---|---|
| `docs/reviews/b1-final-files.sha256` | `dbd7c761bcfae4143d1842a34efc3f22b43a36c98a0a8c6843a1ed24593f93fa` |
| `docs/reviews/b1-final-correction-claude.md` | `a0e9053037da9c15f3af7aca6717b59bb3dac20b7075d79df1b890c590baa9bf` |

Changed files under the final manifest:

| File | SHA-256 |
|---|---|
| `contracts/README.md` | `c19a2045b0b55f177ab9fdd08948694a302fda76af412e9e2803600f5e512658` |
| `contracts/validate.py` | `4587ac55a991a9b23f16c3e1446eaa54bd62719d0a5a56ffd9a6c1591a23be4b` |
| `contracts/schemas/board.schema.json` | `9d0b1702bfed18d50485f6ccd59d2da9eeb14c13e4a3246ccb04cb559178ad97` |
| `contracts/schemas/part.schema.json` | `50e36d4941fe4db3533c0a69f93da3a1c812d5143f569ccc729947daf060e908` |
| `contracts/schemas/supplier-profile.schema.json` | `29489d3a14d5fd7403ff016200375669ffdd78aae42c24ace821fbf34e9c98ea` |
| `contracts/schemas/variants.schema.json` | `23fd221c65924bd777f94131a0b1153f1423e06fa4a88f6435d1fb5264106ae7` |
| `tests/test_pcb_tools.py` | `1627c16d6dd0736d3922b5f27304f9527872a9d4b53ada2df2629ba20b251a39` |

The other 10 manifest paths are unchanged from `b1-correction-files.sha256`. Their reviewed hashes are in `docs/reviews/b1-correction-review-pi.md` section 5. The manifest check passed for all 17.

**6. Next step**

B1 is accepted at this correction. B234 uses the repaired `parse_record`, `canonical_hash`, strict type checker, and identifier rule. B234 must apply the same control-character rule to each new identifier and path field.

This review changes no implementation file. It does not request a contract commit.
