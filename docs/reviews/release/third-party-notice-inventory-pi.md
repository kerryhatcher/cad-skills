# Third-party notice inventory from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: inventory of newly redistributed source, models, supplier evidence, bundled data,
image references, and dependencies for B12. This report gives measured licenses and
attribution. It does not approve a release. It writes no product file.

## Rules applied

1. Only project-authored source is covered by the repository MIT license. Do not relabel
   third-party content MIT.
2. Adding `license: MIT` metadata to a `SKILL.md` file does not resolve the license of
   the content that the skill bundles or references.
3. A `Containerfile` `FROM` line references an image on a registry. It does not
   redistribute the image. If the release publishes a built image or a tarball, the image
   becomes redistributed and the notice must include the image contents and their
   licenses.
4. A dependency line in a PEP 723 header, a lock file, or a Containerfile declares a
   dependency. It does not redistribute the dependency code.
5. A stored supplier page or a supplier document is redistributed bytes. It needs a
   source, a retrieval date, and a measured license or terms statement.

## 1. Redistributed bytes that need a notice

| Item | Type | Source | Retrieval | License state |
|---|---|---|---|---|
| `skills/pcb-fab-package/supplier/pages/*.html` (5 files) | Supplier page copies | OSH Park docs (`docs.oshpark.com`) | 2026-11-14 05:20 UTC | Terms not yet measured. Do not relabel MIT. |
| `skills/pcb-fab-package/supplier/pages/*.headers` (5 files) | HTTP response headers | Same URLs | 2026-11-14 05:20 UTC | Same terms. Evidence only. |
| `docs/reviews/sierra-source-evidence/xy.pdf` | Supplier drawing | Sierra Circuits (`protoexpress.com`) | 2026-11-14 11:05 UTC | Terms not yet measured. |
| `docs/reviews/sierra-source-evidence/xyrs.xlsx` | Supplier placement workbook | Sierra Circuits | 2026-11-14 11:09 UTC | Terms not yet measured. |
| `docs/reviews/sierra-source-evidence/turnkey-faq.html` | Supplier FAQ page | Sierra Circuits | 2026-11-14 11:12 UTC | Terms not yet measured. |
| `docs/reviews/sierra-source-evidence/*.headers` (3 files) | HTTP response headers | Same URLs | 2026-11-14 | Evidence only. |

The supplier pages have `last-modified` 2026-10-01. The Sierra FAQ has `last-modified`
2026-11-14. The Sierra PDF has `last-modified` 2014-04-17. Record each one in the
notice.

## 2. Project-authored bundles under the repository MIT license

These items are copies of project source. They stay MIT. They are not third-party.

| Item | Note |
|---|---|
| `skills/pcb-design/contracts/`, `skills/pcb-fab-package/contracts/` | Byte copies of `contracts/`. |
| `skills/pcb-design/scripts/project_io.py`, `skills/pcb-fab-package/scripts/project_io.py` | Byte copies of `contracts/project_io.py`. |
| `skills/*/scripts/validate.py` | Copies of the project validator. |
| `skills/pcb-design/runtime/Containerfile`, `skills/pcb-fab-package/runtime/Containerfile` | Project build recipe. Text only. |
| `examples/pcb-trial/Containerfile`, `Containerfile.uv` | Project build recipe. Text only. |

A copy test compares the bytes. That test does not change the license.

## 3. Image references, not redistribution

| Reference | Kind | Measured license | Note |
|---|---|---|---|
| `ghcr.io/astral-sh/uv` | Image reference in three Containerfiles | Apache-2.0 | Measured from `astral-sh/uv` on 2026-11-15. Not redistributed. |
| `ghcr.io/inti-cmnb/kicad10_auto_full` | Image reference in three Containerfiles | Image recipe `INTI-CMNB/kicad_auto` is Apache-2.0 | The image holds KiCad (GPL-3.0-or-later), KiBot (AGPL-3.0), ngspice, and other packages. Not redistributed. |
| `ngspice=44.2+ds-1` | Apt package in the build recipe | BSD-3-clause for main files. `doc/*` is BSD-3-clause, CC-BY-SA-4.0 and public-domain. `doc/config/*` is GPL-2+. | Measured from the Debian copyright file on 2026-11-15. Not redistributed. |

If the lead later publishes a built image, this section becomes a redistribution section.
KiCad is GPL-3.0-or-later. KiBot is AGPL-3.0. The image recipe license alone is not
sufficient.

## 4. Python dependencies

PEP 723 headers declare these direct packages. The installed version follows the
constraint. Measure the resolved version at run time.

| Package | Constraint in the tree | License (measured 2026-11-15) | Source |
|---|---|---|---|
| cadquery | `cadquery`, `>=2.5` | Apache-2.0 | PyPI 2.8.0 |
| trimesh | `trimesh>=4` | MIT | PyPI 5.2.1 |
| rtree | `rtree` | MIT | PyPI metadata |
| scipy | `scipy` | BSD-3-Clause | PyPI metadata |
| numpy | `numpy` | BSD-3-Clause and 0BSD, MIT, Zlib, CC0-1.0 parts | PyPI metadata |
| matplotlib | `matplotlib` | matplotlib license, PSF based | PyPI metadata |
| networkx | `networkx` | BSD-3-Clause | PyPI metadata |
| lxml | `lxml` | BSD-3-Clause | PyPI metadata |
| gmsh | `gmsh` | GPL-2.0-or-later | PyPI 4.15.2 |
| scikit-fem | `scikit-fem>=10` | BSD | PyPI metadata |
| meshio | `meshio` | MIT | PyPI metadata |
| pyamg | `pyamg` | MIT | PyPI metadata |
| jsonschema | `jsonschema==4.26.0` | MIT | PyPI metadata |
| pyyaml | `pyyaml==6.0.3` | MIT | PyPI 6.0.3 |
| gerbonara | `gerbonara==1.6.3` | Apache-2.0 | PyPI metadata |
| skidl | `skidl==3.0.0` | MIT | PyPI metadata and upstream LICENSE |

`examples/pcb-trial/requirements.lock` pins about 40 transitive packages with hashes.
The lock file is redistributed project data. The package code stays on PyPI. Record the
lock file as a dependency list. Do not list the packages as redistributed bytes.

`uv` downloads these packages at run time. The skill does not bundle them.

## 5. Models and bundled data

No component model, STEP file, STL file, WRL file, or 3MF file exists in the release
worktree at this review. The B11 mechanical export may add models.

| Item | State | Action |
|---|---|---|
| Mechanical component models | Pending B11 | Record source, license, attribution, and hash for each model. |
| Project-authored proxy envelopes | Pending B11 | Label each as a proxy. Project MIT applies. |
| KiCad installed libraries | Tool dependency | Do not redistribute. If a package redistributes a library collection, retain its license and attribution. |
| Prusa profile bundle | Downloaded at run time | Do not bundle. Record the source and the license of the bundle. |
| `examples/pcb-trial/native/` and `results/` | Project trial data | Project MIT for project-authored files. Supplier evidence inside needs its own entry. |

## 6. Measured license sources

| Item | Source | Date |
|---|---|---|
| Python packages | `pypi.org/pypi/<name>/json` | 2026-11-15 |
| `astral-sh/uv` | GitHub API `repos/astral-sh/uv` | 2026-11-15 |
| `INTI-CMNB/kicad_auto` | GitHub API `orgs/INTI-CMNB/repos` | 2026-11-15 |
| `KiCad/kicad-source-mirror` | GitHub API | 2026-11-15 |
| ngspice 44.2+ds-1 | Debian copyright file, `sources.debian.org` | 2026-11-15 |
| Supplier pages | Local HTTP headers and HTML titles | 2026-11-15 |

The web fetch tool on this host returned an error. The facts above came from `curl` and
local files.

## 7. Open items for the lead

- O1: Measure the OSH Park terms of use and the Sierra Circuits terms. Record the result.
  Do not state MIT for either one.
- O2: Decide whether a release that publishes a built image is in scope. If yes, the
  notice must cover the image contents and their licenses.
- O3: Add the KiCad library license URL and the measured statement to the notice.
- O4: Give each B11 model and proxy an entry before distribution.
- O5: Put the notice in one file. The author proposed `docs/release-licensing.md`.
  Confirm the path.

## Limits

This inventory reads stable files and public license sources. It does not contact a
supplier. It does not give legal advice. A license entry is a measured observation, not
an approval.
