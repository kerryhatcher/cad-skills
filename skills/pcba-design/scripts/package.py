"""Build the pcba-design package: captured inputs, locked KiCad runs, checks, manifest, validation and publication.

The module receives the loaded pcba.py module. It uses that module's capture, neutral build, Sierra
helpers and refusal types. The caller holds the project lock for the whole run.

Order of the run:
1. Capture every input once, and hash the captured bytes.
2. Resolve the locked image identity and refuse a different image or KiCad version.
3. Run the KiCad steps on private copies of the captured bytes.
4. Run the checks on captured bytes and tool output only.
5. Stage every output, write the manifest and the evidence files, and verify the staged bytes.
6. Run the copied validator on the project and on the staged package.
7. Repeat the input freshness check, then publish the staged directory.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
from pathlib import Path

import checks_asm
import checks_design
import checks_fab
import drawing
import export
import report

PACKAGE_ID = re.compile(r"^[a-z0-9][a-z0-9._-]*$")
STAGING = "out/pcba/.package-staging"
# The fixed project paths of the accepted layout. They match FIXED_INPUT_PATHS in the copied validator.
FIXED = {
    "board_record": "board.yaml", "board": "kicad/board.kicad_pcb", "schematic": "kicad/board.kicad_sch",
    "variants": "variants.yaml", "supplier_profile": "manufacturing/supplier.yaml",
    "export_settings": "manufacturing/export.yaml", "toolchain": "toolchain.lock.json",
    "board_interface": "mechanical/board-interface.json",
}
SUPPLIER_RULES = "manufacturing/supplier-rules.yaml"
SUPPLIER_SETTINGS = "manufacturing/supplier-settings.yaml"
EVIDENCE = "manufacturing/evidence/turnkey-pro-service.txt"
WAIVERS = "manufacturing/waivers.yaml"
MANIFEST_ROLES = ("board_record", "board", "schematic", "variants", "supplier_profile", "export_settings",
                  "toolchain", "board_interface", "parts", "supplier_rules", "supplier_settings")
LAYER_ROLE = {"copper_top": "copper", "copper_bottom": "copper", "copper_inner": "copper",
              "mask_top": "mask", "mask_bottom": "mask", "silk_top": "silk", "silk_bottom": "silk",
              "paste_top": "paste", "paste_bottom": "paste", "outline": "outline"}
RULES_SCHEMA = "pcba-design/supplier-rules"
SETTINGS_SCHEMA = "pcba-design/supplier-settings"


def _tool_versions(version: str) -> dict:
    return {"kicad-cli": version, "pcba-design": "1.0"}


def _json_bytes(data) -> bytes:
    return (json.dumps(data, indent=2, sort_keys=True) + "\n").encode("utf-8")


def _verify_staged(staging: Path, expected: dict, refuse) -> None:
    """Final byte gate before the publication: refuse links, extra files, missing files and changed bytes."""
    seen = {}
    for path in staging.rglob("*"):
        rel = path.relative_to(staging).as_posix()
        if path.is_symlink():
            raise refuse("package.link", rel, "A link is in the staged package.")
        if path.is_file():
            if os.stat(path).st_nlink > 1:
                raise refuse("package.link", rel, "A staged file has more than one hard link.")
            raw = path.read_bytes()
            seen[rel] = (report.sha256(raw), len(raw))
    for rel in sorted(set(seen) - set(expected)):
        raise refuse("package.extra_file", rel, "A staged file is not in the validated set.")
    for rel in sorted(set(expected) - set(seen)):
        raise refuse("package.missing_file", rel, "A validated file is missing from the staged package.")
    if len(seen) != len(expected):
        raise refuse("package.count_mismatch", "", "The staged file count differs from the validated set.")
    for rel in sorted(expected):
        if seen[rel] != expected[rel]:
            raise refuse("package.hash_mismatch", rel, "A staged file differs from the validated bytes.")


def _capture(pcba, snap, rel: str, role: str):
    """Capture a mandatory input. A missing file refuses the package, so no package can fail its own evidence."""
    try:
        return snap.capture(rel, role)
    except pcba.Refused as err:
        if err.finding["code"] == "path.missing":
            raise pcba.Refused("package.input_missing", rel, f"The required record {rel} is missing.")
        raise


def _capture_optional(pcba, snap, rel: str, role: str):
    """Capture an optional input. Return None when the file is absent. An escape still refuses."""
    try:
        return snap.capture(rel, role)
    except pcba.Refused as err:
        if err.finding["code"] == "path.missing":
            return None
        raise


def _plain_record(pcba, raw: bytes, rel: str, schema_id: str) -> dict:
    """Parse a skill-owned YAML record. The copied validator has no schema for it, so the skill checks the ID."""
    try:
        record = pcba.validate.parse_record(raw, ".yaml", rel)
    except pcba.validate.RecordError as err:
        raise pcba.Refused(err.findings[0]["code"], rel, err.findings[0]["message"])
    if not isinstance(record, dict) or record.get("schema_id") != schema_id:
        raise pcba.Refused("package.record_kind", rel, f"The record must have the schema ID {schema_id}.")
    return record


def _expected_names(export_record: dict) -> dict:
    """Return {file name: role} that the export settings expect in the Gerber and drill directories."""
    stem = "board"
    extension = export_record["extensions"]["pcba"]
    expected = {}
    for layer in export_record["layers"]:
        name = f"{stem}-{layer['kicad_layer'].replace('.', '_')}{layer['suffix']}"
        expected[name] = layer["role"]
    fab = extension["fabrication_drawing"]
    expected[f"{stem}-{fab['kicad_layer'].replace('.', '_')}{fab['suffix']}"] = "fabrication"
    expected[extension["job_file"]] = "job"
    drill = export_record["drill"]
    expected[f"{stem}{drill['plated_suffix']}"] = "drill_plated"
    expected[f"{stem}{drill['nonplated_suffix']}"] = "drill_nonplated"
    return expected


def build_package(pcba, project: Path, board_rel: str, variant: str, as_of: dt.date, package_id: str,
                  _hooks: dict | None = None) -> dict:
    """Write one complete package, or nothing. The caller holds the project lock.

    `_hooks` is for the tests only. The key `after_stage` runs one function after the staged writes.
    The key `after_validate` runs one function after the validator. The tests use them to change
    a file at a fixed point.
    """
    hooks = _hooks or {}
    proj = project.resolve()
    if not PACKAGE_ID.match(package_id):
        raise pcba.Refused("package.id_invalid", package_id, "The package id must match the release id pattern.")
    if board_rel != FIXED["board"]:
        raise pcba.Refused("package.board_path", board_rel, f"The board of a package must be {FIXED['board']}.")
    rel_dest = f"out/pcba/packages/{package_id}"
    try:
        dest = pcba.project_io.confine(proj, rel_dest)
    except (pcba.project_io.PathEscape, OSError):
        raise pcba.Refused("output.path_invalid", rel_dest, "The package path is not inside the project.")
    if os.path.lexists(dest):
        raise pcba.Refused("package.exists", rel_dest, "A package with this id exists. Choose a new id.")
    staging = proj / STAGING
    if os.path.islink(staging):
        raise pcba.Refused("output.staging_link", STAGING, "The staging path is a symbolic link.")
    if staging.exists():
        raise pcba.Refused("output.staging_exists", STAGING, "A staging directory from an earlier run is present.")
    if (proj / WAIVERS).exists():
        raise pcba.Refused("package.waivers_unsupported", WAIVERS,
                           "This package does not apply waivers. Remove the waiver file or wait for waiver support.")

    registry = pcba.validate.load_registry(pcba.validate.HERE / "schemas")
    snap = pcba.Snapshots(proj)
    result = pcba.build(project, board_rel, variant, as_of, None, snapshots=snap)

    # 1. Capture. Every input is read once, and every later step uses these bytes.
    board_snap = _capture(pcba, snap, FIXED["board_record"], "board_record")
    board = pcba.parse_checked(board_snap["raw"], FIXED["board_record"], registry)
    if board.get("restrictions"):
        texts = " | ".join(item["text"] for item in board["restrictions"])
        raise pcba.Refused("supplier.restriction_review", FIXED["board_record"],
                           f"The board has restrictions that need supplier review before a package: {texts}")
    pcb = _capture(pcba, snap, FIXED["board"], "board")
    schematic = _capture(pcba, snap, FIXED["schematic"], "schematic")
    footprints = pcba.read_board(pcb["raw"], FIXED["board"])
    variants_snap = _capture(pcba, snap, FIXED["variants"], "variants")
    variants = pcba.parse_checked(variants_snap["raw"], FIXED["variants"], registry)["variants"]
    selected = next((v for v in variants if v["id"] == variant), None)
    if selected is None:
        raise pcba.Refused("variant.missing", FIXED["variants"], f"The variant {variant} is not declared.")
    states = selected["references"]
    interface_snap = _capture(pcba, snap, FIXED["board_interface"], "board_interface")
    interface = pcba.parse_checked(interface_snap["raw"], FIXED["board_interface"], registry, suffix=".json")
    export_snap = _capture(pcba, snap, FIXED["export_settings"], "export_settings")
    export_record = pcba.parse_checked(export_snap["raw"], FIXED["export_settings"], registry)
    try:
        export.validate_drill_settings(export_record)
    except export.ExportError as err:
        raise pcba.Refused(err.code, FIXED["export_settings"], err.message)
    toolchain_snap = _capture(pcba, snap, FIXED["toolchain"], "toolchain")
    lock = pcba.parse_checked(toolchain_snap["raw"], FIXED["toolchain"], registry, suffix=".json")
    profile_snap = _capture(pcba, snap, FIXED["supplier_profile"], "supplier_profile")
    profile = pcba.parse_checked(profile_snap["raw"], FIXED["supplier_profile"], registry)
    if profile["content_sha256"] != board["supplier"]["profile_sha256"]:
        raise pcba.Refused("supplier.profile_mismatch", FIXED["supplier_profile"],
                           "The supplier profile content hash does not match the board record.")
    rules_snap = _capture(pcba, snap, SUPPLIER_RULES, "supplier_rules")
    rules = _plain_record(pcba, rules_snap["raw"], SUPPLIER_RULES, RULES_SCHEMA)
    settings_snap = _capture(pcba, snap, SUPPLIER_SETTINGS, "supplier_settings")
    settings = _plain_record(pcba, settings_snap["raw"], SUPPLIER_SETTINGS, SETTINGS_SCHEMA)
    evidence_snap = _capture_optional(pcba, snap, EVIDENCE, "supplier_evidence")
    evidence_raw = evidence_snap["raw"] if evidence_snap is not None else None

    sierra = pcba.load_sierra_module()
    declared = ((profile.get("extensions") or {}).get("pcba") or {}).get("hand_installed_bom")
    policy = declared if declared in ("include_in_bom", "exclude_from_bom") else (
        "missing" if declared is None else "unknown")
    bom_produced = policy in ("include_in_bom", "exclude_from_bom")
    neutral_bytes = _json_bytes(result)

    # 2. Toolchain. The local image must be the locked image, and its KiCad version must match the lock.
    container = lock.get("container")
    if container is None:
        raise pcba.Refused("toolchain.container_missing", FIXED["toolchain"], "The lock names no container image.")
    try:
        identity = export.resolve_image(container["image"], container["digest"])
        version = export.kicad_version(identity)
    except export.ExportError as err:
        raise pcba.Refused(err.code, FIXED["toolchain"], err.message)
    if version != lock["tools"]["kicad"]["version"]:
        raise pcba.Refused("toolchain.version_mismatch", FIXED["toolchain"],
                           f"The image reports KiCad {version}. The lock names {lock['tools']['kicad']['version']}.")

    # 3. KiCad runs on private copies of the captured bytes.
    try:
        fab = export.run_fabrication(identity, pcb["raw"], export_record)
        drc_bytes = export.run_drc(identity, pcb["raw"])
        erc_bytes = export.run_erc(identity, schematic["raw"])
        netlist_bytes = export.run_netlist(identity, schematic["raw"])
        worker_bytes = Path(__file__).with_name("board_inventory_worker.py").read_bytes()
        inventory_bytes = export.run_board_inventory(identity, pcb["raw"], worker_bytes)
    except export.ExportError as err:
        raise pcba.Refused(err.code, FIXED["board"], err.message)

    inventory = json.loads(inventory_bytes)
    if inventory["refused"]:
        message = " ".join(f"{item['object']}: {item['reason']}" for item in inventory["refused"])
        raise pcba.Refused("drill.unsupported", FIXED["board"], message)
    holes = [{"id": item["object"], "x": item["x_mm"], "y": item["y_mm"],
              "diameter_mm": item["diameter_mm"], "plated": item["plated"]}
             for item in inventory["holes"]]
    inventory.update({"board_sha256": pcb["sha256"], "worker_sha256": report.sha256(worker_bytes),
                      "image_identity": identity})

    # 4. Checks and outputs.
    layers = [(layer["role"], layer["kicad_layer"]) for layer in export_record["layers"]]
    fab_layer = export_record["extensions"]["pcba"]["fabrication_drawing"]["kicad_layer"]
    layers.append(("fabrication", fab_layer))
    expected = _expected_names(export_record)
    actual = {**fab["gerber"], **fab["drill"]}
    layer_result = checks_fab.layer_order(fab["gerber"], layers)
    plated_name = f"board{export_record['drill']['plated_suffix']}"
    nonplated_name = f"board{export_record['drill']['nonplated_suffix']}"

    outputs = {
        "reports/assembly-neutral.json": ("report", None, neutral_bytes),
        "placement/sierra-xy-draft.csv": ("placement", None, sierra.xy_csv_bytes(result)),
        "test/test-record.json": ("test_record", None, sierra.test_record_bytes(result, board["electrical_limits"])),
        "reports/sierra-status.json": ("report", None, sierra.status_bytes(
            board["supplier"]["profile_sha256"], policy, bom_produced, board["supplier"]["id"])),
        "reports/drc.json": ("report", None, drc_bytes),
        "reports/board-hole-inventory.json": ("report", None, _json_bytes(inventory)),
    }
    if bom_produced:
        bom_bytes = sierra.xlsx_bytes(sierra.bom_table(result, board["name"], board["release_revision"], policy))
        outputs["bom/sierra-bom.xlsx"] = ("bom", None, bom_bytes)
    else:
        bom_bytes = None
    # Layer files are found by the function in their content. The output names come from the settings.
    for layer, name in layer_result["layer_files"].items():
        if layer == fab_layer:
            outputs["fab/fabrication-drawing.gbr"] = ("fabrication_drawing", None, fab["gerber"][name])
            continue
        role = next(item_role for item_role, kicad in layers if kicad == layer)
        outputs[f"fab/gerber/{expected_name_for(export_record, layer)}"] = (
            LAYER_ROLE[role], layer, fab["gerber"][name])
    if plated_name in fab["drill"]:
        outputs["drill/plated.drl"] = ("drill_plated", None, fab["drill"][plated_name])
    if nonplated_name in fab["drill"]:
        outputs["drill/nonplated.drl"] = ("drill_nonplated", None, fab["drill"][nonplated_name])
    outputs["drawings/assembly.svg"] = ("assembly_drawing", None, drawing.assembly_svg(
        result["rows"], interface["outline"], variant, board["name"]))
    if fab["image"]:
        outputs["image/board.svg"] = ("image", None, fab["image"])

    results = [
        checks_design.drc(drc_bytes, version),
        checks_design.erc(erc_bytes, version),
        checks_design.parity(netlist_bytes, pcb["raw"], version),
        checks_fab.profile_evidence(evidence_raw, profile["evidence_sha256"]),
        checks_fab.export_inventory(actual, expected),
        layer_result,
        checks_fab.drill_split(fab["drill"], export_record["drill"]["decimal_places"], holes,
                               plated_name, nonplated_name),
        checks_fab.supplier_rules(rules, settings, export_record),
        checks_asm.bom_consistent(bom_bytes, result["bom_groups"], policy),
        checks_asm.placement_rotation(result["rows"], footprints, neutral_bytes),
        checks_asm.variant_agreement(result["rows"], dict(states), neutral_bytes),
        checks_asm.stock_dated(result["stock"], neutral_bytes),
        checks_asm.test_record(outputs["test/test-record.json"][2], board["electrical_limits"],
                               selected.get("hand_installed", []), variant),
    ]
    for res in results:
        if res["artifact"] is not None and res["artifact"]["path"] not in outputs:
            outputs[res["artifact"]["path"]] = ("report", None, res["artifact"]["bytes"])

    # 5. Evidence, manifest, staging.
    inputs = snap.inputs(MANIFEST_ROLES)
    evidence = {}
    for res in results:
        record = report.evidence_record(res, inputs, as_of.isoformat())
        problems = pcba.validate.validate_record(record, registry, f"evidence/{res['id']}.json")
        if problems:
            raise pcba.Refused(problems[0]["code"], f"evidence/{res['id']}.json", problems[0]["message"])
        evidence[f"evidence/{res['id']}.json"] = _json_bytes(record)
    checks = []
    for res in results:
        path = f"evidence/{res['id']}.json"
        checks.append({"id": res["id"], "status": res["status"], "evidence_path": path,
                       "evidence_sha256": report.sha256(evidence[path])})
    reasons = []
    for res in results:
        for item in res["reasons"]:
            reasons.append({"code": item["code"], "text": item["text"]})
    reasons.append({"code": "supplier.location_unconfirmed",
                    "text": "The fabrication and assembly locations are unconfirmed for turnkey_pro."})
    out_entries = []
    for rel, (role, layer, data) in sorted(outputs.items()):
        item = {"role": role, "path": rel, "sha256": report.sha256(data), "size_bytes": len(data)}
        if layer is not None:
            item["layer"] = layer
        out_entries.append(item)
    for rel, data in sorted(evidence.items()):
        out_entries.append({"role": "evidence", "path": rel, "sha256": report.sha256(data), "size_bytes": len(data)})
    manifest = report.manifest_record(package_id, board, pcb["sha256"], variant,
                                      board["supplier"]["profile_sha256"], inputs, out_entries, checks, reasons,
                                      _tool_versions(version))
    manifest_bytes = _json_bytes(manifest)
    problems = pcba.validate.validate_record(manifest, registry, "manifest.json")
    if problems:
        raise pcba.Refused(problems[0]["code"], "manifest.json", problems[0]["message"])

    files = {**{rel: data for rel, (_, _, data) in outputs.items()}, **evidence, "manifest.json": manifest_bytes}
    expected_hashes = {rel: (report.sha256(data), len(data)) for rel, data in files.items()}
    try:
        for rel, data in sorted(files.items()):
            pcba.project_io.atomic_write(proj, staging / rel, data)
        if "after_stage" in hooks:
            hooks["after_stage"](staging)
        _verify_staged(staging, expected_hashes, pcba.Refused)

        # 6. The copied validator checks the project and the staged package together.
        code, validation = pcba.validate.build_report([], pcba.validate.HERE / "schemas", project=proj,
                                                      package=staging)
        if code != 0:
            first = validation["findings"][0] if validation["findings"] else {
                "code": "package.validation_failed", "file": "", "message": "The validator refused the package."}
            raise pcba.Refused(first["code"], first["file"] or rel_dest, first["message"])
        if "after_validate" in hooks:
            hooks["after_validate"]()

        # 7. Freshness again, immediately before publication.
        snap.check_unchanged()
        _verify_staged(staging, expected_hashes, pcba.Refused)
        dest.parent.mkdir(parents=True, exist_ok=True)
        pcba.project_io.publish_dir(proj, staging, dest)
    except pcba.project_io.PostRenameError as err:
        raise pcba.ReplacedThenFailed(rel_dest, err.__cause__ or err) from err
    except pcba.Refused:
        shutil.rmtree(staging, ignore_errors=True)
        raise
    except OSError as err:
        shutil.rmtree(staging, ignore_errors=True)
        raise pcba.Refused("output.write_failed", rel_dest, f"The package cannot be published: {err.strerror}.")
    return {"status": "written", "package": rel_dest, "status_manifest": "unqualified",
            "files": len(files), "checks": {c["id"]: c["status"] for c in checks},
            "validation": {"status": validation["status"], "exit_code": code}}


def expected_name_for(export_record: dict, kicad_layer: str) -> str:
    """Return the canonical output name of a Gerber layer, built from the export settings."""
    for layer in export_record["layers"]:
        if layer["kicad_layer"] == kicad_layer:
            return f"board-{kicad_layer.replace('.', '_')}{layer['suffix']}"
    raise KeyError(kicad_layer)
