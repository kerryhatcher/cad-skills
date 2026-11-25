# B11 consolidated interface: Claude (revision 8)

Date: 2026-11-15 (UTC). Author: claude-mechanical-dev (model claude-haiku-5-5). Branch: `work/mechanical`. Worktree: `/mnt/storage/projects/cad-skills-worktrees/mechanical`. Base: `75d99da`.

Status: one consolidated revision. Pi gave final explicit agreement. Codex agreement and lead acceptance are pending. The revision includes the lead addendum on thickness, the finished-board envelope, the complete hole set and the Q7 trial (section 9.3). It applies the lead decisions in [b11-decisions-root.md](b11-decisions-root.md), the Pi reviews (I1 to I16 and J1 to J18), the Codex review of revision 3, the bounded export trial in section 9, and the Pi bounded export trial in [b11-export-trial-pi.md](b11-export-trial-pi.md), which confirms the frame and reports four more findings (section 9.2). No product file changed. No image pulled. No `pcb.py` edit. No schema change. No B5 file changed.

## 1. Decisions

- Two modules, both in `pcb-design` (lead decision 1):
  - `skills/pcb-design/scripts/mechanical.py`: records, orchestration, release record, readiness.
  - `skills/pcb-design/scripts/mechanical_fit.py`: CadQuery geometry and its PEP 723 dependency.
- Template: `skills/pcb-design/templates/mech-fit-a/` (lead decision 2).
- Transform: strict `extensions.transform`. `origin_mm` is the target origin. No duplicate target origin and no formula string (decision 3).
- Outline start and anchor are different points. The drill/place origin equals the anchor (decision 4).
- Exporter frame: measured in the bounded trial (section 9). The mapping is frozen before acceptance tests. No best-fit transform (decision 5).
- Connector: six schema fields only. Local insertion vector and envelope are in component evidence. Side alone does not set the insertion direction (decision 6).
- Export settings in one record. Explicit DXF mm units. Same drill/place origin for STEP and DXF (decision 7).
- DXF carries outline and hole circles. Holes are compared independently (decision 8).
- Plated hole `H3` added. Unequal nonplated holes, chamfer, bottom-side part and rotated bottom-side connector test kept (decision 9).
- Release record `mech-release/1`, strict, outside the shared registry. Closed output-role list. Expected release ID read from an explicit input record (decision 10).
- Canonical-hash helper: reuse the accepted helper. Exact file hashes and canonical record hashes stay separate (decision 11).
- Lateral clearance separate from height limits. Owner declarations compared by dimension name (decision 12).
- Tolerances fixed for the first trial: 0.01 mm, 0.1°, 1e-6 mm³. No automatic widening. Proposed changes go to both reviewers and the lead first (decision 13).
- `pcb.py`: narrow `mechanical` dispatch and readiness integration, after agreement (decision 14). Existing interface review behavior is unchanged.
- Input capture, project locks, confined paths, atomic report writes, and a final freshness gate before publication (decision 15, Codex).
- B5 history and the tracked draft interface `ce5e0f3b…` are not changed or reused.

## 2. Owners and files

| Path | Owner | Content |
|---|---|---|
| `skills/pcb-design/scripts/mechanical.py` | Mechanical | Transform validation, evidence and owner checks, input capture, freshness gate, release record, readiness function. |
| `skills/pcb-design/scripts/mechanical_fit.py` | Mechanical | STEP and DXF reading, measurement, comparison, proxy solids, insertion box. PEP 723 header lists `cadquery`. |
| `skills/pcb-design/templates/mech-fit-a/` | Mechanical | Source generator, `board.yaml`, `fixture-source.json`, `board-interface.json` (generated), `component-evidence.json`, export settings record. |
| `skills/pcb-design/references/mechanical-fit.md` | Mechanical | Reference for agents. |
| `tests/test_mechanical.py` | Mechanical | Cases in section 8. Run with `uv`. |
| `pcb.py` `mechanical` dispatch and readiness | Mechanical, after agreement | Narrow wiring (decision 14). |
| Copied contracts, shared schemas, `manifest.schema.json`, CI | Lead | Not changed by this team. |

Local image: `localhost/cad-skills-pcb:b6`, ID `b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f`, KiCad CLI 10.0.5. The release records this ID. No pull.

## 3. Transform

Declared in `extensions.transform` of the fixture interface. The object is strict: finite numbers only, booleans are not numbers, exact field types, no unknown keys. Any violation refuses.

```json
"extensions": {
  "transform": {
    "source_frame": "kicad-board",
    "source_origin_mm": {"x": 103.7, "y": 118.2},
    "source_axes": {"x": "right", "y": "down"},
    "target_axes": {"x": "right", "y": "up"},
    "scale": 1
  }
}
```

Rules:

- `x_target = origin_mm.x + x_source − source_origin_mm.x`
- `y_target = origin_mm.y + source_origin_mm.y − y_source`
- `origin_mm` is `(0, 0)` for this fixture. It is the target origin. It is not the board anchor.
- `scale` must be 1. Unsupported axes refuse.
- Angle datum (J11): 0° is the target `+x` direction. Positive rotation is counterclockwise seen from `+z`. The target angle is derived from the transformed direction vector: `target_deg = atan2(v_target.y, v_target.x)` mod 360. For a file-stored footprint with stored angle `θ` and local vector angle `φ`, the target angle is `θ − φ` (section 9.3). It equals `θ` only when the local vector points along local `+x` (`φ = 0`). Revision 6 stated the opposite sign. The measurement corrects it.
- The outline start `(100, 100)` is declared in `fixture-source.json`. It is a board corner, not the anchor.
- The B5 anchor `(100, 125)` stays in B5 history only.

The trial confirmed this formula for the DXF frame (section 9).

## 4. Fixture `mech-fit-a`

New asymmetric template. No copy of the trial board. No silent edit of a source board.

KiCad values in `fixture-source.json`:

- Outline start `(100, 100)`. Size 60 mm by 36 mm. One 6 mm chamfer at the lower-left corner. Vertices `(100,100)`, `(160,100)`, `(160,136)`, `(106,136)`, `(100,130)`.
- Drill/place origin (auxiliary origin, `aux_axis_origin` in the board `setup` block): `(103.7, 118.2)`, equal to `source_origin_mm`.
- Holes:
  - `H1` at `(110.0, 130.0)`, Ø3.2 mm, not plated.
  - `H2` at `(152.5, 103.5)`, Ø2.5 mm, not plated.
  - `H3` at `(118.0, 106.0)`, Ø3.0 mm, plated.
- Connector `CN1`: right edge, center `(160.0, 112.0)`, side `top`, rotation 0°, `insertion_depth_mm` 4.0.
- Bottom-side part `B1`: center `(130.0, 120.0)`, rotation 90°, side `bottom`.
- Test-only variants (J17): `CN2` (bottom side, nonzero rotation) and a changed `B1` height. They change the board hash and refuse to produce a release.
- Stackup: an explicit stackup is declared (section 9, Q8).

Interface and records:

- `height_limits`: `top_mm` 10.0, `bottom_mm` 4.0.
- `enclosure_clearance_mm` 0.5. `geometry_tolerance_mm` 0.01. `extensions.angle_tolerance_deg` 0.1.
- `board.yaml`: `width_mm` 60, `height_mm` 36, `thickness_mm` (total stack, Q8), `coordinate_system` x right and y up, `release_revision` equal to the interface `board_revision`. `contracts/validate.py` cross-checks the outline and `release_revision` (I5, J3). `board.yaml` holds no owner field. The schema rejects one (O1, validator run by Pi: `schema.unknown_field`, exit 1). T47 covers this.
- Electrical owners: `board-interface.json` `dimension_owners`, which the interface schema requires (O1).
- Stackup (addendum, Q8): `fixture-source.json` declares an independent stackup: `core_mm`, `copper_top_mm`, `copper_bottom_mm`, `mask_top_mm`, `mask_bottom_mm`, and the total `thickness_mm`. The expected `core_mm` is never taken from a tested output or from the B5 trial (O4).
- Finished-board envelope (addendum, Pi item 2): a labeled record `finished_envelope` in `fixture-source.json`, label `FINISHED BOARD ENVELOPE`. Its Z origin is the bottom face of the core, `z = 0`. Its bottom mounting surface is at `z = −(copper_bottom_mm + mask_bottom_mm)`. Its top mounting surface is at `z = core_mm + copper_top_mm + mask_top_mm`. Its outline is the board outline. Its stackup source is the fixture stackup. A substrate-only solid cannot prove clearance for the finished board. The substrate solid serves C05 only. The finished-board envelope serves C08 and C09 (Codex items 1 and 2).
- Component height limits (`top_mm`, `bottom_mm`) are measured from the finished-board mounting surfaces, not from the core.
- `board-interface.json`: the six `connector_frames` fields only (I3, J2). Passes `validate.py` and the existing `interface` operation (J16).
- Connector envelope and insertion vector are in `component-evidence.json` (decision 6, section 5).

## 5. Constraints, evidence and connector geometry

Constraints stay in `height_limits`. Heights are evidence in `mechanical/component-evidence.json`, one record per reference:

`ref`, `side`, `footprint`, `part_revision`, `evidence` (`measured`, `datasheet`, `proxy`, `unconfirmed`), `height_mm`, `limit_mm`, `source_sha256`, `owner`, `model` (name, version, license, source URL and hash, or `none`).

Connector records (decision 6):

- `connector_envelope`: `width_mm`, `height_mm`.
- `insertion_vector_local`: the insertion direction in the part frame, as a unit vector, and `insertion_depth_mm`.
- `pad_frame`: `placed-file` (the only accepted value, section 9.3). Required for every footprint with a `B.Cu` side.
- The target insertion vector is `[[cos θ, sin θ], [sin θ, −cos θ]] · local`, the measured matrix rule of section 9.3. The same rule applies to top and bottom sides. The side sets only the Z range, not a second mirror. Side alone does not define the direction.

Status rules:

- `measured` or `datasheet`: height compared with the limit. Over the limit fails.
- `proxy`: envelope checked only. Result `conservative_envelope_only`. No detailed-fit claim.
- `unconfirmed`: result `unconfirmed`. Never `pass`.

Proxy solids come from `mechanical_fit.py`. Each carries `PROXY` in its STEP product name. They never enter the KiCad export. The fixture uses no third-party model (`models: []`).

The enclosure box is generated. Its parameters are in `fixture-source.json`. That file is hashed, not the generated solid (I16, J14).

## 6. Exports, input capture and origin check

Outputs under `out/mechanical/`:

- `board.step`: `kicad-cli pcb export step --drill-origin --board-only --no-extra-pad-thickness` (board body). The exact command, with its switch set, is recorded in the settings record. `--include-soldermask`, `--include-pads` and `--include-silkscreen` are off (Codex item 6).
- `outline.dxf`: `kicad-cli pcb export dxf --use-drill-origin --output-units mm --mode-single --layers Edge.Cuts --drill-shape-opt 2`. The DXF carries the outline and the through-hole circles. `--drill-shape-opt 0` removes the holes and is refused (J5, decision 8, Pi trial item 3).
- `drill/`: `kicad-cli pcb export drill --drill-origin plot --excellon-units mm`. Roles `drill_pth` and `drill_npth`. C04 reads the plated flag from the `AperFunction` comment of each aperture (Pi trial item 5).
- `board.step` is the board-only export (`--board-only`). The STEP also holds global points at `(0, 0, 0)` and `(0, 0, 1.51)`. The measurement selects board-body geometry by its X and Y range and does not use the global bounding box (Pi trial item 1).
- `fit-assembly.step`: board plus proxies from `mechanical_fit.py`, labeled proxy geometry.
- `mechanical-report.json`: each comparison with measured value, expected value, tolerance and status, plus the measured report-only frames (`step_frame`, `dxf_frame`).

Export settings record (decision 7, I6, J4). The settings hash covers every switch and the variant behavior:

- STEP: `--drill-origin`; `--no-dnp`; `--subst-models`; `--min-distance 0.01mm`; `--no-extra-pad-thickness` (required for the body check, Q8); `--include-soldermask` off; `--include-silkscreen` off; `--include-pads` off; component set stated per run.
- DXF: `--use-drill-origin`; `--output-units mm` (the default is inch); `--mode-single`; `--layers Edge.Cuts`; `--use-contours` off, stated.
- Variant: the default variant only (`--variant` not used).

Input capture (Codex, decision 15): every input is read once into bytes. The report binds those bytes by SHA-256. A final freshness gate re-hashes the captured inputs before publication. A mismatch refuses publication and names the input. Project locks, confined paths and atomic report writes reuse the accepted helpers.

Origin and axis check (decision 4, C4, J12), before any hole comparison:

1. Read the auxiliary drill/place origin from the board file (`aux_axis_origin`). Do not derive it from holes. The accepted B5 board has no `aux_axis_origin`, so its origin is `(0, 0)`. The fixture must set `aux_axis_origin` to the anchor (Pi trial item 6).
2. Require it to equal `source_origin_mm` within 0.01 mm.
3. Require the STEP `--drill-origin` and DXF `--use-drill-origin` outputs to use that origin. Check each file from its outline vertices.
4. Measure the effective axes and the Z datum from the board body outline.
5. On mismatch: refuse with exit 1, name the file and the measured origin. Do not edit the source board. Do not infer a new anchor.

C12 uses the auxiliary origin and the outline only. C02 and C02d are the only hole-position comparisons.

## 7. Comparisons

Status separation (Codex item 5): a geometry pass does not make a fit pass. C01 to C07, C09 (lateral) and C12 give `geometry_status`. C08, C10 and C11 give `fit_status`. An `unconfirmed` evidence item makes `fit_status` `unconfirmed` and leaves `geometry_status` unchanged.

Geometry comparison (Codex): sets are compared without vertex-order dependence. Each expected point must match one measured point within tolerance, and the counts must agree. No best-fit alignment and no rotation search.

| ID | Measured from | Expected from | Tolerance | Fails when |
|---|---|---|---|---|
| C01 | DXF `Edge.Cuts` outline vertices | Outline, transformed | 0.01 mm | Set mismatch or count mismatch |
| C02 | STEP cylinder axes | Hole centers, transformed | 0.01 mm | Any center missing or extra |
| C02d | DXF hole circles | Hole centers, transformed | 0.01 mm | Any center missing or extra. Count must be 3 |
| C03 | STEP cylinder radius and DXF circle radius | Hole diameters | 0.01 mm | Any diameter differs |
| C04 | Excellon drill files, `AperFunction` plated flag per aperture | Interface hole `plated` flags | exact | Any flag differs |
| C05 | CadQuery imports the STEP substrate solid (one valid solid, selected by the board X and Y range; global points excluded) | Fixture stackup `core_mm` and datum `z = 0` at the core bottom | 0.01 mm | The solid count is not one, or its Z span or datum differs from `core_mm` |
| C05s | Stackup record | Declared total `thickness_mm` (1.6) | exact sum | `core_mm` + `copper_top_mm` + `copper_bottom_mm` + `mask_top_mm` + `mask_bottom_mm` ≠ `thickness_mm` (O6) |
| C06 | Connector proxy placement | Frame record and rotation rule | 0.01 mm, 0.1° | Position or rotation differs |
| C07 | Solids that intersect the insertion box (membership), then boolean volume | None | 1e-6 mm³ | Any other solid in the box |
| C08 | Proxy and component Z extents | `top_mm` above the top mounting surface, `bottom_mm` below the bottom mounting surface, both from `finished_envelope` | 0.01 mm | Over a confirmed limit (vertical clearance) |
| C09 | Proxy extents | `finished_envelope` outline offset by clearance, chamfer included | 0.01 mm | Lateral clearance violated (lateral only) |
| C10 | Evidence records | Evidence rules | exact | Any `unconfirmed` item gives `unconfirmed` |
| C11 | Owner declarations | Owner rule | exact | Two records name different owners for one dimension |
| C12 | Origin and axis check | `source_origin_mm` | 0.01 mm | Origin or axes differ |

Closed hole set (Pi trial item 4): every through hole in the STEP, DXF and Excellon outputs must be either in the interface `holes` list or in `extensions.excluded_through_holes` (renamed from `via_drills`, O2). Each excluded hole gives its position, diameter and reason. `mechanical.py` examines the list. An unlisted hole refuses.

Complete supported hole set (addendum): the comparison uses the complete set of through holes from the STEP cylinders, the DXF circles and the Excellon hits. Each set must equal the interface `holes` list plus `excluded_through_holes`. Only circular drills are supported. A slot, an oval or any other drill class refuses and names the object. Do not ignore an extra footprint hole or a drill class. The B5 two-hole list does not define the board inventory.

Proxy limit (addendum, Pi): `CN1` is a frame record with no footprint. Its proxy envelope is conservative. It proves an envelope check only. It does not prove detailed connector fit. The report must state this limit in each connector result.

Fixture through-hole set (O3): `CN1` is a frame record with no footprint. The fixture has exactly `H1`, `H2` and `H3`. `excluded_through_holes` is empty. C02d count 3 is correct. A later connector footprint with plated pin holes must first add those holes to the interface `holes` list with `plated: true`. The count is then taken from the full list. The accepted B5 board has four through holes (two at 3.2 mm, two at 1.0 mm), but its interface lists only two. B5 history is not changed. The B11 fixture lists every through hole. The fixture has no via drill.

Insertion box: a box on the connector frame. Its footprint is the connector width. It extends `insertion_depth_mm` along the target insertion vector (section 5). Its Z range is the connector height. C07 tests other solids only. It excludes the connector's own proxy (Codex item 4). Each other solid that intersects the box fails and is named by its reference.

Owner records (J13, O1): `board-interface.json` `dimension_owners` (electrical declaration, required by the schema) and `fixture-source.json` `dimension_owners` (mechanical). A conflict arises when the two name different owners for one dimension. The release refuses and names the dimension and the two records (C11, T19, T32).

Lateral and vertical split (J18): C09 is lateral only. C08 is vertical only.

## 8. Release record, identity and acceptance

Release record `out/release/mech-release.json`, record `mech-release/1`, field `version` `1`, strict. Validated by `mechanical.py`. Outside the shared registry (decision 10).

Fields:

- `release_id`: read from the explicit input record `fixture-source.json` (J7, decision 10). Not derived from a hash.
- `electrical_release_id`: read from the prior electrical release record named in the input record (J7).
- `fixture_id`, `board_revision`, `board_sha256`
- `electrical_inputs`: each input path and its exact SHA-256
- `interface_sha256`, `component_evidence_sha256`, `fixture_source_sha256` (the hash of `fixture-source.json`, which holds the enclosure parameters and the finished-board stackup source; O5), `export_settings_sha256`
- `geometry_status` (C01 to C07, C09 lateral, C12) and `fit_status` (C08, C10, C11, and the proxy limit). The two statuses are separate (Codex item 5).
- `toolchain_image_id`
- `outputs`: path, role and exact SHA-256 and byte count. Closed role list: `step_board`, `step_fit`, `dxf_outline`, `drill_pth`, `drill_npth`, `report`.
- `comparisons`: C01 to C12
- `status`, `first_mismatch`

Identity rules:

- Canonical record hashes use the accepted canonical-hash helper (decision 11). Exact file hashes use SHA-256 of the file bytes. The two are never mixed.
- Each output keeps its exact SHA-256. The release binds exact STEP and DXF bytes.
- Regenerated files pass C01 to C05 and C02d when geometry agrees, even with new bytes. The new exact hash is recorded.
- Tolerances are fixed for the first trial (decision 13). A failed tolerance is not widened automatically. A proposed change goes to both reviewers and the lead before another acceptance run.
- STEP and DXF are gitignored. Generation source and settings are committed. Generated files are not force-added.

Stale refusal order. The first mismatch stops publication and names the input, expected hash and measured hash: `electrical_release_id`, `release_id`, `board_sha256`, `interface_sha256`, `component_evidence_sha256`, `fixture_source_sha256`, `export_settings_sha256`, `toolchain_image_id`, `fixture_id`. Exit 1.

Readiness (decision 14): `mechanical.py` exposes one readiness function. `pcb.py` calls it through the narrow `mechanical` dispatch. The existing interface review (section 13 of `pcb.py`) is unchanged.

Acceptance cases:

| ID | Case | Necessary result |
|---|---|---|
| T1 | Fixture with declared transform | C01 to C12 pass within tolerance |
| T2 | Mirrored X | Fails a named comparison (C01, C02 or C02d) |
| T3 | Y-flipped board, no flip in transform | Fails the transform check |
| T4 | Wrong `source_origin_mm` | Fails C12 |
| T5 | Untransformed fixture | Fails |
| T6 | `scale` not 1, unsupported axes, or a boolean given as a number | Refuses the transform |
| T7 | STEP and DXF drill origins differ | Refuses (C12), names the file and the measured origin |
| T8 | Fixture without `B1` | Fails and names the missing part |
| T9 | Fixture without `CN1` | Fails and names the missing frame |
| T10 | `CN1` rotated 180° | C06 fails |
| T11 | Another solid in the `CN1` insertion box | C07 fails |
| T12 | Bottom-side `CN2`, nonzero rotation, clear space (test-only) | C06 passes with the rule of section 3. Refuses as a release |
| T13 | Bottom-side `CN2`, obstructed insertion box (test-only) | C06 and C07 fail and name the obstructing solid |
| T14 | `B1` height 5.0 mm, limit 4.0 mm, `measured` | C08 fails |
| T15 | Same case, `unconfirmed` evidence | Result `unconfirmed`. No fit claim |
| T16 | `proxy` envelope within limits | Passes with `conservative_envelope_only` |
| T17 | Regenerated STEP and DXF, new bytes, same geometry | Passes C01 to C05 and C02d. New hashes bound |
| T18 | Board-only `board.step` | Board geometry only. No clearance claim |
| T19 | Owner conflict on one dimension | C11 refuses and names the conflict |
| T20 | Missing or altered `extensions.transform` | Fails closed and states the action |
| T21 | Changed electrical release ID or electrical input hash | Stale. Exit 1. Names the input |
| T22 | Changed `board_sha256`, interface, evidence, enclosure or settings hash | Stale. Names the first mismatch |
| T23 | Changed component revision or supplier profile | Stale. Names the first mismatch |
| T24 | Release record `release_id` differs from `fixture-source.json` | Stale. Names `release_id` |
| T25 | Missing image | Exit 2. No pull |
| T26 | B5 files and records | Hashes unchanged |
| T27 | Connector item with a seventh field | Interface validation fails |
| T28 | `board.yaml` dimensions differ from the outline | Cross-check fails with a named finding |
| T29 | Export without the agreed switch set | Refuses, or the settings hash differs |
| T30 | `H3` plated | C04 passes with the exact plated flag |
| T31 | Rotated bottom-side connector with obstructed box | C06 and C07 fail |
| T32 | Dimension with two owners | Release refuses with the named conflict |
| T33 | Repeated export, same geometry, new bytes | C01 to C05 and C02d pass. New exact hash recorded |
| T34 | Missing or unknown `extensions.transform` | `mechanical.py` refuses and states the action |
| T35 | Interface against `validate.py` and the existing `interface` operation | Both pass. Only `mechanical.py` checks `extensions.transform` |
| T36 | Export settings with one switch removed | Settings hash differs. Release refuses |
| T37 | Test-only variant used for a release | Refuses |
| T38 | Expected `release_id` and `electrical_release_id` | Each read from its named source record |
| T39 | Vertex order of DXF outline reversed | C01 passes (no order dependence) |
| T40 | Input file changed after capture | Freshness gate refuses before publication. Names the input |
| T41 | Two circles at one hole center in DXF | C02d fails the count check |
| T42 | An unlisted through hole in STEP, DXF or drill output | Closed-hole-set check refuses and names the hole |
| T43 | STEP global points present, board body selected by X and Y range | C05 uses the body only, and the result is unchanged by the global points |
| T44 | Excellon aperture with a `Plated` comment on a hole listed as not plated | C04 fails and names the hole |
| T45 | `--drill-shape-opt 0` in the DXF settings | Refuses. The holes would be missing from the DXF |
| T46 | A text span of the STEP points (including control points outside the substrate solid) is used as a thickness | Refused. Thickness comes from the imported substrate solid (C05) and the layer sum (C05s), never from the text span (lead addendum) |
| T47 | `board.yaml` with a `dimension_owners` field | `contracts/validate.py` fails with `schema.unknown_field`, exit 1 (O1) |
| T48 | Fixture with `CN1` frame-only and no footprint | Exactly three through holes. C02d count is 3 (O3) |
| T49 | A non-empty `excluded_through_holes` list | `mechanical.py` examines each entry. An entry without a reason refuses (O2) |
| T50 | `core_mm` taken from the B5 trial instead of the fixture stackup | Refuses until the fixture stackup trial confirms the value (O4) |
| T51 | `CN1` proxy overlaps its own insertion box | No collision finding. C07 excludes the connector's own proxy (Codex item 4) |
| T52 | Geometry passes, but C10 evidence is `unconfirmed` | Result has `geometry_status` `pass` and `fit_status` `unconfirmed`. The report makes no detailed-fit claim (Codex item 5) |
| T53 | `board.step` exported with a different switch set than the settings record | The settings hash differs. Release refuses (Codex item 6) |
| T54 | `B.Cu` connector declared `pad_frame` `library-unflipped` | Refuses. No frozen rule for that frame (lead Q7) |
| T55 | `B.Cu` footprint with no `pad_frame` declaration | Refuses. The file does not show edit history, so the declaration is required |
| T56 | Asymmetric local vectors at +30° on top and bottom (table in section 9.3) | Target vectors and target angles match the table within tolerance. Mirror or sign errors fail a named comparison |

Exit codes follow `skills/pcb-design/references/exit-codes.md`: 0 pass, 1 failed comparison or stale input, 2 invocation or missing prerequisite, 3 tool failure.

## 9. Bounded export trial (scratchpad, not product)

Scope: one minimal board with the planned holes, outline and plated hole, generated outside the repository. Run in `localhost/cad-skills-pcb:b6` with `--pull=never --network none`. Measured with a standard-library parser. Trial files: `/tmp/claude-1000/-mnt-storage-projects-cad-skills-worktrees-mechanical/3cdd52be-0def-47cb-b9ba-8d59fff2a7a5/scratchpad/b11-trial/`.

Confirmed flags (from `kicad-cli pcb export step --help` and `pcb export dxf --help`): `--drill-origin`, `--no-extra-pad-thickness`, `--min-distance`, `--include-soldermask`, `--include-silkscreen`, `--include-pads`, `--use-drill-origin`, `--output-units`, `--mode-single`, `--layers`, `--use-contours`. The DXF command has no `--force` option. The DXF default unit is `in`.

Measured frame (DXF, `--use-drill-origin`, mm):

- Outline vertices: `(100,100)` to `(-3.7, 18.2)`; `(160,100)` to `(56.3, 18.2)`; `(160,136)` to `(56.3, -17.8)`; `(106,136)` to `(2.3, -17.8)`; `(100,130)` to `(-3.7, -11.8)`.
- Frame formula: `x_dxf = x_kicad − 103.7` and `y_dxf = 118.2 − y_kicad`. This equals the section 3 transform with `origin_mm = (0, 0)` and anchor `(103.7, 118.2)`. The frame is frozen from this result.
- Holes in the DXF: `(6.3, −11.8)` r 1.6; `(48.8, 14.7)` r 1.25; `(14.3, 12.2)` r 1.5. These match `H1`, `H2` and `H3`.
- An Edge.Cuts-only DXF also contains the hole circles. An extra layer (`F.SilkS`) duplicated them. So the count check (C02d, T41) is needed.

Measured frame (STEP, `--drill-origin`):

- Hole cylinder axes: `(6.3, −11.8)`, `(14.3, 12.2)`, `(48.8, 14.7)`. These match the DXF in x and y.
- Planar faces of the body: bottom at `z = 0.0`, top at `z = 1.51`. The body thickness is 1.51 mm.
- Hole cylinder ends reach `z = −0.046` with default settings and `z = −0.036` with `--no-extra-pad-thickness`.
- `--no-board-body` failed with "Error writing STEP file" in this trial. It is not used.

Resolved (Q8, lead addendum). The imported STEP body has one valid substrate solid, from Z 0 to 1.51 mm, in both files. A text span of 1.556 mm includes control points outside that solid. It does not define the thickness, and it is not used. C05 compares the imported solid with the independent `fixture-source.json` stackup `core_mm`. C05s compares the declared layer sum with the total `thickness_mm`. The finished-board envelope (section 4) serves clearance. No tolerance is widened (decision 13).

### 9.2 Pi bounded export trial (corroborating)

Source: [b11-export-trial-pi.md](b11-export-trial-pi.md). It used the accepted board and the template in the local image without a pull. It confirms the frame (X unchanged relative to the origin, Y negated) and the Z findings of 9.1. It adds four findings, folded above:

1. Global STEP points at `(0, 0, 0)` and `(0, 0, 1.51)` must be excluded (section 6).
2. The substrate span is 1.51 mm for both boards. The soldermask case gives 1.610 mm. The template with pads gives 1.596 mm. The raw span must not be compared with `thickness_mm` (C05, C05s).
3. DXF holes need `--drill-shape-opt` 1 or 2. Option 0 removes them (section 6, T45).
4. The accepted board has four through holes, but its interface lists two. The B11 fixture lists all holes and uses the closed hole set (section 7).
5. The Excellon plated flag is in the `AperFunction` comment (C04).
6. The fixture auxiliary origin must equal the anchor (section 6).

### 9.3 Q7 bounded trial: bottom and top footprint mapping

Scratchpad trial in `localhost/cad-skills-pcb:b6` (no pull). Two footprints: `TOP1` on `F.Cu` at `(120, 110)` rotation 30°, and `BOT1` on `B.Cu` at `(140, 120)` rotation 30°. Each has one pad at local `(2.0, 0.5)`. The Gerber pad flashes were read and converted to KiCad coordinates (Gerber Y is negated).

Measured pad positions:

- `TOP1` pad: `(121.982, 109.433)`. Offset from the origin: `(1.982, −0.567)`.
- `BOT1` pad: `(141.982, 119.433)`. Offset from the origin: `(1.982, −0.567)`.

Measured rule for file-stored footprints, both sides: `offset = [[cos θ, sin θ], [−sin θ, cos θ]] · local`. The check gives `(2·0.866 + 0.5·0.5, −2·0.5 + 0.5·0.866) = (1.982, −0.567)`. This matches both sides. The file-stored pads of a `B.Cu` footprint are not mirrored again.

Consequences for the insertion vector (decision 6, Q7):

- The board-frame insertion vector is the rule above applied to the local insertion vector. The side does not add a second mirror.
- The contract vector is `(x, −y)` of the board vector. The target vector is `R(θ) · F · local`, where `F = diag(1, −1)` and `R(θ)` is the standard rotation by `θ` (section 9.3). The target angle is `atan2` of that vector, which equals `θ − φ` (Codex Q7 review). It is not copied from `θ` alone.
- Limit: this trial covers footprints stored on `B.Cu` in the file with the `placed-file` frame. A footprint flipped in the KiCad editor is not detectable from the file, and the file does not record edit history. The only enforced condition is the declared `pad_frame` (section 9.3, limit below). No refusal of editor-flipped footprints is claimed.

Insertion marker trial (Codex item 3). Two frames with a marker pad at the insertion end, local `(4.0, 0.0)`, so the local insertion vector is `(1, 0)` with depth 4.0 mm:

- `CN1` on `F.Cu` at `(160.0, 112.0)`, rotation 0°. Marker measured at `(164.0, 112.0)`. Board vector `(4.0, 0.0)`. Contract vector `(4.0, 0.0)`. Rule: angle 0°.
- `CN2` on `B.Cu` at `(140.0, 120.0)`, rotation 30°. Marker measured at `(143.464, 118.0)`. Board vector `(3.464, −2.0)`. Contract vector `(3.464, 2.0)`, angle 30°. The predicted rule gives the same point.

Frame definitions (lead Q7 request):

- Local frame: the footprint frame as stored in the board file. Its `x` is right and its `y` is down, the KiCad convention. Its angle datum is `local (1, 0)` at 0°.
- Board frame: the KiCad board frame, `y` down. Board vector `= [[cos θ, sin θ], [−sin θ, cos θ]] · local`. The `θ` is the stored footprint angle.
- Contract frame: `x_target = x_board` and `y_target = −y_board`, as section 3. Target vector `= (x, −y)` of the board vector.
- Target vector formula: `target = R(θ) · F · local`, with `F = diag(1, −1)` and `R(θ) = [[cos θ, −sin θ], [sin θ, cos θ]]`. Combined, the target matrix is `[[cos θ, sin θ], [sin θ, −cos θ]]`. Check: `board = F · target = [[cos θ, sin θ], [−sin θ, cos θ]] · local`, the measured rule above.
- Target angle: `atan2` of the target vector, which equals `θ − φ`, where `φ = atan2(local.y, local.x)`. It equals `θ` only for `φ = 0`. The earlier claim that it always equals `θ` was wrong. Codex Q7 review corrected it.

Explicit vectors (asymmetric local vectors at +30° on both sides, test set T56):

| Part | Side | Source θ | Local insertion vector | Depth | Board vector | Target vector | Target angle |
|---|---|---|---|---|---|---|---|
| `CN1` | top | 0° | `(1, 0)` | 4.0 | `(4.000, 0.000)` | `(4.000, 0.000)` | 0° |
| `CN2` | bottom | 30° | `(1, 0)` | 4.0 | `(3.464, −2.000)` | `(3.464, 2.000)` | 30° |
| top footprint (asymmetric pad) | top | 30° | `(2.0, 0.5)`, φ = 14.04° | — | `(1.982, −0.567)` | `(1.982, 0.567)` | 15.96° = θ − φ (pad position measured) |
| bottom footprint (asymmetric pad) | bottom | 30° | `(2.0, 0.5)`, φ = 14.04° | — | `(1.982, −0.567)` | `(1.982, 0.567)` | 15.96° = θ − φ (pad position measured) |

The source angle equals the target angle only for a local vector along local `+x`. The asymmetric rows show the general case. The angle of the target vector gives the target angle, whatever the local vector.

The side does not change the xy rule for file-stored footprints. The Z range comes from the connector height and the side (section 7).

Frame condition (lead request, distinguishing file-stored from library-unflipped):

- `pad_frame` is a required field in each connector and footprint evidence record. Its only accepted value for this rule is `placed-file`: the pads are stored in the placed board frame, as this trial measured.
- A value `library-unflipped` (a canonical library frame that needs a mirror for a `B.Cu` placement) has no frozen rule. It refuses until measured.
- A `B.Cu` footprint without a declared `pad_frame` refuses.
- Limit: a footprint flipped in the KiCad editor and stored in the file is indistinguishable from a footprint authored on `B.Cu` in the file. The file does not record edit history. This interface therefore does not claim to detect GUI flips. It accepts only the declared `placed-file` frame, and a footprint declared that way must be reviewed by the author.

Gate: the rule is frozen by this trial, for `placed-file` footprints only. Acceptance tests use it. A change needs a new trial.

## 10. Resolved, open and reviewer requests

Resolved by the lead: decisions 1 to 15 in `b11-decisions-root.md`, C1, C3, C4, C10.

Resolved from Pi reviews: I1 to I16, J1 to J18, Q1 to Q4.

Resolved from Codex review of revision 3: input capture and freshness, canonical-hash helper reuse, output roles, readiness wiring, test-only variant refusal, geometry comparison without vertex-order dependence or best-fit alignment, connector collision membership.

Resolved in this revision (all three are closed; no open question remains in section 10):

- Q6. Export switch set. Confirmed by help output (section 9). The full set is recorded in the settings hash.
- Q7. Resolved by the bounded trial in section 9.3. The insertion vector rule is frozen for file-stored footprints, with measured `CN1` and `CN2` vectors. Footprints flipped in the editor are not detectable from the file. They are accepted only through the declared `pad_frame` (section 9.3).
- Q8. Resolved by the lead addendum (section 9.1). The independent fixture stackup is the authority (O4). The imported substrate solid is compared with `core_mm`.

Review state: Pi gave final explicit agreement to revision 6 and concurred with the seven Codex items (`b11-interface-review-claude-pi.md` section 3a). Codex reviewed the revision 6 snapshot `ffb091ed…` and agreed to the design after seven corrections (`b11-interface-review-claude-codex.md`). Those corrections are folded into this revision. Pi confirmed the Q7 frame text at `295239507c…` (section 3c). Codex's final agreement on the current hash is the only review still open. The lead accepts after Codex agrees. No product implementation before that.

## 11. Scope limits

- No supplier contact, upload or order.
- No detailed component fit from a proxy.
- No change to accepted B1 to B6 history, the tracked draft interface, shared schemas or copied contracts.
- No product implementation before both reviews agree and the lead accepts.
