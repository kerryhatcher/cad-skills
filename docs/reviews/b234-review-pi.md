# Frozen B234 review: Pi

Date: 2026-11-14.

**Decision: blocking corrections**

I do not accept the frozen B234 implementation. I agree with all six Codex defects R1 to R6. I add one defect that I reproduced: `check_skill` crashes on non-mapping frontmatter.

The six defects already prevent acceptance. The added defect is small and belongs to the same batch.

**Reviewed identity**

| Item | Value |
|---|---|
| Manifest | `docs/reviews/b234-files.sha256` |
| Manifest SHA-256 | `74471a6530dd20f0debb9a7b024371a64c004c4359c9d507a5ef4bad671263ed` |
| Proposal revision 3 SHA-256 | `d8e48243d8be4bd4a3573da3aeee716f66c493266a571a67e21e719bd2b51f80` |

All 34 manifest entries passed before the probes and after the probes. The implementation did not change.

I ran focused probes only. I did not repeat the mechanical suites. The probes used temporary fixtures and the frozen functions through `uv`. They changed no implementation file.

**R1: repeated reads can qualify inconsistent evidence — agree**

I reproduced a false qualification.

Probe: build a qualified package with no holes. Remove the drill outputs and add interface-based `no_plated_holes` and `no_nonplated_holes` items. Write new interface bytes with one plated hole. Set the manifest interface input hash and the `fab.drill_split` evidence input hash to the new bytes. Make the first read of the interface return the old bytes and later reads return the new bytes.

Result: exit 0, no findings, two interface reads, and the file on disk had a plated hole. The old hole list satisfied the drill exception, and the new bytes satisfied the input hash.

Limit: the probe patched `_read_confined` to model the controlled change. It did not run a live concurrent file change. The code path is the same as the Codex instrumentation.

Correction: cache the bytes and hash of each resolved file for one validation run. Reuse them for record parsing, manifest comparisons, and evidence comparisons.

**R2: non-pass evidence skips listed-item validation — agree**

Probe: make the first check and its evidence `pending` in a draft package. Set a listed evidence input hash to 64 zeros. Set the artifact path to `absent-report.txt`. Update the evidence-file hash and size in the manifest.

Result: exit 0, no findings, and no artifact file.

Correction: compare each listed input and artifact for all statuses. Apply mandatory-role completeness only to passed evidence. Add cases for `pending`, `unconfirmed`, `fail`, and a record that rightly omits those items.

**R3: a qualified SKiDL package can omit its circuit source — agree**

Probe: build a project, set `board.yaml` `circuit_source` to `skidl`, and build a qualified package. The package had no `circuit_source` input.

Result: exit 0, no findings.

Correction: for a qualified SKiDL package, require the source input and compare its path and hash with the file bytes. Keep native KiCad acceptance and draft behavior.

**R4: publication accepts an existing dangling destination link — agree**

Probe: create a staging directory with one file. Make the destination a symbolic link to an absent directory under the project. Call `publish_dir`.

Result: the call succeeded and created the referent directory and file. The destination stayed a link.

Correction: refuse an existing lexical destination, including a dangling symbolic link, before the rename. Keep confinement of the resolved paths. Test that the refusal leaves the stage and the link unchanged.

**R5: a failed snippet worker can report a pass — agree**

Probe: run a worker that prints `{"status":"ok","stdout":"","stderr":""}` and then exits with code 7. Call `run_in_worker`.

Result: the function returned `(None, None)`. The suite would treat the block as successful.

Correction: require a successful process exit as well as an acceptable worker response. Add the nonzero-exit case and a signal-termination case. Keep the timeout and malformed-output tests.

**R6: the legacy baseline hides new missing references — agree**

Probe: copy the `cadquery` skill to a temporary directory. Add `references/new-missing.md` to `recipes.md`.

Result: `check_skill` reported two findings in `recipes.md` with the code `skill.reference_missing`. The baseline key is the file and the code, so the two findings collapsed to one key and the test passed.

Correction: use the root choice. Remove the repository-test path from the `recipes` prose. Use `../scripts/inspect_model.py` in `troubleshooting`. Remove the legacy baseline. Require no findings for the existing skills. Add a regression that rejects a new missing reference in a previously affected file.

**A1: `check_skill` crashes on non-mapping frontmatter — new defect**

Location: `tests/test_skill_packages.py`, `check_skill`.

`check_skill` reads the frontmatter with `yaml.safe_load` and then calls `meta.get`. A valid YAML document can be a list, a string, or an integer. The `or {}` fallback does not apply to a non-empty non-mapping value.

Probe: create a temporary skill with `SKILL.md` frontmatter `---\n- name: demo\n  description: x\n---\n`. Call `check_skill`.

Result: `AttributeError: 'list' object has no attribute 'get'`. A scalar and an integer frontmatter also crash.

This is a concrete packaging defect. A malformed skill file must produce a finding, not stop the checker.

Correction: require the frontmatter root to be a mapping. If it is not, add one finding such as `skill.frontmatter_invalid` and continue with empty metadata. Add tests for a list, a scalar, and an integer.

**Correction scope for Claude**

R1 to R6 plus A1. No later-batch feature is necessary. Update the affected files and supply focused regression results with replacement hashes.

**Limits**

- R1 uses a controlled read function, not a live concurrent change.
- A1 covers the three non-mapping forms that I tested. Other YAML shapes may need the same guard.
- No test uses KiCad. The fixtures show record consistency only.
- I did not rerun the full test suites. The Codex report records those results.

**Final hash comparison**

All 34 entries passed again after the probes. The manifest and proposal hashes are the values above. The reviewed implementation stayed frozen.

This report requests no commit and changes no implementation file.
