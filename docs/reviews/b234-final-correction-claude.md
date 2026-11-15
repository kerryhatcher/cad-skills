# B234 final correction record (Claude)

Date: 2026-11-14.

Scope: the one remaining R1 defect of `b234-correction-review-codex.md` (two names for one file). Pi agrees with this scope in the addendum of `b234-correction-review-pi.md` (measured hash `b4ac419097566de200fd07e26e583a2c2e619cf7b217c1a2d547810f62daa945`). I made no commit, no push, no B5 implementation, and no supplier contact.

The earlier records and manifests stay as evidence: `b234-implementation-claude.md` with `b234-files.sha256`, and `b234-correction-claude.md` with `b234-correction-files.sha256`. This record and `b234-final-files.sha256` replace them for the final re-review.

State: ready for both reviews. I stop implementation edits here.

**1. The defect**

The cache of the first correction used the key (root, relative path). Two relative paths that resolve to one file through an in-project symbolic link got two reads and two snapshots. A controlled change between the reads could give a false qualification. Codex reproduced it with `components/part.yaml` as a link to `mechanical/board-interface.json`.

**2. The change**

One file changed in the code: `contracts/validate.py`.

| Item | Change |
|---|---|
| `_resolve_confined(root, rel)` | New. It tests one requested path against its own root and returns `ok` with the resolved path, `missing`, or `escape`. It reads no file. |
| `_read_confined(root, rel)` | It calls `_resolve_confined` and then reads the file. Its result is the same as before. |
| `_Ctx.read(root, rel)` | Each requested path first passes its own confinement test against its own root. Only then does the run look up a snapshot. The snapshot key is the resolved file path. A missing file and a path that leaves its root return their status at once, as before, and the run caches neither. The run caches a successful read only. |

Effects: two names for one file use one snapshot. The same file seen from two roots uses one snapshot, but a root that does not contain the file still refuses it, because the confinement test runs for each requested path before the lookup. The ordinary one-path case reads each file one time. The tests replace `V._read_confined`, and the new code still calls it at call time.

**3. Regressions**

`tests/test_pcb_tools.py` has 59 test functions (57 before).

| Test | What it proves |
|---|---|
| `test_aliases_share_one_snapshot` | The scenario of the review. The `parts` input is a link to the interface file. The interface has no holes, both drill outputs are omitted, and interface-based exceptions cover them. The file on disk then gets a plated hole. The `parts` input and the evidence references of the assembly checks carry the new hash. The interface input and its evidence references keep the old hash. The first read of the resolved file returns the old bytes. The run must not exit 0, it must give `cross.input_hash_mismatch`, and the resolved file must be read exactly one time. |
| `test_cached_success_does_not_bypass_confinement` | A package output is a link to the project interface file. The link is inside the project and outside the package root. The project read cached the file, yet the package output must give `cross.path_escape`, with no `cross.output_hash_mismatch` and no `cross.output_missing`. An input that is a link to a file outside the project must give `cross.path_escape` and no hash finding. The ordinary one-path package still passes, and each resolved file is read one time. |

Before the code change, `test_aliases_share_one_snapshot` failed with exit 0 and no finding (the false qualification). `test_cached_success_does_not_bypass_confinement` already passed with the old key and keeps protecting the new key. After the change, both pass, and the 57 earlier tests pass without change.

**4. Environment and versions**

| Item | Value |
|---|---|
| `uv` | 0.12.5 |
| Python selected by `uv` | 3.13.15 |
| `jsonschema` | 4.26.0 |
| `PyYAML` | 6.0.3 |

**5. Commands and results**

| Command | Exit code | Result |
|---|---:|---|
| `uv run tests/test_pcb_tools.py` | 0 | 59/59 passed |

I ran the contract suite only, as the lead said. I did not repeat the snippet suites, the project_io and skill-package suites, or the mechanical tests. This change touches no file that those suites test. The log file is in the session scratchpad. A reboot can clear it.

**6. STE**

I did not lint this record or the new test text. The new docstrings in `validate.py` use active voice and short sentences. The old flags in the strings of `validate.py` stay.

**7. Limits**

- The controlled change uses a replacement read function. It does not use a live change of a file during validation.
- The cache is per run.
- The snapshot key is the resolved path at the time of the first read. A file that another process replaces by a different link during the run is outside the claim.
- The tests run on one host and one Python version. No test uses KiCad.

**8. Hash manifest**

`docs/reviews/b234-final-files.sha256` lists the same 36 paths as `b234-correction-files.sha256`. Verify it with:

```bash
cd /mnt/storage/projects/cad-skills && sha256sum -c docs/reviews/b234-final-files.sha256
```

The check printed no failure when I made the manifest. Two files have a new hash compared with `b234-correction-files.sha256`:

```text
9bd30eada02d518f415428dbd9ae730c5cb920b846ef61622f4b8099e96463f2  contracts/validate.py
bf57320178ed2af8fcad01670e6ff0b2ab54af656608d989c3176bfd4b84d4a5  tests/test_pcb_tools.py
```

The other 34 files have the same hashes as in the correction manifest.

**9. For the reviewers**

1. `_Ctx.read`: whether any path can return a cached success for a name that fails its own confinement test.
2. `_resolve_confined` and `_read_confined`: whether the status values and the failure behavior are the same as before.
3. The two regressions: whether the alias case models the review scenario.

I will not change an implementation file until both re-reviews arrive.
