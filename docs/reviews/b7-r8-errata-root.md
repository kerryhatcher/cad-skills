# B7/B8 revision 8 errata

Date: 2026-11-14. Proposal hash: `8ff1da0d452902edfc8bc93129ce26e27d861340fb5a5c75deba813be83e09e5`.

The trials now support the selected methods and their stated limits. The lead confirmed all 195 manifest entries from `docs/reviews`. The first attempt from the repository root failed because the manifest paths use the review directory.

These corrections preserve earlier decisions. They do not add features.

1. Use the schema value `fabrication`, not `fab`, in the profile scope table. Remove `margin` from all published process-capability rows.
2. Set the physical copper-layer requirement to integer values 2, 2, 2, 4, and 6 for the five profiles. The single-layer service uses the two-layer process. Set `service.order_multiple` to integer 3.
3. Preserve source nominal values in the records. Board minimum is 0.25 in. Board maxima are 16 in and 22 in. Finished thickness is 63 mil, or 32 mil for HHDC. Keep rounded metric labels separate. Name the source-value field for thickness beside the existing metric display field.
4. The 250 mil drill statement is a process note. It is neither a maximum nor a design recommendation. Correct the remaining acceptance-row wording.
5. Confirm the slot tolerance explicitly with both reviewers. Revision 8 changes it from 0.001 mm to 0.000501 mm. Retain independent board plating, coordinate conversion, endpoint order, and multiplicity checks. Test the selected tolerance boundary.
6. Keep the file-level distinction between the analytic geometry trial and the future production inspector. Unknown macros, overlapping clusters, and unsupported constructs must refuse before qualification. No trial establishes these refusals unless its output demonstrates them.

The command record contains abbreviated invocations. Retained scripts support some reconstruction, but they are not a complete invocation log. Give executable commands with explicit paths for the accepted trials. Do not repeat unrelated tests to supply this record.

The eight new glossary entries are the lead's authorized change after B6 acceptance. B6 code is unchanged. Its historical manifest now differs on the glossary path.
