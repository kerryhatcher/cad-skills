# Release licensing recheck from Pi

Date: 2026-11-15 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: recheck of `docs/release-licensing.md` after the author applied L-1 to L-5 from
`docs/reviews/release/release-licensing-review-pi.md`. This report gives the result. It
writes no product file. It does not approve a release.

## Result

L-1 to L-5 are applied and correct. The three extra measurements are correct. One
residual correction remains (R-1).

## Check of L-1 to L-5

| ID | Author claim | Check | Result |
|---|---|---|---|
| L-1 | 61 tracked `.kicad_sch` files. All carry `lib_symbols`. 52 under `skills`, `tests`, `examples`. 9 under `docs/reviews` | `git ls-files` and `grep -rIl lib_symbols` | Correct |
| L-2 | Section 2.1 quotes the KiCad exception and states the consequence | Compare with `kicad.org/libraries/license/` | Correct. The two quotes match the page |
| L-3 | Full image digests | Compare with the four Containerfiles | Correct. Both digests match |
| L-4 | Expat added to the KiAuto row | Read section 4 | Correct |
| L-5 | `drill-probe.py` and `drill-probe.json` added as project-authored | Read section 3 | Correct |

The L-1 scope split is exact. The 9 files are one under
`docs/reviews/b7-implementation-evidence/` and eight under
`docs/reviews/b7-trial-evidence-r8/`.

## Check of the extra measurements

| Item | Author claim | Check | Result |
|---|---|---|---|
| KiCad legacy GPL v2 header | The image `copyright` file has a legacy GPL v2 header. Upstream is GPL-3.0-or-later | `podman run --pull=never localhost/cad-skills-pcb:b6 head /usr/share/doc/kicad/copyright` | Correct. The file reads "Software: GPL v2" |
| Five 3D model references | `board.kicad_pcb` holds five `(model ...)` references to `${KICAD10_3DMODEL_DIR}`. The file does not embed them | `grep -c '(model '` | Correct. Five matches. No model file is in the tree |
| PrusaSlicer AGPL-3.0 | PrusaSlicer is AGPL-3.0. No profile bundle is in the tree | GitHub API `prusa3d/PrusaSlicer` and a file search | Correct. No `PrusaResearch` file exists |

The KiBot conflict is also correct. The installed metadata reads GPL-3.0. The upstream
`LICENSE` reads AGPL-3.0. The author records the upstream text as authoritative.

## Residual correction

### R-1 Section 7: "Only the OSH Park copies block distribution now"

The Sierra copies have unmeasured terms. An unmeasured term is not proof of permission.
Thus the Sierra copies are not proven permitted and are also an open blocker.

Correction: write that the OSH Park copies are a measured blocker and the Sierra copies
have unmeasured terms that also need a decision. Keep the sentence that the KiCad symbol
definitions wait for O3.

## R-1 verification

The author applied R-1 before this report was final. Section 7 now says that the OSH Park
copies block distribution and that the Sierra copies also need a lead decision, because
their terms are unmeasured. The statement matches this review. No correction remains.

## Verdict

The notice is in a good state. R-1 is applied. The lead decisions remain O1 to O6. Do not
publish the OSH Park or Sierra copies before the lead decides.

## Limits

This recheck reads the file, the release tree, the local image
`localhost/cad-skills-pcb:b6` with `--pull=never`, and public license sources. It does
not contact a supplier. It does not give legal advice.
