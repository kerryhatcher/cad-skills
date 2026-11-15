# B6 final record (claude-skill-dev)

Date: 2026-11-14. Basis: `b6-consolidated-proposal-claude-r3.md`, its revision 3 hash `a46998a5a3f1b72c3a38700638f2b7b3d172e2d731e9428ad0cc4ca938bec48f`. This is the record for the B6 review. The manifest is `b6-final-files.sha256`.

## Host and paths

- Host: `kudzu` (Linux 7.3.3-300.fc45.x86_64). KiCad is not installed on the host.
- Repository: `/mnt/storage/projects/cad-skills`. Session scratch: `/tmp/claude-1000/-mnt-storage-projects-cad-skills/338648c2-5719-486b-b8c3-0bfb3fce6649/scratchpad`.
- Runtime images: the B5 image `localhost/cad-skills-trial:b5`; the B6 image `localhost/cad-skills-pcb:b6` (ID `b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f`); the standalone rebuild `localhost/cad-skills-pcb:b6-rebuild` (ID `032582d4298bfe68b07fde9942c5a92148de90b4a7fe911c095799ffc1eb2285`, built with `--no-cache`, apt installs `ngspice 44.2+ds-1`).

## Measured results

- Focused suite `tests/test_pcb_design.py`: 33 pass, exit 0 (log in scratchpad: `suite-final2.txt`). It covers the template checks, waivers, freshness, refill, interface rebinding and review validation, the GUI integration and its negative summaries, the slot refusal, the four- and six-layer copper declarations, `check --for export`, the external library refusal, the native route inside the image, and the runtime refusals on the host.
- Package tests `tests/test_skill_packages.py`: 8 pass, exit 0.
- Repository suites run at the start of this checkpoint: `test_project_io.py` 11/11, `test_pcb_tools.py` 59/59 (contracts unchanged).
- Standalone rebuild: the image was built from `runtime/Containerfile` with `--no-cache` and measured versions KiCad 10.0.5, ngspice 44.2, uv 0.12.5. In an isolated copy with an explicit lock revision, `env`, `erc`, `drc`, `sim`, `export` and `check` passed. A lock digest mismatch, an explicit different image and a GUI update all exited 2.
- Agent trials (`claude -p`, `claude-sonnet-5-5`, stream-json, same skill copy per trial). Records are in `b6-trials/`.
  - A (first run, failed): the agent hand-edited a hash in the interface file. Recorded for evidence.
  - A2 (failed): the agent edited the board by hand after the manual route. It stayed not ready. Recorded.
  - A3 (passed the readiness check through the GUI route, before the image-ID and staging repairs).
  - A4 (final): R2 changed through the GUI adapter with a predeclared expectation. `check --for ready` exits 0. Checked independently: the board has `20k` in both files, the update result is `pass`, `ready`, identity `equal`, and the GUI trace exists.
  - B (first manual run) and B2 (final): the manual route preserved the board and wrote the handoff. `check --for ready` exits 1, with the reasons `cross.board_pcb_hash_mismatch` and `interface.review_stale`. Checked independently.
  - C and C2: the agent refused to move R2 and asked the user to choose. This is the correct result under the rule "never move a symbol to another sheet".

## Coverage and limits

- Native route: tested inside the runtime image with a native lock. The host route is refused. KiCad is not installed on the host, and no host installation was made.
- Blind or buried via: refused by the worker rule. Not tested with a fixture, because the two-layer and four- and six-layer boards cannot hold one.
- Four- and six-layer boards: fixtures made from the template by `pcbnew`. They test the copper declarations only.
- GUI adapter: certified only for the measured image IDs. The standalone rebuild is not certified.
- Interface: the whole-board comparison is used only for automatic rebinding. The GUI publication does not use it.
- Staged snapshot: each closure file is read once. Its bytes are written to staging, and those bytes are hashed. Live inputs are compared again before publication.
- Staging: removed after success and after handled refusals. Refused runs keep their logs in `out/history/failures/`. Residual staging directories are listed by `check`.

## Deviations and changes recorded

- One bare `python3` edit helper was used during the work. AGENTS.md requires `uv`. The rule now applies to every helper. This is recorded once here.
- `contracts/README.md` changed with the reviewers' agreement. Only project and package path examples now use `${PROJECT}` and `${PACKAGE}`. The skill copy is byte-identical to the source. The scanner is unchanged.
- `--runtime auto|container|native` is implemented. The default is `auto`. `native` on a container lock is a conflict.
- Worker invocations use the agreed `uv run --no-project --no-config --offline --python /usr/bin/python3 python WORKER ARGS` form.
- The template generator now keeps the template README and renames the B5 `trial.*` references to `board.*`. Without this, KiCad rewrote the sheet references on the first GUI save.
- The inventory docstring now describes stdout as the place for structured records. The worker behavior is unchanged.

## Not run in this checkpoint

- The STE checkers named in AGENTS.md (`ste100`, `ste-lint.py`, `ste-cli`) were not run. They need the network through `uvx` or a copy of the ASD-STE100 dictionary.
- The unrelated repository suites (`test_snippets.py`, `test_print_tools.py`) were not repeated, as instructed. `test_project_io.py` and `test_pcb_tools.py` were run at the start of this checkpoint.
- No commit, push or supplier action was taken.
