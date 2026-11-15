# B11 residual release addendum

Date: 2026-11-15 UTC. Author: claude-mechanical-dev. Basis: `docs/reviews/mechanical/b11-acceptance-complete-root.md` (lead release of the minor wording and test-name correction).

## Retained manifest

The accepted manifest is not changed:

- `docs/reviews/mechanical/b11-residual-batch.sha256`
- SHA-256 `2f264b6790010a58e5771fbb62ee2542c725528ac05bc344baa002fd31a82204`

The other 19 files in the manifest still match their recorded hashes.

## Changed files

Two files changed. Both changes are text only. No test assertion and no implementation code changed.

| File | Old SHA-256 (accepted manifest) | New SHA-256 |
|---|---|---|
| `tests/test_mechanical.py` | `14a5dcb514460e63bc1cc6676f0dcd2e3c4fb9a919cfcbc43ab776974b48132f` | `fbac7436c4bd10421e3107139f74f52baa1602a59b1c42cf652e48691eab32e4` |
| `docs/reviews/mechanical/b11-residual-evidence/RUN-LOG.md` | `a5ba209ae9dd8474c95d185ea714c6eed6326605bfcb751578c62ddb698d8417` | `5de6ce166d17d419da211e4d94ddeb42e3cd02779b23d9d7f73cd44dc26dcd13` |

## Changes made

1. In `tests/test_mechanical.py`, the test method `test_release_id_change_names_fixture_source_first` is renamed to `test_release_id_change_names_release_id_first`. The body, the docstring and the assertions are unchanged. The test checks that a changed `release_id` gives `release.mismatch` with `release_id` and the new value in the message.
2. In `docs/reviews/mechanical/b11-residual-evidence/RUN-LOG.md`, the line for the changed `release_id` now says that it names `release_id` as the first mismatch. The old text named `mechanical/fixture-source.json`.

## Suites

No suite was run again for this release. The lead decided that a name and prose correction needs no repetition.
