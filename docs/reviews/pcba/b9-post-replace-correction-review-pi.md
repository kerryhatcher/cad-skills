# B9 post-replace correction review: Pi

Date: 2026-11-15. Author: pi-pcba-dev. Reviewer for the B9 bounded start.

Subject: `docs/reviews/pcba/b9-post-replace-correction-claude.md`. Scope: the
post-replace case only. I changed no product file.

## 1. Result

I accept the correction. No blocker.

- `uv run tests/test_pcba_design.py`: 41 passed, 0 failed, exit 0.
- All 30 listed file hashes match.
- `sha256sum -c skills/pcba-design/COPY_SHA256.txt`: 15 of 15 copies OK.
- The shared snippet route remains the release-owned integration item.

## 2. Before and after hashes

| Path | Before | After |
|---|---|---|
| `skills/pcba-design/SKILL.md` | `a7315a7b6c3dd7a504268cfb18b57edc3a2a8ec11f1e1dbd22f77337d01e759d` | `3fb2f9de791c938879f9cf82abada1e85a2e64dc49c70de2b72a15e2728d5146` |
| `skills/pcba-design/scripts/pcba.py` | `8cda4a6b473a8f98b095f78b23d749cf07061364ebb688aa9618440b4a6ee5b7` | `30ae7d359c1c3977c31519238d6c03020c81223b87d7443e44322a58f131e3a3` |
| `tests/test_pcba_design.py` | `2adf25817a32ab75acfbaa30de2f4969bbb32a64f0eae1ac433a8334633a5010` | `e21e06d81bc15ee755164fd0d164a070acca3648f60257aa360ec527947a5cb6` |

The other 27 files are unchanged. The interface file stays at
`36d7e1b0917417d6e537db57fd46a92d4b949303e1d13d5f40b93e0a29b1d361`.

## 3. Agreed terms

| Term | Result |
|---|---|
| Exit 1 | Pass |
| Status `failure` | Pass. It no longer collides with the exit-2 argument status `error`. |
| Finding `output.replaced_then_failed` | Pass |
| `output_replaced` true | Pass, at the top level next to `status` and `findings`. |
| Message states new bytes in place and synchronization failed | Pass |
| No refusal or rollback claim | Pass |
| Specific `PostReplaceError` catch before `OSError` | Pass |
| Exception information passed to `main` | Pass. The message keeps the original cause. |
| Controlled post-replace test | Pass |
| Ordinary pre-write failure unchanged | Pass. It stays `refused` with `output.write_failed`. |
| Exit description is `1 failure` | Pass in the docstring and `SKILL.md`. |

## 4. Independent probe

I triggered the real path, not a fabricated exception. I replaced
`project_io._sync_directory` with a function that raises `OSError(5, ...)`. The real
`atomic_write` then raises `PostReplaceError`.

Result: exit 1. Status `failure`. `output_replaced` true. One finding
`output.replaced_then_failed`. The message names the output, states the new bytes are in
place, states the synchronization failure, and keeps the cause text. The output file
exists and holds the new bytes.

The focused test fabricates the `PostReplaceError` through a wrapped `atomic_write`. That
covers the `build` to `main` handling. My probe also covers the `atomic_write` translation.
Together the two paths are covered.

## 5. Limits

- Alternates and the placement fields stay outside the batch.
- The shared snippet route for `pcba-design` is an integration task. Release owns it.
- This acceptance covers the post-replace case and the earlier repairs. It does not cover
  Sierra conversion or B10 publication.
