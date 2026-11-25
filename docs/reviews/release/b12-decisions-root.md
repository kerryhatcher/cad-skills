# B12 lead decisions

Date: 2026-11-15 UTC.

The harness directory is `tests/eval/`. The notice file is `docs/release-licensing.md`.
The public skill scope is `pcb-design`, `pcb-fab-package`, and `pcba-design`.
Mechanical exports belong to `pcb-design`. Existing CAD skills get regression tests.

## Matrix and limits

The lead accepts the matrix design, subject to both final interface reviews.
The matrix has 162 routing runs, nine artifact runs, nine matched baselines, 27 explicit-invocation runs, and three compaction runs.
The total is 210 scheduled provider runs. Add 24 local installation checks separately.
Do not add automatic retries. Retain each failed attempt.
Provider execution waits for accepted integrated skill artifacts.

| Run class | Turns | Seconds | Reported tokens |
|---|---|---|---|
| Routing and explicit invocation | 10 | 300 | 30000 |
| Artifact, baseline, and compaction | 30 | 1200 | 250000 |

The batch ceiling is 12000000 reported tokens and 210 scheduled runs.
State the provider's accounting and enforcement limits. Do not claim an exact hard ceiling when a host cannot enforce it.
Stop before another request when the remaining budget is insufficient. Test limits without provider calls.

## Ownership and distribution

Claude owns the harness, README, AGENTS, CI, and shared test configuration changes. Both reviewers write reports only.
The lead owns shared contract changes and their integration.

No built-image publication belongs to this feature.
Image references and dependency declarations are different from redistributed image or package bytes.
Use the license from the exact pinned KiBot source. Retain the conflict with image metadata.
Cite the KiCad design exception for embedded design data. Do not extend that exception to redistributed library collections.
B11 uses project-authored labeled proxies. Keep model provenance explicit if the scope changes.
Record source URLs, hashes, retrieval dates, and applicable license evidence for redistributed content.

Permission for full supplier copies remains unconfirmed. A copyright line alone does not decide all use rights.
Preserve the local evidence. Do not distribute full supplier pages or documents in a release bundle without established permission.
A reviewed fetch-at-setup path can replace those bundled copies. Propose its boundary with the fabrication team first.
Do not delete evidence or change the runtime silently. This open item does not block harness implementation.

Final licensing and artifact acceptance remain separate from interface acceptance.
