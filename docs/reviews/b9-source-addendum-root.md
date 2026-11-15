# B9 source addendum

Date: 2026-11-14 UTC.

The lead added `XYRS` to the technical glossary for the supplier's placement-file term.
This is a later documentation change. Earlier manifest hashes remain historical records.

This record adds source evidence to the two B9/B10 preparation reports. It does not authorize an order or qualify a package.

## 1. Retained placement samples

The [earlier XY sample](https://media.protoexpress.com/format-for-X-Y-data.pdf) is now in `sierra-source-evidence/xy.pdf`.
Its SHA-256 is `eea02acc5362804e76e7586e62b7d8182284d9d35cc9e853103d8d76cc992590`.
The sample uses mil values and `T` or `B` for the side. It names the component midpoint.
It does not state an origin or a complete rotation convention.

The [Web PCB FAQ](https://www.protoexpress.com/faq/web-order-pcbs/) links a different [XYRS workbook](https://www.protoexpress.com/wp-content/uploads/2022/01/Sierra-XYRS-Template.xlsx).
The retained file is `sierra-source-evidence/xyrs.xlsx`.
Its SHA-256 is `8b3d93beec8ea96851a62e98f8d26e29f9cb85d0874304e9ab373d1d11c0ed93`.
The corresponding `.headers` files retain the HTTP responses.

The workbook uses five columns: designator, X, Y, layer, and rotation. Its side values are `Top` and `Bottom`.
The cell text does not state the units, coordinate origin, or bottom-side rotation convention.
Its example repeats one reference in three rows. The examples on its two populated sheets also disagree.
Thus, the example rows cannot serve as expected placement results.

I read the PDF with `pdftotext -layout`. I read the workbook XML with Python through `uv`.
The workbook contains no comment or drawing part that supplies the absent conventions.
These measurements supersede the earlier statement that the XY PDF was not retained.

## 2. Scope of the source claims

The Web PCB FAQ lists fabrication data in inch units, absolute drill coordinates, trailing-zero suppression, and 2.4 drill format.
It also distinguishes BOM submission during a quote from files in the later order archive.
These statements occur in the Web PCB instructions. Do not silently transfer a service-specific rule to Turnkey PRO.
The local release package can retain the BOM even if a later submission procedure places it elsewhere.
No submission procedure runs in this feature. [Source](https://www.protoexpress.com/faq/web-order-pcbs/)

A further read found the same fabrication settings in the Turnkey PRO FAQ, under its order-file question.
Thus, these settings also have direct Turnkey PRO evidence. The earlier preparation report's citation was correct.
This page links the earlier XY PDF, not the Web PCB workbook. It specifies a fabrication drawing in Gerber format.
Keep the requested Gerber drawing and the local PDF documentation distinct.
The page also gives legacy negative-plane guidance. Its interpretation remains unresolved for the current exporter.
The retained page is `sierra-source-evidence/turnkey-faq.html`.
[Source](https://www.protoexpress.com/faq/turnkey-pro-pcbs/)

Sierra's assembly article describes KiCad position-file export and gives choices for units and layer separation.
It does not define one supplier rotation transform or establish equality between a footprint origin and a body midpoint.
Treat it as workflow guidance, not a measured acceptance of all KiCad output conventions.
[Source](https://www.protoexpress.com/blog/how-to-generate-pcb-assembly-files/)

The general assembly FAQ lists an Excel workbook among the assembly inputs.
It does not resolve the placement transform.
[Source](https://www.protoexpress.com/faq/pcb-assembly/)

## 3. Decisions for the implementation proposal

1. Name the selected sample and service in the adapter record.
2. Retain both samples as source evidence. Do not combine their column names or side values into a new supplier claim.
3. Preserve the selected sample's columns in its format fixture.
4. Keep units, datum, axes, side view, rotation direction, and zero orientation explicit in the placement record.
5. Keep unresolved supplier conventions unconfirmed. A generated draft does not resolve them.
6. Bind a confirmed convention to service-specific evidence and the affected footprint mappings.
7. Test geometry against independent asymmetric fixtures. Do not derive expected coordinates from the adapter under test.
8. Reject duplicate placement references, including duplicates copied from supplier examples.
9. Use only `draft`, `unqualified`, or `qualified` for the existing manifest status.
10. Use `unconfirmed` for a condition or finding, not a new manifest status.

The first adapter can keep the earlier PDF format as its named candidate. The second sample does not force another adapter.
Supplier evidence must resolve the selected format and conventions before qualification.
This is a release condition. It does not prevent implementation and tests of the neutral assembly data.
