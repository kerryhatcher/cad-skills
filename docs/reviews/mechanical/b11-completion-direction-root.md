# B11 completion direction

Date: 2026-11-15 UTC. Author: skill-dev-lead.

The lead read both Batch 2 review reports.
Both reviewers agree on R1 to R6.
The lead authorizes the complete correction and the remaining accepted implementation.
Use the current candidate files as the starting point.
Keep the old review hashes as historical evidence.

1. Read the measured KiCad Excellon format. Test retained export bytes.
2. Refuse success when any necessary comparison is absent.
3. Compare both STEP and DXF radii against the independent hole dimensions.
4. Complete C06 to C09, with proxy labels, the insertion volume and the finished-board envelope.
5. Complete the export, fit, report and release flow through the documented command.
6. Bind captured inputs and measured outputs. Use the accepted lock and atomic-write helpers.
7. Refuse stale inputs, path escapes and altered staged outputs before publication.
8. Make the reference describe only behavior that the command implements.

Use fresh fixture copies and the existing local image.
Retain the end-to-end commands, exits, hashes and negative results.
Do not replace independent expectations with values measured from the output under test.
No new design phase is necessary.

Freeze one coherent completion batch for both reviewers.
After the freeze message, stop edits to its files until the lead releases that set.
Reviewer findings do not release a frozen set by themselves.
No merge or push belongs to this authorization.
