# B5 setup final correction record (Claude)

Date: 2026-11-14.

Scope: the combined narrow checker repair that both reviewers agree on (`b5-setup-correction-review-pi.md` and `b5-setup-correction-review-codex.md`), authorized by the lead for `examples/pcb-trial/scripts/check_native.py` and `tests/test_trial_checker.py`. My first edit attempt was blocked by the permission classifier. I did not use another route. After the lead's explicit authorization, the same edit succeeded. I made no commit, push, or image rebuild. `sexp.py`, `expected/pins.json` and `expected/netlist.json` did not change.

The earlier manifests (`b5-setup-files.sha256`, `b5-setup-correction-files.sha256`) and records stay as evidence.

**Repairs in `check_native.py`**

| Guard | Change |
|---|---|
| Direct symbol with a missing or unusable `lib_id` | A direct child `symbol` of the schematic is an instance. A missing, nested, or blank `lib_id` is a problem (`symbol N misses mandatory data: lib_id`). The old loop skipped it. The library definitions are inside `lib_symbols`, so no instance is skipped by mistake. |
| Non-scalar number | `as_number` returns a float. A nested list or a text that is not a number gives a clear message (`... is not a number`). It covers the instance x, y and rotation, and the embedded pin positions. |
| Non-scalar property | A property name or value that is a list is a problem (`... not text`). |
| Backstop | `TypeError` is in the set of exceptions that `run` turns into a problem report. |

**New CLI regressions in `tests/test_trial_checker.py`** (15 tests now; 12 before)

- `test_malformed_extra_symbol_with_seven_valid_instances`: seven valid instances plus an extra symbol with no `lib_id`, a nested `lib_id`, or a blank `lib_id`. Exit 1, the report counts 7 instances and names the missing `lib_id`, no traceback.
- `test_nested_at_value_gives_a_report`: `(at (x) 50.8 0)` and `(at abc 50.8 0)`. Exit 1, "is not a number", no traceback (with a present and with a missing netlist).
- `test_non_scalar_property_gives_a_report`: a nested property name and a nested property value. Exit 1, "not text", no traceback.

**Results**

`uv run tests/test_trial_checker.py` exit 0, 15/15 passed, 0 unavailable (log `checker_tests_005.out`, including the two fresh KiCad exports). The nominal fixture still passes.

**Hash manifest**

`docs/reviews/b5-setup-final-files.sha256` lists the same 16 paths. `sha256sum -c` shows no failure. Two files have a new hash compared with `b5-setup-correction-files.sha256`:

```text
eb75945634f927f849de3faf356090ab94fcd2f73246e39202ea1f41a56e009e  examples/pcb-trial/scripts/check_native.py
38fb89065a9f2680ef3cc8137317cb0ca42657c3f3167dbe048c3265dec6152f  tests/test_trial_checker.py
```

Limits: this is a small reader for this fixture, not a general KiCad parser. STE lint was not run on this record.
