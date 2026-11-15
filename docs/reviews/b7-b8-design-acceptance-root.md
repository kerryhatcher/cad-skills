# B7/B8 design acceptance

Date: 2026-11-14. Both reviewers accept revision 8 together with `b7-r8-errata-root.md` as the implementation interface.

The proposal SHA-256 is `8ff1da0d452902edfc8bc93129ce26e27d861340fb5a5c75deba813be83e09e5`. The errata SHA-256 is `08eecbedee4be4e63326803b44e9202d2a163f4d9f03045b5dbf33a7e27584ad`.

The agreement appears in `b7-b8-design-codex.md`, final section, and `b7-b8-design-pi.md`, section 18. The lead accepts the same interface.

The prerequisite manifest has 195 entries. Its SHA-256 is `2ef5503dd2fc86c2e300536e3c75b74a9c88e8e6031de87d819fb524827773d9`. Run its hash command from `docs/reviews`. The lead and both reviewers confirmed those entries.

Claude can implement the independent `pcb-fab-package` skill. The scope includes the agreed shared-contract additions and all corresponding skill copies. Keep the earlier manifests as history. The glossary already has the lead's eight new terms.

The slot tolerance is 0.000501 mm per coordinate. Test that boundary and 0.000502 mm. Preserve independent board plating, coordinate conversion, endpoint order, and multiplicity tests.

The mask trials establish a limited analytic method. Production code must refuse unknown macros, overlapping clusters, and unsupported constructs. Manual geometry evidence must identify the artifact and current input hashes. These are implementation tests, not reasons for another prerequisite cycle.

The fabrication drawing must include the agreed content. Its test must inspect that content and render the example. A non-empty layer PDF alone is insufficient.

The author must supply complete executable trial commands with explicit paths. Do not describe the abbreviated command table as a complete execution log. Do not repeat unrelated tests for this record.

Implementation acceptance remains separate. Both reviewers must examine frozen code, tests, and evidence. No commit, supplier upload, or order is authorized.
