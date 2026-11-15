# Frozen B234 review: Codex

Date: 2026-11-14.

**Decision: blocking corrections**

I do not accept this revision. Six concrete corrections remain below. No later-batch feature is necessary to correct them.

**Reviewed identity and tests**

Manifest: `docs/reviews/b234-files.sha256`.

Manifest SHA-256: `74471a6530dd20f0debb9a7b024371a64c004c4359c9d507a5ef4bad671263ed`.

Proposal revision 3 SHA-256: `d8e48243d8be4bd4a3573da3aeee716f66c493266a571a67e21e719bd2b51f80`.

I read the implementation record, including section 4 deviations, and the agreed proposal. All 34 manifest entries passed before review.

| Command | Measured result |
|---|---|
| `uv run tests/test_pcb_tools.py` | 53/53 passed, exit 0 |
| `uv run tests/test_project_io.py` | 10/10 passed, exit 0 |
| `uv run tests/test_skill_packages.py` | 6/6 passed, exit 0 |
| `uv run tests/test_snippets.py --dry-run` | 52 blocks listed, 5 skips with reasons, exit 0 |
| `uv run /tmp/cad-skills-b234-evidence-probe.py` | The invalid draft gave exit 0 and no findings |

I did not repeat mechanical suites. Independent probes used temporary fixtures and the frozen functions through `uv`. They changed no implementation file.

**R1: repeated reads can qualify inconsistent evidence**

Locations: `contracts/validate.py`, `_load_project`, `_package_rules`, and `_evidence_rules`.

The proposal says that each file has one read and that parsing and hashing use the same bytes. The implementation reads project inputs again for manifest comparisons. It also reads evidence once as an output and again as a record.

Independent instrumentation measured two reads of the PCB and two reads of an evidence file during a valid package run.

I reproduced a false qualified result with a controlled file change:

1. Build an interface with no holes and a qualified package.
2. Omit the plated drill output with an interface-based `no_plated_holes` exception.
3. Prepare new interface bytes that contain a plated hole.
4. Set the manifest and drill evidence input hashes to those new bytes.
5. Change the interface file immediately after its first read.

The validator used the old hole list for the exception and the new bytes for the input hash. It returned exit 0 with no findings. The file on disk contained a plated hole.

This probe models a file change during read-only validation. It does not depend on hostile symlink changes.

Cache the bytes and hash for each resolved file within one validation run. Reuse them for record parsing, manifest comparisons, and evidence comparisons. Add the controlled-change regression. Reject the mismatched snapshot without a false qualification. No additional lock protocol is necessary.

**R2: non-pass evidence skips listed-item validation**

Location: `contracts/validate.py:1043`.

`_evidence_rules` continues before input and artifact comparisons when the evidence status is not `pass`.

Reproduction: make the first check and its evidence `pending` in a draft package. Set a listed evidence input hash to 64 zeros. Set the artifact path to `absent-report.txt`. Update the evidence-file hashes and size in the manifest.

The root's probe returned `{"exit_code": 0, "findings": []}`. My separate probes also accepted a wrong artifact hash and a wrong input hash independently.

F3 permits incomplete drafts. It still validates the items that they list. Compare each listed input and artifact for all statuses. Apply mandatory-role completeness only to passed evidence. Add cases for `pending`, `unconfirmed`, and `fail`, plus an incomplete record that legitimately omits those items.

**R3: a qualified SKiDL package can omit its circuit source**

Locations: `contracts/validate.py`, `_rules_manifest` and `_package_rules`.

The proposal requires a `circuit_source` input for a SKiDL project. Neither function applies that condition.

Reproduction with `tests/pcb_support.py`: build a project, set `board.yaml` `circuit_source` to `skidl`, and build its package. The helper supplies no `circuit_source` input. Project and package validation returned exit 0 with no findings.

For a qualified SKiDL package, require the source input and compare its listed path and hash with the file bytes. Preserve native KiCad acceptance and incomplete-draft behavior. This is provenance validation, not SKiDL execution.

**R4: publication accepts an existing dangling destination link**

Location: `contracts/project_io.py`, `publish_dir`, before the destination existence test.

The function resolves the destination before it calls `lexists`. This loses an existing symbolic link when its referent does not exist.

Reproduction under one temporary project:

```text
stage/file contains data
dest is a symbolic link to the absent project/referent directory
publish_dir(project, "stage", "dest")
```

The call succeeded and made `referent/file`. The existing destination was not refused. No concurrent process was necessary.

Refuse an existing lexical destination, including a dangling symbolic link, before rename. Retain confinement of the resolved paths. Test that refusal leaves the stage and link unchanged and makes no referent directory.

The ordinary post-replacement and post-rename failure guarantees passed independent checks. I injected an error into the directory synchronization function. The functions raised their respective post-operation exceptions and retained the complete new bytes or package.

**R5: a failed snippet worker can report a pass**

Location: `tests/test_snippets.py:107`, `run_in_worker`.

The function reads the JSON status but does not examine the process exit code.

Reproduction: a worker prints `{"status":"ok","stdout":"","stderr":""}` and then exits with code 7. `run_in_worker` returned `(None, None)`. The suite therefore treats the block as successful.

Require a successful process exit as well as an acceptable worker response. Add the nonzero-exit case and a signal-termination case. Keep timeout and malformed-output tests. Do not let response text override process failure.

**R6: the legacy baseline hides new missing references**

Location: `tests/test_skill_packages.py:160`, `KNOWN_FINDINGS` and `test_existing_skills`.

The baseline identifies a finding only by Markdown file and finding code. The test converts findings to a set. A second missing reference in an already listed file disappears into the same baseline entry.

I reproduced this in a temporary skill with the two legacy references. I added `references/new-missing.md` to its `recipes.md`. The scanner reported the new defect, but `test_existing_skills` still passed.

I agree with the root's narrow repair choice:

- Remove the repository-test path from the recipes prose.
- Use `../scripts/inspect_model.py` in troubleshooting.
- Remove the legacy baseline and require no findings for the existing skills.

Add a regression that rejects a new missing reference in a previously affected file. No general legacy-exception mechanism is necessary.

**Other deviations and limits**

The bare-filename scanner restriction is a documented heuristic. A bare example filename can differ from a bundled-file reference. I do not block this batch on that restriction alone. Retain explicit relative paths for bundled files and the stated scan limits.

Schema reach for named findings is acceptable when semantic validation rejects the value. Counting a stale evidence input toward role coverage is also acceptable because its hash mismatch still fails validation. Early termination after an invalid manifest prevents qualification; it does not establish a pass.

The copy-run test explicitly states that it is not a sandbox. Library/model duplicate checks within each list do not add a cross-list ownership rule. The explicit `try` lock command retains its lock for token-based release. These choices do not add blockers.

The two legacy references need only the documentation repairs above. A broader CAD skill rewrite is outside this review. The existing CI permissions, SHA pins, timeouts, and deferred container job agree with the interface. I found no reason to expand this batch into B5.

**Final hash comparison**

All 34 entries passed again after the probes. The manifest and proposal hashes remained the values above. The reviewed implementation stayed frozen.

Correct R1–R6 and supply focused regression results with replacement hashes. I will re-review the affected files. This report requests no commit and changes no implementation file.

**Agreement on Pi A1**

I agree with the root's narrow A1 repair. `check_skill` must reject non-mapping frontmatter with `skill.frontmatter_invalid`, without an `AttributeError`.

Test list, string, and integer frontmatter values. Preserve ordinary name and description checks for mapping metadata. No schema framework is necessary.

This addition joins the agreed R1–R6 correction scope. Acceptance still awaits the corrected frozen files and regression results.
