# B7 complete correction freeze review (pi-skill-dev)

Date: 2026-11-15 UTC. Scope: the seven B7 corrections in the frozen
`pcb-fab-package` workflow. I did not edit product code. I ran no broad accepted suite.
I used focused probes on temporary projects. The geometry and report-key cases stay closed.

## Hash boundary

- Freeze: `docs/reviews/b7-complete-correction-freeze-claude.md`,
  SHA-256 `0ff3976651f25171fd7bbdcad8a9a2314fe62690785027aa63fdfbb2fdb46772`.
- Manifest: `docs/reviews/b7-workflow-evidence/c4c6c7-freeze.sha256`. All 17 entries pass.
  `sha256sum -c` exit 0.
- Product hashes before and after the probes:
  - `65f88be99b9fb758fc095e9086f954688eb1b240b5f192d69d9660bceb075f0b` `workflow.py`
  - `f63e4d581f9d623b6007b7162c760c347370b7d0d32298205059a2e1a05a47be` `fab.py`
  - `0686624ec3c0072279f747053dff649f8293cbcb02dfacb54e14c02d4d920932` `tests/test_pcb_fab_workflow.py`
- I changed no product file. The retained probe sources are `b7-complete-correction-*-pi.py`
  in this directory.

## Probes

| Probe | Command | Exit |
|---|---|---|
| Leaf links (C1) | `uv run --quiet /tmp/b7-review-unit-probe-pi.py` | 0 |
| Bytes and manual record (C2, C3) | `uv run --quiet /tmp/b7-review-workflow-probe-pi.py` | 0 |
| Design leaf links (C1) | `uv run --quiet /tmp/b7-review-c1design-probe-pi.py` | 0 |
| Review lock and interruption (C6, C7) | `uv run --quiet /tmp/b7-review-c6c7-probe-pi.py` | 0 |
| Result double read (C2, C5) | `uv run --quiet /tmp/b7-review-c2residual-probe-pi.py` | 0 |

## C1: file leaves still escape confinement (blocker)

Root measured a link at `captured/profile.yaml`. I confirmed it independently.
`profile_from_bytes` confines the directory `captured`. It does not confine the file
`captured/profile.yaml`.

- The call returned without refusal.
- The target did not exist before the call.
- `outside_file_created` is true.
- The target hash is `2aedaa0c8076b18005345bf0f56f97396121e1faae915152d5bfcf10a942ad87`.
- The link is unchanged.

The same defect is at other direct-write leaves:

- `check_manual` wrote `manual-artifact.txt` and `manual-evidence.json` outside the project.
  It returned `pass`.
- `inspect_slots.main` wrote the report outside the project with exit 0.
- A design run with links at `out/fab/design/inventory.json` and
  `out/fab/design/logs/erc.stderr` returned exit 0. Both outside files exist.
  The inventory hash is `668cd36362fccae9302d96f8a1c212b0e1462aa171863854bce413e8a7e28b90`.
  The log hash is `e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855`.
  The links remain.

The mask report path has a freshness guard. A link at `out/mask.json` returns exit 2 and
writes no outside file. The worker writes the report directly after the guard. A change
between the guard and the write is not prevented.

### Direct-write inventory

Status key: **A** uses `PIO.atomic_write`. **L** is a direct write with no check on the leaf.
**D** is a directory operation with no check on the leaf. **S** is a fresh staging path.

- `_design`:
  - `captured/profile.yaml` (L), `work/*` (S).
  - `logs/erc.stderr`, `logs/drc.stderr`, `logs/export-*.stderr`, `logs/inventory.stderr` (L).
  - `out/inventory.json` (L).
  - `out/erc.json`, `out/drc.json` through `shutil.copy2` (L).
  - `out/export/*` through `shutil.copy2` (L).
  - `out/drawing-facts.json` (L), `out/fabrication-drawing.pdf` (L).
  - `out/design-binding.json` (A), `out/design-result.json` (A).
- `_supplier`:
  - `captured/profile.yaml` (L), `work/*` (S).
  - `out/supplier-drc.stderr` (L).
  - `out/slots.json` through the worker (L).
  - `out/mask.json`, `out/mask-bottom.json` through the worker (L, guarded).
  - `out/supplier.kicad_dru`, `out/supplier.kicad_pro`, `out/supplier-drc.json` (L).
  - `out/manual-artifact.txt`, `out/manual-evidence.json` (L).
  - `out/supplier-binding.json` (A), `out/supplier-result.json` (A).
- `_package`:
  - `supplier/captured/profile.yaml` (L).
  - `dest/`, `dest/evidence/`, `dest/reports/` (D).
  - every staged output (S), `dest/manifest.json` rewrites (S).
  - `PIO.publish_dir` (A).
- `review-source`:
  - `out` and `out.parent/observations.json` through `PIO.atomic_write` (A).
- `fab.py` commands `drawing-facts` and `drawing` write their `--out` path directly.
  They are outside the design, supplier and package write set.

The directory-link regression is preserved. `confine(project, scratch)` still refuses a
link at `captured`. The frozen 112/112 log records `test_captured_child_link` as pass.
I did not rerun the suite.

Required repair: confine the complete destination, including the file leaf, before any
mutation. Write every direct leaf through `PIO.atomic_write`. That includes the logs, the
`copy2` copies, the manual files and the worker reports. Add a file-link regression. Keep
the directory-link regression.

## C2: bound artifacts pass, unbound results do not (blocker)

The baseline package returned exit 0 and `qualified`. The published
`gerber/board-F_Cu.gbr` hash equals the measured binding hash and the manifest hash:
`021492e73c46aadd172b04c0b79a905973a590ee2272b8dc39763ce25f9860a1`.

A controlled change to the bound PTH drill after `review.gate`:

- exit 1, `draft`.
- the reason `gerber/board-PTH.drl changed after its measurement` is present.
- the published bytes are the injected bytes.
- the binding, the final gate and the drill check also name the change.

This matches the accepted rule: a changed artifact fails or keeps the measured bytes.

Residual blocker: `supplier-result.json` is read twice. The package loads it early for
the decisions. `out_item` reads it again for the copy. It is not in the supplier binding,
so `expected_for` returns None.

A hook changed `supplier-result.json` after the early load:

- exit 0, `qualified`, `reasons []`.
- the published `reports/supplier-result.json` contains the injected field.
- the published hash is `b1889ec18892c620aa76683354d9b01185ad76c17d04ad57c91e125ec4bf5ae9`.

Thus a new hash from a changed copy inherits the old pass. This is the C2 prohibition.
The same double read exists for `design-result.json`, `observations.json` and
`REVIEW.json`. The current checks catch those three, and the package becomes `draft`.
The `design-result.json` probe returned exit 1 and `draft` with the reason
`the supplier result does not bind this design result`.

Required repair: read each consumed artifact once. Use those bytes for both the semantic
decision and the package copy. Retain the same hash. Add the result files to the binding,
or capture their bytes before the decisions.

## C3: original manual record (accepted)

I added one byte to `out/fab/manual-record.json` after the supplier run.

- Package exit 1, `draft`.
- Reason `original manual record changed before publication`.
- The original hash changed from
  `de4170df5d3132ba1b8687602d320fcbc9710fed371cac20a466f3bdc0e68901` to
  `49c71f8d546321eaa3d3495e3f2e949645b0169c37c890a97af271f02c730e61`.
- The final gate also names the supplier input change.

The comparison of the original record, the retained copy and the referenced artifact is
present. Accepted.

## C4: captured inputs and remaining live reads

The design and supplier calculations use `captured` for these items:

- the runtime lock, the source rules, the project settings, the board record and the
  drawing inputs.
- the manual record and the manual artifact.
- the manifest inputs, the board hash and the tool versions.

The manifest inputs and the board record come from the capture. The board hash is
`sha256(consumed["kicad/board.kicad_pcb"])`.

These live reads remain:

- `review.gate` reads the stored pages and the live review pages at package start. A
  difference adds a problem and makes the package `draft`. It cannot make a package pass.
- The B1 validator reads the live project and the staged package. It adds findings and
  makes the package `draft`. It cannot remove a finding.
- The supplier reads the design outputs (`inventory.json`, the export drill and mask
  Gerbers) live. The design binding and the final gate check them. The supplier does not
  verify the design binding before it uses them.

Residual inspection finding: the supplier mask report records `gerber_sha256` of the mask
Gerber at supplier time. The package does not compare that field with the published
Gerber hash. A transient change during the supplier run could bind a measurement to bytes
that differ from the published bytes. I did not measure this case. The measured C2 result
blocker is independent of it.

## C5: staged package bytes (blocker, codex probe)

The final gate is immediately before `publish_dir`. It compares the source inputs, the
bindings and the original manual record. It does not take `dest` and does not hash the
staged package.

The validator hashes the staged package before the final gate. A change after the
validator and before `publish_dir` is not caught. I agree with codex's staged-output
mutation finding. The final gate must bind the actual staged bytes (the manifest and
every output) to the validated bytes immediately before `PIO.publish_dir`.

My `supplier-result.json` probe is the same class from the source side. The semantic
decision uses the early bytes. The package publishes later bytes.

## C6: review-source lock (accepted)

All five focused checks pass:

- a held lock refuses `review-source` with exit 2.
- no review record is written.
- the existing observation file is unchanged.
- without a holder, `review-source` writes the record with exit 0.
- the lock is released after the command.

The lock covers the reads and the two atomic writes.

## C7: interrupted binding and result (accepted)

All five focused checks pass:

- the run stops after the new binding write.
- the new binding is written.
- the old result remains, because the new result is not written.
- the interrupted run releases the project lock.
- the old design result cannot pass against the new binding.

The package returns a non-zero code and the reason
`does not bind the current design-binding.json`.

## Verdict

- Accepted: C3, C6 and C7. The geometry and report-key cases stay closed. I did not
  change them.
- Blocked: C1 (file leaves), C2 (`supplier-result.json` double read) and C5 (the staged
  bytes are not bound at publication). The C1 directory-link case is not a blocker. The
  file-link case is.
- The next narrow repair must also cover every direct leaf in the inventory above. The
  repair must confine the complete destination and use the atomic helper. It must read
  each consumed artifact once. It must bind the staged package bytes immediately before
  publication.
- Add a file-link regression. Keep the directory-link regression.

## Limits

- The probes use in-process hooks and temporary projects. They do not prove a race with
  another process.
- The C1 design probe uses the accepted image through `podman`. The other C1 cases are
  direct calls.
- The interrupted run uses an exception. It does not kill the process.
- I did not run the 112-test suite. I used the frozen 112/112 and 101/101 logs as evidence
  for the unchanged accepted cases.