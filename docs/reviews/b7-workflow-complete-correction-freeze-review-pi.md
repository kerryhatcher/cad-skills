# B7 workflow complete correction freeze review (pi-skill-dev)

Date: 2026-11-14 UTC. Scope: `b7-workflow-complete-correction-freeze-claude.md`
(SHA-256 `92c22fdb7d9a6d9bd45e5d238e798a0e4e504c3363a06b07d04a99dba2b86847`). My focus is the actual
row-15a source and staged reports, the drill and copper-edge product cases, the project lock, and nested
confinement with failure behavior. I did not edit implementation and I ran no unrelated suite.

## Hash boundary

The three workflow hashes match the freeze record before and after this review.

```text
05ad9a5ab565d1eb0ef18d6d9a8b0e4575e869c9d9f7cb344de33811e82435d4 skills/pcb-fab-package/scripts/workflow.py
84a09ec61fb3b453ff74e0a748b8974b17ac5739929697423e1c76bc615da3ca skills/pcb-fab-package/scripts/fab.py
bf80316793ee9e4090112688e17714a80ce97ab427ebfe60040fe8863ea1b1e1 tests/test_pcb_fab_workflow.py
```

The final log is `5a82c8bca456d1d8ad28bbcc0eae51ac729f5b9fc4168586e76d28036d22cf7d`. It is identical to the
92/92 product-key log, per `b7-workflow-evidence/final-freeze-logs.sha256`. The root link probe is
`docs/reviews/b7-complete-correction-link-probe-root.json`
(`16608f8cd7c9ae430e30919323dac119ed9ce2b1585cac3cc486d27f06ae8877`).

## Row 15a source and staged reports: accepted

`test_row_15a` now uses `_first_track_marker`, which reads the board with the accepted S-expression parser and
returns the segment midpoint in nanometres and the segment UUID. It runs the two cases separately.

- Ignore case: the source sets `rule_severities.track_width = "ignore"`. The source `design/drc.json` omits
  the target finding. The staged `supplier-drc.json` shows it active.
- Exclusion case: the source sets the measured exclusion `track_width|<mx>|<my>|<uuid>|<nil>`. The source
  `design/drc.json` marks the target finding `excluded`. The staged `supplier-drc.json` shows it active.
- Both cases: the `min_trace` row fails with the measured key, the staged project clears the exclusion and
  sets the `track_width` severity to `error`, and the source bytes stay unchanged.

The 92/92 log shows the fourteen row-15a checks pass. This matches the accepted requirement and my earlier
finding.

## Drill and copper-edge product cases: accepted

`test_product_keys` changes the board to a 0.2 mm via and a track inside the edge limit. It reads the
staged `supplier-drc.json` and checks:

- `drill_out_of_range` on the fixture via UUID.
- `copper_edge_clearance` on the fixture track UUID.
- The `min_drill` and `edge_keepout` rows fail through those keys.

The 92/92 log shows these checks pass. This is a product result, not a dictionary assertion.

## Project lock: accepted

`design`, `supplier` and `package` hold `project_lock` for the whole operation. `LockHeld` and
`LockMalformed` map to exit 2. `test_binding_and_lock` writes an invalid `.cad-skills.lock` and measures exit
2. The 92/92 log confirms.

## Nested confinement and failure behavior: concrete blocker

`profile_from_bytes` writes `scratch/profile.yaml` with `scratch.mkdir(parents=True, exist_ok=True)` and
`path.write_bytes(raw)`. It does not confine the write path.

`_package` calls `profile_from_bytes(consumed["profile"], supplier_dir / "captured")` before
`confine(project, final)`. A symbolic link at `supplier_dir/captured` therefore writes `profile.yaml` outside
the project. The root probe measured exactly this: `outside_profile_created` is true, and the command then
exits 1 for a missing design result (no container ran).

The same pattern exists in `_design` and `_supplier`. They call `confine(project, out)` before
`profile_from_bytes(consumed["profile"], out / "captured")`, but `confine(project, out)` checks `out` and its
parents, not the child `captured`. A symbolic link at `out/captured` is the same escape.

The 92/92 test replaces `out/fab/design` (the `out` itself), which `confine` catches. It does not cover the
`captured` child or the pre-confine package write, so the pass does not cover this escape.

Required correction: confine every write path, including the nested `captured` scratch and its parents and
links, before any mutation. Prefer parsing the captured profile bytes without a scratch write, or write the
scratch through the confined and atomic helpers. `_package` must confine before the profile write.

## Combined with the root review

I read the current `b7-complete-correction-review-root.md`
(`4fed76deb44f8f9c1ea501a002dd16a2bb214a2929a850e412512191129f3522`). I agree with C1, C2, and C3.

C2 is the package copy binding. The retained probe `b7-package-copy-probe-root.py`
(`a22ce9422499fc4e98ff774ec403766507b7e361d0e68a113f67d7c6bffd3f53`) and its result
`b7-package-copy-probe-root.json` (`06f1df0b76d4953d58cc3d895d989c07209e8c9b3c3fb9d18233852b2ad10eb1`)
hook `shutil.copy2`, inject invalid Gerber bytes during the copper export copy, and restore the source.
`out_item` copies with `shutil.copy2` and records `sha_file(target)`. The later binding check reads the
restored source and passes. Measured: `changed_copy_exit 0`, `changed_copy_status qualified`, `reasons []`,
`published_injected_bytes true`, `source_sha256 d14d20de...`, `published_sha256 00964a24....`

C3 is the changed original manual record. The retained evidence `b7-manual-current-probe-root.json`
(`60d5bd787195f2262ee9eee38e81005f31fe5063b880f163515f4947cf06ed11`) shows `exit 0`, `status qualified`,
`reasons []` after one newline was appended to the original `out/fab/manual-record.json`
(`manual_before_sha256 78631b69...`, `manual_after_sha256 a8e3e453...`). The package compares the retained
copy `supplier_dir/manual-evidence.json` for the `manual` key. `check_manual` does not retain the original
record path, so the package cannot compare the current original record. The artifact comparison is present.

Required correction for C1, C2, and C3: read each consumed artifact one time, verify that byte snapshot
against the hash from the accepted measurement binding, write those bytes, and record that same hash. Do not
hash the published copy after a separate read and attach the new hash to the old pass. Confine the full write
path, including nested `captured` components and links, before any mutation. Retain the original manual
record path with its measured hash, and compare that current path before publication, in addition to the
retained copy and the referenced artifact.

## Agreement on the publication correction

I read `b7-publication-correction-root.md` at SHA-256
`3f66e87e9b7c899d1b7a34bf7b84d258ef65aa730025037be47743cd43711e06`. The earlier hash `258c7a3f...` became
stale after a text-only STE edit in item 7 ("Confirm that" became "Make sure that"). No requirement changed.
I confirm agreement with all seven required changes and the focused regressions. They restore the original
four-part decision and include C1, C2, C3 and the Codex live-input, final-gate, review-lock and
interrupted-write findings. I have no concrete scope conflict. The accepted geometry, KiCad report keys, row
15a, and the deliberate drill and edge results stay.

## Verdict

Row 15a, the drill and copper-edge product cases, and the project lock are accepted. The nested confinement
escape (C1), the package copy binding escape (C2), and the changed original manual record (C3) block
publication integrity. The agreed publication correction resolves C1, C2, C3 and the Codex findings. The
complete correction freeze is not accepted until that correction lands and passes its focused regressions.
No unrelated suite and no implementation edit.
