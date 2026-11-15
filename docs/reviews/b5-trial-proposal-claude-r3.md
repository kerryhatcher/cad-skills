# B5 trial execution proposal (Claude), revision 3

Date: 2026-11-14.

Status: proposal only. I change no implementation file. Earlier versions stay as evidence:

- `b5-trial-proposal-claude-r1.md` (SHA-256 `ccac378e4526433834a31f21a3306ab098fe732289407a40cc6c256c27433b6c`)
- `b5-trial-proposal-claude-r2.md` (SHA-256 `550305edd513672638e414e4bbbf618ee6e553335d28f381cd9f24a2235b324a`)

Codex reviewed revision 2 as the bytes with SHA-256 `7b377597bf229facd99bd22e2b398d425a6f79be129570a363f4873b81e4f5ae`. That draft is an earlier state of the same text. The lead accepted all six corrections of `b5-design-codex.md` (B5-1 to B5-6). This revision applies them. No research cycle was necessary.

**1. Aim and limits**

B5 answers four questions with measured results:

1. Do the fixed tools run in the container and give the exit codes and files that the contracts expect?
2. Which method updates a board from a schematic, and what does it do to footprint identity?
3. Does the SKiDL path keep identity, and what does it cost?
4. Do the B234 validators accept a project and a package that real tool output produces?

B5 does not choose a supplier, order a board, or test a physical board. It keeps tscircuit and atopile out. B5 uses the B234 validator and package rules after the B234 corrections are accepted.

**2. Change log: what this revision changes**

| Codex item | Change | Section |
|---|---|---|
| B5-1 | The schematic and the PCB have separate format versions. KiCad output and the format documents give them. The generator has its own name. Tests check instances, pin positions and the complete connectivity map. A generator failure is "untested", not evidence about KiCad. | 3 |
| B5-2 | `requirements.in`, a complete `uv pip compile` command with the full digest, separate `uv venv` and `uv pip sync` operations, an offline probe after the online build, and a derived image ID for the runs. | 4 |
| B5-3 | Every Python run uses `uv` with `--offline`. The common command sets `/work`. T9 has full commands. The installed 10.0.5 help is the authority. | 4, 5 |
| B5-4 | Phase A (identity experiments on an intermediate board) and phase B (the final reference board with full routing, zones and clean checks) are separate. The package stays `draft`. | 5, 7 |
| B5-5 | Identity comparisons check exact fields against an expected-difference file. Routing changes are named by object UUID. The reader is tested on real saved output and on negative fixtures. | 6 |
| B5-6 | U3 is a distinct netlist import with an input-dependent test. U4 results are separate for each input. S5 has two cases. The stop outcomes are honest. | 6, 8 |

**3. Fixed environment and fixtures**

| Item | Value |
|---|---|
| Base image | `ghcr.io/inti-cmnb/kicad10_auto_full@sha256:96e75f885b15617c6b38aef11db7856a93f4367cab7a0b6c2b30465557619330` (local) |
| Measured by the lead | KiCad 10.0.5, KiBot 1.9.1, KiAuto 2.3.10, Python 3.13.5. `pcbnew` prints 3 assertion messages when imported and has no `BOARD_NETLIST_UPDATER`. The image has no ngspice, no `uv`, and no 3D models. |
| Command authority | The `--help` of the installed 10.0.5 tools. The online manual describes 10.0.8. |
| Old image 1.9.0 | Evidence only. B5 does not use it. |
| uv | The static binary (entry point `/uv`) of `ghcr.io/astral-sh/uv@sha256:e85be844203885286c60ffad8a858d48afb6c5a5c237ca0e67f12e74b8f174b1` (uv 0.12.5). The host `uv` crashes in the container. |
| ngspice | Debian 13 package `ngspice` 44.2+ds-1 |
| Mounts | Mount a temporary copy of the trial directory with `:Z`. Never relabel the repository or other files. |
| Disk | Stay below the 15 GB budget. The image uses 3.95 GB. |

Board: two layers, 40 mm by 25 mm, offset origin. Parts: `J1` (header 1x02), `D1` (LED 0603, asymmetric and polarized), `R1` (series resistor), `R2` (10 kohm), `C1` (100 nF), `MH1` and `MH2` (mounting holes at unequal positions). The RC network has an analytic result: the time constant is 1.000 ms, and the voltage at one time constant for a 3.3 V step is 2.086 V. The simulation must agree within 1%. A deliberately wrong capacitor value must fail the same test.

**Native fixture (B5-1).** The generator is `scripts/trial_native_writer.py`. Its output has the generator name `cad_skills_trial_native`. It uses no SKiDL and no file from a person.

1. Format versions. The schematic and the PCB are two formats with two version numbers. The version of `Device.kicad_sym` is a third value and is not used for them. The generator takes each version from installed KiCad output: it writes a stub with a candidate version, runs `kicad-cli sch upgrade` and `kicad-cli pcb upgrade`, and reads the `(version ...)` that KiCad 10.0.5 writes. It compares the result with the version in the [schematic format document](https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/) and the [board format document](https://dev-docs.kicad.org/en/file-formats/sexpr-pcb/). The record shows both values and their evidence.
2. Symbols. It copies the text of `Device:R`, `Device:C`, `Device:LED`, `Connector_Generic:Conn_01x02` and `Mechanical:MountingHole` from the installed libraries into `lib_symbols`.
3. Instances. It places one instance for each part with a UUID from `uuid5` of the reference, so two runs give the same file. It connects pins with net labels at the pin ends and computes the pin positions from the symbol text. It sets the footprint property of each symbol.
4. PCB. It writes a `.kicad_pcb` with its own version, a 40 mm by 25 mm outline on `Edge.Cuts`, and no footprints, and a minimal `.kicad_pro`.

A successful load is not enough. Step T3 requires all of these:

- `kicad-cli sch erc` reads the schematic and writes a report.
- The schematic has exactly 7 symbol instances with the expected references, values and footprints. The pin positions that the generator computed equal the positions in `expected/pins.json`.
- `kicad-cli sch export netlist` writes a netlist. The complete pin-to-net map equals `expected/netlist.json`.
- `kicad-cli pcb drc` reads the PCB and writes a report.

If the generator gives an invalid file, the generator changes at most two times. After that the native path is "untested". A generator failure is no evidence that KiCad cannot keep identity.

**SKiDL fixture.** `skidl/circuit.py` builds the same circuit with a tag on each part, with the same references and footprints.

Files: `examples/pcb-trial/{native,skidl}/`, `rc.cir`, `requirements.in`, `requirements.lock`, `scripts/`, `expected/`. Generated output goes to `out/`, which Git ignores.

**4. Sources, setup and offline runs (B5-2, B5-3)**

B5 may use these sources only:

1. the official fixed images above (base image and `uv` image)
2. the Debian package source for `ngspice` and its dependencies
3. PyPI for SKiDL and its pinned dependencies

`TRIAL` is the absolute path of a temporary copy of `examples/pcb-trial`. `requirements.in` holds the one line `skidl==3.0.0`.

Online setup, one time:

```bash
# T0a: resolve and hash the dependencies
podman run --pull=never --rm -v "$TRIAL:/work:Z" \
  ghcr.io/astral-sh/uv@sha256:e85be844203885286c60ffad8a858d48afb6c5a5c237ca0e67f12e74b8f174b1 \
  pip compile /work/requirements.in --python-version 3.13.5 \
  --generate-hashes --no-header -o /work/requirements.lock
# T0b: build the derived image
podman build -t localhost/cad-skills-trial:b5 -f "$TRIAL/Containerfile" "$TRIAL"
IMAGE_ID=$(podman image inspect --format '{{.Id}}' localhost/cad-skills-trial:b5)
```

The record states the target platform and the resolved package versions. The Containerfile does these operations in this order, with these paths:

```text
COPY --from=uv /uv /usr/local/bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends ngspice=44.2+ds-1 && rm -rf /var/lib/apt/lists/*
COPY requirements.lock /opt/trial/requirements.lock
RUN uv venv --python /usr/bin/python3 --system-site-packages /opt/trial-venv
RUN uv pip sync --python /opt/trial-venv/bin/python --require-hashes /opt/trial/requirements.lock
```

A resolved lock file does not make an offline environment. The online build installs every package and tool. The setup check then runs offline:

```bash
podman run --rm --pull=never --network none -w /work "$IMAGE_ID" \
  uv run --no-project --no-config --offline --python /opt/trial-venv/bin/python python -c "import skidl, pcbnew"
```

The probe must import both SKiDL and the system KiCad bindings through `uv`. The assertion messages of `pcbnew` are recorded, not hidden. The same probe runs once during the online build and once with `--network none`.

The common command for all steps after T0:

```bash
podman run --rm --pull=never --network none -w /work -v "$TRIAL:/work:Z" "$IMAGE_ID" COMMAND
```

Trial runs use the derived image ID, not only the local tag. `examples/pcb-trial/toolchain.lock.json` records the derived image in the fields that the toolchain schema has: `container.image` is the tag and `container.digest` is `sha256:` followed by the derived image ID. The schema has no field for the base image digest. The base digest goes in the `notes` of the `kicad` tool entry and in the trial record. The tools carry their measured versions. B5 makes no claim about a field that no test checked.

`requirements.lock` is in the repository with the version and the hashes of each package. The record repeats the package versions and the SHA-256 of `requirements.lock`.

**5. Steps**

Every Python command uses `uv` with `--no-project --no-config --offline`. For KiCad scripts the interpreter is `--python /usr/bin/python3`. For SKiDL it is `--python /opt/trial-venv/bin/python`. Host-only scripts have PEP 723 headers. Each step records the command, the exit code, and the hash of the output.

| Step | Command (inside the container, in `/work`) | Pass condition |
|---|---|---|
| T1 versions | `kicad-cli version`, `kibot --version`, `eeschema_do --version`, `ngspice -v`, `uv --version`, `uv run ... --python /usr/bin/python3 python --version` | Equal the measured versions |
| T2 discovery | `--help` of `sch erc`, `sch upgrade`, `pcb drc`, `pcb upgrade`, `pcb export gerbers`, `drill`, `pos`, `step`, `dxf`, `ipcd356` | The options exist. T2 builds a table: contract setting, CLI flag, value. |
| T3 native fixture | `uv run ... --python /usr/bin/python3 python scripts/trial_native_writer.py`, then the checks in section 3 | All checks of section 3 pass |
| T4 SKiDL schematic | `uv run ... --python /opt/trial-venv/bin/python python skidl/circuit.py` with `KICAD10_SYMBOL_DIR=/usr/share/kicad/symbols`, twice in two fresh directories | A `.kicad_sch` and a netlist. The structural comparison is in section 6. |
| T5 ERC exit | `kicad-cli sch erc --exit-code-violations --severity-all --format json -o erc.json FILE` on a good and a defective schematic | Exit 0 for the good file. Nonzero for the defective file. |
| T6 SKiDL `ERC()` exit | A run with a deliberately wrong circuit | Record the exit code. The B6 wrapper must turn a detected violation into a failure. |
| T7 board update | U1 to U6 (section 6) | One result row for each of U1 to U6 |
| T8 identity phase A | The gate edits and limit probes of section 6 on the intermediate board | The tables of section 6 |
| T9 final board | Section 7 | Clean checks on the saved final board |
| T10 exports | Section 7 | Exports agree with the expected values |
| T11 KiBot | `kibot -c trial.kibot.yaml -b FILE.kicad_pcb -e FILE.kicad_sch` | Same layer set, drill split and position columns as T10. Record each difference. KiBot agreement alone is not enough. |
| T12 simulation | `ngspice -b rc.cir -o rc.log` | The value is within 1% of 2.086 V |
| T13 contracts | On the host: `uv run contracts/validate.py --project PROJECT --package PACKAGE --json` | Exit 0 for the draft package (section 7) |

**6. Board update methods and identity (B5-5, B5-6)**

The KiCad manual states that `Update PCB from Schematic` matches footprints by UUID, and that re-linking by reference is off by default. The trial measures what this does.

| ID | Input | Operation | Time box |
|---|---|---|---|
| U1 | The native schematic | The schematic update (F8) | 30 minutes |
| U2 | The schematic that SKiDL `generate_schematic()` writes | The schematic update (F8) | 30 minutes |
| U3 | The SKiDL netlist with tags | A netlist import in the PCB editor | 30 minutes |
| U4 | The scripted GUI mechanism | `scripts/gui_update.py` starts Xvfb, opens `pcbnew`, sends the keys with `xdotool`, and saves the board. It serves U1, U2 and U3. | 1 hour to build |
| U5 | The IPC API | A session of the GUI in the container | 30 minutes |
| U6 | `pcbnew` Python | Look for a netlist updater. The lead's probe found none, so this is a recorded negative. | 10 minutes |

**U3 is distinct from U1 and U2.** F8 is the schematic-update workflow. U3 uses the netlist-import operation of the installed editor, if the 10.0.5 editor has one. T7 first looks for the operation. If none exists, U3 is "unsupported" and the record says so. If it exists, the trial proves that the operation read the netlist: it imports a netlist N1 that differs from the schematic (it adds one footprint that the schematic does not have). The result must contain that footprint. A result that follows the schematic is not a netlist trial.

**U4 results are separate for each input.** For U1, U2 and U3 the record has these fields: the dialog options, the process exit code, the hash of the saved file, and the parity result. A sequence of keystrokes that ends without error is not a successful update. The update succeeds only when the saved file has the expected footprints and the parity result is empty.

If U4 fails for an input within its time box, the record states an explicit manual handoff: the named operator, the before-and-after hashes, and the tested operation. A manual handoff is not an automated pass. B5 never claims unattended board generation unless U4 passes the gate edits twice in a row for the same input. If a person must act, the request is a normal task step for the lead or the user.

**Dialog options.** The trial records the exact labels and defaults of the options of the `Update PCB from Schematic` dialog in KiCad 10.0.5. The options cover re-linking footprints by reference, replacing footprints with those in the schematic, and removing footprints that have no symbol. B5 stores a screenshot of the dialog (with `xwd`, if the image has it) or the label list from the manual section. Every run records the option state. The footprint-change edit and the remove edit run with each option on and off. The record states which option each gate edit needs. The default state (re-linking off) is the first run.

**Identity reader.** `scripts/identity.py` is a pure-Python reader of `.kicad_pcb` text. It does not import `pcbnew`, so it runs on the host and in the container. A snapshot holds:

- for each footprint: reference, value, library ID, UUID, schematic `path`, position, rotation, layer, and for each pad its number and net name
- for each track and via: UUID, net name, geometry, layer
- for each zone: UUID, net name, layer, and the polygon definition

The reader lists the top-level forms it understands and the forms it ignores (a documented list of volatile or irrelevant forms, such as `setup` and `title_block`). A form in neither list makes the reader exit with `identity.unparsed_class`. A reader that omits an object class never reports that identity is kept for that class.

```bash
uv run examples/pcb-trial/scripts/identity.py snapshot BOARD.kicad_pcb -o before.json
uv run examples/pcb-trial/scripts/identity.py compare before.json after.json --expect expected/EDIT.json --json
```

The comparison has no blanket exception such as "allow R1 to change". `expected/EDIT.json` lists the exact differences that the edit may cause, field by field. The comparison fails if a difference is not listed. It also fails if a listed difference does not occur. An allowed routing change names the object UUID and the expected connection. Tracks of a shared net are not exempt. The comparison normalizes only the fields on the documented volatile list.

Test of the reader (`tests/test_trial_identity.py`):

- positive tests on text fixtures and on real saved KiCad output from T3 and T7
- negative fixtures: an unauthorized move, a UUID change, a pad-net change, and the deletion of an unrelated track
- a fixture with an unknown top-level form gives `identity.unparsed_class`

Both source paths use the same edit sequence, and each edit starts from the same intermediate baseline.

**Gate edits.** These are the edits that the plan names. A path passes the gate only when all of them pass. The invariants are exact:

| Edit | Invariant |
|---|---|
| Change the value of `R2` | Only the value of `R2` changes |
| Reorder the symbols in the source | No persistent identity, placement, rotation, layer, connectivity or routing changes |
| Add `C2` | Exactly the expected new footprint and its connectivity appear. Nothing else changes. |
| Remove `D1` | Only the footprint `D1` and the routing objects named by UUID change |
| Change the footprint of `R1` | The footprint of `R1` changes. Its position and every unaffected object stay. |
| A second update with no edit | No persistent difference |

**Limit probes.** These edits measure limits. They can fail without failing the path. The record keeps each failure as a limit of the path.

| Edit | What the trial records |
|---|---|
| Rename `C1` to `C9` | Whether the footprint keeps its UUID, with re-linking on and off |
| Move `R2` to another sheet (a hierarchy change) | Whether the footprint keeps its UUID (KiCad issue 22572 says this can break the link) |
| Remove `D1` and add it again | Whether the footprint is new |

The gate does not change in B5. A failed gate edit means "not supported for that edit" in the record and in the B6 documents. A change of the gate needs a written decision of the lead.

**SKiDL structural comparison.** The trial compares two fresh SKiDL runs with no edit by structure: the parts, pins, nets, tags, and the generated identities (UUIDs and netlist time stamps). The record lists the tags and the generated identities. It does not assume that tags control every schematic identifier. The trial measures this.

**7. Intermediate board and final reference board (B5-4)**

Phase A (identity experiments) uses the intermediate baseline: the first update plus `scripts/layout.py`, which sets unequal positions and rotations and adds some track segments. The outputs of phase A are labeled "intermediate experiment data". The record keeps the full DRC exit code and the findings of each phase A board, even when the parity section is empty.

Phase B starts only when at least one path passed the gate. It makes the final reference board:

1. Finish the routing and the zones that apply (`scripts/layout.py --final`).
2. Refill the zones and save the board (`kicad-cli pcb drc --refill-zones --save-board ...`).
3. Run ERC, DRC and the schematic parity check on the saved revision. The criteria are: ERC exit 0, DRC exit 0 with no violations and no unconnected items, and an empty parity section. A waiver, if one is necessary, uses the B234 waiver record and binds to the exact bytes of the PCB and the schematic. The trial does not suppress all findings except parity.
4. Only then make the exports and their hashes (T10).

T10 exports use full commands. Each command names the input file, the output path, the layers, the units, the origin and the drill settings. T2 resolves each contract setting to an installed CLI option. The record has a table: contract setting, CLI option, value used. For example, the contract's drill zero suppression `leading` is resolved to the installed Excellon option, and no default is accepted just because a file exists.

The checks of T10 compare the exported files with the expected values of the trial, not with KiBot: the layer set, the file names with their suffixes, the drill files (plated and non-plated, hole count and diameters), and the placement rows (references, positions, rotations, sides). The expected values come from the layout parameters in `scripts/layout.py`, not from the exported files.

T13 builds a neutral package from the T10 files and the real reports of T5 and T9. The manifest status is `draft`. B5 selects no supplier, so it has no supplier evidence. The check `fab.profile_evidence` stays `pending`, and the trial invents no passed supplier-evidence check to obtain qualification. The B234 validator must accept the draft. A DRC-clean final board and a qualified supplier package are two separate results. B5 produces the first and not the second.

**8. Stop conditions and completion**

| ID | Condition | Action |
|---|---|---|
| S1 | The base image digest differs from the one above | Stop and report the actual digest. |
| S2 | The derived image build fails | Stop. Do not install packages by another route. |
| S3 | `kicad-cli version` is not 10.0.5 | Stop. |
| S4 | The native generator gives an invalid file after two changes | Mark the native path "untested". This is no evidence about KiCad. |
| S5a | The defective schematic has no expected ERC finding | The fixture or the rule is wrong. Correct the fixture. Do not judge the flag. |
| S5b | ERC reports a violation but the exit code is 0 | The exit behavior is a problem. Record `--exit-code-violations` as unreliable. |
| S6 | No path passes all gate edits | Stop P2. Keep the experiment logs and the partial exports as incomplete evidence. B5 promises no final reference export. |
| S7 | Both source paths fail a gate edit | Stop P2 and write a correction proposal, as the plan says. |
| S8 | A command needs a source other than the three allowed in section 4, or needs the network after setup | Stop and report the source. |
| S9 | The disk budget of 15 GB is near | Stop and report. Do not remove unrelated images. |
| S10 | A command would relabel files outside the temporary trial copy | Stop. |
| S11 | SKiDL 3.0.0 does not run under Python 3.13.5 | Record the error and mark the SKiDL path untested. The native path continues. |
| S12 | The identity gate passes, but the final board fails DRC, ERC, parity or an export comparison | B5 is incomplete. B6 does not continue under a parity-only gate. |

B5 is complete only when all of these hold:

- **C1.** T1 and T2 pass, and the command table exists.
- **C2.** At least one native or SKiDL fixture passes its load and connectivity checks.
- **C3.** At least one path passes all gate edits. Manual handoffs are named.
- **C4.** The final reference board passes the clean criteria of section 7, and the exports agree with the expected values.
- **C5.** The B234 validator accepts the draft package, and the draft status is explicit.

A GUI time limit produces an explicit manual handoff. It never produces an automated-pass claim. Unsupported paths and measured limits stay visible in the record.

**9. Deliverables**

- `examples/pcb-trial/` with the Containerfile, both sources, `rc.cir`, `requirements.in`, `requirements.lock`, `toolchain.lock.json`, `scripts/`, the expected values, and the project and package files that real output produced.
- `docs/reviews/b5-trial-claude.md`. It holds these items:
  - every command with its exit code
  - the tool versions, the format versions with their evidence, and the dependency versions
  - the result row of each of U1 to U6, with separate U4 rows for each input
  - the identity tables (gate edits and limit probes) for both paths
  - the dialog option table and the contract-setting to CLI-option table
  - the manual handoffs with their operator
  - the list of unsupported paths and untested paths
- `docs/reviews/b5-files.sha256` with the hashes of all changed files. The log files stay in the scratchpad and the record names them.
- Tests: `tests/test_pcb_tools.py` stays green. B5 adds `tests/test_trial_identity.py` (host, no KiCad). A gated test file for the container steps shows a visible `unavailable` status when `podman` or the image is absent.

**10. Order**

T0a and T0b, T1 and T2, the identity reader with its tests (host), T3, T4 to T6, U4 and T7, T8, then phase B (T9 and T10), T11, T12, and T13. The calendar time depends on U4 and on the fallback that needs a person.
