# B9 neutral batch review: Pi

Date: 2026-11-15. Author: pi-pcba-dev. Reviewer for the B9 bounded start.

Subject: `docs/reviews/pcba/b9-neutral-batch-claude.md`, the frozen neutral batch for
interface sections 4 to 8. Branch `work/pcba`.

Scope of this review: neutral mapping, variants, neutral rows, BOM and stock. Sierra
conversion, B10 publication, and the alternates rule stay outside. The files are frozen.
I changed no product file.

## 1. Result

The batch is not ready for acceptance. Two path defects are reproducible and break the
capture rule. The repository test suite fails in the batch state, and the cause is now
known. Four smaller items need a decision. The neutral logic itself is sound.

## 2. Defects that block acceptance

### D1. The `components/` boundary is not enforced for a symlink

`check_part_path` examines the text of the map value. `project_io.confine` confines the
target to the project root. Neither step confines the target to `components/`. A symlink
under `components/` that points to a file elsewhere in the project is accepted.

Reproduction:

```bash
cp tests/fixtures/pcba-design/project/components/resistor-10k.yaml /tmp/p/outside.yaml
ln -s ../outside.yaml /tmp/p/components/link.yaml
# set the R1 part path to components/link.yaml
uv run skills/pcba-design/scripts/pcba.py neutral --project /tmp/p --board board.kicad_pcb \
    --variant base --as-of 2026-11-15
```

Result: exit 0. The R1 row uses `components/link.yaml`. Interface section 4 requires a
rejection of a symlink that leaves `components/`.

### D2. `--out` can replace an input file

The step accepts an output path that equals a captured input path.

Reproduction:

```bash
cp -r tests/fixtures/pcba-design/project /tmp/q
uv run skills/pcba-design/scripts/pcba.py neutral --project /tmp/q --board board.kicad_pcb \
    --variant base --as-of 2026-11-15 --out board.yaml
```

Result: exit 0. The board record is replaced by the neutral JSON. Its SHA-256 changes
from `95901a4b284357c2b6507f7eb4d7dcb39a84228587cb6d759c71743cf7a9257a` to
`6f4b0c7acdcbe69caabb59e174ead5bc7189b787199b8d4134df34003cbdf3d3`. The step must refuse an
output path that equals any captured input path.

## 3. Test state

- `uv run tests/test_pcba_design.py`: 20 passed, exit 0. I agree with the result.
- `uv run tests/test_snippets.py`: fails with `FAIL pcba-design [snippet.unrouted]`.
- `uv run tests/test_skill_packages.py`: `test_snippet_routing` fails at line 388.

Cause: `skills/pcba-design` has no entry in `tests/snippet_envs.json`. A clean HEAD
worktree passes `test_snippet_routing` 1 of 1. Thus the batch introduces the failure. The
earlier batch note that the failure is pre-existing is incorrect. The lead assigns the
routing edit to the release workstream. `skills/pcba-design/SKILL.md` has no Python fenced
block, so the routing entry is sufficient.

## 4. Items that need a decision

- The project lock is taken only around the final write. Inputs are captured before the
  lock. Interface section 14 requires the lock from capture through final freshness.
- There is no final freshness rehash before the write. Interface section 14 requires one
  before publication.
- Part identity uses the textual map path. Two spellings of one file become two captures.
  Normalize the path or record the real path.
- `per_board_quantity` is 0 for `exclude_from_assembly` rows. Interface section 6 says 1
  for each reference row. `test_base_rows_match_board_and_sides` asserts 0 for TP1. The
  interface or the code must change.
- The neutral rows lack `datum`, `midpoint_mapping`, per-row `board_quantity`, and
  `selected_alternate`. The BOM grouping key lacks the interface term "assembly
  instruction". Decide if the placement fields wait for the placement batch and if the
  interface term is correct.

The lock and freshness items are section 14 rules. They can wait for B10, but the batch
must not claim them.

## 5. Verified correct

- All 30 listed file hashes match. The record has 30 file rows, not 32. The two extra
  rows in the record are command rows.
- `sha256sum -c skills/pcba-design/COPY_SHA256.txt` passes for all 15 copies. The copied
  `validate.py`, `project_io.py` and `sexp.py` are byte-identical to their sources.
- Rotation normalization keeps the source value and gives 0 for 360 and 270 for -90.
- The three population states, the hand-installed rule, the BOM split, and the stock
  statuses match sections 5, 6 and 8.
- A path that leaves the project root is refused.

## 6. Verdict

Correct D1 and D2 before acceptance. Decide the items in section 4. The snippet routing
edit belongs to the release workstream. Alternates remain incomplete and stay outside this
start.
