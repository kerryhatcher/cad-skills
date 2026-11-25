# Source retrieval implementation review (codex-skill-dev)

Date: 2026-11-15 UTC. This review covers implementation freeze `docs/reviews/source-retrieval-implementation-freeze-claude.md`, SHA-256 `386106caae33fc9347d6e6cbafe07392aa50763992d6d41f9067d5c4a89448c8`.

## Freeze and test evidence

All ten entries in `docs/reviews/source-retrieval-implementation-files.sha256` pass. The code hash is `33397ab92b085d28d95b873e78011b9e7d03746105f5a9ee801023fcfd7e0dc3`. The test hash is `58e33eb71bd0ce6d0faa213a42f7bfe9258e1f3efb95114c6a51254dd590c285`.

The retained logs report 48 of 48 retrieval tests and 8 of 8 skill-package tests. This review did not rerun those suites.

## Blocker: a destination can replace a protected input

The command does not compare output paths with the manifest path or profile paths. A source entry can set `path` to `./sources.yaml`. The command reads the manifest, fetches the source, and atomically replaces that manifest. It exits 0.

I ran a focused offline probe for that path and for `supplier/profiles/./fixture.yaml`. Both runs fetched once, replaced the protected file, and exited 0. The probe source is `docs/reviews/source-retrieval-input-alias-probe-codex.py`, SHA-256 `41ed85a251b391b8516b0760307361a9666a119d7feb434caccd4f975b39e835`. Its result is `docs/reviews/source-retrieval-input-alias-probe-codex.json`, SHA-256 `db98bc9ed7b8c1d459bda0183148eb165d6c11b3ce0dc40b5dd75ad9a0c535e5`.

Before any fetch, compare each resolved destination with the resolved manifest path and all profile paths in the manifest. Refuse any alias with exit 2. Add tests for the manifest path and a profile path. Each test must confirm exit 2, zero fetch calls, and unchanged protected bytes.

## Compatibility corrections confirmed

The implementation refuses links on destination and profile paths. It confines profile targets under `supplier/profiles` and refuses a profile target under `supplier/pages`. It checks the profile page key and hash. It uses the required magic tokens and reports both content statuses. Tests 45–48 cover the added link cases.

The release manifest normalization remains a documented dependency. Release owns that change.

## Review result

Protect the manifest and profile files from destination aliases before fetch. Keep the existing confinement checks and the release-owned manifest normalization separate. The frozen implementation hashes remained unchanged during the focused probes.
