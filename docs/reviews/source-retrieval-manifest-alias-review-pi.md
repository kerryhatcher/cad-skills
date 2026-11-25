# Source retrieval manifest-alias blocker review (pi-skill-dev)

Date: 2026-11-15 UTC. Scope: the retrieval blocker that root measured. I changed no product
file. I ran no broad suite. I ran two focused probes.

## The blocker

An entry with `path: sources.yaml` replaces the manifest itself and exits 0.

Root retained `docs/reviews/source-retrieval-manifest-probe-root.py`
(`95f2a856e8fb0cd2507e668167c4e279b3d07d0167a1dcf027ce84b28cc6e88d`) and
`docs/reviews/source-retrieval-manifest-probe-root.json`
(`473f9f953fd4bfa9b60b85cee25ab00c968d3ff868006ad906b232fc0079a0cf`).

I ran the probe myself. The result matches:

- exit 0.
- `manifest_changed` is true.
- `response_replaced_manifest` is true.
- the report says `all match` and the entry `written`.

This contradicts the accepted rule: the command never edits `sources.yaml`.

## The same class affects a profile

I ran a second probe, `docs/reviews/source-retrieval-profile-alias-probe-pi.py`
(`abbb1673832683d1f67a8b39c9ecb9d97d2eef566328c558c3c66101f7d34f84`).

The manifest has two entries. Entry `alias` has `path: supplier/profiles/fixture.yaml`. Entry
`bound` reads that same profile through `profile_binding`.

Result:

- exit 0.
- `profile_changed` is true.
- `profile_replaced` is true.
- both entries are `written`.

So a destination can also replace a profile that another entry reads. This contradicts the
accepted rule: the command never writes a profile.

## Narrow correction: refuse a destination that aliases an input

I confirm the narrow correction. The destination must not resolve to a path that the command
reads. Refuse, with exit 2 before any fetch:

1. a destination whose resolved path equals the resolved manifest path. This covers
   `sources.yaml` and `./sources.yaml`.
2. a destination whose resolved path equals the resolved path of any profile that the run
   reads through a `profile_binding`. This covers the two-entry case above.
3. the safe simple form: refuse any destination whose resolved path is under the resolved
   `supplier/profiles/` directory. This also keeps the rule `never writes a profile`.

The check belongs in `validate`, after the destination map is built and before the fetch
loop, next to the duplicate-destination check. It must run for a write request. In
`--check-only` no write occurs, so it may be skipped, but a uniform refusal is simpler.

## Required tests

- `path: sources.yaml` is refused with exit 2. The manifest keeps its bytes. No fetch occurs.
- `path: ./sources.yaml` is refused the same way.
- `path: supplier/profiles/<read profile>.yaml` is refused with exit 2. The profile keeps its
  bytes. No fetch occurs.
- A normal `supplier/guidance/x.html` still writes and exits 0.
- A `--check-only` run of the refused entries writes nothing and reports the outcomes.

## Accepted checks stay closed

The link checks (tests 7, 8, 45, 47, 48) and the outcome checks (exit precedence, two-status,
skipped, candidate, changed, magic, fetch failure, post-replace) stay accepted. This
correction only adds the destination and input alias refusal.

## Verdict

The blocker is confirmed. The narrow destination and input alias refusal corrects it. No
product edit. I hold for the corrected implementation freeze.