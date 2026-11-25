# Hole-clearance fixture diagnostic (codex-skill-dev)

Date: 2026-11-15 UTC. Scope: retained evidence and KiCad 10.0.5 rule behavior. No product file changed. No broad suite ran. No probe was run because the retained evidence does not include the source boards or `.kicad_dru` for `g_02.out` and `i_02.out`.

## Initial retained findings

The retained logs do not demonstrate internal-layer `hole_clearance` coverage.

- `g_02.out` reports a `clearance` violation between `Track [GND] on In1.Cu` and a through via. Its measured copper-to-copper gap is 0.0984 mm, below the 0.1270 mm `supplier_min_space` limit. It reports no `hole_clearance` violation.
- `i_02.out` reports four `hole_clearance` violations between a PTH pad and a through via. Each reports a 0.2000 mm hole clearance against the 0.2540 mm custom-rule limit. The log does not identify an internal-layer copper object as the offending item.
- `zone-r23-drc.json` identifies a filled zone on `In1.Cu`, but reports only isolated copper and a footprint-library warning. It reports no `hole_clearance` violation. The DRC JSON does not retain the board or rule bytes.

The most likely explanation for `g_02` is fixture geometry, not proof of an engine scope limit. `hole_clearance` measures from the drill boundary. The observed 0.0984 mm is the track-to-via copper gap. A via annular ring separates those measurements. The retained output does not give the via annular width or hole-to-track distance, so it cannot establish that the drill clearance fell below 0.2540 mm. The standard `clearance` finding only proves that copper shapes violate the 0.1270 mm spacing rule.

KiCad 10.0 documentation defines `hole_clearance` as clearance from a drilled hole in a pad or via to copper on a different net. It defines the `inner` selector as applying to internal copper layers. This supports internal-layer applicability, but does not replace a measured negative fixture. [KiCad 10 PCB Editor manual](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html#custom_design_rules)

## Diagnostic limit

## Bounded engine-scope explanation

The author supplied the exact acceptance fixture method: copy each board to a scratch directory, write `workflow.effective_pro(b'', profile)` to `board.kicad_pro`, write `workflow.supplier_rules_text(profile)` to `board.kicad_dru`, then run KiCad DRC with `--severity-all` and no refill. The owned fixtures produce an internal-only blind via finding at 0.2000 mm on `In1.Cu - In2.Cu`, and an outer via control finding at the same 0.2000 mm. `internal-negative-checks.txt` records both results. This meets the internal-only and outer-layer control requirement. It does not establish a manufacturable internal plane case.

The KiCad 10.0 manual gives the relevant scope. A hole-clearance violation requires a drilled hole in a pad or via and another copper object. The objects must share at least one layer. The rule `hole_clearance` compares the drill boundary with different-net copper. Thus a track or SMD pad cannot act as the drilled-hole side of this constraint. A track can act as the copper side only when it shares a copper layer with a drilled pad or via and violates the configured distance. The manual also confirms that internal copper layers are selectable with the `inner` layer selector. [KiCad 10 PCB Editor manual](https://docs.kicad.org/10.0/en/pcbnew/pcbnew.html#custom-design-rules)

This explains the tested blind-via and through-via behavior: each via is a drilled-hole object, and its span supplies the shared internal or outer copper layers. The rule reports 0.2000 mm against its 0.2540 mm minimum. The manual's layer-intersection scope and different-net condition explain why object class, shared layer, net, and drill-boundary distance matter. They do not establish why the author's track and SMD-pad probes failed. Those probes and their exact measured geometry are not among the retained fixtures or reports. The cause of those specific negative results is therefore undetermined, not evidence of an engine limitation.

The older `g_02` fixture remains ambiguous. Its reported 0.0984 mm value is track-to-via copper clearance, not drill-boundary clearance. It can violate `supplier_min_space` at 0.1270 mm while not violating `hole_clearance` at 0.2540 mm. The missing hole-to-track measurement prevents a stronger conclusion.

## Scratch-pair comparison

The author supplied `/tmp/claude-1000/-mnt-storage-projects-cad-skills/1498d7bc-bc96-42a4-a233-ae48c580ec6e/scratchpad/clr`. The paired `k_internal` and `k_smd_internal` files identify the probes. Both report a `supplier_min_space` violation at 0.0984 mm and no `hole_clearance` finding. The objects are a PTH pad on N1 and, respectively, an In1.Cu track or an In1.Cu SMD pad on GND. The outer-layer counterparts report the same result. Their paired boards differ from the `k_via_internal` and `k_via_outer` via probes.

The one rule file in `k_internal/board.kicad_dru` has an unconditional `hole_clearance` minimum of 0.254 mm. It has no type or layer condition. Thus a rule condition does not explain the difference. The tracks and SMD pads serve as the copper target; the PTH pad serves as the drilled-hole object. The via probe also has a drilled via and produces the finding. KiCad's documented constraint applies to a drilled hole in a pad or via and copper on a shared layer, so the observed track/SMD distinction is not explained by documented object scope. The retained DRC output reports copper spacing of 0.0984 mm but does not report the hole-to-copper distance for those pairs. The board geometry must be read from the paired bytes before we can attribute the absence to clearance distance, same-net status, or an engine defect. No claim of internal-track or SMD coverage follows from the via result.

This is the bounded finding: internal and outer blind/through via hole-clearance checks work at 0.2000 mm against 0.2540 mm. The tested PTH-to-track and PTH-to-SMD pairs do not report that constraint, despite 0.0984 mm copper spacing. The published scope supports pads, tracks, vias, and zones as the two objects, subject to common layers and different nets. The exact cause for these negative pairs remains unresolved from the reports alone. The separate `r23-zone-internal-plane` fixture has a measured 0.25799 mm gap and passes, so it does not test a below-limit plane violation.

## Stable row 23 and 24 evidence

I examined the stable 40-file evidence set. Its manifest hash is `c6a417802c5a2ccdb8cf8256fa04e3fe6f8c33a8d1cfd2ef21a7dc1c86f9d8aa`; all 40 entries pass `sha256sum -c`. The focused boundary log reports four of four cases passed, exit 0. The runtime record names KiCad image `localhost/cad-skills-pcb:b6`, identity `b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f`, network `none`, and pull `never`.

For row 24, independent geometry uses the hole radius 0.15 mm and track half-width 0.1 mm. Track centers at Y 10.50146, 10.50400, and 10.50654 mm give edge gaps 0.25146, 0.25400, and 0.25654 mm. The supplier rule remains at 0.254 mm. The 9.9 mil case reports 0.2515 mm. The 10 and 10.1 mil cases report no finding. The README also records that copper-to-copper spacing exceeds the 0.127 mm supplier minimum in these fixtures.

For row 23, the same-net filled In1.Cu plane uses N1, contains the plated pad center, and has a full pad connection. The retained measurement JSON confirms the same net and filled containment. DRC reports no hole-clearance finding. This supports the same-net exception for this fixture. The plane case is distinct from the earlier different-net zone fixture, whose measured gap was 0.25799 mm and which only tested a passing clearance.

These results close the bounded row 23/24 fixture questions represented by this evidence. They do not close other acceptance rows, nor establish a universal KiCad behavior beyond the measured fixtures. The earlier 0.2 mm interaction probe changed copper spacing and remains diagnostic only.

Do not claim coverage until a scratch-copy DRC demonstrates both:

1. An internal-only, different-net copper feature with drill-edge clearance below 0.2540 mm produces `hole_clearance`.
2. An outer-layer control with the same rule and measured violation produces the expected result.

Record the source board, staged rule, image identity, command, exits, and measured drill-edge limits for both cases. The reference limits in the retained evidence are 0.2540 mm (10 mil) for `hole_clearance` and 0.1270 mm (5 mil) for `supplier_min_space`.
