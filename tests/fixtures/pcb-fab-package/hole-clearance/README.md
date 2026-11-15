# Hole clearance fixtures (r8 rows 23 and 24)

Each board is a minimal four-layer KiCad 10 board with named nets. The hole under test is a through-hole pad on net `N1` in a footprint `Probe:THT_Hole`, at (10, 10) mm. The pad has a 0.3 mm drill and a 0.5032 mm copper diameter (0.1016 mm annulus, the minimum).

- `r24-unconnected-*`: a through via on net `GND` at the exact hole-to-copper gap. The via copper runs through In1.Cu. The rule is `plated_drill_to_internal_copper` (`hole_clearance`, min 0.254 mm). Gaps: 0.25146 mm (9.9 mil, fail), 0.254 mm (10 mil, pass), 0.25654 mm (10.1 mil, pass).
- `r23-same-net-0mil`: the copper via is on net `N1`, the hole's own net, at 0 mm. No finding is the pass.
- `probe-unconnected-0.2mm`: a deliberately large violation, gap 0.2 mm. The DRC must report 0.2000 mm.
- `r23-zone-internal-plane`: a GND zone on In1.Cu with 0.1 mm zone clearance. The zone must be refilled and saved before the check. The measured cutout radius is 0.40799 mm, so the hole gap is 0.25799 mm, which passes.

Each board is checked with `kicad-cli pcb drc` without `--refill-zones`, after the project severities and the supplier rule file are written by the workflow functions. The zone board is refilled and saved first, as the supplier path expects.

Measured on KiCad 10.0.5 (container `localhost/cad-skills-pcb:b6`) in the scratch probes. The probes showed:
- Changing the annulus did not change the zone cutout radius (0.40799 mm for pads of 0.4016 mm and 0.5032 mm).
- A `--refill-zones` pass removes the violations that a plain DRC reports on the same board. The check must run on the saved, filled board.
- Track copper on In1.Cu was not reported against a hole in the probes, so the fixtures use through-via copper.

## Internal-track boundaries and connected plane

The lead added these fixtures on 2026-11-15:

- `r24-internal-track-9.9mil.kicad_pcb`
- `r24-internal-track-10mil.kicad_pcb`
- `r24-internal-track-10.1mil.kicad_pcb`
- `r23-connected-plane-root.kicad_pcb`

The track fixtures contain copper only on `In1.Cu` at the test position.
The plated hole center is (10, 10) mm. Its drill radius is 0.15 mm.
The track width is 0.2 mm. Its center Y values are 10.50146, 10.50400 and 10.50654 mm.
Subtract the hole radius and half the track width to get the gaps: 0.25146, 0.25400 and 0.25654 mm.
These values equal 9.9, 10 and 10.1 mil.

The pad copper radius is 0.2516 mm. The copper-spacing gaps exceed the 0.127 mm supplier minimum.
This prevents the separate copper-spacing failure that concealed a hole finding in the earlier 0.2 mm probe.
The supplier rules stay unchanged for the three boundary cases.

The connected-plane fixture uses net `N1` for the plated pad and the `In1.Cu` zone.
The zone uses a full pad connection. The filled polygon contains the pad center.
The retained pcbnew measurement confirms these values. Thus the plane reaches the hole without a clearance gap.
The same-net exception gives no `hole_clearance` finding.

Evidence: `docs/reviews/b7-completion-evidence/internal-copper-root/`.
The focused boundary test passes four of four cases.
The relaxed-spacing probe is diagnostic evidence only. It is not an acceptance fixture.
