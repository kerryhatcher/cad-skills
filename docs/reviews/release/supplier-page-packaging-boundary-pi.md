# Supplier page packaging boundary from Pi

Date: 2026-11-15 UTC. Revised after the lead decision of 2026-11-15 01:52 UTC.
Author: pi-skill-dev (Pi pane `w1P:pF`), reviewer.

Scope: accepted packaging boundary for the stored supplier pages and documents, plus the
interface for the release packaging inventory and exclusion checks. This report gives the
interface. Claude owns product changes. Reviewers write reports only.

## 1. Accepted lead decisions

| ID | Decision |
|---|---|
| P1 | Accept the source manifest, the explicit setup fetch, and the local evidence excluded from distribution. |
| P2 | Preserve the current evidence. Exclude unlicensed full copies from release artifacts and public source publication. |
| P3 | The local common snapshot is a work snapshot. It is not approval of the publication history. |
| P4 | Use the existing source hash and source-review rules. Changed bytes need a new recorded review and a profile binding. Changed bytes are not accepted automatically. |
| Gate | Reject the mandatory license acknowledgment gate. A user acknowledgment does not establish distribution rights. |
| License state | Keep the license state informational for local retrieval. Keep the distribution decision separate. |
| Suppliers | No credentials. No supplier contact. |

## 2. Corrected design

Remove the acknowledgment gate. Remove the "stop on unconfirmed license" rule.

The three-part split stays.

| Part | Location | Contents | Distributed |
|---|---|---|---|
| Source manifest | `skills/pcb-fab-package/supplier/sources.yaml` | URL, title, retrieval date, SHA-256, content type, informational license state, review status | Yes |
| Fetch path | `skills/pcb-fab-package/scripts/fetch_sources.py` | Fetch, hash check, local record | Yes |
| Local evidence | The repository review tree | The full stored bytes for audit | No |

### Explicit setup fetch

1. A user runs `fetch_sources.py`. It does not run automatically.
2. The script reads `sources.yaml`.
3. The script fetches each public URL.
4. The script compares the bytes with the recorded SHA-256.
5. A match writes a local record with the retrieval date.
6. A mismatch writes a finding and stops that entry. It does not accept the new bytes.
7. A changed hash needs a new recorded review and a profile binding. Then the manifest
   receives the new hash and the new retrieval date.
8. The script does not ask for a license acknowledgment. It records the informational
   license state only.

### Distribution decision

The distribution decision is separate from the local retrieval.

1. An unlicensed full copy is not a release artifact.
2. An unlicensed full copy is not part of public source publication.
3. The local evidence stays for audit.
4. The manifest and the fetch script can be distributed.

## 3. Fabrication team interface

| Item | Owner |
|---|---|
| `supplier/sources.yaml` and `fetch_sources.py` | Fabrication team |
| The smallest runtime path change | Fabrication team, after the current frozen correction |
| The evidence copies stay in the review tree | Lead and release team |
| The packaging inventory and exclusion checks | Release team, after interface agreement |
| Tests with project-authored page fixtures | Both teams |

No deletion. No silent runtime change. The fabrication team proposes the smallest path
change after the current frozen correction.

## 4. Release packaging inventory and exclusion check

The release team can implement these checks now. Proposed path:
`tests/test_release_packaging.py`. The checks are local. They call no provider.

### Inputs

- The `sources.yaml` manifest of each skill that stores a supplier source.
- One repository-level manifest for supplier evidence outside a skill. The Sierra
  evidence under `docs/reviews/` needs a repository-level entry.
- The file list of each distributed skill package.
- An explicit distribution allowlist. The allowlist names the files that may ship.
- The regression exclusion rules. The paths `skills/*/supplier/pages/**` and the known
  Sierra evidence under `docs/reviews/sierra-source-evidence/` are excluded. The `.headers`
  files are in the exclusion. The rules are regression checks, not the only decision.

### Findings

| ID | Check | Result |
|---|---|---|
| D-1 | Each stored supplier source in a skill has a skill-level manifest entry, and each repository supplier evidence item has a repository-level manifest entry | A missing entry is a finding |
| D-2 | Each entry has URL, retrieval date, SHA-256, content type, `license_state` (informational), and `distribution_decision` (separate). No acknowledgment field is necessary | A missing field is a finding |
| D-3 | A file is in the distributed set only if the distribution allowlist names it. A full supplier page or document and a local evidence file, including the `.headers` files, are absent | A distributed copy is a finding |
| D-4 | The local evidence copy is present in the review tree and absent from the distribution list | A present distributed copy is a finding |
| D-5 | A changed source hash has a recorded review and a profile binding | An unbound changed hash is a finding |
| D-6 | The distributed supplier files are the manifest and the fetch script only. Zero fetch scripts is valid until the fabrication team delivers one | Another distributed supplier file is a finding |
| D-7 | The test fixtures are project-authored pages | A supplier byte in a fixture is a finding |
| D-8 | Type detection reads the file extension and the file magic. Example magic: `%PDF`, `PK` for XLSX, and HTML markup. File magic identifies a format. It does not identify a license or an owner. A project-authored PDF or HTML fixture is not forbidden by type alone. A changed hash is decided by the recorded hash, not by the type alone | A type that disagrees with the manifest is a finding |

The checker writes one finding for each defect. It does not write a bare `pass` string. It
reads bytes and hashes, not a model statement.

### Interface agreement

The author and both reviewers agree on this interface before implementation. The author
implements it. The reviewers examine the code and the fixture results.

The author agreed with the interface and added four corrections C-1 to C-4. This review
accepts all four. The final findings are D-1 to D-8.

| ID | Correction | Review result |
|---|---|---|
| C-1 | A per-skill `sources.yaml` covers supplier data inside a skill. The Sierra evidence under `docs/reviews/` needs a repository-level manifest | Accept. D-1 now names both scopes |
| C-2 | Separate `license_state` from `distribution_decision`. No acknowledgment field | Accept. D-2 now names both fields |
| C-3 | D-3 treats the `.headers` files as local evidence and excludes them from distribution | Accept. D-3 now names them |
| C-4 | Type detection reads the extension and the file magic. The hash decides a change | Accept. Added as D-8 |
| D-6 note | Accept zero fetch scripts until the fabrication team delivers one | Accept. Folded into D-6 |

Proposed path: `tests/test_release_packaging.py`. Tests use project-authored page
fixtures. No provider call.

### Provisional and final packaging

A missing fetch script is acceptable for a provisional packaging test. A final standalone
release cannot pass without the necessary setup path. Record the state as `provisional`
until the fabrication team delivers the fetch path.

## 5. Lead answers (2026-11-15 01:54 UTC)

| ID | Answer |
|---|---|
| Q1 | `tests/test_release_packaging.py` is accepted. |
| Q2 | Use an explicit provenance manifest and a distribution allowlist, plus the `supplier/pages/**` and known Sierra evidence exclusions as regression checks. Include the `.headers` files. File magic identifies format, not license or ownership. A project-authored PDF or HTML fixture is not forbidden by type alone. |
| Q3 | The existing supplier-profile content and evidence hashes and the source-review record are the binding authority. The source manifest names URLs and expected hashes but does not add a second competing approval record. Its location is the author's choice within the assigned paths. |

Routine file names inside the owned directories need no further lead question.

## 6. Limits

This proposal reads local files. It does not contact a supplier. It does not give legal
advice. It does not change a product file.
