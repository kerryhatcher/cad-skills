# B9/B10 preparation review: Pi

Date: 2026-11-14.

**Decision: the plan and the measured records are sufficient for the assembly interface. The Sierra XY origin and rotation convention, and the in-house service evidence, stay explicit unknowns. The choices and tests below are necessary. No implementation, container test, supplier contact, upload or broad research was done.**

## 1. Source check

| Source | Fact used |
|---|---|
| Plan section 8 | One supplier must do fabrication and assembly in-house. Sierra Turnkey PRO is the first adapter candidate. The package needs the Excel BOM, assembly drawing and XY data. Submit one board image. Sierra arrays the boards. Do not use JLCPCB names for Sierra. |
| Plan section 17 | The Sierra sample BOM has item, per-board quantity, MPN, DNI, references and optional fields. DNI applies to the whole row. The XY sample has designator, footprint, midpoint X/Y, side and rotation. It uses mil and `T`/`B`. It does not define the origin or rotation convention. Do not infer a bottom-side transform from four sample rotations. The FAQ uses inch RS-274X, Excellon absolute, trailing-zero suppression, 2.4 format. Its plane guidance differs from OSH Park. |
| `/tmp/cad-skills-sierra-bom.xls` | Read locally. Exact header strings: `Item #`, `Quantity per board`, `Manufacturer Part #`, `Do Not Install`, `Reference designators`, `Vendor (optional)`, `Vendor Part Number (optional)`, `Value (optional)`, `Size / Footprint  (optional)` (two spaces before the parenthesis), `Part description/ specs (optional, but recommended)`, and `Manfacturer (optional)` (the sample spelling). The row note says DNI applies to the whole row. Split populated and DNI references into different rows. The note, not a guessed label, controls DNI. Keep these exact strings in the format fixture. |
| `/tmp/sierra.html` (Turnkey PRO page) | Service-specific: PCB fabrication in Silicon Valley, in-house assembly, Excel BOM plus assembly drawing and XY data, one board image and supplier arraying, IPC-6012 class 2 and IPC-A-610 class 2, 2 to 100 assembled boards, 10 in by 16 in box and below 150 square inches, 0.062/0.031/0.093 in with +/-10 percent, 4 mil trace/space, ITAR and export-controlled orders excluded. |
| Company-wide claims | The page also shows "ITAR Registered" and a separate "Mil-Spec & Class 3" tier. Do not transfer those to Turnkey PRO. The service page explicitly excludes ITAR and export-controlled orders. |

The Sierra XY sample PDF is not saved. Use the plan's measured facts and keep the origin and rotation unresolved.

## 2. Necessary interface choices

| ID | Choice | Recommended answer |
|---|---|---|
| D1 | Neutral assembly dataset | One supplier-neutral record before any BOM or XY output: reference, per-board quantity, MPN, manufacturer, footprint, value, selected variant, population state (`populate`, `dnp`, `exclude_from_assembly`), side, X, Y, units, origin and rotation. Derive the BOM and the XY file from this one record. |
| D2 | Sierra BOM format | Use the exact Sierra header strings and order, including `Size / Footprint  (optional)` with two spaces, `Part description/ specs (optional, but recommended)`, and `Manfacturer (optional)`. Keep those bytes in the format fixture. The row note controls DNI: the whole row is DNI, split one MPN into a populated row and a DNI row, and use the sample's `DNI` value. `Quantity per board` is the count of references in that row, not the order quantity. Use the supplier's Excel format. Do not rename columns to JLCPCB names. Use one stable comma-separated reference list. Fill the optional fields from the part record only where known. |
| D3 | Sierra XY format | Use designator, footprint, midpoint X, midpoint Y, side and rotation. Do not assume the KiCad footprint origin equals the requested midpoint. Keep the datum interpretation `unconfirmed`, or bind an explicit per-footprint origin-to-midpoint mapping to evidence. Convert the neutral mm values to mil with 0.0254 mm/mil. Use `T`/`B` for side. Do not copy the KiCad `pos` file as the Sierra XY file. Apply a declared adapter transform. |
| D4 | Separate fabrication and assembly exports | The Sierra package has separate fabrication data and assembly data. Use the Sierra FAQ settings for the fabrication files: inch RS-274X, Excellon absolute, trailing-zero suppression, 2.4 format, fabrication drawing, layer identification. Do not reuse the OSH Park positive-plane rule. Record an unresolved plane interpretation as a release condition. The assembly data is the Excel BOM, the assembly drawing and the XY file. Submit one board image. Do not submit an array. |
| D5 | Origin and rotation convention | Add explicit fields for XY origin, axis direction, rotation convention, side convention and units, with a status `confirmed` or `unconfirmed`. The measured sample does not define the origin or rotation. Do not invent a value. A package with an `unconfirmed` convention can be generated with the declared assumption but cannot be qualified. |
| D6 | Rotation corrections | Keep a correction table keyed by footprint and supplier. Never add a universal offset. Test top and bottom components at 0, 90, 180 and 270 degrees. Use asymmetric polarized parts so a mirror or orientation error is visible. |
| D7 | In-house service condition | Record the selected service, the fabrication location, the assembly location, the evidence URL, the retrieval date, the reviewer and the qualification status. Use service-specific evidence. Keep an unresolved location `unconfirmed`. Do not infer an order's process from a company-wide claim. Keep MacroFab and Ninja provisional until the condition is met. |
| D8 | Project restrictions and service exclusions | Record known restrictions and their source in `board.yaml`. Compare them with the service exclusions before selection. Do not infer a legal classification from the circuit. Unknown applicability stays an open project question. |
| D9 | Package manifest and qualification | Record the selected supplier profile hash, the selected variant, the BOM, XY, assembly drawing, fabrication files, source and output hashes, the origin/rotation status and the in-house evidence. A profile hash change repeats qualification. Preserve old reports with their original hash. |
| D10 | Stock age policy | The project or supplier profile sets the maximum stock age or the stale policy. Do not invent a universal interval. A missing policy keeps the stock date as a dated observation, not a stale failure. |

## 3. Concrete tests

| Test | Expected result |
|---|---|
| BOM columns and order | Header equals the Sierra sample, including `Size / Footprint  (optional)`, `Part description/ specs (optional, but recommended)` and `Manfacturer (optional)`. A JLCPCB-style header fails. |
| BOM DNI split | The row note controls DNI. One MPN with populated and DNP references gives two rows. The DNP row has the sample's `DNI` value in `Do Not Install`. The populated row is blank. A guessed `DNP` label fails. |
| BOM quantity | `Quantity per board` equals the number of references in that row. The order quantity is not used. |
| BOM optional fields | A known manufacturer, value and footprint appear in the optional columns. An unknown field stays blank. No invented value. |
| BOM Excel | The output opens as an Excel workbook with the expected sheet, columns and rows. A renamed CSV is not the supplier's exact format unless the supplier accepts it. |
| BOM variant/DNP | A `dnp` part is in the DNI row. A `populate` part is in a normal row. An `exclude_from_assembly` part is absent. A variant change updates all rows. |
| XY columns | designator, footprint, midpoint X, midpoint Y, side, rotation. |
| XY units | 1 mm converts to 39.3701 mil with the exact 0.0254 factor. No cumulative rounding drift. |
| XY side | A top part uses `T`, a bottom part uses `B`. A swapped side fails. |
| XY datum and midpoint | The datum is `unconfirmed` or an explicit per-footprint origin-to-midpoint mapping. A fixture with an offset board origin and a footprint whose origin is not the component midpoint applies the declared mapping. An assumed equality fails. |
| XY 0/90/180/270 | Top and bottom parts at all four angles place correctly. An asymmetric polarized LED or diode exposes a mirror or orientation error. |
| XY rotation correction | A correction for one footprint and supplier is applied. An uncorrected part fails. A universal offset is rejected. |
| XY origin/rotation | An `unconfirmed` convention gives a package status `unconfirmed` and no qualification. A confirmed service-specific convention can qualify. Changing the declared convention changes the XY hash. |
| BOM and XY agreement | Both use the same references and the selected variant. A DNP or excluded part is absent from the XY file. A missing reference fails. |
| Separate fabrication and assembly | The Sierra Gerber is inch RS-274X. The Excellon header is 2.4, absolute and trailing-zero suppressed. The BOM and XY are the Sierra formats. Reject only an unsupported or ambiguous Sierra convention. A common `.gbr` or `.gtl` filename is not OSH Park-specific and is not rejected merely because OSH Park also uses it. No OSH Park-specific rule or JLCPCB column enters the Sierra package without Sierra evidence. |
| One board image | The package has one board image, not an array. An arrayed design fails. The assembly drawing notes that Sierra arrays the boards. |
| Plane interpretation | A positive internal plane is tested only if the selected Sierra service accepts it. An unresolved plane interpretation is a release condition, not a silent pass. |
| In-house evidence | A service-specific fabrication and assembly location with the URL, date and reviewer passes. A company-wide claim alone fails or stays `unconfirmed`. An unresolved location stays `unconfirmed`. |
| ITAR/export exclusion | A board with a known ITAR or export-control restriction is blocked for Turnkey PRO. The company's "ITAR Registered" mark does not override the service exclusion. An unknown applicability stays open. |
| Profile hash change | A changed supplier profile hash repeats qualification. The old package keeps its original hash and reports. |
| Stock age policy | The explicit project or supplier policy sets the maximum stock age. A date inside the policy passes. A date outside it is flagged. With no policy, the date stays a dated observation, not a stale failure. A universal 90-day or similar interval is rejected. |
| Upload preview (later, only after authorization) | Compare layer order, dimensions, component locations, side and polarity. The preview does not replace electrical tests. |
| Physical trial (later) | Continuity, power, current and interface measurements against recorded limits. Not a paper check. |

## 4. Traps and limits

- Do not use the company-wide "ITAR Registered" mark as a Turnkey PRO capability. The service excludes ITAR and export-controlled orders.
- Do not use the "Mil-Spec & Class 3" tier data for Turnkey PRO. The service is IPC-6012 class 2 and IPC-A-610 class 2.
- Do not use JLCPCB column names or centroid fields for Sierra.
- Do not correct the sample header spelling `Manfacturer` without supplier confirmation.
- Do not infer the XY origin or rotation convention from the four sample rotations.
- Do not assume the KiCad footprint origin is the Sierra midpoint. Keep the datum unconfirmed or bind an explicit per-footprint mapping.
- Do not invent a bottom-side transform to close the unknown.
- Do not copy the KiCad `pos` file as the Sierra XY file.
- Do not add a universal rotation offset.
- Do not divide the order between OSH Park and an assembler.
- Do not reuse the OSH Park positive-plane rule for Sierra without service evidence.
- Do not reject a common Gerber extension merely because OSH Park also uses it. Reject only an unsupported or ambiguous Sierra convention.
- Do not invent a universal stock-age interval. Use the explicit project or supplier policy.
- Do not treat an upload preview as an electrical test.
- Do not treat a company-wide campus or certification claim as service-specific evidence.
- Do not make ODB++ or IPC-2581 a prerequisite. Use either only after the exporter and supplier acceptance tests pass.

The measured BOM and page facts are local evidence. The XY sample PDF is not saved, so the origin and rotation remain unconfirmed. This review makes no implementation change, contacts no supplier and starts no upload.

## 5. Sierra source addendum decision

Date: 2026-11-14.

I read `docs/reviews/b9-source-addendum-root.md` (`5b5e433ad48435e11c558fee73847d2331c7ab16697bc00b1dce9f21de3a9a10`) and the two retained samples in `docs/reviews/sierra-source-evidence/`. I confirm the service and sample distinction and the unresolved placement conventions. I accept the addendum decisions 1 to 10. Three small points are added.

**Service and sample.** The two retained samples are the placement sample PDF (`xy.pdf`, `eea02acc5362804e...`, mil, `T`/`B`, columns designator, footprint, mid X, mid Y, rotation) and the XYRS workbook (`xyrs.xlsx`, `8b3d93beec8ea968...`, columns designator, X coordinate, Y coordinate, layer, rotation, with `Top`/`Bottom`). They are samples, not service specifications. The inch, absolute, trailing-zero and 2.4 drill facts belong to the Web PCB FAQ, not Turnkey PRO. Correct my section 2 D4: the Turnkey PRO fabrication settings must come from Turnkey PRO service evidence, not from the Web PCB FAQ. Do not combine the two samples' columns or side tokens into one claim.

**Unresolved conventions.** The PDF names the midpoint and uses mil. It states no origin, no axis direction, no side view, no rotation direction and no zero orientation. It contains one rotation of `360`, outside the usual `[0, 360)` range. The workbook states no units, no origin and no bottom-side rotation convention. Its example repeats `RP1` in three rows, and its two populated sheets disagree (`R10` rotation 90 and 180). Thus the workbook examples cannot be expected placement results. Keep units, datum, axes, side view, rotation direction and zero orientation explicit and `unconfirmed` until service-specific evidence resolves them, and bind a confirmed convention to the affected footprint mappings.

**First adapter.** The first adapter keeps the PDF format as its named candidate. The workbook does not force a second adapter. The format fixture preserves the selected sample's columns. The `360` value needs a normalization rule or an explicit refusal. The repeated `RP1` confirms the duplicate-reference rejection.

The earlier statement that the XY sample PDF is not saved is superseded: the PDF is now retained with its hash, and the workbook and both `.headers` files are retained. No product edit or test was done.

## 6. Turnkey PRO fabrication-setting clarification

Date: 2026-11-14.

I read the updated `docs/reviews/b9-source-addendum-root.md` (`28b3062bf1022acc8eb6572ffeef87e1f8a17bceaa9fb0d5a81755de0b982bec`) and the retained `docs/reviews/sierra-source-evidence/turnkey-faq.html` (`680bd9c7d8e647ad8ebae532ce1ec5e2ddc0fc6009187809f796abe2450dbd99`).

One sentence in my section 5 is wrong. The inch RS-274X, absolute inch drill, trailing-zero and 2.4 settings do not belong only to Web PCB. The Turnkey PRO FAQ states them directly under its order-file question:

- "Gerber files using English units in 274X format or ODB++ format."
- "Units = Inch", "Tool units = Inch", "Coordinate = Absolute", "Zeros omitted = Trailing", "Number format = 2.4".
- "Fabrication drawing in Gerber format."

Thus these settings have direct Turnkey PRO evidence. Section 2 D4 is correct to use the Turnkey PRO FAQ for the Turnkey PRO adapter. The Web PCB FAQ lists the same settings, but it is not the only source. Supersede the section 5 sentence that says the facts belong only to Web PCB.

Two further points:

- The Turnkey PRO FAQ requests a fabrication drawing in Gerber format. Keep that requested Gerber drawing distinct from the local PDF documentation (the B7 fabrication drawing content requirement). State which artifact the adapter sends to the supplier.
- The FAQ keeps legacy negative-plane guidance. Its interpretation for the current exporter stays unresolved and `unconfirmed`, and the plane interpretation stays a release condition.

The placement conventions remain unresolved. The XY PDF and the XYRS workbook still lack units (the workbook), the origin, the axes, the side view, the rotation direction and the zero orientation. Keep them `unconfirmed`. The first adapter keeps the PDF format as the named candidate; the Turnkey PRO FAQ links the PDF. The workbook is Web PCB evidence. No product edit and no broad research was done.
