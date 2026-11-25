# Source retrieval implementation review (pi-skill-dev)

Date: 2026-11-15 UTC. Scope: the retrieval implementation release from root, and the latest
compatibility proposal `docs/reviews/proposals/source-retrieval-interface-claude.md`,
SHA-256 `faa31c20ff804c066600333f3d813db3203bda759048a56d9267056d5627d10e`.
I changed no product file. I ran no broad suite.

## State of the implementation

No implementation file exists in this worktree. `skills/pcb-fab-package/scripts/fetch_sources.py`
and `tests/test_source_retrieval.py` are absent. No implementation freeze record is present.
I reviewed the design freeze. I cannot review a code freeze until the files and the freeze
record exist. The retained note is `/tmp/b7-pi-confine-probe.py` and
`/tmp/b7-pi-binding-check.py`.

## Confirmed

- The manifest meaning is kept. `profile_binding` names a profile, not a destination. `path`
  is the only write destination.
- The magic tokens are `markup`, `%PDF`, `PK\u0003\u0004`, `OLE2` and `null`. `pdf`, `xlsx`
  and `none` are refused.
- Codex's in-root profile blocker is addressed in the design. The proposal now requires the
  resolved absolute profile path to stay under the resolved `supplier/profiles` directory.
  A profile link that resolves into `supplier/pages` is refused before the read and before any
  fetch. Test 47 covers this case.
- Test 45 covers an outside-root profile link.
- The five release bindings still resolve after normalization. I measured each one: the `path`
  stem is a key of the profile `extensions.evidence_pages`, and the manifest `sha256` equals
  the profile `sha256`.

## Concrete defect: the link mechanism is not explicit

Root releases the implementation with `explicit is_symlink on all path components`.
The current proposal does not state that mechanism. It says `A link on any component is
refused` and relies on `project_io.confine` plus the resolved-path check.

I measured `project_io.confine` on 2026-11-15:

- An in-root link resolved without an error. `confine` returned
  `<root>/real/file.yaml`.
- `project_io.atomic_write` followed the link and wrote the file at the real path.
- Only an escaping link raised `PathEscape`.

Consequence: an in-root link that still resolves under `supplier/profiles`, for example
`supplier/profiles/link.yaml` to `supplier/profiles/real.yaml`, passes `confine` and the
resolved-path check. It is not refused. The proposal claim is false for that case. The
destination path has the same gap.

The design must state the explicit mechanism:

1. Check `os.path.islink` on every component of the profile path and the destination path
   before the read and before the write, as `workflow.refuse_links` does.
2. Add a test for an in-root link that stays under `supplier/profiles`, and a test for an
   in-root link in the destination path.

Without this, the implementation can follow a link inside the root and the design does not
require a refusal.

## Minor points

- State the YAML storage form of `PK\u0003\u0004`. An unquoted scalar and a double-quoted
  scalar parse differently.
- The normalization of the five release `profile_binding` values is required before
  integration. It is assigned to release. Make the dependency explicit in the freeze.

## Verdict

The design addresses codex's in-root profile blocker, but it does not yet state the explicit
`is_symlink` mechanism that root released. That is a concrete defect for the implementation
freeze. No product edit. I hold for the implementation files and the freeze record.