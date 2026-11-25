# B12 source-path normalization: text correction r3 (text only)

Date: 2026-11-15 UTC. Author: `claude-release-dev`. Type: text-only change record. No executable line changes.
Authority: lead decision, 2026-11-15 03:47 UTC (N-4 text correction).

## Exact diff in `tests/test_release_packaging.py`

Three lines change. Nothing else in the file changes.

1. Docstring of `test_fixture_symlinked_manifest_directory_is_refused`.
   - Old: `"""D-9. A manifest directory reached through a symbolic link, or through a linked parent, is refused."""`
   - New: `"""The parser refuses a linked manifest directory and a linked parent."""`

2. Failure message for a linked manifest directory.
   - Old: `raise AssertionError(f"symlinked manifest directory was not refused: {found}")`
   - New: `raise AssertionError("The parser accepted a linked manifest directory.")`

3. Failure message for a linked parent.
   - Old: `raise AssertionError(f"manifest directory under a linked parent was not refused: {found}")`
   - New: `raise AssertionError("The parser accepted a linked parent.")`

## Unchanged

- `tests/eval/packaging.py`, its D-9 behavior and its finding messages.
- `skills/pcb-fab-package/sources.yaml`, SHA-256 `fd415dc58ab60455c022112105905ede674ce389ba26b025ead80651dbee488f`.
- The test logic and its assertions.
- A1 and A2 files.

Check performed: the file compiles. No functional suite ran, per the lead decision.
