# B7 workflow correction decisions

Date: 2026-11-14 UTC.

These decisions combine the root, Codex, and Pi checkpoint reviews.
They restore the accepted interface. They do not add another framework.
The latest partial W1/W2 freeze is `b7-workflow-freeze-w1-w2-claude.md`.
Apply the complete correction to that state after both reviewers agree.

1. **Capture and consume the same bytes.**
   Keep the captured bytes available to the whole operation.
   Use them for parsing, staging, rule generation, and manual evidence.
   Do not discard the captured bytes and read the live profile or settings again.
   Include the selected profile, optional source rules, manual record, and referenced manual artifact.
   Preserve absent optional inputs as an explicit state.
   Compare current inputs with the capture before publication.
   A changed input fails the operation and cannot receive a fresh success binding.
2. **Use the existing lock and atomic helpers.**
   Hold `project_lock` across each project operation, including final publication.
   Use `atomic_write` for shared reports and records.
   Confine each write path, including nested paths and links, before a mutation.
   Preserve the accepted pre-replace and post-replace failure meanings.
   Publish a package through `publish_dir` only after the final freshness and validation gates.
3. **Complete the raw report, binding, and result sequence.**
   Retain raw report bytes. Bind all consumed inputs and referenced output artifacts to their hashes.
   Each result records the hash of its complete binding file.
   Write that result last. Reject a result with a missing, changed, or mismatched binding.
   Before package publication, compare current raw reports and artifacts with those recorded hashes.
   Do not copy a changed manual artifact and attach its current hash to an old pass.
   Use small local records and the existing helpers. Do not add an index or a generic evidence framework.
4. **Use measured KiCad report keys.**
   Keep constraint names separate from report and severity keys.
   Use the six mappings in `b7-workflow-checkpoint-1-root.md`.
   Do not add unmeasured aliases for constraint names in the report-key mapping.
   Row 15a must use `track_width` and the retained exclusion that matches a measured marker.
   Establish the source's suppressed or excluded finding before the staged result exposes it.
   Test ignored severity and an effective exclusion as distinguishable cases.
   Preserve source bytes. Confirm the drill and edge mappings through product results, not dictionary contents alone.

## Focused evidence

The correction record must identify the exact command, exit, source hashes, and retained result for each changed behavior.
The focused cases must cover:

- A source change after capture: staged bytes keep the captured content, and publication refuses the changed source.
- A changed selected profile, export settings, manual record, or manual artifact after measurement.
- A held project lock and a nested output link, with no unintended writes.
- An interrupted binding/result sequence: an old success cannot match the new binding.
- A changed raw report or export artifact before packaging.
- The measured ignored-severity and exclusion cases, with source preservation.
- Drill and copper-edge violations counted by their actual report types.

Keep the earlier failed logs. Do not rerun unrelated geometry or mechanical suites.
Freeze this complete correction once. Then obtain both reviews before another implementation change.
Supplier condition completeness and standalone acceptance remain the next work.
