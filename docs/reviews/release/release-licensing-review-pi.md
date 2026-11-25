# Release licensing review from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: check of `docs/release-licensing.md` against
`docs/reviews/release/third-party-notice-inventory-pi.md` and the release tree. This
report gives concrete corrections. It does not approve a release. It writes no product
file.

## Environment

| Item | Value |
|---|---|
| Working directory | `/mnt/storage/projects/cad-skills-worktrees/release` |
| Branch | `work/release` |
| HEAD | `75d99da` |
| Host | Pi 1.5.2 |
| Local image | `localhost/cad-skills-pcb:b6` |

## Verdict

`docs/release-licensing.md` is a strong improvement on my inventory. It corrects two of
my errors. It finds two new items that I missed. Five corrections remain. With those
corrections, I agree that the file can hold the notice, subject to the lead decisions on
the OSH Park terms and the open items.

## The four requested differences

### 1. Four Containerfiles, not three

Confirmed. The four files are:

- `skills/pcb-design/runtime/Containerfile`
- `skills/pcb-fab-package/runtime/Containerfile`
- `examples/pcb-trial/Containerfile`
- `examples/pcb-trial/Containerfile.uv`

My inventory said "three Containerfiles". That count was incorrect. The author file is
correct. All four reference the two images.

### 2. Schematic files with KiCad symbol definitions

Confirmed in part. The count depends on the scope.

| Scope | Files with `lib_symbols` |
|---|---|
| `skills/`, `tests/`, `examples/` | 52 |
| `docs/reviews/` | 9 |
| Total in the worktree | 61 |

All 61 `.kicad_sch` files contain a `lib_symbols` block. All 61 are tracked by Git. The
author text says 52 and names the scope `skills`, `tests` and `examples`. That statement
is correct for its scope. It omits 9 tracked files under `docs/reviews/`. These are:

- `docs/reviews/b7-implementation-evidence/project/kicad/board.kicad_sch`
- 8 files under `docs/reviews/b7-trial-evidence-r8/`

Correction: write the total 61, or state the scope and the 9 excluded files. A
distribution includes the tracked `docs/reviews/` tree.

### 3. OSH Park copyright line and no license

Confirmed. All five pages contain "Copyright 2023 OSH Park, LLC". I found no license,
terms of use, or reuse permission on the pages. The author entry is correct. The status
"Blocking for distribution" is correct.

### 4. KiBot metadata GPL-3.0 and upstream AGPL-3.0

Confirmed with two independent measurements:

- Installed metadata in `localhost/cad-skills-pcb:b6`:
  `License: GPL-3.0` and `Classifier: ... GNU General Public License v3 or later (GPLv3+)`.
- Upstream `INTI-CMNB/KiBot` `LICENSE`: "GNU AFFERO GENERAL PUBLIC LICENSE Version 3".

The author entry is correct. The upstream LICENSE is the authoritative text. The PyPI
and installed metadata are stale. Record that statement.

## Additional findings

### 5. KiCad library design exception

The author file leaves the design exception open. The measured text on
`kicad.org/libraries/license/` (fetched 2026-11-15) says:

> The KiCad libraries are licensed under the Creative Commons CC-BY-SA 4.0 License,
> with the following exception: ... the copyright holder waives article 3 of the license
> with respect to these designs and any generated files which use data provided as part
> of the 'Licensed Material'.

The same page says: "Use of the library data in a project does not (by itself) require
that the design or any files generated from the design are licensed under the license."

Consequence: the embedded `lib_symbols` blocks in the design and trial files fall under
the exception. Those files stay project MIT. A redistribution of the library collection
itself still needs CC-BY-SA 4.0 and attribution. The library collection is not in the
tree. Correction: record the measured quote and this consequence. Keep the lead decision
on O3, but give the measured basis.

### 6. KiCad image copyright mismatch

Confirmed. The image file `/usr/share/doc/kicad/copyright` starts with a legacy "GPL v2"
header. The upstream is GPL-3.0-or-later. The author entry is correct. Record the
upstream statement as authoritative for the image contents.

### 7. KiAuto extra license

Confirmed Apache-2.0. The image copyright also lists Expat for some files. Correction:
add Expat to the KiAuto row.

### 8. Truncated image digests

Section 4 writes `sha256:e85be844...` and `sha256:96e75f88...`. Correction: record the
full digests in the notice:

- `ghcr.io/astral-sh/uv@sha256:e85be844203885286c60ffad8a858d48afb6c5a5c237ca0e67f12e74b8f174b1`
- `ghcr.io/inti-cmnb/kicad10_auto_full@sha256:96e75f885b15617c6b38aef11db7856a93f4367cab7a0b6c2b30465557619330`

### 9. Project-authored evidence scripts

Section 3 does not list `docs/reviews/sierra-source-evidence/drill-probe.py` and
`drill-probe.json`. They are project-authored. Correction: add them to the project MIT
list, or state that they are project evidence scripts that use supplier facts.

### 10. Template 3D model references

`skills/pcb-design/templates/rc-bare-board/kicad/board.kicad_pcb` holds five `(model ...)`
references. These reference external 3D model paths. The `.kicad_pcb` files do not embed
the models. Correction: state this, so a later reader does not count the models as
redistributed.

### 11. PrusaSlicer license

Section 6 says the PrusaSlicer license is not measured. The skill downloads a profile
bundle at run time. Nothing is redistributed. Correction: state the PrusaSlicer license
as an open item, or measure it. Do not bundle the profile file.

## Defects

| ID | Section | Defect | Correction |
|---|---|---|---|
| L-1 | 2 | The schematic count is 52 and omits 9 tracked files under `docs/reviews/` | Write 61, or name the scope and the 9 files |
| L-2 | 2 | The KiCad design exception is open with no measured basis | Add the measured quote and the consequence |
| L-3 | 4 | The image digests are truncated | Write the full digests |
| L-4 | 4 | The KiAuto row omits Expat | Add Expat |
| L-5 | 3 | The Sierra probe script and JSON are absent | Add them as project-authored evidence |

## Agreement

I agree with the following author statements:

- The repository MIT license covers project-authored files only.
- A `FROM` line references an image. A published image is a redistribution.
- The OSH Park pages and headers are blocking. The OSH Park copyright line is real.
- The KiBot metadata and upstream text conflict. The upstream text wins.
- The image-level license is unmeasured (O2).
- The supplier terms remain open (O1).
- The B11 models need their own entries (O5).
- The provenance items O6 are open.

I do not agree that the task is complete while L-1 to L-5 stand. The remaining lead
decisions are O1 (OSH Park terms) and the distribution of the stored supplier pages.

## Recommendations

- R-1: Apply L-1 to L-5.
- R-2: Add the KiCad library exception quote and the code-swap test result.
- R-3: Keep the KiBot conflict open with the measured upstream text.
- R-4: Do not publish the OSH Park page copies until the lead decides the terms.
- R-5: Keep the notice in one file. Confirm the path `docs/release-licensing.md`.

## Limits

This review reads repository files, the local image `localhost/cad-skills-pcb:b6` with
`--pull=never`, and public license pages. It does not contact a supplier. It does not
give legal advice. It does not run a paid call.
