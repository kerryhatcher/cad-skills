#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["cadquery", "jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Mechanical fit for a board (B11), completion repair.

  uv run scripts/mechanical.py check --fixture DIR      # contract rules on a generated fixture
  uv run scripts/mechanical.py readiness --project DIR  # route state
  uv run scripts/mechanical.py export --project DIR     # STEP, DXF and separate PTH/NPTH drill files
  uv run scripts/mechanical.py fit --project DIR        # comparisons C01 to C12 on the export
  uv run scripts/mechanical.py release --project DIR    # publish mech-release/1

Every command reads each input once as captured bytes, confines every record path before access,
runs the measured image ID, and checks freshness and output integrity before it publishes.

Exit status (highest priority first):
  3  Tool execution or integrity failure after publication started.
  2  Incorrect invocation, missing prerequisite, unsupported frame, transform, settings, drill, or image.
  1  Invalid record, failed or incomplete comparison, stale input, altered output, lock or path refusal.
  0  Pass.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import project_io as PIO  # noqa: E402  (accepted lock, confinement and atomic-write helpers)
import validate as V  # noqa: E402  (accepted canonical hash helper)

RECORD_VERSION = "1"
RELEASE_RECORD = "mech-release/1"
REPORT_RECORD = "mech-report/1"
EXPORT_RECORD = "mech-export/1"
ROLES = ("step_board", "dxf_outline", "drill_pth", "drill_npth", "step_fit", "report")
EXPORT_FILES = {"board.step": "step_board", "outline.dxf": "dxf_outline",
                "board-PTH.drl": "drill_pth", "board-NPTH.drl": "drill_npth"}
EXPORT_DIR = "out/mechanical/export"
REPORT = "out/mechanical/report.json"
FIT_ASSEMBLY = "out/mechanical/fit-assembly.step"
RELEASE = "out/release/mech-release.json"
CAPTURED = ("board.kicad_pcb", "export-settings.json", "mechanical/board-interface.json",
            "mechanical/fixture-source.json", "mechanical/component-evidence.json")
FIXED_TOLERANCE = {"geometry_mm": 0.01, "angle_deg": 0.1, "volume_mm3": 1e-6}
OWNER_KEYS = ("outline", "holes", "connector_frames", "thickness", "height_limits")
PAD_FRAME = "placed-file"
EVIDENCE = ("measured", "datasheet", "proxy", "unconfirmed")
TRANSFORM_KEYS = {"source_frame", "source_origin_mm", "source_axes", "target_axes", "scale"}
CONNECTOR_KEYS = {"id", "side", "x", "y", "rotation_deg", "insertion_depth_mm"}
RELEASE_ORDER = ("electrical_release_id", "release_id", "board_sha256", "interface_sha256",
                 "component_evidence_sha256", "fixture_source_sha256", "export_settings_sha256",
                 "toolchain_image_id", "fixture_id")
KICAD = {
    "step": ["pcb", "export", "step", "--drill-origin", "--board-only", "--no-extra-pad-thickness",
             "--min-distance", "0.01mm", "-o", "out/board.step", "board.kicad_pcb"],
    "dxf": ["pcb", "export", "dxf", "--use-drill-origin", "--output-units", "mm", "--mode-single",
            "--layers", "Edge.Cuts", "--drill-shape-opt", "2", "-o", "out/outline.dxf", "board.kicad_pcb"],
    "drill": ["pcb", "export", "drill", "--drill-origin", "plot", "--excellon-units", "mm",
              "--excellon-separate-th", "-o", "out/drill/", "board.kicad_pcb"],
}
DRILL_OUTPUTS = {"board-PTH.drl": "out/drill/board-PTH.drl", "board-NPTH.drl": "out/drill/board-NPTH.drl"}
STAGED_OUTPUTS = {"board.step": "out/board.step", "outline.dxf": "out/outline.dxf",
                  "board-PTH.drl": "out/drill/board-PTH.drl", "board-NPTH.drl": "out/drill/board-NPTH.drl"}


class MechError(Exception):
    """A refusal. `code` names the cause. `status` is the exit status."""

    def __init__(self, code: str, message: str, status: int = 1):
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.status = status


def _num(value, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise MechError("transform.type", f"{where} must be a finite number.", 2)
    return float(value)


def _point(value, where: str) -> tuple[float, float]:
    if not isinstance(value, dict) or set(value) != {"x", "y"}:
        raise MechError("transform.type", f"{where} must hold exactly x and y.", 2)
    return _num(value["x"], f"{where}.x"), _num(value["y"], f"{where}.y")


def _sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _json(data: bytes, where: str) -> dict:
    try:
        value = json.loads(data.decode("utf-8"))
    except (UnicodeDecodeError, ValueError) as err:
        raise MechError("record.json", f"{where} is not JSON: {err}", 2)
    if not isinstance(value, dict):
        raise MechError("record.json", f"{where} must be a JSON object.", 2)
    return value


# --------------------------------------------------------------------------- transform and frame


def load_transform(iface: dict) -> dict:
    ext = iface.get("extensions")
    if not isinstance(ext, dict) or "transform" not in ext:
        raise MechError("transform.missing", "The interface has no extensions.transform. Refusing.", 2)
    t = ext["transform"]
    if not isinstance(t, dict) or set(t) != TRANSFORM_KEYS:
        raise MechError("transform.keys", "extensions.transform must hold exactly: "
                        + ", ".join(sorted(TRANSFORM_KEYS)) + ".", 2)
    if t["source_frame"] != "kicad-board":
        raise MechError("transform.frame", "Only source_frame kicad-board is supported.", 2)
    if t["source_axes"] != {"x": "right", "y": "down"}:
        raise MechError("transform.axes", "source_axes must be x right and y down.", 2)
    if t["target_axes"] != {"x": "right", "y": "up"}:
        raise MechError("transform.axes", "target_axes must be x right and y up.", 2)
    if _num(t["scale"], "transform.scale") != 1.0:
        raise MechError("transform.scale", "Only scale 1 is supported.", 2)
    return {"origin": _point(iface.get("origin_mm"), "origin_mm"),
            "anchor": _point(t["source_origin_mm"], "transform.source_origin_mm")}


def to_target(point, transform: dict) -> tuple[float, float]:
    """x_target = origin.x + x − anchor.x ; y_target = origin.y + anchor.y − y."""
    ox, oy = transform["origin"]
    ax, ay = transform["anchor"]
    x, y = point
    return ox + x - ax, oy + ay - y


def target_vector(local, theta_deg: float) -> tuple[float, float]:
    """target = R(θ) · F · local. Combined matrix [[cos θ, sin θ], [sin θ, −cos θ]] (Q7 trial)."""
    th = math.radians(theta_deg)
    c, s = math.cos(th), math.sin(th)
    lx, ly = local
    return c * lx + s * ly, s * lx - c * ly


def target_angle_deg(vector) -> float:
    return math.degrees(math.atan2(vector[1], vector[0])) % 360.0


def board_vector(local, theta_deg: float) -> tuple[float, float]:
    th = math.radians(theta_deg)
    c, s = math.cos(th), math.sin(th)
    lx, ly = local
    return c * lx + s * ly, -s * lx + c * ly


# --------------------------------------------------------------------------- stackup, envelope, owners


def check_stackup(src: dict) -> dict:
    st = src.get("stackup")
    keys = ("core_mm", "copper_top_mm", "copper_bottom_mm", "mask_top_mm", "mask_bottom_mm", "thickness_mm")
    if not isinstance(st, dict) or set(st) != set(keys):
        raise MechError("stackup.keys", "stackup must hold exactly: " + ", ".join(keys) + ".", 2)
    v = {k: _num(st[k], f"stackup.{k}") for k in keys}
    for k in keys:
        if v[k] <= 0:
            raise MechError("stackup.value", f"stackup.{k} must be positive.")
    total = round(v["core_mm"] + v["copper_top_mm"] + v["copper_bottom_mm"] + v["mask_top_mm"]
                  + v["mask_bottom_mm"], 6)
    if total != round(v["thickness_mm"], 6):
        raise MechError("C05s", f"The layer sum {total} differs from thickness_mm {v['thickness_mm']}.")
    return {"core_mm": v["core_mm"],
            "bottom_surface_z": round(-(v["copper_bottom_mm"] + v["mask_bottom_mm"]), 6),
            "top_surface_z": round(v["core_mm"] + v["copper_top_mm"] + v["mask_top_mm"], 6)}


def check_finished_envelope(src: dict, surfaces: dict) -> None:
    env = src.get("finished_envelope")
    if not isinstance(env, dict):
        raise MechError("envelope.missing", "fixture-source.json has no finished_envelope.", 2)
    if env.get("label") != "FINISHED BOARD ENVELOPE":
        raise MechError("envelope.label", "finished_envelope.label must be FINISHED BOARD ENVELOPE.", 2)
    if _num(env.get("z_origin_mm"), "z_origin_mm") != 0.0:
        raise MechError("envelope.origin", "The Z origin is the core bottom face, z = 0.", 2)
    if round(_num(env.get("bottom_surface_z_mm"), "bottom_surface_z_mm"), 6) != surfaces["bottom_surface_z"]:
        raise MechError("envelope.surface", "bottom_surface_z_mm differs from the stackup.")
    if round(_num(env.get("top_surface_z_mm"), "top_surface_z_mm"), 6) != surfaces["top_surface_z"]:
        raise MechError("envelope.surface", "top_surface_z_mm differs from the stackup.")
    if env.get("stackup_source") != "fixture-source.json":
        raise MechError("envelope.source", "finished_envelope.stackup_source must be fixture-source.json.", 2)


def owner_conflicts(interface_owners: dict, source_owners: dict) -> list[str]:
    for name, owners in (("board-interface", interface_owners), ("fixture-source", source_owners)):
        if not isinstance(owners, dict) or set(owners) != set(OWNER_KEYS):
            raise MechError("owner.keys", f"{name} dimension_owners must name exactly: " + ", ".join(OWNER_KEYS) + ".", 2)
    return [k for k in OWNER_KEYS if interface_owners[k] != source_owners[k]]


# --------------------------------------------------------------------------- evidence, connectors, holes


def evidence_status(rec: dict) -> str:
    ev = rec.get("evidence")
    if ev not in EVIDENCE:
        raise MechError("evidence.kind", f"Unknown evidence {ev!r}.", 2)
    if ev == "unconfirmed":
        return "unconfirmed"
    if ev == "proxy":
        return "conservative_envelope_only"
    return "pass" if _height(rec.get("height_mm"), "height_mm") <= _height(rec.get("limit_mm"), "limit_mm") else "fail"


def _height(value, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(float(value)):
        raise MechError("evidence.height", f"{where} must be a finite number.", 2)
    return float(value)


def check_evidence_source(rec: dict) -> None:
    ev = rec.get("evidence")
    digest = rec.get("source_sha256")
    if ev in ("measured", "datasheet"):
        if not (isinstance(digest, str) and len(digest) == 64 and all(c in "0123456789abcdef" for c in digest)):
            raise MechError("evidence.source", f"{rec.get('ref', '?')}: {ev} evidence needs a SHA-256 source.")
    elif digest is not None and not (isinstance(digest, str) and len(digest) == 64):
        raise MechError("evidence.source", f"{rec.get('ref', '?')}: source_sha256 must be null or 64 hex digits.")


def check_placement(rec: dict) -> None:
    centre = rec.get("kicad_center_mm")
    if not isinstance(centre, dict) or set(centre) != {"x", "y"}:
        raise MechError("placement.missing", f"{rec.get('ref', '?')}: kicad_center_mm with x and y is required.", 2)
    _height(centre["x"], f"{rec.get('ref', '?')}.x")
    _height(centre["y"], f"{rec.get('ref', '?')}.y")
    _height(rec.get("rotation_deg"), f"{rec.get('ref', '?')}.rotation_deg")


def check_connector_agreement(iface: dict, src: dict, evidence: dict) -> None:
    """Side and insertion depth must agree across the interface, the source record and the evidence.
    A mismatch names the connector and the field (residual correction 1, Pi N1)."""
    frames = {f.get("id"): f for f in iface.get("connector_frames", [])}
    records = {c.get("ref"): c for c in evidence.get("components", [])}
    for sf in src["connector_frames"]:
        ref = sf["id"]
        if ref not in frames:
            raise MechError("connector.missing", f"{ref}: the interface has no connector frame for it.", 1)
        for field, interface_value, source_value, evidence_value in (
                ("side", frames[ref].get("side"), sf.get("side"), records.get(ref, {}).get("side")),
                ("insertion_depth_mm", frames[ref].get("insertion_depth_mm"), sf.get("insertion_depth_mm"),
                 records.get(ref, {}).get("insertion_depth_mm"))):
            if not (interface_value == source_value == evidence_value):
                raise MechError("connector.mismatch",
                                f"{ref}: {field} differs: interface {interface_value!r}, source "
                                f"{source_value!r}, evidence {evidence_value!r}.", 1)


def check_footprint_evidence(rec: dict) -> None:
    """A B.Cu footprint must declare pad_frame placed-file. Other frames refuse."""
    if rec.get("side") != "bottom":
        return
    frame = rec.get("pad_frame")
    if frame is None:
        raise MechError("pad_frame.missing", f"{rec.get('ref', '?')}: a B.Cu footprint must declare pad_frame.")
    if frame != PAD_FRAME:
        raise MechError("pad_frame.unsupported", f"{rec.get('ref', '?')}: frame {frame!r} has no frozen rule.", 2)


def check_connector_record(frame: dict) -> None:
    extra = set(frame) - CONNECTOR_KEYS
    if extra:
        raise MechError("connector.field", "The connector item has fields outside the schema: "
                        + ", ".join(sorted(extra)) + ".")


def check_connector_evidence(rec: dict) -> None:
    """A connector needs its envelope, insertion vector, insertion depth and its own body length."""
    for key in ("connector_envelope", "insertion_vector_local", "insertion_depth_mm", "body_length_mm"):
        if key not in rec:
            raise MechError("connector.evidence", f"{rec.get('ref', '?')}: the connector record needs {key}.")
    body = _height(rec["body_length_mm"], f"{rec.get('ref', '?')}.body_length_mm")
    if body <= 0:
        raise MechError("connector.evidence", f"{rec.get('ref', '?')}: body_length_mm must be positive.")


def validate_excluded(iface: dict) -> list[dict]:
    """Each excluded through hole needs an id, a finite position, a positive diameter, a plated flag
    and a nonblank reason (R1, P3). Anything else refuses by name."""
    entries = iface.get("extensions", {}).get("excluded_through_holes", [])
    if not isinstance(entries, list):
        raise MechError("excluded.type", "excluded_through_holes must be a list.", 2)
    out = []
    for item in entries:
        if not isinstance(item, dict) or set(item) != {"id", "x", "y", "diameter_mm", "plated", "reason"}:
            raise MechError("excluded.fields", "Each excluded hole needs exactly: id, x, y, diameter_mm, plated, reason.", 2)
        if not isinstance(item["id"], str) or not item["id"].strip():
            raise MechError("excluded.id", "An excluded hole needs a nonblank id.", 2)
        if not isinstance(item["reason"], str) or not item["reason"].strip():
            raise MechError("excluded.reason", f"Excluded hole {item['id']} needs a nonblank reason.", 2)
        if not isinstance(item["plated"], bool):
            raise MechError("excluded.plated", f"Excluded hole {item['id']} needs a boolean plated flag.", 2)
        x = _num(item["x"], f"excluded {item['id']}.x")
        y = _num(item["y"], f"excluded {item['id']}.y")
        d = _num(item["diameter_mm"], f"excluded {item['id']}.diameter_mm")
        if d <= 0:
            raise MechError("excluded.diameter", f"Excluded hole {item['id']} needs a positive diameter.", 2)
        out.append({"id": item["id"], "x": x, "y": y, "diameter_mm": d, "plated": item["plated"]})
    return out


def check_required_components(src: dict, evidence: dict) -> None:
    """Every source part and connector frame needs an evidence record, by reference (R4)."""
    refs = {c.get("ref") for c in evidence.get("components", [])}
    required = [p["ref"] for p in src.get("parts", [])] + [f["id"] for f in src["connector_frames"]]
    missing = [r for r in required if r not in refs]
    if missing:
        raise MechError("component.missing", "No evidence record for: " + ", ".join(missing) + ".", 1)
    extra = [r for r in refs if r not in required]
    if extra:
        raise MechError("component.unknown", "Evidence without a source record: " + ", ".join(sorted(extra)) + ".", 1)


# --------------------------------------------------------------------------- captured contract


def contract_check(files: dict) -> dict:
    """Every contract rule on captured bytes. Returns a summary. Raises MechError."""
    iface = _json(files["mechanical/board-interface.json"], "board-interface.json")
    src = _json(files["mechanical/fixture-source.json"], "fixture-source.json")
    evidence = _json(files["mechanical/component-evidence.json"], "component-evidence.json")
    settings = _json(files["export-settings.json"], "export-settings.json")
    transform = load_transform(iface)
    surfaces = check_stackup(src)
    check_finished_envelope(src, surfaces)
    conflicts = owner_conflicts(iface["dimension_owners"], src["dimension_owners"])
    if conflicts:
        raise MechError("C11", "Owner conflict on: " + ", ".join(conflicts) + ".")
    for frame in iface.get("connector_frames", []):
        check_connector_record(frame)
    validate_excluded(iface)
    check_required_components(src, evidence)
    check_connector_agreement(iface, src, evidence)
    for rec in evidence.get("components", []):
        check_footprint_evidence(rec)
        check_evidence_source(rec)
        check_placement(rec)
        if "connector_envelope" in rec:
            check_connector_evidence(rec)
        evidence_status(rec)
    variants = src.get("test_variants", {})
    if variants.get("release_allowed") is not False or variants.get("test_only") is not True:
        raise MechError("variant.release", "Test-only variants must declare test_only true and release_allowed false.")
    import mechanical_fit as MF  # noqa: PLC0415
    problems = MF.settings_switches_ok(settings)
    if problems:
        raise MechError("export.settings", "; ".join(problems), 2)
    return {"transform_anchor": list(transform["anchor"]), "origin": list(transform["origin"]),
            "surfaces": surfaces, "tolerance": FIXED_TOLERANCE}


def read_project(project: Path, rel: str) -> bytes:
    """One confined read of a project file."""
    path = PIO.confine(project, rel)
    if not path.is_file():
        raise MechError("input.missing", f"The input {rel} is missing.", 2)
    return path.read_bytes()


def capture(project: Path) -> dict:
    """Read each consumed input once. Returns {rel: {bytes, sha256, size}}. The bytes are kept for
    every later calculation, so no calculation reopens a live file (R6, I3)."""
    out = {}
    for rel in CAPTURED:
        data = read_project(project, rel)
        out[rel] = {"bytes": data, "sha256": _sha(data), "size": len(data)}
    return out


def files_of(cap: dict) -> dict:
    return {rel: meta["bytes"] for rel, meta in cap.items()}


def inputs_record(cap: dict) -> dict:
    return {rel: {"sha256": meta["sha256"], "size": meta["size"]} for rel, meta in cap.items()}


def first_stale(recorded: dict, cap: dict) -> dict | None:
    """Freshness: the first captured input whose hash differs from the recorded hash."""
    for rel in CAPTURED:
        if recorded.get(rel, {}).get("sha256") != cap[rel]["sha256"]:
            return {"input": rel, "expected": recorded.get(rel, {}).get("sha256"), "measured": cap[rel]["sha256"]}
    return None


def release_first_mismatch(expected: dict, actual: dict) -> dict | None:
    """The accepted mismatch order (interface section 8). Returns the first mismatch."""
    for key in RELEASE_ORDER:
        if expected.get(key) != actual.get(key):
            return {"input": key, "expected": expected.get(key), "measured": actual.get(key)}
    return None


def check_fixture(fixture: Path) -> dict:
    """Contract rules on a generated fixture directory (its mechanical/ folder, and its settings)."""
    cap = capture(fixture)
    return contract_check(files_of(cap))


# --------------------------------------------------------------------------- image and staging


def _image_id(ref: str) -> str:
    import subprocess  # noqa: PLC0415
    proc = subprocess.run(["podman", "image", "inspect", ref, "--format", "{{.Id}}"], capture_output=True, text=True)
    if proc.returncode != 0 or not proc.stdout.strip():
        raise MechError("runtime.image_missing", f"The image {ref} is not present. No pull is made.", 2)
    return proc.stdout.strip()


def _run_kicad(stage: Path, image_id: str, args: list[str]) -> tuple[int, str]:
    import subprocess  # noqa: PLC0415
    cmd = ["podman", "run", "--rm", "--pull=never", "--network", "none", "--security-opt", "label=disable",
           "-w", "/work", "-v", f"{stage}:/work", image_id, "kicad-cli", *args]
    proc = subprocess.run(cmd, capture_output=True, text=True)
    return proc.returncode, proc.stdout + proc.stderr


def _stage_dir(project: Path, prefix: str, token: str) -> Path:
    import shutil  # noqa: PLC0415
    stage = PIO.confine(project, f"out/staging/{prefix}-{token}")
    if stage.exists():
        shutil.rmtree(stage)
    return stage


def _export_record_check(record: dict) -> None:
    """Confine and validate the export record (R7). Each output path is the fixed relative path."""
    if record.get("record") != EXPORT_RECORD or record.get("version") != RECORD_VERSION:
        raise MechError("export.record", "The export record has the wrong record or version.", 1)
    outputs = record.get("outputs")
    if not isinstance(outputs, dict) or set(outputs) != set(EXPORT_FILES):
        raise MechError("export.outputs", "The export record must name exactly the four export files.", 1)
    for name, meta in outputs.items():
        expected = f"{EXPORT_DIR}/{name}"
        if not isinstance(meta, dict) or meta.get("path") != expected or meta.get("role") != EXPORT_FILES[name]:
            raise MechError("export.path", f"{name}: the record path or role is not the accepted one.", 1)
        if not (isinstance(meta.get("sha256"), str) and len(meta["sha256"]) == 64):
            raise MechError("export.sha256", f"{name}: a SHA-256 is required.", 1)
        if not (isinstance(meta.get("size"), int) and not isinstance(meta.get("size"), bool) and meta["size"] > 0):
            raise MechError("export.size", f"{name}: a positive byte count is required.", 1)


def run_export(project: Path, image_ref: str) -> dict:
    """Export STEP, DXF and separate PTH and NPTH drill files in the measured local image."""
    import shutil  # noqa: PLC0415
    with PIO.project_lock(project, "mechanical-export"):
        cap = capture(project)
        files = files_of(cap)
        contract_check(files)
        settings = _json(files["export-settings.json"], "export-settings.json")
        image_id = _image_id(image_ref)
        if settings.get("image_id") != image_id:
            raise MechError("runtime.image_mismatch",
                            f"The pinned image is {settings.get('image_id')}; the local image is {image_id}.", 2)
        token = _sha(json.dumps(inputs_record(cap), sort_keys=True).encode("utf-8"))[:16]
        stage = _stage_dir(project, "mech", token)
        (stage / "out" / "drill").mkdir(parents=True)
        (stage / "board.kicad_pcb").write_bytes(files["board.kicad_pcb"])
        exits, logs = {}, {}
        for name, args in KICAD.items():
            code, text = _run_kicad(stage, image_id, args)
            exits[name] = code
            logs[name] = text
            if code != 0:
                raise MechError("export.kicad_exit", f"kicad-cli {name} exited {code}.", 3)
        staged = {}
        for name, rel in STAGED_OUTPUTS.items():
            path = stage / rel
            if not path.is_file():
                raise MechError("export.missing", f"{name} was not produced.", 3)
            data = path.read_bytes()
            if not data:
                raise MechError("export.empty", f"{name} is empty.", 3)
            staged[name] = data
        outputs = {}
        for name, data in staged.items():
            outputs[name] = {"role": EXPORT_FILES[name], "path": f"{EXPORT_DIR}/{name}",
                             "sha256": _sha(data), "size": len(data)}
        for name, data in staged.items():
            if _sha(data) != outputs[name]["sha256"]:
                raise MechError("export.altered", f"The staged {name} changed before publication.", 1)
        # Source drift check before the first publication write (residual correction 2).
        stale = first_stale(inputs_record(cap), capture(project))
        if stale is not None:
            raise MechError("stale.input", f"{stale['input']} changed during the export; nothing was published.", 1)
        for name, data in staged.items():
            PIO.atomic_write(project, f"{EXPORT_DIR}/{name}", data)
        record = {"record": EXPORT_RECORD, "version": RECORD_VERSION, "image_id": image_id, "image_ref": image_ref,
                  "inputs": inputs_record(cap), "exits": exits,
                  "commands": {k: " ".join(v) for k, v in KICAD.items()}, "outputs": outputs}
        PIO.atomic_write(project, f"{EXPORT_DIR}/export.json",
                         (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        shutil.rmtree(stage)
    return record


def run_fit(project: Path) -> dict:
    """Run every comparison on captured bytes and the published export. Refuses stale and altered inputs."""
    import mechanical_fit as MF  # noqa: PLC0415
    with PIO.project_lock(project, "mechanical-fit"):
        cap = capture(project)
        files = files_of(cap)
        contract_check(files)
        export_bytes = read_project(project, f"{EXPORT_DIR}/export.json")
        export = _json(export_bytes, "export.json")
        _export_record_check(export)
        stale = first_stale(export.get("inputs", {}), cap)
        if stale is not None:
            raise MechError("stale.input", f"{stale['input']} changed after the export; export again.", 1)
        published = {}
        for name, meta in export["outputs"].items():
            data = read_project(project, meta["path"])
            if _sha(data) != meta["sha256"] or len(data) != meta["size"]:
                raise MechError("export.altered", f"The published {name} differs from the export record.", 1)
            published[name] = data
        token = _sha(export_bytes)[:16]
        work = _stage_dir(project, "fit", token)
        work.mkdir(parents=True)
        fit_tmp = work / "fit-assembly.step"
        run = MF.evaluate({"board_kicad": files["board.kicad_pcb"], "interface": files["mechanical/board-interface.json"],
                           "source": files["mechanical/fixture-source.json"],
                           "evidence": files["mechanical/component-evidence.json"],
                           "dxf": published["outline.dxf"], "step": published["board.step"],
                           "pth": published["board-PTH.drl"], "npth": published["board-NPTH.drl"]},
                          work / "private", fit_tmp)
        src = _json(files["mechanical/fixture-source.json"], "fixture-source.json")
        status = MF.recompute_status(run["results"], run["keys"])
        fit_bytes = fit_tmp.read_bytes()
        # Final freshness and output integrity before publication: the live inputs must still match
        # the captured bytes, and each published output must still match its record.
        now = capture(project)
        if first_stale(inputs_record(cap), now) is not None:
            raise MechError("stale.input", "An input changed during the fit; nothing was published.", 1)
        for name, meta in export["outputs"].items():
            if _sha(read_project(project, meta["path"])) != meta["sha256"]:
                raise MechError("export.altered", f"{name} changed during the fit; nothing was published.", 1)
        PIO.atomic_write(project, FIT_ASSEMBLY, fit_bytes)
        settings = _json(files["export-settings.json"], "export-settings.json")
        expected = {"electrical_release_id": src["electrical_release_id"], "release_id": src["release_id"],
                    "board_sha256": cap["board.kicad_pcb"]["sha256"],
                    "interface_sha256": cap["mechanical/board-interface.json"]["sha256"],
                    "component_evidence_sha256": cap["mechanical/component-evidence.json"]["sha256"],
                    "fixture_source_sha256": cap["mechanical/fixture-source.json"]["sha256"],
                    "export_settings_sha256": cap["export-settings.json"]["sha256"],
                    "toolchain_image_id": settings["image_id"], "fixture_id": src["fixture_id"]}
        report = {"record": REPORT_RECORD, "version": RECORD_VERSION, "expected": expected,
                  "inputs": inputs_record(cap), "export_record_sha256": _sha(export_bytes),
                  "outputs": {name: {"path": meta["path"], "role": meta["role"], "sha256": meta["sha256"],
                                     "size": meta["size"]} for name, meta in export["outputs"].items()},
                  "results": run["results"], "status": status,
                  "fit_assembly": {"path": FIT_ASSEMBLY, "sha256": _sha(fit_bytes), "size": len(fit_bytes)}}
        PIO.atomic_write(project, REPORT, (json.dumps(report, indent=2, sort_keys=True) + "\n").encode("utf-8"))
        import shutil  # noqa: PLC0415
        shutil.rmtree(work)
    return report


def run_release(project: Path) -> dict:
    """Publish mech-release/1 only for a complete, recomputed pass with every bound input and output current."""
    import mechanical_fit as MF  # noqa: PLC0415
    with PIO.project_lock(project, "mechanical-release"):
        report_path = PIO.confine(project, REPORT)
        if not report_path.is_file():
            raise MechError("report.missing", "Run the fit before the release. The report is missing.", 2)
        report_bytes = report_path.read_bytes()
        report = _json(report_bytes, "report.json")
        if report.get("record") != REPORT_RECORD or report.get("version") != RECORD_VERSION:
            raise MechError("report.record", "The report has the wrong record or version.", 1)
        cap = capture(project)
        files = files_of(cap)
        src = _json(files["mechanical/fixture-source.json"], "fixture-source.json")
        recomputed = MF.recompute_status(report.get("results", []), MF.required_keys(src))
        if recomputed["geometry_status"] != "pass" or recomputed["fit_status"] != "pass" or recomputed["missing"]:
            raise MechError("release.status", f"The report is not a complete pass: {recomputed}.", 1)
        if report.get("status") != recomputed:
            raise MechError("release.status", "The recorded status differs from the recomputed status.", 1)
        mismatch = release_first_mismatch(report["expected"], {
            "electrical_release_id": src["electrical_release_id"], "release_id": src["release_id"],
            "board_sha256": cap["board.kicad_pcb"]["sha256"],
            "interface_sha256": cap["mechanical/board-interface.json"]["sha256"],
            "component_evidence_sha256": cap["mechanical/component-evidence.json"]["sha256"],
            "fixture_source_sha256": cap["mechanical/fixture-source.json"]["sha256"],
            "export_settings_sha256": cap["export-settings.json"]["sha256"],
            "toolchain_image_id": _json(files["export-settings.json"], "settings")["image_id"],
            "fixture_id": src["fixture_id"]})
        if mismatch is not None:
            raise MechError("release.mismatch", f"First mismatch: {mismatch['input']} (expected "
                            f"{mismatch['expected']}, measured {mismatch['measured']}).", 1)
        stale = first_stale(report.get("inputs", {}), cap)
        if stale is not None:
            raise MechError("stale.input", f"{stale['input']} changed after the fit; run fit again.", 1)
        roles = {}
        outputs = []
        for name, meta in report["outputs"].items():
            data = read_project(project, meta["path"])
            if _sha(data) != meta["sha256"] or len(data) != meta["size"]:
                raise MechError("export.altered", f"The published {name} changed before release.", 1)
            roles[meta["role"]] = True
            outputs.append({"role": meta["role"], "path": meta["path"], "sha256": meta["sha256"], "size": meta["size"]})
        fit_bytes = read_project(project, FIT_ASSEMBLY)
        if _sha(fit_bytes) != report["fit_assembly"]["sha256"] or len(fit_bytes) != report["fit_assembly"]["size"]:
            raise MechError("stale.fit_assembly", "The fit assembly changed after the fit.", 1)
        roles["step_fit"] = True
        outputs.append({"role": "step_fit", "path": FIT_ASSEMBLY, "sha256": _sha(fit_bytes), "size": len(fit_bytes)})
        outputs.append({"role": "report", "path": REPORT, "sha256": _sha(report_bytes), "size": len(report_bytes)})
        roles["report"] = True
        missing = [r for r in ROLES if r not in roles]
        if missing:
            raise MechError("release.role_missing", "Missing output roles: " + ", ".join(missing) + ".", 1)
        for out_item in outputs:
            if out_item["role"] not in ROLES:
                raise MechError("release.role", f"Role {out_item['role']!r} is not in the closed list.", 2)
        # Final freshness and output integrity before publication.
        now = capture(project)
        if first_stale(inputs_record(cap), now) is not None:
            raise MechError("stale.input", "An input changed during the release; nothing was published.", 1)
        record = {"record": RELEASE_RECORD, "version": RECORD_VERSION,
                  "release_id": src["release_id"], "electrical_release_id": src["electrical_release_id"],
                  "fixture_id": src["fixture_id"], "board_revision": src["board_revision"],
                  "board_sha256": cap["board.kicad_pcb"]["sha256"],
                  "electrical_inputs": [{"path": "board.kicad_pcb", "sha256": cap["board.kicad_pcb"]["sha256"],
                                         "size": cap["board.kicad_pcb"]["size"]}],
                  "interface_sha256": cap["mechanical/board-interface.json"]["sha256"],
                  "component_evidence_sha256": cap["mechanical/component-evidence.json"]["sha256"],
                  "fixture_source_sha256": cap["mechanical/fixture-source.json"]["sha256"],
                  "export_settings_sha256": cap["export-settings.json"]["sha256"],
                  "toolchain_image_id": report["expected"]["toolchain_image_id"],
                  "outputs": sorted(outputs, key=lambda o: o["path"]),
                  "comparisons": [{"id": r["id"], "ref": r.get("ref"), "status": r["status"]} for r in report["results"]],
                  "status": recomputed, "first_mismatch": None}
        record["record_sha256"] = V.canonical_hash(record)
        for item in outputs:
            data = read_project(project, item["path"])
            if _sha(data) != item["sha256"] or len(data) != item["size"]:
                raise MechError("export.altered", f"{item['role']} ({item['path']}) changed during the release; "
                                "nothing was published.", 1)
        PIO.atomic_write(project, RELEASE, (json.dumps(record, indent=2, sort_keys=True) + "\n").encode("utf-8"))
    return record


# --------------------------------------------------------------------------- readiness and CLI


def readiness(project: Path) -> dict:
    result = {"route": "mechanical", "commands": ["export", "fit", "release"],
              "geometry_module": "mechanical_fit.py", "dependency": "cadquery (PEP 723 header)", "state": "not_ready"}
    try:
        cap = capture(project)
        contract_check(files_of(cap))
    except MechError as err:
        result["reason"] = err.code
        return result
    except (OSError, ValueError, KeyError) as err:
        result["reason"] = f"records_invalid: {err}"
        return result
    result["state"] = "ready_for_export"
    return result


def _project_refusal(err):
    if type(err).__name__ == "UnsupportedDrill":
        return ("drill.unsupported", 2)
    if isinstance(err, PIO.LockHeld):
        return ("lock.held", 1)
    if isinstance(err, PIO.PathEscape):
        return ("path.escape", 1)
    if isinstance(err, (PIO.PostReplaceError, PIO.PostRenameError)):
        return ("publish.post_replace", 3)
    return None


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Mechanical fit (B11): contract, export, fit and release.")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("check", help="run the contract rules on a fixture directory")
    p.add_argument("--fixture", required=True, type=Path)
    q = sub.add_parser("readiness", help="report the mechanical route state")
    q.add_argument("--project", required=True, type=Path)
    e = sub.add_parser("export", help="export STEP, DXF and separate drill files in the pinned local image")
    e.add_argument("--project", required=True, type=Path)
    e.add_argument("--image", default="localhost/cad-skills-pcb:b6")
    f = sub.add_parser("fit", help="run comparisons C01 to C12 on the published export")
    f.add_argument("--project", required=True, type=Path)
    r = sub.add_parser("release", help="publish mech-release/1 when the fit is a complete pass")
    r.add_argument("--project", required=True, type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "check":
            print(json.dumps(check_fixture(args.fixture), sort_keys=True))
            return 0
        if args.command == "readiness":
            print(json.dumps(readiness(args.project), sort_keys=True))
            return 0
        if args.command == "export":
            print(json.dumps(run_export(args.project, args.image)["exits"], sort_keys=True))
            return 0
        if args.command == "fit":
            report = run_fit(args.project)
            print(json.dumps(report["status"], sort_keys=True))
            return 0 if report["status"]["geometry_status"] == "pass" and report["status"]["fit_status"] == "pass" else 1
        record = run_release(args.project)
        print(json.dumps({"release_id": record["release_id"], "record_sha256": record["record_sha256"]}, sort_keys=True))
        return 0
    except MechError as err:
        print(f"{err.code}: {err.message}", file=sys.stderr)
        return err.status
    except Exception as err:  # noqa: BLE001 (classified below; anything unknown is a tool failure)
        mapped = _project_refusal(err)
        if mapped is None:
            print(f"mechanical.tool: {err}", file=sys.stderr)
            return 3
        print(f"{mapped[0]}: {err}", file=sys.stderr)
        return mapped[1]


if __name__ == "__main__":
    raise SystemExit(main())
