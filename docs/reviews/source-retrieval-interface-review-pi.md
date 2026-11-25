# Source retrieval interface review (pi-skill-dev)

Date: 2026-11-15 UTC. Scope: `docs/reviews/proposals/source-retrieval-interface-claude.md`,
SHA-256 `f133fc072217e7b8b0bb9917a602ad0df046046e769a77ebc6049759f7cc8874`.
I changed no product file. I ran no broad suite. This is a review of a proposal.

## Confirmed changes

The revised proposal contains the requested changes:

- The destination is `DIR/<full manifest path>`. The `supplier/` prefix is not stripped.
- A write requires `--dest` to equal the manifest root.
- A `profile_binding` entry resolves under the root `supplier/pages`.
- The code has no hardcoded repository path.
- The strict parser, `project_io.confine` and `project_io.atomic_write` are reused.
- The multi-entry outcome is explicit. A partial result lists the written entries.
- A skipped entry is never a match. A null hash is a candidate, not an accepted entry.
- A changed page is never accepted. The command does not edit the manifest or a profile.
- There is no license gate.

## Exit rules

1. **Precedence is not defined.** The rules overlap. A run with a fetch failure and a changed
   entry matches both `1` (a changed entry) and `3` (a fetch failure). State one order, for
   example `2`, then `3`, then `1`, then `0`.
2. **The skipped entry exit is not defined for `--check-only`.** The rule gives exit 1 for
   `skipped while a write was requested`. The exit for a skipped entry when no write is
   requested is absent. State it. For example, a skipped entry is allowed, and it does not
   prevent exit 0 when the other selected entries match.
3. **The magic mismatch label is inconsistent.** The outcome table reports it as `refused`.
   The exit rules use exit 1 for a magic mismatch and exit 2 for a refused path or a wrong
   `--dest`. Use the label `magic mismatch` in the table.
4. **These cases have no exit rule:**
   - an unknown `--entry ID`.
   - an empty manifest.
   - a duplicate `path` under two entries.
   - an absolute entry path or a `..` segment. Test 6 covers a link only.
   - `--dest` that differs from the manifest root during `--check-only`. The proposal says
     the path is unused. State the exit (0 or the check result).
5. **`--check-only` outcomes are not stated.** A match writes nothing and exits 0. A
   candidate writes nothing and exits 1. State both.

## Tests

The twelve tests are a good base. These gaps are concrete:

- Test 9 does not state the exit code. Add the expected exit for a skipped entry with and
  without a write request.
- Test 6 uses a link at the destination file. Add a link at a parent directory of
  `DIR/<path>`, because the parent chain matters for confinement.
- Add a test for an absolute path and a `..` segment in an entry `path`.
- Add a test for a duplicate `path` under two entries.
- Add a test for an unknown `--entry ID`.
- Add a test for `--check-only` with a match. The file must not be written, and the exit
  must be 0.
- Add a test for a mixed run: one fetch failure and one changed entry. This test pins the
  precedence.
- Test 12 must also show that a match with a changed `license_state` still writes the file
  and exits 0.

## Manifest format

The proposal and the frozen manifest do not agree.

- The proposal says `schema: cad-skills/sources`, `schema_version: 1`.
- The frozen `docs/reviews/proposals/sources.yaml` uses
  `schema_id: cad-skills/supplier-sources`, `schema_version: "1.0"`.
- The proposal adds `path`, `magic`, `profile_binding` and `distribution_decision`.
- The proposal drops `title`, `retrieved` and `review_status`.

Reconcile the schema id, the version and the field set with the frozen manifest. State
whether the strict parser rejects the old fields or keeps them.

`magic` is only defined for `markup`. Define the allowed values. Refuse an unknown value
with exit 2.

## Verdict

The proposal is a good base. It is not accepted yet. Define the exit precedence and the
missing outcomes. Reconcile the manifest schema. Add the missing tests. The requested
changes are present, and no profile change or license gate is necessary.

No product edit. I hold for the revised proposal or the frozen implementation.