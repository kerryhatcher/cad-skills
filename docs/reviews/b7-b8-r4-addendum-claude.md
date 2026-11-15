# B7/B8 revision 4 addendum (claude-skill-dev)

Date: 2026-11-14. Scope: two notes from the lead for the reviewers. `b7-b8-proposal-claude-r4.md` stays unchanged under review.

## 1. Slot-capable derivative

The B6 inventory worker refuses slot and oval drills (exit 2, with the named object). The `pcb-fab-package` skill needs a slot-capable inventory for the slot rule (`min_slot_size`, minor dimension). It therefore needs an explicitly owned derivative:

- The skill ships its own inventory worker, a byte copy of the B6 worker with one owned change: slot and oval drills are read and reported with their minor and major dimensions, not refused. The change is recorded as a separate, named worker version in the skill manifest.
- The derivative has its own tests: a slot fixture (the B6 slot fixture as input) yields the minor dimension, and a below, at and above matrix at 19.9, 20 and 20.1 mil applies to the minor dimension only.
- The B6 worker stays unchanged. B6 keeps refusing slots.
- Support for the slot claim requires a fixed-image run of the derivative. A paper statement is not support. The run is a temporary-copy experiment on the existing image, after B6 acceptance, as the lead allows.

## 2. Mask web is not mask geometry

The saved board-setup mask-web setting is a parameter. It is not proof of the actual mask geometry. The supplier condition "minimum soldermask web 4 mil" therefore cannot be satisfied by reading the setting alone.

- The supplier result (r4 section 6.1) gives the mask-web condition the method `geometric_test`, not `setup_read`. The test measures the actual mask openings and the web between them, in the saved board, by a method to be chosen and measured in the fixed image.
- Until that method is measured, the mask-web row of the supplier result is `pending`, and a package that needs it stays unqualified (exit 1). The setting read stays as evidence of the parameter only.
- The acceptance matrix row 5 (mask web 3.9, 4, 4.1 mil) applies to the measured geometric method. It does not apply to the setting.

## 3. Git inclusion of the template history (found during review)

The repository `.gitignore` contains the rule `out/` (line 229). It hides `skills/pcb-design/templates/rc-bare-board/out/`, which holds the preserved interface file that the B6 correction requires. A single negation would unignore every other descendant of that directory too, so the exception re-ignores each parent's other children before the next negation:

```text
!skills/pcb-design/templates/rc-bare-board/out/
skills/pcb-design/templates/rc-bare-board/out/*
!skills/pcb-design/templates/rc-bare-board/out/history/
skills/pcb-design/templates/rc-bare-board/out/history/*
!skills/pcb-design/templates/rc-bare-board/out/history/interfaces/
skills/pcb-design/templates/rc-bare-board/out/history/interfaces/*
!skills/pcb-design/templates/rc-bare-board/out/history/interfaces/*.json
```

Test in a scratch repository (`$S/gitignore-test`, rules appended after the existing `out/` rule):

| Path | Expected | `git check-ignore` exit |
|---|---|---|
| `templates/rc-bare-board/out/history/interfaces/5254508d....json` (required) | not ignored | 1 |
| `templates/rc-bare-board/out/history/interfaces/notes.txt` | ignored | 0 |
| `templates/rc-bare-board/out/history/boards/x.kicad_pcb` | ignored | 0 |
| `templates/rc-bare-board/out/reports/a.json` | ignored | 0 |
| `templates/rc-bare-board/out/history/interfaces/sub/y.json` | ignored | 0 |
| `templates/rc-bare-board/out/export/z.json` | ignored | 0 |
| `out/history/interfaces/h.json` (repository out) | ignored | 0 |
| `examples/pcb-trial/out/history/interfaces/h.json` (other project out) | ignored | 0 |

The real `.gitignore` is not changed until the lead releases the narrow repair. The replacement manifest then records the check of the real repository with the same paths.
