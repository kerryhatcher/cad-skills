# B7 final publication repair review (pi-skill-dev)

Date: 2026-11-15 UTC. Scope: the frozen C1/C2/C5 repair,
`docs/reviews/b7-final-publication-repair-claude.md`. I did not edit product code.
I ran no broad suite. I used focused independent probes on temporary projects.
I keep the previous acceptance of the geometry, C3, C6 and C7.

## Hash boundary

Freeze record: `docs/reviews/b7-final-publication-repair-claude.md`,
SHA-256 `bc6b59eac5e0694781a1987ac290a36818af08af22f851e8c182621645244543`.
The record matches the request.

| File | Before (complete-correction freeze) | After (this freeze) |
|---|---|---|
| `skills/pcb-fab-package/scripts/workflow.py` | `65f88be99b9fb758fc095e9086f954688eb1b240b5f192d69d9660bceb075f0b` | `ac38b636a748816a530f89f7a951296da4fd140304a66ee74e5b09261f7a48a7` |
| `skills/pcb-fab-package/scripts/fab.py` | `f63e4d581f9d623b6007b7162c760c347370b7d0d32298205059a2e1a05a47be` | `f63e4d581f9d623b6007b7162c760c347370b7d0d32298205059a2e1a05a47be` |
| `tests/test_pcb_fab_workflow.py` | `0686624ec3c0072279f747053dff649f8293cbcb02dfacb54e14c02d4d920932` | `58b8a45f20e73907b5ca538950189e157f190676f4e67688883732d770276338` |

- `fab.py` is unchanged, as the record states.
- `docs/reviews/b7-workflow-evidence/c1-c2-c5-freeze.sha256` verifies 5 of 5 entries. `sha256sum -c` exit 0.
- The final log `docs/reviews/b7-workflow-evidence/workflow-run-c1-c2-c5-final.log`
  (`fe9d234629587afefac82aed3a25e9c2c1305b786d67c0dabedc43b9ac38f059`) ends with `124/124 passed`, exit 0.
- My probe sources in this directory keep the same product hashes before and after.

## Probes

| Probe | Command | Exit |
|---|---|---|
| C1, C2 and C5 | `uv run --quiet /tmp/b7-final-review-probe-pi.py` | 0 |
| C2 design inputs | `uv run --quiet /tmp/b7-final-c2-probe-pi.py` | 0 |
| Accepted C3, C6, C7 and the directory link | `uv run --quiet /tmp/b7-final-accepted-probe-pi.py` | 0 |

The retained sources are `b7-final-publication-repair-probe-pi.py`,
`b7-final-publication-repair-c2-probe-pi.py` and
`b7-final-publication-repair-accepted-probe-pi.py` in this directory.

## C1: complete destination writes (accepted)

`write_out` confines the complete destination and then calls `PIO.atomic_write`.
`refuse_links` refuses a planned destination that is a link before any write.

I measured these cases. Each case returned exit 2. The link stayed. The outside target stayed
unchanged.

- A link at the profile file `design/captured/profile.yaml`.
- A dangling link at the same profile file.
- A link at a design output (`inventory.json`).
- A link at a design log (`logs/erc.stderr`).
- A link at a supplier output (`supplier.kicad_dru`).
- A link at a worker report (`mask.json`).
- A link at the package final destination.
- A link at the package staging destination.

The directory-link regression (`test_captured_child_link`) also passes. The outside directory
stays empty.

The worker reports are written to the private directory `out/fab/supplier/measure`, then
published through `write_out`. The worker geometry code is unchanged.

## C2: one byte set and captured design inputs (accepted)

The `Reader` reads each package input once. The decision and the copy use the same bytes.

- I changed `supplier-result.json` after the package read it. The package stayed `qualified`.
  The published report equals the original bytes. The injected field is absent.
  The manifest output hash equals the original hash.
- I changed `design-result.json` after the package read it. The same result holds.

The supplier reads each consumed design output once and compares it with the design binding
before any measurement. I changed `export/board-PTH.drl` after the design run and before the
supplier run. The supplier returned exit 1 with the reason
`the design output export/board-PTH.drl differs from the accepted design binding`.

The measurements read the private copies only. I changed the source mask Gerber during the
mask worker. The measured hash stayed the captured hash. The `mask.json` `gerber_sha256` and
the `measure_inputs` entry are equal and equal the captured hash. The `measure_inputs` hashes
are recorded in the supplier result and in the supplier binding.

## C5: validated bytes at publication (accepted)

The manifest is validated. The final gate then compares the staged manifest and each staged
output with the validated hash and size. It rejects a link, a missing output and an
unexpected file. A gate failure raises `pkg.final_gate` and keeps the staging directory.
Nothing is published.

I measured these cases. Each case returned exit 1. The final package is absent. The staging
directory is kept. The named failure is present.

- A staged Gerber changed after validation:
  `gerber/board-F_Cu.gbr differs from its validated bytes`.
- The staged manifest changed after validation:
  `the staged manifest differs from its validated bytes`.
- An unexpected file in the staging tree: `extra.txt is not an expected output`.
- A missing staged output:
  `gerber/board-F_Cu.gbr is missing from the staged package`.

The unchanged project returned exit 0 and `qualified`, and it published the package.

## Accepted cases under the frozen code

I ran the previous accepted focused cases again. All checks pass.

- C1 directory link: refused, no outside write.
- C3: a byte-only change to the original manual record is refused before publication.
- C6: a held project lock refuses `review-source`, writes nothing, and releases the lock later.
- C7: the interrupted run stops after the binding write, keeps the old result, releases the
  lock, and the old result cannot pass.

## Direct drawing command limit

The record discloses that the `drawing-facts` and `drawing` commands in `fab.py` write their
`--out` path directly. I examined this limit against the assigned scope.

- The repair scope is the design, supplier and package command inventory.
- The design and supplier commands call the pure functions `fab.drawing_facts` and
  `fab.drawing_pdf`. They write the result through `write_out`.
- The two standalone commands are outside the design, supplier and package flow. A caller of
  those commands supplies the path.

Thus the limit is outside the assigned scope and does not block this correction. If a later
change makes those commands part of the package flow, that change must confine their paths.

## Limits and residual risks

- The probes use in-process hooks and temporary projects. They do not prove a race with
  another process. The record discloses the same limit.
- `review.gate` and the B1 validator still read live project files. These are freshness
  reads. The record discloses this.
- The private execution trees (`out/work` and `out/measure`) use direct writes inside a fresh
  private directory. `refuse_links` refuses the top directory before mutation. A concurrent
  plant inside the tree is not covered. This is the disclosed race limit.
- An empty unexpected directory in the staging tree is not reported. Only files are checked.
  This is not a publication risk.

## Verdict

The C1/C2/C5 repair is accepted. The three corrections meet the accepted conditions:

- C1: every direct leaf of design, supplier and package goes through `write_out`. A
  preexisting link is refused before any mutation.
- C2: the package reads each artifact once. The decision and the copy use the same bytes. The
  supplier binds its measurement inputs to the design binding.
- C5: the final gate binds the staged manifest and every staged output to the validated bytes.
  A failure keeps the staging directory and publishes nothing.

The previous geometry, C3, C6 and C7 acceptance stays. I found no new blocker inside the
assigned scope.