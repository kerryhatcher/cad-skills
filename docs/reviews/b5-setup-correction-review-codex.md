# B5 native-checker correction review: Codex

Date: 2026-11-14.

**Decision: one N1 correction remains**

I accept N2 and N3. The duplicate-reference and missing-reference repairs also pass. One malformed-instance case still gives a false pass.

Setup acceptance remains unchanged. This review adds no general parser or renderer feature.

**Reviewed hashes**

Manifest: `docs/reviews/b5-setup-correction-files.sha256`.

Manifest SHA-256: `8b73fb3b083e8e75fac4eacfab9447c324f67cdd5173dbced58345e36fda107f`.

All 16 entries passed before and after review. The changed checker and new test have these hashes:

```text
d880232daf55c9174a952594bd8061ef8653625ae8c40c0b39b30373269ec857  examples/pcb-trial/scripts/check_native.py
7a5c97283c16a6bf3cbf5bc762e8e8a011f19dc97af1a8d21c85f9fb63ee57c2  tests/test_trial_checker.py
```

The independent expectation files retain their original hashes:

```text
7e30aa03beea01f1d8ca675d6a008dd5fbc2292d4f139920ef9112dce5425c30  examples/pcb-trial/expected/pins.json
56db2c74fb63bac9c4f24071c61988b27c5744bda18f7c814673b42989881a7b  examples/pcb-trial/expected/netlist.json
```

**Remaining N1 defect**

Location: `examples/pcb-trial/scripts/check_native.py:50`.

`read_instances` silently skips a top-level `symbol` without `lib_id`. The comment attributes this case to library definitions. Those definitions are nested under `lib_symbols`. This loop visits direct schematic children only.

Reproduction in a temporary native copy: add this direct child before the final schematic parenthesis:

```text
(symbol (at 200 200 0)
  (property "Reference" "EXTRA")
  (property "Value" "bad")
  (property "Footprint" "bad"))
```

Run the CLI checker with the nominal XML map. It returns exit 0 and this report:

```json
{"instances": 7, "pins_compared": 10, "nets_compared": 10, "problems": []}
```

The schematic contains an extra malformed instance. The agreed N1 rule says to reject missing mandatory instance data rather than silently omit it.

Add a problem when a direct symbol lacks a usable `lib_id`. Preserve the no-traceback behavior. Add a CLI regression with seven valid instances plus this malformed extra instance. It must return exit 1 and identify the missing mandatory data. This is a small guard in the existing loop.

**Accepted corrections and tests**

`uv run tests/test_trial_checker.py` passed: 12/12, zero unavailable. The local image tag resolved to the authorized derived ID:

```text
d881df4ef3e2ec76995f4070596550db118b23e7f6db9017f09a418c44c4b1c2
```

The tests used temporary copies, `--network none`, and `--pull=never`. I did not rebuild or pull an image.

The suite confirms these repairs:

- Duplicate references and pin memberships produce problems.
- A missing expected reference produces a report without a traceback.
- Net-name comparison removes at most one leading slash.
- Pin checks measure embedded definitions rather than the sidecar.
- Unsupported instance rotations and mirrors fail explicitly.
- Malformed schematic syntax and XML produce problem reports.
- Fresh KiCad exports retain the changed-pin and renamed-label negative results.

The nominal result means seven instances and ten pin-to-net entries across four nets. `nets_compared: 10` does not mean ten distinct nets.

The remaining N1 probe used the CLI independently of the supplied suite. All frozen hashes remained unchanged. I ran no unrelated suites and changed only this report.

**Combined narrow repair — explicit agreement**

I read `b5-setup-correction-review-pi.md`. I agree with Pi's malformed-field finding and the root's combined repair scope.

- Reject a direct symbol with a missing or unusable `lib_id`.
- Report a malformed non-scalar field as a problem, including `TypeError`, without a traceback.
- Add CLI regressions for the malformed extra instance, a nested `at` value, and a non-scalar property name.
- Require exit 1 and a problem report for each case.
- Keep `sexp.py` and the independent expectations unchanged.

No broader parser or renderer change is necessary. Setup acceptance and the accepted N2–N3 repairs remain unchanged. Final checker acceptance waits for this focused correction and its frozen hashes.
