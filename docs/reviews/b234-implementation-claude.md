# B234 implementation record (Claude)

Date: 2026-11-14.

Scope: the combined batch B234, as in `b2-b4-proposal-claude.md` revision 3 (final design agreement of Codex and Pi). Claude wrote all implementation files. I made no commit, no push, no image action, and no supplier contact. I did not edit the root plan, the status file, or any reviewer report. The lead edited `AGENTS.md` (the Herdr message section) and the glossary (`Herdr`, `UTC`). I kept those edits, did not duplicate them, and added only the test commands to `AGENTS.md`.

State: ready for both reviews. I stop implementation edits here.

**1. What B234 contains**

| Part | Files |
|---|---|
| A. Records | `contracts/validate.py` (new flags, rules, cross-file checks), `contracts/schemas/{waivers,manifest,evidence,board-interface,toolchain-lock,export-settings}.schema.json`, `contracts/schemas/registry.json`, `contracts/README.md` |
| B. Safety | `contracts/project_io.py` |
| C. Packaging | `tests/test_skill_packages.py`, `tests/test_snippets.py` (routing, `--list-envs`, `--dry-run`), `tests/snippet_envs.json`, reasons on five `# notest` lines in existing skill references, `.github/workflows/test.yml`, `.gitignore` |
| Tests | `tests/test_pcb_tools.py` (53 test functions), `tests/test_project_io.py` (10), `tests/test_skill_packages.py` (6), `tests/pcb_support.py` (helpers that build a project and a package in a temporary directory) |
| Documents | `AGENTS.md` and `README.md` (test commands), `ste-glossary.yaml` (21 appended terms) |

The B1 fixtures, the four B1 schemas, and the B1 behavior did not change. The 35 B1 tests are part of the 53 tests of `test_pcb_tools.py` and pass without change. The fixed hash digests did not change.

**2. Environment and versions**

| Item | Value |
|---|---|
| `uv` | 0.12.5 |
| Python selected by `uv` | 3.13.15 |
| `jsonschema` | 4.26.0 |
| `PyYAML` | 6.0.3 |
| `referencing` | 0.37.0 |
| `rpds-py` | 2026.9.1 |

The scripts pin `jsonschema==4.26.0` and `pyyaml==6.0.3` in their PEP 723 headers. `project_io.py` has no dependency.

**3. Commands and results**

I ran each command with its output in a log file and read the exit code of `uv run` itself. No pipe hid an exit code.

| Command | Exit code | Result |
|---|---:|---|
| `uv run tests/test_pcb_tools.py` | 0 | 53/53 passed |
| `uv run tests/test_project_io.py` | 0 | 10/10 passed |
| `uv run tests/test_skill_packages.py` | 0 | 6/6 passed |
| `uv run tests/test_snippets.py --dry-run` | 0 | 52 blocks listed, 5 skipped with reasons |
| `uv run tests/test_snippets.py` | 0 | 52/52 blocks passed, 5 skipped |
| `uv run tests/test_print_tools.py` | 0 | 6/6 passed |

The logs are in the session scratchpad and a reboot can clear them. The GitHub workflow did not run. The workflow tests read the file only.

The tests cover these items of the agreed interface:

- **Records:** all six new schemas, the rules of each record, and the final-newline and control-character cases through the validator.
- **Board identity:** the five tests of the proposal section 4. A PCB change gives five `cross.board_pcb_hash_mismatch` findings and no board-record or schematic code. A `board.yaml` change that does not touch geometry gives one `cross.board_record_hash_mismatch`. A width change gives that finding and `cross.dimension_mismatch`. A schematic change gives `cross.schematic_hash_mismatch` and one `cross.waiver_schematic_hash_mismatch` (the `erc` waiver only). A substituted file in the `board` role gives `cross.input_path_mismatch`.
- **Qualification:** outline layer (correct, absent, wrong, duplicate, exchanged suffix), missing inner layer, one copper file for two layers, zero-byte and wrong-hash outputs in every state, missing drill with and without an applicability item, a condition that does not pair with the role, an interface that contradicts the item, a check exception with a passed and a pending `fab.drill_split`, incomplete draft against the identical qualified contents, PCBA with SMD parts and no paste.
- **Evidence:** all-pass checks with no evidence, changed evidence bytes, a stale input hash, a manual record with a reviewer and a date only, an unrelated input with a correct hash, parity with one of two inputs, a missing assembly role, an artifact outside the outputs, a profile evidence mismatch, an unsupported evidence schema version, a tool record without a reviewer (accepted).
- **Safety:** two real processes compete, a read-only run while the lock is held, an interrupted owner (`SIGKILL`), a wrong token, a malformed lock, release on failure, failure before and after `os.replace`, a symbolic link target, confinement (including a new leaf under an outside link), publication confinement, failure before and after `os.rename`, the publish order with the lock held across validation and publication.
- **Packaging:** name, description and length checks, the reference scanner (links, spans, fences, fragments, external URLs, anchors, `../` inside and outside the skill), the copy set (missing, extra, changed), the copy-run test with a canary directory, and the routing table (unrouted, missing environment, bare `# notest`, a failing block, timeout, invalid worker output, unavailable environment, changed skill source, an unrelated edit).
- **CI and ignore rules:** permissions, job names, command strings, SHA pins, timeouts, cache globs, no `continue-on-error`, no container job, and the ignore rules for lock and KiCad state files.

**4. Differences from the agreed text and decisions I made**

I list these so the reviewers can examine them.

1. **Reference scanner.** A backticked token with a known file extension counts as a reference only if it also contains `/` or starts with `./` or `../`. The agreed text did not include the `/` condition. Without it, the examples `part.py` and `bracket.py` in the existing skills are false findings.
2. **Known findings in the existing skills.** The scanner finds two defects: `references/recipes.md` names `tests/test_snippets.py` (a repository file), and `references/troubleshooting.md` names `scripts/inspect_model.py` (from `references/` the path is `../scripts/inspect_model.py`). I did not edit the skills. `test_existing_skills` holds both in a `KNOWN_FINDINGS` baseline with the reason. A new finding fails the test, and a stale entry fails the test. The lead decides on the correction.
3. **Schema reach.** To reach the named codes, the schema allows some values that the code then rejects. `size_bytes` has a minimum of 0 (`pkg.output_empty`). A drill applicability `reason` and `evidence` are optional in the schema (`pkg.applicability_reason_missing`). Paths in a manifest and in evidence only need a visible character in the schema, and the code applies `pkg.path_invalid` (absolute, `.`, `..`, empty segment, backslash, control character).
4. **Added code `cross.record_kind_mismatch`.** A file at a fixed project name must have the matching schema ID.
5. **Evidence inputs.** An evidence input whose path is a manifest input counts toward the role coverage even if its hash differs. The hash difference gives `pkg.check_evidence_mismatch`. Without this, one stale hash gave two findings.
6. **Manifest rule failures stop the package rules.** If the manifest itself fails (for example a qualified manifest with a failed required check), the package-level rules do not run. A draft reaches them.
7. **Library and model duplicates** are tested inside each list, not across the two lists.
8. **Snippet codes.** I added `snippet.block_failed`, `snippet.timeout`, `snippet.worker_output` and `snippet.source_changed`. The source check hashes the files of one skill before and after the blocks of that skill.
9. **`project_io.py try`** leaves the lock after it exits. The caller releases it with `release --token`. `hold` defaults to 60 seconds.
10. **Old file name `variants.duplicate_reference`** does not exist, as in B1.

**5. STE lint**

| Target | Result |
|---|---|
| `contracts/README.md` | 3 findings, all synonym flags for technical terms (`retrieved`/`get`, `check`/`validate`, `correct`/`fix`). I examined each and kept them. |
| Strings of `validate.py`, `project_io.py`, `test_snippets.py`, `test_skill_packages.py`, `test_project_io.py`, `pcb_support.py` (extracted with an `ast` script) | After my corrections, I fixed the passive sentences in messages. Remaining flags: the word `check` against `validate` (technical terms), and the usage lines of the command-line help (`uv run ...` text, which is code). |
| `b2-b4-proposal-claude.md` | 8 findings: long sentences in table cells and technical-term flags |
| This record | Not linted before the freeze. |

This check is not an ASD certification.

**6. Process notes**

- All Python ran through `uv run`, with one exception. A heredoc line `python3 - <<'E' ... E` with an empty body ran by mistake in one shell command. It read no file and wrote nothing. The schemas, the splice of `validate.py`, and every text edit used `uv run` scripts or the edit tool.
- Two scratch scripts generated the six new schema files (`gen_b234_schemas.py`, which imports the role lists from `validate.py`) and spliced the new rules into `validate.py`. They are in the session scratchpad and are not part of the batch. The schema files are the committed result. The test `test_registry_and_role_lists` checks that the role enums equal the constants in `validate.py`.

**7. Limits and untested items**

- The GitHub workflow did not run. The first CI run will measure the job times. The timeouts (15 and 30 minutes) are upper limits.
- No test uses KiCad. The PCB, the schematic, and the reports in the tests are small text files. They show record consistency. They do not show that a tool ran or that a board works.
- The geometry checks use plain point lists. Touching boundary points of a hole count as inside or outside by the ray rule. A spike (a segment that folds back on itself) does not count as a crossing.
- `file.too_complex`, the deep-YAML `RecursionError`, and the CLI outcome of `tool.validator_failure` have no new test. These are B1 limits that stay.
- The copy-run test is not a sandbox. It shows that a fixture needs no repository path. The final gate (B12) runs real isolated tasks.
- A file reference in a skill is checked relative to the Markdown file that holds it. A skill that writes paths relative to its root from a nested reference file gets a finding. That is how I found the second known finding.
- The lock protects cooperating processes on one local file system. A power loss, a network file system, a hostile process, and a rollback of several files are outside the claim.
- `--dry-run` still makes `uv` install CadQuery because the header of `test_snippets.py` names it.
- The tests run on one host and one Python version.

**8. Hash manifest**

`docs/reviews/b234-files.sha256` lists 34 files: all files that B234 changed or added, the four unchanged B1 fixtures, and the final proposal. It includes the current `AGENTS.md` and `ste-glossary.yaml` bytes with the lead's edits. The earlier B1 manifests stay as historical evidence. Verify it with:

```bash
cd /mnt/storage/projects/cad-skills && sha256sum -c docs/reviews/b234-files.sha256
```

The check printed no failure when I made the manifest. Compared with `b1-final-files.sha256`, these files have a new hash: `AGENTS.md`, `README.md`, `ste-glossary.yaml`, `.github/workflows/test.yml`, `contracts/README.md`, `contracts/validate.py`, `contracts/schemas/registry.json`, and `tests/test_pcb_tools.py`. The four B1 schemas and the four B1 fixtures have the same hashes as in the B1 final manifest.

The SHA-256 of the final proposal `docs/reviews/b2-b4-proposal-claude.md` is `d8e48243d8be4bd4a3573da3aeee716f66c493266a571a67e21e719bd2b51f80`.

**9. For the reviewers**

Examine these points first:

1. `_package_rules` and `_evidence_rules` in `contracts/validate.py`: a package that the rules accept but the agreed interface rejects (qualification, evidence inputs, the drill exceptions).
2. `confine`, `atomic_write` and `publish_dir` in `contracts/project_io.py`: the replacement and rename boundaries, and the confinement of both paths.
3. The differences in section 4, especially items 1, 3 and 6.
4. The two known findings in the existing skills (section 4, item 2). They are a result for the lead, not a change of the skills.
5. The new `.gitignore` rules, and whether the rule `*.lck` is too broad.

After the freeze I prepare only the compact B5 trial execution proposal. I will not change an implementation file until both reviews arrive.
