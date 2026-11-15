# /// script
# requires-python = ">=3.10"
# dependencies = ["openpyxl==3.1.5"]
# ///
"""Sierra Turnkey PRO output rules for pcba-design. Pure functions, no file I/O.

The inputs are the neutral data of the package and the supplier policy. The outputs are
draft files and a status record. Every convention that the supplier has not confirmed is
stated as `unconfirmed`. A draft never claims a qualified result.
"""

from __future__ import annotations

import csv
import datetime as dt
import io
import json

import openpyxl

# The header strings are copied from the retained sample BOM. Keep them unchanged.
SAMPLE_INTRO = ("This is a sample BOM for  Sierra Circuits' online BOM pricing system. "
                "Please use this preferred format for your BOM that you upload.")
SAMPLE_NOTE = ("Note: DNI applies to whole row. If only some specific locations of a given ITEM are not to be "
               "installed, please create two rows for that item and mark one as DNI.")
SAMPLE_HEADERS = ["Item #", "Quantity per board", "Manufacturer Part #", "Do Not Install",
                  "Reference designators", "Vendor (optional)", "Vendor Part Number (optional)",
                  "Value (optional)", "Size / Footprint  (optional)",
                  "Part description/ specs (optional, but recommended)", "Manfacturer (optional)"]
HEADER_ROW = 7  # the header is the seventh Excel row, as in the sample
DNI_TEXT = "DNI"  # the sample uses this value in the Do Not Install column
XY_HEADERS = ["Designator", "Footprint", "Mid X", "Mid Y", "Side", "Rotation"]
MM_PER_MIL = 0.0254
FIXED_TIME = dt.datetime(2026, 11, 15, 0, 0, 0)  # a constant: the tool never reads the clock
UNCONFIRMED = "unconfirmed"


def bom_table(neutral: dict, board_name: str, revision: str, policy: str) -> list[list]:
    """Return the BOM rows. `policy` is `include_in_bom` or `exclude_from_bom`."""
    rows_by_ref = {row["reference"]: row for row in neutral["rows"]}
    table = [[SAMPLE_INTRO], [SAMPLE_NOTE], [f"BOM: {board_name}"], [f"Assembly Part Number/Revision: {revision}"],
             ["Customer / Company Name: "], [], SAMPLE_HEADERS]
    item = 0
    for group in neutral["bom_groups"]:
        if group["installation_method"] == "hand_installed" and policy == "exclude_from_bom":
            continue
        refs = group["references"]
        values = {rows_by_ref[ref]["value"] for ref in refs}
        footprints = {rows_by_ref[ref]["footprint"] for ref in refs}
        item += 1
        table.append([
            item,
            group["quantity_per_board"],
            group["mpn"],
            DNI_TEXT if group["variant_state"] == "dnp" else "",
            ",".join(refs),
            "",
            "",
            values.pop() if len(values) == 1 else "",
            footprints.pop() if len(footprints) == 1 else "",
            "",
            group["manufacturer"],
        ])
    return table


def xlsx_bytes(table: list[list]) -> bytes:
    """Write the BOM table as one worksheet, with fixed document properties."""
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Sierra Sample BOM"
    for row_index, row in enumerate(table, start=1):
        for col_index, value in enumerate(row, start=1):
            if value != "":
                ws.cell(row=row_index, column=col_index, value=value)
    wb.properties.creator = "pcba-design"
    wb.properties.created = FIXED_TIME
    wb.properties.modified = FIXED_TIME
    buffer = io.BytesIO()
    wb.save(buffer)
    return buffer.getvalue()


def xy_csv_bytes(neutral: dict) -> bytes:
    """Write the placement draft for automatic populated rows. Units are mil, by the sample statement."""
    out = io.StringIO()
    writer = csv.writer(out, lineterminator="\n")
    writer.writerow(XY_HEADERS)
    for row in neutral["rows"]:
        if row["variant_state"] != "populate" or row["installation_method"] != "automatic":
            continue
        writer.writerow([
            row["reference"],
            row["footprint"],
            f"{row['x_mm'] / MM_PER_MIL:.4f}",
            f"{row['y_mm'] / MM_PER_MIL:.4f}",
            "T" if row["side"] == "top" else "B",
            f"{row['rotation_deg']:.6f}",
        ])
    return out.getvalue().encode("utf-8")


def test_record_bytes(neutral: dict, limits: dict) -> bytes:
    """List every board limit and hand-install step as `not measured`. No physical pass is recorded."""
    items = []
    for name in sorted(limits):
        limit = limits[name]
        items.append({"id": f"limit.{name}", "kind": "limit", "quantity": name,
                      "expected": {"value": limit["value"], "unit": limit["unit"]},
                      "status": "not measured",
                      "steps": [f"Measure {name} at the board under the stated load."]})
    for row in neutral["rows"]:
        if row["installation_method"] == "hand_installed":
            items.append({"id": f"hand-install.{row['reference']}", "kind": "hand_install",
                          "reference": row["reference"], "instruction": row["assembly_instruction"],
                          "status": "not measured"})
    record = {"schema": "pcba-design/test-record", "schema_version": "1.0",
              "variant": neutral["variant"], "physical_test_passed": False, "items": items}
    return (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")


def status_bytes(profile_sha: str, policy: str | None, bom_produced: bool, supplier_id: str) -> bytes:
    """State every convention as unconfirmed, and the qualification as unqualified."""
    record = {
        "schema": "pcba-design/sierra-status", "schema_version": "1.0",
        "profile_sha256": profile_sha,
        "service": {"id": supplier_id, "service": "turnkey_pro",
                    "fabrication_location": UNCONFIRMED, "assembly_location": UNCONFIRMED},
        "export_applicability": UNCONFIRMED,
        "hand_installed_bom": policy if policy is not None else "missing",
        "conventions": {
            "xy_units": "stated_by_sample",
            "xy_origin": UNCONFIRMED,
            "xy_axes": UNCONFIRMED,
            "xy_side_view": UNCONFIRMED,
            "xy_rotation_direction": UNCONFIRMED,
            "xy_zero_orientation": UNCONFIRMED,
            "midpoint_mapping": UNCONFIRMED,
            "plane_interpretation": UNCONFIRMED,
        },
        "artifacts": {"bom": "produced" if bom_produced else "not_produced", "placement": "draft"},
        "qualification": "unqualified",
    }
    return (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")
