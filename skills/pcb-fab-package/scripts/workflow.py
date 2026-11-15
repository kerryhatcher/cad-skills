# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///

"""The design, supplier and package commands of pcb-fab-package.

Every KiCad command runs in the accepted image through podman with no network. Each command works on a copy of
the project. The project files are hashed before and after the run. A change to a source file is exit 1.

Exit status: 0 success, 1 check failure or unmet condition, 2 unsupported construct or missing prerequisite,
3 tool failure.
"""
import hashlib
import json
import os
import pathlib
import shutil
import subprocess
import sys
from decimal import Decimal
from fractions import Fraction

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validate as VAL  # noqa: E402
import fab  # noqa: E402
import inspect_slots  # noqa: E402
import export_inspect  # noqa: E402
import review  # noqa: E402
import semantics  # noqa: E402
import project_io as PIO  # noqa: E402

IMAGE = "localhost/cad-skills-pcb:b6"
SCHEMAS = HERE.parent / "contracts" / "schemas"
EXIT_OK, EXIT_FAIL, EXIT_UNSUPPORTED, EXIT_TOOL = 0, 1, 2, 3
RULE_CONSTRAINT = {"min_trace": "track_width", "min_space": "clearance", "min_annular_ring": "annular_width",
                   "min_drill": "hole_size", "plated_drill_to_internal_copper": "hole_clearance",
                   "edge_keepout": "edge_clearance"}
# Report keys of KiCad 10.0.5 for each supplier rule: the constraint name and the violation key that the
# DRC report uses. A count must include every key that the rule can produce.
# The six measured pairs (constraint name, violation and severity key) are in b7-workflow-checkpoint-1-root.md.
# Constraint names are used only in the generated rule file. Report counts and severities use these keys only.
REPORT_KEYS = {
    "min_trace": ("track_width",),
    "min_space": ("clearance",),
    "min_annular_ring": ("annular_width",),
    "min_drill": ("drill_out_of_range",),
    "plated_drill_to_internal_copper": ("hole_clearance",),
    "edge_keepout": ("copper_edge_clearance",),
}


def violations_for(counts, key):
    """The number of violations of one supplier rule, counted by every report key of that rule."""
    return sum(counts.get(name, 0) for name in REPORT_KEYS[key])


SOURCE_FILES = ("kicad/board.kicad_pcb", "kicad/board.kicad_sch", "kicad/board.kicad_pro")
INPUT_RECORDS = ("board.yaml", "manufacturing/export.yaml", "manufacturing/supplier.yaml", "toolchain.lock.json")


class Stop(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def sha_file(path):
    return hashlib.sha256(pathlib.Path(path).read_bytes()).hexdigest()


RUN_IMAGE = IMAGE  # replaced by the measured image identity in runtime_identity
STAGE_MARK = ".pcb-fab-stage"
# Every project input that a command consumes. Each one is read once, into the capture.
SNAPSHOT_FILES = ("board.yaml", "toolchain.lock.json", "variants.yaml", "kicad/board.kicad_pcb",
                  "kicad/board.kicad_sch", "kicad/board.kicad_pro", "kicad/board.kicad_dru",
                  "mechanical/board-interface.json", "manufacturing/export.yaml", "manufacturing/supplier.yaml",
                  "manufacturing/waivers.yaml")


def captured(project, extra=None):
    """Read each consumed input once. An absent optional input is None."""
    data = {}
    for rel in SNAPSHOT_FILES:
        path = project / rel
        data[rel] = path.read_bytes() if path.is_file() else None
    for rel, path in sorted((extra or {}).items()):
        path = pathlib.Path(path)
        data[rel] = path.read_bytes() if path.is_file() else None
    return data


def digest(data):
    return {key: (hashlib.sha256(value).hexdigest() if value is not None else "absent") for key, value in data.items()}


def snapshot(project, extra=None):
    """The SHA-256 of every consumed input, from one read of each file."""
    return digest(captured(project, extra))


def podman(stage, argv, worker=None):
    cmd = ["podman", "run", "--rm", "--pull=never", "--network", "none", "--security-opt", "label=disable",
           "-w", "/work", "-v", f"{stage}:/work"]
    if worker is not None:
        cmd += ["-v", f"{worker}:/worker:ro"]
    proc = subprocess.run(cmd + [RUN_IMAGE] + argv, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def profile_from_bytes(project, raw, scratch):
    """Parse the profile from the captured bytes. The scratch copy holds the same bytes.

    The scratch path is confined before any write: under out/fab, with no link in any component."""
    confine(project, scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    path = scratch / "profile.yaml"
    path.write_bytes(raw)
    return fab.check_profile(path)


def export_from_bytes(raw):
    """The export contract and its layer list, parsed from the captured bytes."""
    contract = VAL.parse_record(raw, ".yaml", "export.yaml")
    return contract, [layer["kicad_layer"] for layer in contract["layers"]]


def stage_project(project, stage, extra=None):
    return stage_from(captured(project, extra), stage)


def stage_from(data, stage):
    """Stage the captured bytes of the KiCad files and return the digests of the same bytes."""
    if stage.exists():
        if not (stage / STAGE_MARK).is_file():
            raise Stop(EXIT_UNSUPPORTED, f"the stage {stage} exists without the stage marker; it is not removed")
        shutil.rmtree(stage)
    (stage / "kicad").mkdir(parents=True)
    (stage / STAGE_MARK).write_text("pcb-fab-package stage\n")
    for rel in SOURCE_FILES:
        if data[rel] is None:
            raise Stop(EXIT_UNSUPPORTED, f"missing prerequisite {rel}")
        (stage / rel).write_bytes(data[rel])
    return digest(data)


def source_hashes(project, extra=None):
    return snapshot(project, extra)


def findings(data):
    """Count the violations, unconnected items and parity items of a KiCad JSON report."""
    counts = {"violations": 0, "unconnected": 0, "parity": 0}
    for key in ("violations",):
        counts["violations"] += len(data.get(key, []))
        for sheet in data.get("sheets", []):
            counts["violations"] += len(sheet.get("violations", []))
    counts["unconnected"] = len(data.get("unconnected_items", []))
    counts["parity"] = len(data.get("schematic_parity", []))
    return counts


def read_json(path):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError) as err:
        raise Stop(EXIT_TOOL, f"KiCad produced no readable report {path.name}: {err}")


def write_result(path, record):
    path.parent.mkdir(parents=True, exist_ok=True)
    data = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")
    project = path.parents[3]  # <project>/out/fab/<step>/<file>
    PIO.atomic_write(project, path, data)




def confine(project, out):
    """Every write of a command stays under the project's out/fab tree. Refuse a link or an escape."""
    root = (project / "out" / "fab").resolve()
    target = out.resolve()
    if target != root and root not in target.parents:
        raise Stop(EXIT_UNSUPPORTED, f"the path {out} is outside out/fab")
    for part in [out] + list(out.parents):
        if part.is_symlink():
            raise Stop(EXIT_UNSUPPORTED, f"the path {out} contains a symbolic link")
        if part == project:
            break


def runtime_identity(lock_raw):
    """Compare the measured image identity with the captured lock, then measure the KiCad version in the image."""
    lock = json.loads(lock_raw)
    image = lock["container"]["image"]
    proc = subprocess.run(["podman", "image", "inspect", image, "--format", "{{.Id}}"], capture_output=True, text=True)
    if proc.returncode != 0:
        raise Stop(EXIT_UNSUPPORTED, f"the image {image} is not present")
    image_id = "sha256:" + proc.stdout.strip()
    if image_id != lock["container"]["digest"]:
        raise Stop(EXIT_UNSUPPORTED, "the image identity differs from the toolchain lock")
    global RUN_IMAGE
    RUN_IMAGE = image_id.split(":", 1)[1]  # every later run uses the measured identity, not the mutable tag
    ver = subprocess.run(["podman", "run", "--rm", "--pull=never", "--network", "none", "--security-opt", "label=disable",
                          RUN_IMAGE, "kicad-cli", "version"], capture_output=True, text=True)
    measured = ver.stdout.strip().splitlines()[0] if ver.returncode == 0 and ver.stdout.strip() else ""
    if measured != lock["tools"]["kicad"]["version"]:
        raise Stop(EXIT_UNSUPPORTED, f"the measured KiCad version {measured!r} differs from the lock")
    return {"image": image, "image_id": image_id, "kicad_version": measured}


def _design(project, profile_path, out):
    """Run ERC, DRC with parity, the exports, the slot inventory and the drawing. Return (exit, result)."""
    consumed = captured(project, {"profile": profile_path})
    confine(project, out)
    for child in ("export", "logs", "work", "captured"):
        confine(project, out / child)
    profile = profile_from_bytes(project, consumed["profile"], out / "captured")
    runtime = runtime_identity(consumed["toolchain.lock.json"])
    stage = out / "work"
    before = stage_from(consumed, stage)
    contract, layers = export_from_bytes(consumed["manufacturing/export.yaml"])
    kicad_stage = stage / "kicad"
    exp = out / "export"
    if exp.exists():
        shutil.rmtree(exp)
    exp.mkdir(parents=True)
    (stage / "export").mkdir()
    logs = out / "logs"
    logs.mkdir(exist_ok=True)
    rc_erc, _, err_erc = podman(stage, ["kicad-cli", "sch", "erc", "--exit-code-violations", "--severity-all",
                                        "--format", "json", "-o", "/work/erc.json", "/work/kicad/board.kicad_sch"])
    rc_drc, _, err_drc = podman(stage, ["kicad-cli", "pcb", "drc", "--schematic-parity", "--severity-all",
                                        "--format", "json", "-o", "/work/drc.json", "/work/kicad/board.kicad_pcb"])
    (logs / "erc.stderr").write_text(err_erc)
    (logs / "drc.stderr").write_text(err_drc)
    erc = read_json(stage / "erc.json")
    drc = read_json(stage / "drc.json")
    rc_exports = {}
    commands = {
        "gerbers": ["kicad-cli", "pcb", "export", "gerbers", "--output", "/work/export/", "--layers", ",".join(layers),
                    "--no-x2", "--precision", "6", "--board-plot-params", "/work/kicad/board.kicad_pcb"],
        "drill": ["kicad-cli", "pcb", "export", "drill", "--output", "/work/export/", "--format", "excellon",
                  "--drill-origin", "absolute", "--excellon-zeros-format", "suppressleading", "-u", "mm",
                  "--excellon-separate-th", "/work/kicad/board.kicad_pcb"],
        "layers_pdf": ["kicad-cli", "pcb", "export", "pdf", "--output", "/work/export/layers.pdf",
                       "--layers", "F.Fab,B.Fab,Edge.Cuts", "/work/kicad/board.kicad_pcb"],
        "schematic_pdf": ["kicad-cli", "sch", "export", "pdf", "--output", "/work/export/schematic.pdf",
                          "/work/kicad/board.kicad_sch"],
    }
    for name, argv in commands.items():
        rc_exports[name], _, err = podman(stage, argv)
        (logs / f"export-{name}.stderr").write_text(err)
        if rc_exports[name] != 0:
            raise Stop(EXIT_TOOL, f"the export {name} failed with exit {rc_exports[name]}")
    worker_rc, worker_out, worker_err = podman(stage, ["/usr/bin/python3", "/worker/board_inventory_slots.py",
                                                       "/work/kicad/board.kicad_pcb"], worker=HERE)
    (logs / "inventory.stderr").write_text(worker_err)
    if worker_rc == 2:
        raise Stop(EXIT_UNSUPPORTED, "the inventory refuses the board: " + worker_out.strip())
    if worker_rc != 0:
        raise Stop(EXIT_TOOL, f"the inventory worker failed with exit {worker_rc}")
    inventory = json.loads(worker_out)
    (out / "inventory.json").write_text(json.dumps(inventory, indent=1, sort_keys=True) + "\n")
    for name in ("erc.json", "drc.json"):
        shutil.copy2(stage / name, out / name)
    for name in sorted(p.name for p in (stage / "export").iterdir()) if (stage / "export").is_dir() else []:
        shutil.copy2(stage / "export" / name, exp / name)
    for name in sorted(p.name for p in exp.iterdir() if p.is_file()):
        pass
    counts_erc = findings(erc)
    counts_drc = findings(drc)
    after = source_hashes(project, {"profile": profile_path})
    if after != before:
        raise Stop(EXIT_FAIL, "the source files changed during the design run")
    drawing_facts = out / "drawing-facts.json"
    fab_sheet = out / "fabrication-drawing.pdf"
    fact_obj = fab.drawing_facts(inventory, profile, consumed["kicad/board.kicad_pcb"],
                                 "design-run", consumed["manufacturing/supplier.yaml"])
    drawing_facts.write_text(json.dumps(fact_obj, indent=2, sort_keys=True) + "\n")
    fab_sheet.write_bytes(fab.drawing_pdf(fact_obj))
    result = {"schema_id": "pcb-fab-package/design-result", "schema_version": 1,
              "tool": {"kicad": runtime["kicad_version"], "image_id": runtime["image_id"]},
              "erc": {"exit": rc_erc, "counts": counts_erc},
              "drc": {"exit": rc_drc, "counts": counts_drc},
              "exports": {k: v for k, v in rc_exports.items()},
              "source_sha256": before, "runtime": runtime,
              "inputs": {rel: hashlib.sha256(consumed[rel]).hexdigest() for rel in INPUT_RECORDS if consumed[rel] is not None},
              "outputs": {}}
    for path in sorted(out.rglob("*")):
        if path.is_file() and path.name not in ("design-result.json",) and "work" not in path.parts:
            result["outputs"][str(path.relative_to(out))] = sha_file(path)
    code = EXIT_OK
    if counts_erc["violations"] or counts_drc["violations"] or counts_drc["unconnected"] or counts_drc["parity"]:
        code = EXIT_FAIL
    result["exit"] = code
    binding = {"schema_id": "pcb-fab-package/design-binding", "schema_version": 1,
               "snapshot": before, "outputs": result["outputs"]}
    binding_bytes = (json.dumps(binding, indent=2, sort_keys=True) + "\n").encode("utf-8")
    PIO.atomic_write(project, out / "design-binding.json", binding_bytes)
    result["binding_sha256"] = hashlib.sha256(binding_bytes).hexdigest()
    result["content_sha256"] = VAL.canonical_hash(result)
    write_result(out / "design-result.json", result)
    return code, result


SLOT_CLASSES = {"pth": "PTH", "npth": "NPTH"}


def supplier_rules_text(profile):
    """The generated KiCad rules, one per supplier limit that KiCad checks. Values are exact decimals in mm."""
    lines = ['(version 1)']
    for key in sorted(profile["division"]["kicad_dru"]):
        limit = profile["limits"][key]
        mm = Decimal(str(limit["value"])) * (Decimal("0.0254") if limit["unit"] == "mil" else Decimal(1))
        constraint = RULE_CONSTRAINT[key]
        lines.append(f'(rule "supplier_{key}" (constraint {constraint} (min {mm.normalize()}mm)))')
    return "\n".join(lines) + "\n"


def effective_pro(project_pro_bytes, profile):
    data = json.loads(project_pro_bytes or b"{}")
    ds = data.setdefault("board", {}).setdefault("design_settings", {})
    ds.pop("drc_exclusions", None)  # mandatory supplier checks clear source exclusions in staging
    severities = ds.setdefault("rule_severities", {})
    for key in profile["division"]["kicad_dru"]:
        for name in REPORT_KEYS[key]:
            severities[name] = "error"
    return json.dumps(data, indent=2, sort_keys=True) + "\n"


def _supplier(project, profile_path, out, design_dir, manual_path=None):
    """Run the supplier checks on a staged copy. Return (exit, result)."""
    extra_inputs = {"profile": profile_path}
    if manual_path is not None:
        extra_inputs["manual"] = manual_path
        extra_inputs["manual-artifact"] = manual_artifact_path(project, pathlib.Path(manual_path).read_bytes())
    consumed = captured(project, extra_inputs)
    confine(project, out)
    for child in ("export", "logs", "work", "captured"):
        confine(project, out / child)
    profile = profile_from_bytes(project, consumed["profile"], out / "captured")
    runtime = runtime_identity(consumed["toolchain.lock.json"])
    stage = out / "work"
    before = stage_from(consumed, stage)
    generated = supplier_rules_text(profile)
    src_dru = consumed["kicad/board.kicad_dru"]
    dru_text = (src_dru.decode("utf-8").rstrip("\n") + "\n" + generated.split("\n", 1)[1]) if src_dru is not None else generated
    (stage / "kicad" / "board.kicad_dru").write_text(dru_text)
    (stage / "kicad" / "board.kicad_pro").write_text(effective_pro(consumed["kicad/board.kicad_pro"] or b"", profile))
    rc, _, err = podman(stage, ["kicad-cli", "pcb", "drc", "--severity-all", "--format", "json", "-o", "/work/drc.json",
                                "/work/kicad/board.kicad_pcb"])
    (out / "supplier-drc.stderr").write_text(err)
    if rc not in (0, 5):
        raise Stop(EXIT_TOOL, f"the supplier DRC failed with exit {rc}")
    drc = read_json(stage / "drc.json")
    counts = {}
    for item in drc.get("violations", []):
        counts[item.get("type")] = counts.get(item.get("type"), 0) + 1
    rows = []
    for key in sorted(profile["division"]["kicad_dru"]):
        typ = RULE_CONSTRAINT[key]
        n = violations_for(counts, key)
        rows.append({"condition": key, "method": "kicad_dru", "mandatory": True,
                     "status": "pass" if n == 0 else "fail", "violations": n,
                     "interpretation": f"KiCad {typ} with the supplier minimum"})
    inventory = read_json(design_dir / "inventory.json")
    outline = inventory["outline"]
    for key in ("board_min_edge",):
        limit = profile["limits"][key]
        value = min(Fraction(str(outline["width"])), Fraction(str(outline["height"]))) * fab.UNIT_MM["mm"]
        rows.append({"condition": key, "method": "geometric_test", "mandatory": True,
                     "status": "pass" if value >= fab.limit_in_mm(limit) else "fail",
                     "interpretation": "minimum outline dimension from the saved board"})
    for key, kind in (("board_max_width", "width"), ("board_max_height", "height")):
        limit = profile["limits"][key]
        value = Fraction(str(outline[kind]))
        rows.append({"condition": key, "method": "geometric_test", "mandatory": True,
                     "status": "pass" if value <= fab.limit_in_mm(limit) else "fail",
                     "interpretation": "maximum outline dimension from the saved board"})
    slot_report = out / "slots.json"
    exp = design_dir / "export"
    code_slot = inspect_slots.main(["--board-inventory", str(design_dir / "inventory.json"),
                                    "--pth", str(exp / "board-PTH.drl"), "--npth", str(exp / "board-NPTH.drl"),
                                    "--report", str(slot_report)])
    min_slot_mm = fab.limit_in_mm(profile["limits"]["min_slot_size"])
    minors = [Fraction(str(s["minor_mm"])) for s in inventory.get("slots", [])]
    slot_ok = all(m >= min_slot_mm for m in minors)
    if code_slot == 2:
        raise Stop(EXIT_UNSUPPORTED, "the slot records are unsupported")
    if code_slot == 3:
        raise Stop(EXIT_TOOL, "the slot inspection could not read its inputs")
    rows.append({"condition": "min_slot_size", "method": "slot_inspection", "mandatory": True,
                 "status": "pass" if (code_slot == 0 and slot_ok) else "fail",
                 "interpretation": "minor dimension of every drilled slot and record match"})
    mask_report = out / "mask.json"
    mask_report.unlink(missing_ok=True)
    rc_mask = fab.run_mask_worker(str(exp / "board-F_Mask.gbr"), str(profile["limits"]["mask_web_min"]["value"]), str(mask_report))
    if rc_mask == 2:
        raise Stop(EXIT_UNSUPPORTED, "the mask construct is unsupported for automatic inspection")
    if rc_mask == 3:
        raise Stop(EXIT_TOOL, "the mask inspection failed")
    mask_result = json.loads(mask_report.read_text())["result"]
    rows.append({"condition": "mask_web_min", "method": "mask_inspection", "mandatory": True,
                 "status": mask_result if mask_result in ("pass", "fail", "uncertain") else "fail",
                 "interpretation": "exact web distance of the exported mask flashes"})
    top = json.loads((out / "mask.json").read_text())
    if top["gerber_sha256"] != sha_file(exp / "board-F_Mask.gbr"):
        raise Stop(EXIT_FAIL, "the top mask measurement is not bound to the published Gerber")
    rows.append({"condition": "mask_web_min_top", "method": "mask_inspection", "mandatory": True,
                 "status": top["result"] if top["result"] in ("pass", "fail", "uncertain") else "fail",
                 "interpretation": "exact web distance of the top mask flashes"})
    bottom_report = out / "mask-bottom.json"
    bottom_report.unlink(missing_ok=True)
    rc_bottom = fab.run_mask_worker(str(exp / "board-B_Mask.gbr"), str(profile["limits"]["mask_web_min"]["value"]), str(bottom_report))
    if rc_bottom == 2:
        raise Stop(EXIT_UNSUPPORTED, "the bottom mask construct is unsupported for automatic inspection")
    if rc_bottom == 3:
        raise Stop(EXIT_TOOL, "the bottom mask inspection failed")
    bottom = json.loads(bottom_report.read_text())
    if bottom["gerber_sha256"] != sha_file(exp / "board-B_Mask.gbr"):
        raise Stop(EXIT_FAIL, "the bottom mask measurement is not bound to the published Gerber")
    rows.append({"condition": "mask_web_min_bottom", "method": "mask_inspection", "mandatory": True,
                 "status": bottom["result"] if bottom["result"] in ("pass", "fail", "uncertain") else "fail",
                 "interpretation": "exact web distance of the bottom mask flashes"})
    layers_needed = profile["extensions"]["service.layers"]["value"]
    rows.append({"condition": "service.layers", "method": "geometric_test", "mandatory": True,
                 "status": "pass" if len(inventory["copper_layers"]) == layers_needed else "fail",
                 "interpretation": "copper layers of the saved board equal the service layer count"})
    multiple = profile["extensions"]["service.order_multiple"]["value"]
    quantity = VAL.parse_record(consumed["board.yaml"], ".yaml", "board.yaml")["quantity"]
    rows.append({"condition": "service.order_multiple", "method": "geometric_test", "mandatory": True,
                 "status": "pass" if quantity % multiple == 0 else "fail",
                 "interpretation": f"order quantity {quantity} is a multiple of {multiple} (board record)"})
    manual_info = None
    silk_row = {"condition": "silk_line_min_short_text", "method": "manual_evidence", "mandatory": True,
                "status": "pending", "interpretation": "manual evidence is required before qualification"}
    if manual_path is not None:
        manual_info, silk_row["status"], silk_row["interpretation"] = check_manual(
            manual_path, consumed["manual"], consumed["manual-artifact"], consumed["kicad/board.kicad_pcb"],
            design_dir, "silk_line_min_short_text", out)
    rows.append(silk_row)
    for key in ("silk_line_recommended", "overlapping_drill_clearance"):
        rows.append({"condition": key, "method": "manual_evidence", "mandatory": False, "status": "finding",
                     "interpretation": "recommendation: reported, never a failure"})
    after = source_hashes(project, extra_inputs)
    if after != before:
        raise Stop(EXIT_FAIL, "the source files changed during the supplier run")
    mandatory = [r for r in rows if r["mandatory"]]
    if any(r["status"] == "pending" for r in mandatory) or any(r["status"] == "uncertain" for r in mandatory):
        code = EXIT_FAIL
    elif any(r["status"] == "fail" for r in mandatory):
        code = EXIT_FAIL
    else:
        code = EXIT_OK
    (out / "supplier.kicad_dru").write_text(dru_text)
    (out / "supplier.kicad_pro").write_text((stage / "kicad" / "board.kicad_pro").read_text())
    (out / "supplier-drc.json").write_text((stage / "drc.json").read_text())
    result = {"schema_id": "pcb-fab-package/supplier-result", "schema_version": 1, "profile": profile["id"],
              "manual": manual_info, "design_binding": sha_file(design_dir / "design-result.json"), "runtime": runtime,
              "profile_sha256": profile["content_sha256"], "rows": rows, "source_sha256": before,
              "effective": {"board.kicad_dru": sha_file(out / "supplier.kicad_dru"),
                            "board.kicad_pro": sha_file(out / "supplier.kicad_pro")},
              "exit": code}
    binding = {"schema_id": "pcb-fab-package/supplier-binding", "schema_version": 1, "snapshot": before,
               "design_binding_sha256": sha_file(design_dir / "design-binding.json"), "manual": manual_info,
               "outputs": {rel: sha_file(out / rel) for rel in ("supplier.kicad_dru", "supplier.kicad_pro",
                                                              "supplier-drc.json", "slots.json", "mask.json", "manual-artifact.txt", "manual-evidence.json",
                                                              "mask-bottom.json") if (out / rel).is_file()}}
    binding_bytes = (json.dumps(binding, indent=2, sort_keys=True) + "\n").encode("utf-8")
    PIO.atomic_write(project, out / "supplier-binding.json", binding_bytes)
    result["binding_sha256"] = hashlib.sha256(binding_bytes).hexdigest()
    write_result(out / "supplier-result.json", result)
    return code, result


MANUAL_KEYS = {"schema_id", "schema_version", "condition", "result", "procedure", "artifact_path", "artifact_sha256",
               "inputs", "reviewer", "statement"}


def manual_artifact_path(project, raw):
    """The project path of the manual artifact that a manual record names. Refuse a path outside out/fab/manual."""
    try:
        rec = VAL.parse_record(raw, ".json", "manual-evidence")
    except VAL.RecordError as err:
        raise Stop(EXIT_FAIL, f"the manual evidence record is invalid: {err}")
    if not isinstance(rec, dict) or not isinstance(rec.get("artifact_path"), str):
        raise Stop(EXIT_FAIL, "the manual evidence record names no artifact path")
    art_rel = pathlib.PurePosixPath(rec["artifact_path"])
    if art_rel.is_absolute() or ".." in art_rel.parts or art_rel.parts[:3] != ("out", "fab", "manual"):
        raise Stop(EXIT_FAIL, "the manual artifact must be under out/fab/manual/")
    return project.joinpath(*art_rel.parts)


def check_manual(manual_path, raw, art_bytes, board_bytes, design_dir, condition, out):
    """Check the captured manual evidence record, artifact and board bytes. Return (info, status, interpretation).

    The inputs are the captured bytes. Raise Stop for a defect."""
    try:
        rec = VAL.parse_record(raw, ".json", "manual-evidence")
    except VAL.RecordError as err:
        raise Stop(EXIT_FAIL, f"the manual evidence record is invalid: {err}")
    if not isinstance(rec, dict) or set(rec) != MANUAL_KEYS:
        raise Stop(EXIT_FAIL, "the manual evidence record has the wrong keys")
    if rec["schema_id"] != "pcb-fab-package/manual-evidence" or rec["schema_version"] != 1:
        raise Stop(EXIT_FAIL, "the manual evidence schema is wrong")
    if rec["condition"] != condition:
        raise Stop(EXIT_FAIL, "the manual evidence names another condition")
    if rec["result"] not in ("pass", "fail", "uncertain"):
        raise Stop(EXIT_FAIL, "the manual evidence result must be pass, fail or uncertain")
    art_rel = pathlib.PurePosixPath(rec["artifact_path"])
    if art_rel.is_absolute() or ".." in art_rel.parts or art_rel.parts[:3] != ("out", "fab", "manual"):
        raise Stop(EXIT_FAIL, "the manual artifact must be under out/fab/manual/")
    if art_bytes is None or hashlib.sha256(art_bytes).hexdigest() != rec["artifact_sha256"]:
        raise Stop(EXIT_FAIL, "the manual artifact is missing or its hash differs")
    out.mkdir(parents=True, exist_ok=True)
    (out / "manual-artifact.txt").write_bytes(art_bytes)
    inputs = rec["inputs"]
    if not isinstance(inputs, dict) or set(inputs) != {"board_sha256", "silk_gerber_sha256"}:
        raise Stop(EXIT_FAIL, "the manual inputs must name board_sha256 and silk_gerber_sha256")
    if inputs["board_sha256"] != hashlib.sha256(board_bytes).hexdigest():
        raise Stop(EXIT_FAIL, "the manual evidence is stale: the board hash differs")
    silk = design_dir / "export" / "board-F_Silkscreen.gbr"
    if not silk.is_file() or inputs["silk_gerber_sha256"] != sha_file(silk):
        raise Stop(EXIT_FAIL, "the manual evidence is stale: the silk Gerber hash differs")
    out.mkdir(parents=True, exist_ok=True)
    (out / "manual-evidence.json").write_bytes(raw)
    info = {"path": "manual-evidence.json", "sha256": hashlib.sha256(raw).hexdigest(),
            "artifact_path": rec["artifact_path"], "artifact_sha256": rec["artifact_sha256"],
            "original_path": str(pathlib.Path(manual_path).resolve()),
            "original_sha256": hashlib.sha256(raw).hexdigest()}
    return info, rec["result"], f"manual evidence by {rec['reviewer']}: {rec['procedure']}"


def supplier_inputs_now(project, profile_path, supplier_result):
    """The current digests of the supplier inputs, read live. The keys match the supplier source hashes."""
    extra = {"profile": profile_path}
    manual = supplier_result.get("manual")
    if manual:
        extra["manual"] = manual["original_path"]
        extra["manual-artifact"] = project.joinpath(*pathlib.PurePosixPath(manual["artifact_path"]).parts)
    return snapshot(project, extra)


def final_gate(project, profile_path, design_dir, supplier_dir, design_result, supplier_result):
    """The last freshness check, run just before publication. Return the problems.

    It compares the source inputs, the bound outputs, and the original manual record with their current bytes."""
    problems = []
    if design_result.get("source_sha256") != snapshot(project, {"profile": profile_path}):
        problems.append("the source files changed before publication")
    if supplier_result.get("source_sha256") != supplier_inputs_now(project, profile_path, supplier_result):
        problems.append("the supplier inputs changed before publication")
    for base, bind_name in ((design_dir, "design-binding.json"), (supplier_dir, "supplier-binding.json")):
        bind = base / bind_name
        if not bind.is_file():
            problems.append(f"the binding {bind_name} is missing at publication")
            continue
        for rel, digest in json.loads(bind.read_text()).get("outputs", {}).items():
            if not (base / rel).is_file() or sha_file(base / rel) != digest:
                problems.append(f"{rel} changed before publication")
    manual = supplier_result.get("manual")
    if manual:
        original = pathlib.Path(manual.get("original_path", ""))
        if not original.is_file() or sha_file(original) != manual.get("original_sha256"):
            problems.append("the original manual record changed before publication")
    return problems


def _package(project, profile_path, release, review_path, dest, design_dir, supplier_dir, expected_review_sha):
    """Build the package and run the B1 validator. Return (exit, manifest)."""
    consumed = captured(project, {"profile": profile_path})
    profile = profile_from_bytes(project, consumed["profile"], supplier_dir / "captured")
    final = dest
    if final.exists():
        raise Stop(EXIT_UNSUPPORTED, "the destination exists")
    confine(project, final)
    dest = final.parent / (".staging-" + final.name)
    if dest.exists():
        raise Stop(EXIT_UNSUPPORTED, "a staging directory exists")
    design_result = json.loads((design_dir / "design-result.json").read_text())
    supplier_result = json.loads((supplier_dir / "supplier-result.json").read_text())
    reasons = []
    design_bound = json.loads((design_dir / "design-binding.json").read_text()).get("outputs", {}) if (design_dir / "design-binding.json").is_file() else {}
    supplier_bound = json.loads((supplier_dir / "supplier-binding.json").read_text()).get("outputs", {}) if (supplier_dir / "supplier-binding.json").is_file() else {}
    if design_result["exit"] != 0:
        reasons.append("design checks are not all passing")
    if supplier_result["exit"] != 0:
        reasons.append("supplier conditions are not all passing")
    review_bytes = review_path.read_bytes() if review_path.is_file() else None
    gate_problems = review.gate(project, profile, consumed["profile"], review_bytes,
                                expected_review_sha, release)
    reasons.extend(gate_problems)
    if review_bytes is not None and sha_file(review_path) != expected_review_sha:
        reasons.append("the review bytes differ from the accepted review hash")
    dest.mkdir(parents=True)
    evidence_dir, report_dir = dest / "evidence", dest / "reports"
    evidence_dir.mkdir()
    report_dir.mkdir()
    outputs = []

    def expected_for(src):
        """The measured hash of a bound output, or None for an unbound file (results are checked as read)."""
        for base, binding in ((design_dir, design_bound), (supplier_dir, supplier_bound)):
            try:
                rel = str(pathlib.Path(src).relative_to(base))
            except ValueError:
                continue
            if rel in binding:
                return binding[rel]
        return None

    def out_item(rel_src, rel_dst, role, layer=None):
        data = pathlib.Path(rel_src).read_bytes()  # read once; the copy and the digest use these bytes
        digest = hashlib.sha256(data).hexdigest()
        expected = expected_for(rel_src)
        if expected is not None and digest != expected:
            reasons.append(f"{rel_dst} changed after its measurement")
        target = dest / rel_dst
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        if sha_file(target) != digest:
            reasons.append(f"{rel_dst} differs from the bytes read for the package")
        item = {"role": role, "path": rel_dst, "sha256": digest, "size_bytes": len(data)}
        if layer:
            item["layer"] = layer
        outputs.append(item)
        return item

    contract, layers = export_from_bytes(consumed["manufacturing/export.yaml"])
    for layer in contract["layers"]:
        src = design_dir / "export" / ("board" + layer["suffix"])
        if not src.is_file():
            reasons.append(f"missing export file {src.name}")
            continue
        out_item(src, f"gerber/board{layer['suffix']}", role_of(layer["role"]), layer["kicad_layer"])
    for suffix, role in (("-PTH.drl", "drill_plated"), ("-NPTH.drl", "drill_nonplated")):
        src = design_dir / "export" / ("board" + suffix)
        if src.is_file():
            out_item(src, f"gerber/board{suffix}", role)
        else:
            reasons.append(f"missing drill file board{suffix}")
    out_item(design_dir / "export" / "schematic.pdf", "docs/schematic.pdf", "schematic_pdf")
    out_item(design_dir / "fabrication-drawing.pdf", "docs/fabrication.pdf", "fabrication_drawing")
    out_item(design_dir / "design-result.json", "reports/design-result.json", "report")
    out_item(supplier_dir / "supplier-result.json", "reports/supplier-result.json", "report")
    out_item(supplier_dir / "supplier-drc.json", "reports/supplier-drc.json", "report")
    out_item(design_dir / "inventory.json", "reports/inventory.json", "report")
    obs_path = review_path.parent / "observations.json"
    if review_bytes is not None and obs_path.is_file():
        review_obs = json.loads(review_bytes).get("observations_file_sha256")
        if review_obs != sha_file(obs_path):
            reasons.append("the observation file differs from the review record")
        out_item(obs_path, "reports/observations.json", "report")
    else:
        reasons.append("the observation file is missing")
    if supplier_result.get("manual"):
        out_item(supplier_dir / "manual-evidence.json", "reports/manual-evidence.json", "report")
        out_item(supplier_dir / "manual-artifact.txt", "reports/manual-artifact.txt", "report")
    if review_bytes is not None:
        out_item(review_path, "reports/REVIEW.json", "report")
    evidence_page = PAGES_OF(profile)
    out_item(evidence_page, "evidence/supplier-page.html", "report")
    inputs = []
    for role, rel in VAL.FIXED_INPUT_PATHS.items():
        if consumed.get(rel) is not None:
            inputs.append({"role": role, "path": rel, "sha256": hashlib.sha256(consumed[rel]).hexdigest()})
    inputs.append({"role": "supplier_rules", "path": "out/fab/supplier/work/kicad/board.kicad_dru",
                   "sha256": supplier_result["effective"]["board.kicad_dru"]})
    inputs.append({"role": "supplier_settings", "path": "out/fab/supplier/work/kicad/board.kicad_pro",
                   "sha256": supplier_result["effective"]["board.kicad_pro"]})
    current = snapshot(project, {"profile": profile_path})
    if design_result.get("source_sha256") != current:
        reasons.append("the design result is stale: a source file changed after the design run")
    if supplier_result.get("source_sha256") != supplier_inputs_now(project, profile_path, supplier_result):
        reasons.append("the supplier result is stale: a source file changed after the supplier run")
    if supplier_result.get("design_binding") != sha_file(design_dir / "design-result.json"):
        reasons.append("the supplier result does not bind this design result")
    for label, result_obj, base, bind_name in (
            ("design", design_result, design_dir, "design-binding.json"),
            ("supplier", supplier_result, supplier_dir, "supplier-binding.json")):
        bind_path = base / bind_name
        if not bind_path.is_file():
            reasons.append(f"the {label} binding file is missing")
            continue
        if result_obj.get("binding_sha256") != sha_file(bind_path):
            reasons.append(f"the {label} result does not bind the current {bind_name}")
        binding = json.loads(bind_path.read_text())
        for rel, digest in binding.get("outputs", {}).items():
            if not (base / rel).is_file() or sha_file(base / rel) != digest:
                reasons.append(f"the {label} output {rel} changed after its binding")
    if supplier_result.get("manual"):
        art = project / supplier_result["manual"]["artifact_path"]
        if not art.is_file() or sha_file(art) != supplier_result["manual"]["artifact_sha256"]:
            reasons.append("the manual artifact changed after its measurement")
    checks, evidence_items = [], []
    if consumed["manufacturing/supplier.yaml"] != consumed["profile"]:
        reasons.append("the project supplier record differs from the profile")
    for check_id in VAL.BARE_CHECKS:
        status, detail = check_status(check_id, design_result, supplier_result, gate_problems, project, profile, design_dir, contract)
        if status != "pass":
            reasons.append(f"{check_id}: {detail}")
        art = None
        if check_id == "fab.profile_evidence":
            art = next(o for o in outputs if o["path"] == "evidence/supplier-page.html")
        else:
            art = out_item_text(dest, evidence_dir, check_id, detail, outputs)
        listed = [{"path": m["path"], "sha256": m["sha256"]} for role in VAL.CHECK_INPUT_ROLES[check_id]
                  for m in inputs if m["role"] == role]
        evidence = {"schema_id": "cad-skills/evidence", "schema_version": "1.0", "check_id": check_id,
                    "status": status, "method": "tool", "tool": {"name": "pcb-fab-package", "version": "1"},
                    "inputs": listed, "artifact": {"path": art["path"], "sha256": art["sha256"]}}
        ev = out_item_json(dest, evidence_dir, check_id, evidence, outputs)
        checks.append({"id": check_id, "status": status, "evidence_path": ev["path"], "evidence_sha256": ev["sha256"]})
    board_record = VAL.parse_record(consumed["board.yaml"], ".yaml", "board.yaml")
    manifest = {"schema_id": "cad-skills/manifest", "schema_version": "1.0", "release_id": release,
                "kind": "bare_board", "board_revision": board_record["release_revision"],
                "board_sha256": hashlib.sha256(consumed["kicad/board.kicad_pcb"]).hexdigest(),
                "variant": board_record["variant"],
                "supplier": board_record["supplier"],
                "inputs": inputs, "outputs": outputs, "drill_applicability": [], "checks": checks,
                "status": "qualified" if not reasons else "draft",
                "reasons": [{"code": "pkg.reason", "text": text} for text in sorted(set(reasons))],
                "tool_versions": {"kicad": design_result["runtime"]["kicad_version"]}}
    (dest / "manifest.json").write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
    manifest_path = dest / "manifest.json"
    for _ in range(2):
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        _, report = VAL.build_report([str(manifest_path)], SCHEMAS, project, dest)
        if report["findings"]:
            manifest["status"] = "draft"
            manifest["reasons"] = [{"code": "pkg.reason", "text": text} for text in sorted(set(reasons))] + [
                {"code": "pkg.validator", "text": f"{f['code']} at {f['location']}"} for f in report["findings"]]
            manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
            _, report = VAL.build_report([str(manifest_path)], SCHEMAS, project, dest)
            break
    clean = not report["findings"]
    gate = final_gate(project, profile_path, design_dir, supplier_dir, design_result, supplier_result)
    if gate:
        manifest["status"] = "draft"
        manifest["reasons"] = manifest["reasons"] + [{"code": "pkg.final_gate", "text": text} for text in gate]
        manifest_path.write_text(json.dumps(manifest, indent=2, sort_keys=True) + "\n")
        clean = False
    PIO.publish_dir(project, dest, final)
    code = EXIT_OK if (manifest["status"] == "qualified" and clean) else EXIT_FAIL
    return code, manifest


def PAGES_OF(profile):
    return fab.PAGES / f"{next(iter(fab.PROFILE_PAGES[profile['id']]))}.html"


def role_of(name):
    return {"copper_top": "copper", "copper_bottom": "copper", "mask_top": "mask", "mask_bottom": "mask",
            "silk_top": "silk", "silk_bottom": "silk", "paste_top": "paste", "paste_bottom": "paste",
            "outline": "outline"}[name]


def check_status(check_id, design_result, supplier_result, gate_problems, project, profile, design_dir, contract):
    if check_id == "design.erc":
        ok = design_result["erc"]["counts"]["violations"] == 0
        return ("pass" if ok else "fail"), "ERC violations are present" if not ok else "no ERC violations"
    if check_id == "design.drc":
        c = design_result["drc"]["counts"]
        ok = c["violations"] == 0 and c["unconnected"] == 0
        return ("pass" if ok else "fail"), "DRC violations are present" if not ok else "no DRC violations"
    if check_id == "design.parity":
        ok = design_result["drc"]["counts"]["parity"] == 0
        return ("pass" if ok else "fail"), "schematic parity differences are present" if not ok else "no parity differences"
    if check_id == "fab.profile_evidence":
        ok = sha_file(PAGES_OF(profile)) == profile["evidence_sha256"]
        return ("pass" if ok else "fail"), "the stored page hash differs" if not ok else "stored page matches"
    if check_id == "fab.export_inventory":
        expected = {"board" + layer["suffix"] for layer in contract["layers"]}
        expected |= {"board-PTH.drl", "board-NPTH.drl"}
        found = {p.name for p in (design_dir / "export").iterdir() if p.is_file()}
        ok = expected <= found
        return ("pass" if ok else "fail"), "every expected export file is present" if ok else f"missing {sorted(expected - found)}"
    if check_id == "fab.layer_order":
        copper = json.loads((design_dir / "inventory.json").read_text())["copper_layers"]
        problems = semantics.function_problems(contract, design_dir / "export", copper)
        return ("pass" if not problems else "fail"), "; ".join(problems) or "every layer declares its exact function"
    if check_id == "fab.drill_split":
        inventory = json.loads((design_dir / "inventory.json").read_text())
        problems = semantics.drill_problems(inventory, design_dir / "export")
        return ("pass" if not problems else "fail"), "; ".join(problems) or "drill holes match the saved board"
    if check_id == "fab.supplier_rules":
        ok = supplier_result["exit"] == 0 and not gate_problems
        return ("pass" if ok else "fail"), "supplier conditions are not all passing" if not ok else "all conditions pass"
    return "fail", "unknown check"


def out_item_text(dest, evidence_dir, check_id, detail, outputs):
    target = dest / "reports" / f"{check_id}.txt"
    target.write_text(f"report of {check_id}: {detail}\n")
    item = {"role": "report", "path": f"reports/{check_id}.txt", "sha256": sha_file(target),
            "size_bytes": target.stat().st_size}
    outputs.append(item)
    return item


def out_item_json(dest, evidence_dir, check_id, record, outputs):
    target = evidence_dir / f"{check_id}.json"
    target.write_text(json.dumps(record, indent=2, sort_keys=True) + "\n")
    item = {"role": "evidence", "path": f"evidence/{check_id}.json", "sha256": sha_file(target),
            "size_bytes": target.stat().st_size}
    outputs.append(item)
    return item


def design(project, profile_path, out):
    """Hold the project lock for the whole design operation, including its writes."""
    try:
        with PIO.project_lock(project, "design"):
            return _design(project, profile_path, out)
    except (PIO.LockHeld, PIO.LockMalformed) as err:
        raise Stop(EXIT_UNSUPPORTED, f"the project is locked: {err}")


def supplier(project, profile_path, out, design_dir, manual_path=None):
    """Hold the project lock for the whole supplier operation."""
    try:
        with PIO.project_lock(project, "supplier"):
            return _supplier(project, profile_path, out, design_dir, manual_path)
    except (PIO.LockHeld, PIO.LockMalformed) as err:
        raise Stop(EXIT_UNSUPPORTED, f"the project is locked: {err}")


def package(project, profile_path, release, review_path, dest, design_dir, supplier_dir, expected_review_sha):
    """Hold the project lock through the final freshness and validation gates and the publication."""
    try:
        with PIO.project_lock(project, "package"):
            return _package(project, profile_path, release, review_path, dest, design_dir, supplier_dir, expected_review_sha)
    except (PIO.LockHeld, PIO.LockMalformed) as err:
        raise Stop(EXIT_UNSUPPORTED, f"the project is locked: {err}")
