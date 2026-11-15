# B5 setup correction review: Pi

Date: 2026-11-14.

**Decision: N1 to N3 accepted, with one blocking malformed-input correction**

The native-checker repairs N1, N2 and N3 are correct. The focused regression suite passes 12/12 with zero unavailable, including the two fresh KiCad exports.

One concrete defect remains. A malformed schematic can still raise an uncaught `TypeError` and print a traceback, against the record's statement that malformed input gives a problem report. The fix is narrow. The checkpoint correction is not final until it is corrected.

The container setup stays accepted.

**1. Reviewed identity**

| Item | Value |
|---|---|
| Manifest | `docs/reviews/b5-setup-correction-files.sha256` |
| Manifest SHA-256 | `8b73fb3b083e8e75fac4eacfab9447c324f67cdd5173dbced58345e36fda107f` |
| Proposal revision 4 SHA-256 | `458ff984c4a552f2a7a339ec937f6a066b187bb61ea2c210b3cfdba8dea5c0f6` |
| `examples/pcb-trial/scripts/check_native.py` SHA-256 | `d880232daf55c9174a952594bd8061ef8653625ae8c40c0b39b30373269ec857` |
| `tests/test_trial_checker.py` SHA-256 | `7a5c97283c16a6bf3cbf5bc762e8e8a011f19dc97af1a8d21c85f9fb63ee57c2` |
| `examples/pcb-trial/expected/pins.json` SHA-256 | `7e30aa03beea01f1d8ca675d6a008dd5fbc2292d4f139920ef9112dce5425c30` |
| `examples/pcb-trial/expected/netlist.json` SHA-256 | `56db2c74fb63bac9c4f24071c61988b27c5744bda18f7c814673b42989881a7b` |
| `examples/pcb-trial/scripts/sexp.py` SHA-256 | `2dfc36f2bc4141c870de2eb4edb2bc83fd692dedf7c31241aa084f3927e8669a` |

All 16 manifest entries passed before the focused tests and after the focused tests. `git status` shows `examples/pcb-trial/` and `tests/test_trial_checker.py` as new files in the working tree. They are frozen.

**2. N1: duplicate and missing instances — accepted**

`read_instances` builds a list of raw instances. It does not merge by reference.

- A duplicate reference is reported and counted in the raw list. The test `test_duplicate_reference_counts_raw_instances` reports 8 raw instances and the duplicate `MH1`.
- An instance with missing `Reference`, `Value`, `Footprint` or `at` is reported and not counted. `test_missing_mandatory_instance_data` passes.
- A missing expected reference gives a problem and the pin loop skips it. `test_missing_expected_reference_has_no_traceback` runs the CLI, asserts exit 1, and asserts no traceback.
- The exactly-seven test concerns the raw instance list.

**3. N2: netlist map and net names — accepted**

- `read_netlist` reports a repeated `ref.pin` before it writes the map. The rule applies to a repeat in a different net and to a repeat in the same net. `test_duplicate_pin_membership` passes.
- The checker removes at most one leading slash. A `//VIN` export stays `/VIN` and fails the map comparison. `test_double_leading_slash_is_not_normalized` passes.
- The nominal single-slash and no-slash cases pass.
- The fresh export with a renamed label exports `//VIN` and the checker reports the map difference. `test_fresh_export_renamed_label` passes.

**4. N3: measured pin points — accepted**

- The checker measures pin points from the embedded `lib_symbols` text and the instance position. It compares them with the hand-written `expected/pins.json` offsets.
- The sidecar `pin_points.json` does not decide the result. `test_sidecar_does_not_decide` passes.
- A changed embedded pin definition with matching labels is found. `test_changed_embedded_pin_definition` passes, including with an empty sidecar.
- A rotation or a mirror is rejected explicitly. `test_changed_instance_orientation` passes.
- A duplicate pin number in an embedded definition is reported.
- The independent constants did not change. `expected/pins.json`, `expected/netlist.json`, and `EXPECTED_PARTS` keep their earlier values.

**5. Malformed-input reports — one blocking defect**

The existing malformed-input tests pass. They cover an unterminated string, an extra parenthesis, an empty schematic, malformed XML, and an absent XML file.

One path still raises a traceback. Reproduction:

1. Copy the native fixture to a temporary directory.
2. Replace one instance position `(at 101.6 50.8 0)` with `(at (x) 50.8 0)`.
3. Run `uv run examples/pcb-trial/scripts/check_native.py --dir <copy> --netlist <missing> --expected examples/pcb-trial/expected`.

Result: exit 1 through an uncaught `TypeError` in `read_instances` at `float(at[1])`. The output is a traceback, not a problem report.

The record says that malformed input gives a problem report and exit 1. This input does not.

Narrow correction:

1. Add `TypeError` to the exception set that `run` catches around the schematic parse, `read_instances` and `embedded_pins`. Return the problem report for that case.
2. Prefer a specific message for a non-scalar numeric field, for example `the instance position is not a number`.
3. Add a regression that puts a nested list in an `at` field and a regression with a non-scalar property name. Assert exit 1 and no `Traceback` in the output.
4. Keep `sexp.py` unchanged. This is not a general parser change.

**6. Focused regressions**

| Command | Result |
|---|---|
| `uv run tests/test_trial_checker.py` | 12/12 passed, 0 unavailable, exit 0 |

The two fresh-export tests used the derived image through the local tag resolved to its measured ID, with `--pull=never --network none` and a temporary `:Z` mount. They used temporary copies only.

**7. Unchanged independent expectations and fixture scope**

- `expected/pins.json` and `expected/netlist.json` have the same hashes as the setup checkpoint.
- `scripts/sexp.py` did not change. The reader stays a small fixture reader.
- No general parser or symbol renderer was added.
- Unsupported rotations and mirrors fail explicitly.
- The lock count correction is present. The lock file still has 29 pinned package entries and its hash did not change.

**8. Naming note**

`nets_compared` is 10. This value counts ten pin-to-net entries across four distinct nets. It does not count ten distinct nets. Use this wording in the trial record.

**9. Limits**

- I used one host and the existing derived image. I did not rebuild or pull an image.
- I did not relabel the repository. The malformed-input probe used a temporary copy.
- I did not run the SKiDL, identity or GUI steps.
- The focused suite covers the fixture cases, not a general KiCad parser.

**10. Verdict**

N1, N2 and N3 are accepted. The container setup stays accepted.

The checkpoint correction is not final until the malformed-input `TypeError` is caught and tested. After that narrow correction, this part of the setup is ready for the remaining B5 results.

**11. Combined narrow repair agreement**

I read `docs/reviews/b5-setup-correction-review-codex.md`. I agree with its remaining N1 finding and with my malformed-input finding. The combined narrow repair is correct.

Codex finding: `read_instances` silently skips a direct schematic `symbol` without `lib_id`. The comment assigns that case to library definitions, but those definitions are nested under `lib_symbols`. The loop visits direct schematic children only. A malformed extra instance can therefore escape the count and the report.

My finding: a non-scalar numeric field, for example `(at (x) 50.8 0)`, raises an uncaught `TypeError` at `float(at[1])`. The CLI prints a traceback instead of a problem report.

Combined repair:

1. In `read_instances`, require a usable `lib_id` for each direct schematic symbol. If `lib_id` is absent, not a list, or has no nonblank name, add a problem and do not count that symbol. Do not skip it silently.
2. Keep the existing checks for `Reference`, `Value`, `Footprint` and `at`.
3. Add `TypeError` to the exceptions that `run` catches around the schematic parse, `read_instances` and `embedded_pins`. Return a problem report. When practical, name the non-scalar field in the message.
4. Add focused CLI regressions in `tests/test_trial_checker.py` for these three cases:
   - a direct malformed extra instance with no usable `lib_id`
   - a nested list in an `at` value
   - a non-scalar property name
   Each regression must run the checker as a process, assert exit 1, and assert that no `Traceback` text appears.
5. Keep `scripts/sexp.py` unchanged.
6. Keep `expected/pins.json`, `expected/netlist.json` and `EXPECTED_PARTS` unchanged.
7. Do not add a general parser or symbol renderer.

I agree with this scope. The container setup stays accepted. The checkpoint correction is not final until the combined repair and the three focused regressions pass.

I did not run new probes for this agreement. The Codex reproduction, my reproduction and the frozen source are sufficient evidence.

This review changes only this report. It makes no implementation edit.
