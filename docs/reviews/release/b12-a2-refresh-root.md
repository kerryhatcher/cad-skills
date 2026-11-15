# A2 refresh for the accepted fabrication skill

The lead integrated the accepted B7 completion files before this run.
The source manifest is `docs/reviews/b7-completion-freeze-root.sha256`, hash `3f5904c28ba21ee8f09f4c480ff02a439741d59cceacff300ca9925ed0e4a411`.
The lead preserved the integration `AGENTS.md` and its separate documentation acceptance.

The A2 input changes are limited to `board.yaml` and `manufacturing/supplier.yaml`.
The board selects the current profile and declares `standard_through`.
The profile copy has content hash `e3f2789d1033aa284750002b6d71798ca2931d079a5fc0d989938bf9d8b172b9`.
The shared template and all A1 and A3 fixture bytes stay unchanged.

The local profile command returned exit 0. The design command returned exit 0.
The supplier command returned exit 1, as expected.
The KiCad operations used the accepted local image through the existing Podman service, with no network and no pull.
The command record and stdout and stderr files are in `a2-refresh-evidence/`.

The supplier result has 18 mandatory conditions. Sixteen pass.
The only mandatory failure is `service.order_multiple`. The order quantity stays at 5.
The only mandatory pending condition is `silk_line_min_short_text`.
The three new via and corner conditions pass and remain mandatory.
The fixture remains incomplete. No source review or package command ran.

The matrix has 17 run expectations and five separate fixture expectations for A2.
The new run expectations examine the three conditions and bind the supplier result, binding file and two reports.
Both corner conditions use the same corner report.
All run expectations use `base: run`.

The existing `sha256_binding` kind accepts exactly one selector, `key` or `json_path`.
Invalid selectors and invalid hash values fail the comparison without an exception.
The top-level key form remains compatible with A1 and the harness tests.
The new tests cover missing, duplicate and changed rows, changed reports, invalid selectors, links and an escaping path.
The fixture test permits only the two named input replacements and compares the board transformation and profile bytes independently.

Focused results:

- Artifact expectations: 35 of 35 pass.
- Fixture tests: 16 of 16 pass.
- Harness tests: 65 of 65 pass.
- Packaging tests: 34 of 34 pass.

The complete harness freeze is `docs/reviews/b12-a2-refresh-freeze-root.sha256`.
It supersedes the A3 harness freeze for current files. The earlier manifests remain history.
It includes the B7 inputs and all fixture files that the harness consumes.
The harness pointer names the new freeze.

Provider authorization stays zero. A3 stays held. No authenticated provider route ran.
The lead made no commit or push for this batch before review.
