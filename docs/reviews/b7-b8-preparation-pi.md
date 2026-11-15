# B7/B8 preparation review: Pi

Date: 2026-11-14.

**Decision: the plan and the source evidence agree. Nine decisions and the boundary tests below are necessary before the supplier-profile and package work. No implementation, container run or repeated test was done.**

## 1. Source check

The five OSH Park pages in `/tmp/cad-skills-supplier-evidence/` match `supplier-evidence-root.md`:

| Page | Bytes | SHA-256 |
|---|---:|---|
| single-layer | 12845 | `e937f343e7d4ce37d75770df6aff567c71de430b5421a1c34d63f430ffbacbc1` |
| two-layer | 20498 | `d757495f505f67436d6e9dc3b15d724c3d513d256372cbf7eb69523ae5913e25` |
| two-layer HHDC | 20695 | `641310abcd61e5b6c588b8f12554990e07941399f3d6cefce07c5602e16f1471` |
| four-layer | 28556 | `566570a807c779c60841a44c773e1f40f9ff4abc961c1d6b960025a7e22d3e38` |
| six-layer | 29228 | `e174c3a58bfa776f6f860b4fd2441174520dd7c20f6c51f4af273beb95060cfa` |

Facts that the profile must not lose:

- The single-layer service is a two-layer process. It needs the two-layer file set.
- The four-layer HTML has hidden historical stackup comments (January and June 2026). The rendered page and its changelog do not present them as current limits. Do not use them.
- The HHDC substrate is 4x 7628 Ventec VT-47 with a 28 mil core. The nominal finished board is 0.8 mm (32 mil). These are different values.

## 2. Confirmed limits

| Service | Layers | Thickness | Copper weight | Trace / space | Min drill | Min annular |
|---|---:|---:|---|---:|---:|---:|
| Single-layer | 2-layer process | same as two-layer | same as two-layer | 6 / 6 mil | 10 mil | 5 mil |
| Two-layer | 2 | 1.6 mm (63 mil) | 1 oz | 6 / 6 mil | 10 mil | 5 mil |
| Two-layer HHDC | 2 | 0.8 mm (32 mil) | 2 oz | 6 / 6 mil | 10 mil | 5 mil |
| Four-layer | 4 | 1.6 mm (63 mil) | 1 oz outer, 0.5 oz inner | 5 / 5 mil | 10 mil | 4 mil |
| Six-layer | 6 | 1.6 mm (63 mil) | 1 oz outer, 0.5 oz inner | 5 / 5 mil | 8 mil | 4 mil |

Common published limits:

- Board edge keepout: 15 mil (0.381 mm) from the nominal edge.
- Minimum slot: 20 mil (0.508 mm), drill slot only.
- Minimum mask web: 4 mil (0.1016 mm). Maximum mask alignment: 3 mil (0.0762 mm).
- Silkscreen: 5 mil (0.127 mm) recommended minimum. 3 mil (0.0762 mm) for short lines, text and graphics.
- Board size: minimum 0.25 in by 0.25 in (6.35 mm by 6.35 mm). Maximum 16 in by 22 in (406.4 mm by 558.8 mm).
- Via plating thickness: 1 mil (0.0254 mm).
- Outline tool: 0.068 in (1.72 mm), radius 0.034 in. Interior cutout tool: 0.040 in (1.01 mm), radius 0.020 in.
- Drill size tolerance: maximum +/- 2.5 mil (0.0635 mm), typical +/- 1.0 mil (0.0254 mm). Position: maximum 2 mil (0.0508 mm), typical below 1 mil (0.0254 mm).
- Blind vias, buried vias, and filled-and-plated via-in-pad: not supported.
- Overlapping drills: allowed but not guaranteed. 5 mil (0.127 mm) clearance is recommended.
- Castellations: allowed but not guaranteed.
- Maximum drill: none. Drills above 250 mil (6.35 mm) get larger milling tolerances.
- Four-layer and six-layer: plated drill to internal-layer copper clearance is 10 mil (0.254 mm). Positive internal planes are required.
- Material and finish: ENIG (Gold), compliant with IPC-4552; soldermask purple. Two-layer substrate is 175Tg FR4 (Kingboard KB6167F). HHDC substrate is 180Tg Ventec VT-47. Four-layer and six-layer use the published stackup.
- Record the finish, colour, stackup tolerances, drill tolerances and via plating as manual evidence. They are not `.kicad_dru` rules.
- Order quantity: multiples of three for every service.
- Keep the source unit for each value. Thickness uses mm (source 63/32 mil). Copper weight uses oz. Trace, drill and annular values use mil. Do not convert copper weight, temperature or counts to mil. Keep the source nominal and a separate rounded metric label. The exact dimensional conversion is 0.0254 mm/mil.
- Mask alignment, via plating, drill size/position tolerance and finished-thickness tolerance are process capability data. The tests validate the profile and evidence, not a fabricated board measurement.

## 3. Necessary decisions

| ID | Decision | Recommended answer |
|---|---|---|
| D1 | Profile unit | Use the source unit for each quantity. Dimensional values use mil or mm with the exact `MIL_TO_MM = 0.0254`. Copper weight stays `oz`, temperature stays `C`, and counts stay counts. The top-level `units` names the primary dimensional unit, and each limit's `unit` names its own unit. Keep the source nominal value and a separate rounded metric label. Do not overwrite the nominal. |
| D2 | Hard rule or recommendation | Design geometry: `minimum`/`maximum` for trace, space, annular, drill, slot, edge, mask web, board size, and the 10 mil internal clearance. `recommendation` for silkscreen 5 mil, overlapping-drill 5 mil, castellations and the 250 mil note. The 3 mil silkscreen value is the hard conditional minimum. Process capability, not a CAD measurement: mask alignment, via plating, drill size/position tolerance and finished-thickness tolerance. Record those as policy/evidence. |
| D3 | Rule division | Put each condition in exactly one `division` list: `.kicad_dru` for net-aware copper/drill clearances, project settings for stackup and net classes, geometric tests for outline, cutout and slot, manual evidence for finish, colour, tolerances and the order-quantity rule. No duplicates. |
| D4 | Drill-to-internal-copper scope | The 10 mil applies to internal copper that is not on the same net as the plated drill. A connected pad or plane at 0 mil must pass. An unconnected feature at 9.9 mil must fail, at 10 mil must pass. The page lists three alternative mitigations: always include annular rings, increase ground-plane clearance, or use custom net rules. Do not make one of them a universal supplier rule. The check tests the actual connected and unconnected clearance. |
| D5 | Stackup source | Use the rendered stackup and the visible changelog. Do not use the hidden January/June 2026 comments. Record the applicable stackup for impedance work. Recompute the page hash when the page changes. |
| D6 | HHDC thickness and single-layer files | Keep the 28 mil VT-47 core separate from the 0.8 mm nominal finished thickness. The single-layer profile reuses the two-layer limits and exports the two-layer file set. |
| D7 | Via construction | Reject blind, buried and filled-and-plated via-in-pad. Examine other via-in-pad geometry as manual evidence. A tented via is not a filled or flat pad. |
| D8 | Layer identity for four and six layers | Use the published copper filename pattern `.GTL`, `.G2L`, `.G3L`, `.GBL` with the neutral X2-off bytes. Add independent layer-content checks. Do not add an untested X2 export path merely for naming. |
| D9 | Evidence and qualification | The profile `evidence_sha256` is the page HTML hash. `retrieved` is 2026-11-14. A source-byte change triggers a review. Re-retrieve and compare the material limits. A harmless HTML change does not stop qualification after the review. An unresolved or material change stops qualification. Keep a draft export with an explicit `unconfirmed` status. |

## 4. Drill and internal-copper interpretation

The four-layer and six-layer page value is **Plated Drill to Internal Layer Copper Clearance: 10 mil (0.254 mm)**. It is not a blanket clearance to all internal copper.

- A plated through-hole connected to an internal plane is the same net. The pad, annulus and plane connection must pass. A rule that applies 10 mil to the connected plane would reject an intended connection.
- An unconnected internal copper feature at the drill edge must be at least 10 mil away.
- The page lists three alternative mitigations for the internal-layer clearance: always include annular rings, increase ground-plane clearance, or use custom net rules. These are alternatives, not a new universal supplier rule. The profile must not turn one of them into a mandatory rule for every unconnected layer.
- The check uses the actual annular ring and the actual drill position against the actual internal copper. It is not a clearance from the pad centre. It tests the connected and unconnected cases.

## 5. Boundary tests

| Test | Below | At | Above |
|---|---|---|---|
| Two-layer trace/space | 5.9 mil | 6 mil | 6.1 mil |
| Four/six-layer trace/space | 4.9 mil | 5 mil | 5.1 mil |
| Two-layer annular | 4.9 mil | 5 mil | 5.1 mil |
| Four/six-layer annular | 3.9 mil | 4 mil | 4.1 mil |
| Two/four-layer drill | 9.9 mil | 10 mil | 10.1 mil |
| Six-layer drill | 7.9 mil | 8 mil | 8.1 mil |
| Slot | 19.9 mil | 20 mil | 20.1 mil |
| Edge keepout | 14.9 mil | 15 mil | 15.1 mil |
| Mask web | 3.9 mil | 4 mil | 4.1 mil |
| Board size | 6.34 mm | 6.35 mm | 6.36 mm |
| Silkscreen | 2.9 mil fails | 3 mil passes for short lines/text/graphics | 4 mil passes with a recommendation warning, 5 mil passes |
| Overlapping drills | 4.9 mil passes with a warning | 5 mil passes | 5.1 mil passes |
| Max drill | 249 mil passes | 250 mil passes | 251 mil passes with a larger-tolerance note, never a max failure |
| Order quantity | 1 or 2 fails or is flagged | 3 passes | 4 or 5 fails or is flagged, no silent increase |
| Internal copper, connected | 0 mil passes (same net) | 0 mil passes | not applicable |
| Internal copper, unconnected | 9.9 mil fails | 10 mil passes | 10.1 mil passes |
| Blind via | fails | fails | fails |
| Buried via | fails | fails | fails |
| Filled-and-plated via-in-pad | fails | fails | fails |
| Tented via | not a filled/flat pad | not a filled/flat pad | not a filled/flat pad |
| Positive internal plane | negative plane fails or is converted | positive plane passes | clear-polarity hole primitives in a positive image pass |
| Outline concave corner | 0.033 in fails | 0.034 in passes | 0.035 in passes |
| Cutout concave corner | 0.019 in fails | 0.020 in passes | 0.021 in passes |
| Single-layer file set | one-layer set fails | two-layer set passes | not applicable |

Additional expectations:

- The drill-to-internal-copper test uses a net-aware rule or two explicit cases: connected and unconnected. It does not use a single blanket clearance.
- The positive internal-plane test renders the copper and compares it with the board. It does not judge only the file header.
- The four/six-layer layer order is unambiguous: use the published `.GTL/.G2L/.G3L/.GBL` names with the neutral X2-off bytes, and check the layer content independently. Do not rely on the neutral `.gbr` names alone. Do not add an untested X2 path merely for naming.
- The HHDC package uses 0.8 mm as the finished thickness and records the 28 mil VT-47 core as substrate data.
- The profile's `evidence_sha256` equals the page hash in section 1. A source-byte change triggers a review. A harmless HTML change can be accepted after the review. Only an unresolved or material change stops qualification.
- Mask alignment, via plating, drill size/position tolerance and finished-thickness tolerance are process capability data. Their checks validate that the profile records the published value, unit, source and retrieval. They do not measure a fabricated board from CAD geometry.
- The order-quantity rule is a package/order finding, not a `.kicad_dru` geometry rule. The tool must not silently increase 1 or 2 to 3.

## 6. Traps and limits

- Do not treat the 5 mil silkscreen value as the hard minimum. The hard conditional minimum is 3 mil for short lines, text and graphics.
- Do not treat the 5 mil overlapping-drill clearance as a hard minimum. It is a recommendation.
- Do not treat 250 mil as a maximum drill. It is a tolerance change.
- Do not use the hidden four-layer comments as current stackup limits.
- Do not use the 28 mil HHDC core as the finished board thickness.
- Do not export a one-layer file set for the single-layer service.
- Do not treat soldermask tenting as a filled and flat via-in-pad.
- Do not apply the 10 mil internal clearance to a connected plane.
- Do not turn one of the three internal-clearance mitigations into a universal rule for every unconnected layer.
- Do not reject clear-polarity primitives that form holes in a positive internal-plane image.
- Do not claim a fabricated measurement for mask alignment, via plating or finished-thickness tolerance. They are process capability data.
- Do not treat any HTML byte change as a permanent qualification stop. Review it. Only an unresolved or material change stops qualification.
- The pages are evidence of published service limits, not a promise that OSH Park accepts a given board or order.

This review uses the local snapshots and the accepted schema only. It makes no implementation change and starts no broad research.
