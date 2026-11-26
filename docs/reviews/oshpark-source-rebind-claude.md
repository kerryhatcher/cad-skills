# OSH Park source rebind (issue #10)

## 1. Header

- Date (UTC): 2026-11-26.
- Issue: #10. Part: `oshrev`. Implementer: `claude`.
- Base commit: `b25f478`, the same commit as `sheepdog/issues`.
- Binding commit: `5c86077`. This note is in the next commit.
- Fetch date: 2026-11-26.
- Decisions: the lead decision of revision 2, set 3, and the lead decision of 2026-11-26 after the stop at step 3.

## 2. Why `review-source` did not run

- The earlier stored copies are not on this machine (review B2).
- The live pages give new bytes on each fetch. The visible text did not change.
- `review.py` refuses an observation key that the profile does not define (review B3).
- Therefore `fab.py review-source` did not run.
- Git history holds the earlier bound copies, commit `b5872c5^`. This run uses them for the text comparison only.
- The lead decided to bind one saved download of each page. This note records that rebind.

## 3. Pages

Each page has one saved download. The `sha256` is the hash of the saved bytes. The `text_sha256` is the hash of the visible text.

| Page | Old `sha256` | New `sha256` | New `text_sha256` | Headers `sha256` | Re-check before | Re-check after |
|---|---|---|---|---|---|---|
| single-layer | `e937f343e7d4ce37d75770df6aff567c71de430b5421a1c34d63f430ffbacbc1` | `07f95f3cbc3fedda605f9c1751c87834aea1ea451c929e1a42aed3951657ee9b` | `ce48f1dd32c83d362161e678c1931adb881c48af42e630dc0727a746a08ec843` | `747146e89774873c9cc10a02e5ad9e6d8b0ac01dba9c316acbf7fe89f8363050` | changed | layout |
| two-layer | `d757495f505f67436d6e9dc3b15d724c3d513d256372cbf7eb69523ae5913e25` | `fae87affe67341bcd6674a406add9f705ae0465da797e23463aef86b3004c2d1` | `ecd1d62828ac8bbfe1023db7e87d10ce4bf68f921464787ec624a4ad1bac727f` | `6c45403a897bd085a5091fbaf1281a3a39b81994c12c67a26f3eef860a7f3b81` | changed | layout |
| two-layer-hhdc | `641310abcd61e5b6c588b8f12554990e07941399f3d6cefce07c5602e16f1471` | `3ed7a43401b10ea7a781e10a40e973a6155b14d9955b96f718ef643d1a23fd58` | `549433196665c0c122db6afef0be333ff44980711d1828acac9a101b775e43da` | `5d4917a48afe360e6597deefcd5fbac4c6e76d173552ad1a078e9fe6baa2ad40` | changed | layout |
| four-layer | `566570a807c779c60841a44c773e1f40f9ff4abc961c1d6b960025a7e22d3e38` | `4eb0af38b6dfaed2d33adde1c72605d9e1431e5925e61539be89ebc00c8dd1cc` | `94ad5301df55e3f408ffe651087872d0a724f8836a471eb2eea7a160316a91fd` | `3e465be86038832bcc0d656eed9c2ae649744feae3ef1a521adaf2e6858d586f` | changed | layout |
| six-layer | `e174c3a58bfa776f6f860b4fd2441174520dd7c20f6c51f4af273beb95060cfa` | `f92c6f15f673801569db0fe097d12e73d9b85aea297644915c43966a451ab4e2` | `bc02ae797ce7f0f24ebe95293de7ad4867b30e7feb314eaf6507c6fbb7ae7f3a` | `9d0f0065c4cbd6ea988de86bc770d00daf02539544c06cfce824230cbe5abb11` | changed | layout |

The re-check before the rebind gives `changed` for each page. The re-check after the rebind gives `layout`. `layout` means that the bytes differ and the visible text matches. The exit is 0. The byte change is the Cloudflare email-protection token in the footer of each page.

Each headers file starts with `HTTP/2 200`. The headers change on each response, so the saved headers file is the evidence for each page.

## 4. Comparison method

- Tools: `fetch_sources.py` (the text rule `visible_text` and `text_sha256`), `recheck_sources.py`, and `review.fact_items` (the fact list).
- Steps:
  1. One `curl` download for each page. The download saves the body and the headers.
  2. A check-only fetch after the download gives the same `observed_text_sha256` for each page as the saved bytes.
  3. The rebind changes `sources.yaml`, the five profiles and their `content_sha256`.
  4. A check-only fetch after the rebind gives exit 0 and `layout` for each page.
  5. We compare the visible text of each old copy with that of each saved copy. The text is byte-identical for each page.
  6. We match each fact of each profile with the text of its source page.
- Classes of the changed regions: no region changed. No region has the class `fact`.
- Answers to the open questions: Q1 default. Q2 default, with one `curl` download for each header file. Q3 amended, the date in `license_state` changed. Q4 default. Q5 default, no change to `recheck_sources.py`. Q6 replaced by the lead decision. Q7 default, the name `claude`.

## 5. Result for each profile

| Profile | Facts | Limits | Extension facts | Same | Differs |
|---|---|---|---|---|---|
| single-layer | 28 | 13 | 15 | 28 | 0 |
| two-layer | 28 | 13 | 15 | 28 | 0 |
| two-layer-hhdc | 28 | 13 | 15 | 28 | 0 |
| four-layer | 29 | 14 | 15 | 29 | 0 |
| six-layer | 29 | 14 | 15 | 29 | 0 |

All 142 facts give the same value on the new page. No fact is missing from the new page.

Some facts derive from other text. The table gives the source text for each one.

- The single-layer page says that its cost, stackup, specs and turn time are identical to the 2 layer service. We check its limits and its stackup facts on the two-layer page.
- The six-layer value `published stackup` is a reference to the stackup of the page. The page gives the stackup in its material table and in its construction diagram.
- The profile writes `less than 1 mil`. The page writes `<1mil`. It is the same limit.

The table below lists each fact. The page text is a short excerpt, not the full page.

| Profile | Key | Profile value | Page | Page text (short) | Result | Basis |
|---|---|---|---|---|---|---|
| single-layer | `board_max_height` | 22 in | two-layer | Maximum board size 16in (406.4mm) by 22in | same | derived; single-layer page: specs identical to the 2 layer service |
| single-layer | `board_max_width` | 16 in | two-layer | Maximum board size 16in (406.4mm) by 22in | same | derived; single-layer page: specs identical to the 2 layer service |
| single-layer | `board_min_edge` | 0.25 in | two-layer | Minimum board size 0.25in | same | derived; single-layer page: specs identical to the 2 layer service |
| single-layer | `edge_keepout` | 15 mil | two-layer | Board Edge Keepout 15mil | same | derived; single-layer page: specs identical to the 2 layer service |
| single-layer | `mask_web_min` | 4 mil | two-layer | Minimum soldermask web 4 mil | same | derived; single-layer page: specs identical to the 2 layer service |
| single-layer | `min_annular_ring` | 5 mil | two-layer | Minimum Annular Ring 5mil | same | derived; single-layer page: specs identical to the 2 layer service |
| single-layer | `min_drill` | 10 mil | two-layer | Minimum Drill Size 10mil | same | derived; single-layer page: specs identical to the 2 layer service |
| single-layer | `min_slot_size` | 20 mil | two-layer | Minimum Slot Size 20mil | same | derived; single-layer page: specs identical to the 2 layer service |
| single-layer | `min_space` | 6 mil | two-layer | Trace Spacing 6mil | same | derived; single-layer page: specs identical to the 2 layer service |
| single-layer | `min_trace` | 6 mil | two-layer | Trace Width 6mil | same | derived; single-layer page: specs identical to the 2 layer service |
| single-layer | `overlapping_drill_clearance` | 5 mil | two-layer | 5 mil (0.127mm) clearance is recommended | same | derived; single-layer page: specs identical to the 2 layer service |
| single-layer | `silk_line_min_short_text` | 3 mil | two-layer | 3 mil (0.0762mm) (short lines | same | derived; single-layer page: specs identical to the 2 layer service |
| single-layer | `silk_line_recommended` | 5 mil | two-layer | Silkscreen minimum line width 5 mil | same | derived; single-layer page: specs identical to the 2 layer service |
| single-layer | `service.layers` | 2 | single-layer | 2 layer fabrication service | same | derived; single-layer page: "support single layer designs on our 2 layer fabrication service" |
| single-layer | `service.order_multiple` | 3 | single-layer | multiples of three | same | direct |
| single-layer | `service.copper` | 1 oz | single-layer | Copper Weight 1oz (two-layer page) | same | derived; from the two-layer page |
| single-layer | `service.substrate` | two-layer | single-layer | two-layer | same | derived; single-layer page: "support single layer designs on our 2 layer fabrication service" |
| single-layer | `service.finished_thickness_source` | 63 mil | two-layer | Board Thickness 63mil | same | derived; single-layer page: specs identical to the 2 layer service |
| single-layer | `service.finished_thickness_display_mm` | 1.6 | two-layer | Board Thickness 63mil (1.6mm) | same | derived; single-layer page: specs identical to the 2 layer service |
| single-layer | `service.via_construction_prohibited` | ['blind', 'buried', 'filled_plated_via_in_pad'] | single-layer | Buried Via No; Blind Via No; Filled+Plated Vias (via-in-pad) No (two-layer page) | same | derived; single-layer page: specs identical to the 2 layer service |
| single-layer | `process.mask_alignment_max_mil` | 3 | two-layer | Maximum soldermask alignment 3mil | same | derived; single-layer page: specs identical to the 2 layer service |
| single-layer | `process.drill_size_tolerance_max_mil` | 2.5 | two-layer | Drill Size tolerance Max: +/- 2.5mil | same | derived; single-layer page: specs identical to the 2 layer service |
| single-layer | `process.drill_size_tolerance_typical_mil` | 1.0 | two-layer | Drill Size tolerance Max: +/- 2.5mil (0.0635mm) Typical: +/- ... | same | derived; single-layer page: specs identical to the 2 layer service |
| single-layer | `process.drill_position_tolerance_max_mil` | 2 | two-layer | Drill Positional Tolerance Max: 2mil | same | derived; single-layer page: specs identical to the 2 layer service |
| single-layer | `process.drill_position_tolerance_typical` | less than 1 mil | two-layer | Drill Positional Tolerance Max: 2mil (0.0508mm) Typical: <1mil | same | derived; single-layer page: specs identical to the 2 layer service |
| single-layer | `notes.max_drill` | Maximum Drill Size None; above 250mil larger milling tolerances. Process note, not a limit. | single-layer | Maximum Drill Size None (two-layer page) | same | derived; single-layer page: specs identical to the 2 layer service |
| single-layer | `process.outline_cutter_diameter` | 0.068 in | two-layer | Outline/profile milling: 0.068” | same | direct |
| single-layer | `process.cutout_cutter_diameter` | 0.040 in | two-layer | Interior/cutout milling: 0.040” | same | direct |
| two-layer | `board_max_height` | 22 in | two-layer | Maximum board size 16in (406.4mm) by 22in | same | direct |
| two-layer | `board_max_width` | 16 in | two-layer | Maximum board size 16in (406.4mm) by 22in | same | direct |
| two-layer | `board_min_edge` | 0.25 in | two-layer | Minimum board size 0.25in | same | direct |
| two-layer | `edge_keepout` | 15 mil | two-layer | Board Edge Keepout 15mil | same | direct |
| two-layer | `mask_web_min` | 4 mil | two-layer | Minimum soldermask web 4 mil | same | direct |
| two-layer | `min_annular_ring` | 5 mil | two-layer | Minimum Annular Ring 5mil | same | direct |
| two-layer | `min_drill` | 10 mil | two-layer | Minimum Drill Size 10mil | same | direct |
| two-layer | `min_slot_size` | 20 mil | two-layer | Minimum Slot Size 20mil | same | direct |
| two-layer | `min_space` | 6 mil | two-layer | Trace Spacing 6mil | same | direct |
| two-layer | `min_trace` | 6 mil | two-layer | Trace Width 6mil | same | direct |
| two-layer | `overlapping_drill_clearance` | 5 mil | two-layer | 5 mil (0.127mm) clearance is recommended | same | direct |
| two-layer | `silk_line_min_short_text` | 3 mil | two-layer | 3 mil (0.0762mm) (short lines | same | direct |
| two-layer | `silk_line_recommended` | 5 mil | two-layer | Silkscreen minimum line width 5 mil | same | direct |
| two-layer | `service.layers` | 2 | two-layer | Copper Layers 2 | same | direct |
| two-layer | `service.order_multiple` | 3 | two-layer | multiples of three | same | direct |
| two-layer | `service.copper` | 1 oz | two-layer | Copper Weight 1oz Trace | same | direct |
| two-layer | `service.substrate` | 175Tg FR4 (Kingboard KB6167F) | two-layer | 175Tg FR4 Kingboard KB6167F | same | direct; punctuation only: profile has brackets |
| two-layer | `service.finished_thickness_source` | 63 mil | two-layer | Board Thickness 63mil | same | direct |
| two-layer | `service.finished_thickness_display_mm` | 1.6 | two-layer | Board Thickness 63mil (1.6mm) | same | direct |
| two-layer | `service.via_construction_prohibited` | ['blind', 'buried', 'filled_plated_via_in_pad'] | two-layer | Buried Via No; Blind Via No; Filled+Plated Vias (via-in-pad) No | same | direct |
| two-layer | `process.mask_alignment_max_mil` | 3 | two-layer | Maximum soldermask alignment 3mil | same | direct |
| two-layer | `process.drill_size_tolerance_max_mil` | 2.5 | two-layer | Drill Size tolerance Max: +/- 2.5mil | same | direct |
| two-layer | `process.drill_size_tolerance_typical_mil` | 1.0 | two-layer | Drill Size tolerance Max: +/- 2.5mil (0.0635mm) Typical: +/- ... | same | direct |
| two-layer | `process.drill_position_tolerance_max_mil` | 2 | two-layer | Drill Positional Tolerance Max: 2mil | same | direct |
| two-layer | `process.drill_position_tolerance_typical` | less than 1 mil | two-layer | Drill Positional Tolerance Max: 2mil (0.0508mm) Typical: <1mil | same | direct |
| two-layer | `notes.max_drill` | Maximum Drill Size None; above 250mil larger milling tolerances. Process note, not a limit. | two-layer | Maximum Drill Size None; Drill sizes above 250mil (6.35mm) will be fabbed, but with larger milling tolerances | same | direct; process note, not a limit |
| two-layer | `process.outline_cutter_diameter` | 0.068 in | two-layer | Outline/profile milling: 0.068” | same | direct |
| two-layer | `process.cutout_cutter_diameter` | 0.040 in | two-layer | Interior/cutout milling: 0.040” | same | direct |
| two-layer-hhdc | `board_max_height` | 22 in | two-layer-hhdc | Maximum board size 16in (406.4mm) by 22in | same | direct |
| two-layer-hhdc | `board_max_width` | 16 in | two-layer-hhdc | Maximum board size 16in (406.4mm) by 22in | same | direct |
| two-layer-hhdc | `board_min_edge` | 0.25 in | two-layer-hhdc | Minimum board size 0.25in | same | direct |
| two-layer-hhdc | `edge_keepout` | 15 mil | two-layer-hhdc | Board Edge Keepout 15mil | same | direct |
| two-layer-hhdc | `mask_web_min` | 4 mil | two-layer-hhdc | Minimum soldermask web 4 mil | same | direct |
| two-layer-hhdc | `min_annular_ring` | 5 mil | two-layer-hhdc | Minimum Annular Ring 5mil | same | direct |
| two-layer-hhdc | `min_drill` | 10 mil | two-layer-hhdc | Minimum Drill Size 10mil | same | direct |
| two-layer-hhdc | `min_slot_size` | 20 mil | two-layer-hhdc | Minimum Slot Size 20mil | same | direct |
| two-layer-hhdc | `min_space` | 6 mil | two-layer-hhdc | Trace Spacing 6mil | same | direct |
| two-layer-hhdc | `min_trace` | 6 mil | two-layer-hhdc | Trace Width 6mil | same | direct |
| two-layer-hhdc | `overlapping_drill_clearance` | 5 mil | two-layer-hhdc | 5 mil (0.127mm) clearance is recommended | same | direct |
| two-layer-hhdc | `silk_line_min_short_text` | 3 mil | two-layer-hhdc | 3 mil (0.0762mm) (short lines | same | direct |
| two-layer-hhdc | `silk_line_recommended` | 5 mil | two-layer-hhdc | Silkscreen minimum line width 5 mil | same | direct |
| two-layer-hhdc | `service.layers` | 2 | two-layer-hhdc | Copper Layers 2 | same | direct |
| two-layer-hhdc | `service.order_multiple` | 3 | two-layer-hhdc | multiples of three | same | direct |
| two-layer-hhdc | `service.copper` | 2 oz | two-layer-hhdc | Copper Weight 2oz Trace | same | direct |
| two-layer-hhdc | `service.substrate` | 180 Tg FR4 Ventec VT-47, core 4x 7628 Ventec VT-47, 28 mil (0.711mm) core | two-layer-hhdc | 180 Tg FR4 Ventec VT-47; Core construction: 4x 7628 Ventec VT-47; 28mil (0.711mm) core | same | direct; three parts of one stackup text |
| two-layer-hhdc | `service.finished_thickness_source` | 32 mil | two-layer-hhdc | Board Thickness 32mil | same | direct |
| two-layer-hhdc | `service.finished_thickness_display_mm` | 0.8 | two-layer-hhdc | Board Thickness 32mil (0.8mm) | same | direct |
| two-layer-hhdc | `service.via_construction_prohibited` | ['blind', 'buried', 'filled_plated_via_in_pad'] | two-layer-hhdc | Buried Via No; Blind Via No; Filled+Plated Vias (via-in-pad) No | same | direct |
| two-layer-hhdc | `process.mask_alignment_max_mil` | 3 | two-layer-hhdc | Maximum soldermask alignment 3mil | same | direct |
| two-layer-hhdc | `process.drill_size_tolerance_max_mil` | 2.5 | two-layer-hhdc | Drill Size tolerance Max: +/- 2.5mil | same | direct |
| two-layer-hhdc | `process.drill_size_tolerance_typical_mil` | 1.0 | two-layer-hhdc | Drill Size tolerance Max: +/- 2.5mil (0.0635mm) Typical: +/- ... | same | direct |
| two-layer-hhdc | `process.drill_position_tolerance_max_mil` | 2 | two-layer-hhdc | Drill Positional Tolerance Max: 2mil | same | direct |
| two-layer-hhdc | `process.drill_position_tolerance_typical` | less than 1 mil | two-layer-hhdc | Drill Positional Tolerance Max: 2mil (0.0508mm) Typical: <1mil | same | direct |
| two-layer-hhdc | `notes.max_drill` | Maximum Drill Size None; above 250mil larger milling tolerances. Process note, not a limit. | two-layer-hhdc | Maximum Drill Size None; Drill sizes above 250mil (6.35mm) will be fabbed, but with larger milling tolerances | same | direct; process note, not a limit |
| two-layer-hhdc | `process.outline_cutter_diameter` | 0.068 in | two-layer-hhdc | Outline/profile milling: 0.068” | same | direct |
| two-layer-hhdc | `process.cutout_cutter_diameter` | 0.040 in | two-layer-hhdc | Interior/cutout milling: 0.040” | same | direct |
| four-layer | `board_max_height` | 22 in | four-layer | Maximum board size 16in (406.4mm) by 22in | same | direct |
| four-layer | `board_max_width` | 16 in | four-layer | Maximum board size 16in (406.4mm) by 22in | same | direct |
| four-layer | `board_min_edge` | 0.25 in | four-layer | Minimum board size 0.25in | same | direct |
| four-layer | `edge_keepout` | 15 mil | four-layer | Board Edge Keepout 15mil | same | direct |
| four-layer | `mask_web_min` | 4 mil | four-layer | Minimum soldermask web 4 mil | same | direct |
| four-layer | `min_annular_ring` | 4 mil | four-layer | Minimum Annular Ring 4mil | same | direct |
| four-layer | `min_drill` | 10 mil | four-layer | Minimum Drill Size 10mil | same | direct |
| four-layer | `min_slot_size` | 20 mil | four-layer | Minimum Slot Size 20mil | same | direct |
| four-layer | `min_space` | 5 mil | four-layer | Trace Spacing 5mil | same | direct |
| four-layer | `min_trace` | 5 mil | four-layer | Trace Width 5mil | same | direct |
| four-layer | `overlapping_drill_clearance` | 5 mil | four-layer | 5 mil (0.127mm) clearance is recommended | same | direct |
| four-layer | `plated_drill_to_internal_copper` | 10 mil | four-layer | Plated Drill to Internal Layer Copper Clearance 10mil | same | direct |
| four-layer | `silk_line_min_short_text` | 3 mil | four-layer | 3 mil (0.0762mm) (short lines | same | direct |
| four-layer | `silk_line_recommended` | 5 mil | four-layer | Silkscreen minimum line width 5 mil | same | direct |
| four-layer | `service.layers` | 4 | four-layer | Copper Layers 4 | same | direct |
| four-layer | `service.order_multiple` | 3 | four-layer | multiples of three | same | direct |
| four-layer | `service.copper` | 1 oz outer, 1/2 oz inner | four-layer | Copper Weight 1oz outer 1/2oz inner Trace | same | direct |
| four-layer | `service.substrate` | 190Tg FR408-HR | four-layer | 190Tg FR408-HR ISOLA FR408-HR | same | direct; main material table; the changelog note of 28-JAN-2026 is a temporary alternate |
| four-layer | `service.finished_thickness_source` | 63 mil | four-layer | Board Thickness 63mil | same | direct |
| four-layer | `service.finished_thickness_display_mm` | 1.6 | four-layer | Board Thickness 63mil (1.6mm) | same | direct |
| four-layer | `service.via_construction_prohibited` | ['blind', 'buried', 'filled_plated_via_in_pad'] | four-layer | Buried Via No; Blind Via No; Filled+Plated Vias (via-in-pad) No | same | direct |
| four-layer | `process.mask_alignment_max_mil` | 3 | four-layer | Maximum soldermask alignment 3mil | same | direct |
| four-layer | `process.drill_size_tolerance_max_mil` | 2.5 | four-layer | Drill Size tolerance Max: +/- 2.5mil | same | direct |
| four-layer | `process.drill_size_tolerance_typical_mil` | 1.0 | four-layer | Drill Size tolerance Max: +/- 2.5mil (0.0635mm) Typical: +/- ... | same | direct |
| four-layer | `process.drill_position_tolerance_max_mil` | 2 | four-layer | Drill Positional Tolerance Max: 2mil | same | direct |
| four-layer | `process.drill_position_tolerance_typical` | less than 1 mil | four-layer | Drill Positional Tolerance Max: 2mil (0.0508mm) Typical: <1mil | same | direct |
| four-layer | `notes.max_drill` | Maximum Drill Size None; above 250mil larger milling tolerances. Process note, not a limit. | four-layer | Maximum Drill Size None; Drill sizes above 250mil (6.35mm) will be fabbed, but with larger milling tolerances | same | direct; process note, not a limit |
| four-layer | `process.outline_cutter_diameter` | 0.068 in | four-layer | Outline/profile milling: 0.068” | same | direct |
| four-layer | `process.cutout_cutter_diameter` | 0.040 in | four-layer | Interior/cutout milling: 0.040” | same | direct |
| six-layer | `board_max_height` | 22 in | six-layer | Maximum board size 16in (406.4mm) by 22in | same | direct |
| six-layer | `board_max_width` | 16 in | six-layer | Maximum board size 16in (406.4mm) by 22in | same | direct |
| six-layer | `board_min_edge` | 0.25 in | six-layer | Minimum board size 0.25in | same | direct |
| six-layer | `edge_keepout` | 15 mil | six-layer | Board Edge Keepout 15mil | same | direct |
| six-layer | `mask_web_min` | 4 mil | six-layer | Minimum soldermask web 4 mil | same | direct |
| six-layer | `min_annular_ring` | 4 mil | six-layer | Minimum Annular Ring 4mil | same | direct |
| six-layer | `min_drill` | 8 mil | six-layer | Minimum Drill Size 8mil | same | direct |
| six-layer | `min_slot_size` | 20 mil | six-layer | Minimum Slot Size 20mil | same | direct |
| six-layer | `min_space` | 5 mil | six-layer | Trace Spacing 5mil | same | direct |
| six-layer | `min_trace` | 5 mil | six-layer | Trace Width 5mil | same | direct |
| six-layer | `overlapping_drill_clearance` | 5 mil | six-layer | 5 mil (0.127mm) clearance is recommended | same | direct |
| six-layer | `plated_drill_to_internal_copper` | 10 mil | six-layer | Plated Drill to Internal Layer Copper Clearance 10mil | same | direct |
| six-layer | `silk_line_min_short_text` | 3 mil | six-layer | 3 mil (0.0762mm) (short lines | same | direct |
| six-layer | `silk_line_recommended` | 5 mil | six-layer | Silkscreen minimum line width 5 mil | same | direct |
| six-layer | `service.layers` | 6 | six-layer | Copper Layers 6 | same | direct |
| six-layer | `service.order_multiple` | 3 | six-layer | multiples of three | same | direct |
| six-layer | `service.copper` | 1 oz outer, 1/2 oz inner | six-layer | Copper Weight 1oz outer 1/2oz inner Trace | same | direct |
| six-layer | `service.substrate` | published stackup | six-layer | Substrate 175Tg FR4 ISOLA FR408-HR; Complete construction diagram | same | direct; profile value is a reference to the published stackup; page gives the stackup |
| six-layer | `service.finished_thickness_source` | 63 mil | six-layer | Board Thickness 63mil | same | direct |
| six-layer | `service.finished_thickness_display_mm` | 1.6 | six-layer | Board Thickness 63mil (1.6mm) | same | direct |
| six-layer | `service.via_construction_prohibited` | ['blind', 'buried', 'filled_plated_via_in_pad'] | six-layer | Buried Via No; Blind Via No; Filled+Plated Vias (via-in-pad) No | same | direct |
| six-layer | `process.mask_alignment_max_mil` | 3 | six-layer | Maximum soldermask alignment 3mil | same | direct |
| six-layer | `process.drill_size_tolerance_max_mil` | 2.5 | six-layer | Drill Size tolerance Max: +/- 2.5mil | same | direct |
| six-layer | `process.drill_size_tolerance_typical_mil` | 1.0 | six-layer | Drill Size tolerance Max: +/- 2.5mil (0.0635mm) Typical: +/- ... | same | direct |
| six-layer | `process.drill_position_tolerance_max_mil` | 2 | six-layer | Drill Positional Tolerance Max: 2mil | same | direct |
| six-layer | `process.drill_position_tolerance_typical` | less than 1 mil | six-layer | Drill Positional Tolerance Max: 2mil (0.0508mm) Typical: <1mil | same | direct |
| six-layer | `notes.max_drill` | Maximum Drill Size None; above 250mil larger milling tolerances. Process note, not a limit. | six-layer | Maximum Drill Size None; Drill sizes above 250mil (6.35mm) will be fabbed, but with larger milling tolerances | same | direct; process note, not a limit |
| six-layer | `process.outline_cutter_diameter` | 0.068 in | six-layer | Outline/profile milling: 0.068” | same | direct |
| six-layer | `process.cutout_cutter_diameter` | 0.040 in | six-layer | Interior/cutout milling: 0.040” | same | direct |

## 6. Notes that the profiles do not record

These items are notes only. The profiles do not change for them.

- single-layer turn time: `ship within 10-12 days`. The page says that its turn time is identical to the 2 layer service. The two-layer page gives `ship within 9-12 calendar days`, and `90%` of its orders ship in 10 calendar days.
- two-layer-hhdc turn time: `shipped within 12-21 calendar days of ordering`. The changelog of `2025-AUG-02` documents a stackup change in the page. The change is documentation only.
- four-layer turn time: `ship within 9-14 calendar days of ordering`.
- four-layer stackup note: the changelog of `28-JAN-2026` says `Added notes regarding the temporary alternate stackup used for some 4 layer orders.` The page does name EM528. The name is in two HTML comments directly before the Material Specs table. The comments are not visible text, so `fetch_sources.visible_text` removes them. The first comment gives the window 2026JUN9 to 2026JUN22 for orders in production and shipped. The second comment gives the window 2025-Dec-20 to 2026-Jan-28 for the alternate stackup. The old copy at `b5872c5^` has the same two comments. Thus the EM528 note is not new since 2026-11-14. This item stays a note only. The visible Substrate row still gives `190Tg FR408-HR`. The last changelog date is 2026-01-28.
- six-layer turn time: `ship within 12-21 calendar days of ordering`. The changelog of `15-DEC-2025` says `Adjusted official turn time from 9-14 days to 12-21 days due to order volumes.` The last changelog date is 2025-12-15.
- Copyright (Q3): the line `© Copyright 2023 OSH Park, LLC` is the same on all five pages. The date in `license_state` changed to 2026-11-26.
- Watch dates (Q5): the newest changelog dates of the four-layer and six-layer pages equal the watch dates of `recheck_sources.py`. The script did not change.

## 7. Changed files

The file `docs/reviews/oshpark-source-rebind-files.sha256` lists the 57 files of commit `5c86077`. It also lists this note and `a2-commands.json`. Its format is the `sha256sum` format. The table gives the main files.

| File | SHA-256 |
|---|---|
| `skills/pcb-fab-package/sources.yaml` | `1bd7c4661cd11739385a3a62a3eefc1c199bfadf247d4a2195bd74842f91eb79` |
| `skills/pcb-fab-package/supplier/profiles/oshpark-single-layer.yaml` | `2681fbb9569153eb173115836d1bb591b4337e8b8722c815fa4e1dc12b1a029f` |
| `skills/pcb-fab-package/supplier/profiles/oshpark-two-layer.yaml` | `b083ff9228441d87acb34753cd8da28e41f4677817852e6a20864b57c941d2ec` |
| `skills/pcb-fab-package/supplier/profiles/oshpark-two-layer-hhdc.yaml` | `3dfb72259167ae53e8fb775f1544a040ff2b62f0fd8125932e23d2f486db37db` |
| `skills/pcb-fab-package/supplier/profiles/oshpark-four-layer.yaml` | `8244c3781ed8be0d417d990d2095b33769895e088cde0ee57955a7d684fc740d` |
| `skills/pcb-fab-package/supplier/profiles/oshpark-six-layer.yaml` | `9f0dd2563ea31c1c10e79e5d76a3c5111cc8ea460d14c0d5999e2a7b428c7edb` |
| `tests/eval/fixtures/artifacts/A2/profile/oshpark-two-layer.yaml` | `b083ff9228441d87acb34753cd8da28e41f4677817852e6a20864b57c941d2ec` |
| `tests/eval/fixtures/artifacts/A2/project/manufacturing/supplier.yaml` | `b083ff9228441d87acb34753cd8da28e41f4677817852e6a20864b57c941d2ec` |
| `tests/eval/fixtures/artifacts/A2/project/board.yaml` | `852c0b4b74b6a576deb1daaa363dd8d2fee5b02d1d7cbcd710a2077ccdb39d26` |
| `tests/eval/fixtures/artifacts/A2/status.json` | `8cccfca1f20a712356f9bc8c454fc0a6c29ac70ebc1d86622c57dc33c022cd4f` |
| `tests/eval/fixtures/artifacts/A2/README.md` | `5f63c904e8c147ec37b1b98a1b57ea39c6cc4e2d55a74fcd77f1466054b6004f` |
| 46 changed files under `tests/eval/fixtures/artifacts/A2/project/out/fab/` | listed in the manifest |

## 8. A2 run

The commands ran in the podman image `localhost/cad-skills-pcb:b6`. The image ID is `sha256:b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f`. The KiCad version is `10.0.5`. The record is `docs/reviews/oshpark-source-rebind-evidence/a2-commands.json`.

| Command | Expected exit | Exit |
|---|---|---|
| `fab.py profile` | 0 | 0 |
| `fab.py design` | 0 | 0 |
| `fab.py supplier` | 1 | 1 |

- The file set of `A2/project/out` did not change. It has 72 tracked files. No new file and no ignored file exists.
- The comparison (`a2-compare.txt`) finds 46 changed files. Each difference has a reason. We find no other difference.
- The changes follow from the new hashes. The profile hash `e3f2789d` changed to `5d53abbb`. The page hash `d757495f` changed to `fae87aff`. The hash of `board.yaml` changed to `852c0b4b`. The hash of the manufacturing copy changed to `b083ff92`. The facts hash of the drawing changed from `01c135b8` to `1bb8b294`.
- We check the derived hashes (`a2-verify.txt`). Two of two `binding_sha256` values match the binding file. Two of two `content_sha256` values match `fab.content_hash`. Fifty-nine of fifty-nine file hashes match the file they name.
- Rows 1 and 2 of `supplier-result.json` change only `process_fact.source_sha256`, the page hash. The comparison replaces the profile and page hashes before it compares the rows. There are 18 mandatory rows. 16 rows pass. `service.order_multiple` fails. `silk_line_min_short_text` is pending. `status.json` reports 2 recommendations.
- Ruling: the G04 header and the DRILL header of each Gerber and drill file also hold a timestamp, and these lines changed too. We accept them as timestamps. The plan named only `TF.CreationDate`. Cost if wrong: a reviewer must accept these timestamp lines.
- Expected failure: `test_a2_source_manifest_matches_the_repository_sources`. Four lines differ (Q4): `skills/pcb-fab-package/sources.yaml`, `skills/pcb-fab-package/supplier/profiles/oshpark-two-layer.yaml`, `tests/eval/fixtures/artifacts/A2/project/board.yaml` and `tests/eval/fixtures/artifacts/A2/project/manufacturing/supplier.yaml`. The integrator must accept these four hash lines.

## 9. Tests

| Run | Test files | Result |
|---|---|---|
| Baseline at `b25f478`, pages absent (run 1) | 38 | 38 exit 0 |
| After the rebind at `5c86077`, pages present | 38 | 37 exit 0. One expected failure: `test_artifact_fixtures.py`, 15 of 16 pass. |
| Final, pages present, on the note commit | 38 | 37 exit 0. One expected failure: `test_artifact_fixtures.py`, 15 of 16 pass (Q4). |
| Final, clean clone without pages | 38 | 37 exit 0. The same expected failure, 15 of 16 pass (Q4). |

## 10. Not done

- The write mode of `fetch_sources.py` did not run. The saved bytes are the stored copy, as the lead decided. Write mode writes only a live page that matches the binding.
- Step 12 (the `since` dates of `recheck_sources.py`) did not run. Q5 gives no change.
- The stored pages are in `skills/pcb-fab-package/supplier/pages/`. They are local evidence and are not committed. A later fetch gives other bytes. The `layout` result shows that the visible text is the same.
- Run 1 did not keep its fetch reports, because its scratch data is gone. The run 1 results are in the Run 2 section of the dev report.
