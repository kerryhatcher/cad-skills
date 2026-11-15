# B5 checkpoint 1 record (Claude)

Date: 2026-11-14.

Scope: the setup and the native fixture of the trial, under the accepted proposal revision 4 (SHA-256 `458ff984c4a552f2a7a339ec937f6a066b187bb61ea2c210b3cfdba8dea5c0f6`). This record is a checkpoint, not the final trial record. I made no commit, no push, no supplier contact, and no change to a B234 file.

The files in `b5-setup-files.sha256` stay unchanged during the focused review. If a reviewed helper must change, I report that dependency first.

**1. Temporary paths**

| Item | Path |
|---|---|
| Scratchpad root | `/tmp/claude-1000/-mnt-storage-projects-cad-skills/31456ff4-3cc5-4474-895e-358d2be1c713/scratchpad` |
| Trial copy (mounted with `:Z`) | `<scratchpad>/b5/trial` |
| Step logs (`*.cmd`, `*.out`, `steps.txt`) | `<scratchpad>/b5/logs` |
| Frozen step list at this checkpoint | `<scratchpad>/b5/logs/steps.checkpoint1.txt` (SHA-256 `46e9e8a5d2d656d391751d417f1890b213cd80af2d59d8c59d0ac2925dad0e6d`) |
| Environment helper | `<scratchpad>/b5/env.sh` and `<scratchpad>/b5/image_id.env` |
| Repository files | `examples/pcb-trial/` |

A reboot can clear the scratchpad. The commands and the output hashes are in the step logs.

**2. Setup results**

| Step | Result |
|---|---|
| Base image | `ghcr.io/inti-cmnb/kicad10_auto_full@sha256:96e75f885b15617c6b38aef11db7856a93f4367cab7a0b6c2b30465557619330` (local, used with `--pull=never`) |
| uv image | `ghcr.io/astral-sh/uv@sha256:e85be844203885286c60ffad8a858d48afb6c5a5c237ca0e67f12e74b8f174b1` (local) |
| T0a, as written in the proposal | **Failed, exit 2.** The uv image has no libc binaries, so uv could not find a Python interpreter. The log is `T0a.out`. |
| T0a, changed | `Containerfile.uv` (the same two fixed images, base plus the uv binary) built as `localhost/cad-skills-trial-uv:b5` (ID `5a445339421b…`). `uv pip compile /work/requirements.in --python /usr/bin/python3 --python-version 3.13.5 --generate-hashes` ran in it with PyPI as the source. Exit 0. |
| `requirements.lock` | 28 pinned packages with hashes. SHA-256 `f505b04d9bc3588c10d66954aba4b7eab6f6f8ad0cbf517b39b97fa544b7de15`. Includes `skidl==3.0.0`, `numpy==2.5.4`, `matplotlib==3.11.2`, `kinet2pcb==1.1.4`, `inspice==1.7.0.7`. |
| T0b, derived image | Built from `Containerfile` (exit 0). ID `d881df4ef3e2ec76995f4070596550db118b23e7f6db9017f09a418c44c4b1c2`, size 4415434534 bytes. The lead measured the same ID and size. |
| ID normalization | The raw output had no `sha256:` prefix. The 64-hexadecimal check passed. The record digest is `sha256:d881df4e…c1c2`. |
| Import probe | `import skidl, pcbnew` through `uv run --no-project --no-config --offline --python /opt/trial-venv/bin/python`: exit 0 online, and exit 0 with `--network none`. Both outputs have the same hash. The output keeps three `PROPERTY_ENUM` assertion messages, two `fp-lib-table` warnings, and `pcbnew 10.0.5-unknown`. |
| Versions | KiCad 10.0.5, KiBot 1.9.1, KiAuto 2.3.10, ngspice 44.2, uv 0.12.5 (musl), Python 3.13.5 |
| T2 discovery | `--help` of 11 `kicad-cli` subcommands: exit 0. Saved in `<logs>/help/`. The Excellon option `--excellon-zeros-format suppressleading` maps the contract setting `leading`. `--excellon-separate-th` maps `separate_files`. |

**3. Native fixture results**

| Check | Result |
|---|---|
| Format versions | KiCad 10.0.5 `sch upgrade --force` and `pcb upgrade --force` on stubs give a schematic version `20260306` and a PCB version `20260206`. The installed symbol library header is `20251024`. The installed templates are KiCad 9 files (`20250114`, `20241229`). The three values differ. The generator uses the two values that KiCad wrote. |
| Generator | `scripts/trial_native_writer.py` (name `cad_skills_trial_native`). It uses the installed symbol libraries and the text format. It needs no SKiDL and no file from a person. It worked on its first full run. It needed one change: the PCB stub needs two copper layers (the first stub failed with "1 is not a valid layer count"). |
| ERC | `kicad-cli sch erc --exit-code-violations --severity-all --format json`: exit 0, 0 violations |
| Netlist | `kicad-cli sch export netlist --format kicadxml`: exit 0. Four nets: `/GND`, `/N_LED`, `/N_RC`, `/VIN` (KiCad adds a leading slash to a local label). |
| `check_native.py` | 7 symbol instances with the expected references, values and footprints. 10 pin points equal the hand-written values in `expected/pins.json`. The complete 10-pin net map equals `expected/netlist.json`. Exit 0. |
| Negative check | One label renamed in a copy: the same check fails with exit 1 and reports the map difference |
| DRC on the empty PCB | `kicad-cli pcb drc --exit-code-violations --severity-all --format json`: exit 0, 0 violations, 0 unconnected items |

The native path passed the fixture checks of the plan (C2) at the first full run. The correction limit of two changes was not used up.

**4. Failed commands and deviations (kept as evidence)**

1. T0a as written failed with exit 2 (above). The change is `Containerfile.uv`. Both images and the PyPI source are allowed sources of the proposal.
2. A first T1 loop used unsplit arguments (the shell passed `kicad-cli version` as one word). Seven commands failed with exit 127. I reran T1 correctly. The logs of the failed run are overwritten by the rerun, but the lines stay in this record.
3. A first T3 line had a typo (`$=UVPY`) and ran no real command. I reran it.
4. The first run of `T1a` and `T1b` failed with exit 126 because the common command had no `/work` mount for the probe. The helper `RUN` and `RUN_ONLINE` now set `-w /work -v "$TRIAL:/work:Z"`.
5. The first PCB stub failed (one copper layer). Fixed in the generator.
6. Python rule: I read one JSON file with the host `python3` in a shell command, not with `uv`. Later reads use `uv`.
7. A probe (`scripts/gui_probe.sh`) is an exploration script. It is not in the setup manifest and is not part of a result.

**5. Hash manifest**

`docs/reviews/b5-setup-files.sha256` lists 15 files: the Containerfiles, the requirements, the parser, the writer, the checker, the expected data, and the generated native fixture. Its SHA-256 is `317f73269e6326043ab6c692fd94cb8f56782472ecaaa5eb831b4d1856eca1b0`. Verify it with:

```bash
cd /mnt/storage/projects/cad-skills && sha256sum -c docs/reviews/b5-setup-files.sha256
```

**6. Limits**

- The checks used one host and one image.
- The native fixture has not yet been through any update experiment. It is only the starting point.
- The first GUI probe shows that `pcbnew` starts in Xvfb and loads the fixture board. A first-run setup dialog appears because the container user has no `kicad_common.json`. The next step handles it. That is an experiment, not a result.
- STE lint was not run on this record.

**7. Next steps**

The SKiDL probes (T4 to T6), the identity reader (in separate files), and the GUI experiments (U4) run against temporary project copies. The setup files stay unchanged.
