# Third-party notice inventory for B12

Date: 2026-11-15 UTC.
Author: `claude-release-dev` (Claude, assigned model Haiku 5.5).
Base commit: `75d99da`. Branch: `work/release`.
Sources: `docs/reviews/release/third-party-notice-inventory-pi.md` (Pi), measurements in this team's worktree and in the local image `localhost/cad-skills-pcb:b6` (read with `podman run --pull=never`).

Status: open. This inventory records measured observations. It does not approve a release. It does not resolve any third-party license.

## 1. Rules

1. The repository MIT license covers project-authored files only. Third-party content keeps its own license. Do not relabel it MIT.
2. Adding `license:` metadata to a `SKILL.md` file does not resolve the license of the content that the skill bundles or references.
3. A `FROM` line in a Containerfile references an image on a registry. It does not redistribute the image. A published image or tarball is a redistribution. Such a release needs a notice for the image contents.
4. A dependency line (PEP 723 header, lock file, Containerfile package line) declares a dependency. It does not redistribute the dependency.
5. A stored supplier page, drawing or workbook is redistributed bytes. It needs a source, a retrieval date and a measured license or terms statement.

## 2. Redistributed third-party bytes in the repository

| Item | Type | Source | Measured license or terms | Attribution | State |
|---|---|---|---|---|---|
| `skills/pcb-fab-package/supplier/pages/*.html` (5 files) | Supplier page copies | `docs.oshpark.com`, retrieved 2026-11-14 | Page footer reads "© Copyright 2023 OSH Park, LLC". No license, terms of use or reuse permission found on `docs.oshpark.com` (fetched 2026-11-15) | OSH Park, LLC, with URL and retrieval date | Blocking for distribution. Lead decides: remove the copies, keep only hashes and source URLs, or obtain permission |
| `skills/pcb-fab-package/supplier/pages/*.headers` (5 files) | HTTP response headers | Same URLs | Evidence only | Source URL | Same decision as the pages |
| `docs/reviews/sierra-source-evidence/turnkey-faq.html` and `*.headers` | Supplier FAQ copy and headers | Sierra Circuits (`protoexpress.com`), 2026-11-14 | Not measured | Source URL | Open. Measure Sierra terms (O1) |
| `docs/reviews/sierra-source-evidence/xy.pdf` | Supplier drawing | Sierra Circuits, retrieved 2026-11-14 | Not measured | Source URL | Open (O1) |
| `docs/reviews/sierra-source-evidence/xyrs.xlsx` | Supplier placement workbook | Sierra Circuits, retrieved 2026-11-14 | Not measured | Source URL | Open (O1) |
| `docs/reviews/sierra-source-evidence/BOM-Sample-and-Demo.xls` | Supplier BOM sample workbook. Local evidence, excluded from distribution | Sierra Circuits (`media.protoexpress.com`), public GET 2026-11-15T03:12:26Z | The author did not assess reuse permission. The record claims no permission | Source URL | Excluded from distribution (`exclude-full-copy`). Open for the lead decision on Sierra terms (O1) |
| KiCad library symbol definitions inside `.kicad_sch` files | Library data copied into design files | KiCad official libraries | KiCad libraries: CC-BY-SA 4.0 (`kicad.org/libraries/license/`, fetched 2026-11-15). Exception quoted in section 2.1 | KiCad library attribution and license documents must stay with redistributed library data. A redistributed library collection keeps CC-BY-SA 4.0 | Open. Measured basis in section 2.1. Lead decides (O3) |

The KiCad symbol definitions are measured in these files. Each `lib_symbols` block names `Device:C`, `Device:R`, `Device:LED` and `Connector_Generic:Conn_01x02`:

- `skills/pcb-design/templates/rc-bare-board/kicad/board.kicad_sch`.
- `skills/pcb-design/examples/rc-edit/before/kicad/board.kicad_sch` and `after/kicad/board.kicad_sch`.
- `tests/fixtures/pcb-design/defective.kicad_sch`.
- 48 files under `examples/pcb-trial/` (schematics written by the trial runs).
- 9 tracked files under `docs/reviews/`: `docs/reviews/b7-implementation-evidence/project/kicad/board.kicad_sch` and 8 files under `docs/reviews/b7-trial-evidence-r8/`.

Count, measured 2026-11-15 with `git ls-files`: 61 tracked `.kicad_sch` files. All 61 carry a `lib_symbols` block. That is 52 under `skills`, `tests` and `examples`, plus 9 under `docs/reviews`.

The `.kicad_pcb` files match footprint instances. They do not contain library definitions.

### 2.1 KiCad exception (measured)

Fetched from `https://www.kicad.org/libraries/license/` on 2026-11-15. Re-check the page before release.

> "To the extent that the creation of electronic designs that use 'Licensed Material' can be considered to be 'Adapted Material', then the copyright holder waives article 3 of the license with respect to these designs and any generated files which use data provided as part of the 'Licensed Material'."

> "Use of the library data in a project does not (by itself) require that the design or any files generated from the design are licensed under the CC-BY-SA 4.0 License."

Consequence:

- Under this exception, the `lib_symbols` blocks in design and trial files do not require CC-BY-SA 4.0 for those files. Pi reads this as project MIT for the design files. The lead decides (O3).
- A redistribution of the library collection itself still needs CC-BY-SA 4.0 and attribution. The collection is not in this repository.

## 3. Project-authored bundles (repository MIT license)

These items are project copies or project-authored data. They keep the repository MIT license.

| Item | Note |
|---|---|
| `skills/pcb-design/contracts/`, `skills/pcb-fab-package/contracts/` | Byte copies of `contracts/` |
| `skills/pcb-design/scripts/project_io.py`, `skills/pcb-fab-package/scripts/project_io.py` | Byte copies of `contracts/project_io.py` |
| `skills/*/scripts/validate.py` | Copies of the project validator |
| `docs/reviews/sierra-source-evidence/drill-probe.py` and `drill-probe.json` | Project-authored evidence script and its output. The script uses supplier facts from the Sierra evidence. The supplier facts keep the status in section 2 |
| `skills/pcb-design/templates/rc-bare-board/simulations/rc.cir` | Added by Kerry Hatcher in `75d99da` |
| `skills/pcb-fab-package/supplier/profiles/oshpark-*.yaml` (5 files) | Repository-written data. Each file names its source URL and evidence hash. The supplier text is not copied. OSH Park remains the source of the facts |
| `tests/fixtures/pcb-fab-package/drawing-example.png` | Added by Kerry Hatcher in `75d99da`. Origin not recorded. Provenance is open (O6) |
| `examples/respeaker-nightlight/refs/*.png` | Added in `98ecfb0`. Origin not recorded. Provenance is open (O6) |

A copy test that compares bytes does not change any license.

## 4. Image references (not redistributed)

Four Containerfiles reference images or packages. None redistributes an image in this repository.

| File | Reference | Kind |
|---|---|---|
| `skills/pcb-design/runtime/Containerfile` | `ghcr.io/astral-sh/uv@sha256:e85be844203885286c60ffad8a858d48afb6c5a5c237ca0e67f12e74b8f174b1` and `ghcr.io/inti-cmnb/kicad10_auto_full@sha256:96e75f885b15617c6b38aef11db7856a93f4367cab7a0b6c2b30465557619330` | Image reference, pinned by digest |
| `skills/pcb-fab-package/runtime/Containerfile` | Same two references | Image reference |
| `examples/pcb-trial/Containerfile` | Image and package references | Image reference |
| `examples/pcb-trial/Containerfile.uv` | Image and package references | Image reference |

Components of the two images, measured where stated:

| Component | Measured license | Source |
|---|---|---|
| `uv` (`ghcr.io/astral-sh/uv`) | Apache-2.0 OR MIT (dual) | `LICENSE-APACHE` and `LICENSE-MIT` in `astral-sh/uv`, fetched 2026-11-15 |
| KiCad 10.0.5 (in the image) | GPL-3.0-or-later (upstream statement, authoritative for the image contents). The image copy carries the Debian `copyright` file with a legacy GPL v2 header from the Debian packaging. The mismatch is recorded, not resolved | `kicad.org/about/licenses/`, fetched 2026-11-15. `/usr/share/doc/kicad/copyright` in the image |
| KiBot 1.9.1 (in the image) | AGPL-3.0, from the pinned upstream `LICENSE` at tag `v1.9.1`: SHA-256 `0d96a4ff68ad6d4b6f1f30f713b18d5184912ba8dd389f86aa7710db079abcb0` (fetched and hashed 2026-11-15). The installed metadata `kibot-1.9.1.egg-info/PKG-INFO` reads GPL-3.0. That metadata is stale and is kept as a recorded conflict | `https://raw.githubusercontent.com/INTI-CMNB/KiBot/v1.9.1/LICENSE` |
| KiAuto 2.3.10 (in the image) | Apache-2.0 (package metadata). The Debian `copyright` file also lists Expat for some files (measured: one match) | `kiauto-2.3.10.egg-info/PKG-INFO` and `/usr/share/doc/kiauto/copyright` |
| ngspice 44.2+ds-1 (Debian package) | BSD-3-clause. Documentation parts also carry CC-BY-SA-4.0 and public-domain terms. `doc/config/*` is GPL-2+ (Pi) | `/usr/share/doc/ngspice/copyright` in the image |
| KiCad libraries (in the image) | CC-BY-SA 4.0 with the design exception (section 2) | `kicad.org/libraries/license/` |

The image labels state only a description and a maintainer. The labels do not state the license of the complete image. The image-level license is unmeasured (O2).

If a release publishes a built image or tarball, this section becomes a redistribution section. The notice must then cover every component above and its attribution.

## 5. Python dependencies

PEP 723 headers and lock files declare these packages. `uv` downloads them at run time. The repository does not bundle their code.

| Package | Constraint in the tree | Measured license | Source |
|---|---|---|---|
| jsonschema | `==4.26.0` | MIT (`license_expression`) | `pypi.org/pypi/jsonschema/4.26.0/json`, fetched 2026-11-15 |
| pyyaml | `==6.0.3` | MIT | `pypi.org/pypi/pyyaml/6.0.3/json`, fetched 2026-11-15 |
| gerbonara | `==1.6.3` | Apache-2.0 (classifier; `info.license` is null) | `pypi.org/pypi/gerbonara/1.6.3/json`, fetched 2026-11-15 |
| cadquery | `>=2.5` | Apache-2.0 | PyPI metadata (Pi) |
| trimesh | `>=4` | MIT | PyPI (Pi) |
| gmsh | unpinned | GPL-2.0-or-later | PyPI 4.15.2 (Pi) |
| skidl | `==3.0.0` | MIT | PyPI metadata and upstream LICENSE (Pi) |
| Others in the trees (rtree, scipy, numpy, matplotlib, networkx, lxml, scikit-fem, meshio, pyamg) | Unpinned or pinned | As listed by Pi (BSD-3-Clause, MIT, PSF-based) | PyPI metadata (Pi) |

`examples/pcb-trial/requirements.lock` pins about 40 transitive packages with hashes. The lock file is a dependency list. It is not a redistribution of the package code.

## 6. Models, bundled data and tool dependencies

- No component model, STEP, STL, WRL or 3MF file exists in this worktree. B11 may add them. Each model needs its own entry before distribution (O5).
- `skills/pcb-design/templates/rc-bare-board/kicad/board.kicad_pcb` holds five `(model …)` references to `${KICAD10_3DMODEL_DIR}` paths (measured 2026-11-15). The file does not embed the models. Do not count them as redistributed.
- KiCad installed libraries are a tool dependency. They are not redistributed by this repository, except the embedded symbol definitions in section 2.
- The PrusaSlicer skill reads a profile bundle that the installed PrusaSlicer provides. No `PrusaResearch` bundle file exists in the tree. Nothing is redistributed. PrusaSlicer is licensed under AGPL-3.0 (`prusa3d/PrusaSlicer` LICENSE, fetched 2026-11-15). Do not bundle the profile file.

## 7. Open items

| ID | Item | Action | Owner |
|---|---|---|---|
| O1 | OSH Park and Sierra Circuits terms | Measure the terms. OSH Park shows a copyright line and no license. Do not state MIT for either source | Lead |
| O2 | Image-level license of `kicad10_auto_full` and any published image | Decide whether a published image is in scope. If yes, cover all components in section 4 | Lead |
| O3 | Design exception for KiCad symbols (measured basis in section 2.1) | Lead decides whether the exception covers the copied definitions in the 61 design and trial files. Retain attribution in any case | Lead |
| O4 | KiBot license for the pinned version 1.9.1. The upstream `LICENSE` at tag `v1.9.1` reads AGPL-3.0 (SHA-256 recorded in section 4). The installed metadata reads GPL-3.0 and is kept as a stale conflict | Use the pinned upstream text. Keep the metadata conflict in this notice | Closed for the pinned version. Lead decided 2026-11-15 |
| O5 | Each B11 model and proxy | Add source, license, attribution and hash before distribution | Mechanical team |
| O6 | Provenance of `drawing-example.png` and `respeaker-nightlight/refs/*.png` | Record the source or remove the file | Lead |

The OSH Park copies block distribution now. Do not publish them before the lead decides. The Sierra copies also need a lead decision. Their terms are not measured, so their permission is not proven. The KiCad symbol definitions wait for the lead decision on O3. The other items are open records.

## 8. Limits

This inventory reads repository files and public license sources on 2026-11-15 UTC. It does not contact a supplier. It does not give legal advice. A license entry is a measured observation, not an approval.
