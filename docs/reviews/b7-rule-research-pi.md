# B7 rule-generation research: Pi design assessment

Date: 2026-11-14.

**Decision: I agree with the proposed implementation boundary. Two design points need an explicit choice. No implementation, container run or broad research was done.**

## Agreement

The record reads the KiCad 10 behavior correctly. A later custom rule is examined before an earlier rule, a rule with severity `ignore` still participates, and project severity settings can disable a check. Thus a generated rule file alone does not prove that the effective checks enforce a supplier limit. The two-result separation, the disposable project copy, the preserved source bytes, the no-refill rule and the fixed five-profile rule set are sound. No general rule-merging engine is necessary.

## Design points

1. **Rule selector for the internal-copper clearance.** Use `hole_clearance` for the 10 mil plated-drill-to-internal-copper rule. It measures to copper on another net, so an intended same-net pad or plane connection passes. Do not use `physical_hole_clearance` where a same-net connection must pass, because it applies without a net distinction. Keep the connected and unconnected fixtures separate. The `inner` layer selector covers internal copper for the four-layer and six-layer profiles.
2. **Staged settings, not the source.** The supplier run must use its own rule file and its own severity mapping in the staged copy. Do not edit the source rule file or the source project severity. Name the staged files and their hashes. Order the mandatory rules so that no later matching rule shadows them. The weaker-later-rule test proves this.
3. **Oval and slot geometry.** `hole_size` compares the minor diameter with a minimum and the major diameter with a maximum. Test slot width independently from slot length. Do not turn the 250 mil tolerance threshold into a maximum diameter.
4. **Exception evidence.** A supplier exception is a profile decision with applicable supplier evidence, not a local DRC waiver. The profile records the decision and its source. The B234 waiver binds board and schematic bytes and does not prove supplier acceptance.
5. **Binding.** The result records the profile hash, the staged rule-file hash, the staged-settings hash and the command. The source PCB hash stays unchanged. The generated rule file and the staged settings are explicit artifacts, as the record requires.

## Tests

I agree with the six necessary tests. Add two focused cases:

- A connected same-net pad or plane at 0 mil passes with `hole_clearance`; an unconnected internal feature at 9.9 mil fails and at 10 mil passes.
- A staged severity or exclusion that would hide a mandatory check fails the supplier result, while the source project keeps its setting.

These supplement the below/at/above cases. The fixed image must execute the generated rules. Documentation alone does not establish support for the selected patch version.

## Limits

This is a paper assessment. I did not run KiCad custom rules and did not test a rule file. The B6 interim review stays open.
