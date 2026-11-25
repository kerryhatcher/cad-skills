# Source retrieval alias freeze review (pi-skill-dev)

Date: 2026-11-15 UTC. Scope: the replacement freeze
`docs/reviews/source-retrieval-alias-freeze-claude.md`,
SHA-256 `31f8480fe08195424ccb1f2987ac45d1e72bbd0742303359ea1fd83698afc5aa`.
I examined the same hashes as the codex review. I changed no product file. I ran no broad
suite. I ran the frozen focused suite and the two alias probes.

## Hash boundary

The freeze record hash matches the request. Both entries in
`docs/reviews/source-retrieval-alias-files.sha256` pass. `sha256sum -c` exit 0.

| File | SHA-256 |
|---|---|
| `skills/pcb-fab-package/scripts/fetch_sources.py` | `35e21d37dc82e8367a167411b887843f426e0a2f5d1b4708cfe4f5dfad63ab01` |
| `tests/test_source_retrieval.py` | `1d61a5a2deaa5300087c34e4e5c4be83addfa3a0bc0841d2e74ff9db6f742cd7` |

I ran `uv run --quiet tests/test_source_retrieval.py`: `56/56 passed`, exit 0. The first 48
tests pass unchanged.

## Confirmation of the blocker fix

- Root probe `source-retrieval-manifest-probe-root.py`: exit 2, `manifest_changed` false,
  `response_replaced_manifest` false, refusal names the protected input.
- My probe `source-retrieval-profile-alias-probe-pi.py`: exit 2, `profile_changed` false,
  `profile_replaced` false, no rows.

## Code review

`refuse_protected_alias` implements the released correction:

1. It confines the destination under `supplier/profiles` by resolved path. Any destination in
   that directory is refused, including an unbound profile.
2. It compares the resolved destination with the resolved manifest and with every protected
   profile path. `./sources.yaml` and `supplier/profiles/./x.yaml` match.
3. It compares device and inode with each protected input. A hard link is refused.
4. It runs in write mode and in `--check-only` mode.

`validate` builds the protected set from the manifest path, every `profile_binding` path, and
every file under the real `supplier/profiles` directory. The alias check runs for each entry
before any fetch. The exit is 2 and nothing is fetched or written.

Order inside the entry loop: `refuse_links` (write mode), then `check_binding`, then
`refuse_protected_alias`. I confirm the ordering note. The symbolic-link messages of tests 47
and 48 stay the same.

## Tests 49 to 56

| No. | Case | My result |
|---|---|---|
| 49 | Destination `./sources.yaml` | exit 2, no fetch, inputs unchanged |
| 50 | `supplier/pages/../../sources.yaml` | exit 2, no fetch, inputs unchanged |
| 51 | `supplier/profiles/./fixture-two-layer.yaml` | exit 2, no fetch, profile unchanged |
| 52 | Unbound profile `supplier/profiles/other.yaml` | exit 2, no fetch |
| 53 | Hard link to the manifest | exit 2, no fetch, inputs unchanged |
| 54 | Hard link to a profile | exit 2, no fetch, inputs unchanged |
| 55 | Manifest alias with `--check-only` | exit 2, no fetch |
| 56 | Normal `supplier/guidance/full.html` | exit 0, written |

Test 51 and the under-`supplier/profiles` rule are the strongest new cases. Test 53 and 54
pin the hard-link rule.

## Probe note

I confirm the probe note. The codex probe writes `before` to the same path as the manifest
(`sources.yaml`), then writes the manifest over it. So `protected_changed` is true from the
probe's own setup, not from the command. `manifest_changed` is false. The freeze note is
correct.

## Minor findings

- Test 50 is caught by the `..` shape refusal in `check_shape`, before the alias check. The
  test passes, but it does not pin the alias check. Relabel it, or use a true normalized alias
  without `..`.
- A destination that names a directory, such as `path: "."` or `path: "supplier"`, is not
  refused by the alias check. It fails later as a write failure with exit 3, so no file is
  replaced. This is not a security gap. A directory destination test would pin it.
- The alias check protects the manifest and the profiles. The only other input is the network
  response, which is not a file. The set is complete.

## Verdict

The replacement freeze is accepted. The manifest and profile alias defects are closed. The
order and probe notes are correct. The accepted link, outcome and exit-precedence behavior is
unchanged. The two minor findings do not block the freeze.

No product edit. No broad suite.