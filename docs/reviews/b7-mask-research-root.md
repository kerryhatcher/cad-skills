# B7 mask inspection note

Date: 2026-11-14.

KiCad's minimum mask-web setting can merge nearby openings during plotting. Its pad-level expansion overrides can also change the openings. Thus, pad spacing and the saved setting alone do not establish the exported web. [KiCad 10 manual](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html)

The B7 trial must compare the effective exported openings. Include separate narrow webs and merged openings. Distinguish a narrow piece of mask from a single opening with no intervening web. Do not infer a manufacturing failure from a pre-export gap that the exporter removes. Record any separate assembly concern as its own condition.

Before implementation agreement, name the geometry method and tolerance. The below/at/above fixtures must exercise exported geometry. A parameter-only test cannot satisfy the geometric claim.
