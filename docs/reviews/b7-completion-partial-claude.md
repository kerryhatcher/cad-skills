# B7/B8 completion batch: partial status (claude-skill-dev)

Date: 2026-11-15 UTC. Author: claude-skill-dev (model claude-haiku-5-5). Release: `b7-acceptance-completion-release-root.md`.

This is a partial record. It does not freeze the whole completion batch. The open items in section 4 remain.

## 1. Done

### 1.1 Normalized source manifest installed

- Copied byte for byte from `/mnt/storage/projects/cad-skills-worktrees/release/skills/pcb-fab-package/sources.yaml`.
- Installed at `skills/pcb-fab-package/sources.yaml`.
- SHA-256 `fd415dc58ab60455c022112105905ede674ce389ba26b025ead80651dbee488f`, the accepted value.
- No profile or source byte changed.

### 1.2 Row 44: drawing correction

Change: `skills/pcb-fab-package/scripts/workflow.py`, new function `drawing_problem`, called in `_package` right after the profile is loaded. It runs before staging and before publication.

The check does three things:

1. It reads `drawing-facts.json`, `fabrication-drawing.pdf` and `inventory.json` from the design directory.
2. It recomputes the facts from the captured inventory, the captured board and the captured supplier record. It requires the stored facts to equal the recomputed facts byte for byte.
3. It requires the stored PDF to equal `fab.drawing_pdf` of the recomputed facts.

A mismatch raises `Stop(EXIT_FAIL, ...)`. Nothing is published. Two reasons are used: `the drawing facts differ from the captured board inventory and profile`, and `the fabrication drawing is not the drawing made from its captured facts`.

The accepted final gate and the captured-byte rule are unchanged.

### 1.3 Acceptance tests, new file

`tests/test_pcb_fab_acceptance.py`. Result: 15 of 15 passed, exit 0 (`b7-completion-evidence/acceptance-run1.log`).

| Row | Checks | Result |
|---|---|---|
| 31 | 31a no maximum drill limit; 31b generated rules are minimums only; 31c the 250 mil note is a note | pass |
| 41 | 41a B6 worker refuses the slot drill with exit 2 and names it; 41b B7 derivative reports the slot with endpoints, minor and major dimensions | pass |
| 44 | 44a genuine drawing matches its facts; 44b stored drawing equals a rebuild from its stored facts; 44c substituted PDF refused; 44d changed facts refused; 44e package refuses the substituted PDF with exit 1 and no destination | pass |
| 45 | 45a hole count equals inventory; 45b diameters equal inventory; 45c board hash bound; 45d no regex parser in `drawing_facts` | pass |

### 1.4 Regression check after the row 44 change

`tests/test_pcb_fab_workflow.py`: 132 of 132 passed, exit 0 (`b7-completion-evidence/workflow-run-after-r44.log`).

The geometry suite (`tests/test_pcb_fab_package.py`) was not rerun. The change does not touch the geometry files.

### 1.5 Standalone installation: first steps

- Copy of the skill outside the repository: `/tmp/claude-1000/-mnt-storage-projects-cad-skills/1498d7bc-bc96-42a4-a233-ae48c580ec6e/scratchpad/standalone/pcb-fab-package`.
- Hashes of the copy: `b7-completion-evidence/copy-hashes.txt`.
- `fab.py profile` on the two-layer and four-layer profiles: exit 0, `profile valid` (`profile-two-layer.out`, `profile-four.out`).
- `fab.py judge --kind minimum --measured 9.9 --threshold 10 --unit mil`: exit 1, `fail` (`judge.out`). This is the correct result.
- Container image: `localhost/cad-skills-pcb:b6`, present locally. Not pulled. The `design` run passed through it, and the design result records its identity.
- Not yet run: `design`, `supplier`, `package` from the installed copy, with a project copied into scratch space.

## 2. Source findings

### 2.1 Row 28: outline and cutout concave corner radii

- The retained source is the supplier page `skills/pcb-fab-package/supplier/pages/two-layer.html`, section "Milling tool diameter". It states:
  - Outline or profile milling: 0.068 in (1.72 mm).
  - Interior or cutout milling: 0.040 in (1.01 mm).
- The page gives tool diameters. It does not state a minimum concave corner radius.
- The r8 values (0.033, 0.034, 0.035 in outline; 0.019, 0.020, 0.021 in cutout) are half of the tool diameters, rounded. The page does not state the half-diameter rule.
- Meaning: the minimum concave corner radius equals the tool radius. This is an inference from the tool diameter, not a retained statement. Do not implement it as a supplier rule from the acceptance table alone.
- No profile has a corner limit. `min_corner` and `corner_radius` do not appear in any profile or script.
- The smallest change needs a source sentence from the supplier. Until then, row 28 stays open. The profile schema already permits named limit keys, so no shared schema change is needed.

### 2.2 Row 29: filled-plated via-in-pad

- The profile key `service.via_construction_prohibited` lists `blind`, `buried` and `filled_plated_via_in_pad` for all five profiles. The retained two-layer page states "Filled+Plated Vias (via-in-pad)": "No".
- No existing project field records a filled or plated via process. The contract schemas contain no via-fill field.
- The bound manual evidence record is specific to the silk condition. Its keys bind `board_sha256` and `silk_gerber_sha256` (`check_manual` in `workflow.py`). It cannot establish a via process.
- Therefore the process cannot be established from a via position alone, and no existing field or manual route establishes it. Per the release, the supplier must not infer it.

Exit distinction (preserved, from the release):

- Blind and buried vias can be established from the board, because the via span is a geometric fact. Release says these must report a supplier failure with exit 1 when establishable. The current worker refuses a non-through span with exit 2 (`board_inventory.py` line 73, `REFUSED_VIA`). This is an open behavior change. It needs a decision on the mapping of the worker refusal to the supplier condition, because `board_inventory_slots.py` is frozen.
- Filled and plated via-in-pad: not establishable, so exit 2 (unsupported) until a bound field or evidence exists. Decision needed on the evidence route.

## 3. Open product items (not done)

| Row | Item | Blocker |
|---|---|---|
| 23, 24 | Four-layer fixture with a filled internal zone, plated holes at measured clearances, same-net 0 mil and unconnected 9.9, 10, 10.1 mil | Fixture work. `stack4.kicad_pcb` has no zone. Needs zone creation, refill and DRC measurement. Not started. |
| 26 | Manual route with three measured silk boundary fixtures and bound artifacts | Fixture work. Not started. |
| 28 | Corner measurement and profile limit | Source sentence needed (2.1). |
| 29 | Blind and buried exit 1 mapping; via-in-pad process evidence | Decisions (2.2). |
| 32 | Order quantities 1, 2, 3, 4 through the supplier path | Needs supplier runs. Not started. |
| 16, 22 | Package omission tests (`fab.supplier_rules`, schematic and drawing) | Not started. |
| 36 | Stored page hash through the review path | Not started. |
| Standalone | `design`, `supplier` and `package` from the installed copy | Not started. |

## 4. Freeze status

Changed files in this batch, with hashes in `b7-completion-files.sha256`:

- `skills/pcb-fab-package/scripts/workflow.py`: `33a751ca66111ab0bd81ae3722bde6fdaa5782bdabd50a46f4e693f0469a60a7`.
- `tests/test_pcb_fab_acceptance.py`: `9df565568f3b488b085646e5aebefedbc4ed31fad677d286c90d8aa14e19b793`.
- `skills/pcb-fab-package/sources.yaml`: `fd415dc58ab60455c022112105905ede674ce389ba26b025ead80651dbee488f`.

These hashes describe a partial batch. The complete batch will be frozen after section 3 is closed or assigned.

## 5. Not changed

- The frozen retrieval files: `fetch_sources.py` (`35e21d37…`) and `test_source_retrieval.py` (`1d61a5a2…`) are unchanged.
- The accepted geometry files are unchanged.
- The accepted publication path is unchanged, except the new check before staging.
- No historical trial script was repaired.
- No provider call and no commit.
