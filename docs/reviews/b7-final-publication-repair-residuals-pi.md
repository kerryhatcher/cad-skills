# B7 final publication repair residuals (pi-skill-dev)

Date: 2026-11-15 UTC. Scope: the three residual findings in
`docs/reviews/b7-final-publication-repair-review-codex.md` and the OSH Park setup
coverage note `docs/reviews/oshpark-kicad-setup-root.md`.
I changed no product file. I ran no broad suite.

## Hash boundary

- Frozen repair: `docs/reviews/b7-final-publication-repair-claude.md`,
  SHA-256 `bc6b59eac5e0694781a1987ac290a36818af08af22f851e8c182621645244543`.
- `skills/pcb-fab-package/scripts/workflow.py`
  `ac38b636a748816a530f89f7a951296da4fd140304a66ee74e5b09261f7a48a7` before and after this review.
- `skills/pcb-fab-package/scripts/fab.py`
  `f63e4d581f9d623b6007b7162c760c347370b7d0d32298205059a2e1a05a47be` before and after this review.
- The retained probe source is `b7-final-publication-repair-residuals-probe-pi.py` in this
  directory. Command `uv run --quiet /tmp/b7-codex-findings-probe-pi.py`, exit 0.

## Finding 1: standalone drawing leaves (agreement)

I agree. The `drawing` and `drawing-facts` branches in `fab.py` call `Path.write_bytes` and
`Path.write_text` on `--out`. They do not confine the path and they follow a symbolic link.

My measurements:

- `drawing` with a link at `--out`: exit 0, the link stayed, the outside file changed.
  The new outside hash is `a81ecd3e0dad66b2643a71970f73f15e45ac79f0ea7e427dd78fe99accd4156d`.
- `drawing-facts` with a link at `--out`: exit 0, the link stayed, the outside file changed.
  The new outside hash is `9090f642761234e8f099cedb70bf8d515fa8dce9a9570a38362aea0027dd6b24`.

This is a real defect in `fab.py`. It is outside the design, supplier and package command
inventory, but it is not safe. It stays open.

## Finding 2: supplier result integrity (agreement)

I agree. `supplier-result.json` has no content hash. The supplier binding does not list
`supplier-result.json` in its outputs. The package reads the result bytes once, but it does
not re-derive the exit from the mandatory rows.

My measurement: I changed one mandatory row to `fail` and kept `exit: 0`. The package
returned exit 0, status `qualified`, no reasons, and it published the package. The result
hash changed from
`634e0d25fa400f220558020766d1f9198350017d23880f88ff2f7c85b085b7bd` to
`9b08480f84943ef6a5723d49a2d7cf243effce419c67f537fbd17c4ad397086e`.

The repair must give the supplier result a checked content hash, or bind its exact bytes in
the supplier binding. The package must also refuse a mandatory row that disagrees with the
recorded exit. Add a focused regression for a changed mandatory row.

## Finding 3: final gate binding freshness (narrow agreement)

I agree with a boundary. `final_gate` re-reads each binding from its live path and checks the
live outputs against that binding. It does not compare the current binding bytes with the
captured binding bytes. A coordinated change to a binding and its output after the package
read is not detected.

My measurement: I changed `design/export/board-F_Cu.gbr` and the matching
`design-binding.json` output hash after the manifest validation. The package returned exit 0,
status `qualified`, no reasons, and it published the package. The captured binding hash
`8ee25af9649b1ae06146e0dc894046361c5e55e253fa0433369fd8b894f0c8ae` differs from the current
binding hash `829fa43e99ee5ef74c8ac45d7415fe0daf4b57373d47106fc4f837345acd3b58`.

Boundary: the published Gerber is the captured bytes
(`21158fad32961531dd6f2dd66b12d69ac9dcdd1d0eade9597a816356496f0ea7`), not the changed source
(`d2192d76a05a07274626a0d0404995914085889ca3914fb5fdb43566c00ceb67`). The staged manifest
and output gate binds the staged bytes. So this finding is a missed source and binding drift,
not a wrong staged artifact. The package publishes a frozen snapshot. It can be stale against
the current source.

The repair must compare the current binding bytes with the captured binding bytes, or with the
result `binding_sha256`, immediately before publication. Add a focused binding change after
manifest validation.

## Accepted checks

I keep the accepted C1/C2/C5 parts from
`docs/reviews/b7-final-publication-repair-review-pi.md`. The three findings above are
additional residuals. They do not change the accepted behavior of the complete destination
writes, the one byte set, or the staged manifest and output gate. C3, C6, C7, the directory
link and the geometry results stay accepted.

## OSH Park KiCad setup coverage

I read `docs/reviews/oshpark-kicad-setup-root.md` and all listed constraints. I agree with
the plan.

- The KiCad 9.x native route and the KiCad 10 Gerber route stay separate. Local Gerber
  success does not prove native KiCad 10 support.
- The setup table must not change the accepted export contract, the mask geometry rules or
  the profile without a concrete compatibility reason and both reviews.
- Item 9 (X2) is the highest-risk item. OSH Park recommends X2. The accepted neutral
  exporter uses no X2 attributes. Keep this as a recorded difference until a measured
  compatibility reason exists.
- Items 4 and 7 (fill and save, and the effective exported layer functions) touch the export
  contract. They stay in the coverage text and do not change the contract.
- The source links, the measured version and the source dates belong in the release text.
  Full supplier page copies stay as local evidence outside the bundle.

I will examine Claude's coverage-gap report and the exact proposed files when root sends it.

## Verdict

- Finding 1: agreed. The two standalone drawing commands are unsafe.
- Finding 2: agreed. The supplier result must bind its content and reject inconsistent
  mandatory rows.
- Finding 3: narrowly agreed. The final gate must compare the current binding bytes with the
  captured bytes. The published artifacts stay the captured bytes, so the gap is stale-source
  detection.
- No product edit. No broad suite.