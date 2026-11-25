# SKILL.md mechanical documentation review: Pi

Date: 2026-11-15. Reviewer: pi-mechanical-dev, pane w1P:pE.

Subject: `skills/pcb-design/SKILL.md`, SHA-256 `e053bd645538c0f51d897bb6f3d805b9b5a22822f5dacd6905cdce926310c391`. Diff against HEAD: 20 insertions, 0 deletions. Text-only review. I edited no file and ran no suite.

Scope: the new `## Mechanical fit` section, the Scope table row, and the Files entries.

**Decision: findings. Five items, all minor and non-blocking.**

## 1. Verified

- The subject hash matches the requested value. `git diff HEAD` shows 20 insertions and 0 deletions, all in the three named places.
- Every `references/*.md` name in the file exists, including `references/mechanical-fit.md` (SHA-256 `8b5793c45180f18f7954468177487e36c0220622b1be2c838101e50c382281c9`).
- The commands match `scripts/pcb.py`:
  - The `mechanical` subparser has the actions `check`, `readiness`, `export`, `fit` and `release`, and a positional `path`.
  - `check DIR` maps to `mechanical.py check --fixture DIR`. The other actions map to `--project DIR`.
  - The `--image` option exists and applies to `export` only. `cmd_mechanical` forwards it for `export` only.
- The Scope row and the section agree with `references/mechanical-fit.md` on the fixture `mech-fit-a`, the proxy components, and the limit that a proxy proves a conservative envelope only.
- The exit-code pointer to `references/mechanical-fit.md` is correct. That reference lists the exit status.
- The Scope row is placed after the GUI row and follows the table form.

## 2. Findings

### D1. The Files entry calls `mechanical_fit.py` a command holder

The entry reads: "`scripts/mechanical.py`, `scripts/mechanical_fit.py`: the mechanical fit commands."

`mechanical_fit.py` is the geometry library. It has no command entry point. The commands are in `mechanical.py`, reached through `pcb.py mechanical`. `references/mechanical-fit.md` separates the two roles.

Recommend: "`scripts/mechanical.py` and `scripts/mechanical_fit.py`: the mechanical fit records and geometry. See `references/mechanical-fit.md`."

### D2. "safe envelope" differs from the accepted term

The section reads: "The check proves only a safe envelope."

The accepted term in `references/mechanical-fit.md` and in the interface is "conservative envelope". "Safe" can read as a safety claim. Use "conservative envelope".

### D3. The command block omits `readiness`

The block lists `check`, `export`, `fit` and `release`. `pcb.py mechanical` also has `readiness`, and `references/mechanical-fit.md` lists it. Add `uv run scripts/pcb.py mechanical readiness DIR`, or state that the block lists the fit flow only.

### D4. The block does not show how to make `DIR`

The block defines `DIR` as the fixture directory. The generator is `uv run templates/mech-fit-a/make_fixture.py --out DIR`, which `references/mechanical-fit.md` shows. The section says to read the reference first, so this item is optional. One added line helps a reader.

### D5. "check" as a verb

The first sentence uses "check" as a verb: "Use this route to check the mechanical fit". The STE guidance lists "check" as a verb for change, with "examine" or "do a check" as the approved forms. The accepted file already uses "checks" as a verb in the introduction, so this item is a consistency choice, not a defect. Consider "to do a check of the mechanical fit".

## 3. Limits

- This is a text-only review of one file. I ran no suite and no command.
- The findings are minor and do not block the change.
