# Final B234 correction review: Codex

Date: 2026-11-14.

**Decision: accepted**

I accept the final B234 cache correction. The remaining R1 blocker is closed. R2–R6 and A1 retain their earlier acceptance.

Manifest: `docs/reviews/b234-final-files.sha256`.

Manifest SHA-256: `0a907940cd056379138a45c81eced740e698129bf1cc619b51525b64d2404c0b`.

All 36 manifest entries passed before and after review. The manifest comparison shows changes only to these files:

```text
9bd30eada02d518f415428dbd9ae730c5cb920b846ef61622f4b8099e96463f2  contracts/validate.py
bf57320178ed2af8fcad01670e6ff0b2ab54af656608d989c3176bfd4b84d4a5  tests/test_pcb_tools.py
```

**Focused review**

I read `b234-final-correction-claude.md`, the cache code, the path-resolution helper, and the two new regressions.

Each request passes its own root-confinement test before cache lookup. Successful snapshots use the resolved file path as their key. Confined aliases share the same bytes. A request outside its own root cannot reuse an earlier success.

The helper preserves the `ok`, `missing`, and `escape` results. It reads no bytes during path resolution. The cache stores successful reads only.

The controlled alias-change regression now fails qualification with `cross.input_hash_mismatch` and reads the resolved interface once. The cross-root regression reports `cross.path_escape` without a false missing-file or hash finding.

**Measured tests**

`uv run tests/test_pcb_tools.py` passed: 59/59 test functions, exit 0. This includes the earlier correction tests and the original fixed-byte hash tests.

Independent checks confirmed these results:

- Two confined aliases retained the original snapshot after a byte change, with one underlying read.
- An outside-root alias returned `escape` despite the earlier cached success.
- A missing-file result did not prevent a later successful read after the file appeared.

No remaining blocker appeared in this correction scope. I did not repeat unrelated suites or mechanical tests. I did not reopen the accepted design.

The final manifest hash remained unchanged after the checks. I changed only this report and request no commit.
