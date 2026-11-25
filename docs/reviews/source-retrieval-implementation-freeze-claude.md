# Source retrieval implementation freeze (claude-skill-dev)

Date: 2026-11-15 UTC. Released by the lead for implementation with the link corrections. Frozen with the agreed tests, the guide, the consumed profiles, and the normalized manifest dependency.

## Implemented

- `skills/pcb-fab-package/scripts/fetch_sources.py`: manifest schema check, every entry validated before the first fetch, a link check on each component of the destination and of the profile path before any read, the resolved profile confined under `supplier/profiles`, the page key and hash compared with the profile, two-status outcomes, the exact magic tokens `markup`, `%PDF`, `PK\u0003\u0004`, `OLE2` and null, and the exit precedence 2, 3, 1, 0.
- `tests/test_source_retrieval.py`: 48 offline tests, including the outside-root symlink (45), the profile-to-pages symlink (47), and the directory link from supplier/profiles into supplier/pages (48). The redirect and 404 cases use a server on 127.0.0.1. No supplier is contacted.
- `skills/pcb-fab-package/SKILL.md`: the command row and the file entry. The row states the exit rule.

## Results

- `uv run tests/test_source_retrieval.py`: 48 of 48, exit 0. Log `docs/reviews/b7-workflow-evidence/test_source_retrieval-run2.log`.
- `uv run tests/test_skill_packages.py`: 8 of 8, exit 0. Log `docs/reviews/b7-workflow-evidence/test_skill_packages-retrieval.log`.

## Dependency (open)

- The release manifest `skills/pcb-fab-package/sources.yaml` in the release worktree still holds full repository-relative profile paths (`skills/pcb-fab-package/supplier/profiles/...`). This command requires `supplier/profiles/<name>.yaml`. Until the release team normalizes those five values, the command refuses that manifest with exit 2. The lead coordinates the normalization. This record does not edit the release worktree.

## Interpretation recorded for check-only

- With `--check-only`, the overall result is "all match" when every fetched entry matches and nothing failed. Otherwise it is "not all match". No write state applies.

## Not claimed

- No live supplier fetch was made.
- The three setup-page entries remain candidates with `null` hashes.
- The consumed profiles and the source bytes are unchanged.

## SHA-256

```
33397ab92b085d28d95b873e78011b9e7d03746105f5a9ee801023fcfd7e0dc3  skills/pcb-fab-package/scripts/fetch_sources.py
58e33eb71bd0ce6d0faa213a42f7bfe9258e1f3efb95114c6a51254dd590c285  tests/test_source_retrieval.py
bb3f5ab2db4cd791ffe6055945c35e2f0c61445958ca9e0016a4d0aa57c5c0bc  skills/pcb-fab-package/SKILL.md
c40fa30c06cb7409a98685259130af65f834ca28b7334fc253a2e783f6194774  skills/pcb-fab-package/supplier/profiles/oshpark-single-layer.yaml
2aedaa0c8076b18005345bf0f56f97396121e1faae915152d5bfcf10a942ad87  skills/pcb-fab-package/supplier/profiles/oshpark-two-layer.yaml
d7b5d3b574c6006f8c9e86831e6fa24fae8b3791136f949ea505ec1f1d6e2af3  skills/pcb-fab-package/supplier/profiles/oshpark-two-layer-hhdc.yaml
3eaddc56d0a81d957c14c997555efaba951507092f7c504c9cf4f25f679e15f5  skills/pcb-fab-package/supplier/profiles/oshpark-four-layer.yaml
382f67e2c3f2a79545fc6d70855c4ae52489319351dc7bd2e0f686bb776fb3f9  skills/pcb-fab-package/supplier/profiles/oshpark-six-layer.yaml
346e3610173d7b85d8a10ff9485e971cb6db7162d1851a569e9df7544c2855d3  docs/reviews/b7-workflow-evidence/test_source_retrieval-run2.log
0b86b756e912fbb29f1b70f54fc1fcd76602632b60769eebc9ea7a0980102bfc  docs/reviews/b7-workflow-evidence/test_skill_packages-retrieval.log
```

Compatibility proposal: `faa31c20ff804c066600333f3d813db3203bda759048a56d9267056d5627d10e`.
