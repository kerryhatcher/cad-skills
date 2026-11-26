# Release checklist

## 1. Purpose

This checklist gives the steps before a release of the skills.
The lead does each step by hand.

## 2. Local checks

Run each command from the repository root. Run one command at a time.

```sh
uv run tests/test_snippets.py
uv run tests/test_print_tools.py
uv run tests/test_pcb_tools.py
uv run tests/test_project_io.py
uv run tests/test_skill_packages.py
uv run tests/test_release_packaging.py
uv run tests/test_release_harness.py
uv run tests/test_release_isolation.py
uv run tests/test_artifact_fixtures.py
uv run tests/test_artifact_expectations.py
uv run tests/test_source_retrieval.py
uv run tests/test_recheck_sources.py
for t in tests/test_pcb_fab_*.py; do uv run "$t" || break; done
```

The `test_pcb_fab_*` files use one KiCad container. The loop runs them one after the other.

## 3. Live source re-check

Do this step before each release. Do not run it in CI. The command contacts the supplier pages.

```sh
cd skills/pcb-fab-package
uv run scripts/recheck_sources.py --manifest sources.yaml > ../../docs/reviews/source-recheck-YYYY-MM-DD.md
```

Add the option `--allow-ci` only when the shell sets the `CI` variable.
Without this option, the command does not run in a CI shell.

The command writes no file. Use the `>` symbol to send the report to a file.
The report holds hashes and status values, and no supplier text.
Do not commit the report without the lead's approval.

| Exit | Result | Next step |
|---|---|---|
| 0 | The hash of each fetched page matches the recorded hash, or only the layout changed (`layout`). | No new source review. For `layout`, do not edit the profile. |
| 1 | A page changed, has no recorded hash, or has an incorrect magic token. | Follow "If a page changed". |
| 1 | The bytes match, but the text hash does not match the visible text (`text-mismatch`). | Follow "If a page changed". |
| 2 | An argument, manifest, binding or watch problem. The command fetched no page. | Repair the problem. Run the command again. |
| 3 | A fetch failed. The report also gives the pages that changed. | Follow "If a fetch failed". |

## 4. Watch items

A hash cannot examine the notes on two OSH Park pages.
A hash shows that a page changed. A hash does not show the change.

| Entry | Service | Date | Examine |
|---|---|---|---|
| `oshpark-four-layer-html` | Four-layer service | 2026-01-28 | The temporary alternate stackup note. |
| `oshpark-six-layer-html` | Six-layer service | 2025-12-15 | The lead time changed on this date. |

Read these two live pages by hand at each release, also when the hash is the same.

## 5. If a page changed

1. Do not change the profile.
2. Read the live page. Write the observations.
3. Run `fab.py review-source` with the observations. Keep the review hash.
4. If a rule value changes, change the profile in a separate commit. Then change the hash in `sources.yaml` and in the profile `evidence_pages`.
   When you change the `sha256` of an entry, also examine its `text_sha256`.
   If the entry is `markup` and `observed_text_sha256` is not `null`, write this value as `text_sha256` in `sources.yaml`.
   If the entry is not `markup` or the value is `null`, do not write `text_sha256`.
5. Run `fetch_sources.py` again. Then run the re-check again. The re-check must give exit 0.

## 6. If a fetch failed

Run the re-check again. If the failure continues, examine the URL by hand.
Record the result in the release notes.

## 7. Distribution

The full supplier copies stay out of distribution.
Read `docs/release-licensing.md` for the distribution decisions.
