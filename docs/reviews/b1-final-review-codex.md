# Final B1 review: Codex

Date: 2026-11-13.

**Decision: accepted**

I accept the frozen final B1 correction. No blocker remains in the agreed scope.

Manifest: `docs/reviews/b1-final-files.sha256`.

Manifest SHA-256: `dbd7c761bcfae4143d1842a34efc3f22b43a36c98a0a8c6843a1ed24593f93fa`.

`sha256sum -c docs/reviews/b1-final-files.sha256` passed for all 17 entries. The manifest identifies this accepted revision.

I read `b1-final-correction-claude.md` and examined the changed schemas, identifier tests, MPN diagnosis, and documentation.

The schemas reject U+0000 through U+001F and U+007F in identifier fields, named-map keys, and units. The correction preserves spaces, Unicode, and prose newlines. It does not impose a generic string ban.

The CLI regressions cover 29 identifier and key locations. Preservation tests exercise Unicode labels, spaces, multiline prose, and extension data. The MPN diagnosis distinguishes a blank value from an invalid type or control character.

**Test evidence**

- `uv run tests/test_pcb_tools.py`: 35/35 passed, exit 0.
- Independent CLI test: all 33 prohibited characters failed in a name, a named-map key, and a unit. All 99 cases gave `schema.invalid`, exit 1, with no unprocessed input.
- Earlier repair regressions passed: exact version and hash boundaries, malformed scalar tags, large integers, strict hash inputs, and supplier limit scopes.

I independently recalculated the original fixed-byte hashes with `printf '%s' ... | sha256sum`. Both remain unchanged:

```text
225bf4f028ae2296b75f18a67cb6adae61f78d2c2f6005866e8de7b3f907c0d4
cbab099b9ffd6ef044f8fce49e98d7b42847e3661c255fb1fb10f107b90cdd0f
```

I did not repeat mechanical suites or review later-batch implementation. Earlier documented limits remain unchanged. I changed only this report.
