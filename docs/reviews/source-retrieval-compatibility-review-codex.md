# Source retrieval compatibility review (codex-skill-dev)

Date: 2026-11-15 UTC. This review covers the compatibility revision named by `source-retrieval-compatibility-root.md`. It does not cover the setup-document freeze.

Proposal hash: `4dd920c6aac29d9c94b03fff2797c1de07e90b72756e79cbb32569d0293549e5`.

## Finding

### Blocker: the profile path is not confined before the read

The proposal confines `DIR/<path>`. It reads `profile_binding` to check `extensions.evidence_pages`, but it does not require `project_io.confine` for that profile path.

The release rule says to confine both paths. Confine the profile under `supplier/profiles` before the read. Refuse a path that escapes through a symbolic link. Add an offline test with a profile path that links outside the manifest root. Confirm exit 2 before fetch and no outside write.

## Compatibility examined

The five release profile records store page evidence under `extensions.evidence_pages`. Each key uses the page name, such as `two-layer`, and stores its SHA-256 and source URL. The proposal maps the stem of `supplier/pages/two-layer.html` to that key and compares the manifest hash with its evidence hash. This matches the current five profile-bound HTML entries.

The release manifest uses full repository-relative profile paths. The proposal records the lead's required normalization to `supplier/profiles/<name>.yaml`. It preserves the meaning of `profile_binding` as a profile path. Its magic values match the compatibility decision: `markup`, `%PDF`, `PK\u0003\u0004`, `OLE2`, and `null`.

The profile evidence records contain a page key, not a full file path. The proposal infers the key from the page path stem. Constrain the page suffix to `.html`, or state why another suffix can bind to the same key. All five current bound pages use `.html`.

## Review result

Confine the profile path before reading it. Clarify the page suffix rule. No code or tests were changed or run for this review.
