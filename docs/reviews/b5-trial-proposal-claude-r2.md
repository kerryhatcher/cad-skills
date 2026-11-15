# B5 trial execution proposal (Claude), revision 2

Date: 2026-11-14.

Status: proposal only. I change no implementation file. The first version stays as `b5-trial-proposal-claude-r1.md` (SHA-256 `ccac378e4526433834a31f21a3306ab098fe732289407a40cc6c256c27433b6c`). No research cycle was necessary. The facts come from the lead's probe messages, `tool-trial-preparation-claude.md`, and the frozen B1 to B234 code.

**1. Aim and limits**

B5 answers four questions with measured results:

1. Do the fixed tools run in the container and give the exit codes and files that the contracts expect?
2. Which method updates a board from a schematic, and what does it do to footprint identity?
3. Does the SKiDL path keep identity, and what does it cost?
4. Do the B234 validators accept a project and a package that real tool output produces?

B5 does not choose a supplier, order a board, or test a physical board. It keeps tscircuit and atopile out.

**2. What changed in this revision**

| Lead item | Change | Section |
|---|---|---|
| 1 | The native path does not depend on SKiDL or on a file from a person. A script makes an original minimal schematic from the installed KiCad libraries. KiCad must load it, and its netlist must equal the expected connectivity. | 3 |
| 2 | The sources that B5 may use are the official fixed images, the Debian package source, and PyPI for pinned SKiDL dependencies. A hashed lock file records the versions. Runs after setup are offline. | 4 |
| 3 | U2 is explicit. U4 is the scripted mechanism. U1, U2 and U3 are the three update inputs. Each of U1 to U6 has a result row. | 5 |
| 4 | The edits have two classes: gate edits (agreed identity gate) and limit probes (measured limits). The gate does not change. The trial records the dialog options for footprint replacement, deletion and relinking. | 6 |
| 5 | This revision rewrites the prose findings that were valid. | all |

**3. Fixed environment and fixtures**

| Item | Value |
|---|---|
| Base image | `ghcr.io/inti-cmnb/kicad10_auto_full@sha256:96e75f885b15617c6b38aef11db7856a93f4367cab7a0b6c2b30465557619330` (local) |
| Measured by the lead | KiCad 10.0.5, KiBot 1.9.1, KiAuto 2.3.10, Python 3.13.5. `pcbnew` prints 3 assertion messages when imported and has no `BOARD_NETLIST_UPDATER`. The image has no ngspice, no `uv`, and no 3D models. |
| Old image 1.9.0 | Evidence only. B5 does not use it. |
| uv | The static binary from the official image `ghcr.io/astral-sh/uv@sha256:e85be844203885286c60ffad8a858d48afb6c5a5c237ca0e67f12e74b8f174b1` (uv 0.12.5). The host `uv` crashes in the container. |
| ngspice | Debian 13 package `ngspice` 44.2+ds-1 |
| Python rule | `uv run --no-project --no-config --python /usr/bin/python3 python SCRIPT`. Direct PEP 723 execution hides `pcbnew` from the script. |
| Mounts | Mount a temporary copy of the trial directory with `:Z`. Never relabel the repository or other files. |
| Disk | Stay below the 15 GB budget. The image uses 3.95 GB. |

Board: two layers, 40 mm by 25 mm, offset origin. Parts: `J1` (header 1x02), `D1` (LED 0603, asymmetric and polarized), `R1` (series resistor), `R2` (10 kohm), `C1` (100 nF), `MH1` and `MH2` (mounting holes at unequal positions). The RC network has an analytic result: the time constant is 1.000 ms, and the voltage at one time constant for a 3.3 V step is 2.086 V. The simulation must agree within 1%. A deliberately wrong capacitor value must fail the same test.

**Native fixture (no SKiDL, no supplied file).** `scripts/make_native.py` makes the schematic and the PCB in the container. It uses only the installed KiCad libraries and the text format:

1. It reads the version number from the header of the installed library `Device.kicad_sym`.
2. It copies the symbols `Device:R`, `Device:C`, `Device:LED`, `Connector_Generic:Conn_01x02` and `Mechanical:MountingHole` as text into `lib_symbols`.
3. It places one instance for each part. It uses UUIDs from `uuid5` of the reference, so two runs give the same file. It connects the pins with net labels at the pin ends. It computes the pin positions from the symbol text.
4. It sets the footprint property of each symbol (`Resistor_SMD:R_0603_1608Metric` and similar).
5. It writes a minimal `.kicad_pro` and a `.kicad_pcb` with the same version number, a 40 mm by 25 mm outline on `Edge.Cuts`, and no footprints.

KiCad must load these files. Step T3 proves it:

- `kicad-cli sch erc` reads the schematic and writes a report.
- `kicad-cli sch export netlist` writes a netlist. A script compares its pin-to-net map with `expected/netlist.json`. The map must be equal.
- `kicad-cli pcb drc` reads the PCB and writes a report.

If KiCad rejects a file, the error text is the result. Then I change the script and run the step again. After two failed corrections, stop condition S4 applies.

**SKiDL fixture.** `skidl/circuit.py` builds the same circuit with a tag on each part. It uses the same references and footprints.

**Baseline layout.** `scripts/layout.py` edits the PCB text after the first update. It sets unequal positions and rotations, and it adds straight track segments. This baseline is the start of every edit test. Unrouted items can remain. The parity section of the DRC report must be empty.

Files: `examples/pcb-trial/{native,skidl}/`, `rc.cir`, `requirements.lock`, `scripts/`, `expected/`. Generated output goes to `out/`, which Git ignores.

**4. Sources, setup and offline runs**

B5 may use these sources only:

1. the official fixed images above (base image and `uv` image)
2. the Debian package source for `ngspice` and its dependencies
3. PyPI for SKiDL and its pinned dependencies

Setup (online, one time):

```bash
# T0a: resolve and hash the SKiDL dependencies
podman run --rm -v "$TRIAL:/work:Z" ghcr.io/astral-sh/uv@sha256:e85be84... \
  pip compile --python-version 3.13 --generate-hashes --no-header skidl==3.0.0 -o /work/requirements.lock
# T0b: build the derived image
podman build -t localhost/cad-skills-trial:b5 -f examples/pcb-trial/Containerfile examples/pcb-trial
```

The Containerfile copies `uv`, installs `ngspice=44.2+ds-1`, and builds a virtual environment `/opt/trial-venv` from `requirements.lock` with `uv pip install --require-hashes` and `--system-site-packages`. After setup, every run uses `podman run --network none`. A step that needs the network after setup is a stop condition (S8).

`requirements.lock` is in the repository and holds the version and the hashes of each package. The record `b5-trial-claude.md` repeats the package versions and the SHA-256 of `requirements.lock`. `examples/pcb-trial/toolchain.lock.json` holds `execution: container`, the base digest, the derived image ID, the tools with measured versions, and the libraries with their licenses. The B234 validator must accept it.

**5. Steps**

All steps after T0 run as `podman run --rm --network none -v "$TRIAL:/work:Z" localhost/cad-skills-trial:b5 COMMAND`. Each step records the command, the exit code, and the hash of the output.

| Step | Command (inside the container) | Pass condition |
|---|---|---|
| T1 versions | `kicad-cli version`, `kibot --version`, `eeschema_do --version`, `ngspice -v`, `uv --version`, `python3 --version` | Equal the measured versions |
| T2 help | `--help` of `sch erc`, `pcb drc`, `pcb export gerbers`, `drill`, `pos`, `step`, `dxf`, `ipcd356` | The options that the plan names exist. Record the exact flag names. |
| T3 native fixture | `python3 scripts/make_native.py`, then the three commands in section 3 | Both files load. The netlist map equals `expected/netlist.json`. |
| T4 SKiDL schematic | `/opt/trial-venv/bin/python skidl/circuit.py` with `KICAD10_SYMBOL_DIR=/usr/share/kicad/symbols`, twice in two fresh directories | A `.kicad_sch` and a netlist. The two runs are equal. |
| T5 ERC exit | `kicad-cli sch erc --exit-code-violations --severity-all --format json -o erc.json FILE` on a good and a defective schematic | Exit 0 for the good file. Nonzero for the defective file. |
| T6 SKiDL `ERC()` exit | A run with a deliberately wrong circuit | Record the exit code. The B6 wrapper must turn a detected violation into a failure. |
| T7 board update | U1 to U6 (below) | One result row for each of U1 to U6 |
| T8 DRC and parity | `kicad-cli pcb drc --schematic-parity --exit-code-violations --severity-all --format json -o drc.json FILE` | The parity section is empty after a correct update. It has an entry after a deliberate defect. |
| T9 exports | `kicad-cli pcb export gerbers`, `export drill --excellon-separate-th`, `export pos --format csv --units mm --side both`, `export step`, `export dxf`, `export ipcd356` | The files exist, are not empty, and agree with the export settings of the project |
| T10 KiBot | `kibot -c trial.kibot.yaml -b FILE.kicad_pcb -e FILE.kicad_sch` | Same layer set, drill split and position columns as T9. Record each difference. |
| T11 simulation | `ngspice -b rc.cir -o rc.log` | The value is within 1% of 2.086 V |
| T12 contracts | On the host: `uv run contracts/validate.py --project PROJECT --package PACKAGE --json` | Exit 0 for a package built from the T9 files and the real reports |
| T13 no 3D models | `kicad-cli pcb export step` | Record the output with no component models. This is a known limit. |

T12 builds the package with a short script that uses the B234 helpers. The evidence files cite the real report files of T5, T8 and T9 with their hashes.

**6. Board update methods U1 to U6**

The KiCad manual states that `Update PCB from Schematic` matches footprints by UUID, and that re-linking by reference is off by default. The trial measures what this does.

| ID | Input | Mechanism | Time box |
|---|---|---|---|
| U1 | The native schematic | U4 first. A person does the GUI operation only if U4 fails for this input. | 30 minutes |
| U2 | The schematic that SKiDL `generate_schematic()` writes | The same as U1 | 30 minutes |
| U3 | The SKiDL netlist with tags (time-stamp matching) | The same as U1 | 30 minutes |
| U4 | The scripted GUI mechanism itself | `scripts/gui_update.py` starts Xvfb, opens `pcbnew`, sends F8 and the dialog keys with `xdotool`, and saves the board. It is the automation for U1 to U3. | 1 hour to build |
| U5 | The IPC API | A session of the GUI in the container | 30 minutes |
| U6 | `pcbnew` Python | Look for a netlist updater. The lead's probe found none, so this is a recorded negative. | 10 minutes |

The record has one result row for each of U1 to U6. U4 has one row that counts its runs (success and failure) for each of U1, U2 and U3. The record marks a method that needs a person as manual. It gives the operator and the before-and-after hashes. B5 never claims unattended board generation unless U4 passes the gate edits twice in a row for the same input. If a person must act, the request is a normal task step for the lead or the user.

**Dialog options.** The trial records the exact labels and defaults of the options of the `Update PCB from Schematic` dialog in KiCad 10.0.5. The options cover re-linking footprints by reference, replacing footprints with those in the schematic, and removing footprints that have no symbol. B5 stores a screenshot of the dialog (with `xwd`, if the image has it) or the label list from the manual section. Every run records the option state. The footprint-change edit and the remove edit run with each option on and off. The record states which option each gate edit needs and what each option does to identity. The default state (re-linking off) is the first run.

**7. Identity measurement**

`scripts/identity.py` is a pure-Python reader of `.kicad_pcb` text. It does not import `pcbnew`, so it runs on the host and in the container.

```bash
uv run examples/pcb-trial/scripts/identity.py snapshot BOARD.kicad_pcb -o before.json
uv run examples/pcb-trial/scripts/identity.py compare before.json after.json --allow-changed R1 --allow-added C2 --json
```

A snapshot holds, for each footprint: reference, value, library ID, UUID, schematic `path`, position, rotation, and layer. It holds each track, via and zone with its net name and geometry. The comparison reports every difference that the allowed list does not cover. Exit codes follow the B1 policy.

Both source paths use the same edit sequence, and each edit starts from the same baseline layout.

**Gate edits.** These are the edits that the plan names. A path passes the gate only when all of them pass.

| Edit | Allowed difference |
|---|---|
| Change the value of `R2` | The value of `R2` |
| Reorder the symbols in the source | None |
| Add `C2` | One new footprint, unplaced |
| Remove `D1` | The footprint `D1` and its tracks |
| Change the footprint of `R1` | The footprint of `R1`, with its position kept |
| A second update with no edit | None |

**Limit probes.** These edits measure limits. They can fail without failing the path. The record keeps each failure as a limit of the path.

| Edit | What the trial records |
|---|---|
| Rename `C1` to `C9` | Whether the footprint keeps its UUID, with re-linking on and off |
| Move `R2` to another sheet (a hierarchy change) | Whether the footprint keeps its UUID (KiCad issue 22572 says this can break the link) |
| Remove `D1` and add it again | Whether the footprint is new |

The gate does not change in B5. A failed gate edit means "not supported for that edit" in the record and in the B6 documents. A change of the gate needs a written decision of the lead. For the SKiDL path the trial also compares two fresh runs with no edit. The UUIDs and the netlist time stamps must be equal. Tags must be the only source of stable part identity.

Pass condition for a path: all gate edits pass, T8 gives an empty parity section after each update, and the second update changes nothing.

**8. Stop conditions**

| ID | Condition | Action |
|---|---|---|
| S1 | The base image digest differs from the one above | Stop and report the actual digest. |
| S2 | The derived image build fails | Stop. Do not install packages by another route. |
| S3 | `kicad-cli version` is not 10.0.5 | Stop. |
| S4 | KiCad rejects the native fixture after two corrections of `make_native.py` | Stop the native path. Report the error text. |
| S5 | T5 gives exit 0 for the defective schematic | Stop the ERC wrapper work. Record `--exit-code-violations` as unreliable. |
| S6 | U4, U1, U2 and U3 all fail | Record "no tested update method". B5 ends with the identity tool and the reference exports. B6 does not claim board generation. |
| S7 | Both source paths fail a gate edit | Stop P2 and write a correction proposal, as the plan says. |
| S8 | A command needs a source other than the four allowed in section 4, or needs the network after setup | Stop and report the source. |
| S9 | The disk budget of 15 GB is near | Stop and report. Do not remove unrelated images. |
| S10 | A command would relabel files outside the temporary trial copy | Stop. |
| S11 | SKiDL 3.0.0 does not run under Python 3.13.5 | Record the error and mark the SKiDL path untested. The native path continues. |

**9. Deliverables and acceptance**

- `examples/pcb-trial/` with the Containerfile, both sources, `rc.cir`, `requirements.lock`, `toolchain.lock.json`, `scripts/`, the expected values, and the B234 project and package files that real output produced.
- `docs/reviews/b5-trial-claude.md`. It holds these items:
  - every command with its exit code
  - the tool versions and the dependency versions
  - the result row of each of U1 to U6
  - the identity tables (gate edits and limit probes) for both paths
  - the dialog option table
  - the manual steps with their operator
  - the list of unsupported paths
- `docs/reviews/b5-files.sha256` with the hashes of all changed files. The log files stay in the scratchpad and the record names them.
- Tests: `tests/test_pcb_tools.py` stays green. B5 adds `tests/test_trial_identity.py` for `identity.py` (fixture boards in text, no KiCad). A gated test file for the container steps shows a visible `unavailable` status when `podman` or the image is absent.

Acceptance: at least one source path passes the gate. Manual steps and unsupported paths are explicit. T12 passes on the host. The record states no result that a command did not produce.

**10. Order**

T0a and T0b, T1 and T2, the identity tool with its text-fixture tests (host), T3, T4 to T6, U4, T8 to T11, then T12. The calendar time depends on U4 and on the fallback that needs a person.
