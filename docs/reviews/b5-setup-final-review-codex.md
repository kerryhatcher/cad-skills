# Final B5 native-checker review: Codex

Date: 2026-11-14.

**Decision: accepted for this checkpoint**

I accept the final narrow native-checker correction. The remaining malformed-instance and non-scalar-field blockers are closed. Earlier setup and N1–N3 acceptance otherwise remain unchanged.

Manifest: `docs/reviews/b5-setup-final-files.sha256`.

Manifest SHA-256: `2e90992f2c2dc9ed164843f4e6a25690c10a444d356082fcb4b4ba2ed51888d7`.

All 16 entries passed before and after review. Only these hashes differ from the previous manifest:

```text
eb75945634f927f849de3faf356090ab94fcd2f73246e39202ea1f41a56e009e  examples/pcb-trial/scripts/check_native.py
38fb89065a9f2680ef3cc8137317cb0ca42657c3f3167dbe048c3265dec6152f  tests/test_trial_checker.py
```

**Focused results**

I read `b5-setup-final-correction-claude.md`, the changed guards, and the three CLI regressions.

Direct symbols with missing, nested, or blank `lib_id` now produce a problem. Non-scalar positions and properties produce clear problem reports. The schematic-input exception boundary also catches `TypeError`. These changes do not expand the parser or renderer scope.

`uv run tests/test_trial_checker.py` passed: 15/15, zero unavailable, exit 0. This includes the nominal fixture, prior N1–N3 regressions, and fresh KiCad exports.

I independently ran the CLI on temporary copies with an extra malformed symbol, a nested `at` value, and a non-scalar property name. Each returned exit 1, a JSON problem report, and no traceback.

The image tag resolved to the authorized existing image:

```text
d881df4ef3e2ec76995f4070596550db118b23e7f6db9017f09a418c44c4b1c2
```

Container tests used temporary mounts, `--pull=never`, and `--network none`. I did not rebuild or pull an image.

`sexp.py`, the independent expectations, and the native fixture retain their previous hashes. The nominal map has ten pin-to-net entries across four nets.

No unrelated suite ran. The final manifest hash remained unchanged after review. I changed only this report. Final B5 acceptance still depends on the remaining identity, GUI, clean-board, export, simulation, and draft-package results.
