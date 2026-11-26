# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///

"""The design, supplier and package commands of pcb-fab-package.

Every KiCad command runs in the accepted image through podman with no network. Each command works on a copy of
the project. The project files are hashed before and after the run. A change to a source file is exit 1.

Every output file is written through write_out. That helper confines the complete destination and then replaces
it atomically. A package is published only after the final gate passes.

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
import tempfile
from decimal import Decimal
from fractions import Fraction

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validate as VAL  # noqa: E402
import fab  # noqa: E402
import inspect_slots  # noqa: E402
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
# The exact factor of each supported unit to millimeters, as a fraction. The rule text is exact.
RULE_UNIT_MM = {"mm": Fraction(1), "mil": Fraction(127, 5000), "in": Fraction(127, 5)}


def violations_for(counts, key):
    """The number of violations of one supplier rule, counted by every report key of that rule."""
    return sum(counts.get(name, 0) for name in REPORT_KEYS[key])


SOURCE_FILES = ("kicad/board.kicad_pcb", "kicad/board.kicad_sch", "kicad/board.kicad_pro")
INPUT_RECORDS = ("board.yaml", "manufacturing/export.yaml", "manufacturing/supplier.yaml", "toolchain.lock.json")
# The design outputs that the supplier measurements read. Each one is checked against the design binding.
MEASURE_INPUTS = ("inventory.json", "export/board-PTH.drl", "export/board-NPTH.drl",
                  "export/board-F_Mask.gbr", "export/board-B_Mask.gbr")
SILK_INPUT = "export/board-F_Silkscreen.gbr"


class Stop(Exception):
    def __init__(self, code, message):
        super().__init__(message)
        self.code = code


def sha(data):
    """The SHA-256 of bytes."""
    return hashlib.sha256(data).hexdigest()


def sha_file(path):
    return sha(pathlib.Path(path).read_bytes())


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
    return {key: (sha(value) if value is not None else "absent") for key, value in data.items()}


def snapshot(project, extra=None):
    """The SHA-256 of every consumed input, from one read of each file."""
    return digest(captured(project, extra))


class Reader:
    """Read each file once per operation. Later uses get the same bytes, so the decision and the copy agree."""

    def __init__(self):
        self.cache = {}

    def bytes(self, path):
        key = str(path)
        if key not in self.cache:
            self.cache[key] = pathlib.Path(path).read_bytes()
        return self.cache[key]

    def optional(self, path):
        return self.bytes(path) if pathlib.Path(path).is_file() else None


def podman(stage, argv, worker=None):
    cmd = ["podman", "run", "--rm", "--pull=never", "--network", "none", "--security-opt", "label=disable",
           "-w", "/work", "-v", f"{stage}:/work"]
    if worker is not None:
        cmd += ["-v", f"{worker}:/worker:ro"]
    proc = subprocess.run(cmd + [RUN_IMAGE] + argv, capture_output=True, text=True)
    return proc.returncode, proc.stdout, proc.stderr


def confine(project, out):
    """Every write of a command stays under the project's out/fab tree. Refuse a link or an escape.

    The check covers the path itself and each parent up to the project root."""
    root = (project / "out" / "fab").resolve()
    target = out.resolve()
    if target != root and root not in target.parents:
        raise Stop(EXIT_UNSUPPORTED, f"the path {out} is outside out/fab")
    for part in [out] + list(out.parents):
        if part.is_symlink():
            raise Stop(EXIT_UNSUPPORTED, f"the path {out} contains a symbolic link")
        if part == project:
            break


def refuse_links(project, paths):
    """Refuse a planned destination that is a link, or that lies outside out/fab, before any write."""
    for path in paths:
        confine(project, path)
        if os.path.islink(path):
            raise Stop(EXIT_UNSUPPORTED, f"the destination {path} is a symbolic link; nothing is written")


def write_out(project, path, data):
    """Write one output file. Confine the complete destination, then replace it atomically.

    A link at the file itself is refused. A directory check alone is not enough."""
    confine(project, path)
    PIO.atomic_write(project, path, data)


class Outputs:
    """The files that one command writes. Each entry keeps the digest of the bytes that were written."""

    def __init__(self, project, base):
        self.project = project
        self.base = base
        self.items = {}

    def write(self, path, data):
        write_out(self.project, path, data)
        self.items[path.relative_to(self.base).as_posix()] = sha(data)
        return data

    def digests(self, names):
        return {name: self.items[name] for name in names if name in self.items}


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


def profile_from_bytes(project, raw, scratch):
    """Parse the profile from the captured bytes. The scratch copy holds the same bytes.

    The scratch file is written through write_out, so its complete path is confined before the write."""
    confine(project, scratch)
    scratch.mkdir(parents=True, exist_ok=True)
    write_out(project, scratch / "profile.yaml", raw)
    return fab.check_profile(scratch / "profile.yaml")


def export_from_bytes(raw):
    """The export contract and its layer list, parsed from the captured bytes."""
    contract = VAL.parse_record(raw, ".yaml", "export.yaml")
    return contract, [layer["kicad_layer"] for layer in contract["layers"]]


def stage_project(project, stage, extra=None):
    return stage_from(captured(project, extra), stage)


def stage_from(data, stage):
    """Stage the captured bytes of the KiCad files and return the digests of the same bytes.

    The stage is a private execution directory. An old stage is removed, and a stage without the marker is refused."""
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


def read_json_once(path):
    """Read one JSON file. Return (raw bytes, parsed value). Raise Stop when the file is absent or invalid."""
    try:
        raw = pathlib.Path(path).read_bytes()
    except OSError as err:
        raise Stop(EXIT_TOOL, f"KiCad produced no readable report {path.name}: {err}")
    try:
        return raw, json.loads(raw)
    except ValueError as err:
        raise Stop(EXIT_TOOL, f"KiCad produced no readable report {path.name}: {err}")


def read_required(path):
    """Read one design output that the supplier needs. Raise Stop when it is absent."""
    if not path.is_file():
        raise Stop(EXIT_FAIL, f"the design output {path.name} is missing")
    return path.read_bytes()


def check_result_content(result):
    """A design result must hold the hash of its own content. Raise Stop when the content differs."""
    body = {key: value for key, value in result.items() if key != "content_sha256"}
    if result.get("content_sha256") != VAL.canonical_hash(body):
        raise Stop(EXIT_FAIL, "the design result content differs from its content hash")


def write_result(path, record):
    """Write a result file through the confined helper. The project is four levels above the result."""
    project = path.parents[3]  # <project>/out/fab/<step>/<file>
    write_out(project, path, (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8"))


def design_destinations(out, contract):
    """The fixed destinations of the design command. Each one is refused when it is a link."""
    names = ["erc.json", "drc.json", "inventory.json", "drawing-facts.json", "fabrication-drawing.pdf",
             "design-binding.json", "design-result.json", "captured/profile.yaml", "logs/erc.stderr",
             "logs/drc.stderr", "logs/inventory.stderr", "export/board-PTH.drl", "export/board-NPTH.drl",
             "export/schematic.pdf", "export/layers.pdf"]
    names += [f"logs/export-{name}.stderr" for name in ("gerbers", "drill", "layers_pdf", "schematic_pdf")]
    names += [f"export/board{layer['suffix']}" for layer in contract["layers"]]
    return [out / name for name in names]


def supplier_destinations(out):
    """The fixed destinations of the supplier command."""
    names = ["slots.json", "mask.json", "mask-bottom.json", "supplier.kicad_dru", "supplier.kicad_pro",
             "supplier-drc.json", "supplier-drc.stderr", "manual-artifact.txt", "manual-evidence.json",
             "supplier-binding.json", "supplier-result.json", "captured/profile.yaml", "measure",
             "via-report.json", "via.stderr", "corner-report.json", "corner.stderr"]
    return [out / name for name in names]


SLOT_CLASSES = {"pth": "PTH", "npth": "NPTH"}


def supplier_rules_text(profile):
    """The generated KiCad rules, one per supplier limit that KiCad checks. Values are exact decimals in mm."""
    lines = ['(version 1)']
    for key in sorted(profile["division"]["kicad_dru"]):
        if key not in RULE_CONSTRAINT:
            raise Stop(EXIT_UNSUPPORTED, f"the rule {key} has no KiCad constraint. Remove it from division.kicad_dru.")
        limit = profile["limits"][key]
        unit = limit.get("unit")
        if not isinstance(unit, str) or unit not in RULE_UNIT_MM:
            raise Stop(EXIT_UNSUPPORTED, f"the rule {key} has the unsupported unit {unit!r}. Use mm, mil or in.")
        number = _limit_number(limit["value"])
        if number is None:
            raise Stop(EXIT_UNSUPPORTED, f"the rule {key} must have a finite value greater than 0.")
        try:
            text = fab.mm_text(number * RULE_UNIT_MM[unit])
        except ValueError:
            raise Stop(EXIT_UNSUPPORTED, f"the value of the rule {key} is not a terminating decimal.")
        lines.append(f'(rule "supplier_{key}" (constraint {RULE_CONSTRAINT[key]} (min {text}mm)))')
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


# The division names that the workflow measures. Each profile must have all five of them.
GEOMETRIC_ROWS = ("board_min_edge", "board_max_width", "board_max_height", "min_slot_size", "mask_web_min")
CORE_KICAD_DRU = ("min_trace", "min_space", "min_annular_ring", "min_drill", "edge_keepout")
MASK_SIDE_ROWS = ("mask_web_min_top", "mask_web_min_bottom")
# These rows come from the extensions and the measurements, not from a limit.
FIXED_ROWS = ("service.layers", "service.order_multiple", "service.via_construction_prohibited",
              "process.outline_tool_compatibility", "process.cutout_tool_compatibility")
MANUAL_KINDS = ("minimum", "maximum", "recommendation")
PENDING_TEXT = "Give manual evidence. The row stays pending until then."
FINDING_TEXT = "recommendation: reported, never a failure"


def manual_conditions(profile):
    """The mandatory and optional manual-evidence names, in division order."""
    mandatory, optional = [], []
    for key in profile["division"].get("manual_evidence", []):
        kind = profile["limits"].get(key, {}).get("kind")
        if kind in ("minimum", "maximum"):
            mandatory.append(key)
        elif kind == "recommendation":
            optional.append(key)
    return tuple(mandatory), tuple(optional)


def optional_conditions(profile):
    """The optional manual-evidence names of the profile."""
    return manual_conditions(profile)[1]


def manual_rows(profile, silk_row):
    """The manual-evidence rows in division order. A minimum or a maximum without a procedure is pending, thus the result stays fail-closed."""
    mandatory, optional = manual_conditions(profile)
    rows = []
    for key in mandatory:
        rows.append(silk_row if key == "silk_line_min_short_text" else
                    {"condition": key, "method": "manual_evidence", "mandatory": True, "status": "pending",
                     "interpretation": PENDING_TEXT})
    for key in optional:
        rows.append({"condition": key, "method": "manual_evidence", "mandatory": False, "status": "finding",
                     "interpretation": FINDING_TEXT})
    return rows


def _limit_number(value):
    """The exact number of a limit value, or None when the value is not a finite number greater than 0.

    Decimal refuses the slash form "1/0" and "1/3". A decimal string stays exact. A float value is already
    rounded before this function sees it."""
    try:
        decimal_value = Decimal(str(value))
    except (ValueError, TypeError, ArithmeticError):
        return None
    if not decimal_value.is_finite() or decimal_value <= 0:
        return None
    return Fraction(decimal_value)


def check_division(profile):
    """Stop a division that the workflow cannot measure. Each profile must have the five geometric tests
    and the five core KiCad rules."""
    division = profile["division"]
    dru = division.get("kicad_dru", [])
    geometric = division.get("geometric_tests", [])
    for key in dru:
        if key not in RULE_CONSTRAINT:
            raise Stop(EXIT_UNSUPPORTED, f"the rule {key} has no KiCad constraint. Remove it from division.kicad_dru.")
    for key in dru:
        if key not in REPORT_KEYS:
            raise Stop(EXIT_UNSUPPORTED, f"the rule {key} has no DRC report keys. Remove it from division.kicad_dru.")
    for key in geometric:
        if key not in GEOMETRIC_ROWS:
            raise Stop(EXIT_UNSUPPORTED, f"the geometric test {key} has no workflow measurement. Remove it from division.geometric_tests.")
    if division.get("project_settings"):
        raise Stop(EXIT_UNSUPPORTED, "the workflow cannot apply division.project_settings. Remove the keys "
                   f"{sorted(division['project_settings'])}.")
    for section, names, required in (("geometric_tests", geometric, GEOMETRIC_ROWS),
                                     ("kicad_dru", dru, CORE_KICAD_DRU)):
        for name in required:
            if name not in names:
                raise Stop(EXIT_UNSUPPORTED, f"the profile has no {name} in division.{section}. "
                           "The workflow must examine this limit. Add it to the profile.")
    for section in ("geometric_tests", "kicad_dru"):
        for key in division.get(section, []):
            if _limit_number(profile["limits"].get(key, {}).get("value")) is None:
                raise Stop(EXIT_UNSUPPORTED, f"the limit {key} must have a finite value greater than 0.")
    manual = division.get("manual_evidence", [])
    if ("silk_line_min_short_text" not in manual
            or profile["limits"].get("silk_line_min_short_text", {}).get("kind") != "minimum"):
        raise Stop(EXIT_UNSUPPORTED, "the profile has no silk_line_min_short_text in division.manual_evidence "
                   "with the kind minimum. The workflow must examine this limit. Add it to the profile.")
    for key in manual:
        kind = profile["limits"].get(key, {}).get("kind")
        if kind not in MANUAL_KINDS:
            raise Stop(EXIT_UNSUPPORTED, f"the manual-evidence limit {key} has the kind {kind!r}. "
                       "Use minimum, maximum or recommendation.")
    if profile["extensions"].get("service.order_multiple", {}).get("kind") == "not_stated":
        raise Stop(EXIT_UNSUPPORTED, "The profile states no order multiple. The workflow cannot examine the order quantity.")
    return None


def rows_exit(rows):
    """The supplier exit from the rows, with the existing precedence.

    A pending or uncertain mandatory row gives EXIT_FAIL. A failing mandatory row gives EXIT_FAIL. Otherwise EXIT_OK."""
    mandatory = [r for r in rows if r["mandatory"]]
    if any(r["status"] == "pending" for r in mandatory) or any(r["status"] == "uncertain" for r in mandatory):
        return EXIT_FAIL
    if any(r["status"] == "fail" for r in mandatory):
        return EXIT_FAIL
    return EXIT_OK


def mandatory_conditions(profile):
    """The mandatory condition names that the selected profile requires."""
    division = profile["division"]
    return (set(division["kicad_dru"]) | set(division["geometric_tests"]) | set(MASK_SIDE_ROWS) | set(FIXED_ROWS)
            | set(manual_conditions(profile)[0]))


def validate_supplier_result(result, profile):
    """Refuse a supplier result whose content, profile, rows or exit are inconsistent. Return the result.

    The content hash detects a change. It is not a signature. It does not prove who wrote the result."""
    body = {key: value for key, value in result.items() if key != "content_sha256"}
    if result.get("content_sha256") != VAL.canonical_hash(body):
        raise Stop(EXIT_FAIL, "the supplier result content differs from its content hash")
    if result.get("profile") != profile["id"] or result.get("profile_sha256") != profile["content_sha256"]:
        raise Stop(EXIT_FAIL, "the supplier result names another profile")
    rows = result.get("rows")
    if not isinstance(rows, list) or not rows:
        raise Stop(EXIT_FAIL, "the supplier result has no rows")
    names = [row.get("condition") for row in rows]
    if len(names) != len(set(names)):
        raise Stop(EXIT_FAIL, "the supplier result repeats a condition")
    for row in rows:
        if row.get("mandatory") is True:
            if row.get("status") not in ("pass", "fail", "uncertain", "pending"):
                raise Stop(EXIT_FAIL, f"the supplier row {row.get('condition')} has an invalid status")
        elif row.get("mandatory") is False:
            if row.get("condition") not in optional_conditions(profile) or row.get("status") != "finding":
                raise Stop(EXIT_FAIL, f"the supplier row {row.get('condition')} is not a recommendation")
        else:
            raise Stop(EXIT_FAIL, f"the supplier row {row.get('condition')} has no mandatory flag")
    mandatory_seen = {row["condition"] for row in rows if row["mandatory"] is True}
    expected = mandatory_conditions(profile)
    if mandatory_seen != expected:
        missing, extra = sorted(expected - mandatory_seen), sorted(mandatory_seen - expected)
        raise Stop(EXIT_FAIL, f"the supplier result has missing mandatory rows {missing} or extra rows {extra}")
    if result.get("exit") != rows_exit(rows):
        raise Stop(EXIT_FAIL, "the supplier result exit differs from its rows")
    return result


def _design(project, profile_path, out):
    """Run ERC, DRC with parity, the exports, the slot inventory and the drawing. Return (exit, result)."""
    consumed = captured(project, {"profile": profile_path})
    confine(project, out)
    for child in ("export", "logs", "work", "captured"):
        confine(project, out / child)
    contract, layers = export_from_bytes(consumed["manufacturing/export.yaml"])
    refuse_links(project, design_destinations(out, contract))
    outputs = Outputs(project, out)
    profile = profile_from_bytes(project, consumed["profile"], out / "captured")
    outputs.items["captured/profile.yaml"] = sha(consumed["profile"])
    check_division(profile)
    runtime = runtime_identity(consumed["toolchain.lock.json"])
    stage = out / "work"
    before = stage_from(consumed, stage)
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
    outputs.write(logs / "erc.stderr", err_erc.encode())
    outputs.write(logs / "drc.stderr", err_drc.encode())
    erc_raw, erc = read_json_once(stage / "erc.json")
    drc_raw, drc = read_json_once(stage / "drc.json")
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
        outputs.write(logs / f"export-{name}.stderr", err.encode())
        if rc_exports[name] != 0:
            raise Stop(EXIT_TOOL, f"the export {name} failed with exit {rc_exports[name]}")
    worker_rc, worker_out, worker_err = podman(stage, ["/usr/bin/python3", "/worker/board_inventory_slots.py",
                                                       "/work/kicad/board.kicad_pcb"], worker=HERE)
    outputs.write(logs / "inventory.stderr", worker_err.encode())
    if worker_rc == 2:
        raise Stop(EXIT_UNSUPPORTED, "the inventory refuses the board: " + worker_out.strip())
    if worker_rc != 0:
        raise Stop(EXIT_TOOL, f"the inventory worker failed with exit {worker_rc}")
    inventory = json.loads(worker_out)
    outputs.write(out / "inventory.json", (json.dumps(inventory, indent=1, sort_keys=True) + "\n").encode())
    outputs.write(out / "erc.json", erc_raw)
    outputs.write(out / "drc.json", drc_raw)
    if (stage / "export").is_dir():
        for name in sorted(p.name for p in (stage / "export").iterdir()):
            outputs.write(exp / name, (stage / "export" / name).read_bytes())
    counts_erc = findings(erc)
    counts_drc = findings(drc)
    after = source_hashes(project, {"profile": profile_path})
    if after != before:
        raise Stop(EXIT_FAIL, "the source files changed during the design run")
    fact_obj = fab.drawing_facts(inventory, profile, consumed["kicad/board.kicad_pcb"],
                                 "design-run", consumed["manufacturing/supplier.yaml"])
    outputs.write(out / "drawing-facts.json", (json.dumps(fact_obj, indent=2, sort_keys=True) + "\n").encode())
    outputs.write(out / "fabrication-drawing.pdf", fab.drawing_pdf(fact_obj))
    result = {"schema_id": "pcb-fab-package/design-result", "schema_version": 1,
              "tool": {"kicad": runtime["kicad_version"], "image_id": runtime["image_id"]},
              "erc": {"exit": rc_erc, "counts": counts_erc},
              "drc": {"exit": rc_drc, "counts": counts_drc},
              "exports": {k: v for k, v in rc_exports.items()},
              "source_sha256": before, "runtime": runtime,
              "inputs": {rel: sha(consumed[rel]) for rel in INPUT_RECORDS if consumed[rel] is not None},
              "outputs": dict(sorted(outputs.items.items()))}
    code = EXIT_OK
    if counts_erc["violations"] or counts_drc["violations"] or counts_drc["unconnected"] or counts_drc["parity"]:
        code = EXIT_FAIL
    result["exit"] = code
    binding = {"schema_id": "pcb-fab-package/design-binding", "schema_version": 1,
               "snapshot": before, "outputs": result["outputs"]}
    binding_bytes = (json.dumps(binding, indent=2, sort_keys=True) + "\n").encode("utf-8")
    PIO.atomic_write(project, out / "design-binding.json", binding_bytes)
    result["binding_sha256"] = sha(binding_bytes)
    result["content_sha256"] = VAL.canonical_hash(result)
    write_result(out / "design-result.json", result)
    return code, result


def via_condition(profile, declaration, measured):
    """Compare measured spans and the declared process with the supplier prohibition."""
    if declaration not in (None, "unconfirmed", "standard_through", "filled_plated_via_in_pad"):
        raise Stop(EXIT_UNSUPPORTED, "extensions.fabrication.via_process is invalid. Select a supported process.")
    prohibited = profile["extensions"]["service.via_construction_prohibited"]
    vias = measured["vias"]
    refused = [item for item in vias if item["construction"] in prohibited]
    if refused or declaration in prohibited:
        status = "fail"
        text = "The measured span or declared process is prohibited by the supplier."
    elif not vias:
        status = "pass"
        text = "The board has no vias. The measured count is zero."
    elif declaration in (None, "unconfirmed"):
        status = "pending"
        text = "Declare the requested process in extensions.fabrication.via_process."
    elif all(item["construction"] == "through" for item in vias):
        status = "pass"
        text = "The measured spans are through spans. The declared process is standard_through."
    else:
        raise Stop(EXIT_UNSUPPORTED, "The via span has no supported supplier interpretation.")
    return {"condition": "service.via_construction_prohibited", "method": "board_measurement_and_declaration",
            "mandatory": True, "status": status, "interpretation": text,
            "declaration": declaration, "via_count": len(vias), "prohibited_spans": refused}


def measure_vias(consumed, out, outputs, runtime, profile):
    """Measure a private board copy and bind the worker, image and board bytes."""
    board_record = VAL.parse_record(consumed["board.yaml"], ".yaml", "board.yaml")
    extensions = board_record.get("extensions", {})
    if not isinstance(extensions, dict):
        raise Stop(EXIT_UNSUPPORTED, "The board extensions must be an object.")
    fabrication = extensions.get("fabrication", {})
    if not isinstance(fabrication, dict):
        raise Stop(EXIT_UNSUPPORTED, "extensions.fabrication must be an object.")
    declaration = fabrication.get("via_process")
    if declaration not in (None, "unconfirmed", "standard_through", "filled_plated_via_in_pad"):
        raise Stop(EXIT_UNSUPPORTED, "extensions.fabrication.via_process is invalid. Select a supported process.")
    worker = (HERE / "via_inventory.py").read_bytes()
    with tempfile.TemporaryDirectory(prefix="via-", dir=out) as directory:
        stage = pathlib.Path(directory)
        (stage / "board.kicad_pcb").write_bytes(consumed["kicad/board.kicad_pcb"])
        (stage / "worker.py").write_bytes(worker)
        code, stdout, stderr = podman(stage, ["python3", "/work/worker.py", "/work/board.kicad_pcb"])
    outputs.write(out / "via.stderr", stderr.encode())
    if code:
        raise Stop(EXIT_UNSUPPORTED if code == 2 else EXIT_TOOL, f"The via measurement failed with exit {code}: {stdout}")
    try:
        measured = json.loads(stdout)
        if measured["board_sha256"] != sha(consumed["kicad/board.kicad_pcb"]):
            raise ValueError("The measured board hash differs from the captured hash.")
        row = via_condition(profile, declaration, measured)
    except (ValueError, KeyError, TypeError) as err:
        raise Stop(EXIT_TOOL, f"The via report is invalid: {err}")
    report = {"measurement": measured, "row": row, "worker_sha256": sha(worker), "runtime": runtime,
              "board_record_sha256": sha(consumed["board.yaml"])}
    outputs.write(out / "via-report.json", (json.dumps(report, indent=2, sort_keys=True) + "\n").encode())
    return row


def corner_conditions(profile, measured):
    """Compare exact corner radii with radii derived from the published cutter diameters.

    The cutter diameter can be in mm, mil or in. The tool radius is exact in nanometers."""
    rows = []
    corners = measured["corners"]
    for corner in corners:
        if (corner.get("location") not in ("outline", "cutout")
                or type(corner.get("radius_nm")) is not int or corner["radius_nm"] < 0):
            raise Stop(EXIT_TOOL, "The corner report has an invalid location or radius.")
    pages = profile["extensions"]["evidence_pages"].values()
    for location in ("outline", "cutout"):
        key = f"process.{location}_cutter_diameter"
        fact = profile["extensions"].get(key)
        if not isinstance(fact, dict) or not isinstance(fact.get("unit"), str) or fact["unit"] not in fab.UNIT_MM:
            raise Stop(EXIT_UNSUPPORTED, f"The profile has no supported cutter fact for {location}.")
        if not any(page["sha256"] == fact.get("source_sha256") and page["source_url"] == fact.get("source_url") for page in pages):
            raise Stop(EXIT_UNSUPPORTED, f"The cutter fact for {location} has no matching source binding.")
        try:
            tool_radius = Fraction(str(fact["value"])) * fab.UNIT_MM[fact["unit"]] * 1000000 / 2
        except (ValueError, KeyError, ZeroDivisionError):
            raise Stop(EXIT_UNSUPPORTED, f"The cutter diameter for {location} is invalid.")
        if tool_radius <= 0 or tool_radius.denominator != 1:
            raise Stop(EXIT_UNSUPPORTED, f"The cutter radius for {location} has no positive integer nanometer value.")
        selected = [item for item in corners if item["location"] == location]
        rows.append({"condition": f"process.{location}_tool_compatibility", "mandatory": True,
                     "method": "derived_tool_compatibility", "status": "pass" if all(item["radius_nm"] >= tool_radius for item in selected) else "fail",
                     "interpretation": "The corner radius must fit the derived circular tool radius. This is not a quoted supplier minimum.",
                     "process_fact": fact, "derivation": "tool radius = published cutter diameter / 2",
                     "tool_radius_nm": int(tool_radius), "measured_corners": selected})
    return rows


def measure_corners(consumed, out, outputs, runtime, profile):
    """Measure recognized Edge.Cuts geometry from a private copy of the captured board."""
    worker = (HERE / "corner_inventory.py").read_bytes()
    with tempfile.TemporaryDirectory(prefix="corners-", dir=out) as directory:
        stage = pathlib.Path(directory)
        (stage / "board.kicad_pcb").write_bytes(consumed["kicad/board.kicad_pcb"])
        (stage / "worker.py").write_bytes(worker)
        code, stdout, stderr = podman(stage, ["python3", "/work/worker.py", "/work/board.kicad_pcb"])
    outputs.write(out / "corner.stderr", stderr.encode())
    if code:
        raise Stop(EXIT_UNSUPPORTED if code == 2 else EXIT_TOOL, f"The corner measurement failed with exit {code}: {stdout}")
    try:
        measured = json.loads(stdout)
        if measured["board_sha256"] != sha(consumed["kicad/board.kicad_pcb"]):
            raise ValueError("The corner report names different board bytes.")
        rows = corner_conditions(profile, measured)
    except (ValueError, KeyError, TypeError) as err:
        raise Stop(EXIT_TOOL, f"The corner report is invalid: {err}")
    report = {"measurement": measured, "rows": rows, "worker_sha256": sha(worker), "runtime": runtime}
    outputs.write(out / "corner-report.json", (json.dumps(report, indent=2, sort_keys=True) + "\n").encode())
    return rows


def _supplier(project, profile_path, out, design_dir, manual_path=None):
    """Run the supplier checks on a staged copy. Return (exit, result).

    The design outputs are read once, checked against the design binding, and copied into a private execution
    directory. The measurements read only those copies."""
    extra_inputs = {"profile": profile_path}
    if manual_path is not None:
        extra_inputs["manual"] = manual_path
        extra_inputs["manual-artifact"] = manual_artifact_path(project, pathlib.Path(manual_path).read_bytes())
    consumed = captured(project, extra_inputs)
    confine(project, out)
    for child in ("export", "logs", "work", "captured"):
        confine(project, out / child)
    refuse_links(project, supplier_destinations(out))
    outputs = Outputs(project, out)
    profile = profile_from_bytes(project, consumed["profile"], out / "captured")
    outputs.items["captured/profile.yaml"] = sha(consumed["profile"])
    check_division(profile)
    runtime = runtime_identity(consumed["toolchain.lock.json"])
    via_row = measure_vias(consumed, out, outputs, runtime, profile)
    if via_row["prohibited_spans"]:
        before = digest(consumed)
        if source_hashes(project, extra_inputs) != before:
            raise Stop(EXIT_FAIL, "The source files changed during the via measurement.")
        result = {"schema_id": "pcb-fab-package/supplier-precondition", "schema_version": 1,
                  "profile": profile["id"], "profile_sha256": profile["content_sha256"],
                  "status": "refused", "rows": [via_row], "source_sha256": before,
                  "runtime": runtime, "exit": EXIT_FAIL}
        result["content_sha256"] = VAL.canonical_hash(result)
        outputs.write(out / "supplier-result.json", (json.dumps(result, indent=2, sort_keys=True) + "\n").encode())
        return EXIT_FAIL, result
    design_result_raw, design_result = read_json_once(design_dir / "design-result.json")
    check_result_content(design_result)
    design_binding_raw = read_required(design_dir / "design-binding.json")
    design_binding = json.loads(design_binding_raw)
    if design_result.get("binding_sha256") != sha(design_binding_raw):
        raise Stop(EXIT_FAIL, "the design result does not bind the design binding")
    measure = {rel: read_required(design_dir / rel) for rel in MEASURE_INPUTS}
    silk_path = design_dir / SILK_INPUT
    measure[SILK_INPUT] = silk_path.read_bytes() if silk_path.is_file() else None
    for rel, data in measure.items():
        if data is not None and design_binding.get("outputs", {}).get(rel) != sha(data):
            raise Stop(EXIT_FAIL, f"the design output {rel} differs from the accepted design binding")
    inventory = json.loads(measure["inventory.json"])
    corner_rows = measure_corners(consumed, out, outputs, runtime, profile)
    stage = out / "work"
    before = stage_from(consumed, stage)
    generated = supplier_rules_text(profile)
    src_dru = consumed["kicad/board.kicad_dru"]
    dru_text = (src_dru.decode("utf-8").rstrip("\n") + "\n" + generated.split("\n", 1)[1]) if src_dru is not None else generated
    (stage / "kicad" / "board.kicad_dru").write_text(dru_text)
    (stage / "kicad" / "board.kicad_pro").write_bytes(
        effective_pro(consumed["kicad/board.kicad_pro"] or b"", profile).encode("utf-8"))
    exec_dir = out / "measure"
    if exec_dir.exists():
        shutil.rmtree(exec_dir)
    for rel, data in measure.items():
        if data is not None:
            (exec_dir / rel).parent.mkdir(parents=True, exist_ok=True)
            (exec_dir / rel).write_bytes(data)
    try:
        return _supplier_measure(project, profile, out, extra_inputs, manual_path, consumed, outputs, stage,
                                 exec_dir, measure, inventory, design_result_raw, design_binding_raw, dru_text,
                                 runtime, before, via_row, corner_rows)
    finally:
        shutil.rmtree(exec_dir, ignore_errors=True)


def _supplier_measure(project, profile, out, extra_inputs, manual_path, consumed, outputs, stage, exec_dir, measure,
                      inventory, design_result_raw, design_binding_raw, dru_text, runtime, before, via_row, corner_rows):
    """The measurements, the outputs and the binding of one supplier run. The inputs are in exec_dir."""
    rc, _, err = podman(stage, ["kicad-cli", "pcb", "drc", "--severity-all", "--format", "json", "-o", "/work/drc.json",
                                "/work/kicad/board.kicad_pcb"])
    outputs.write(out / "supplier-drc.stderr", err.encode())
    if rc not in (0, 5):
        raise Stop(EXIT_TOOL, f"the supplier DRC failed with exit {rc}")
    drc_raw, drc = read_json_once(stage / "drc.json")
    counts = {}
    for item in drc.get("violations", []):
        counts[item.get("type")] = counts.get(item.get("type"), 0) + 1
    rows = [via_row, *corner_rows]
    for key in sorted(profile["division"]["kicad_dru"]):
        typ = RULE_CONSTRAINT[key]
        n = violations_for(counts, key)
        rows.append({"condition": key, "method": "kicad_dru", "mandatory": True,
                     "status": "pass" if n == 0 else "fail", "violations": n,
                     "interpretation": f"KiCad {typ} with the supplier minimum"})
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
    slot_report = exec_dir / "slots.json"
    exp_exec = exec_dir / "export"
    code_slot = inspect_slots.main(["--board-inventory", str(exec_dir / "inventory.json"),
                                    "--pth", str(exp_exec / "board-PTH.drl"), "--npth", str(exp_exec / "board-NPTH.drl"),
                                    "--report", str(slot_report)])
    if code_slot == 2:
        raise Stop(EXIT_UNSUPPORTED, "the slot records are unsupported")
    if code_slot == 3:
        raise Stop(EXIT_TOOL, "the slot inspection could not read its inputs")
    if slot_report.is_file():
        outputs.write(out / "slots.json", slot_report.read_bytes())
    min_slot_mm = fab.limit_in_mm(profile["limits"]["min_slot_size"])
    minors = [Fraction(str(s["minor_mm"])) for s in inventory.get("slots", [])]
    slot_ok = all(m >= min_slot_mm for m in minors)
    rows.append({"condition": "min_slot_size", "method": "slot_inspection", "mandatory": True,
                 "status": "pass" if (code_slot == 0 and slot_ok) else "fail",
                 "interpretation": "minor dimension of every drilled slot and record match"})
    # The top mask: the worker reads the private copy, and the report must bind to the measured bytes.
    mask_limit = profile["limits"]["mask_web_min"]
    top_report = exec_dir / "mask.json"
    rc_mask = fab.run_mask_worker(str(exp_exec / "board-F_Mask.gbr"), str(mask_limit["value"]), str(top_report),
                                  unit=mask_limit["unit"])
    if rc_mask == 2:
        raise Stop(EXIT_UNSUPPORTED, "the mask construct is unsupported for automatic inspection")
    if rc_mask == 3:
        raise Stop(EXIT_TOOL, "the mask inspection failed")
    top_raw = top_report.read_bytes()
    top = json.loads(top_raw)
    mask_result = top["result"]
    rows.append({"condition": "mask_web_min", "method": "mask_inspection", "mandatory": True,
                 "status": mask_result if mask_result in ("pass", "fail", "uncertain") else "fail",
                 "interpretation": "exact web distance of the exported mask flashes"})
    if top["gerber_sha256"] != sha(measure["export/board-F_Mask.gbr"]):
        raise Stop(EXIT_FAIL, "the top mask measurement is not bound to the measured Gerber")
    outputs.write(out / "mask.json", top_raw)
    rows.append({"condition": "mask_web_min_top", "method": "mask_inspection", "mandatory": True,
                 "status": top["result"] if top["result"] in ("pass", "fail", "uncertain") else "fail",
                 "interpretation": "exact web distance of the top mask flashes"})
    bottom_report = exec_dir / "mask-bottom.json"
    rc_bottom = fab.run_mask_worker(str(exp_exec / "board-B_Mask.gbr"), str(mask_limit["value"]), str(bottom_report),
                                    unit=mask_limit["unit"])
    if rc_bottom == 2:
        raise Stop(EXIT_UNSUPPORTED, "the bottom mask construct is unsupported for automatic inspection")
    if rc_bottom == 3:
        raise Stop(EXIT_TOOL, "the bottom mask inspection failed")
    bottom_raw = bottom_report.read_bytes()
    bottom = json.loads(bottom_raw)
    if bottom["gerber_sha256"] != sha(measure["export/board-B_Mask.gbr"]):
        raise Stop(EXIT_FAIL, "the bottom mask measurement is not bound to the measured Gerber")
    outputs.write(out / "mask-bottom.json", bottom_raw)
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
            measure[SILK_INPUT], "silk_line_min_short_text", out, outputs)
    rows.extend(manual_rows(profile, silk_row))
    after = source_hashes(project, extra_inputs)
    if after != before:
        raise Stop(EXIT_FAIL, "the source files changed during the supplier run")
    code = rows_exit(rows)
    dru_bytes = dru_text.encode("utf-8")
    pro_bytes = (stage / "kicad" / "board.kicad_pro").read_bytes()
    outputs.write(out / "supplier.kicad_dru", dru_bytes)
    outputs.write(out / "supplier.kicad_pro", pro_bytes)
    outputs.write(out / "supplier-drc.json", drc_raw)
    measured = {rel: sha(data) for rel, data in measure.items() if data is not None}
    result = {"schema_id": "pcb-fab-package/supplier-result", "schema_version": 1, "profile": profile["id"],
              "manual": manual_info, "design_binding": sha(design_result_raw), "runtime": runtime,
              "profile_sha256": profile["content_sha256"], "rows": rows, "source_sha256": before,
              "measure_inputs": measured,
              "effective": {"board.kicad_dru": sha(dru_bytes), "board.kicad_pro": sha(pro_bytes)},
              "exit": code}
    binding = {"schema_id": "pcb-fab-package/supplier-binding", "schema_version": 1, "snapshot": before,
               "design_binding_sha256": sha(design_binding_raw), "manual": manual_info,
               "measure_inputs": measured,
               "outputs": outputs.digests(["supplier.kicad_dru", "supplier.kicad_pro", "supplier-drc.json", "slots.json",
                                           "mask.json", "manual-artifact.txt", "manual-evidence.json", "mask-bottom.json",
                                           "via-report.json", "corner-report.json"])}
    binding_bytes = (json.dumps(binding, indent=2, sort_keys=True) + "\n").encode("utf-8")
    PIO.atomic_write(project, out / "supplier-binding.json", binding_bytes)
    result["binding_sha256"] = sha(binding_bytes)
    result["content_sha256"] = VAL.canonical_hash(result)
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


def check_manual(manual_path, raw, art_bytes, board_bytes, silk_bytes, condition, out, outputs):
    """Check the captured manual evidence record, artifact, board and silk bytes. Return (info, status, interpretation).

    The inputs are the captured bytes. The retained copies are written through the outputs helper. Raise Stop for a defect."""
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
    if art_bytes is None or sha(art_bytes) != rec["artifact_sha256"]:
        raise Stop(EXIT_FAIL, "the manual artifact is missing or its hash differs")
    outputs.write(out / "manual-artifact.txt", art_bytes)
    inputs = rec["inputs"]
    if not isinstance(inputs, dict) or set(inputs) != {"board_sha256", "silk_gerber_sha256"}:
        raise Stop(EXIT_FAIL, "the manual inputs must name board_sha256 and silk_gerber_sha256")
    if inputs["board_sha256"] != sha(board_bytes):
        raise Stop(EXIT_FAIL, "the manual evidence is stale: the board hash differs")
    if silk_bytes is None or inputs["silk_gerber_sha256"] != sha(silk_bytes):
        raise Stop(EXIT_FAIL, "the manual evidence is stale: the silk Gerber hash differs")
    outputs.write(out / "manual-evidence.json", raw)
    info = {"path": "manual-evidence.json", "sha256": sha(raw),
            "artifact_path": rec["artifact_path"], "artifact_sha256": rec["artifact_sha256"],
            "original_path": str(pathlib.Path(manual_path).resolve()),
            "original_sha256": sha(raw)}
    return info, rec["result"], f"manual evidence by {rec['reviewer']}: {rec['procedure']}"


def supplier_inputs_now(project, profile_path, supplier_result):
    """The current digests of the supplier inputs, read live. The keys match the supplier source hashes."""
    extra = {"profile": profile_path}
    manual = supplier_result.get("manual")
    if manual:
        extra["manual"] = manual["original_path"]
        extra["manual-artifact"] = project.joinpath(*pathlib.PurePosixPath(manual["artifact_path"]).parts)
    return snapshot(project, extra)


def staged_problems(staging, manifest, manifest_bytes):
    """Compare the staged package with the validated manifest. Return the problems.

    The manifest bytes must be the validated bytes. Each output must match its recorded hash and size. A link,
    a missing output or an unexpected file is a problem."""
    problems = []
    manifest_path = staging / "manifest.json"
    if not manifest_path.is_file() or manifest_path.is_symlink():
        problems.append("the staged manifest is missing or is a link")
    elif sha(manifest_path.read_bytes()) != sha(manifest_bytes):
        problems.append("the staged manifest differs from its validated bytes")
    expected = {item["path"]: (item["sha256"], item["size_bytes"]) for item in manifest["outputs"]}
    present = set()
    for path in sorted(staging.rglob("*")):
        rel = path.relative_to(staging).as_posix()
        if path.is_symlink():
            problems.append(f"{rel} is a symbolic link")
        elif path.is_file():
            present.add(rel)
    for rel, (digest, size) in sorted(expected.items()):
        if rel not in present:
            problems.append(f"{rel} is missing from the staged package")
            continue
        data = (staging / rel).read_bytes()
        if sha(data) != digest or len(data) != size:
            problems.append(f"{rel} differs from its validated bytes")
    for rel in sorted(present - set(expected) - {"manifest.json"}):
        problems.append(f"{rel} is not an expected output")
    return problems


def final_gate(project, profile_path, design_dir, supplier_dir, design_result, supplier_result, staging, manifest,
               manifest_bytes, captured_bindings):
    """The last check before publication. Return the problems. A problem means nothing is published.

    It compares the source inputs, the captured binding bytes, the output map of each captured binding, the
    original manual record, and the staged package. The captured bytes are the bytes read at the start of the package."""
    problems = []
    if design_result.get("source_sha256") != snapshot(project, {"profile": profile_path}):
        problems.append("the source files changed before publication")
    if supplier_result.get("source_sha256") != supplier_inputs_now(project, profile_path, supplier_result):
        problems.append("the supplier inputs changed before publication")
    for base, bind_name, result_obj in ((design_dir, "design-binding.json", design_result),
                                        (supplier_dir, "supplier-binding.json", supplier_result)):
        raw = captured_bindings.get(bind_name)
        if raw is None:
            problems.append(f"the binding {bind_name} is missing at publication")
            continue
        bind = base / bind_name
        current = bind.read_bytes() if bind.is_file() else None
        if current != raw or sha(raw) != result_obj.get("binding_sha256"):
            problems.append(f"the binding {bind_name} changed before publication")
        for rel, digest in json.loads(raw).get("outputs", {}).items():
            if not (base / rel).is_file() or sha_file(base / rel) != digest:
                problems.append(f"{rel} changed before publication")
    manual = supplier_result.get("manual")
    if manual:
        original = pathlib.Path(manual.get("original_path", ""))
        if not original.is_file() or sha_file(original) != manual.get("original_sha256"):
            problems.append("the original manual record changed before publication")
    problems.extend(staged_problems(staging, manifest, manifest_bytes))
    return problems


def drawing_problem(design_dir, reader, board_bytes, profile, supplier_bytes):
    """Return None when the design drawing matches the captured facts, or the reason it does not.

    The facts come from the design inventory, the captured board and the captured supplier record. The drawing
    must be the deterministic drawing made from those facts. A substituted PDF fails here, before publication."""
    facts_raw = reader.optional(design_dir / "drawing-facts.json")
    pdf_raw = reader.optional(design_dir / "fabrication-drawing.pdf")
    inventory_raw = reader.optional(design_dir / "inventory.json")
    if facts_raw is None or pdf_raw is None or inventory_raw is None:
        return "the drawing, its facts or the board inventory is missing"
    expected = fab.drawing_facts(json.loads(inventory_raw), profile, board_bytes, "design-run", supplier_bytes)
    if facts_raw != (json.dumps(expected, indent=2, sort_keys=True) + "\n").encode():
        return "the drawing facts differ from the captured board inventory and profile"
    if pdf_raw != fab.drawing_pdf(expected):
        return "the fabrication drawing is not the drawing made from its captured facts"
    return None


def _package(project, profile_path, release, review_path, dest, design_dir, supplier_dir, expected_review_sha):
    """Build the package and run the B1 validator. Publish only after the final gate. Return (exit, manifest)."""
    consumed = captured(project, {"profile": profile_path})
    final = dest
    if final.exists():
        raise Stop(EXIT_UNSUPPORTED, "the destination exists")
    confine(project, final)
    staging = final.parent / (".staging-" + final.name)
    if staging.exists():
        raise Stop(EXIT_UNSUPPORTED, "a staging directory exists")
    refuse_links(project, [final, staging, supplier_dir / "captured" / "profile.yaml", supplier_dir / "package-check"])
    reader = Reader()
    profile = profile_from_bytes(project, consumed["profile"], supplier_dir / "captured")
    problem = drawing_problem(design_dir, reader, consumed["kicad/board.kicad_pcb"], profile,
                              consumed["manufacturing/supplier.yaml"])
    if problem is not None:
        raise Stop(EXIT_FAIL, problem)
    design_raw = reader.bytes(design_dir / "design-result.json")
    supplier_raw = reader.bytes(supplier_dir / "supplier-result.json")
    design_result = json.loads(design_raw)
    supplier_result = json.loads(supplier_raw)
    design_binding_raw = reader.optional(design_dir / "design-binding.json")
    supplier_binding_raw = reader.optional(supplier_dir / "supplier-binding.json")
    design_bound = json.loads(design_binding_raw).get("outputs", {}) if design_binding_raw is not None else {}
    supplier_bound = json.loads(supplier_binding_raw).get("outputs", {}) if supplier_binding_raw is not None else {}
    check_result_content(design_result)
    validate_supplier_result(supplier_result, profile)
    reasons = []
    if design_result["exit"] != 0:
        reasons.append("design checks are not all passing")
    if supplier_result["exit"] != 0:
        reasons.append("supplier conditions are not all passing")
    review_bytes = reader.optional(review_path)
    gate_problems = review.gate(project, profile, consumed["profile"], review_bytes, expected_review_sha, release)
    reasons.extend(gate_problems)
    if review_bytes is not None and sha(review_bytes) != expected_review_sha:
        reasons.append("the review bytes differ from the accepted review hash")
    staging.mkdir(parents=True)
    evidence_dir, report_dir = staging / "evidence", staging / "reports"
    evidence_dir.mkdir()
    report_dir.mkdir()
    outputs = []
    measured = supplier_result.get("measure_inputs", {})

    def design_name(src):
        """The design-relative name of a design output, or None."""
        try:
            return pathlib.Path(src).relative_to(design_dir).as_posix()
        except ValueError:
            return None

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

    def out_item(src, rel_dst, role, layer=None):
        data = reader.optional(src)  # read once; the decision, the copy and the digest use these bytes
        if data is None:
            reasons.append(f"missing output {rel_dst}: the design or supplier output is absent")
            return
        digest = sha(data)
        expected = expected_for(src)
        if expected is not None and digest != expected:
            reasons.append(f"{rel_dst} changed after its measurement")
        name = design_name(src)
        if name in measured and measured[name] != digest:
            reasons.append(f"{rel_dst} differs from the measured design input {name}")
        target = staging / rel_dst
        write_out(project, target, data)
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
    out_item(supplier_dir / "via-report.json", "reports/via-report.json", "report")
    out_item(supplier_dir / "corner-report.json", "reports/corner-report.json", "report")
    out_item(design_dir / "inventory.json", "reports/inventory.json", "report")
    obs_path = review_path.parent / "observations.json"
    obs_bytes = reader.optional(obs_path)
    if review_bytes is not None and obs_bytes is not None:
        review_obs = json.loads(review_bytes).get("observations_file_sha256")
        if review_obs != sha(obs_bytes):
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
            inputs.append({"role": role, "path": rel, "sha256": sha(consumed[rel])})
    inputs.append({"role": "supplier_rules", "path": "out/fab/supplier/work/kicad/board.kicad_dru",
                   "sha256": supplier_result["effective"]["board.kicad_dru"]})
    inputs.append({"role": "supplier_settings", "path": "out/fab/supplier/work/kicad/board.kicad_pro",
                   "sha256": supplier_result["effective"]["board.kicad_pro"]})
    current = snapshot(project, {"profile": profile_path})
    if design_result.get("source_sha256") != current:
        reasons.append("the design result is stale: a source file changed after the design run")
    if supplier_result.get("source_sha256") != supplier_inputs_now(project, profile_path, supplier_result):
        reasons.append("the supplier result is stale: a source file changed after the supplier run")
    if supplier_result.get("design_binding") != sha(design_raw):
        reasons.append("the supplier result does not bind this design result")
    for label, result_obj, base, bind_name, bind_raw in (
            ("design", design_result, design_dir, "design-binding.json", design_binding_raw),
            ("supplier", supplier_result, supplier_dir, "supplier-binding.json", supplier_binding_raw)):
        if bind_raw is None:
            reasons.append(f"the {label} binding file is missing")
            continue
        if result_obj.get("binding_sha256") != sha(bind_raw):
            reasons.append(f"the {label} result does not bind the current {bind_name}")
        for rel, digest in json.loads(bind_raw).get("outputs", {}).items():
            if not (base / rel).is_file() or sha_file(base / rel) != digest:
                reasons.append(f"the {label} output {rel} changed after its binding")
    if supplier_result.get("manual"):
        art = project.joinpath(*pathlib.PurePosixPath(supplier_result["manual"]["artifact_path"]).parts)
        if not art.is_file() or sha_file(art) != supplier_result["manual"]["artifact_sha256"]:
            reasons.append("the manual artifact changed after its measurement")
    checks = []
    if consumed["manufacturing/supplier.yaml"] != consumed["profile"]:
        reasons.append("the project supplier record differs from the profile")
    # The semantic checks read a private copy of the design files. These are the bytes that were read above.
    checkdir = supplier_dir / "package-check"
    if checkdir.exists():
        shutil.rmtree(checkdir)
    if (design_dir / "export").is_dir():
        for path in sorted((design_dir / "export").iterdir()):
            if path.is_file():
                write_out(project, checkdir / "export" / path.name, reader.bytes(path))
    write_out(project, checkdir / "inventory.json", reader.bytes(design_dir / "inventory.json"))
    for check_id in VAL.BARE_CHECKS:
        status, detail = check_status(check_id, design_result, supplier_result, gate_problems, project, profile,
                                      checkdir, contract)
        if status != "pass":
            reasons.append(f"{check_id}: {detail}")
        if check_id == "fab.profile_evidence":
            art = next(o for o in outputs if o["path"] == "evidence/supplier-page.html")
        else:
            art = out_item_text(project, staging, check_id, detail, outputs)
        listed = [{"path": m["path"], "sha256": m["sha256"]} for role in VAL.CHECK_INPUT_ROLES[check_id]
                  for m in inputs if m["role"] == role]
        evidence = {"schema_id": "cad-skills/evidence", "schema_version": "1.0", "check_id": check_id,
                    "status": status, "method": "tool", "tool": {"name": "pcb-fab-package", "version": "1"},
                    "inputs": listed, "artifact": {"path": art["path"], "sha256": art["sha256"]}}
        ev = out_item_json(project, staging, check_id, evidence, outputs)
        checks.append({"id": check_id, "status": status, "evidence_path": ev["path"], "evidence_sha256": ev["sha256"]})
    shutil.rmtree(checkdir, ignore_errors=True)
    board_record = VAL.parse_record(consumed["board.yaml"], ".yaml", "board.yaml")
    manifest = {"schema_id": "cad-skills/manifest", "schema_version": "1.0", "release_id": release,
                "kind": "bare_board", "board_revision": board_record["release_revision"],
                "board_sha256": sha(consumed["kicad/board.kicad_pcb"]),
                "variant": board_record["variant"],
                "supplier": board_record["supplier"],
                "inputs": inputs, "outputs": outputs, "drill_applicability": [], "checks": checks,
                "status": "qualified" if not reasons else "draft",
                "reasons": [{"code": "pkg.reason", "text": text} for text in sorted(set(reasons))],
                "tool_versions": {"kicad": design_result["runtime"]["kicad_version"]}}
    manifest_path = staging / "manifest.json"
    manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    write_out(project, manifest_path, manifest_bytes)
    _, report = VAL.build_report([str(manifest_path)], SCHEMAS, project, staging)
    if report["findings"]:
        # The validator found a defect. The manifest records it, and the record is validated again.
        manifest["status"] = "draft"
        manifest["reasons"] = [{"code": "pkg.reason", "text": text} for text in sorted(set(reasons))] + [
            {"code": "pkg.validator", "text": f"{f['code']} at {f['location']}"} for f in report["findings"]]
        manifest_bytes = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
        write_out(project, manifest_path, manifest_bytes)
        _, report = VAL.build_report([str(manifest_path)], SCHEMAS, project, staging)
    clean = not report["findings"]
    problems = final_gate(project, profile_path, design_dir, supplier_dir, design_result, supplier_result, staging,
                          manifest, manifest_bytes, {"design-binding.json": design_binding_raw,
                                                     "supplier-binding.json": supplier_binding_raw})
    if problems:
        raise Stop(EXIT_FAIL, "pkg.final_gate: " + "; ".join(problems) + f". The staging directory {staging} is kept"
                              " and nothing is published.")
    PIO.publish_dir(project, staging, final)
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


def out_item_text(project, dest, check_id, detail, outputs):
    target = dest / "reports" / f"{check_id}.txt"
    data = f"report of {check_id}: {detail}\n".encode("utf-8")
    write_out(project, target, data)
    item = {"role": "report", "path": f"reports/{check_id}.txt", "sha256": sha(data), "size_bytes": len(data)}
    outputs.append(item)
    return item


def out_item_json(project, dest, check_id, record, outputs):
    target = dest / "evidence" / f"{check_id}.json"
    data = (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8")
    write_out(project, target, data)
    item = {"role": "evidence", "path": f"evidence/{check_id}.json", "sha256": sha(data), "size_bytes": len(data)}
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
    """Hold the project lock through the final gate and the publication."""
    try:
        with PIO.project_lock(project, "package"):
            return _package(project, profile_path, release, review_path, dest, design_dir, supplier_dir, expected_review_sha)
    except (PIO.LockHeld, PIO.LockMalformed) as err:
        raise Stop(EXIT_UNSUPPORTED, f"the project is locked: {err}")
