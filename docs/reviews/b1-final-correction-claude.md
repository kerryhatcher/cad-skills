# B1 final correction record (Claude)

Date: 2026-11-14.

Scope: one narrow repair, as the lead instructed after `b1-correction-review-pi.md`. Identifier fields and named-map keys now reject control characters. I did not start B234. I made no commit, push, or external action.

Evidence kept unchanged: `b1-implementation-claude.md`, `b1-files.sha256`, `b1-correction-claude.md`, `b1-correction-files.sha256`. This record and `b1-final-files.sha256` replace them for the final review.

State: ready for both reviews. I stop implementation edits here.

**1. Change**

| Item | Change |
|---|---|
| Rule | An identifier field and a key of a named map reject U+0000 to U+001F and U+007F. A schema clause `not: {pattern: "[\\u0000-\\u001f\\u007f]"}` does it. A final newline, a tab, a carriage return and NUL fail. |
| Identifier fields | All short labels in the four schemas: `name`, `supplier.id`, `supplier.service`, `release_revision`, `variant`, `manufacturer`, `mpn`, `package`, `symbol`, `footprint`, `datasheet_revision`, `polarity`, supplier part number `supplier` and `number`, every `unit`, `pin_map` values, profile `id`, `revision`, `service`, `division` names, variant `id`, and `hand_installed.reference`. |
| Named-map keys | `electrical_limits`, `pin_map`, `ratings`, supplier `limits`, and the `references` of a variant. The three maps that had no `propertyNames` (`electrical_limits`, `pin_map`, `ratings`) now have one. |
| Prose (line breaks stay valid) | `restrictions` `text` and `source`, `hand_installed.reason`, `stock.source`, the text `value` of a limit, and `extensions`. |
| Not changed | Spaces, Unicode letters and Unicode normalization. I added no generic string ban. `U+0080` stays valid. |
| MPN code | `part.missing_mpn` now applies to an absent or blank MPN only (the `pattern` error). An MPN with a control character, or a non-string MPN, gives `schema.invalid` at `/mpn`. Before, any `/mpn` error gave `part.missing_mpn`. This is an incidental change in one line of `_schema_findings`. It stops the new control-character case from getting a misleading code. |
| README | `contracts/README.md` lists the rejected characters, the identifier fields, the named maps, and the prose fields. |

The fixed hash bytes, the accepted corrections, and the first B1 behavior do not change.

**2. New tests**

`tests/test_pcb_tools.py` has 35 test functions (32 before). The new functions:

| Test | Cases |
|---|---|
| `test_identifiers_reject_control_characters` | 29 identifier fields and map keys, each with a final newline, in one CLI call with `--json`. The tab and NUL are also tested on three representative cases (`name`, a map key under `electrical_limits`, and a key under `pin_map`). Each case must give exactly one finding: `schema.invalid` at the field or map location. The exit code is 1 and no file is unprocessed. |
| `test_identifiers_keep_spaces_unicode_and_prose_line_breaks` | A name with Unicode letters and a space, `Turnkey PRO`, line breaks in four prose fields, a line break in an `extensions` key and value, and a text limit value with a line break. All pass through the CLI with exit 0. U+0000, U+001F and U+007F fail in `name`. `U+0080` and a normal space pass. The four valid fixtures still pass. |
| `test_mpn_diagnosis` | A blank MPN gives `part.missing_mpn`. An MPN with a final newline or a number gives `schema.invalid`. |

**3. Environment and versions**

| Item | Value |
|---|---|
| `uv` | 0.12.5 |
| Python selected by `uv` | 3.13.15 |
| `jsonschema` | 4.26.0 |
| `PyYAML` | 6.0.3 |
| `referencing` | 0.37.0 |
| `rpds-py` | 2026.9.1 |

**4. Commands and results**

I ran each command with its output in a log file and read the exit code of `uv run` itself.

| Command | Exit code | Result |
|---|---:|---|
| `uv run tests/test_pcb_tools.py` | 0 | 35/35 passed |
| `uv run tests/test_snippets.py` | 0 | 52/52 blocks passed, 5 skipped |
| `uv run tests/test_print_tools.py` | not run | The lead said to run the contract tests only |

I also ran the snippet suite once after the repair. It is a documentation test, not a mechanical rerun, and I should not have added it without an instruction. It passed and changed nothing.

**5. STE lint**

`uv run /tmp/cad-skills-ste-lint.py contracts/README.md`: one passive sentence ("are accepted") in my new text. I changed it to active voice. Two technical-term flags remain, as before: `retrieved` against `get`, and `check` against `validate`. The strings that `validate.py` writes (messages, help text, comments, docstrings): 0 findings. I did not lint the test file or this record.

**6. Limits**

- The rule rejects control characters only. A name can still hold other invisible characters (for example U+200B). The lead asked for no generic string ban and no normalization.
- An identifier field that I did not list can exist in a later schema. B234 must apply the same rule to new identifier fields. The B234 proposal states this.
- The JSON Schema `pattern` clause uses `\u` escapes. Another JSON Schema engine can read the escape in a different way. A copy of the schemas in another tool needs its own test.
- The non-blocking items of earlier reviews are unchanged: the deep-YAML `RecursionError`, underflow, explicit tags, and the observations listed in `b1-correction-review-pi.md` section 4.
- The tests run on one host and one Python version.

**7. Hash manifest**

`docs/reviews/b1-final-files.sha256` lists the same 17 paths as the earlier manifests. Verify it with:

```bash
cd /mnt/storage/projects/cad-skills && sha256sum -c docs/reviews/b1-final-files.sha256
```

The check printed no failure when I made the manifest. Changed files (compared with `b1-correction-files.sha256`):

```text
c19a2045b0b55f177ab9fdd08948694a302fda76af412e9e2803600f5e512658  contracts/README.md
9d0b1702bfed18d50485f6ccd59d2da9eeb14c13e4a3246ccb04cb559178ad97  contracts/schemas/board.schema.json
50e36d4941fe4db3533c0a69f93da3a1c812d5143f569ccc729947daf060e908  contracts/schemas/part.schema.json
29489d3a14d5fd7403ff016200375669ffdd78aae42c24ace821fbf34e9c98ea  contracts/schemas/supplier-profile.schema.json
23fd221c65924bd777f94131a0b1153f1423e06fa4a88f6435d1fb5264106ae7  contracts/schemas/variants.schema.json
4587ac55a991a9b23f16c3e1446eaa54bd62719d0a5a56ffd9a6c1591a23be4b  contracts/validate.py
1627c16d6dd0736d3922b5f27304f9527872a9d4b53ada2df2629ba20b251a39  tests/test_pcb_tools.py
```

Unchanged files: `.github/workflows/test.yml`, `AGENTS.md`, `README.md`, `ste-glossary.yaml`, `contracts/schemas/registry.json`, the four fixtures, and `docs/reviews/implementation-proposal-claude.md`. The fixtures did not change, so every earlier fixture hash stays valid.

**8. For the reviewers**

1. The list of identifier fields and map keys in section 1. Look for a short label in the four schemas that still accepts a control character.
2. The prose list. Look for a prose field that now rejects a line break, or an identifier that stayed in the prose list.
3. The MPN code change in `_schema_findings`.

I will not change an implementation file until both reviews arrive.
