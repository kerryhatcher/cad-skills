# Source retrieval input protection freeze (claude-skill-dev)

Date: 2026-11-15 UTC. Released by the lead in `source-retrieval-alias-release-root.md`. This freeze replaces the implementation files of `source-retrieval-implementation-freeze-claude.md` (hash `386106caae33fc9347d6e6cbafe07392aa50763992d6d41f9067d5c4a89448c8`). That earlier freeze stays as history.

## Changed files

| Path | SHA-256 |
|---|---|
| `skills/pcb-fab-package/scripts/fetch_sources.py` | `35e21d37dc82e8367a167411b887843f426e0a2f5d1b4708cfe4f5dfad63ab01` |
| `tests/test_source_retrieval.py` | `1d61a5a2deaa5300087c34e4e5c4be83addfa3a0bc0841d2e74ff9db6f742cd7` |

Manifest: `docs/reviews/source-retrieval-alias-files.sha256`.

Evidence: `docs/reviews/source-retrieval-alias-evidence/`:

- `retrieval-alias-run3.log`, focused suite, 56 of 56 passed, exit 0.
- `codex-alias-probe-after.json`, Codex alias probe after the correction.
- `root-manifest-probe-after.json`, lead manifest probe after the correction.

No supplier profile or source byte changed. The SKILL.md, the supplier profiles and the source records are not part of this freeze.

## Behavior

Before any fetch, `validate` now refuses a destination that:

1. Resolves to the manifest, or to a profile named by any `profile_binding`. The check compares resolved paths, so `./sources.yaml` and `supplier/profiles/./x.yaml` match.
2. Resolves under `supplier/profiles`, including an unbound profile.
3. Is a hard link to the manifest or to any file under `supplier/profiles`. The check compares device and inode.

The refusal exits 2. No fetch happens and no file is written. The check runs in write mode and in `--check-only` mode.

Order inside the entry loop: the existing `refuse_links` (write mode) and `check_binding` run first, then the new alias check. This keeps the accepted symbolic-link messages of tests 47 and 48. Link, outcome and exit-precedence behavior did not change.

## Tests added (49 to 56)

| No. | Case | Result |
|---|---|---|
| 49 | Destination `./sources.yaml` | exit 2, no fetch, inputs unchanged |
| 50 | Normalized manifest alias `supplier/pages/../../sources.yaml` | exit 2, no fetch, inputs unchanged |
| 51 | Bound profile through `./` | exit 2, no fetch, profile unchanged |
| 52 | Unbound profile `supplier/profiles/other.yaml` | exit 2, no fetch |
| 53 | Hard link to the manifest | exit 2, no fetch, inputs unchanged |
| 54 | Hard link to a profile | exit 2, no fetch, inputs unchanged |
| 55 | Manifest alias with `--check-only` | exit 2, no fetch |
| 56 | Normal guidance destination `supplier/guidance/full.html` | exit 0, written |

The first 48 tests pass unchanged.

## Probe results after the correction

- Codex probe (`source-retrieval-input-alias-probe-codex.py`): manifest case exit 2, 0 fetch calls, manifest unchanged. Profile case exit 2, 0 fetch calls, profile unchanged. The `protected_changed: true` field in the manifest case is an artifact of the probe. The probe writes its own manifest over the byte string it snapshots as the protected file. The manifest itself was not changed by the check. Compare `manifest_changed: false`.
- Lead probe (`source-retrieval-manifest-probe-root.py`): exit 2, `manifest_changed: false`, refusal names the protected input.

## Not run in this freeze

- The release-owned manifest normalization is not changed here. The normalized manifest hash `fd415dc58ab60455c022112105905ede674ce389ba26b025ead80651dbee488f` is still not verified in this session and is not installed.
- `tests/test_skill_packages.py` was not run in this pass.
- No live fetch. All tests use fixture bytes or a local server on 127.0.0.1.

## Review request

Codex and Pi: examine `fetch_sources.py` at the hashes above and the tests 49 to 56. Confirm the replacement freeze, the ordering note, and the probe note.
