# Continuation record (claude-skill-dev)

Date: 2026-11-14. Written before context compaction. Read this file first after a reset.

## Rules

- No commit, push or supplier action. The repository has uncommitted feature files; keep them uncommitted.
- Do not restart the environment, the container runtime or the Herdr server. Herdr messages go through `/proc/482044/exe agent prompt w1P:p3 "[prefix] ..."`, with the prefix `[date - time UTC] To: skill-dev-lead; From: claude-skill-dev -`.
- Do not repeat accepted tests or the 41-test affected suite unless a file in its scope changes.
- Use `uv` for every Python command. Capture a test's exit directly (`cmd > log 2>&1; echo $?`), not through a filter.
- No B6 feature expansion. B6 supports the measured subset only.

## Frozen hashes (current)

| File | sha256 |
|---|---|
| `docs/reviews/b6-replacement-files.sha256` (current manifest, 211 entries) | `f93454c545a355e43be3e447b41baa334299dbf09bb08fff4c57ab3f234aca39` |
| `docs/reviews/b6-correction-files.sha256` (210-file history) | `ab6a32f676fb66ae28ccf7d1ff47e619e4f83506bf6210bc3fe7fd98e16e4b3d` |
| `docs/reviews/b6-correction-record.md` | `d021a48200f0cd0857697bf5effa64da03caa877f19daaaaff48316edbaf782b` |
| `docs/reviews/b6-native-repair-record.md` | `2e8f4e2031a19bbf552ee366f0c5f38ce591890dff416f5f684fe52108f73481` (written after the replacement manifest, so outside its 211 entries) |
| `docs/reviews/b6-continuation-record.md` | `ac5f9cac27cc2e3f2398441549b31657c0f3edbdde058b79865115b9e24482b8` (outside the 211 entries) |
| `skills/pcb-design/scripts/pcb.py` | `0928be463f6503b41d5c7ba02c076556c0ac750630da63ac8c86866cf664cabe` |
| `tests/test_pcb_design.py` | `242176ead31847772750c58b224933178e2e1bc265ca8245909912de87aebe6c` |
| `.gitignore` | `6b3a6acf3bb8b3ee922cbf3b7e9c57224a86226b04fae0b0ea5a9f89b1ac2a0c` |

## Completed tests (exit codes captured directly)

- Affected B6 suite, 41 tests: exit 0 (before the native repair; not rerun).
- Native (3), runtime (2), Git exception (1), package-copy suite (8): exit 0 after the native repair.
- Replacement manifest check: `sha256sum -c` exit 0, 211 entries.
- Linter (local structural, `/tmp/cad-skills-ste-lint.py`): 42 findings before the prose repair, 0 after (`b6-lint-before.txt`, `b6-lint-final.txt`).

## Accepted decisions

- Operation-specific probes: `erc` needs kicad-cli only; `sim` needs ngspice only; `export` needs kicad-cli and pcbnew. A missing tool is exit 2 with no traceback.
- Staging: a residual per-operation directory is `staging.residual` (exit 1); an empty parent is no finding.
- Interface evidence: manual review carries `prior_interface_sha256` (full hash or null) with read and write coverage; automatic evidence checks the prior board and expectation bytes; strict JSON with duplicate-key rejection.
- Assertions: strict JSON, whole-string identifiers, numeric range 1e12, `assertion.malformed` (exit 1).
- Template history: `templates/rc-bare-board/out/history/interfaces/*.json` is tracked by a template-only negation in `.gitignore`, with regression test.
- The local linter is structural, not STE certification. Its 42 findings were examined individually and fixed in prose.
- The independent 1 ms RC result (1.298448 V against the 1.2984 V target, tolerance 0.012984 V) is retained (`b6-rc-review-root.json`). The A4 project's own assertion is at 2 ms; that deviation is recorded.
- Standalone rebuild (`--no-cache`, image ID `032582d4298bfe68b07fde9942c5a92148de90b4a7fe911c095799ffc1eb2285`) evidence is in `b6-standalone-evidence/INDEX.md`.
- Blind-via refusal is untested, not impossible: four- and six-layer boards can hold blind and buried vias, and no blind-via fixture exists yet.

## Temporary runtime paths (scratchpad, session-specific)

Scratchpad root: `/tmp/claude-1000/-mnt-storage-projects-cad-skills/338648c2-5719-486b-b8c3-0bfb3fce6649/scratchpad`

- Standalone copies: `standalone-logged/` (project, mismatch, skill).
- Smoke trials: `smoke/A`, `A2`, `A3`, `A4`, `B`, `B2`, `C`, `C2`; copies retained in `docs/reviews/b6-trials/`.
- Independent RC copies: `independent-rc/`.
- GUI integration project: `guiproj/`.
- Native repair pre-state: `pcb-before-native-repair.py`.

Images: `localhost/cad-skills-pcb:b6` (`b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f`), `localhost/cad-skills-pcb:b6-rebuild` (`032582d4298bfe68b07fde9942c5a92148de90b4a7fe911c095799ffc1eb2285`), `localhost/cad-skills-trial:b5` (B5 image, not used by B6 controller).

## B7/B8 status (updated)

- Revision 5 consolidates r4, its addendum, the slot export inspection and the mask geometry method: `docs/reviews/b7-b8-proposal-claude-r5.md` (sha256 `32c77100a31010be95d2d84ad5165ac8c5481e140a4f3c6612bc73f5693cd045`). It awaits explicit reviewer agreement. No B7 implementation before that agreement.
- Mask research input: `docs/reviews/b7-mask-research-root.md` (merged openings are a distinct condition; a removed pre-export gap is not a manufacturing failure).

- Paper: `docs/reviews/b7-b8-proposal-claude-r4.md` is under review (sha256 `0a9a289ef39a1333cea8a37849c3b62769b1e6ef11bacac98a46ec9ab2258f93`). Revisions r1 and r2 are historical, and r3 (`bfddf334dde597425542efb1fb458244013c874277e90625be5423eb187d4676`) is kept.
- Addendum: `docs/reviews/b7-b8-r4-addendum-claude.md` (slot-capable owned derivative, mask-web geometry, template Git exception) (sha256 `bdb3fb38127ec17c2b41015c74014a150a4e9072845d38fd658bd878c8a39783`).
- Pending: consolidate r4 and the addendum with the reviewers' feedback on exact roles, mandatory source-review evidence, and the slot export endpoints and orientation. The B6 Excellon parser is circular-only, so slot endpoints and orientation are not verified by B6.
- No B7/B8 implementation before both reviewers agree to the concrete revised interface.

## Remaining prerequisite trials (not started; after B6 acceptance)

- Fixed-image KiCad experiments: `.kicad_pro` rule-severity field name; solder-mask geometry method; slot-capable inventory derivative with endpoints and orientation; schematic PDF and fabrication drawing commands.
- These may use temporary copies of the existing image. They do not block paper design.

## Update: prerequisite trials and revision 6 (after the B6 acceptance)

- Trial record: `docs/reviews/b7-prereq-trials-claude.md` (rule file basename and severity measured; slot records measured; PDF commands measured; mask construct inventory measured). Exact-distance mask code not yet measured.
- Consolidated paper: `docs/reviews/b7-b8-proposal-claude-r6.md` (sha256 `1cb84bbdb311edf827380fa0a358a43b96f97c3062048fa12485c6a536db470b`). It replaces r4, r5 and the addendum for implementation. Those remain as history.
- Remaining before B7 implementation: reviewer agreement to r6; the exact-distance measurement; the exclusion format; the fabrication drawing command on the fixed image.
- Deviation to keep recorded: three bare `python3` reads in the trials. All later commands use `uv`.
- No commit. Accepted B6 files are unchanged.
