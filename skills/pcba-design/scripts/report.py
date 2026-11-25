"""Evidence and manifest records for the pcba-design package.

The records are dicts. The caller validates each one with the copied validator before publication.
"""

from __future__ import annotations

import hashlib

# The input roles each check reads. Taken from the accepted interface, section 14.
CHECK_INPUT_ROLES = {
    "design.drc": ("board",),
    "design.erc": ("schematic",),
    "design.parity": ("schematic", "board"),
    "fab.profile_evidence": ("supplier_profile",),
    "fab.export_inventory": ("board", "export_settings"),
    "fab.layer_order": ("board", "export_settings"),
    "fab.drill_split": ("board", "board_interface", "export_settings"),
    "fab.supplier_rules": ("board", "supplier_profile", "export_settings", "supplier_rules", "supplier_settings", "toolchain"),
    "asm.bom_consistent": ("parts", "variants", "board_record", "supplier_profile"),
    "asm.placement_rotation": ("board", "parts", "variants"),
    "asm.variant_agreement": ("board_record", "variants", "parts"),
    "asm.stock_dated": ("parts", "board_record"),
    "asm.test_record": ("board", "parts", "variants", "board_record"),
}


def sha256(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def evidence_record(result: dict, inputs: list, as_of: str) -> dict:
    """Build the evidence record of one check. Inputs are the manifest inputs with the check's roles."""
    roles = CHECK_INPUT_ROLES[result["id"]]
    bound = [{"path": i["path"], "sha256": i["sha256"]} for i in inputs if i["role"] in roles]
    record = {"schema_id": "cad-skills/evidence", "schema_version": "1.0", "check_id": result["id"],
              "status": result["status"], "method": result["method"], "observed_on": as_of,
              "notes": result["observed"]}
    if result["tool"] is not None:
        record["tool"] = result["tool"]
    if bound:
        record["inputs"] = bound
    if result["artifact"] is not None:
        record["artifact"] = {"path": result["artifact"]["path"], "sha256": sha256(result["artifact"]["bytes"])}
    return record


def manifest_record(package_id: str, board: dict, board_sha: str, variant: str, profile_sha: str,
                    inputs: list, outputs: list, checks: list, reasons: list, tool_versions: dict) -> dict:
    """Build the manifest. The status is unqualified whenever a check is not pass, or a convention is open."""
    return {
        "schema_id": "cad-skills/manifest", "schema_version": "1.0",
        "release_id": package_id, "kind": "pcba",
        "board_revision": board["release_revision"], "board_sha256": board_sha, "variant": variant,
        "supplier": {"id": board["supplier"]["id"], "service": board["supplier"]["service"],
                     "profile_sha256": profile_sha},
        "inputs": inputs, "outputs": outputs,
        "applicability": {"smd_parts": True, "firmware": False, "stencil": False, "panel": False},
        "drill_applicability": [],
        "checks": checks,
        "status": "unqualified",
        "reasons": reasons,
        "tool_versions": tool_versions,
    }
