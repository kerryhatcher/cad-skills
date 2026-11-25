# B9 final neutral repair review: Pi

Date: 2026-11-15. Author: pi-pcba-dev. Reviewer for the B9 bounded start.

Subject: `docs/reviews/pcba/b9-final-neutral-repair-claude.md`, the frozen replacement
batch. Authorization: `docs/reviews/pcba/b9-final-neutral-repair-root.md`.

Scope: the five repair items only. Alternates, Sierra conversion, B10 publication and
the shared snippet route stay outside. I changed no product file.

## 1. Result

I accept the batch. The five repair items are present and correct. No blocker remains.

- `uv run tests/test_pcba_design.py`: 40 passed, 0 failed, exit 0.
- All 30 listed file hashes match.
- `sha256sum -c skills/pcba-design/COPY_SHA256.txt`: 15 of 15 copies OK.
- The snippet routing failure is only the known release-owned integration item.

## 2. Before and after hashes

The repair changed three files. The other 27 files are unchanged.

| Path | Before | After |
|---|---|---|
| `skills/pcba-design/SKILL.md` | `da3d22eb0cd74078fbb35ae175126f3595e7e265b8d4802d53b1a6e3315ec91f` | `a7315a7b6c3dd7a504268cfb18b57edc3a2a8ec11f1e1dbd22f77337d01e759d` |
| `skills/pcba-design/scripts/pcba.py` | `1e69b6f3bced2cb9b30556829a6ced51b6d8330a0a1c1353239e2033bc3471a4` | `8cda4a6b473a8f98b095f78b23d749cf07061364ebb688aa9618440b4a6ee5b7` |
| `tests/test_pcba_design.py` | `123592419d4cbe7a7ee3953a8e1ffb09bccc0e8cac6912c8326689efc905b454` | `2adf25817a32ab75acfbaa30de2f4969bbb32a64f0eae1ac433a8334633a5010` |

The interface file is unchanged at
`36d7e1b0917417d6e537db57fd46a92d4b949303e1d13d5f40b93e0a29b1d361`.

## 3. The five repair items

| Item | Result | Evidence |
|---|---|---|
| 1 `SKILL.md` wording | Pass | The board row says the numeric fields are derived finite numbers and only `source_tokens` keeps the exact source text. |
| 2 held-lock regression before capture | Pass | With a broken board record and a held lock, the run gives `project.locked`. A capture before the lock would give `stock.policy_missing`. The test proves the lock comes first. No output. |
| 3 CLI boundary for output errors | Pass | `output_target` catches only `PathEscape` and `OSError`. `build` catches `OSError` only around the atomic write. No broad handler. |
| 4 one `output.path_invalid` finding | Pass | An escaping path and a directory output each give one finding. |
| 5 alias finding names the requested path | Pass | `--out board.yaml` names `board.yaml` in the `file` field and the message. |

## 4. Independent probes

- `--out ../escape.json`: exit 1, one `output.path_invalid` finding, no traceback, no
  file outside the project.
- `--out components`: exit 1, one `output.path_invalid` finding, no traceback. The
  directory is unchanged.
- `--out board.yaml`: exit 1, one `output.aliases_input` finding. The `file` field is
  `board.yaml`. The input bytes are unchanged.
- Unwritable output directory (`chmod 500`): exit 1, one `output.write_failed` finding,
  no traceback. The process runs as uid 1000, so the case is exercised.
- Held lock and a broken board record: exit 1, one `project.locked` finding, no traceback.

## 5. Non-blocking note

`project_io.atomic_write` can raise `PostReplaceError` after the new bytes are in place,
when the later directory synchronization fails. `PostReplaceError` is an `OSError`, so
`build` reports `output.write_failed` and the run exits 1. In that case the output is in
place, and the message says it cannot be written. Also `err.strerror` is None for that
class, so the message ends with `None`. This is rare, and it is outside the five repair
items. A later batch can catch `PostReplaceError` separately or let it propagate.

## 6. Limits

- Alternates remain incomplete. `selected_alternate` is empty.
- The placement fields `export_rotation_deg` and the midpoint estimates are not produced.
- The shared snippet route for `pcba-design` is an integration task. Release owns it.
- No supplier file and no manifest is written.
- This acceptance covers the five repair items and the earlier 15 items. It does not
  cover Sierra conversion or B10 publication.
