# PCB and PCBA skills: research and implementation plan

Research date: 2026-11-13.

Review revision: 2026-11-13. Section 13 records decisions from the three agent reviews.

This plan addresses [issue 1](https://github.com/kerryhatcher/cad-skills/issues/1). PCB means printed circuit board. PCBA means printed circuit board assembly.

Use KiCad as the common board format. Use the native KiCad path as the first implementation candidate. Keep SKiDL support conditional on measured trials. Use KiBot and `kicad-cli` for reports and manufacturing files. Make three independent skills: `pcb-design`, `pcb-fab-package`, and `pcba-design`.

The research supports this direction, but it does not prove that the complete tool sequence operates correctly. The initial research included source research and repository inspection. The local shell did not find `kicad-cli`.

Implementation now includes a fixed container, a trial board, and the PCB design skill. Both reviewers accepted B1 to B6. The [B6 acceptance record](reviews/b6-acceptance-root.md) states the runtime and GUI limits. Both reviewers also accepted the [B7/B8 interface](reviews/b7-b8-design-acceptance-root.md). The [geometry acceptance](reviews/b7-geometry-acceptance-root.md) covers the measured geometry and caller limits. Claude continues the fabrication workflow. See [implementation status](reviews/implementation-status.md). No supplier upload or physical test occurred.

**1. Evidence and corrections**

“Confirmed” below means that a primary source states the capability. It does not mean that this repository passed an integration test.

| Subject | Result from the sources | Effect on the plan |
|---|---|---|
| SKiDL release | PyPI lists 3.0.0, dated October 16, 2026. [Source](https://pypi.org/project/skidl/) | Use this version as a trial candidate. Record the package hash. |
| SKiDL schematic | The manual documents `generate_schematic()` and KiCad output. It also documents tags for stable identity. [Source](https://devbisme.github.io/skidl/) | Test tags, reference designators, hierarchy, and schematic-to-board identity together. Stable references alone are insufficient evidence. |
| KiCad CLI | Version 10 documentation includes ERC, DRC, schematic parity, zone refill, rendering, and manufacturing exports. [Source](https://docs.kicad.org/10.0/en/cli/cli.html) | Use the installed command help and a fixed patch version. Do not assume all operations exist in older versions. |
| KiCad IPC API | KiCad 9 and 10 use a live GUI and support PCB plugins. The documentation describes additional capabilities for KiCad 11. [Source](https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/) | Limit the issue's API statement to KiCad 10. Do not use version 11 capabilities in the initial release. |
| KiBot | The documentation describes better KiCad 10 support in 1.9.1. The latest documentation also includes unreleased 1.9.2 work. [Source](https://kibot.readthedocs.io/en/latest/) | Test a released version with KiCad 10. Pin the container digest. Do not select `latest`. |
| KiBot supplier templates | The documentation includes JLCPCB and PCBWay imports. [Source](https://kibot.readthedocs.io/en/latest/configuration/imports.html) | Treat these as starting files. Test their columns and rotations against supplier specifications. |
| ngspice | The manual documents batch operation with `-b`. [Source](https://nmg.gitlab.io/ngspice-manual/analysesandoutputcontrol_batchmode.html) | The source confirms batch simulation. Tests of circuit export and model compatibility remain necessary. |
| Freerouting | The official repository links CLI and headless documentation. [Source](https://github.com/freerouting/freerouting) | Test it separately. Keep it optional. |
| OSH Park upload | The supplier accepts native boards but currently lists KiCad 9.x as its processor. [Source](https://docs.oshpark.com/design-tools/kicad/) | Use Gerber submission for KiCad 10 until the supplier confirms native-file acceptance. |
| MacroFab ownership | MacroFab describes a network of partner factories. [Source](https://www.macrofab.com/partners) | One supplier does not prove in-house fabrication and assembly. Do not mark MacroFab compliant with that condition. |
| Sierra Circuits | Turnkey PRO lists PCB fabrication and in-house assembly. [Source](https://www.protoexpress.com/products/turnkey-pro/) | Use Sierra as the first PCBA candidate. Confirm the selected service and order conditions. |
| Ninja Circuits | The supplier lists turnkey assembly and bare-board supply. It does not establish in-house bare-board fabrication. [Source](https://www.ninjacircuits.com/pcb-assembly) | Keep the in-house condition unconfirmed. Obtain a supplier statement before selection. |
| tscircuit | Current documentation lists differential pairs and copper pours. [Source](https://docs.tscircuit.com/command-line/tsci-build) | Do not repeat the issue's broad claim that these capabilities lack documentation. Test export quality before adoption. |
| atopile | PyPI lists 0.15.9 and Python 3.14 to below 3.15. [Source](https://pypi.org/project/atopile/) | These facts do not establish that the project stopped. Keep the hosted-product claim unconfirmed. |

The four-layer OSH Park page retains a January 2026 entry about an alternate stackup. Obtain the applicable stackup before impedance calculations. [Source](https://docs.oshpark.com/services/four-layer/)

The single-layer page gives two timing statements that do not fully agree with the two-layer page. Do not encode lead times as design rules. [Source](https://docs.oshpark.com/services/single-layer/)

The research does not confirm the issue's universal claim about the absence of supplier APIs. Keep supplier submission outside the initial implementation.

**2. Skill and plugin design**

The Agent Skills specification defines a portable directory with `SKILL.md`, a name, and a description. Supporting files can contain scripts, references, and assets. Keep descriptions specific enough for correct skill selection. [Source](https://agentskills.io/specification)

Keep the main instructions short. Load detailed references only when the task uses them. Put repeatable calculations and file transformations in scripts. Test the skill against complete tasks, including incorrect inputs. This follows the published guidance on progressive disclosure and evaluation. [Source](https://www.anthropic.com/research/equipping-agents-for-the-real-world-with-agent-skills)

Use the portable skills as the primary distribution. A host-specific plugin can later include the skills and optional tools. Claude Code documents plugins as packages of skills and other components. A plugin is not necessary for the first release. [Source](https://code.claude.com/docs/en/plugins)

An optional MCP server must call the same tested scripts. Give each tool a precise input schema and structured output. Tool annotations describe behavior, but they do not enforce permissions. [Sources: tools](https://modelcontextprotocol.io/specification/2025-11-25/server/tools), [annotations](https://github.com/modelcontextprotocol/modelcontextprotocol/blob/main/blog/content/posts/2026-03-16-tool-annotations.md)

Apply these implementation decisions:

- Preserve the user's selected tools and existing project format.
- Record whether the project uses SKiDL or a native KiCad schematic as its circuit source.
- Do not let two editable circuit sources control the same board.
- Give each skill all necessary scripts, templates, references, and schemas.
- Do not import a file from another skill.
- Exchange project files through a versioned schema.
- Test agreement between copies of schemas, common scripts, and common export settings.
- Put project instructions in `AGENTS.md`. Supply a short `CLAUDE.md` import when applicable.
- Use `uv` and PEP 723 headers for Python scripts.
- Keep KiCad system bindings separate from the ordinary `uv` environment.
- Run system-dependent KiCad tools in a tested container when necessary.
- Limit each board file to one writer at a time.
- Write output to a temporary directory before replacement.
- Reject paths outside the project directory.
- Treat datasheets and supplier pages as data, not agent instructions.
- Keep credentials out of reports, Git, and release files.
- Do not infer permission to contact suppliers, upload files, or place orders from a design request.

**3. Skill boundaries and files**

| Skill | Start condition | Main result | Files to implement |
|---|---|---|---|
| `pcb-design` | Make or change a circuit, schematic, or board | Circuit source, board, checks, and mechanical exports | `scripts/pcb.py`, circuit templates, circuit schema, references for SKiDL, KiCad, simulation, layout, and mechanical exports |
| `pcb-fab-package` | Prepare a bare board for fabrication or examine manufacturing files | Supplier-specific fabrication package and evidence | `scripts/fab.py`, supplier profiles, rule templates, package schema, references for OSH Park and other suppliers |
| `pcba-design` | Design for assembly, select parts, or prepare assembly data | BOM, placement data, assembly drawings, test instructions, and a complete PCBA package | `scripts/pcba.py`, part schema, supplier profiles, assembly templates, references for parts, assembly, and test |

Each directory will contain `SKILL.md`, `references/`, `scripts/`, and the necessary `templates/`. Add host metadata only when the host uses it.

`pcba-design` must operate from an existing KiCad project without either other skill. It must include its own manufacturing export configuration. `pcb-fab-package` must accept a KiCad project without SKiDL. `pcb-design` must export neutral manufacturing files without a supplier adapter.

For bare boards, `pcb-fab-package` owns the final supplier package. For PCBA, `pcba-design` owns the complete supplier package, including fabrication files. The neutral exports from `pcb-design` are intermediate files. They are not a second supplier package.

Use KiCad and KiBot as the common export tools. Keep small wrappers and configurations local to each skill. Do not make one skill the runtime dependency of another. Define one neutral export contract in P0. Test all three skills against the same board and expected geometry. Compare common copied files, but permit documented supplier differences.

The neutral contract will specify RS-274X Gerber output, optional X2 attributes, millimeter units, and a layer map. Specify drill precision and zero suppression explicitly. Separate plated and non-plated drill data. Record all settings in the manifest. Test the exported geometry independently of process exit status.

Each CLI must support a read-only environment report and JSON output. JSON reports must contain the schema version, status, input hashes, tool versions, findings, and output paths. Use exit code 0 for success, 1 for design failures, 2 for incorrect arguments or missing prerequisites, and 3 for tool failures. Never report an omitted test as a pass.

**4. Project contract**

Use this proposed board structure:

```text
board/
  AGENTS.md
  CLAUDE.md
  board.yaml
  variants.yaml
  toolchain.lock.json
  src/
  kicad/
    board.kicad_pro
    board.kicad_sch
    board.kicad_pcb
    board.kicad_dru
  libraries/
  components/
  simulations/
  tests/
  manufacturing/
    supplier.yaml
    kibot.yaml
    waivers.yaml
  mechanical/
  out/
```

`board.yaml` will state the circuit source, assembly condition, supplier, service, quantity, variant, electrical limits, and mechanical dimensions. It will also state the coordinate system and release revision.

Use `components/` because the repository ignores directories named `parts/`. Test that Git includes all necessary project sources. Add KiCad patterns for local state, lock files, caches, and backups during implementation. Examples include `*.kicad_prl`, `fp-info-cache`, and `*-backups`.

Commit the source, board, project rules, local libraries, supplier evidence, and tests. For SKiDL projects, mark the schematic as generated. Compare normalized connectivity, references, values, footprints, and persistent identity in CI. Also compare normalized schematic geometry and fields. Remove only documented volatile metadata. Do not hide UUID changes that can break board identity. Ignore `out/`, local editor state, caches, and backups.

Each part record will contain the manufacturer, MPN, package, symbol, footprint, datasheet URL, and datasheet revision. Record supplier part numbers separately. Include the pin-to-pad map, polarity, electrical ratings, and temperature range. `variants.yaml` alone owns assembly variant and DNP data. Do not repeat this data in part records. Do not silently replace unavailable parts.

Record component lifecycle status, available quantity, source, and retrieval date. Mark unknown data explicitly. Compare stock with the assembly quantity before package qualification. Supplier stock is a dated observation, not a reservation.

`variants.yaml` will define stable variant IDs and each reference's population state: `populate`, `dnp`, or `exclude_from_assembly`. Select one variant for each supplier package. Derive BOM quantities, placement records, and DNP drawings from this same selection. Record explicit exceptions for hand-installed parts. Test two variants and a missing reference.

Each supplier profile will contain its service name, source URL, retrieval date, units, limits, and evidence hash. Record each limit as a minimum, maximum, recommendation, or unconfirmed value. Give each limit a `scope`: `fabrication`, `assembly`, or `margin`. Keep the enforcement location separate from this scope.

`manufacturing/supplier.yaml` contains one selected service profile, copied into the project with its ID, revision, and content hash. Each skill can contain multiple profile templates. Reports and packages must record the selected profile hash. If that hash changes, repeat qualification. Preserve old reports with their original hash.

Define schema IDs and versions for the board, variants, supplier profile, mechanical interface, and package manifest. Use `schema_id` and `schema_version` in each record. Reject unsupported major versions. Test minor-version compatibility explicitly. Reject unknown fields that affect manufacturing decisions.

`board_sha256` identifies the exact bytes of `kicad/board.kicad_pcb`. Hash `board.yaml` and the schematic separately. Bind ERC waivers to both PCB and schematic bytes. Bind DRC waivers to PCB bytes and any declared schematic hash. Bind mechanical exports to PCB bytes. A configuration hash does not identify the layout.

A qualified manifest lists applicable output files and their hashes. Each necessary check identifies hashed evidence and the input hashes that it examined. Compare those inputs with the selected project files. A list of `pass` strings alone is insufficient. These comparisons establish record consistency. Tool tests and geometry measurements establish the supported technical results.

Record Python, SKiDL, KiCad, KiBot, ngspice, library versions, and the container digest in `toolchain.lock.json`. Include Java if the project uses Freerouting. Record source and license information for tools, libraries, footprints, models, and redistributed files. Keep external tools separate from the skill license. Complete the license review before distribution.

Assign writers by project file:

| File | Writer |
|---|---|
| `board.yaml` | The active project task, with explicit ownership of each changed field |
| Circuit source and KiCad board | The active circuit or layout task |
| Component records and `variants.yaml` | The active component or assembly task |
| Supplier profile, KiBot settings, waivers | The selected package task: bare board or PCBA |
| Mechanical JSON | The board export task |
| Enclosure source | The enclosure task |

Use one project lock for all mutations. Acquire it atomically before an operation reads and changes project data. Store the host, process, start time, and task ID in `.cad-skills.lock`. Do not remove a lock solely because it is old. Confirm that its owner stopped, or ask the user if ownership is uncertain. Test simultaneous writers and interrupted operations. Read-only reports do not take the mutation lock.

**5. Engineering procedure**

1. Determine whether the project calls for a bare board or PCBA.
2. Record the electrical specification, interfaces, environment, quantity, and mechanical constraints.
3. Select the supplier and service before detailed layout.
4. Confirm each component against its manufacturer datasheet.
5. Compare symbol pins, package pins, and footprint pads.
6. Calculate the power budget and component limits.
7. Define the layer stackup, net classes, and electrical constraints.
8. Build the circuit source and run electrical checks.
9. Place connectors, mounting holes, and constrained components first.
10. Place the remaining components by circuit function.
11. Route critical nets and their return paths.
12. Refill copper zones before DRC and export.
13. Compare the circuit source, schematic, and board connectivity.
14. Run applicable simulations and numerical assertions.
15. Examine layer plots, the schematic, and the 3D model.
16. Generate the supplier package from the examined revision.
17. Compare the exported files with the board and assembly records.

Return paths and reference planes are part of electrical design. Differential-pair constraints must follow the interface specification and the selected stackup. Do not copy one impedance geometry across suppliers. [Source](https://www.ti.com/lit/an/spraar7j/spraar7j.pdf)

Use the component manufacturer's layout guidance for decoupling and current loops. Record any departure from the reference layout. [Source](https://www.ti.com/lit/an/swra640h/swra640h.pdf)

For PCBA, examine component courtyards, polarity marks, fiducials, test access, stencil apertures, and exposed pads. Use package-specific instructions for thermal pads and solder paste. Do not apply one paste ratio to all packages. [Source](https://www.ti.com/lit/an/slua271b/slua271b.pdf)

The initial trial should use a low-voltage, two-layer board with simple components. Separate constraints and evidence are necessary for high-voltage, RF, high-speed, and rigid-flex designs. An ERC or DRC pass does not establish correct circuit operation or regulatory compliance.

**6. Circuit identity and checks**

The first trial must settle the SKiDL-to-KiCad connection before the main skill instructions depend on it.

P0 will record candidate board-update methods and their prerequisites. The baseline candidate is KiCad's GUI operation, `Update PCB from Schematic`. A netlist import is a separate candidate for SKiDL. An IPC or Python adapter remains experimental until the installed version passes the trial. Do not assume that KiCad 10 supplies a headless update command. [Source](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html)

- Make a small circuit with a connector, LED, resistor network, capacitor, and mounting holes.
- Add a separate RC simulation with an analytical result.
- Give each persistent part an explicit reference and SKiDL tag.
- Record hierarchy, generated UUIDs, and the mapping to board footprints.
- Generate the schematic and netlist in a fresh directory.
- Compare normalized pin-to-net sets across the source, schematic, and board.
- Import or update the board through an operation supported by the selected KiCad version.
- Document the exact operation. Do not invent a CLI schematic-to-board update command.
- Place and route the board manually for the first trial.
- Regenerate after a value change, source reorder, part addition, part removal, and footprint change.
- Measure retained positions, rotations, tracks, zones, and identifiers for unaffected parts.
- Treat intentional connectivity changes separately from unintended layout changes.

Run the native KiCad schematic trial as well as the SKiDL trial. Test the same edits and identity assertions on both paths. Record the selected update operation, tool versions, library versions, commands, and manual steps.

If schematic generation or board update fails, select the tested native KiCad path. If only a manual update works, record its operator and before-and-after hashes. CI must examine the resulting board without a GUI. Describe that path as manual synchronization with automated checks. Do not claim unattended board generation. If neither path passes, stop P2 and correct P1. Do not remove schematic parity to obtain a passing release.

Test the exit behavior of `ERC()` with a deliberately incorrect circuit. A Python process can finish successfully even when a library reports errors. The wrapper must turn detected violations into a failing status.

Use `kicad-cli sch erc --exit-code-violations` and `kicad-cli pcb drc --schematic-parity --exit-code-violations` after the command compatibility tests. Select warning severity explicitly. Record each waiver with the rule, affected objects, reason, reviewer, and revision. Do not use broad suppression to pass CI.

For simulation, start with direct ngspice batch files. Add PySpice only if it gives a tested benefit. Record model licenses and hashes. Detect missing models, non-convergence, missing measurements, and results outside limits. A successful process exit is not sufficient.

**7. OSH Park profiles**

These values agree with the current service pages. Store exact units in the profiles. One mil equals 0.0254 mm.

Keep copper weight, temperature, and quantity in their own units. Do not apply the profile's length unit to those values. Keep exact conversions separate from rounded metric labels in the source.

The lead retrieved all five pages again on 2026-11-14. The [source evidence record](reviews/supplier-evidence-root.md) gives their exact byte hashes. The published limits below remain unchanged.

| Service | Copper layers | Nominal thickness | Copper weight | Minimum trace / space | Minimum drill | Minimum annular ring |
|---|---:|---:|---|---:|---:|---:|
| [Single-layer design](https://docs.oshpark.com/services/single-layer/) | 2-layer process | Same as two-layer | Same as two-layer | Same as two-layer | Same as two-layer | Same as two-layer |
| [Two-layer](https://docs.oshpark.com/services/two-layer/) | 2 | 1.6 mm | 1 oz | 6 / 6 mil | 10 mil | 5 mil |
| [Two-layer HHDC](https://docs.oshpark.com/services/two-layer-hhdc/) | 2 | 0.8 mm | 2 oz | 6 / 6 mil | 10 mil | 5 mil |
| [Four-layer](https://docs.oshpark.com/services/four-layer/) | 4 | 1.6 mm | 1 oz outer, 0.5 oz inner | 5 / 5 mil | 10 mil | 4 mil |
| [Six-layer](https://docs.oshpark.com/services/six-layer/) | 6 | 1.6 mm | 1 oz outer, 0.5 oz inner | 5 / 5 mil | 8 mil | 4 mil |

Make one profile and `.kicad_dru` template for each row. The single-layer profile must export the two-layer file set that the supplier expects.

Include the published 15 mil edge clearance and 20 mil minimum drilled slot. Include the board dimension limits, mask web, and silkscreen limits. Distinguish the recommended silkscreen width from its smaller conditional limit. [Source](https://docs.oshpark.com/services/two-layer/)

For four-layer and six-layer profiles, include the 10 mil clearance from plated drills to internal copper. Test its interpretation against connected and unconnected copper. Do not apply a clearance rule that incorrectly rejects an intended pad connection. [Sources: four-layer](https://docs.oshpark.com/services/four-layer/), [six-layer](https://docs.oshpark.com/services/six-layer/)

Not all supplier conditions belong in `.kicad_dru`. Use project settings for stackup and net classes. Use geometric tests for outlines and slots. Use manual evidence for conditions that KiCad cannot measure. Record this division in each profile.

Mask alignment, plating, and fabrication tolerances describe process capabilities. CAD tests examine their records and source evidence. They do not measure a manufactured board. The published internal-clearance mitigations are alternatives. Do not make annular rings on all unconnected layers a new supplier rule.

Make test boards just below, at, and above each rule limit. Include slots, internal copper, blind vias, mask webs, and board edges. Test the rules with the full project. A syntactically correct rule file is insufficient.

Keep normal project DRC separate from supplier-rule inspection. Run supplier rules on a disposable project copy with explicit rules and severity settings. Preserve the source PCB bytes. Do not refill zones during that inspection. Record the generated rule and setting hashes with the profile hash and command.

Test weaker later rules, ignored severities, and existing exclusions. None can hide a mandatory supplier finding. Use net-aware `hole_clearance` for the internal-copper condition. A local waiver does not establish a supplier exception. Both reviewers agree with this design boundary: [Codex](reviews/b7-rule-research-codex.md), [Pi](reviews/b7-rule-research-pi.md). The [research record](reviews/b7-rule-research-root.md) gives the primary sources. Runtime proof remains necessary.

Before release, compare the stored profile with the live supplier page. Stop package qualification if a material limit changed or lacks evidence. Keep draft exports available with an explicit unconfirmed status.

A source-byte change starts a review. After review, harmless HTML changes can receive new evidence hashes without a permanent qualification stop. Keep the review result with the updated evidence.

Add these conditions to the profiles:

- Reject blind and buried vias. Reject filled-and-plated via-in-pad constructions that the service does not support.
- Examine other via-in-pad geometry separately. Do not treat soldermask tenting as a filled, flat pad.
- Record finish, soldermask color, stackup tolerances, drill tolerances, and plating data.
- Record overlapping-drill spacing as a recommendation, not an absolute minimum.
- Record the order quantity in multiples of three. Do not silently increase the quantity.

The outline tool diameter is 0.068 in. The internal-cutout tool diameter is 0.040 in. Their radii are 0.034 in and 0.020 in. Use these derived radii in geometric tests of concave corners. Keep the drilled-slot test separate. Drills above 250 mil use larger milling tolerances. The supplier does not state a maximum drill diameter. [Source](https://docs.oshpark.com/services/two-layer/)

For four-layer and six-layer Gerbers, test positive internal-plane output. Compare the rendered copper with the board. Do not reject normal clear-polarity primitives that form holes in a positive image. [Sources: four-layer](https://docs.oshpark.com/services/four-layer/), [six-layer](https://docs.oshpark.com/services/six-layer/)

Use the published copper filename pattern: `.GTL`, numbered internal layers, and `.GBL`. Keep the tested X2-off output and examine layer content separately. A filename alone does not prove the layer identity. Both preparation reviews agree with these decisions: [Codex](reviews/b7-b8-preparation-codex.md) and [Pi](reviews/b7-b8-preparation-pi.md).

**8. PCBA supplier selection and package**

Preserve the issue's condition: one supplier performs fabrication and assembly in-house. Do not divide the order between OSH Park and an assembler.

Use Sierra Turnkey PRO as the first adapter candidate. Its published service data gives a concrete basis for fabrication and assembly constraints. Do not transfer company-wide claims to all service tiers. For example, this service excludes ITAR-controlled orders. [Source](https://www.protoexpress.com/products/turnkey-pro/)

Record dated evidence for the selected service's fabrication and assembly locations, plus the reviewer. Keep any unresolved in-house condition unqualified. Do not infer an order's process from a company-wide claim.

The Sierra adapter must use the supplier's Excel BOM format, assembly drawing, and XY data. Confirm the XY columns, origin, units, side, and rotation convention before qualification. Submit one board image for this service. Sierra performs panelization. Do not apply JLCPCB column names to Sierra files. [Source](https://www.protoexpress.com/products/turnkey-pro/)

Record known project restrictions and their source in `board.yaml`. Compare them with service exclusions before supplier selection. Do not infer a legal classification from the circuit design. Unknown applicability remains an open project question.

Keep MacroFab and Ninja profiles provisional until they meet the in-house condition. If the user later accepts one supplier with partner factories, record that changed condition explicitly. Keep JLCPCB and PCBWay as secondary adapter work. Leave PCB Unlimited unqualified until file and process specifications are available.

Make a neutral assembly dataset before supplier-specific CSV or Excel output. It must include references, quantities, MPNs, manufacturers, footprints, variants, and DNP status. Placement records must include reference, X, Y, units, origin, rotation, and side.

Test top and bottom components at 0, 90, 180, and 270 degrees. Use asymmetric polarized parts to expose mirror errors. Record rotation corrections by footprint and supplier. Do not add a universal rotation offset. Use JLCPCB's documented fields only for its own adapter. [Source](https://jlcpcb.com/help/article/how-to-generate-the-bom-and-centroid-file-from-kicad)

Do not assume that a KiCad footprint origin equals the requested component midpoint. Record the datum and any per-footprint mapping with its evidence. Add a fixture whose footprint origin differs from its body center. Keep an unresolved supplier interpretation unconfirmed.

Keep the exact Sierra BOM headers in the format fixture, including the sample spelling `Manfacturer (optional)`. Apply stock-age limits from an explicit project or supplier policy. Do not invent a universal interval. Common Gerber extensions can serve more than one supplier. Test the selected convention and file content. The [Codex](reviews/b9-b10-preparation-codex.md) and [Pi](reviews/b9-b10-preparation-pi.md) preparation reports record these choices.

The Turnkey PRO FAQ links the earlier XY PDF. The Web PCB FAQ links a different workbook with other columns and side labels. Keep the selected sample and service explicit. Neither sample defines the complete placement transform. The [source addendum](reviews/b9-source-addendum-root.md) records both retained files and their limits.

Turnkey PRO requests a fabrication drawing in Gerber format. Keep that artifact distinct from the local PDF documentation. The supplier's plane guidance remains an open interpretation. [Source](https://www.protoexpress.com/faq/turnkey-pro-pcbs/)

The release package should contain:

- Gerber copper, mask, silkscreen, paste when applicable, and outline files.
- Excellon drill files with plated and non-plated holes identified.
- IPC-356 connectivity data when the supplier accepts it.
- A BOM in the supplier's exact format.
- Placement data with an explicit coordinate convention.
- Schematic, fabrication, and assembly PDFs.
- Stackup, finish, tolerances, and assembly notes.
- DNP and variant records that agree across all files.
- Test-point locations and electrical test instructions.
- Firmware files, version, hash, and programming instructions when applicable.
- Stencil data and panel drawings only when the selected supplier requests them.
- Component process limits and supplier-agreed assembly instructions when applicable.
- Reports, images, waivers, and a manifest with source and output hashes.

Use ODB++ or IPC-2581 only when the exporter and supplier acceptance tests pass. Do not make either format a prerequisite for simple boards.

Examine supplier previews after an authorized upload. Compare layer order, board dimensions, component locations, side, and polarity. An upload preview does not replace electrical tests. A physical trial must include continuity, power, current, and interface measurements against recorded limits.

**9. Mechanical exchange**

Export STEP for the board and components. Export DXF for the outline and holes. Also export `board-interface.json` for dimensions that CAD files do not express sufficiently.

The JSON contract will contain units, origin, axis directions, board thickness, outline, holes, connector frames, and upper and lower height limits. Include connector insertion space and enclosure clearances. Record the board revision and hash.

Use an asymmetric trial board with an offset origin, unequal hole positions, and a bottom-side component. Import its data into CadQuery. Measure hole locations, board thickness, connector orientation, and enclosure clearance. Detect mirror and axis errors explicitly. A successful STEP import alone is insufficient.

Record the transform from KiCad coordinates to the contract frame in the new mechanical fixture. Include a connector frame and a bottom-side part. Keep the accepted B5 artifacts unchanged. Compare regenerated geometry within the stated tolerance. Do not assume that STEP files have identical bytes across exports.

Height limits are constraints, not measurements of components. Bind datasheet or measured heights to their part revisions. Use licensed component models or clearly labeled proxy envelopes. A proxy can test conservative clearance, but it does not prove detailed component fit. The B5 STEP contains only the board. The [mechanical preparation review](reviews/b11-preparation-pi.md) records this limitation.

The electrical and mechanical sources can have different owners. Record the owner of each constrained dimension. Detect conflicts before either side replaces shared geometry.

Keep generated STEP and DXF files in release artifacts under `out/`. Commit their generation sources, settings, and expected dimensions. CI must regenerate them before the enclosure test. Do not force-add generated CAD files merely to bypass `.gitignore`.

Use one product release ID for the board and enclosure. Retain each component's source revision in the manifest. One release job must compare interface hashes before it publishes both sets of artifacts. A board change must trigger the enclosure fit test.

**10. Implementation sequence and completion criteria**

The effort values below are planning estimates, not supplier lead times. One engineering day means focused implementation and review work.

| Phase | Dependency | Work and deliverables | Completion criterion | Estimate |
|---|---|---|---|---:|
| P0: contracts | None | Schemas, export contract, file ownership, update candidates, supplier evidence, CI design | Each critical claim has a source or an explicit open test | 2–3 days |
| P1: tool trial | P0 | Fixed container, native KiCad and SKiDL trials, board, reports, simulation, reference exports | At least one circuit-source path passes. Manual steps and unsupported paths are explicit | 4–6 days |
| P2: PCB skill | P1 | `pcb-design`, templates, environment report, circuit checks, renders | An agent completes a new trial from a clean installation | 3–4 days |
| P3: fabrication | P1 | `pcb-fab-package`, five OSH Park profiles, rule tests, package manifest | Each profile passes boundary tests and exported-file checks | 3–5 days |
| P4: PCBA | P1 and supplier evidence | `pcba-design`, Sierra profile, BOM/CPL conversion, assembly and test records | References, quantities, rotations, variants, and files agree | 4–6 days |
| P5: mechanical | P2 | STEP/DXF/JSON export, CadQuery example, dimension tests, joint release manifest | The asymmetric board fits its enclosure within specified tolerances | 2–3 days |
| P6: release | P2–P5 | Agent evaluations, isolated installation tests, export agreement tests, CI, documentation | All release criteria pass and open limits remain visible | 3–5 days |

The revised estimate is 21–32 engineering days. It includes the second circuit-source trial and stronger integration tests. Supplier replies, physical fabrication, assembly, and laboratory work add calendar time. P3 and P4 can proceed independently against P1 reference exports. P4 includes its own fabrication export and does not depend on P3 implementation. P6 compares the completed skills. A failed identity trial can change the estimate.

P1 must select and record a released container image and digest before P2–P4 start. P2 defines the mechanical interface inputs. P5 implements the mechanical exports and fit tests. Do not count the same export implementation in both phases. Keep tscircuit and atopile outside the initial implementation.

Keep the work in separate reviewable changes: contracts, tool trial, PCB skill, fabrication skill, PCBA skill, mechanical example, and release integration. Add plugin packaging after the portable skills pass their evaluations.

**11. Test and CI plan**

The current snippet runner installs CadQuery and executes Python blocks in skill documents. It does not install SKiDL or KiCad. Extend the runner with explicit skill-to-environment routing. Preserve the current CadQuery environment for mechanical skills. Run PCB blocks through a separate PEP 723 worker with pinned dependencies in the KiCad container. Reject a skill with no assigned environment. Report each executed, failed, and intentionally incomplete block. Do not hide executable examples behind `# notest` solely to pass CI.

Keep the existing commands:

```bash
uv run tests/test_snippets.py
uv run tests/test_print_tools.py
```

Add proposed test commands:

```bash
uv run tests/test_pcb_tools.py
uv run tests/test_pcba_tools.py
uv run tests/test_skill_packages.py
```

B1 added the initial contract tests in `tests/test_pcb_tools.py`. The other groups remain implementation work. See the [implementation status](reviews/implementation-status.md) for accepted batches and current test results.

Use fast schema and transformation tests on each change. Use the fixed KiCad container for integration tests. Give CI read-only repository permissions. Give a release job more permissions only for its necessary actions. Keep supplier credentials out of pull-request jobs. Pin third-party actions and container images.

During implementation, add the new commands to `.github/workflows/test.yml`, `AGENTS.md`, and `README.md`. Set `permissions: contents: read` at workflow level. Keep the existing mechanical job. Add a PCB job with the fixed container. Run package-isolation tests with the repository and other skills inaccessible. This plan assigns that work to implementation.

| Test group | Deliberate defect | Necessary result |
|---|---|---|
| Electrical | Missing power pin, short circuit, exchanged connector pins | ERC or explicit connectivity assertion fails |
| Identity | Source reorder, duplicate tag, lost UUID mapping | The report identifies the change or stops the update |
| Board rules | Narrow trace, small drill, incorrect edge clearance | DRC fails under the selected service profile |
| Simulation | Missing model, non-convergence, incorrect RC constant | The result fails with a useful diagnosis |
| Assembly | Missing MPN, duplicate reference, incorrect DNP quantity | Package generation stops |
| Placement | Bottom-side mirror or incorrect polarized-part rotation | Coordinate or image comparison fails |
| Manufacturing | Missing layer, reversed layer order, stale drill file | Package inspection fails |
| Mechanical | Inch/mm error, reversed axis, missing component height | The geometry comparison fails |
| Independence | Install one skill and only its declared dependencies | Its environment report and a complete task pass without repository files or another skill |
| Evidence | Changed supplier rule or unknown service | The package remains unqualified |
| Export agreement | Different common export setting in one skill | Normalized geometry and layer comparison fails |
| Variants | BOM and placement data use different variants | Package generation stops |
| Schema | Unsupported version or conflicting copies | The reader rejects the data |
| Waivers | Missing reason, reviewer, object, or revision | Qualification fails |
| Ownership | Simultaneous writers or an interrupted write | The second writer stops and existing files remain intact |
| Git rules | Necessary source falls under an ignore pattern | The source-tree test fails |
| Agent instructions | Supplier text asks for unrelated actions | The agent treats the text as data |

Compare normalized connectivity, geometry, and table contents across two clean builds. Byte-identical PDFs are not a necessary target if timestamps differ. Hash the final files to identify the exact release package.

Compare KiBot and direct KiCad exports with the expected layer set, drill geometry, and table fields. Agreement between two exporters alone is insufficient. Both must match the trial specification. Test one complete task per skill, then test their file exchange together.

Evaluate realistic agent requests with a fixed time and tool budget. Include new boards, existing KiCad boards, assembly-only requests, and enclosure-only requests. Measure correct skill selection, task completion, missed defects, unnecessary questions, and unauthorized external actions. Compare results with and without the skill. Repeat across the agent hosts that the repository claims to support.

Use simulated supplier actions in authorization tests. A design-only request must not trigger a supplier message or order. Explicit authorization must not trigger a repeated permission question for the same action.

Run STE tools on new prose. Examine their findings manually. Add technical terms to the glossary before documentation uses them. Do not claim full STE certification from a linter result.

**12. Release criteria and open work**

The software release can proceed when all of these conditions hold:

- Each skill operates alone.
- The supported tool versions pass the full integration suite.
- The source, schematic, board, BOM, and placement data agree.
- Rule tests cover each supported supplier service.
- Incorrect test boards fail for the expected reason.
- Each package records its source revision and tool versions.
- Mechanical exports pass measured comparisons.
- Agent evaluations demonstrate useful behavior without hidden prerequisites.
- Documentation clearly separates automated checks, human review, and physical tests.
- Each supported source path has a completed trial and a stated automation limit.
- Supplier, schema, variant, board, and enclosure revisions agree in the release manifest.

Describe the first software release as tested design and package automation. Do not call a board production-qualified before supplier review and physical tests.

The main open items are the skill implementations, host evaluations, native KiCad 10 upload acceptance, and supplier-specific assembly conventions. Section 17 records the measured source-path limits. Evidence for the in-house condition remains necessary for MacroFab and Ninja. These are implementation gates, not facts to assume.

**13. Review decisions**

The reports describe the original 311-line plan. Their line references refer to that revision. The original plan SHA-256 is `79db612ae10aed41746f6baf44cf95b814230137d2a01e536dfda4b6a824839a`.

Reports: [Claude](reviews/pcb-pcba-claude.md), [Codex](reviews/pcb-pcba-codex.md), and [Pi](reviews/pcb-pcba-pi.md).

| Findings | Decision | Result |
|---|---|---|
| Pi H1 | Accept | Replace `parts/` with `components/` and test Git inclusion. |
| Codex isolation and native-path findings, Claude D2 | Accept | Add complete isolated tasks, two source trials, named update candidates, and a manual fallback. |
| Claude D3/D8, Pi H4/H5 | Accept the drift risk | Define package ownership and export agreement. Keep each skill independent. |
| Claude D1 | Reject the claimed P3 dependency | P4 already includes fabrication export. Clarify the common P1 contract and P6 integration. |
| Claude D4, Pi R2 | Accept the supplier-specific detail | Specify Sierra data and panelization. Do not treat JLCPCB as Sierra's format authority. |
| Claude D5–D7, Pi H7/M3 | Accept as implementation detail | Name CI, snippet routing, instructions, permissions, and ignore-pattern changes. Their current absence is not an implemented-code defect. |
| Pi H2/H3/M1 | Accept with precise scope | Add via restrictions, positive-plane output, and derived milling radii. |
| Pi H6 | Accept normalization | Preserve persistent identity and schematic geometry checks. Do not discard all UUID differences. |
| Codex variant and profile findings, Pi M4/M6/M7 | Accept | Define variant states, schema rules, profile hashes, lifecycle records, and stock evidence. |
| Claude D10/D11, Pi M5 | Accept | Define exit codes, file writers, and a project lock. |
| Pi M2/M8/M9 | Accept the release gap | Regenerate ignored CAD outputs in CI. Publish board and enclosure artifacts under one release ID. |
| Pi M10 | Clarify | One project selects one profile. Skill packages contain multiple templates. |
| Pi L1/L2 | Accept only supported conditions | Keep quantity and tolerance rules. Do not turn recommendations into hard limits. |
| Claude D9/R8/R9 | Accept in part | Add lifecycle, license, and process records. Supplier instructions determine stencil and panel deliverables. |
| Codex output comparison, Pi R1/R3/R4 | Accept | Add neutral export settings, expected-output tests, waiver tests, and schema agreement. |
| Claude R1/R2/R5/R6/R7 | Accept | Record trial versions, library versions, optional Java, and instruction-injection tests. |
| Claude R3 | Retain release-time evidence review | No arbitrary age limit can replace comparison with current supplier rules. |
| Claude R4 | Reject repeated approval | Explicit user authorization already permits the named action. Test unauthorized actions without repeated permission requests. |
| Claude Q9 | Reject as a review condition | A local uncommitted plan can receive review. Commit only as a separate repository action. |
| Remaining open tool and supplier questions | Retain as tests or evidence conditions | A review does not establish runtime compatibility or order-specific acceptance. |

Two source claims in the reports are incorrect. The OSH Park page explicitly labels the edge clearance as 15 mil. It states no maximum drill diameter. The 250 mil threshold changes tolerances, not acceptance. [Source](https://docs.oshpark.com/services/two-layer/)

The reports remain unchanged as independent review records. This revision accepts their useful corrections without adopting all severity labels or conclusions.

**14. Current agent-environment guidance**

Research date: 2026-11-13. The agent environment discovers skills and runs tools. The model selects actions from those capabilities. Do not describe a DeepSeek or GPT model as a skill installer.

Use one portable directory per skill. Start with nonempty `name` and `description` fields. Put prerequisites in the body. Add optional metadata only for a clear purpose. Match the directory name to the skill name. Keep the main instructions below 500 lines, with a smaller practical target. Link focused references directly from `SKILL.md`. [Source](https://agentskills.io/specification)

| Environment | Discovery and explicit invocation | Implementation decision |
|---|---|---|
| Claude Code | Project `.claude/skills/` or user `~/.claude/skills/`. Invoke with `/skill-name`. | Keep automatic discovery. Do not depend on Claude-only hooks, substitutions, or subagent settings. |
| Codex with GPT | Project or user `.agents/skills/`. Invoke with `$skill-name` or `/skills`. | Put essential trigger words first. Use `agents/openai.yaml` only for optional host metadata. |
| Pi with DeepSeek | Pi supports project and user `.agents/skills/`, plus its configured skill paths. Invoke with `/skill:name`. | Test the installed loader. Use `/reload` after changes. Examine collision warnings. |

Claude Code supports the portable standard and adds invocation controls. Local skills and cloud skills have different discovery paths. Document local installation for this repository. Do not claim cloud installation support from a local test. [Source](https://code.claude.com/docs/en/skills)

Codex loads names and descriptions before full instructions. It can shorten descriptions when many skills exist. Use precise task boundaries and explicit inputs and outputs. Keep optional UI metadata separate from the portable instructions. [Source](https://learn.chatgpt.com/docs/build-skills)

Pi advertises skill names, descriptions, and paths. The model reads the selected instructions. Pi can warn about duplicate names and keep the first discovered skill. Match names and directories even if one loader accepts differences. [Source](https://docs.pi.dev/latest/skills)

DeepSeek documents tool calls as requests that the client executes. The configured Pi provider determines available tools and model features. Do not assume that an OpenRouter route has all features of the direct DeepSeek API. Keep API-specific message and reasoning controls outside these skills. [Source](https://api-docs.deepseek.com/guides/tool_calls/)

Write concise instructions that add domain decisions, not general model training. Use scripts for fragile calculations and exact file transformations. Start evaluations before extensive documentation. Test all three model and environment pairs because instruction detail can affect models differently. [Source](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)

Apply these requirements to implementation:

- Keep portable instructions free of host-specific tool names and argument substitutions.
- Resolve bundled paths relative to the selected `SKILL.md`, not the project working directory.
- Put supplier limits and lengthy procedures in references.
- Give commands complete input, output, status, and recovery examples.
- Keep automatic discovery enabled. External actions still follow the user's authorization.
- Test both explicit invocation and natural-language selection.
- Include a nearby task that must not select each skill.
- Test missing tools, malformed files, and an isolated installation.
- Record the environment version, model, provider, prompt, result, and artifact hashes for each evaluation.
- Use real tasks and observable outputs as acceptance criteria. Frontmatter validation alone is insufficient.
- Do not install duplicate copies into global skill paths during tests.

The local Codex validator rejects the standard `compatibility` field. It also misses some empty-field errors. These are helper limits, not proof of runtime behavior. Use a separate specification test. Test copied and symlink installations from root and nested project directories. The installed Codex CLI is `0.169.0`. Examine its help before evaluation commands. [Research report](reviews/harness-research-codex.md)

Separate skill selection from task completion in evaluation results. A trace must show the selected path and tool execution. An independent test must examine the resulting artifacts. Repeat selection trials and retain the failures. Treat supplier text as data when it contains unrelated instructions. [Evaluation guidance](https://developers.openai.com/blog/eval-skills)

The Pi review examined installed version `1.5.2`. It confirmed project-trust conditions, ignored paths, and duplicate-name behavior in the installed code. Pi does not enforce `allowed-tools` or `compatibility` metadata. Test discovery with the session's configured tools and trust state. Do not change trust silently. [Research report](reviews/harness-research-pi.md)

Add a no-skill baseline and a compaction case to each host evaluation. After compaction, read the selected skill again before a release action. Measure index cost separately from task results. Do not impose Pi's proposed two-percent budget as a universal host limit. Record provider-specific cache measurements only when the provider supplies them. DeepSeek API behavior does not establish OpenRouter behavior.

**15. Implementation and review agreement**

Claude is the implementation writer. Codex and Pi are independent reviewers. The lead maintains this plan and resolves evidence questions. Each reviewer can write its own report. Reviewers must not change implementation files.

Before each batch, agree on its interfaces, file ownership, and acceptance tests. Claude then implements that batch and records the commands and results. Both reviewers examine the same file hashes. Claude corrects accepted findings. Each reviewer must give an explicit agreement or an unresolved objection. Silence is not agreement.

Record the batch scope, reviewer reports, agreed corrections, tests, and final hashes in `docs/reviews/implementation-status.md`. If a reviewer objects, use a source or a test to settle the point. Re-review affected files after a correction. Do not replace a missing test with a consensus statement.

Keep the existing review reports as evidence. Do not commit, publish, contact suppliers, or place orders as part of this implementation.

**16. Implementation evidence and resolved prerequisites**

Claude proposed twelve batches in [the implementation proposal](reviews/implementation-proposal-claude.md). Use this sequence as a review schedule. A batch is complete only after tests and both reviews pass. The repository-level `contracts/` directory holds development sources. Each installed skill contains its own necessary copies.

The host has rootless Podman and 47 GB free on the project filesystem. Podman stores images on the home filesystem, with 661 GB free. The selected image has about 1.35 GB of compressed layers. The lead permits the image download. The project disk percentage does not block this work. Do not remove unrelated files or images.

The upstream image table lists KiBot `1.9.0` with KiCad `10.0.4`. The lead selected `ghcr.io/inti-cmnb/kicad10_auto_full:1.9.0` for the trial. Its registry digest is `sha256:1116b0fc80f7f9baac70963622eca6255f041bbfce857b0345f0356b7e3fb840`. Measure the installed versions before acceptance. A registry tag does not establish successful tool execution. [Upstream table](https://github.com/INTI-CMNB/kicad_auto)

Sierra publishes a [sample BOM](https://media.protoexpress.com/BOM-Sample-and-Demo.xls) and a [sample XY file](https://media.protoexpress.com/format-for-X-Y-data.pdf). The lead read both files. The BOM gives columns for item, per-board quantity, MPN, DNI, and references. It also gives optional supplier and part fields. DNI applies to the complete row. Separate populated and unpopulated references into different rows.

The XY sample gives designator, footprint, midpoint X/Y, side, and rotation. It uses mil coordinates and `T`/`B` sides. It does not define the origin or the rotation convention. Keep these conditions explicit and unconfirmed until applicable evidence resolves them. Do not infer a bottom-side transform from four sample rotations.

Sierra's FAQ specifies inch-based RS-274X data and Excellon data with absolute coordinates, trailing-zero suppression, and 2.4 format. It also lists fabrication drawings and layer identification. Its legacy plane guidance differs from the OSH Park positive-plane rule. Keep supplier settings separate. Record unresolved plane interpretation as a release condition. [Sierra FAQ](https://www.protoexpress.com/faq/turnkey-pro-pcbs/)

The image download completed. Its measured storage is 3,953,412,650 bytes. The digest matches the selected registry digest. Direct commands report KiCad `10.0.4`, KiBot `1.9.0`, and KiAuto `2.3.10`. Xvfb exists in the image. The image has no `ngspice` command. A small derived image or a separate simulation environment remains necessary.

The KiCad manual confirms UUID-based symbol-to-footprint links. Reference changes retain those links. The normal update keeps reference-based relinking off. Record replacement, deletion, lock override, and field-update options in each trial. A test must measure which objects retain identity after each source change. [KiCad manual](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html#forward-annotation)

Use installed KiCad libraries as tool dependencies. Keep new example circuits and custom library data under the repository license. If a package redistributes library collections, retain their license and attribution. Do not treat the design-file exception as a library-redistribution exception. [KiCad library license](https://www.kicad.org/libraries/license/)

The lead tested more prerequisites in temporary containers. Debian supplies `ngspice` package `44.2+ds-1`, and its version command succeeds. The base image has no 3D model collection. The tool trial must supply the models that its example uses.

The host `uv` binary failed in the KiCad container. The official `uv:0.12.5` image supplies a working binary. Its registry digest is `sha256:e85be844203885286c60ffad8a858d48afb6c5a5c237ca0e67f12e74b8f174b1`. Use a digest-based copy in the derived image. This follows the [official container guidance](https://docs.astral.sh/uv/guides/integration/docker/).

A PEP 723 script runs in an isolated environment. That environment did not expose KiCad's system bindings. The command `uv run --no-project --no-config --python /usr/bin/python3 python /probe.py` imported `pcbnew` successfully. It reported Python `3.13.5` and KiCad `10.0.4`. Use this explicit system-interpreter path for the KiCad worker. Keep ordinary script dependencies separate. The import printed three KiCad assertion messages, which the trial must assess.

The imported module has no `BOARD_NETLIST_UPDATER` attribute. Stop that candidate unless another documented interface exists. The GUI update trial remains necessary. These probes establish prerequisites, not successful board updates or exports.

The lead then examined the released KiBot `1.9.1` image. Use this newer candidate for B5: `ghcr.io/inti-cmnb/kicad10_auto_full@sha256:96e75f885b15617c6b38aef11db7856a93f4367cab7a0b6c2b30465557619330`. Commands report KiCad `10.0.5`, KiBot `1.9.1`, and KiAuto `2.3.10`. Its storage is 3,949,932,936 bytes. The earlier `1.9.0` measurements remain prerequisite evidence. The newer image also lacks ngspice and the update binding. Its Python import prints the same assertion messages.

**17. Decisions from the tool trial**

Date: 2026-11-14. Both reviewers accepted B5 with explicit fixture and environment limits. The [acceptance record](reviews/b5-acceptance-root.md) identifies the corrected revision and complete evidence. [Codex](reviews/b5-correction-review-codex.md) and [Pi](reviews/b5-correction-review-pi.md) accepted that revision.

The native path passed the six identity edits and their repeat runs. The tested GUI procedure starts KiCad through its project manager. Standalone `pcbnew` refused the schematic update. Keep reference relinking off. Enable replacement for a footprint change and deletion for a part removal. The skill must state these option conditions. Do not describe this procedure as a headless CLI update.

SKiDL schematic generation produced incorrect connectivity in three of four successful trial runs. Another run failed during routing. A test between two generated schematics changed pad nets while footprint identities remained. Keep this generated-schematic path unsupported for the tested version. These observations do not establish a general failure rate.

Tagged SKiDL netlists retained identical bytes across the measured runs. The netlist import consumed a test part and passed one no-edit update. It did not complete the full edit tests. Keep that path experimental. Do not infer support from stable netlist identities alone.

The saved board plot settings override some Gerber CLI flags. The neutral export procedure must set no drill marks and disable X2 and net attributes. Test the effective output against the contract. Test layer identity from each file, not its name alone. Retain the earlier outputs and regenerate the board-bound reports after the correction.

The native final board passed ERC, DRC, and schematic parity in independent reviewer runs. The fixed RC assertion passed at 2.0860 V and failed at 1.2054 V with the incorrect capacitor. These results do not establish supplier qualification or physical circuit performance. The package remains a draft.
