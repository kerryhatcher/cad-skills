# Tool-trial preparation: headless board update (Claude)

Date: 2026-11-13.

Scope: this file records findings on the question "Can a tool run `Update PCB from Schematic` without a person, and does it keep footprint identity?" It supports batch B5 of `docs/reviews/implementation-proposal-claude.md`. I changed no implementation file. I did not start a second image pull.

**1. Short answer**

- No official tool that I examined supplies a headless `Update PCB from Schematic` for KiCad 10.
- KiAuto and KiBot do not supply one. They drive KiCad for reports and exports.
- The KiCad 10 `kicad-cli` has no command for it.
- The KiCad IPC API of versions 9 and 10 needs a running KiCad GUI. The page that I read does not list a netlist-update command.
- A GUI-automation step in the container is possible in principle (KiAuto uses Xvfb and xdotool). Nobody documents it for this operation. It is an experiment, not a fact.
- Identity-preserving sync is a property of KiCad's own update dialog. I have no primary source for the exact matching rule. The trial must measure it.

The host has no Xvfb. This does not decide the question, because the container can include one. I did not inspect the container. The pull of `ghcr.io/inti-cmnb/kicad10_auto_full:1.9.0` was still running when I finished (process 1750576).

**2. What each source says**

Confidence labels: **Source** means that I read the statement in a primary document or its source code. **Secondary** means a forum, a mailing list, or a third-party summary. **Unknown** means that I found no statement.

| Subject | Finding | Confidence |
|---|---|---|
| `kicad-cli` 10 command list | The `pcb` group has `drc`, `export` (23 formats), `import`, `render`, and `upgrade`. The `sch` group has `erc`, `export` (including `netlist`), and `upgrade`. There is also `jobset run`. `pcb import` converts non-KiCad boards. `sch export netlist` writes a file. No command updates a board from a schematic. | **Source** ([KiCad 10 CLI](https://docs.kicad.org/10.0/en/cli/cli.html)). The tool that read the page did not see its last 11,515 characters. The schematic export list was cut off. |
| `kicad-cli jobset` job types | The page that I read does not list the job types. | **Unknown** |
| KiCad IPC API | "The IPC API in KiCad 9 and 10 only supports communication with a running instance of the KiCad GUI." Plugins run only in the PCB editor. Headless use through `kicad-cli` is a KiCad 11 feature. The page lists no PCB command for schematic sync. | **Source** ([IPC API for add-on developers](https://dev-docs.kicad.org/en/apis-and-binding/ipc-api/for-addon-developers/)). The page links to the `kicad-python` documentation for commands. I did not read it. |
| KiAuto, scripts | Three scripts exist in `src/`: `eeschema_do`, `pcbnew_do`, and `kicad2step_do`. | **Source** ([KiAuto repository](https://github.com/INTI-CMNB/KiAuto), directory listing) |
| KiAuto, `pcbnew_do` commands | `export`, `run_drc`, `3d_view`, `export_gencad`, `ipc_netlist`, `export_vrml`, and `convert`. No update command. | **Source** (parser definitions in `src/pcbnew_do`) |
| KiAuto, `eeschema_do` | Commands in the README: `export`, `run_erc`, `netlist`, and `bom_xml`. The README text is old and names KiCad 5 and 6. | **Source** (README). I did not read the current `eeschema_do` source. |
| KiAuto release | v2.3.10, published 2026-07-14. KiCad 10 entries: variants (2.3.9), a workaround for a nameless dialog (2.3.8), and the lib tables for the welcome dialog (2.3.7). | **Source** (`CHANGELOG.md`, release data from the GitHub API) |
| KiAuto, fragility | The old README states that the scripts "are very fragile". | **Source** |
| KiBot preflights | The source directory has no preflight that updates the board from the schematic. The names that include "update" are `update_xml`, `update_footprint`, `update_pcb_characteristics`, `update_qr`, and `update_stackup`. `update_footprint` replaces named footprints from the library. It does not apply netlist changes. | **Source** (`kibot/pre_*.py` listing and `update_footprint.rst`). A code search for `update_pcb`, `pcb_from_sch`, `pcb_update`, and `Update PCB from Schematic` returned no match. I did not search the older branches. |
| KiBot parity check | The `drc` preflight passes `--schematic-parity` to `kicad-cli`. The `check_pcb_parity` option of `update_xml` is for KiCad 6 and 7 only. | **Source** (`kibot/pre_drc.py`, `kibot/pre_update_xml.py`) |
| KiBot 1.9.0 | Dated 2026-05-12. KiCad 10 entries: PCB statistics, `allow_blind_vias` and `allow_buried_vias`, variant `include`. KiBot 1.9.1 was published 2026-07-28. | **Source** ([1.9.0 changelog](https://kibot.readthedocs.io/en/v1.9.0/Changelog.html), GitHub release data) |
| KiBot dependency on KiAuto | `update_xml` states KiAuto `eeschema_do` version 2.3.9 as the minimum for KiCad 10. | **Source** (`kibot/pre_update_xml.py` header) |
| SKiDL, existing PCB | The maintainer wrote "There's currently no way to update the existing PCB file" and called a netlist-matching tool "a pending project". | **Secondary**, and old. The discussion has no date in the text that I read. ([SKiDL discussion 161](https://www.github.com/devbisme/skidl/discussions/161)) |
| SKiDL, `generate_pcb()` | It writes a `.kicad_pcb` that opens in PCBNEW without a netlist import. The page does not say that it can update an existing board. | **Source** ([SKiDL manual](https://devbisme.github.io/skidl/)). The tool that read the page did not see its last 330 characters. |
| SKiDL, tags | Tags keep time stamps stable. The netlist then imports into PCBNEW "using the timestamps (instead of part references)". | **Source** (SKiDL manual) |
| SKiDL, schematic | `generate_schematic()` supports KiCad 6 to 10. | **Source** (SKiDL manual) |
| KiCad matching rule | A forum answer states that KiCad matches symbols to footprints by UUID, and that reannotation does not break this. A KiCad issue asks for a feature to keep the link when a symbol moves between sheets. It says that a copy-and-paste into a new sheet does not update the UUID path. | **Secondary** ([forum](https://forum.kicad.info/t/updating-pcb-from-an-updated-schematic/71490), [KiCad issue 22572](https://gitlab.com/kicad/code/kicad/-/work_items/22572)). I read only search excerpts. |
| KiCad dialog options and CLI | The KiCad 10 PCB editor manual calls `Update PCB from Schematic` "the preferred way" to transfer design data. The 733,000-character page was too long for my fetch tool. I did not read the section on matching and options. The 9.0 section page returned a 404 error. | **Unknown** |
| `BOARD_NETLIST_UPDATER` | A 2019 mailing-list message says that the GUI passes the netlist to `BOARD_NETLIST_UPDATER` from `PCB_EDIT_FRAME::KiwayMailIn()`. The 9.0.2 dialog source includes `board_netlist_updater.h`. This points to editor code, not to a CLI entry point. | **Secondary** ([mailing list](https://archive.lists.launchpad.net/kicad-developers/msg39789.html), [Debian source](https://sources.debian.org/src/kicad/9.0.2+dfsg-1/pcbnew/dialogs/dialog_update_pcb.cpp)) |
| KiCad 10 file format | One blog says that KiCad 10 dropped the numbered net table from `.kicad_pcb`. | **Secondary**, one source. Do not rely on it. The trial must read a real file. |

Two items of the plan need a small correction after this research:

- The plan (section 6) says "Do not assume that KiCad 10 supplies a headless update command." The sources agree. I found no counter-example.
- The plan lists `Update PCB from Schematic` as the baseline. The same plan says to test "an IPC or Python adapter" as experimental. The IPC page supports only GUI use in versions 9 and 10. The trial must therefore run a real GUI in the container for the IPC candidate.

**3. Candidate update methods for B5**

I list them in the order that I propose to test. Each has a precise test and a stop condition.

| ID | Method | What it needs | Identity risk | Automation |
|---|---|---|---|---|
| U1 | A person uses the GUI `Update PCB from Schematic` on the native KiCad project. | A KiCad 10 GUI with a display. The container can supply Xvfb and a VNC viewer. A person can also use a desktop KiCad 10 outside the container. | Low if KiCad matches by UUID. Must be measured. | Manual step with automated before-and-after checks. |
| U2 | The same GUI step on the SKiDL path, after `generate_schematic()`. | The SKiDL tags and the KiCad libraries in the container. | Unknown. Depends on SKiDL schematic UUID stability across runs. | Manual step with automated checks. |
| U3 | A netlist import in the GUI from a SKiDL netlist with tags (time-stamp matching). | The SKiDL netlist output. | Medium. Depends on tag stability. The SKiDL manual supports the method. | Manual step with automated checks. |
| U4 | Scripted GUI automation (xdotool inside Xvfb) of the update dialog, written like KiAuto's `pcbnew_do`. | Xvfb, xdotool, a stable dialog layout. | Same as U1. Adds a fragility risk. | Possible, but no document supports it. |
| U5 | The IPC API against a GUI that runs in the container. | A KiCad 10 GUI session, the `kicad-python` package, and a command that I have not found in the documents. | Unknown | Experimental. Stop if the API has no sync command. |
| U6 | The Python `pcbnew` module calls `BOARD_NETLIST_UPDATER`. | An SWIG binding of the class, which I did not find. | Unknown | Stop if the class is not exposed. |

Method U1 is the baseline of the plan. U4 to U6 are experiments. Time-box them: one hour for each. Do not delay the main trial because of them.

**4. Measurement design for identity (applies to U1 to U4)**

The test must tell "KiCad kept the footprint" from "KiCad deleted it and added a new one". Use these checks on the `.kicad_pcb` text before and after the update. The check code runs on the host, because it reads text only.

1. Parse each footprint: reference, value, footprint library ID, position, rotation, layer, UUID, and the `path` property (the schematic UUID path).
2. Parse each track, via, and zone: net name, geometry, and UUID.
3. Make one change at a time in the source: value change, reorder, add a part, remove a part, footprint change, reference rename, move a symbol to another sheet.
4. After the update, compare the sets of footprint UUIDs, positions, and rotations. A change that the schematic does not cause is a failure.
5. Record the dialog options in use. The options change the result (for example, whether KiCad deletes extra footprints or tracks, and whether it re-links by reference).
6. Run `kicad-cli pcb drc --schematic-parity` after the update. Expect zero parity findings.
7. Run the sequence two times with no source change. The second update must change nothing.

Pass condition for a path: all unaffected footprints keep UUID, position, rotation, and tracks, and step 6 and step 7 pass. Record each failed edit as an explicit limit of the path.

**5. Container facts to confirm when the image is present**

I could not inspect these. Each is a short, read-only command. The lead can order them or can allow me to run them.

| Question | Command idea |
|---|---|
| The image digest equals the digest in the order | `podman image inspect --format '{{.Digest}} {{.Id}}' ...` |
| KiCad version | `podman run --rm IMAGE kicad-cli version` |
| KiBot, KiAuto, and ngspice versions | `kibot --version`, `eeschema_do --version`, `pcbnew_do --version`, `ngspice --version` |
| Xvfb, xdotool, and a window manager exist | `command -v Xvfb xdotool` |
| KiCad GUI binary exists | `command -v kicad pcbnew eeschema` |
| Python can import `pcbnew` and the version | `python3 -c "import pcbnew; print(pcbnew.Version())"` |
| SKiDL is absent and installs by `uv` | `uv` inside the container, or a bind mount |
| Symbol, footprint, and 3D libraries exist and their path | Environment variables `KICAD*_SYMBOL_DIR` and `KICAD*_FOOTPRINT_DIR` |
| The user ID of the container user and the bind-mount permission | `id`, then a write test in a temporary mount |
| Image size in storage | `podman image inspect --format '{{.Size}}'` and `df` |

Disk budget: the lead set 15 GB. The host has 47 GB free. A run must write only to a temporary directory under the repository scratch folder, and must remove it afterward. Never run `podman system prune`. Other projects on this host use podman images and containers.

**6. Effect on the batches**

- B1 to B4 do not change.
- B5 splits into two steps. B5a runs the host-only parts: the identity checker (text parser), fixtures, and the report format. B5b runs in the container: the trial circuit, the update methods, and the measurement.
- B5 must produce a decision record. It lists each of U1 to U6 with its result: pass, fail, or not tried, with the commands and the versions.
- The proposal said "A person must do the GUI step". This stays true for U1 to U3. U4 can remove the person only if the experiment passes. Do not assume it.
- The plan says that unattended board generation must not be claimed unless it passes. This research gives no evidence for a claim.

**7. Sierra public samples**

The lead will inspect the two Sierra files. I list the questions that I will ask of them in B10, so the lead can check them at the same time:

- BOM sample: the column names, the order, and the exact header text. Required and optional columns. Whether one row holds a reference list or one reference. How DNP appears.
- X-Y PDF: the column names, the origin, the units, the side name for the bottom, the rotation direction, and the angle zero position.
- Both files: the date or revision, so the profile can record the evidence date and a hash.

I did not fetch either file.

**8. Open items after this research**

- Read the KiCad 10 section on `Update PCB from Schematic` (matching rule and options). The tool that I used could not reach it. Use the manual's anchor `#forward-annotation` on a tool that can page through a long document, or read it in the container with the GUI help.
- Read the current `eeschema_do` source and the KiBot `docs/` folder for any update feature that I did not find by file name.
- Read the `kicad-python` documentation for the board commands.
- Find the date of SKiDL discussion 161. The SKiDL 3.0.0 behavior of `generate_pcb()` against an existing board is unknown.
- Check whether `kicad-cli jobset run` has a job type for netlist update. I do not expect one.

**9. Authorization**

This research used public web pages and the GitHub read API only. It did not use any account, order, or upload. It started no image pull.
