# B7 continuation state (claude-skill-dev), saved before context compaction

Date: 2026-11-14. Read this first after a reset.

## Rules
- No commit, push or supplier action. Accepted B6 set unchanged (manifest `b6-replacement-files.sha256`, sha256 f93454c545a355e43be3e447b41baa334299dbf09bb08fff4c57ab3f234aca39).
- Every Python command runs through `uv`; use a script file (`uv run ... <file>.py`), not `uv run ... -c`. Deviation recorded: bare `python3` reads in the earlier trials.
- No B7 product code until both reviewers agree to the consolidated interface.
- Keep every superseded record as history: r4, r5, r6, r7, the two-layer example, earlier trial sections 8 and 9.

## Current frozen documents (full sha256)
- r7 (reviewed; keep unchanged): fd5eac361a941f19fcbbef57a2ac4f9546797de07b6798cacb0659936379135e (`b7-b8-proposal-claude-r7.md`)
- trial record (sections 1–10): ba719deffe10bcb0633f7833b36ddc037f638bbd4441f0dc4bd94d6dcc41a7dd (`b7-prereq-trials-claude.md`)
- trial evidence manifest (78 files, earlier run): b87e6f328462fc653e77ddb08cb316283ec258a845c8a219c5682a9506b79219 (`b7-prereq-evidence.sha256`); must be regenerated after new trials

## Measured facts (see the trial record)
- KiCad loads a rule file only when its basename matches the project basename. Severity override `board.design_settings.rule_severities.<rule>` = ignore removes the violations.
- Confirmed exclusion format on KiCad 10.0.5: `drc_exclusions = [["<settingsKey>|<x_nm>|<y_nm>|<mainUUID>|<auxUUID>", "<comment>"]]`. Track-width settings key `track_width`; marker position is the straight track midpoint in nm (sexp parser for the target segment). Exactly the targeted violation is excluded. Section 10.
- Slot records: one `G85` line per slot, 3:3 mm, tool width in `T`. Rotated 45 degrees record measured.
- Mask: the nominal RoundRect macro is four circles, four vector lines and an outline. Exact distance from parameters is max(0, d_core − r1 − r2) (geometry trial, section 7). Polygon approximation error is separate.
- PDF commands measured (exit 0): `kicad-cli sch export pdf` on the schematic, `kicad-cli pcb export pdf` with layers F.Fab,B.Fab,Edge.Cuts.

## Still open (in order)
1. Real mask boundary fixtures: pads at 3.9 / 4.0 / 4.1 mil spacing, exported with the B6 mask command, parsed with gerbonara 1.6.3 (venv in `geom-trial/venv`, pinned), exact distance, uncertainty bound stated (derived: 0.000003 mm coordinate and floating-point; plus exporter quantisation). Verify supported-macro checks: refuse unknown macros.
2. Revision 8 (r8): apply Pi section 16 items 1–7 and Codex r7 item 3 (source-review omission and tamper tests). Read those sections of `b7-b8-design-pi.md` and the Codex r7 review first. Preserve source nominal units; record slot expected plating from board attributes; manifest input roles; a report artifact for manual geometry; old two-layer example superseded.
3. Freeze one full evidence manifest with complete command records (full command lines, exits, full input and output hashes) for every trial.

## Herdr
- `/proc/482044/exe agent prompt w1P:p3 "[date - time UTC] To: skill-dev-lead; From: claude-skill-dev - ..."`.
