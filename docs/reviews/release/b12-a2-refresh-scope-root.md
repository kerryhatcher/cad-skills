# A2 refresh after fabrication acceptance

This scope follows acceptance and integration of the frozen B7 completion batch.
Do not change A1 or A3.
The earlier A2 freeze remains history. A new complete harness freeze will supersede its fixture hashes.

The A2 project retains the RC template geometry, schematic, quantity 5 and toolchain lock.
Only two project inputs change from the template:

- `board.yaml` names the selected OSH Park profile and its current content hash. It declares `extensions.fabrication.via_process: standard_through`.
- `manufacturing/supplier.yaml` is a byte copy of the selected current profile.

The external A2 profile copy must contain the same bytes.
The template comparison will permit only these two explicit replacements and compare all other input bytes without exceptions.
It will compare `board.yaml` with an independently specified transformation of the template text.
It will also compare the declared profile hash with the profile content hash.

The lead will run profile, design and supplier through the accepted local image and existing local service.
No source review, package, public GET or model provider call will run.
The independent expected result remains one mandatory failure for `service.order_multiple` and one mandatory pending silk condition.
The new via and corner rows must pass and must bind their measured reports.
The status record will count the produced rows. It will retain the incomplete status.
The README will state the two input replacements and the new measured counts.

The lead will refresh `sources.sha256` and the retained output hashes.
The matrix keeps its exact named failure and pending sets and its absent package expectation.
The artifact tests must refuse a missing new mandatory row or altered report binding.
A1 and A3 retain their accepted hashes. Provider authorization remains zero.

The existing `sha256_binding` kind will accept an optional `json_path` list for nested hash fields.
Its existing top-level `key` form stays unchanged.
This permits a comparison from each report hash in `supplier-binding.json` to the produced report bytes.
The run expectations will also bind `supplier-result.json` to that binding file.
The three new condition rows must exist once, remain mandatory, and report pass.
Focused temporary mutations will remove a new row and change each report after the binding.
A nested missing field, invalid path or non-hash value must fail the comparison.
No new checker kind is necessary.

## Reviewer clarifications

Profile validation runs in the local Python process.
Only the KiCad tool operations in design and supplier use the locked image and local service.

For `sha256_binding`, exactly one selector must be present: `key` or `json_path`.
The existing `key` form stays the default when `json_path` is absent.
If both selectors are present, the comparison fails with an ambiguity reason.
If neither is present, the comparison fails with a missing-selector reason.
A `key` must be a nonempty string.
A `json_path` must be a nonempty list of string keys or nonnegative integer indices. Booleans are not indices.
Invalid selectors, absent fields and invalid hash values give a failed comparison. They do not abort the run.
The checker docstring will describe both forms.

The tests will preserve the shared template and the A1 before tree.
They will permit only the two named A2 input replacements.
The board profile hash comparison is test-side against the canonical `content_sha256` field, not a full-file binding.
B7 integration supplies the new worker, profile facts and report paths before any A2 run.
The new run expectations explicitly use `base: run`.
The via row binds `via-report.json`. The two corner rows share `corner-report.json`.
The negative row tests will include the three new condition identities.
The source manifest will bind the new integration profile and all consumed source files.
These clarifications resolve the reported interface points without a new checker kind or shared schema change.
