# B11 completion batch review: Pi

Date: 2026-11-15. Reviewer: pi-mechanical-dev, pane w1P:pE.

Scope: the frozen completion batch `docs/reviews/mechanical/b11-completion-batch.sha256` and its evidence. Files stay frozen. I did not edit a product file.

Basis: interface revision 8, SHA-256 `5a0b4850aa57c11973560ca2551ead734b7fcfd3cc70a168d8ec3f25495966f5`, and the completion direction `b11-completion-direction-root.md`.

**Decision: the positive flow works end to end, but the batch is not accepted. Five measured findings and seven integrity findings follow. The narrow corrections reuse the accepted `project_io` helpers.**

## 1. Manifest and suites

The manifest SHA-256 is `f6d69c03847689592a716006f1c2048bd069b0698fe1a4d60a71406c8d013417`. All 26 entries match (`sha256sum -c` gives 26 OK).

| Suite | Result |
|---|---|
| `uv run tests/test_mechanical.py` | 55 pass, exit 0 |
| `uv run tests/test_mechanical_fit.py` | 38 pass, exit 0 |
| `uv run tests/test_skill_packages.py` | 8 pass, exit 0 |
| `uv run tests/test_project_io.py` | 11 pass, exit 0 |

Positive flow on a fresh fixture copy, local image, no pull:

| Step | Command | Exit |
|---|---|---|
| export | `uv run scripts/mechanical.py export --project /tmp/b11c` | 0 |
| fit | `uv run scripts/mechanical.py fit --project /tmp/b11c` | 0 |
| release | `uv run scripts/mechanical.py release --project /tmp/b11c` | 0 |

All fourteen results pass: C01, C02, C02d, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12 and the closed hole set. Regeneration gives new STEP and drill bytes and the geometry still passes. The release binds the exact output hashes. This matches revision 8.

## 2. Measured findings

### P1. A slot or an oval is silently omitted

Revision 8 says: "A slot, an oval or any other drill class refuses and names the object."

I added an oval NPTH pad at `(125, 125)` to a fixture copy and exported the drill file with the recorded switches. KiCad writes the slot as one routed hit:

```text
T2
X20.3Y-6.8G85X22.3Y-6.8
```

`parse_excellon` matches only `X<num>Y<num>` to the end of the line. The G85 line does not match. The parser returns three hits, not four. The slot is not refused and not named. The closed hole set and C04 do not see it.

Correction: detect a routed hit (`G85`), a slot, and an oval, and refuse with the object named. Do not drop a line.

### P2. A crafted export record escapes the project

Revision 8 makes a path-escape refusal necessary.

I added one key to the published `out/mechanical/export/export.json`:

```text
"../../../../../etc/hostname": {"role": "report", "sha256": "<hash of /etc/hostname>", "bytes": <n>}
```

`run_fit` reads `(export_dir / rel).read_bytes()` without `project_io.confine`. It read `/etc/hostname` and the fit exited 0. `project_io.confine` refuses the same path with `PathEscape`.

Correction: confine every path from the export record through `project_io.confine`, and treat a refusal as the named `path.escape`. Apply this to `run_fit` and `run_release`.

### P3. The excluded-hole reason is not checked

Revision 8 and case T49 state that each `excluded_through_holes` entry gives a position, a diameter and a reason. An entry without them must refuse.

I added `extensions.excluded_through_holes: [{"x": 1.0, "y": 1.0}]` to a fixture interface. `mechanical.py check` exited 0. `mechanical.py` has no reference to `excluded_through_holes`, `slot`, `oval` or a reason check.

Correction: validate each excluded entry in `mechanical.py` and refuse a missing reason or a missing diameter.

### P4. A mixed drill file uses the role `drill_pth`

Revision 8 has the roles `drill_pth` and `drill_npth`. The implementation exports one mixed file and labels it `drill_pth`. The release record and the reference state this limit.

Correction: select one rule and state it in the contract:

- Export two files with `--excellon-separate-th` and use the two roles, or
- Add one closed role, for example `drill_mixed`, by a lead contract decision.

Do not label a mixed file `drill_pth`.

### P5. The C09 mating-edge exemption and the proxy body length are unreviewed rules

Revision 8 C09 has no mating-edge exemption. `c09_lateral` exempts the connector corners on the declared mating edge and ignores that edge. The proxy connector body length equals the insertion depth. The reference marks both as unreviewed.

A rule that ignores a boundary can hide a real clearance violation. Correction: remove the exemption, or obtain one lead-reviewed rule that names the detected condition and the reason. State the proxy body length the same way.

## 3. Integrity findings (inspection)

The accepted pattern reads each input once, consumes those bytes, and makes a final freshness check before publication. The flow deviates.

### I1. `capture` does not keep the captured bytes

`capture` returns `{path: {sha256, bytes}}`. It does not return the bytes. `run_export` then calls `shutil.copyfile` on the live `board.kicad_pcb`. The hash check and the read are separate. A file can change between them.

Correction: keep the captured bytes and consume them, as the accepted snapshot pattern does.

### I2. `run_export` runs the mutable image reference

`run_export` calls `_image_id(image_ref)`, compares the ID with the settings, then passes `image_ref` (a string) to `_run_kicad`. The run can use a different image than the checked ID.

Correction: run `kicad-cli` by the pinned image ID or digest, not the mutable reference.

### I3. `run_fit` reopens live export paths

`run_fit` compares each published output with the export record, then `evaluate_project` reopens the same live paths. A file can change between the check and the read.

Correction: pass the checked bytes into `evaluate_project`, or re-check immediately before each read.

### I4. `run_release` trusts `report["status"]`

`run_release` reads `report["status"]` and refuses only on that value. It does not recompute `overall_status(report["results"])`. A forged or edited report can pass.

Correction: recompute the status from the results and compare.

### I5. The release outputs omit the byte count

Revision 8 section 8 states that each output gives a path, a role, an exact SHA-256 and a byte count. `run_release` writes path, role and SHA-256 only.

Correction: add the byte count.

### I6. The release record does not match the revision 8 field list

Revision 8 section 8 lists `board_sha256`, `electrical_inputs`, `interface_sha256`, `component_evidence_sha256`, `fixture_source_sha256`, `export_settings_sha256`, `toolchain_image_id` and `first_mismatch`. The record uses one `inputs` map and has no `first_mismatch`. `first_stale` uses the `CAPTURED` order and does not check `electrical_release_id`, `release_id`, `toolchain_image_id` or `fixture_id`.

Correction: either write the accepted fields and order, or obtain one lead decision that replaces the list. The binding must stay explicit.

### I7. No final input freshness read before publication

`run_release` captures the inputs at the start, then reads the report, the export record, the source record and the outputs. It does not read the inputs again immediately before the final write. The accepted pattern has a last freshness gate.

Correction: add the final freshness read immediately before the release write.

## 4. Public CLI

`pcb.py mechanical` exposes only `check` and `readiness`. `export`, `fit` and `release` are reachable only through `scripts/mechanical.py`. The reference documents the direct module commands.

The completion direction item 5 says to complete the flow through the documented command. Confirm whether decision 14 also needs the flow through `pcb.py mechanical`, or whether the direct module commands are the intended public path.

## 5. Positive confirmations

- The export stages, checks each staged hash, and publishes with atomic writes.
- The Excellon reader takes the plating from the `AperFunction` comment. The real format works.
- C03 compares both the DXF circle and the STEP cylinder radius.
- The connector proxy takes its position and angle from the source record through the transform, not from the interface under test. A rotated frame fails C06.
- C07 uses CadQuery solids, excludes the connector's own proxy, and names an offender.
- `overall_status` fails closed and names every missing identifier.
- The test-only variant refuses a release. The stale input, the altered output and the image mismatch refuse by name.
- Path confinement and atomic writes are used for the captured inputs and the fixed output paths.

## 6. Necessary narrow correction list

1. Refuse a slot, an oval and any routed or non-circular drill class, and name it (P1).
2. Confine every path from the export record and every staged path (P2).
3. Check the excluded-hole reason and diameter (P3).
4. Select the drill role rule (P4).
5. Remove the C09 mating-edge exemption and the proxy body length rule, or obtain one reviewed rule (P5).
6. Keep the captured bytes, run the pinned image by ID, recompute the status, add the byte counts, and add the final freshness read (I1 to I7).
7. Confirm the public CLI path (section 4).

## 7. Lead mechanical resolutions: conflict check

Files stay frozen. I checked each resolution against revision 8 and the measured results.

| Resolution | Conflict check |
|---|---|
| P4: export separate PTH and NPTH files, use the existing roles | No technical conflict. One documented inconsistency follows (C1). |
| P5: no mating-edge exemption. The cavity is the board outline offset outward by `clearance_mm`, chamfer included. Test proxy containment in that cavity. Keep the fixed tolerance. | No conflict with revision 8. The frozen code and reference do the opposite (C2). |
| Connector proxy `body_length_mm` 4.0, separate from `insertion_depth_mm`, no datasheet claim | No conflict. The frozen code uses the insertion depth as the body length. One clarification follows (C3). |
| Keep the revision 8 explicit release fields and mismatch order | No conflict. The frozen record uses one `inputs` map and the `CAPTURED` order (I6). |
| Route export, fit and release through `pcb.py mechanical` as thin dispatch | No conflict. The frozen route has check and readiness only (section 4). |
| I3: consume the captured checked bytes or private copies | No conflict. It strengthens I3. A second check followed by a live read is not the repair. |

### C1. The drill command string conflicts with the two roles

Revision 8 section 6 and the frozen `export-settings.json` write the drill command without `--excellon-separate-th`, but they name the two roles `drill_pth` and `drill_npth`. One mixed file cannot fill two roles. The resolution adds the separate files. Then the command string and the settings record need `--excellon-separate-th`, and the two output file names need a definition. This is a small documented inconsistency, not a technical conflict. State the corrected command and the two file names in the combined report.

### C2. The frozen C09 and reference conflict with the resolution

The frozen `c09_lateral` enforces an inward keepout from the board edge and exempts the connector mating edge. The frozen reference states the same. The resolution replaces both with outward-cavity containment and no exemption. The frozen code and reference must change. State one precise rule: the cavity polygon is the outline offset outward by `clearance_mm`, the chamfer is included, a point on the board edge is inside the cavity, and the proxy corners must stay inside the cavity within 0.01 mm. This also removes the need for the exemption, because a corner on the board edge is inside the outward cavity.

### C3. The body position convention is not stated

The resolution adds `body_length_mm` and removes the exemption, but it does not state which side of the mating face the body occupies. With outward-cavity containment, the placement decides whether C09 passes. State the convention, for example that the body extends inward from the mating face. The fixture proxy must satisfy the cavity, or the positive flow fails. The 4.0 mm proxy overhangs only if the convention places it outward, and the cavity allows only 0.5 mm of overhang.

### C4. The frozen positive evidence becomes historical

The RUN-LOG positive fit and release were produced with the old body length and the removed exemption. After the resolutions, the positive flow must run again and the new evidence must freeze with the corrected files. Keep the old evidence as history.

## 8. Claude position on C2: a concrete wording conflict

Claude accepted C1 to C4 and stated a position: separate PTH and NPTH files with fixed names, "one inward-cavity rule with no exemption", the body inward from the mating face with zero overhang, and a re-run and re-freeze.

C1, C3 and C4 agree with the lead and my notes. C2 does not agree in words.

- The lead states: the cavity is the board outline offset **outward** by `clearance_mm`, and "It is not an inward keepout from the board edge."
- Claude states: "one inward-cavity rule with no exemption."

These conflict if "inward-cavity" means a keepout that measures clearance from the board edge:

- With the body inward from the mating face and zero overhang, the body face sits on the board edge. The distance to the boundary is 0 there.
- An inward keepout with clearance 0.5 mm and no exemption fails C09 at that corner.
- The outward-offset cavity passes, because a point on the board edge is inside the outward cavity.

One precise rule is necessary:

1. The cavity polygon is the outline offset outward by `clearance_mm`, chamfer included.
2. A proxy corner is inside the cavity when it is inside that polygon or on its boundary.
3. The tolerance stays 0.01 mm.
4. No mating-edge exemption.

If Claude means this rule, the word "inward" must go from the position. If Claude means an inward keepout, the positive flow fails and the lead resolution is not met. This is the one concrete conflict to resolve before implementation.

## 9. Resolution confirmation

The lead accepted the four clarifications in `b11-completion-resolutions-root.md`. All conflict notes are closed.

| Note | Resolution |
|---|---|
| C1 drill | Separate staged files with `--excellon-separate-th`. I measured the names in the local image: `board-PTH.drl` and `board-NPTH.drl`. Bind them to `drill_pth` and `drill_npth`. No mixed role. Refuse an unsupported drill class with a named finding. |
| C2 cavity | Confirmed outward offset by `clearance_mm`, chamfer included, tolerance 0.01 mm, no mating-edge exemption. A point on the board edge is inside the outward cavity. Claude withdrew the word "inward". |
| C3 body | The body extends inward from the mating face, opposite the transformed insertion vector, with zero overhang. `body_length_mm: 4.0` is declared in the project proxy evidence and stays separate from `insertion_depth_mm`. No datasheet claim. |
| C4 evidence | The current positive evidence stays historical. Run the corrected positive and negative cases before the next complete freeze. |

The integrity requirements in the resolution match I1 to I7: consume captured bytes or private copies, run the measured image ID, keep the explicit release fields and byte counts and mismatch order, confine record paths before a read or a write, recompute the comparison completeness and status before release, complete the final freshness and output-integrity gate, and use thin local dispatch for `pcb.py mechanical export`, `fit` and `release`.

My measured drill names agree with the resolution file. The positive flow must re-run with the two separate drill files and the outward cavity.

### Open correction that the resolution does not close

P3 remains. The resolution does not state the `excluded_through_holes` reason rule. Revision 8 and case T49 still make the reason and the diameter necessary, and a missing value must refuse. Keep P3 in the correction list.

**I agree with the resolutions. No concrete conflict remains.**

## 10. Limits

- I examined the frozen files and ran the probes above on copies in `/tmp`. I did not change a product file.
- The integrity findings are inspection findings on the frozen bytes.
- The manifest and the positive flow are measured.
- The review covers the announced manifest only. The set stays frozen until the lead releases it.
