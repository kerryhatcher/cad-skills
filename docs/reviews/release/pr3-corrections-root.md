# PR 3 corrections

This batch addresses both findings in the independent review of commit `326074a`.
The review comment is https://github.com/kerryhatcher/cad-skills/pull/3#issuecomment-6890936745.

## Project rules

The PCBA package captures optional `kicad/board.kicad_pro` and `kicad/board.kicad_dru` before the tool runs.
DRC receives the captured project settings and custom rules. ERC receives the captured project settings.
The manifest binds the file hashes with the optional roles `project_settings` and `design_rules`.
The applicable evidence also binds these inputs.
The shared validator refuses a PCBA manifest that omits a present configuration file.
It also refuses passed DRC or ERC evidence that omits its applicable configuration input.
The final gate refuses changed inputs and optional inputs that appear after capture.

The source schema, validator, documentation and all three skill copies agree.
These optional roles extend the manifest enum. Projects without the files remain valid.
The regression uses identical board bytes. A 1 mm minimum track width produces eight track-width findings.
The test measures this result with project settings and custom rules separately.
Other tests examine captured bytes, manifest hashes, evidence hashes and the final freshness gate.

## Public source

The index no longer contains the nine full supplier copies or eight HTTP header files.
All 17 files remain local with their recorded hashes. Exact ignore rules keep them local.
The source manifests retain their URLs, dates and hashes. The supplier profiles remain unchanged.
The tests examine the unfiltered candidate paths, all index blobs and the Git archive.
They detect forced additions, renamed copies and files hidden from an archive with `export-ignore`.
Missing excluded files still receive metadata and profile-binding checks.
Only measurements that depend on absent bytes are omitted.

Fabrication tests use temporary project-authored pages with measured fixture hashes and explicit fixture URLs.
The Sierra test uses a project-authored assertion for the export header. It reads no supplier workbook.
A clean source copy without the excluded files passes the relevant tests.
The setup instructions name the source retrieval command.
This change removes files from the current public tree. Earlier branch history retains the copies.
The merge will use squash to keep the intermediate copies out of the new main commit history.

## Results

- Shared contracts: 60 of 60 pass.
- PCBA: 107 of 109 passed in the first run. Two cases failed on native image lookup.
- The two failed PCBA cases pass through the existing Podman service. All three new project-rule tests passed in the first run.
- Clean-source packaging: 37 of 37 pass.
- Clean-source skill packages: 8 of 8 pass.
- Clean-source fabrication package: 101 of 101 pass.
- Clean-source source retrieval: 56 of 56 pass.
- Clean-source artifact fixtures: 16 of 16 pass. Local harness: 65 of 65 pass.
- Clean-source fabrication acceptance: 35 of 35 pass through the existing service.
- Clean-source fabrication workflow: 132 of 132 pass through the existing service.
- Clean-source standalone trial: seven commands pass with offline fixture pages.
- Document snippets: 52 runnable blocks pass. Five blocks retain their stated exclusions.
- Print tools: 6 of 6 pass.

The first clean-source workflow and acceptance runs stopped when KiCad output files were absent.
Those helpers discarded stderr. Thus the original cause remains unmeasured.
Focused retries and complete service runs passed. The retained logs preserve both outcomes.
The local service uses the accepted image, with no pull and no network for KiCad operations.

The lead regenerated A2 after the shared validator change.
Its command record is in `pr3-a2-evidence/`. Profile, design and supplier exits remain 0, 0 and 1.
A2 retains one mandatory failure and one mandatory pending condition. A3 remains unqualified and held.
The current harness freeze is `docs/reviews/pr3-correction-freeze-root.sha256`.
Earlier manifests remain history. Provider authorization remains zero.

Final integration results: artifact expectations 35, artifact fixtures 16, harness 65, packaging 37 and project IO 11 all pass.
