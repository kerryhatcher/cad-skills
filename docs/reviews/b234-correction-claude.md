# B234 correction record (Claude)

Date: 2026-11-14.

Scope: the seven repairs that the lead accepted after `b234-review-codex.md` (R1 to R6) and `b234-review-pi.md` (R1 to R6 and A1). Claude wrote all changes. I made no commit, no push, no B5 implementation, and no supplier contact. I did not edit the root plan, the status file, or any reviewer report.

The first record `b234-implementation-claude.md` and the first manifest `b234-files.sha256` stay unchanged as evidence. This record and `b234-correction-files.sha256` replace them for the re-review.

State: ready for both reviews. I stop implementation edits here.

**1. Repairs**

| ID | Defect | Repair | Location |
|---|---|---|---|
| R1 | A file was read more than once in a run, so a changed file could give a false qualification | `_Ctx.read` reads each file one time in a run and caches the bytes. The parse, the hash comparisons, the evidence comparisons, and the drill exception all use the same bytes. Every `_read_confined` call in the project and package rules now goes through the cache. | `contracts/validate.py` |
| R2 | Evidence with a status other than `pass` skipped the listed input and artifact comparison | The comparison of each listed evidence input and of the artifact now runs for every status. The mandatory input roles and the profile-evidence comparison stay for `pass` only. An incomplete `pending`, `unconfirmed` or `fail` record that omits inputs and artifact is still accepted. | `contracts/validate.py` (`_evidence_rules`) |
| R3 | A qualified SKiDL package could omit its circuit source | If `board.yaml` has `circuit_source: skidl` and the manifest status is `qualified`, the manifest needs a `circuit_source` input (`pkg.input_missing`). The generic input loop compares its path and hash with the file bytes. Native KiCad packages and incomplete drafts keep their behavior. This is provenance validation. It does not run SKiDL. | `contracts/validate.py` (`_package_rules`) |
| R4 | `publish_dir` accepted an existing dangling destination link | `publish_dir` tests the lexical destination with `lexists` before it resolves any path. It refuses any existing entry, including a dangling link, with `FileExistsError`. Confinement of the resolved paths stays. | `contracts/project_io.py` |
| R5 | A snippet worker that printed an acceptable response and then failed counted as a pass | `run_in_worker` examines the process exit code first. A nonzero exit gives `snippet.worker_failed` with the exit code. A signal gives the same code with the signal number. Timeout and malformed-output handling stay. | `tests/test_snippets.py` |
| R6 | The legacy baseline hid new missing references in already listed files | The two legacy texts are repaired: `recipes.md` no longer names `tests/test_snippets.py`, and `troubleshooting.md` names `../scripts/inspect_model.py`. The `KNOWN_FINDINGS` baseline is removed. `test_existing_skills` requires no finding in any existing skill. | `skills/cadquery/references/recipes.md`, `troubleshooting.md`, `tests/test_skill_packages.py` |
| A1 | `check_skill` crashed on a frontmatter that is not a mapping | The frontmatter root must be a mapping. Otherwise `check_skill` gives one finding `skill.frontmatter_invalid` and skips the name and description checks for that skill. A YAML syntax error in the frontmatter gives the same finding. An empty frontmatter still gives `skill.name_mismatch`. | `tests/test_skill_packages.py` |

The A1 repair was applied after the lead relayed Codex's agreement.

**2. New regressions**

`tests/test_pcb_tools.py` has 57 test functions (53 before). `tests/test_project_io.py` has 11 (10 before). `tests/test_skill_packages.py` has 8 (6 before).

| Test | Cases |
|---|---|
| `test_each_file_is_read_once` | A valid qualified package run. A counting replacement of `_read_confined` shows that no file is read more than once. The PCB and the evidence files are in the count. |
| `test_changed_file_cannot_qualify` | The controlled change of the review. The interface has no holes, both drill outputs are omitted, and interface-based exceptions cover them. The file on disk then gets a plated hole, and the manifest and the drill evidence carry the new hash. The first read returns the old bytes and later reads would return the new bytes. The run must not exit 0, it must give `cross.input_hash_mismatch`, and the interface must be read one time. The same package with a normal read gives `cross.drill_applicability_false`. |
| `test_non_pass_evidence_is_examined` | For `pending`, `unconfirmed` and `fail` in a draft: a complete record passes. A record that omits inputs and artifact passes. A wrong input hash and an absent artifact path give two findings. A wrong input hash alone gives one. A wrong artifact hash alone gives one. An input that is not a manifest input gives `pkg.check_input_role_missing`. |
| `test_skidl_provenance` | A SKiDL package with its source passes. Without the input, a qualified package gives `pkg.input_missing`, and the draft passes. A wrong hash, an absent file, and changed bytes give `cross.input_hash_mismatch`. A native package passes. |
| `test_publish_refuses_existing_lexical_destination` | A dangling link to an absent project path: `FileExistsError`, the stage unchanged, the link unchanged, no referent made. A dangling link to an outside path and an existing directory are refused. |
| snippet routing (in `test_snippet_routing`) | A worker that prints an acceptable response and exits with code 7, and a worker that is killed with signal 9 after the response. Both give `snippet.worker_failed` and the messages name the code and the signal. The timeout, the malformed output and the block failure cases stay. |
| `test_existing_skills`, `test_new_missing_reference_in_a_legacy_file` | The existing skills have no finding. A copy of the cadquery skill gets a new missing reference in `recipes.md`: one finding. A second missing reference in `troubleshooting.md` adds a second finding. |
| `test_frontmatter_shapes` | A list, a scalar, an integer, a string list, and invalid YAML each give exactly `skill.frontmatter_invalid`. An empty frontmatter gives `skill.name_mismatch`. |

`tests/pcb_support.py` has a new parameter `circuit_source` for `build_project`, and `build_package` lists a SKiDL source input when the project has `src/circuit.py`.

**3. Environment and versions**

| Item | Value |
|---|---|
| `uv` | 0.12.5 |
| Python selected by `uv` | 3.13.15 |
| `jsonschema` | 4.26.0 |
| `PyYAML` | 6.0.3 |
| `referencing` | 0.37.0 |
| `rpds-py` | 2026.9.1 |

**4. Commands and results**

I ran each command with its output in a log file and read the exit code of `uv run` itself.

| Command | Exit code | Result |
|---|---:|---|
| `uv run tests/test_pcb_tools.py` | 0 | 57/57 passed |
| `uv run tests/test_project_io.py` | 0 | 11/11 passed |
| `uv run tests/test_skill_packages.py` | 0 | 8/8 passed |
| `uv run tests/test_snippets.py --dry-run` | 0 | 52 blocks listed, 5 skipped with reasons |
| `uv run tests/test_snippets.py` | 0 | 52/52 passed, 5 skipped |
| `uv run tests/test_print_tools.py` | not run | Unchanged by this repair, as the lead said |

The logs are in the session scratchpad. A reboot can clear them.

**5. STE lint**

I extracted the strings of the changed files (messages, help text, docstrings, comments) and linted them. The new repair messages have no finding after I changed three passive sentences ("was stopped by signal", "is refused"). The remaining flags are old: one `check`/`validate` term flag, and long sentences in the usage lines of the command-line help (they are code). I did not lint this record. The wording of the two skill texts is a small change of a sentence and a path.

**6. Limits**

- R1 is tested with a controlled read function, not with a live concurrent change of a file. The code path is the same. A file that changes between the cached read and a later program step outside the validator is outside the claim.
- The cache is per run. A second run reads the files again.
- A1 covers the YAML shapes tested here (list, scalar, integer, string list, invalid YAML). Another shape that `yaml.safe_load` returns is not a mapping and gets the same finding.
- The tests run on one host and one Python version. The GitHub workflow did not run. No test uses KiCad.
- The two repaired skill texts are a minimal edit. A broader rewrite of the cadquery skill is not part of this repair.

**7. Hash manifest**

`docs/reviews/b234-correction-files.sha256` lists 36 files: the 34 files of the first manifest and the two repaired skill texts. Verify it with:

```bash
cd /mnt/storage/projects/cad-skills && sha256sum -c docs/reviews/b234-correction-files.sha256
```

The check printed no failure when I made the manifest. Files with a new hash compared with `b234-files.sha256`:

```text
f4f2fb06ddb14805da9ea80d06bb4ab8e30c17102529746a7015bf15ed6de9e3  contracts/project_io.py
b9bc2e8dc1c3f590d11c803a4de0c6d55f36b87e24398c6676d41732122d9e50  contracts/validate.py
f83581eaa03c8c9ba78ae951140369703b65158bb0168c338cacf1d8f137cf52  tests/pcb_support.py
ca4755133c9eb189f7045f0d867ff9e3fe6f0b153a2cf3af2a36c9c96b57087c  tests/test_pcb_tools.py
26ad2ce27f3cd406569544147bca71908d8e0efa61047527eae9fb7962dd7381  tests/test_project_io.py
4c57eb5486e7bef3e5239193e24b4c0cfa487ba26780ea69efae728d520c50d5  tests/test_skill_packages.py
78edac2af3f0560a1ba0c8f009fde3caaa32324339065178b3952e6beeecb460  tests/test_snippets.py
```

The two repaired skill texts are new entries in the manifest: `skills/cadquery/references/recipes.md` and `skills/cadquery/references/troubleshooting.md`. The schemas, the fixtures, `AGENTS.md`, `README.md`, the glossary, the workflow file and the final B234 proposal have the same hashes as in the first manifest.

**8. For the reviewers**

1. `_Ctx.read` and the replaced call sites in `_load_project`, `_package_rules` and `_evidence_rules`. Look for a path that still calls `_read_confined` directly.
2. The restructured `_evidence_rules`: whether a non-pass record can still skip a listed item.
3. The `circuit_source` rule in `_package_rules`: whether it covers the cases that you named.
4. `publish_dir`: the order of the lexical test and the confinement.
5. `run_in_worker`: whether any path still lets response text override a process failure.

I will not change an implementation file until both re-reviews arrive.
