# B9 and B10 batch 2 correction release

Date: 2026-11-15 UTC. Author: skill-dev-lead.

Both alternate-batch reviews are complete.
Codex recorded the boundary where the working files changed during review.
The original batch record remains historical. It is not acceptance of the changed files.

I release one coherent batch 2 from the disclosed current files.
Include these alternate corrections with the placement and supplier artifact work:

- Forbid alternates on mechanical map entries in schema 1.1 and in the loader.
- Validate alternate selection keys and values before lookup.
- Refuse malformed selections with one named finding and no traceback.
- Test a list-valued selection, an unknown selection and a mechanical entry with alternates.

Keep all accepted neutral tests and interfaces.
Include the source sample provenance and all files that the new tests consume in the freeze.
The release team owns the new source manifest entry for the retained BOM sample.
Keep full supplier sample bytes outside the distribution bundle.

Freeze the whole replacement implementation and its tests before review.
After the freeze, do not edit any listed file until the lead releases it.
Work on a later batch can proceed only in unlisted files with a separate scope.
A hash list does not preserve overwritten source bytes.
No commit, merge or push before acceptance.
