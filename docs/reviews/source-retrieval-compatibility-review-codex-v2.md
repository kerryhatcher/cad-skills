# Source retrieval compatibility review (codex-skill-dev)

Date: 2026-11-15 UTC. This review covers the completed compatibility correction. It does not cover the setup documentation freeze.

Proposal hash: `b2cdf367d932425f9d7914e20385034401b25bf335bdfa7cafe29a3c138796b8`.

## Finding

### Blocker: the profile confinement boundary is not explicit

The proposal confines the profile path and refuses a link on any component. It does not state that the resolved profile path must remain under `supplier/profiles` after resolution.

A profile link can point to another file inside the manifest root, such as a file under `supplier/pages`. A root-only confinement check accepts that path. Confine the resolved path to the `supplier/profiles` directory, or refuse links before the profile read. Add a test for an in-root link from `supplier/profiles` to `supplier/pages`. Confirm exit 2 before fetch and before the read.

## Corrections confirmed

The proposal now keeps `profile_binding` as a profile path. It matches the page stem to `extensions.evidence_pages`, compares the manifest hash with the profile hash, and requires `.html` for bound pages. The magic tokens match the compatibility decision. Tests 45 and 46 cover an outside profile link and a non-HTML page suffix.

The five release profile paths still require normalization before integration. The proposal assigns this change to release, as the lead requested. No code or tests were changed or run for this review.
