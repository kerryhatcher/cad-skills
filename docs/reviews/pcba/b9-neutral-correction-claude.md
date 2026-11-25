# B9 neutral correction batch: frozen record (Claude)

Date: 2026-11-15 UTC. Author: claude-pcba-dev (w1P:p7). Branch `work/pcba`, model `claude-haiku-5-5`.
Authorization: `docs/reviews/pcba/b9-neutral-correction-root.md`. Scope: the 15 correction items only. Sierra conversion, B10 publication and alternates stay outside this batch. No commit has been made.

This record supersedes the snippet statement in `docs/reviews/pcba/b9-neutral-batch-claude.md`. That earlier record called the snippet failure pre-existing. It is not. The failure comes from the new skill directory: `tests/test_skill_packages.py:388` requires every skill to have a `tests/snippet_envs.json` routing entry. The release workstream owns that entry. The earlier record is kept unchanged as history.

## Correction items and where each is covered

| Item | Implementation | Focused test |
|---|---|---|
| 1 lock before capture | `pcba.py` `main` holds `project_lock` around `build` | `test_input_changed_before_write_refused` runs `build` in process |
| 2 confinement by resolved path | `Snapshots.capture` with `under=components` | `test_symlink_outside_components_refused`, `test_symlink_inside_components_resolves_to_one_file` |
| 3 one snapshot per file, relative paths | `Snapshots.by_real`, `inputs()` | `test_input_records_are_project_relative_and_once` |
| 4 same resolved path in rows and inputs | `row.part_path` from the snapshot | `test_symlink_inside_components_resolves_to_one_file` |
| 5 output alias refusal | `check_output_alias` before the write | `test_output_aliasing_board_record_refused_and_input_kept`, `test_output_hard_link_to_input_refused` |
| 6 rehash before write | `Snapshots.check_unchanged` before `atomic_write` | `test_input_changed_before_write_refused` |
| 7 raw tokens in `source_tokens` | `read_board` keeps the tokens | `test_high_precision_tokens_kept_exactly`, `test_neutral_row_fields_present` |
| 8 finite derived values, named refusals | `parse_token` returns `board.malformed_token` or `board.nonfinite_token` | `test_malformed_token_refused_once`, `test_nan_token_refused_once`, `test_overflow_token_refused_once` |
| 9 implicit zero angle | `angle_source` `implicit_zero`, `source_tokens.angle` null | `test_implicit_zero_angle_is_stated` |
| 10 datum, midpoint mapping, board quantity, empty alternate | row fields | `test_neutral_row_fields_present` |
| 11 zero per-board quantity for excluded rows | `per_board_quantity` | `test_base_rows_match_board_and_sides` (TP1) and the interface section 6 text |
| 12 `assembly_instruction` | copied from the hand-install reason, empty on automatic rows | `test_assembly_instruction_and_grouping` |
| 13 BOM key | `(manufacturer, mpn, state, installation_method, assembly_instruction)` | `test_assembly_instruction_and_grouping` |
| 14 conflicting stock refusal | `stock.conflicting_records` | `test_conflicting_stock_records_refused` |
| 15 demand once per reference | demand summed from populated BOM groups | `test_identical_repeated_records_count_demand_once` |

Each refusal writes nothing. The existing 20 tests still pass.

## Commands and exit codes

| Command | Exit | Result |
|---|---:|---|
| `uv run tests/test_pcba_design.py` | 0 | 35 passed, 0 failed |
| `uv run tests/test_skill_packages.py` | 1 | 7 passed. Failure: `test_snippet_routing` at `tests/test_skill_packages.py:388` (missing routing entry for `pcba-design`, release-owned) |
| `sha256sum -c skills/pcba-design/COPY_SHA256.txt` | 0 | 15 of 15 copies OK |

## Files and SHA-256

| Path | SHA-256 |
|---|---|
| `docs/reviews/b9-b10-interface-claude.md` | `36d7e1b0917417d6e537db57fd46a92d4b949303e1d13d5f40b93e0a29b1d361` |
| `skills/pcba-design/COPY_SHA256.txt` | `0ea6a004fb9577587e2364e3f2d365df8d2387cbfd4a4232b048c0b058881c6c` |
| `skills/pcba-design/SKILL.md` | `da3d22eb0cd74078fbb35ae175126f3595e7e265b8d4802d53b1a6e3315ec91f` |
| `skills/pcba-design/contracts/README.md` | `7c3454f4715cb77925e8471d2f2308dc408af30238e0abd8cc7d61db5a874915` |
| `skills/pcba-design/contracts/part-map.schema.json` | `d3c5a6335faf0206461b38c6e9da52c574a9bee354eb63acde3a924fd5a20ed2` |
| `skills/pcba-design/contracts/schemas/board-interface.schema.json` | `8fd8b0e4d15d8ceb29de85245f3f5e3f378b56ed30ac08f9f78cb0cb5a547b9f` |
| `skills/pcba-design/contracts/schemas/board.schema.json` | `9d0b1702bfed18d50485f6ccd59d2da9eeb14c13e4a3246ccb04cb559178ad97` |
| `skills/pcba-design/contracts/schemas/evidence.schema.json` | `eb631648f9862ff31c927cb639df9b6ffd441f4862d96b068966fcf8ec19001b` |
| `skills/pcba-design/contracts/schemas/export-settings.schema.json` | `911043d2779333071517be168015ca6cbcb4a3a531220e3fcf8ce89a5f413116` |
| `skills/pcba-design/contracts/schemas/manifest.schema.json` | `096c7aa85eab334d8e5e48d0a7b35e9d66b15c9468c3916185064895a58df790` |
| `skills/pcba-design/contracts/schemas/part.schema.json` | `50e36d4941fe4db3533c0a69f93da3a1c812d5143f569ccc729947daf060e908` |
| `skills/pcba-design/contracts/schemas/registry.json` | `5ae88c4127e7a51829c89db6a321cfc5adc0b7d9718c9b5a358f75a83285e5fd` |
| `skills/pcba-design/contracts/schemas/supplier-profile.schema.json` | `29489d3a14d5fd7403ff016200375669ffdd78aae42c24ace821fbf34e9c98ea` |
| `skills/pcba-design/contracts/schemas/toolchain-lock.schema.json` | `3911e6fb457798dbd5d621d41be470e93bcf9ab3387980ec6bf4472cc5a73e0c` |
| `skills/pcba-design/contracts/schemas/variants.schema.json` | `23fd221c65924bd777f94131a0b1153f1423e06fa4a88f6435d1fb5264106ae7` |
| `skills/pcba-design/contracts/schemas/waivers.schema.json` | `2e3764fb32fda0766ad489d968d637ad7e0f31e7173e7902367278f906e5d928` |
| `skills/pcba-design/contracts/validate.py` | `102e252c211bab973adc4e5ae97c051ad4b35dfb59e53916d8b8099144731d9e` |
| `skills/pcba-design/scripts/pcba.py` | `1e69b6f3bced2cb9b30556829a6ced51b6d8330a0a1c1353239e2033bc3471a4` |
| `skills/pcba-design/scripts/project_io.py` | `f4f2fb06ddb14805da9ea80d06bb4ab8e30c17102529746a7015bf15ed6de9e3` |
| `skills/pcba-design/scripts/sexp.py` | `2dfc36f2bc4141c870de2eb4edb2bc83fd692dedf7c31241aa084f3927e8669a` |
| `tests/fixtures/pcba-design/project/board.kicad_pcb` | `efa69ee5fb853347ccb336b5049d67d9676602ce07cd9db4cd4bb114b8e81198` |
| `tests/fixtures/pcba-design/project/board.yaml` | `95901a4b284357c2b6507f7eb4d7dcb39a84228587cb6d759c71743cf7a9257a` |
| `tests/fixtures/pcba-design/project/components/cap-100n.yaml` | `6d92bae75baf73304a9e5ed0d5dca93ab58ccc2e64fb9a8c7925fc4040ff593e` |
| `tests/fixtures/pcba-design/project/components/header-2.yaml` | `2546128f2893a074f06cb31978f58f3897d41c8c43ca5d4c3d10722b610ed2e9` |
| `tests/fixtures/pcba-design/project/components/led-green.yaml` | `449962943f98cd6a3db980d3274e92a93a60000510bcde89c0f997f7414c7faa` |
| `tests/fixtures/pcba-design/project/components/parts-map.yaml` | `0d26cc93458dd2d743f24d12901e8e92da04d36175e551c82b60066404144e08` |
| `tests/fixtures/pcba-design/project/components/resistor-10k.yaml` | `11bef0c36e83db32be23df9e0db5b8465d8e18c4b490ab70c8e6d4c1c7f308d5` |
| `tests/fixtures/pcba-design/project/components/testpoint.yaml` | `3c09b1bace014af514a78adc5a6d869403b1bda04b7410930670c35e29f3a81a` |
| `tests/fixtures/pcba-design/project/variants.yaml` | `6ce057427c1d130cb5ef00fcd913a36cbb23927ff38274cea95517653759ad36` |
| `tests/test_pcba_design.py` | `123592419d4cbe7a7ee3953a8e1ffb09bccc0e8cac6912c8326689efc905b454` |

Bytecode caches are excluded. The record is not hashed by itself.

## Known gaps

- Alternates (section 7) are not implemented. The part map schema rejects an `alternates` key, and `selected_alternate` is empty.
- Placement fields (`export_rotation_deg`, midpoint estimates) are not produced. They belong to the placement batch.
- No supplier file and no manifest are written.
- The final freshness check covers the captured inputs. It does not cover the output directory.
