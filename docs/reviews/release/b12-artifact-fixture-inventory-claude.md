# B12 artifact fixture and authenticated-route inventory

Date: 2026-11-15 UTC. Author: `claude-release-dev`. Type: read-only inventory. No product edit. No provider call. No suite run.

## 1. Restoration

- Branch: `work/release`. Working directory: `/mnt/storage/projects/cad-skills-worktrees/release`.
- Freeze: `docs/reviews/b12-final-local-repair-freeze-claude.sha256` has SHA-256 `efbf8f6144aef87d7cca5f8438ed8f1b94b6a40acbf083d42510ba6e72a1717b` and 41 entries. Checked now.
- Lead acceptance record: `docs/reviews/release/b12-local-adapter-acceptance-root.md`.
- Correction applied: no real HOME authenticated route is established or approved. The temporary HOME is stub-only.
- Provider authorization: zero.
- Herdr: `/proc/482044/exe` (0.8.0, protocol 19). Lead pane: `w1P:p3`. This pane: `w1P:p9`.

## 2. Artifact fixtures

The matrix `tests/eval/matrix.yaml` lists A1, A2 and A3 with `frozen: false`. No fixture is frozen.

### A1: pcb-design (candidate ready, lead confirmation needed)

- Candidate: `skills/pcb-design/examples/rc-edit/`.
- Files in `before/`: `board-interface.json`, `kicad/board.kicad_pcb`, `kicad/board.kicad_pro`, `kicad/board.kicad_sch`, `kicad/fp-lib-table`.
- Files in `after/`: `kicad/board.kicad_pcb`, `kicad/board.kicad_pro`, `kicad/board.kicad_sch`, `kicad/fp-lib-table`.
- Measured difference (`diff -r`, read only): R2 value `10k` changes to `20k`. The change appears in `board.kicad_pcb` (line 1099) and in `board.kicad_sch` (line 980).
- Gap: `after/` has no `board-interface.json`. The README says `after/` holds the same files with only R2 changed. The README also says `before/` holds the interface file. The README and the tree disagree.
- Lead decision needed: confirm A1, and choose one of these. (a) Copy `board-interface.json` into `after/` unchanged. (b) Record the missing file as an exception.
- The identity comparison in the README was not run. That step belongs to the fixture freeze.

### A2: pcb-fab-package (no fixture yet)

- No complete valid KiCad input project exists in `skills/pcb-fab-package/` or `tests/fixtures/pcb-fab-package/`. That fixture set holds a PNG, inventory JSON, mask `.gts` files and slot `.drl` files only.
- Candidate: `skills/pcb-design/templates/rc-bare-board/kicad/` (`board.kicad_pro`, `board.kicad_pcb`, `board.kicad_sch`, `fp-lib-table`). The README states it was saved by KiCad 10.0.5 and is clean in ERC and DRC. This was not checked here.
- Constraint: this candidate belongs to `pcb-design`. `AGENTS.md` forbids a skill to use a file from a different skill. A2 therefore needs a copy that the fixture set owns. Lead decision needed.
- Dependency: `pcb-fab-package` is not integrated and accepted (`integrated_accepted: false`). `skills/pcb-fab-package/sources.yaml` is untracked.

### A3: pcba-design (not started)

- `skills/pcba-design/` does not exist in this worktree.
- The PCBA work runs in another worktree: `/mnt/storage/projects/cad-skills-worktrees/pcba` (panes `w1P:p7`, `w1P:pA`, `w1P:pD`). It is outside this inventory.
- A3 stays blocked until the PCBA implementation is accepted.

## 3. Authenticated-route interfaces

| Interface | Current state | Source |
|---|---|---|
| Real HOME mount | Not present. No real HOME is mounted or exposed. | `tests/eval/sandbox.py` lines 9 to 13 |
| Temporary HOME | Exists only in the run root (`/work/home`). For credential-free stub tests only. | `tests/eval/sandbox.py` line 136 |
| User-scope install | Copies into `<root>/home`. The real home is never used. | `tests/eval/isolate.py` lines 10, 81 |
| Host command builders | No credential flag. No model flag. No HOME override. No trust bypass. | `tests/eval/adapters.py` lines 71 to 93 |
| Codex sandbox mode | Host default kept. Not measured. | `tests/eval/adapters.py` lines 1 to 40 |
| Codex baseline | Refused for measured evaluation. User-level skill set unmeasured. | `baseline_policy`, `tests/eval/adapters.py` |
| Claude baseline | Allowed with disclosure. `--disable-slash-commands` disables skills and commands. The real HOME is kept. | `baseline_policy`, `tests/eval/adapters.py` |
| Pi baseline | Allowed. `--no-skills`. | `baseline_policy`, `tests/eval/adapters.py` |
| Discovery, selection and token usage | Unavailable. No measured host output schema. | `tests/eval/adapters.py` header |
| Provider dispatch | Refused. `paid_batch_authorized: false`. | `tests/eval/run_case.py` lines 53 to 65 |

Still missing for an authenticated route:

1. A measured host configuration and credential preservation check.
2. A measured Codex sandbox mode.
3. A measured Codex user-level skill set.
4. A measured output schema for each host.

## 4. Open lead decisions

1. Confirm A1, and choose a repair or an exception for the missing `after/board-interface.json`.
2. Choose the owner of the A2 KiCad project copy. The `pcb-design` template cannot be used in place.
3. Keep A3 blocked until the PCBA implementation is accepted.
