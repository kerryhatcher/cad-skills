# B9 neutral correction authorization

Date: 2026-11-15 UTC. Author: skill-dev-lead.

The lead read both neutral-batch reviews and the numeric/stock agreements.
Both reviewers and the author agree on the combined correction.
The lead releases the frozen neutral files for this work.

1. Acquire the project lock before capture. Hold it through freshness tests and the atomic write.
2. Confine each requested part path under both the project and the component directory.
3. Reuse one successful captured snapshot per resolved file. Keep recorded paths project-relative.
4. Use the same resolved relative part path in rows and input records.
5. Refuse an output that aliases any consumed input before a write.
6. Rehash the inputs immediately before the output write. Refuse changed input bytes.
7. Keep raw x, y and angle strings in `source_tokens`. These strings preserve the source values.
8. Label numeric fields as derived finite values. Refuse malformed and non-finite tokens with one finding and no traceback.
9. Test high precision and the implicit zero angle. State the implicit-angle representation.
10. Emit `datum`, `midpoint_mapping`, per-row `board_quantity` and empty `selected_alternate`.
11. Use `per_board_quantity: 0` for excluded rows. Correct the interface text to agree.
12. Copy the hand-install reason to `assembly_instruction`. Use an empty string for automatic rows.
13. Include `assembly_instruction` and `installation_method` in the BOM grouping key.
14. Refuse conflicting stock or lifecycle records for one manufacturer and MPN.
15. Aggregate demand once per populated reference. Do not add repeated stock quantities.

Identical repeated records can share a stock result.
The map and part schemas remain skill-owned or unchanged copies.
No shared schema expansion is necessary.

Correct the batch record's snippet-test claim.
The missing routing entry is an integration item, not a pre-existing test failure.
Keep the shared routing file unchanged in this worktree.
Alternates remain incomplete. Sierra conversion and B10 publication remain outside this correction.

Run the focused positive and negative tests.
Freeze one complete corrected batch for both reviewers.
After that freeze, stop edits until the lead explicitly releases the files.
No merge or push belongs to this authorization.
