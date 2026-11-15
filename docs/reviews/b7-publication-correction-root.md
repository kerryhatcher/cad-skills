# B7 publication correction

Date: 2026-11-14 UTC.

This correction combines the complete-freeze reviews from root, Codex, and Pi.
It completes the existing four-part decision. It does not add a framework or expand supplier capabilities.
Keep the accepted geometry, KiCad report keys, row 15a, and deliberate drill and edge results.

## Required changes

1. **C1: confine each mutation.**
   Parse captured profile bytes without a scratch write, or confine the full scratch path first.
   Apply the same boundary to all child write paths, not only the top-level output directory.
   Refuse escaping links before a write. Use the existing helpers for shared reports.
2. **C2: bind the package bytes.**
   Read each consumed artifact once and compare its captured bytes with the accepted measurement hash.
   Write those bytes to the package and retain that same hash.
   Compare the staged package artifact with the expected hash before publication.
   Semantic checks must examine the package bytes or bytes proven equal to them.
   A new hash from a changed copy cannot inherit an old pass.
3. **C3: retain the original manual record path.**
   Record its path and measured hash.
   Compare the original record, retained copy, and referenced artifact before publication.
   Capture the referenced artifact bytes with the manual input set.
4. **Complete captured-input consumption.**
   Parse the runtime lock, source rules, project settings, board record, drawing inputs, and manifest metadata from the capture.
   Do not read their live paths during these calculations.
   Live reads belong to the explicit freshness comparison.
5. **Place the final freshness gate immediately before publication.**
   After evidence and manifest preparation, compare the current inputs, raw reports, bindings, and staged outputs with their expected hashes.
   Then call `publish_dir`. A mismatch cannot publish a qualified package.
6. **Lock the source-review write.**
   Use the same project lock for `review-source` across its reads and atomic writes.
   This prevents a cooperative review command from replacing evidence during package publication.
7. **Test an interrupted binding/result sequence.**
   Stop after the new binding write and before the new result write.
   Make sure that the old result cannot pass against that binding.

## Focused regressions

- A link at the captured-profile child path causes no external write.
- A controlled artifact change during packaging either fails or preserves the accepted artifact bytes.
- A changed original manual record fails, including a byte-only change.
- Changed captured settings do not silently enter the calculation from live files.
- A change after manifest preparation fails the final freshness gate.
- A held project lock refuses `review-source` without replacing its records.
- An interrupted binding/result update cannot reuse an old success.

Keep root probe results unchanged. If a probe hook no longer applies, write a new probe against the corrected capture step.
Record exact commands, exits, file hashes, and limits. Do not use a passing count as the only completion test.
Freeze the complete correction once for root. Root will assign both reviews.
