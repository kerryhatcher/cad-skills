"""Assembly checks for the pcba-design package. Each function returns one result dict.

The checks take the neutral data, the packaged bytes and the variants. They never read the project.
"""

from __future__ import annotations

import io
import json

from checks_design import _result

TOOL = {"name": "pcba-design", "version": "1.0"}


def bom_consistent(bom_bytes, groups: list, policy: str) -> dict:
    """asm.bom_consistent: the packaged BOM lists each neutral group with the same references and quantity."""
    if bom_bytes is None:
        return _result("asm.bom_consistent", "pending", "tool", TOOL, None,
                       [{"code": "asm.bom_absent", "text": "No BOM is packaged."}], "not run")
    import openpyxl
    ws = openpyxl.load_workbook(io.BytesIO(bom_bytes)).active
    rows = [r for r in ws.iter_rows(values_only=True) if r and isinstance(r[0], (int, float))]
    packaged = sorted((str(r[10]), str(r[2]), str(r[4]), int(r[1]), "DNI" if r[3] == "DNI" else "") for r in rows)
    expected = sorted((g["manufacturer"], g["mpn"], ",".join(g["references"]), g["quantity_per_board"],
                       "DNI" if g["variant_state"] == "dnp" else "") for g in groups
                      if not (policy == "exclude_from_bom" and g["installation_method"] == "hand_installed"))
    ok = packaged == expected
    reasons = [] if ok else [{"code": "asm.bom_mismatch", "text": "The packaged BOM differs from the neutral groups."}]
    return _result("asm.bom_consistent", "pass" if ok else "fail", "tool", TOOL,
                   {"path": "bom/sierra-bom.xlsx", "bytes": bom_bytes}, reasons, f"rows={len(packaged)}")


def placement_rotation(rows: list, footprints: dict, neutral_bytes: bytes) -> dict:
    """asm.placement_rotation: each neutral row equals the board footprint values, rotation normalized."""
    problems = []
    for row in rows:
        fp = footprints.get(row["reference"])
        if fp is None or (row["x_mm"], row["y_mm"], row["source_rotation_deg"]) != (
                fp["x_mm"], fp["y_mm"], fp["source_rotation_deg"]):
            problems.append(row["reference"])
    reasons = [{"code": "asm.placement_mismatch", "text": f"Placement differs for {ref}."} for ref in problems]
    return _result("asm.placement_rotation", "fail" if problems else "pass", "tool", TOOL,
                   {"path": "reports/assembly-neutral.json", "bytes": neutral_bytes}, reasons,
                   f"rows={len(rows)} differing={len(problems)}")


def variant_agreement(rows: list, variant_states: dict, neutral_bytes: bytes) -> dict:
    """asm.variant_agreement: each neutral row carries the population state of the selected variant."""
    problems = [r["reference"] for r in rows if variant_states.get(r["reference"]) != r["variant_state"]]
    reasons = [{"code": "asm.variant_mismatch", "text": f"Population differs for {ref}."} for ref in problems]
    return _result("asm.variant_agreement", "fail" if problems else "pass", "tool", TOOL,
                   {"path": "reports/assembly-neutral.json", "bytes": neutral_bytes}, reasons,
                   f"rows={len(rows)} differing={len(problems)}")


def stock_dated(stock: list, neutral_bytes: bytes) -> dict:
    """asm.stock_dated: pass when every populated part passes. Any fail gives fail. Otherwise an unknown gives unconfirmed."""
    statuses = {s["status"] for s in stock}
    if "fail" in statuses:
        status = "fail"
    elif "unconfirmed" in statuses:
        status = "unconfirmed"
    else:
        status = "pass"
    reasons = [{"code": "asm.stock_" + s["status"], "text": f"{s['mpn']} is {s['status']}: {', '.join(s['reasons']) or 'ok'}."}
               for s in stock if s["status"] != "pass"]
    return _result("asm.stock_dated", status, "tool", TOOL,
                   {"path": "reports/assembly-neutral.json", "bytes": neutral_bytes}, reasons,
                   f"parts={len(stock)}")


def test_record(record_bytes: bytes, limits: dict, hand_items: list, variant: str) -> dict:
    """asm.test_record: compare the record steps with the captured board limits and hand-install list.

    The expected steps are these items:
    - one `limit.<name>` item for each board limit,
    - one `hand-install.<ref>` item for each hand-installed reference of the selected variant.
    An empty step list fails.
    Each step must have status `not measured`, and the record must not claim a physical pass.
    """
    record = json.loads(record_bytes.decode("utf-8"))
    raw_items = record.get("items", [])
    ids = [item.get("id") for item in raw_items]
    if len(set(ids)) != len(ids):
        return _result("asm.test_record", "fail", "tool", TOOL,
                       {"path": "test/test-record.json", "bytes": record_bytes},
                       [{"code": "asm.test_step_duplicate", "text": "The test record repeats a step ID."}],
                       f"items={len(raw_items)}")
    items = {item.get("id"): item for item in raw_items}
    expected = {f"limit.{name}": limit for name, limit in limits.items()}
    expected.update({f"hand-install.{item['reference']}": item for item in hand_items})
    reasons = []
    if record.get("variant") != variant:
        reasons.append({"code": "asm.test_variant_mismatch", "text": "The test record names a different variant."})
    if not expected:
        reasons.append({"code": "asm.test_steps_absent", "text": "The board and the variant define no test step."})
    if not items:
        reasons.append({"code": "asm.test_items_empty", "text": "The test record has no item."})
    for key in sorted(set(expected) - set(items)):
        reasons.append({"code": "asm.test_step_missing", "text": f"The test record has no step {key}."})
    for key in sorted(set(items) - set(expected)):
        reasons.append({"code": "asm.test_step_extra", "text": f"The test record has the extra step {key}."})
    for key in sorted(set(items) & set(expected)):
        item = items[key]
        if item.get("status") != "not measured":
            reasons.append({"code": "asm.test_claims_result", "text": f"Step {key} claims a result."})
        if key.startswith("limit."):
            limit = expected[key]
            if item.get("expected") != {"value": limit["value"], "unit": limit["unit"]}:
                reasons.append({"code": "asm.test_limit_mismatch", "text": f"Step {key} differs from the board limit."})
        else:
            hand = expected[key]
            if item.get("reference") != hand["reference"] or item.get("instruction") != hand["reason"]:
                reasons.append({"code": "asm.test_instruction_mismatch", "text": f"Step {key} differs from the hand-install instruction."})
    if record.get("physical_test_passed") is not False:
        reasons.append({"code": "asm.test_claims_pass", "text": "The record claims a physical pass."})
    status = "fail" if reasons else "pass"
    return _result("asm.test_record", status, "tool", TOOL,
                   {"path": "test/test-record.json", "bytes": record_bytes}, reasons,
                   f"steps={len(expected)} items={len(items)}")
