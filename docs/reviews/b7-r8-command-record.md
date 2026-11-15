# B7 r8 command record (claude-skill-dev)

Date: 2026-11-14. Every Python command ran through `uv`. Container commands used `podman run --rm --pull=never --network none --security-opt label=disable` with the accepted image `localhost/cad-skills-pcb:b6`. No image was pulled. Evidence copy: `b7-trial-evidence-r8/`. Full exit log of the read-only checks: `b7-trial-evidence-r8/run-exit-codes.log`.

## Mask boundary fixtures (exports, exit codes from the export runs)

| Command | Exit |
|---|---|
| `uv run make.py` (writes m39, m40, m41, rr, m39merge fixture boards from the text header of the retained board) | 0 |
| `podman run ... kicad-cli pcb export gerbers --output /work/out/ --layers F.Cu,F.Mask /work/board.kicad_pcb` for m39, m40, m41 | 0, 0, 0 |
| same command for rr (round-rect pads) | 0 |
| same command for m39merge (adds `solder_mask_min_width 0.1016`) | 0 |
| same command for oval and overlap fixtures | 0, 0 |

## Measurement and refusal (read-only; exits from `run-exit-codes.log`)

| Command | Exit |
|---|---|
| `uv run measure.py` (circle-only script; 3.9, 4.0, 4.1 mil) | 0 |
| `uv run refuse_rr.py` (lists aperture types of the round-rect fixture) | 0 |
| `uv run merge_check.py` (object types with and without the 4 mil setting) | 0 |
| `uv run merge_extent.py` (region extents) | 0 |
| `uv run --with gerbonara==1.6.3 --with shapely==2.2.0 analyze.py <rr Gerber>` (exact RoundRect analyzer, nominal) | 0 |
| same for the oval fixture (obround refused) | 1 |
| same for the overlap fixture (negative gap printed, not refused: refusal is a required implementation test) | 0 |

## Staged exclusion restoration

| Command | Exit |
|---|---|
| `uv run stage-proof/stage_proof.py <evidence>/excl` (source and staged DRC through the image; segment found by the S-expression parser) | 0 |

Result: source 7 active and 1 excluded `track_width`; staged 8 active. Rule file hash unchanged. Full DRC output hashes are in `stage-proof/stage_proof.out` and `stage-proof/source/drc.json`, `stage-proof/staged/drc.json`.

## Dependency lock (measured)

- `uv run` with `--with gerbonara==1.6.3 --with shapely==2.2.0` (Python 3.13.15). The scratch venv `geom-trial/venv` is the same pinned set; its freeze is `geom-trial/pinned-lock-geom-trial.txt`, exit 0 for `uv pip freeze`.

## Fabrication drawing

- The prototype (regex-based facts extraction and a generated PDF sheet) was withdrawn after the review (`b7-pdf-review-root.md` and the lead's note on parsers). It is not evidence. The drawing content rule stays in r8 section 9 item 6, and the content test is an implementation acceptance test.

## Glossary note

- `ste-glossary.yaml` (repository root) gained eight geometry and tool nouns after B6 acceptance, by root's authorized change. The B6 manifest `b6-replacement-files.sha256` no longer matches that path. The next B7 implementation manifest must include it.

## Deviations

- The first command runs used the wrong working directory for relative paths. The reruns above used explicit directories and recorded the exits.
- `make.py` builds fixture boards by text copy of the header. KiCad produced all exported files that were measured.

## Deviation (recorded once, 2026-11-14)

- Bare `python3` was used for file edits in the B7 implementation batch (contract edits, copy-test helper edits, test expectation edits, and revision-8 text edits). Later commands use `uv run` with script files. No result depends on the interpreter used for these text edits. The hashes in this record were measured after the edits.
