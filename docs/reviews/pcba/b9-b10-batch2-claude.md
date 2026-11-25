# B9/B10 batch 2 supersession: frozen record (Claude)

Date: 2026-11-15 UTC. Author: claude-pcba-dev (w1P:p7). Branch `work/pcba`, model `claude-haiku-5-5`.
Release: `docs/reviews/pcba/b9-b10-batch2-release-root.md`. Scope: placement and supplier artifacts, C1 mechanical-alternate prohibition (schema and loader), validated alternate selections with named refusals, and the sample provenance. No commit has been made.

This record supersedes the working-tree state disclosed to the lead after batch 1. The batch 1 record stays unchanged as history. Its hashes do not preserve the overwritten bytes, and this record says so.

## Behaviour in this batch

- Sierra outputs: `bom/sierra-bom.xlsx` with the exact sample header row at Excel row 7, `placement/sierra-xy-draft.csv` in mil with `T`/`B` side, `test/test-record.json` with every limit and hand-install step marked `not measured`, and `reports/sierra-status.json` with every open convention `unconfirmed` and qualification `unqualified`.
- Hand-installed BOM policy: `supplier-profile.yaml` extension `hand_installed_bom`. Missing or unknown stops only the BOM.
- A profile whose bytes differ from the board record hash refuses with `supplier.profile_mismatch`.
- A map 1.1 mechanical entry with alternates refuses with `map.alternate_on_mechanical`, in the loader and in the schema.
- Alternate selections are validated before lookup. A list-valued, numeric or non-mapping selection refuses with `alternate.selection_invalid`, one finding and no traceback.

## Commands and exit codes

| Command | Exit | Result |
|---|---:|---|
| `uv run tests/test_pcba_design.py` | 0 | 62 passed, 0 failed |
| `uv run tests/test_skill_packages.py` | 1 | 7 passed. Failure: `test_snippet_routing` (release-owned routing entry) |
| copies check | 0 | 15 of 15 OK |

## Files and SHA-256

| Path | SHA-256 |
|---|---|
| `docs/reviews/b9-b10-interface-claude.md` | `36d7e1b0917417d6e537db57fd46a92d4b949303e1d13d5f40b93e0a29b1d361` |
| `docs/reviews/sierra-source-evidence/BOM-Sample-and-Demo.provenance.md` | `bda33654ff098881832c746c1586baaa370272eef8d47f210b6cd0c7e0b63d30` |
| `docs/reviews/sierra-source-evidence/BOM-Sample-and-Demo.xls` | `1b486a0a1da968e128cf109bd25e50837c99b5a8f83a490f748a1c1ccb1b769c` |
| `skills/pcba-design/COPY_SHA256.txt` | `0ea6a004fb9577587e2364e3f2d365df8d2387cbfd4a4232b048c0b058881c6c` |
| `skills/pcba-design/SKILL.md` | `371f99d5ae246b43ad6f2f764bb898a2148be29d8d62896c942af5736585fb7f` |
| `skills/pcba-design/contracts/README.md` | `7c3454f4715cb77925e8471d2f2308dc408af30238e0abd8cc7d61db5a874915` |
| `skills/pcba-design/contracts/alternate-approval.schema.json` | `dc598d5666f4a2f6c7a9d62d9d09579310500e5d5dfc534b66f4eb518540a66f` |
| `skills/pcba-design/contracts/part-map-1.1.schema.json` | `890a36acfb696c0823b370a33661ea9d7476578433513bf79c5b0007060217ce` |
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
| `skills/pcba-design/scripts/pcba.py` | `a8f1e0d832444a1820141ec3dafbd5a6fde65fd50cad47c9898ce8dbd82678ab` |
| `skills/pcba-design/scripts/project_io.py` | `f4f2fb06ddb14805da9ea80d06bb4ab8e30c17102529746a7015bf15ed6de9e3` |
| `skills/pcba-design/scripts/sexp.py` | `2dfc36f2bc4141c870de2eb4edb2bc83fd692dedf7c31241aa084f3927e8669a` |
| `skills/pcba-design/scripts/sierra.py` | `13fc4636733498ef568a22d9acb4a881b6aa147a11dd51f4c78604ac46630887` |
| `tests/fixtures/pcba-design/project/board.kicad_pcb` | `efa69ee5fb853347ccb336b5049d67d9676602ce07cd9db4cd4bb114b8e81198` |
| `tests/fixtures/pcba-design/project/board.yaml` | `3137bf4b40e21360c15ad36776f20f9dfda570649197f38a3901ca531019ab4f` |
| `tests/fixtures/pcba-design/project/components/cap-100n.yaml` | `6d92bae75baf73304a9e5ed0d5dca93ab58ccc2e64fb9a8c7925fc4040ff593e` |
| `tests/fixtures/pcba-design/project/components/header-2.yaml` | `2546128f2893a074f06cb31978f58f3897d41c8c43ca5d4c3d10722b610ed2e9` |
| `tests/fixtures/pcba-design/project/components/led-green.yaml` | `449962943f98cd6a3db980d3274e92a93a60000510bcde89c0f997f7414c7faa` |
| `tests/fixtures/pcba-design/project/components/parts-map.yaml` | `0d26cc93458dd2d743f24d12901e8e92da04d36175e551c82b60066404144e08` |
| `tests/fixtures/pcba-design/project/components/resistor-10k.yaml` | `11bef0c36e83db32be23df9e0db5b8465d8e18c4b490ab70c8e6d4c1c7f308d5` |
| `tests/fixtures/pcba-design/project/components/testpoint.yaml` | `3c09b1bace014af514a78adc5a6d869403b1bda04b7410930670c35e29f3a81a` |
| `tests/fixtures/pcba-design/project/supplier-profile.yaml` | `29e33a4103eaa6d19c563a6cea52e1b0b25937480edff3a6d127e3428a2deaa4` |
| `tests/fixtures/pcba-design/project/variants.yaml` | `6ce057427c1d130cb5ef00fcd913a36cbb23927ff38274cea95517653759ad36` |
| `tests/test_pcba_design.py` | `7798a91c507b46e550f331137133c60c6e5a82ff77563b54e96ead88dfdd262b` |

Bytecode caches are excluded. This record is not hashed by itself.
