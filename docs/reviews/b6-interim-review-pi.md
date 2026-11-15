# B6 interim code review: Pi

Date: 2026-11-14.

**Decision: the snapshot is an incomplete implementation. The lead's known items 1 to 7 remain. I found four new concrete findings. This is not B6 acceptance.**

## 1. Reviewed bytes

| Item | Value |
|---|---|
| Snapshot manifest | `docs/reviews/b6-interim-files-root.sha256`, 65 entries, `a13f9295b2e630e076bf2727854ff7a1f8d8de6bafae3be1d2f4e76dd4cc8576` |
| Manifest check | 65 of 65 entries `OK`, before and after this review |
| Main script | `skills/pcb-design/scripts/pcb.py`, `c57de5b825ae03bb32f9132d3ebf2a1e088338f0216c3534286b9738c5f87621` |
| Workers | `board_inventory.py` `b990a150796f988e...fa8`, `gui_update.py` `7e953fead679f3e...18c` |
| Design | `b6-consolidated-proposal-claude-r3.md`, `a46998a5a3f1b72c...c48f` |
| Image | `localhost/cad-skills-pcb:b6`, `b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f` |

I read the 19-pass log but did not rerun it. I ran one focused regression in a temporary copy with the existing image. No pull, no broad suite, no B5 repetition, no implementation edit.

## 2. Focus-area findings

### 2.1 Export geometry and layer checks

The seven checks are present: plot settings, file set, active `%T` attributes, one `G04 #@! TF.FileFunction` comment, Excellon header and hole multiset with the measured Y negation, and placement rows with duplicate rejection. `test_clean_template_passes_all_checks`, `test_export_refuses_unsupported_contract` and `test_export_destination_exists_is_exit_2` cover the happy path and two refusals.

**F1: the layer mapping is two-layer only. `export_subset` refuses `len(copper) != 2` and emits only `Copper,L1,Top` and `Copper,L2,Bot`. It cannot emit `Copper,Ln,Inr`. The r3 section 10 check 4 promised `Copper,Ln,Top|Inr|Bot`. `references/trial-limits.md` documents the two-layer limit. This is a conflict between the accepted r3 interface and the live implementation. The B7/B8 plan needs four and six layers. Resolve the conflict: support `Copper,Ln,Inr` from the copper order, or amend the r3 interface with the two-layer limit.

### 2.2 GUI caller enforcement

`cmd_update_gui` enforces `kicad_exit == {"state": "exited", "code": 0}` and `options_measured[name]["after"] == (want == "on")`. It checks the identity expectation and the full parity. The integration and identity-mismatch tests pass. The caller-side conditions from the worker review remain the known item 5.

### 2.3 Supported edit scope

`cmd_update_gui` calls `normalized_equal` after identity and parity. That comparison allows only declared footprint Value changes, the three plot settings and the zone-fill cache. A footprint move, add, remove, footprint change or reorder fails `board.unexpected_change`. Thus the update path supports value-only edits. This is the lead's known item 3. Keep `normalized_equal` in `cmd_interface` (line 1220). Remove it from the update path.

### 2.4 Runtime identity

`container_image` compares the resolved image ID with the lock digest. `gui_preflight` checks KiCad 10.0.5 and the Xvfb/xdotool/import/kicad tools, but not the exact image ID. This is the lead's known item 4. A rebuilt image with the same tag and KiCad 10.0.5 passes.

**F3: the worker invocations do not use the r3 measured form.** `pcb.py` runs `/usr/bin/python3 /worker/board_inventory.py` (line 1028) and `/usr/bin/python3 /worker/gui_update.py` (line 803). The r3 section 4 worker row is `uv run --no-project --no-config --offline --python /usr/bin/python3 python WORKER ARGS`. The direct form works in the image, but it deviates from the accepted interface. Confirm the intended form.

`native_check` and `native_versions_ok` are operation-specific. `test_native_prerequisites_are_per_operation` confirms that a missing ngspice blocks only `sim`. `runtime_lock` rejects native execution (the checkpoint supports the container route). A true native host is untested. This is the lead's known item 1.

### 2.5 Operation-specific prerequisites

`export` requires current `erc`, `drc` and `sim` results (when `simulations/` exists). `check_report` compares the binding closure with the current closure and checks the result, binding and raw hash chain. `test_staged_bytes_bind_the_closure` and `test_binding_result_mismatch_after_interruption` cover the staging binding and the mixed binding/result. `erc` needs only `kicad-cli`. This matches the r3 section 8 and the lead's known item 2.

### 2.6 Standalone behavior

`cmd_check` passes `SCHEMAS = SKILL_ROOT/contracts/schemas` explicitly. The `contracts/README.md` copies are identical and hold the `${PROJECT}`/`${PACKAGE}` placeholders. The four script copies and the schema names are compared by `test_pcb_design.py::test_copies_are_unchanged`.

**F4: the copy-set byte check is not applied to the real skill.** `test_skill_packages.py::test_existing_skills` calls only `check_skill`, not `check_copies`. The real `skills/pcb-design/contracts/README.md` and the schema bytes are compared only by the synthetic `test_copy_checks`. A changed README or schema copy would go unnoticed. Add `check_copies` for `pcb-design` in `test_existing_skills` or in `test_copies_are_unchanged`.

### 2.7 Staging leftovers

**F2: `stage_snapshot` creates `out/staging/<op>-<token>/` with a full copy of the input closure. Nothing removes it after a successful or failed publication, and `check` does not report it.** The r3 section 9 says the wrapper deletes its own staging after a successful publication, and `check` lists `.tmp`/`.failed` leftovers. Focused regression: I ran `uv run skills/pcb-design/scripts/pcb.py erc` on a temporary copy of the template. The run passed with 0 findings. It left `/tmp/.../out/staging/erc-40e98f717a93/` with the board, the schematic, the project file and the other inputs. `check` reported the missing drc and sim results and did not report the staging directory. Delete the staging directory after publication and on a handled failure. Have `check` list any remaining `out/staging/*` (exit 1).

## 3. Known items from the lead

| Item | Status in the live code |
|---|---|
| 1. Native route and operation-specific prerequisites | Partly done. `native_check`/`native_versions_ok` are per-operation; a true native host is untested. |
| 2. Bind reports to staged bytes | Done. `stage_snapshot` and `check_report` bind the staged closure; two focused tests cover it. |
| 3. Remove `normalized_equal` from the update gate | Open. Line 842. Keep it in `cmd_interface`. |
| 4. Restrict the GUI adapter to the measured image ID | Open. `gui_preflight` lacks the ID check. |
| 5. Caller conditions and focused negative tests | Partly done. Option and exit enforcement is present. `pcb_changed`, the shared placement filter, the unsupported-drill fixture and the negative tests remain. |
| 6. Inventory docstring correction | Open. The error/refusal JSON goes to stdout while the docstring says stderr. |
| 7. Standalone build and runtime tests, agent trials, docs, complete manifest | Open. |

## 4. New concrete findings

| ID | Finding | Focused evidence |
|---|---|---|
| F1 | Two-layer-only export vs the r3 `Copper,Ln,Top`/`Inr`/`Bot` promise | `export_subset` refuses `len(copper) != 2`; `trial-limits.md` documents the limit |
| F2 | Staging leftovers are neither removed nor reported | One `erc` run left `out/staging/erc-40e98f717a93/`; `check` did not report it |
| F3 | Worker invocations use `/usr/bin/python3` directly, not the r3 `uv run ... python` form | `pcb.py` lines 803 and 1028 |
| F4 | The real skill's copy-set bytes are not compared | `test_existing_skills` calls `check_skill`, not `check_copies` |

## 5. Limits of this review

- This is not final B6 acceptance.
- I ran one focused regression (`erc`) in a temporary copy. I did not rerun the 19-pass log or a broad suite.
- The GUI findings are static. I ran no GUI probe.
- I did not probe a four- or six-layer board. F1 is a static finding.
- I did not test a true native host. The native tests run inside the image.
- I did not review the final standalone build and runtime tests or the agent trials (known item 7).
- All reviewed repository hashes are unchanged. No implementation file was edited.

## 6. Lead decisions on F1 to F4 (agreement)

Date: 2026-11-14.

I agree with the lead on F1 to F4. No concrete conflict. These decisions restore the accepted r3 interface.

- **F1. Copper order and inner layers.** Retain the accepted interface. Support `Copper,Ln,Top|Inr|Bot` from the measured copper order, including inner layers. Add focused four-layer and six-layer fixtures. Do not amend the design to two layers. Keep the blind-via, buried-via and unsupported-geometry refusals unchanged. The fix is in `export_subset` (map `copper_top`, `copper_inner` and `copper_bottom` to the measured order and position) and in the per-layer function check. The fixture must cover the inner-layer suffixes such as `-In1_Cu.gbr` and `-In2_Cu.gbr`.
- **F2. Staging cleanup.** Remove only the wrapper-owned disposable directory `out/staging/<op>-<token>`. Remove it after a successful publication and on a handled failure. Do not remove any other content. `check` lists a remaining `out/staging/*` as a leftover (exit 1). Ignore an empty `out/staging`. For `export`, remove the rest of the stage after `publish_dir` moves the `export` subdirectory.
- **F3. Worker command form.** Use the agreed `uv run --no-project --no-config --offline --python /usr/bin/python3 python WORKER ARGS` form for both `board_inventory.py` and `gui_update.py`. The native interpreter selection stays the lead's known item 1. Do not apply the container Python path to a native host.
- **F4. Copy-set byte check.** Add `check_copies` for the real `skills/pcb-design` in `test_existing_skills`, or compare the copy set in `test_copies_are_unchanged`. The check covers `contracts/README.md` and every schema byte, not only the names.

No implementation edit was made.

## 7. B6 continuation correction agreement

Date: 2026-11-14.

I read `docs/reviews/b6-resume-root.md`, SHA-256 `110d2f84f98de8da1164dab463a7862865ea76fee4f5a059041ed09731ee2cc6`. I agree with the five Codex findings and the two new narrow additions. No concrete conflict. These remain accepted-interface repairs.

### Five Codex findings

1. Parse the simulation assertions from the staged snapshot. Do not decide from an earlier live parse.
2. Validate every assertion field before use. Reject an empty list, an incorrect type, a duplicate pair, a non-finite value and a blank identifier. Malformed input is exit 1 and no traceback.
3. Include the confined simulation dependencies in the input closure, or refuse an unsupported dependency before execution. Never silently omit an input.
4. Include the project-local libraries that the library tables name, including nested paths. Refuse an unsupported or external dependency explicitly. Keep the fixed system libraries under the runtime identity.
5. Validate the complete interface-review record on write and on read. Validate the JSON pointers and the coverage rule. A nonempty value alone is not a review.

### Automatic interface result

I agree. `out/reports/interface.result.json` must bind the exact resulting interface bytes, not only the board hash and the status. Add `interface_sha256` with the hash of the written `mechanical/board-interface.json` bytes. `interface_ready` must compare that field with the current interface bytes, and must also validate the result's `prior_board_sha256` and `expect_sha256` against the `board-changes.json` record and the expectation file.

The live code confirms the gap. The result fields are `record`, `version`, `status`, `prior_board_sha256`, `board_sha256` and `expect_sha256`. There is no `interface_sha256`. `interface_ready` accepts the automatic path when `data["board_sha256"] == live`, `iface_board == live` and `data["status"] == "pass"`. Thus an increase of `height_limits.top_mm` leaves the automatic result accepted. With the field, an interface edit makes the automatic result stale, and `check` requires a new review record or a new rebinding. Keep this a small skill record. Do not add a contracts registry.

### `check --for export`

I agree. Add `export` to the `--for` choices. `check_report("export")` must verify the published directory and every hash in the result `outputs` map. A missing published file or a changed file is a failure (exit 1). Do not demand an earlier export result before the `export` command itself. The `ready` check must not require an export result either.

The live code confirms the gap. The parser choices are `["erc", "drc", "sim", "ready"]`. `check_report` checks the result, binding, raw bytes, closure and status, but it does not compare the published export files with their bound hashes.

No implementation edit was made. No broad test was run.
