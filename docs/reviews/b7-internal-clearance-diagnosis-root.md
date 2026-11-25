# Internal copper clearance diagnosis

Date: 2026-11-15 UTC. Author: skill-dev-lead.

The lead reproduced the internal-track case with two controlled changes.
The source is the retained `scratchpad/clr/k_internal` board, project and rule files.
The original track center is at Y 10.45 mm. Its width is 0.2 mm.
The drilled pad center is at Y 10 mm. Its drill diameter is 0.3 mm.
The pad copper diameter is 0.5032 mm.
Thus the drill-to-track gap is 0.2 mm and the copper-to-track gap is 0.0984 mm.

The original report names only the copper clearance violation.
The supplier copper spacing minimum is 0.127 mm. The hole clearance minimum is 0.254 mm.

## Controlled cases

1. The lead moved the track center to Y 10.50146 mm, with all supplier rules unchanged.
   The hole gap is 0.25146 mm (9.9 mil). The copper gap is 0.14986 mm.
   The report names `hole_clearance`, measured 0.2515 mm against 0.2540 mm.
2. The lead kept the original board geometry and changed only the copper spacing rule to 0.01 mm.
   The report names `hole_clearance`, measured 0.2000 mm against 0.2540 mm.

Both commands exit 0 and use the existing local image with no pull and no network.
The reports show that the internal track can trigger the hole rule.
The earlier copper-spacing violation prevented a separate hole finding for that pair in these runs.
This is a measured reporting interaction. It does not establish a general rule for all KiCad violations.

The KiCad manual states that `hole_clearance` measures drilled-hole to different-net copper clearance.
Source: https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html#custom-design-rules

The first case uses the unchanged supplier rules and a through-hole pad.
It does not depend on a prohibited blind via.
The final boundary fixtures must retain the supplier rules and independent geometric expectations.
The relaxed-rule case is diagnostic evidence only.
