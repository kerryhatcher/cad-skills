# B10 completion batch: frozen record (Claude)

Date: 2026-11-15 UTC. Author: claude-pcba-dev (w1P:p7). Branch `work/pcba`, model `claude-haiku-5-5`.
Governing note: `docs/reviews/pcba/b9-b10-remaining-execution-claude.md`, sha256 `22afe3344d32c1306060446fc5622bc9bd586c15811e0b96accd3ce6c3607610`. Release: `docs/reviews/pcba/b9-sierra-acceptance-b10-release-root.md`. Handoff: `docs/reviews/pcba/b10-handoff-claude.md`.
No commit has been made. This record supersedes the overlap record for the bytes listed below. The overlap record is kept unchanged.

## Behaviour in this batch

- Package command: one package per id under out/pcba/packages, staged and checked against the validated set, published once. Prior packages are never changed.
- KiCad export (local image, no pull, no network): gerbers for ten layers, PTH and NPTH drill files in the stated format, an assembly PDF, an SVG board image, and a DRC report. The export runs on a temporary copy outside the project.
- Thirteen independent checks, one evidence file each: design.drc is a tool check; design.erc and design.parity are pending (no schematic bound); fab.profile_evidence is pending (no retained supplier evidence); fab.export_inventory, fab.layer_order and fab.drill_split are tool checks; fab.supplier_rules is unconfirmed (plane and XY conventions open); the five asm checks are tool checks.
- Manifest status is unqualified. Reasons name each open condition, the open supplier locations, and the open export applicability.
- Test record: every step is not measured. No physical result is claimed.
- Restrictions: nonempty board restrictions refuse with supplier.restriction_review, as for the Sierra path.
- Evidence and manifest records are validated with the copied validator before the staged gate.
- Layer names: the silkscreen plots use the Silkscreen name in the file names.

## Commands and exit codes

| Command | Exit | Result |
|---|---:|---|
| `uv run tests/test_pcba_design.py` | 0 | 77 passed, 0 failed |
| `uv run tests/test_skill_packages.py` | 1 | 7 passed. Failure: `test_snippet_routing` (release-owned routing entry) |
| copies check | 0 | 15 of 15 OK |

## Files and SHA-256

| Path | SHA-256 |
|---|---|
| `docs/reviews/b9-b10-interface-claude.md` | `36d7e1b0917417d6e537db57fd46a92d4b949303e1d13d5f40b93e0a29b1d361` |
| `docs/reviews/sierra-source-evidence/BOM-Sample-and-Demo.provenance.md` | `bda33654ff098881832c746c1586baaa370272eef8d47f210b6cd0c7e0b63d30` |
| `docs/reviews/sierra-source-evidence/BOM-Sample-and-Demo.xls` | `1b486a0a1da968e128cf109bd25e50837c99b5a8f83a490f748a1c1ccb1b769c` |
| `skills/pcba-design/COPY_SHA256.txt` | `0ea6a004fb9577587e2364e3f2d365df8d2387cbfd4a4232b048c0b058881c6c` |
| `skills/pcba-design/SKILL.md` | `4025e5cecc5868c6e01bafc13616adf761fa1c277fbeebbf192cbbbeefc20315` |
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
| `skills/pcba-design/scripts/checks_asm.py` | `bb4df3b6619c5f321f99f9d5a13edf7c546853208ccdb9cc853b888f6c9c2133` |
| `skills/pcba-design/scripts/checks_design.py` | `4f1f006e5edf4d32b7a08e2566239e5e59fabaf460b1fa9ef3212fd3e7052858` |
| `skills/pcba-design/scripts/checks_fab.py` | `8e656ae2eae06842a063a5037a3885ff5503f5b3336aad59ac46a520c8b993f4` |
| `skills/pcba-design/scripts/export.py` | `cc1cc26ca6d31b84bb6f45f74b5edec92c655cf2000c053e4bf92885abaa03af` |
| `skills/pcba-design/scripts/package.py` | `89547a618f120d902535d7c7df3899dc830620b6d6b4af3dc493dc62746d2754` |
| `skills/pcba-design/scripts/pcba.py` | `9ced5a78c73d09482a9a237e14eb2fbcf6660486eaf850e84035da1f742b753b` |
| `skills/pcba-design/scripts/project_io.py` | `f4f2fb06ddb14805da9ea80d06bb4ab8e30c17102529746a7015bf15ed6de9e3` |
| `skills/pcba-design/scripts/report.py` | `07ecb36ad20743c0dacbbe84c6d12100a4086001523e1f95a9075d57ed67a1f8` |
| `skills/pcba-design/scripts/sexp.py` | `2dfc36f2bc4141c870de2eb4edb2bc83fd692dedf7c31241aa084f3927e8669a` |
| `skills/pcba-design/scripts/sierra.py` | `f4d8ef1a3b5e832ec0743501cce55947fb019d5ced77576537dcaaa276f0d379` |
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
| `tests/test_pcba_design.py` | `c6c9759d7d77f7fa955e5c2f391d8a5d706867b21330f9c48423cf85efaeb1a9` |

Bytecode caches are excluded. This record is not hashed by itself.
