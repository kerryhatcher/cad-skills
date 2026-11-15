# B5 setup correction record (Claude)

Date: 2026-11-14.

Scope: the native-checker repairs N1 to N3 of `b5-setup-review-codex.md`, accepted by the lead and confirmed by Pi (`b5-setup-review-pi.md`, section 11), and the lock count correction. I made no commit, no push, no image rebuild, and no change to a B234 file. The first setup manifest `b5-setup-files.sha256` and the checkpoint record `b5-checkpoint-claude.md` stay unchanged as evidence.

State: ready for both reviewers. I stop edits to these files here.

**1. Count correction**

The checkpoint record says that `requirements.lock` has 28 pinned packages. The correct count is 29 (`grep -cE '^[A-Za-z0-9_.-]+=='` gives 29). The SHA-256 of the lock file, `f505b04d9bc3588c10d66954aba4b7eab6f6f8ad0cbf517b39b97fa544b7de15`, did not change.

**2. Repairs in `examples/pcb-trial/scripts/check_native.py`**

| ID | Defect | Repair |
|---|---|---|
| N1 | A duplicate reference replaced an earlier instance, and a missing reference raised `KeyError` | The checker reads a list of raw instances and counts that list. A duplicate reference is a problem. An instance with missing mandatory data (`Reference`, `Value`, `Footprint`, `at`) is a problem and is not counted. A missing expected reference is a problem, and the pin loop skips it. No traceback. |
| N2 | A repeated pin membership disappeared, and `lstrip('/')` hid a double slash | A repeated pin key is a problem, including a repeat in the same net. The checker removes at most one leading slash from a net name. A name `//VIN` stays `/VIN` and fails the map comparison. |
| N3 | The pin position test trusted the generated sidecar | The checker measures pin points from the embedded `lib_symbols` text and the instance position. It compares them with the hand-written offsets in `expected/pins.json`. A rotation or a mirror of an instance is not supported by this fixture and is a problem. A duplicate pin number in a definition is a problem. `pin_points.json` is diagnostic only. |

Malformed input gives a problem report and exit 1: an unreadable or malformed schematic, a malformed or missing netlist, and an unterminated string or an extra parenthesis. `sexp.py` did not change. The reader is small and made for this fixture. It is not a general KiCad parser. The independent constants (`EXPECTED_PARTS`, `expected/pins.json`, `expected/netlist.json`) did not change.

**3. Tests (`tests/test_trial_checker.py`)**

| Test | Case |
|---|---|
| `test_nominal` | 7 instances, 10 pins, 10 nets, no problem |
| `test_duplicate_reference_counts_raw_instances` | A copy of `MH1` with a new UUID: 8 raw instances and a duplicate finding |
| `test_missing_expected_reference_has_no_traceback` | `R2` removed: problem report, exit 1, no traceback (CLI run) |
| `test_missing_mandatory_instance_data` | `Footprint` removed from `R1`, and an instance with no position |
| `test_duplicate_pin_membership` | `R1.1` added to `/GND` before `/VIN`, and a repeat in the same net |
| `test_double_leading_slash_is_not_normalized` | Net names `//…` fail. Names with one slash and with no slash pass. |
| `test_changed_embedded_pin_definition` | Pin 1 of the embedded `Device:R` moved by 2.54 mm and the matching labels of `R1` and `R2` moved. The sidecar is unchanged or empty. The checker finds the embedded pin points. |
| `test_changed_instance_orientation` | `C1` at 90 degrees, and a mirror on `R1`: unsupported transformation |
| `test_sidecar_does_not_decide` | A wrong sidecar and a good schematic: no problem |
| `test_malformed_inputs_give_a_report` | Unterminated string, extra parenthesis, empty file, malformed XML, absent XML: problem report, no traceback |
| `test_fresh_export_changed_definition` | A fresh KiCad XML export from the trial container, for the nominal fixture (passes) and for the changed definition (the connectivity is unchanged, and the embedded pin points are found) |
| `test_fresh_export_renamed_label` | Labels `VIN` renamed `/VIN`: KiCad exports `//VIN`, and the checker finds the map difference |

The two fresh-export tests run `podman` with the local image by `--pull=never --network none` and a temporary `:Z` mount. They show `unavailable` if podman or the image is absent.

**4. Commands and results**

| Command | Exit | Result |
|---|---:|---|
| `uv run tests/test_trial_checker.py` | 0 | 12/12 passed, 0 unavailable (log `checker_tests_003.out`) |
| The nominal checker on a fresh export in the container (`N_nominal_111`, then `check_native.py`) | 0 | 7 instances, 10 pins, 10 nets, no problem (log `checker_nominal_004.out`) |

The first run of the new tests had a test error of mine (a sort key), logged as `checker_tests_001.out`. The second run had one test expectation error for an empty file, logged as `checker_tests_002.out`. Both logs are kept in `<scratchpad>/b5/logs`.

**5. Hash manifest**

`docs/reviews/b5-setup-correction-files.sha256` lists 16 files: the 15 setup files and the new test file. `sha256sum -c` shows no failure. One file has a new hash compared with `b5-setup-files.sha256`: `examples/pcb-trial/scripts/check_native.py`, SHA-256 `d880232daf55c9174a952594bd8061ef8653625ae8c40c0b39b30373269ec857`.

**6. Limits**

- Unsupported instance transformations fail explicitly. The fixture needs none.
- The checker does not render symbols. It measures the pin points in the embedded definitions at the instance position, with no rotation.
- The fresh-export tests need podman and the local image.
- STE lint was not run on this record.
