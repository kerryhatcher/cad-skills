# B5 setup final review: Pi

Date: 2026-11-14.

**Decision: accepted**

The combined narrow checker repair is correct. The missing or unusable `lib_id` guard, the non-scalar field reports, and the three CLI regressions pass. No blocking defect remains in this correction.

N1 to N3 semantics, the container setup, the parser scope, and the independent expectations stay accepted.

**1. Reviewed identity**

| Item | Value |
|---|---|
| Manifest | `docs/reviews/b5-setup-final-files.sha256` |
| Manifest SHA-256 | `2e90992f2c2dc9ed164843f4e6a25690c10a444d356082fcb4b4ba2ed51888d7` |
| Proposal revision 4 SHA-256 | `458ff984c4a552f2a7a339ec937f6a066b187bb61ea2c210b3cfdba8dea5c0f6` |
| `examples/pcb-trial/scripts/check_native.py` SHA-256 | `eb75945634f927f849de3faf356090ab94fcd2f73246e39202ea1f41a56e009e` |
| `tests/test_trial_checker.py` SHA-256 | `38fb89065a9f2680ef3cc8137317cb0ca42657c3f3167dbe048c3265dec6152f` |
| `examples/pcb-trial/expected/pins.json` SHA-256 | `7e30aa03beea01f1d8ca675d6a008dd5fbc2292d4f139920ef9112dce5425c30` |
| `examples/pcb-trial/expected/netlist.json` SHA-256 | `56db2c74fb63bac9c4f24071c61988b27c5744bda18f7c814673b42989881a7b` |
| `examples/pcb-trial/scripts/sexp.py` SHA-256 | `2dfc36f2bc4141c870de2eb4edb2bc83fd692dedf7c31241aa084f3927e8669a` |

All 16 manifest entries passed before the focused tests and after the focused tests. Only `check_native.py` and `tests/test_trial_checker.py` differ from `b5-setup-correction-files.sha256`.

`git status` shows `examples/pcb-trial/` and `tests/test_trial_checker.py` as new files in the working tree. They are frozen.

**2. Missing or unusable `lib_id` guard — accepted**

`read_instances` now treats each direct schematic `symbol` as an instance. A missing, nested, or blank `lib_id` gives the problem `symbol N misses mandatory data: lib_id`. The old loop skipped that symbol.

Independent probe: add a direct extra symbol with no `lib_id` to a temporary native copy. Run the CLI with a nominal XML map.

Result: exit 1. The report gives `"instances": 7` and the `misses mandatory data: lib_id` problem. No traceback.

The library definitions stay inside `lib_symbols`. The guard does not reject them.

**3. Non-scalar field reports — accepted**

`as_number` returns a float. A nested list or a non-numeric text gives a clear `... is not a number` message. It covers the instance x, y and rotation, and the embedded pin positions. A property name or value that is a list gives `... not text`. `run` also keeps `TypeError` in its exception set as a backstop.

Independent probe: replace one instance position with `(at (x) 50.8 0)` in a temporary copy. Run the CLI.

Result: exit 1. The report contains `is not a number`. No traceback.

The non-scalar property case is covered by the focused test `test_non_scalar_property_gives_a_report`.

**4. Three CLI regressions — accepted**

The test file adds and passes these cases:

| Test | Case |
|---|---|
| `test_malformed_extra_symbol_with_seven_valid_instances` | Seven valid instances plus an extra symbol with no `lib_id`, a nested `lib_id`, or a blank `lib_id`. Exit 1. The report counts 7 instances and names the missing `lib_id`. No traceback. |
| `test_nested_at_value_gives_a_report` | `(at (x) 50.8 0)` and `(at abc 50.8 0)`. Exit 1 with `is not a number`. No traceback. |
| `test_non_scalar_property_gives_a_report` | A nested property name and a nested property value. Exit 1 with `not text`. No traceback. |

Each test runs the checker as a process and asserts the exit code and the absence of `Traceback` text.

**5. Focused suite**

| Command | Result |
|---|---|
| `uv run tests/test_trial_checker.py` | 15/15 passed, 0 unavailable, exit 0 |

The two fresh KiCad export tests use the existing derived image, `--pull=never`, `--network none`, and a temporary `:Z` mount. They used temporary copies only.

**6. Unchanged scope**

- `expected/pins.json` and `expected/netlist.json` retain their earlier hashes.
- `scripts/sexp.py` did not change.
- `EXPECTED_PARTS` did not change.
- No general parser or symbol renderer was added.
- Unsupported rotations and mirrors fail explicitly.
- The lock count correction stays present.

**7. Naming note**

`nets_compared` is 10. This value counts ten pin-to-net entries across four distinct nets. It does not count ten distinct nets. Use this wording in the trial record.

**8. Limits**

- I used one host and the existing derived image. I did not rebuild or pull an image.
- I did not relabel the repository. The probes used temporary copies.
- I did not run the SKiDL, identity or GUI steps.
- This is a small fixture reader, not a general KiCad parser.

**9. Verdict**

The combined narrow checker repair is accepted. The container setup stays accepted.

This part of the setup is ready for the remaining B5 results.

This review changes only this report. It makes no implementation edit.
