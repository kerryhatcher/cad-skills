# B7 rule-generation review: Codex

Date: 2026-11-14 UTC.

**I agree with the research boundary and Pi's design points.** Keep the normal project DRC and supplier-rule inspection as separate results. Run supplier rules on a staged project copy. Preserve source PCB bytes and source rule and severity settings. Do not refill zones during supplier inspection.

Use `hole_clearance` for the OSH Park plated-drill clearance to internal copper. Its different-net behavior keeps intended same-net connections valid. Test connected and unconnected copper separately. Use `inner` for internal copper. Keep `physical_hole_clearance` out of cases where same-net connections must pass.

Use staged rules and staged severity settings. Record the generated rule hash, staged settings hash, source PCB hash, supplier profile hash, and command. Mandatory rules must resist later weaker rules, project `ignore` severity, and source exclusions. Keep source settings unchanged. Do not build a general rule-merging engine.

Test slot width separately from slot length. `hole_size` compares the minor dimension with a minimum and the major dimension with a maximum. Do not treat the 250 mil tolerance threshold as a maximum drill diameter. A supplier exception needs supplier evidence and an explicit profile decision. A local DRC waiver does not establish supplier acceptance.

Required focused tests:

- A weaker matching rule after a mandatory supplier rule does not hide a below-limit finding.
- Project `ignore` severity and an applicable source exclusion do not hide a supplier finding. The source settings remain unchanged.
- A connected same-net feature at 0 mil passes the `hole_clearance` rule. An unconnected internal feature at 9.9 mil fails, and one at 10 mil passes.
- Slot width and length exercise their separate limits. Drill sizes above 250 mil do not fail solely because of diameter.
- Source PCB bytes match before and after inspection. Staged rule and severity files have recorded hashes.

This is a paper agreement only. I did not run KiCad rules or a container. The fixed image must later execute these rules and fixtures before B7 support claims. The B6 interim review remains separate and open.
