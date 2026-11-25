# OSH Park KiCad setup coverage

Date: 2026-11-15 UTC. Author: skill-dev-lead.

The user asks whether the skill includes the OSH Park KiCad setup guidance.
The plan cites the main page. The product references do not yet cover the full procedure.
Add this coverage to the remaining fabrication work. Keep the current correction files frozen.

## Official sources

- https://docs.oshpark.com/design-tools/kicad/
- https://docs.oshpark.com/design-tools/kicad/kicad-design-rules/
- https://docs.oshpark.com/design-tools/kicad/generating-kicad-gerbers/

I read all three pages on this date.
The main page lists KiCad 9.x for native board processing.
The accepted local toolchain uses KiCad 10. Continue to use the tested Gerber route.
Do not infer native KiCad 10 support from local export success.

## Coverage to add

1. Map the selected service to Board Setup, physical layers, constraints and net classes.
2. Separate supplier limits from setup recommendations and project margins.
3. Explain mask expansion, minimum mask web, optional tenting and assembler-owned paste settings.
4. Fill zones and save before export. OSH Park does not refill a native board upload.
5. Explain embedded fonts for native uploads and local font rendering for Gerbers.
6. List copper, mask, silk and Edge.Cuts layers for the selected service.
7. Disable plot-on-all-layers selections. Examine the effective exported layer functions.
8. Map the documented drill settings to the measured KiCad 10 command and output.
9. Explain the X2 difference. OSH Park recommends X2. The accepted neutral exporter uses no X2 attributes.
10. Link the source pages and record the measured version and source dates.

Do not change the accepted export contract without a concrete compatibility reason and both reviews.
Do not infer microvia support from the setup table alone.
Reconcile the setup table with the selected service specification before a profile change.
Keep the current mask geometry rules. A setup value alone does not prove the exported web dimension.

Use project-authored instructions and source links in the release.
Extend the source manifest and the planned setup retrieval path for these sources.
Keep full supplier page copies as local evidence outside the distribution bundle.
The source review and profile bindings remain the authority for changed source bytes.

Claude will report the coverage gaps and exact proposed files first.
Codex and Pi will examine that report. No new broad research or framework is necessary.
