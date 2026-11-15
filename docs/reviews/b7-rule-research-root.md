# B7 rule-generation research

Date: 2026-11-14. This record adds implementation decisions to the existing supplier research. It does not change code.

## Confirmed KiCad behavior

KiCad examines later custom rules before earlier rules. A matching rule can prevent an earlier rule from applying. A custom rule with severity `ignore` still participates in that selection. Separately, project severity settings can disable a check. Thus, appending a template does not prove that the effective checks enforce a supplier limit. [KiCad 10 manual](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html)

`hole_clearance` measures from the drill boundary to copper on another net. `physical_hole_clearance` also applies without a net distinction. The `inner` layer selector covers internal copper. For oval holes, `hole_size` compares the minor diameter with a minimum and the major diameter with a maximum. [KiCad 10 custom rules](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html#custom_design_rules)

OSH Park publishes a 10 mil plated-drill clearance to internal copper. Its guidance gives alternative methods to achieve that clearance. It does not make one mitigation method mandatory. Keep connected-pad and unconnected-copper tests separate. [OSH Park four-layer service](https://docs.oshpark.com/services/four-layer/)

## Proposed implementation boundary

Keep two results: the normal project DRC result and the supplier-rule result. Neither replaces the other.

Run the supplier rules on a disposable project copy. Preserve the source PCB bytes. Make the generated rule file and necessary staged settings explicit artifacts. Record their hashes with the command and profile hash. Do not silently replace the user's rule file or lower a project constraint.

Do not refill zones during this supplier inspection. That could change the copper before the tool measures it. If the design needs a refill, complete that design change and its checks first. Then inspect the new source revision.

The supplier run must prevent project exclusions, severity settings, or later custom rules from hiding its mandatory checks. A simple fixed rule set for the five profiles is sufficient. No general rule-merging engine is necessary. The final proposal must name the staged settings and prove their effect with negative tests.

Keep recommendations separate from mandatory manufacturing limits. A local DRC waiver alone cannot prove that the supplier accepts a smaller manufacturing limit. Any exception needs applicable supplier evidence and an explicit profile decision.

## Necessary tests

- Put a weaker matching rule after a stronger rule. Show that the supplier result still detects the below-limit geometry.
- Set the applicable project severity to `ignore`. Show that this cannot produce a passed supplier result.
- Put an applicable exclusion in the source project. Preserve it in the source, but do not let it hide the supplier finding.
- Keep an intended same-net connection. Reject nearby unrelated internal copper below the published drill clearance.
- Test slot width independently from slot length. Do not turn the 250 mil tolerance threshold into a maximum diameter.
- Compare source hashes before and after the supplier run. Record the staged rule and setting hashes separately.

These tests supplement the below/at/above cases in the preparation reports. The fixed image must execute the generated rules. Documentation alone does not establish support for the selected patch version.
