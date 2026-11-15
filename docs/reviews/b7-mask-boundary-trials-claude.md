# B7 mask boundary trials (claude-skill-dev)

Date: 2026-11-14. Temporary fixtures only. Scratch path: `/tmp/claude-1000/-mnt-storage-projects-cad-skills/338648c2-5719-486b-b8c3-0bfb3fce6649/scratchpad/mask-fx`.
Image: `localhost/cad-skills-pcb:b6` (accepted B6 image, not changed). Export through `podman run --rm --pull=never --network none` with `kicad-cli pcb export gerbers --layers F.Cu,F.Mask`. Parser: gerbonara 1.6.3 and shapely 2.2.0 through `uv run` (PEP 723 header). Every script is a file, not `-c`.

## Results

| Case | Setting | Export exit | Gerber object | Measured web | Verdict |
|---|---|---|---|---|---|
| m39 | none | 0 | 2 flashes (circle, 0.6 mm) | 0.099060 mm = 3.9000 mil | separate openings |
| m40 | none | 0 | 2 flashes | 0.101600 mm = 4.0000 mil | separate openings |
| m41 | none | 0 | 2 flashes | 0.104140 mm = 4.1000 mil | separate openings |
| rr | none, RoundRect pads | 0 | 2 macro flashes (RoundRect) | not measured | refused: macro aperture |
| m39merge | `solder_mask_min_width 0.1016` | 0 | 2 regions, 25 points each | 0.104194 mm = 4.1000 mil (after shrink) | not merged; openings shrunk and approximated |

## Measured facts
- The web is the centre distance minus both radii. The three nominal gaps reproduce within 1 nm (Gerber 6 decimals).
- A 4 mil minimum web setting did not merge the 3.9 mil openings. KiCad shrank each circle from radius 0.300000 mm to 0.297433 mm and wrote it as a 25-point polygon. The web rose to 4.1 mil.
- Therefore the geometry decides the result. The setting changes the exported shape, so a checker must measure the exported file, not the setting value.
- RoundRect pads export as macro apertures. The measurement refuses them. A later checker must use the exact macro rule (see the geometry trial, section 7 of the trial record) or refuse.

## Derived bounds (not measured)
- Gerber resolution is 1 nm (6 decimals in mm). A distance from two coordinates has at most about 2 nm of rounding. Stated bound: 0.000002 mm per distance, plus floating-point error below 1e-12 mm.
- Polygon approximation in the 4 mil merge case is a separate error. It is measured here (radius change 0.002567 mm), not derived.

## Decision rule for B7
- Pass at and above the limit. Fail below it. A value within the bound of the limit cannot pass or fail on its own. Report it as uncertain.
- The 3.9 mil nominal fixture is a separate opening, so it measures as 3.9 mil and fails a 4.0 mil limit.

## Hashes (sha256, full)
5d37283f8e074398b17105e6dabab06a1d648772cae12218e7f16abb0ecf4d21  m39/board.kicad_pcb
d4c0c9d86b755950f8d15e772dd646db27140630250b53d2ea4e1c5a760d6afb  m40/board.kicad_pcb
62c09a27760456d914069c8b44cbf6dc55de10df76b16e8683370ccbbf2e5826  m41/board.kicad_pcb
1d0b9daa2f5d4fd2df4573b40cc05722eea29af26c7c9efa299cca8a8a0dbe97  rr/board.kicad_pcb
f66f4192e713223a5ab0d57c8b96ae6c1c02f938604c250bc46113fd908ce463  m39merge/board.kicad_pcb
35af87bf837a39eece079c8d6ecac411ba129993814e1dfdfebc0f99faec0518  m39/out/board-F_Mask.gts
518375fbc12909bcc3fae252bd9e1bea8ad0f711414db1df7b134aebef857680  m40/out/board-F_Mask.gts
5b8a781a738112d0f673fe71fb274ea5269aa6f8efaabf21b5795f1d26f53e2d  m41/out/board-F_Mask.gts
547f9117739e5fa382d024c15003ea8da2dfde062149e26804a8b8e4458b0054  rr/out/board-F_Mask.gts
872b14c6862c31a17f08dc55e01f7eb593834e8176082fbba5900007f84e392c  m39merge/out/board-F_Mask.gts

Measurement script: `/tmp/claude-1000/-mnt-storage-projects-cad-skills/338648c2-5719-486b-b8c3-0bfb3fce6649/scratchpad/mask-fx/measure.py` 9cb0dbe4f62051dccb45cc1b4ff2fd72b86967c9eddf48004025b970bf35c470
Merge check: `/tmp/claude-1000/-mnt-storage-projects-cad-skills/338648c2-5719-486b-b8c3-0bfb3fce6649/scratchpad/mask-fx/merge_check.py` a9332c1be6003cb30785487bf15dba0c2a2c9f032113ac62be4888bedc6d8b60; output f41652b1f8b0c58a70007ae725d02908e20dcc0f44849619bc067a9a778a15e8
Merge extent: `/tmp/claude-1000/-mnt-storage-projects-cad-skills/338648c2-5719-486b-b8c3-0bfb3fce6649/scratchpad/mask-fx/merge_extent.py` fa9b166697e5e161ec3048fc4a80902adcc00e63f841e6cbdb49af1a2db75ec4; output 83806c752b68891ae5efaeb37d11422ddf89d03f887e89316fb4c0c4ed183f43
Refusal script: `/tmp/claude-1000/-mnt-storage-projects-cad-skills/338648c2-5719-486b-b8c3-0bfb3fce6649/scratchpad/mask-fx/refuse_rr.py`; output 96d752d3823fa070365301d7d72058a5f222391f9fca30eb6507b2c6e6f9a36a
