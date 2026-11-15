# B7 workflow completion order

Date: 2026-11-14 UTC.

This note orders the accepted work. It does not add an interface or a new review phase.
Use revision 8, the root errata, and the six points in `b7-workflow-draft-root.md`.
The current 51-check result does not establish full acceptance.

1. Complete the runtime, input snapshots, and publication rules together.
   Run the measured image identity, not its mutable tag.
   Snapshot all consumed files, including optional source rules and manual evidence.
   Preserve absence as part of a snapshot when an optional input does not exist.
   Bind each result to its binding file and compare current inputs before package publication.
   Use the accepted project lock, confined writes, fresh staging, and `publish_dir`.
2. Complete the supplier condition table and its evidence.
   Account for each applicable mandatory profile limit and service or process condition.
   Keep unsupported or unmeasured conditions incomplete until the agreed manual evidence establishes them.
   Implement the agreed manual mask route with current input and artifact hashes.
   A silk record alone cannot establish all supplier conditions.
3. Complete the agreed export and supplier regressions.
   Include the product test for source rules, ignored severities, and source exclusions in row 15a.
   Test board-derived limits through the product path where the acceptance row specifies a board.
   Generic threshold tests do not establish KiCad rule application or transformed geometry.
   Test qualification with omitted mandatory checks, omitted outputs, stale inputs, and altered evidence.
   Keep the positive package test with all applicable conditions represented.
4. Complete the skill documents and the standalone test.
   Test the installed skill outside the repository with its own files.
   Update the command table and the measured limits.
   Update the acceptance mapping with exact tests, commands, exits, and retained artifacts.
   State an untested item explicitly. Do not count it as a pass.

Keep old failed logs as evidence. Do not repeat unrelated accepted suites.
The next full freeze must include the product code, tests, skill documents, and the evidence used for its claims.
