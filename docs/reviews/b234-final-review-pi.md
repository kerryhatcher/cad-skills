# Frozen B234 final review: Pi

Date: 2026-11-14.

**Decision: accepted**

I accept the frozen B234 final correction. The resolved-path cache repair is correct. I found no remaining defect in the final R1 scope.

R2 to R6 and A1 stay accepted.

**Reviewed identity**

| Item | Value |
|---|---|
| Manifest | `docs/reviews/b234-final-files.sha256` |
| Manifest SHA-256 | `0a907940cd056379138a45c81eced740e698129bf1cc619b51525b64d2404c0b` |
| `contracts/validate.py` SHA-256 | `9bd30eada02d518f415428dbd9ae730c5cb920b846ef61622f4b8099e96463f2` |
| `tests/test_pcb_tools.py` SHA-256 | `bf57320178ed2af8fcad01670e6ff0b2ab54af656608d989c3176bfd4b84d4a5` |
| Proposal revision 3 SHA-256 | `d8e48243d8be4bd4a3573da3aeee716f66c493266a571a67e21e719bd2b51f80` |

All 36 manifest entries passed before the focused tests and after the focused tests. The implementation did not change.

Only `contracts/validate.py` and `tests/test_pcb_tools.py` differ from `b234-correction-files.sha256`. The other 34 files keep the correction hashes.

**1. Resolved-path success sharing after per-request confinement**

The source is correct.

- `_resolve_confined` tests one requested path against its own root. It returns `ok` with the resolved path, `missing`, or `escape`. It reads no file.
- `_Ctx.read` calls `_resolve_confined` first. A `missing` or `escape` result returns at once. The run does not share that result.
- For an `ok` result, `_Ctx.read` uses the resolved absolute file path as the cache key. It reads the bytes one time and stores them under that key.
- A later confined name for the same file receives the same bytes.
- `_read_confined` keeps the same status values. Its only change is the call to `_resolve_confined`.

The ordinary one-path case reads each file one time. The `test_each_file_is_read_once` test passes.

**2. Preserved failure behavior**

- A missing file returns `missing` from `_resolve_confined`. `_Ctx.read` returns `(missing, None)`. The run does not cache it.
- A path that leaves its root returns `escape`. `_Ctx.read` returns `(escape, None)`. The run does not cache it.
- A read error inside `_read_confined` returns `missing`. `_Ctx.read` returns that result and does not cache it.
- The outside-link rejection is unchanged. The `test_cached_success_does_not_bypass_confinement` test confirms it.

**3. Alias controlled-change case**

I ran the focused test `test_aliases_share_one_snapshot`. It passed.

The test makes `components/part.yaml` a symbolic link to `mechanical/board-interface.json`. The interface has no holes. The drill outputs are omitted and interface-based exceptions cover them. The file then gets a plated hole. The `parts` input and the assembly evidence carry the new hash. The interface input and its evidence keep the old hash. The first read of the resolved file returns the old bytes.

Result: the run does not exit 0. It gives `cross.input_hash_mismatch`. The resolved file is read exactly one time.

This is the direct check of the reported false qualification. The repair stops it.

**4. Cross-root cached-success refusal**

I ran the focused test `test_cached_success_does_not_bypass_confinement`. It passed.

Case A: a package output is a symbolic link to the project interface file. The link is inside the project and outside the package root. The project read already cached the file. The package output still gives `cross.path_escape`. It gives no `cross.output_hash_mismatch` and no `cross.output_missing`.

Case B: a project input is a symbolic link to a file outside the project. It gives `cross.path_escape` and no hash finding.

Case C: the ordinary one-path package passes, and each resolved file is read one time.

The cache does not bypass the confinement test of the current root.

**5. Regression checks**

I ran these focused test functions only. I did not repeat the full suite.

| Test | Result |
|---|---|
| `test_aliases_share_one_snapshot` | 1/1 passed. |
| `test_cached_success_does_not_bypass_confinement` | 1/1 passed. |
| `test_each_file_is_read_once` | 1/1 passed. |
| `test_changed_file_cannot_qualify` | 1/1 passed. |

The contract suite reports 59/59 passed. The correction record says the change touches no file that the other suites test. I did not repeat those suites.

**6. Limits**

- The controlled change uses a replacement read function. It does not use a live concurrent file change.
- The cache is per validation run.
- The snapshot key is the resolved path at the first read. A file replaced through a different link during the run is outside the claim.
- The tests run on one host and one Python version. No test uses KiCad.

**7. Hash comparison**

All 36 manifest entries passed again after the focused tests. The manifest hash, the two changed-file hashes, and the proposal hash are the values above. The reviewed implementation stayed frozen.

This review changes only this report. It makes no implementation edit.
