# B5 supplement review: Codex

Date: 2026-11-14 UTC.

**Decision: accept this supplement's measured T5, T6, native limits, option experiments, and 13 diagnostic records.** No blocking defect remains in those observations. This is not final B5 acceptance. E1, E2, E5, E6, Pi-1, and Pi-2 remain correction work.

I read `b5-supplement-claude.md`, `b5-supplement-addendum-claude.md`, and the Pi trial review. I changed only this report.

## Reviewed hashes

All 325 entries of `docs/reviews/b5-supplement-files-v2.sha256` passed before and after review. Its hash stayed unchanged:

`e54bc0949d687e999649e9d1de0ba0a4ccf9f98e4b88013b67a3beccb58045a8`

The main manifest hash remains:

`86395ff3fa7692f3cbf2ba65ee898be9cc7c443f08ca13419b162441406caf60`

At the final measurement, 704 main entries match. Three differ: `scripts/check_exports.py`, `scripts/export_final.sh`, and `scripts/layout.py`. The lead confirms authorization for those repairs at 06:48 UTC. They are outside this frozen supplement review. I did not examine their active changes. All 325 supplement entries remain unchanged. The later complete correction manifest will define the next review boundary.

| Reviewed record | SHA-256 before and after |
|---|---|
| `docs/reviews/b5-supplement-claude.md` | `f77f81643bd75412cb6defc59ad8dbe6b945cea56a4dd92a39ece8407c429c71` |
| `docs/reviews/b5-supplement-addendum-claude.md` | `e1a5aae3ca572265ab202223e030f1cc48063048c3eb4b797a9e29c204591aee` |
| `examples/pcb-trial/results/supplement/e3/index.json` | `0e310e56e2fed2c66bf1001bd690214cddb0bfbbf60deb6cb7eb719ad22e614c` |

## Agreement with Pi-1 and Pi-2

**Pi-1: agree.** Preserve the three historical comparisons. Add separate results from the current reader. Name the reader version or hash, the snapshots, the expectation, the command, and the exit.

I independently reproduced the stale records:

- `results/skidl/u2_skidl_e/compare.json`: the current reader reports 12 differences. Its five added-footprint records include values.
- `results/skidl_u3/compare/u3b_to_u3c.json`: the current reader reports one added C2, including value `100n`.
- `results/skidl_u3/compare/u3b_to_u3g.json`: the current reader reports one added C2, including value `100n`.

All three statuses remain `different`. The historical records omit the added values. This does not invalidate the saved boards or snapshots. It does prevent an exact claim that those old comparisons reproduce with the current reader.

**Pi-2: agree.** Retain the T13 host build and validation commands, their arguments, and both process exits. Bind the validation result to the regenerated draft. If the original command record is unavailable, label a new invocation as a new run. Do not invent a historical exit record. No command framework is necessary.

Paths below start at `examples/pcb-trial/`.

## Focused measurements

I used temporary copies and the existing image:

`d881df4ef3e2ec76995f4070596550db118b23e7f6db9017f09a418c44c4b1c2`

All container runs used `--pull=never --network none`. Python ran through `uv`. I did not repeat GUI operations, accepted final-board work, or unrelated suites. I did not build or pull an image.

### T5 and T6

I ran fresh ERC commands on the frozen T5 good and defective schematics:

```text
kicad-cli sch erc --exit-code-violations --severity-all --format json -o REPORT SCHEMATIC
```

The good schematic returned 0 with no violations. The defective schematic returned 5 with three `pin_not_connected` errors. This meets the agreed finding-and-exit condition. The invalid earlier attempts retain their markers.

I ran `skidl/erc_probe.py` in both modes with the installed SKiDL interpreter. The good process returned 0 and reported no ERC errors or warnings. The defective process also returned 0. It reported four ERC warnings and zero errors, as the frozen record states.

Thus, a process exit of 0 does not establish ERC success. The later B6 wrapper must examine ERC results under its agreed policy. This test measures warning behavior. It does not measure the exit behavior of an ERC error. No additional B5 rule or test framework is necessary.

The probe docstring also mentions an isolated D1 pin 1. The code actually connects D1 pin 1 to GND. Correct that description when the trial documents receive their agreed prose repairs. The four measured warnings concern empty N_LED and the two disconnected pin-2 terminals. This description error does not change the measured result.

### E3 diagnostic records

I compared all 13 index entries with their complete reports, exit files, and hash files. The hashes identify retained board and schematic bytes. Counts, finding types, descriptions, and parity items agree.

All 13 tool exits are 5. These are intermediate boards, not clean reference boards.

| Saved states | Parity result |
|---|---|
| `vz_none`, `vz_value` | Empty |
| U2 same-source A and B | Four `net_conflict` findings each |
| U3 A, B, F against schematic G | Empty |
| U3 B against schematic H | Three `net_conflict` findings |
| U3 C and G against schematic G | One extra C2 each |
| D1 removal with deletion off | One extra D1 |
| Re-added D1 | Empty |
| R2 hierarchy change | One `duplicate_footprints` finding for R2 |

The U2 A findings include different net names even where the pin partition agrees. They remain recorded failures. The supplement correctly leaves their cause unexamined. U3's literal schematic-H comparison also remains distinct from the matching-netlist comparison against schematic G.

The C2 sentinel and default-restore findings match their declared source difference. They do not count as clean-board results. U3 stays experimental. Its shell helper does not measure the KiCad process exit, and the addendum now states that limit.

These diagnostics supply E3 for the listed preservation, same-source U2, and valid U3 boards. They do not promote the earlier cross-source U2 experiment to a supported path.

### Native limits and option experiments

I recomputed the three new board snapshots and comparisons with the accepted reader. They match the stored results.

- **D1 deletion off:** the old footprint keeps its UUID and `[125, 106, 180]` position. Only its schematic path becomes null. The empty hypothesis fails with exactly that difference. The extra-D1 parity finding agrees. This completes the missing deletion-off observation.
- **D1 re-addition:** the original symbol returns after footprint removal. The added footprint has the expected library, value, and pad nets. No unrelated difference occurs. Its footprint UUID changes from `4b40f9a3-a36b-401f-934b-c5bfce32e707` to `4930f048-ace0-4c08-a3be-657096168f2a`. Its position changes to `[132.545, 132.295, 0]`. Its schematic path remains the same. This is footprint re-creation with the original symbol identity, not preserved placement.
- **R2 hierarchy change:** the old R2 path becomes null. A second R2 appears with the expected value and pad nets. The duplicate-footprint parity finding agrees. The retained XML has the exact ten pin-to-net entries across four nets. The hierarchy schematic's ERC report is clean.

The failed deletion-off hypothesis and hierarchy identity result are valid limit observations. They do not fail the supported native edit gate. Their option states remain explicit. No repeat of these GUI operations is necessary.

The appended `classification.json` correctly identifies replace-off as an option experiment. It also records the `.gbr` suffix correction without changing historical script bytes. The later corrected export script must carry the accurate comment.

## Remaining boundary

The supplement's drill-mark and X2 material is historical context for the accepted E5/E6 repair. Its alternative proposal for a new drill-mark schema field is superseded. Use the agreed saved settings and effective-output tests. Do not expand the schema.

The supplement's sentence that limits incompleteness to U3 and U5 is also superseded. B5 still waits for the export corrections, refreshed exact-byte evidence, and Pi-1/Pi-2 records. Untested U3 edits and U5 remain explicit limits. They must not become unsupported claims, but they do not mandate a new broad trial.

This review accepts the supplement's scoped observations. Final B5 acceptance remains separate.
