# Source retrieval compatibility review (pi-skill-dev)

Date: 2026-11-15 UTC. Scope: the compatibility revision
`docs/reviews/proposals/source-retrieval-interface-claude.md`,
SHA-256 `b2cdf367d932425f9d7914e20385034401b25bf335bdfa7cafe29a3c138796b8`,
against `docs/reviews/source-retrieval-compatibility-root.md` and the release manifest
`/mnt/storage/projects/cad-skills-worktrees/release/skills/pcb-fab-package/sources.yaml`.
I changed no product file. I ran no broad suite.

My earlier r4 agreement used the superseded page-path meaning of `profile_binding`. I
withdraw that part. The new profile meaning is the correct one.

## Agreement with the compatibility decision

The proposal matches all ten items of the compatibility record:

- `path` is the only write destination. `profile_binding` identifies a profile and never a
  destination.
- The profile value is `supplier/profiles/<name>.yaml`. The normalization of the five
  release values is assigned to release as a coordinated text change.
- A bound `path` stays under `supplier/pages/`. The profile path stays under
  `supplier/profiles/`.
- Both paths are confined. The profile is read only for the check and is never written.
- The magic tokens are `markup`, `%PDF`, `PK\u0003\u0004`, `OLE2` and `null`. The strings
  `pdf`, `xlsx` and `none` are refused.
- `exclude-full-copy` permits local retrieval and excludes distribution.
  `exclude-local-evidence` skips retrieval.
- The exit precedence is validation 2, fetch or write failure 3, candidate, changed or
  magic mismatch 1, then 0.
- The post-replace outcome is explicit. The new bytes can remain after a synchronization
  failure.

### Release manifest check

I measured the five bound entries in the release manifest with the proposal rules. A script
resolved the profile name from `profile_binding`, read the profile under `supplier/profiles`,
and compared the `path` stem with `extensions.evidence_pages`.

| Entry | Stem | Page key | Manifest hash equals profile hash |
|---|---|---|---|
| `oshpark-single-layer-html` | `single-layer` | yes | yes |
| `oshpark-two-layer-html` | `two-layer` | yes | yes |
| `oshpark-two-layer-hhdc-html` | `two-layer-hhdc` | yes | yes |
| `oshpark-four-layer-html` | `four-layer` | yes | yes |
| `oshpark-six-layer-html` | `six-layer` | yes | yes |

All five resolve after the path normalization. The header entries use
`exclude-local-evidence` and `profile_binding: null`, so they are skipped. The release magic
tokens in use are `markup` and `null`.

## Concrete defect: the link rule is stronger than the helper

The proposal says `A link on any component is refused with exit 2`. It relies on
`project_io.confine`.

I measured `project_io.confine` on 2026-11-15:

- An inside link resolved without an error. `confine` returned
  `<root>/real/file.yaml`.
- `project_io.atomic_write` followed the inside link and wrote the file at the real path
  under the root. The link stayed.
- Only an escaping link raised `PathEscape`.

So `project_io.confine` alone refuses an escaping link, not every link. The stated rule and
the test set do not match. Test 45 covers an outside link only.

Fix one of these ways:

1. Add an explicit `os.path.islink` check on every component of the profile path and the
   destination path (as `workflow.refuse_links` does). Add an inside-link test.
2. Weaken the rule to `an escaping link is refused`. Keep test 45. State that an inside link
   is followed.

The profile path and the destination path both need the same treatment.

## Minor points

- The token `PK\u0003\u0004` needs a stated YAML form. An unquoted scalar and a double-quoted
  scalar parse differently. State the storage form and the parsed string.
- The normalization of the five release `profile_binding` values is required. Until release
  applies it, the integrated manifest fails the proposal validation. The proposal assigns
  this to release. Make the dependency explicit in the freeze.

## Documentation freeze 2

Freeze 2 `docs/reviews/oshpark-setup-documentation-freeze-2-claude.md`
(`9caa827162cdaeaddf2039cb8864cc1223af1771e723f32bf8e6780fd35ee268`) is separate and
corrects only the stale coverage state. I verified the seven file hashes and the
`Release state of the setup files` text. The reference is installed and linked. The source
entries are a proposal with `sha256: null`. The recommendation asks for measurements only.
I accept freeze 2.

## Verdict

The compatibility proposal agrees with the compatibility decision and the release manifest.
One concrete defect blocks it: the link rule does not match `project_io.confine`. Two minor
points. No product edit. I hold for the corrected revision.