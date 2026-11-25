# B7 residual publication repair review (pi-skill-dev)

Date: 2026-11-15 UTC. Scope: the frozen residual repair
`docs/reviews/b7-residual-publication-repair-claude.md`. I read the same frozen bytes as the
codex review. I changed no product file. I ran no broad suite.

## Hash boundary

Freeze record: `docs/reviews/b7-residual-publication-repair-claude.md`,
SHA-256 `08ec5765fa96e35988a2d08cb70b60a72687aa28bc551bb2a6f64b228ac93b06`.
The record matches the request.

| File | Before (C1/C2/C5 freeze) | After (this freeze) |
|---|---|---|
| `skills/pcb-fab-package/scripts/workflow.py` | `ac38b636a748816a530f89f7a951296da4fd140304a66ee74e5b09261f7a48a7` | `b81466ee0e8329abdb82472083a26d9497efe2d0a3cbea9acb40947d44cc969e` |
| `skills/pcb-fab-package/scripts/fab.py` | `f63e4d581f9d623b6007b7162c760c347370b7d0d32298205059a2e1a05a47be` | `5be6e136b7ebf193d6df11798104c26f10f15c89ee23d4e4409306308d802e0c` |
| `tests/test_pcb_fab_workflow.py` | `58b8a45f20e73907b5ca538950189e157f190676f4e67688883732d770276338` | `a973b5be6164cc8b1eb26fa3dc7636a37099834511db2f539817f95f02b972de` |

- `docs/reviews/b7-workflow-evidence/residual-freeze.sha256` verifies 5 of 5 entries.
  `sha256sum -c` exit 0.
- `workflow-run-residual.log`
  (`90434d2d36091b01c134ed26207734dd2dc6f4cae49e4057afbf8226f90f6b5e`) ends with
  `132/132 passed`, exit 0.
- `test_pcb_fab_package-residual.log`
  (`efd9c46d0650857d5a5fadd6b98bdd934474256ef3b5f27621503f7ff2d1aa88`) ends with
  `101/101 passed`.
- The product hashes are unchanged before and after this review.

## Independent probes

Retained source: `b7-residual-publication-repair-probe-pi.py` in this directory.
Command `uv run --quiet /tmp/b7-residual-review-final-pi.py`, exit 0.

| Case | Result |
|---|---|
| Baseline package | exit 0, `qualified`, published |
| Changed row, old content hash | exit 1, not published, stop `supplier result content differs from its content hash` |
| Changed row, new hash, inconsistent exit | exit 1, not published, stop `supplier result exit differs from its rows` |
| Missing mandatory row, new hash | exit 1, not published, stop `missing mandatory rows ['service.order_multiple']` |
| Empty row set | exit 1, not published, stop `supplier result has no rows` |
| Consistent failing row | exit 1, `draft`, published, reason `supplier conditions are not all passing` |
| Binding changed after validation | exit 1, not published, staging kept, stop `the binding design-binding.json changed before publication` |
| `drawing` at a dangling link | exit 2, link kept, target not created |
| `drawing` at an existing link | exit 2, link kept, target unchanged |
| `drawing-facts` at a dangling link | exit 2, link kept, target not created |
| `drawing-facts` at an existing link | exit 2, link kept, target unchanged |
| `drawing-facts` ordinary output | exit 0, written |

## Assessment

### Drawing output

`write_standalone` makes the path absolute, refuses a link at `--out` and at its parent
directory, then calls `PIO.atomic_write` with the parent directory as the root. I agree with
the output-root rule. The command has no project argument, so it does not claim project
confinement. The reported leaf-link defect is closed for both drawing commands.

Narrow note: `write_standalone` checks the leaf and the immediate parent only. A link at a
higher path component is not refused by that check. The atomic helper confines the write to
the resolved parent root, so the output does not leave that root. This is not a blocker for
the standalone commands.

### Supplier result

`_supplier_measure` writes `content_sha256`. The package calls `validate_supplier_result`
before it consumes the result. The function checks the content hash, the profile id and
hash, the row list, the unique condition names, each row flag and status, the complete
mandatory condition set, and the exit. The exit uses `rows_exit`, which keeps the existing
precedence. A mismatch raises `Stop`, so nothing is published. The design result uses the
same content check.

I agree. The consistent failing row stays a draft and is not a refusal. The content hash
detects a change. It is not a signature. The record states this limit.

### Final binding comparison

The package passes the captured binding bytes to `final_gate`. The gate compares the current
binding bytes with the captured bytes and with the result `binding_sha256`. It then examines
the output map of the captured binding. A drift keeps the staging directory and publishes
nothing. I agree. This closes the final-gate binding finding.

### Preserved accepted checks

The staged manifest and output gate, the complete destination writes, the one byte set, C3,
C6, C7, the directory link and the geometry results stay accepted. The new tests and my
probes do not change them.

## Setup coverage confirmation

I confirm the setup coverage corrections in `docs/reviews/oshpark-kicad-coverage-claude.md`:

- Five service profiles exist. `oshpark-four-layer` gives service layers 4 and
  `oshpark-six-layer` gives service layers 6. Each carries the internal-copper clearance
  rule. The corrected text no longer says that no profile exists.
- B6 supports `drc --refill-zones`. The focused test
  `test_refill_matches_accepted_board_and_rebinds_interface` covers it. The fabrication
  workflow has no fill step. The corrected text states the precondition only and makes no
  new refill measurement.
- The source manifest target is `skills/pcb-fab-package/sources.yaml` at the skill root.

No new refill measurement and no export-contract change are part of this repair.

## Verdict

The residual publication repair is accepted. The three findings are closed inside the
assigned scope:

- The standalone drawing commands refuse a link at the output.
- The supplier result binds its content and rejects inconsistent rows and a wrong exit.
- The final gate compares the current binding bytes with the captured bytes.

No product edit. No broad suite.