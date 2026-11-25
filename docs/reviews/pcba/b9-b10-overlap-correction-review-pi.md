# B9/B10 overlap correction review: Pi

Date: 2026-11-15. Author: pi-pcba-dev.

Subject: `docs/reviews/pcba/b9-b10-overlap-correction-claude.md`, the frozen narrow
correction. Reviewed against the lead's overlap release and Codex's finding. I changed no
product file.

## 1. Result

I accept the correction. Codex's blocker is closed. No blocker remains.

- `uv run tests/test_pcba_design.py`: 71 passed, 0 failed, exit 0.
- All 36 listed file hashes match.
- `sha256sum -c skills/pcba-design/COPY_SHA256.txt`: 15 of 15 copies OK.
- `uv run tests/test_skill_packages.py`: 7 of 8. The failure is only the release-owned
  snippet route.

## 2. Before and after hashes

The correction changed three files. The other 33 files are unchanged.

| Path | Before | After |
|---|---|---|
| `skills/pcba-design/SKILL.md` | `f410fa82a6dddca12e7b2cf76b2969b78c982275e105bebc3adf813b6458fddc` | `69c20a38848a6616d53f84982b0e808c3dab6287d4edbe3e997fb4e589a2777a` |
| `skills/pcba-design/scripts/pcba.py` | `435528f5760d797362866a62a6e31fdada6fe58f760bc40252042141f7d561ad` | `6a7034e4fec3b9815dc23bd8e5c1dd15ac3c0f1226620203910b2443228511a3` |
| `tests/test_pcba_design.py` | `2602a6dd184c696df2d76f7e7479b05807a94f15c723a90e7743347927edbcb3` | `910b12d8c36fdad40a832f636fb02d5f5fa90a2770ab39737df6c1bc61b0fe0f` |

`sierra.py` and all fixtures are unchanged. No shared contract file changed.

## 3. Codex's blocker

The destination overlap check now runs before any capture or write. It compares the real
paths of the destination and `out/pcba/.sierra-staging`:

- equality,
- the destination inside the staging directory,
- the staging directory inside the destination.

Each refuses with `output.path_invalid`. The uncaught `ValueError` from
`project_io.publish_dir` cannot be reached.

Independent probes:

- `--out-dir out/pcba/.sierra-staging`: `output.path_invalid`, exit 1, no traceback, no
  `out` directory.
- `--out-dir out/pcba`: `output.path_invalid`.
- `--out-dir out/pcba/.sierra-staging/x`: `output.path_invalid`.
- A dangling staging symlink: `output.staging_link`, exit 1, no traceback.
- A preexisting staging directory: `output.staging_exists`, exit 1, no traceback.
- A normal positive run: exit 0, and no staging directory remains.

The symlink check uses `os.path.lexists` and `is_symlink`, so a dangling link is caught.
The overlap check uses `resolve`, so a symlinked destination or ancestor is caught.

## 4. Tests

Five new focused tests cover equality, ancestor, descendant, the dangling staging link, and
the existing staging directory. The existing 66 tests still pass.

## 5. Status sentence

The `SKILL.md` Status section now says the skill covers the neutral step and the Sierra
draft command. The stale "neutral step only" sentence is gone.

## 6. Limits

The accepted paths, roles, capture rule and check order are unchanged. The publication
batch with the full manifest, the fabrication Gerber drawing, the drill files, the board
image and the assembly drawing remain later work. The snippet route stays an integration
task.
