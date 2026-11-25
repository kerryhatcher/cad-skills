# A3 artifact connection

Date: 2026-11-15 UTC. Author: skill-dev-lead.

Both release reviewers agreed on the A3 fixture paths and the two additional checker kinds.
The lead copied 59 files from the accepted PCBA replacement into the local A3 fixture.
The source manifest hash is d419688f2e4b5b30a35209985f619c2fc46ae2d58c2a1d949feb9ab24079ca64.
`source-copy-hashes.json` records the source path, local path and accepted hash of each copy.
The local tests use no external worktree.

The matrix has 19 produced-package expectations under base run and one separate fixture expectation.
It retains the exact check sets, DRC counts, stock failure, supplier uncertainty and unmeasured physical results.
The package has status unqualified. No expected result claims a qualified or physical pass.
The output binding examines all 41 unique output paths, hashes and byte counts.
The board binding compares the manifest with the fixture board.
The two new kinds are length_equals and row_binding.

The focused expectation suite passes 30 of 30 tests.
The tests include a minimal manifest, a changed check ID, altered DRC counts and a false physical pass.
The semantic mutation tests update the output hash first, thus the semantic expectation must detect the defect independently.
Output negatives cover changed bytes, missing files, links, duplicate paths, escapes, byte counts, invalid hashes and missing fields.
The count check refuses missing and non-list arrays. A changed fixture board fails its binding.
No A1 or A2 byte changed. A3 remains held. Provider authorization remains zero.
The lead ran no new package, container, simulation or provider for this connection.

The harness description now distinguishes the accepted local stub boundary from the unmeasured authenticated route.
Its freeze pointer names `b12-a3-connection-freeze-root.sha256`.
The earlier freeze records remain history.
