# B5 trial execution proposal (Claude)

Date: 2026-11-14.

Status: proposal only. I change no implementation file. No research cycle was necessary. The facts below come from the lead's probe messages, `tool-trial-preparation-claude.md`, and the frozen B1 to B234 code.

**1. Aim and limits**

B5 answers four questions with measured results:

1. Do the fixed tools run in the container and give the exit codes and files that the contracts expect?
2. Which method updates a board from a schematic, and what does it do to footprint identity?
3. Does the SKiDL path keep identity, and what does it cost?
4. Do the B234 validators accept a project and a package that real tool output produces?

B5 does not choose a supplier, order a board, or test a physical board. It uses no new approval gate. It keeps tscircuit and atopile out.

**2. Fixed environment**

| Item | Value |
|---|---|
| Base image | `ghcr.io/inti-cmnb/kicad10_auto_full@sha256:96e75f885b15617c6b38aef11db7856a93f4367cab7a0b6c2b30465557619330` (already local) |
| Measured by the lead | KiCad 10.0.5, KiBot 1.9.1, KiAuto 2.3.10, Python 3.13.5. `pcbnew` prints 3 assertion messages when imported. It has no `BOARD_NETLIST_UPDATER`. It has no ngspice, no `uv`, and no 3D models. |
| Old image 1.9.0 | Evidence only. B5 does not use it. |
| uv | The static binary from the official image `uv` 0.12.5, digest `sha256:e85be844203885286c60ffad8a858d48afb6c5a5c237ca0e67f12e74b8f174b1`. The host `uv` crashes in the container. |
| ngspice | Debian 13 package `ngspice` 44.2+ds-1, installed in a derived image |
| Python rule | `uv run --no-project --no-config --python /usr/bin/python3 python SCRIPT`. Direct PEP 723 execution hides `pcbnew` from the script. |
| Mounts | Mount a temporary copy of the trial directory with `:Z`. Never relabel the repository or other files. |
| Disk | Stay below the 15 GB budget. The image uses 3.95 GB. The derived image adds a small layer. |

Derived image (`examples/pcb-trial/Containerfile`):

```text
FROM ghcr.io/astral-sh/uv@sha256:e85be844203885286c60ffad8a858d48afb6c5a5c237ca0e67f12e74b8f174b1 AS uv
FROM ghcr.io/inti-cmnb/kicad10_auto_full@sha256:96e75f885b15617c6b38aef11db7856a93f4367cab7a0b6c2b30465557619330
COPY --from=uv /uv /usr/local/bin/uv
RUN apt-get update && apt-get install -y --no-install-recommends ngspice=44.2+ds-1 && rm -rf /var/lib/apt/lists/*
```

Build and record:

```bash
podman build -t localhost/cad-skills-trial:b5 -f examples/pcb-trial/Containerfile examples/pcb-trial
podman image inspect --format '{{.Id}} {{.Size}}' localhost/cad-skills-trial:b5
```

B5 writes `examples/pcb-trial/toolchain.lock.json` with `execution: container`, the base digest, the derived image ID, and the measured tool versions. The B234 validator must accept it.

**3. Fixture**

A two-layer board of 40 mm by 25 mm, as in the B234 test project.

| Part | Reference | Use |
|---|---|---|
| Header 1x02 | `J1` | Power input |
| LED 0603 | `D1` | Asymmetric polarized part |
| Resistors 0603 | `R1`, `R2` | Series resistor and RC resistor (10 kohm) |
| Capacitor 0603 | `C1` | RC capacitor (100 nF) |
| Mounting holes | `MH1`, `MH2` | Unequal positions |

The origin is offset. The RC network has an analytic result: the time constant is 1.000 ms, and the voltage at one time constant is 63.2% of the step. Simulation (`ngspice -b rc.cir`) must give 2.086 V (3.3 V step) within 1%. A deliberately wrong capacitor value must fail the test.

Native path source: a KiCad 10 schematic. The first schematic is the file that SKiDL `generate_schematic()` writes in the container. B5 then freezes that file as the native source. Edits to it use a text-edit script, not the GUI. If SKiDL cannot write the file, the stop condition S4 applies.

Files: `examples/pcb-trial/{native,skidl}/`, `rc.cir`, `scripts/identity.py`, `scripts/edit_native.py`, `expected/`. Generated output goes to `out/`, which Git ignores.

**4. Steps and commands**

All steps run as `podman run --rm -v "$TRIAL:/work:Z" localhost/cad-skills-trial:b5 COMMAND`, where `$TRIAL` is a temporary copy of the trial directory. Each step records the command, the exit code, and the output hash in `docs/reviews/b5-trial-claude.md`.

| Step | Command (inside the container) | Pass condition |
|---|---|---|
| T1 versions | `kicad-cli version`, `kibot --version`, `eeschema_do --version`, `ngspice -v`, `uv --version`, `python3 --version` | Equal the measured versions |
| T2 help | `kicad-cli sch erc --help`, `kicad-cli pcb drc --help`, `kicad-cli pcb export gerbers --help`, `... drill --help`, `... pos --help`, `... step --help`, `... dxf --help` | The options that the plan names exist. Record the exact flag names. |
| T3 SKiDL schematic | `uv run --no-project --no-config --python /usr/bin/python3 --with skidl==3.0.0 python skidl/circuit.py` with `KICAD10_SYMBOL_DIR=/usr/share/kicad/symbols` | Writes a `.kicad_sch` and a netlist. Run it twice in two fresh directories and compare. |
| T4 ERC exit | `kicad-cli sch erc --exit-code-violations --severity-all --format json -o erc.json board.kicad_sch` on the good and on a defective schematic | Exit 0 on the good file. Nonzero on the defective file. |
| T5 SKiDL `ERC()` exit | A Python run with a deliberately wrong circuit | Document the exit code. The B6 wrapper must turn a detected violation into a failure. |
| T6 board update | Methods U1 to U6 (section 5) | One result for each method |
| T7 DRC and parity | `kicad-cli pcb drc --schematic-parity --exit-code-violations --severity-all --format json -o drc.json board.kicad_pcb` | Exit 0 after a correct update. Nonzero after a deliberate defect. |
| T8 exports | `kicad-cli pcb export gerbers`, `export drill --excellon-separate-th`, `export pos --format csv --units mm --side both`, `export step`, `export dxf`, `export ipcd356` | Files exist, are not empty, and match the export settings of the project |
| T9 KiBot | `kibot -c trial.kibot.yaml -b board.kicad_pcb -e board.kicad_sch` | Same layer set, drill split, and position columns as T8. Differences are recorded. |
| T10 simulation | `ngspice -b rc.cir -o rc.log` | The measured value is within 1% of 2.086 V |
| T11 contracts | On the host: `uv run contracts/validate.py --project PROJECT --package PACKAGE --json` | Exit 0 for a package built from the T8 files and real reports |
| T12 no 3D models | `kicad-cli pcb export step` | Record the output with no component models. This is a known limit, not a failure. |

T11 builds the package with a short script that uses the B234 helpers. The evidence files cite the real report files of T4, T7 and T8 with their hashes.

**5. Board update methods**

The KiCad manual confirms that `Update PCB from Schematic` matches footprints by UUID. Re-linking by reference is off by default. The trial measures what this does.

| ID | Method | Operator | Time box |
|---|---|---|---|
| U4 | A script in Xvfb sends F8 and the update dialog keys with `xdotool`, in the style of `pcbnew_do` | Automatic | 1 hour |
| U1 | The same GUI operation in a display session of the container | A person, only if U4 fails and a viewer is present in the image | 30 minutes |
| U3 | A netlist import in the GUI, for the SKiDL netlist with tags | Same as U1 | 30 minutes |
| U5 | The IPC API against a GUI session in the container | Automatic | 30 minutes |
| U6 | `pcbnew` Python: look for any netlist updater | Automatic | 10 minutes. The lead's probe found no `BOARD_NETLIST_UPDATER`, so this is a recorded negative. |

Order: U4 first, because it is the only automatic candidate with evidence of a mechanism. The record states for each method: command, exit code, files changed, and the identity result. A method that needs a person is recorded as manual, with the operator and the before-and-after hashes. B5 never claims unattended board generation unless U4 passes the identity tests twice in a row.

If a person must act, the request is a normal task step for the lead or the user. It is not a new approval gate.

**6. Identity measurement**

`scripts/identity.py` is a pure-Python reader of `.kicad_pcb` text. It does not import `pcbnew`, so it runs on the host and in the container. Commands:

```bash
uv run examples/pcb-trial/scripts/identity.py snapshot BOARD.kicad_pcb -o before.json
uv run examples/pcb-trial/scripts/identity.py compare before.json after.json --allow-changed R1 --allow-added C2 --json
```

A snapshot holds, for each footprint: reference, value, library ID, UUID, schematic `path`, position, rotation, and layer. It holds each track, via and zone with its net name and geometry. The comparison reports every difference that the allowed list does not cover. Exit codes follow the B1 policy.

The native path and the SKiDL path use the same edit sequence. Each edit starts from the same routed board.

| Edit | Allowed difference |
|---|---|
| Change the value of `R2` | The value of `R2` |
| Reorder the symbols in the source file | None |
| Add `C2` | One new footprint, unplaced |
| Remove `D1` | The footprint `D1` and its tracks |
| Change the footprint of `R1` | The footprint of `R1` only, with its position kept |
| Rename `C1` to `C9` | Reference only, if the update keeps the UUID |
| Move `R2` to another sheet | None (KiCad issue 22572 says this can break the link) |
| No edit, a second update | None |

A footprint that keeps its UUID, position, rotation, and tracks passes. Each failure is a recorded limit of the path, not a hidden step. For the SKiDL path the trial also compares two fresh runs without any edit: the UUIDs and the netlist time stamps must be equal. Tags must be the only source of the stable part identity.

Pass condition for a path: all edits pass the allowed-difference test, T7 gives exit 0 after each update, and the second update changes nothing.

**7. Stop conditions**

| ID | Condition | Action |
|---|---|---|
| S1 | The base image digest differs from the one above | Stop. Report the actual digest. |
| S2 | The derived image build fails | Stop. Do not install packages by another route. |
| S3 | `kicad-cli version` is not 10.0.5 | Stop. |
| S4 | SKiDL 3.0.0 does not run under Python 3.13.5, or cannot write the schematic | Record the error. Try the native path from a KiCad-saved schematic that a person supplies. Mark the SKiDL path untested. |
| S5 | T4 gives exit 0 for the defective schematic | Stop the ERC wrapper work. Record `--exit-code-violations` as unreliable. |
| S6 | U4, U1 and U3 all fail | Record "no tested update method". B5 ends with the identity tool and the reference exports. B6 does not claim board generation. |
| S7 | Both source paths fail the identity tests | Stop P2 and write a correction proposal, as the plan says. |
| S8 | A command needs a network source other than the Debian mirror for the `ngspice` package | Stop and report the source. |
| S9 | The disk budget of 15 GB is near | Stop and report. Do not remove unrelated images. |
| S10 | A command would relabel files outside the temporary trial copy | Stop. |

**8. Deliverables and acceptance**

- `examples/pcb-trial/` with the Containerfile, both sources, `rc.cir`, `scripts/`, the expected values, and the B234 project and package files that real output produced.
- `docs/reviews/b5-trial-claude.md`: every command with its exit code, versions, the result of U1 to U6, the identity table for both paths, the manual steps with their operator, and the list of unsupported paths.
- `docs/reviews/b5-files.sha256` with the hashes of all changed files, and the log files in the scratchpad named in the record.
- Tests: `tests/test_pcb_tools.py` stays green. B5 adds `tests/test_trial_identity.py` for `identity.py` (fixture boards in text, no KiCad) and a gated test file for the container steps that skips with a visible `unavailable` status when `podman` or the image is absent.

Acceptance: at least one source path passes. Manual steps and unsupported paths are explicit. T11 passes on the host. Nothing in the record says a result that no command produced.

**9. Estimate and order**

Order: T1 and T2, then the identity tool and its text-fixture tests (they run on the host), then T3 to T5, then U4, then T7 to T10, then T11. The calendar time is set by U4 and the person-in-the-loop fallback.
