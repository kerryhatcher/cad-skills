# Frozen B234 correction review: Pi

Date: 2026-11-14.

**Decision: accepted**

I accept the frozen B234 correction. The seven repairs R1 to R6 and A1 are correct. I found no remaining defect in the correction scope.

The repair keeps the accepted design. It changes only the seven named defects.

**Reviewed identity**

| Item | Value |
|---|---|
| Manifest | `docs/reviews/b234-correction-files.sha256` |
| Manifest SHA-256 | `846f5496b67938311d5c200b7bc4f70086c3d260eab209ccce918015e97e0bfb` |
| Proposal revision 3 SHA-256 | `d8e48243d8be4bd4a3573da3aeee716f66c493266a571a67e21e719bd2b51f80` |

All 36 manifest entries passed before the probes and after the probes. The implementation did not change.

I ran focused independent probes only. I did not repeat the mechanical suites. The reported suite results are: contracts 57/57, project_io 11/11, skill_packages 8/8, snippets 52/52, and dry-run exit 0.

**R1: repeated reads — repaired**

`_Ctx.read` reads each file one time and caches the bytes. The parse, the hash comparisons, the evidence comparisons and the drill exception use the cached bytes.

Probe results:

| Probe | Result |
|---|---|
| Valid package, counting `_read_confined` | Max one read per file across 50 reads. The PCB and the evidence files are in the count. |
| Controlled interface change | Exit 1, finding `cross.input_hash_mismatch`. One interface read. |
| Same package with a normal read | Exit 1, finding `cross.drill_applicability_false`. The file on disk has a plated hole. |

No direct `_read_confined` call remains in the project or package rules. Only `_Ctx.read` calls it.

**R2: non-pass evidence — repaired**

The listed input and artifact comparison runs for every status. The mandatory roles and the profile comparison stay for `pass` only.

Probe results:

| Probe | Result |
|---|---|
| Complete `pending` record | Exit 0. |
| `pending` record with no inputs and no artifact | Exit 0. |
| Wrong input hash and absent artifact | Exit 1, two `pkg.check_evidence_mismatch` findings. |
| Wrong artifact hash alone | Exit 1, one `pkg.check_evidence_mismatch` finding. |
| Input that is not a manifest input | `pkg.check_input_role_missing`. |

**R3: SKiDL provenance — repaired**

A qualified SKiDL package needs a `circuit_source` input. The generic input loop compares its path and hash with the file bytes.

Probe results:

| Probe | Result |
|---|---|
| SKiDL package with `src/circuit.py` | Exit 0. |
| Qualified package without the source | Exit 1, `pkg.input_missing`. |
| Draft package without the source | Exit 0. |
| Wrong source hash | Exit 1, `cross.input_hash_mismatch`. |
| Native KiCad package | Exit 0. |

**R4: dangling destination link — repaired**

`publish_dir` tests the lexical destination with `lexists` before it resolves any path.

Probe results:

| Probe | Result |
|---|---|
| Dangling link to an absent project path | `FileExistsError`. The stage and the link stay. No referent directory. |
| Dangling link to an outside path | `FileExistsError`. No outside path. |
| Existing directory destination | `FileExistsError`. |

**R5: snippet worker exit — repaired**

`run_in_worker` examines the process exit code before it accepts the response.

Probe results:

| Probe | Result |
|---|---|
| Worker prints acceptable JSON and exits 7 | `snippet.worker_failed`, message names code 7. |
| Worker prints acceptable JSON and receives signal 9 | `snippet.worker_failed`, message names signal 9. |

Timeout and malformed-output handling stay.

**R6: legacy reference baseline — repaired**

The two legacy texts are repaired. `recipes.md` no longer names `tests/test_snippets.py`. `troubleshooting.md` names `../scripts/inspect_model.py`. The `KNOWN_FINDINGS` baseline is removed.

Probe results:

| Probe | Result |
|---|---|
| All existing skills | No finding. |
| New missing reference in `recipes.md` | One `skill.reference_missing`. |
| A second missing reference in `troubleshooting.md` | Two findings. Both stay visible. |

**A1: non-mapping frontmatter — repaired**

`check_skill` requires a mapping root. A non-mapping root gives one `skill.frontmatter_invalid` and skips the name and description checks.

Probe results:

| Frontmatter | Result |
|---|---|
| List, scalar, integer, string list, invalid YAML | `skill.frontmatter_invalid`. |
| `null`, `~`, comment only | `skill.frontmatter_invalid`. |
| Empty frontmatter | `skill.name_mismatch` and `skill.description_empty`. |

No crash. The checker continues.

**Regressions from the edits**

- The cache replaced the direct reads in `_load_project`, `_package_rules` and `_evidence_rules`. No path reads a file twice.
- The restructured `_evidence_rules` keeps the pass-only completeness rules. A non-pass record that omits inputs and artifact still passes.
- `publish_dir` keeps the confinement of the resolved paths.
- `run_in_worker` keeps the timeout and malformed-output paths.
- `check_skill` keeps the name, description and length checks for a valid mapping.

I found no regression.

**Limits**

- R1 uses a controlled read function, not a live concurrent change. The code path is the same.
- The cache is per run. A second run reads the files again.
- I did not rerun the full test suites. The reported results are from the correction record.
- No test uses KiCad.
- The tests run on one host and one Python version.

**Final hash comparison**

All 36 entries passed again after the probes. The manifest and proposal hashes are the values above. The reviewed implementation stayed frozen.

**Addendum: R1 cache identity by resolved file**

Codex found one remaining R1 defect. I agree. The finding is correct.

`_Ctx.read` keys on `(resolved root, relative name)`. Two confined names that resolve to one file get two snapshots. The Codex reproduction uses `components/part.yaml` as a symbolic link to `mechanical/board-interface.json`. The drill exception reads the original hole list through one name, and the `parts` input hash reads changed bytes through the other name. The run qualified an inconsistent snapshot.

Agreed correction:

1. Resolve the candidate file path and run the root-confinement test for each read request. Do not consult a shared cache before this test.
2. If the status is `escape` or `missing`, return that status. Preserve the current outside-link rejection and missing behavior. Do not share these results by resolved file path.
3. If the status is `ok`, use the resolved absolute file path as the cache key. Read the bytes one time and store them under that key. Later confined names for the same file receive the same bytes.
4. Keep the one-read-per-resolved-file rule. Keep the per-run cache.
5. Add one regression with two confined names for one file and a controlled byte change. The run must not qualify inconsistent snapshots.
6. Keep the existing outside-link rejection test and the ordinary one-path cache test.

This completes the already agreed one-read-per-resolved-file rule. It does not change the design. It does not affect R2 to R6 or A1.

I did not run new probes for this addendum. The Codex reproduction and the `_Ctx.read` source are sufficient evidence.

This review changes only this report. It makes no implementation edit.
