#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Checks and tool runs for a KiCad board project. The CLI never designs a circuit.

  uv run scripts/pcb.py env [--project DIR] [--image REF] [--json]
  uv run scripts/pcb.py check [--project DIR] [--for erc|drc|sim|ready]
  uv run scripts/pcb.py erc [--project DIR]
  uv run scripts/pcb.py drc [--project DIR] [--refill-zones]
  uv run scripts/pcb.py sim [--project DIR]
  uv run scripts/pcb.py settings [--project DIR] [--apply]
  uv run scripts/pcb.py update --adapter manual|gui [--project DIR]

Every tool runs in a disposable copy of the input files inside the runtime image. The
live project is never mounted. A command that writes holds the project lock. Each result
has three files: the raw tool bytes (named by their SHA-256), a binding file with the
full input hashes, and a result file that holds the decision. The result file is written last.

Exit status (highest priority first):
  3  Tool execution or result failure: unexpected tool exit, missing output, unparsable report,
     missing measured value, or a failed publication step after a replacement.
  2  Incorrect invocation, missing prerequisite, runtime mismatch, or an unsupported adapter.
  1  Invalid record, unwaived violation, failed assertion, stale or missing evidence, lock refusal.
  0  Complete success under the operation's policy.
"""

from __future__ import annotations

import argparse
import contextlib
import csv
import glob
import hashlib
import json
import math
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import identity as IDN  # noqa: E402
import project_io as PIO  # noqa: E402
import sexp  # noqa: E402
import validate as VAL  # noqa: E402
import yaml  # noqa: E402

SKILL_ROOT = HERE.parent
SCHEMAS = SKILL_ROOT / "contracts" / "schemas"
DEFAULT_IMAGE = "localhost/cad-skills-pcb:b6"
OK, VIOLATION, INVOCATION, TOOL = 0, 1, 2, 3
GUI_TIMEOUT = 900
NIL_UUID = "00000000-0000-0000-0000-000000000000"
UUID_RE = re.compile(r"^[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}$")
VIOLATION_SEVERITIES = {"error", "warning", "exclusion"}
PLOT_CONTRACT = {"drillshape": "0", "usegerberattributes": "no", "usegerberadvancedattributes": "no"}
ROOT_SCH = "kicad/board.kicad_sch"
BOARD = "kicad/board.kicad_pcb"
PROJECT_FILE = "kicad/board.kicad_pro"
SHEET_RE = re.compile(r'\(property\s+"Sheetfile"\s+"([^"]+)"')


class Refusal(Exception):
    """A stop with a stable code, a message and an exit status."""

    def __init__(self, code: str, message: str, status: int):
        super().__init__(message)
        self.code, self.status = code, status


def say(code: str, message: str) -> None:
    print(f"{code}: {message}", file=sys.stderr)


def sha(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def write_bytes(project: Path, rel: str, data: bytes) -> None:
    """Atomic write of a file under the project. The caller holds the lock."""
    PIO.atomic_write(project, rel, data)


def write_json(project: Path, rel: str, value) -> bytes:
    data = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    write_bytes(project, rel, data)
    return data


# --------------------------------------------------------------------------- project closure


def sheet_paths(project: Path, root_rel: str) -> list[str]:
    """Return the schematic sheets of the root, found by walking the Sheetfile entries."""
    found, todo, seen = [], [root_rel], set()
    while todo:
        rel = todo.pop(0)
        if rel in seen:
            continue
        seen.add(rel)
        found.append(rel)
        path = PIO.confine(project, rel, must_exist=True)
        text = path.read_text(encoding="utf-8", errors="replace")
        for target in SHEET_RE.findall(text):
            sub = str((Path(rel).parent / target).as_posix())
            todo.append(os.path.normpath(sub))
    return found


SYSTEM_LIBRARY_ROOTS = ("/usr/share/kicad/",)
LIBRARY_TABLES = ("kicad/fp-lib-table", "kicad/sym-lib-table")
LIBRARY_URI = re.compile(r'\(uri\s+"([^"]*)"\)')


def library_closure(project: Path) -> set[str]:
    """The files of the project-local libraries that the library tables name, nested paths included (Codex 4).

    A system library under the runtime identity needs no file here. Any other reference that leaves the project or
    uses an unknown variable is refused. A named path that does not exist is also refused.
    """
    out = set()
    kicad_dir = project / "kicad"
    for table in LIBRARY_TABLES:
        path = project / table
        if not path.is_file():
            continue
        for uri in LIBRARY_URI.findall(path.read_text(encoding="utf-8", errors="replace")):
            if uri.startswith(SYSTEM_LIBRARY_ROOTS):
                continue
            if "${KIPRJMOD}" in uri:
                target = Path(uri.replace("${KIPRJMOD}", str(kicad_dir)))
            elif "$" in uri or uri.startswith("/"):
                raise Refusal("pcb.external_library", f"{table} names {uri}, which is outside the project. Refused.",
                              INVOCATION)
            else:
                target = kicad_dir / uri
            try:
                target = PIO.confine(project, target, must_exist=True)
            except (PIO.PathEscape, FileNotFoundError):
                raise Refusal("pcb.library_missing", f"{table} names {uri}, which is not inside the project or is missing.",
                              INVOCATION)
            files = [target] if target.is_file() else [f for f in target.rglob("*") if f.is_file()]
            for f in files:
                out.add(f.relative_to(project).as_posix())
    return out


def closure_paths(project: Path, op: str) -> list[str]:
    """The input closure of one operation (section 8). Missing required files raise Refusal."""
    fixed = ["board.yaml", "variants.yaml", "toolchain.lock.json", "manufacturing/export.yaml",
             "manufacturing/waivers.yaml", "manufacturing/supplier.yaml", "mechanical/board-interface.json",
             BOARD, PROJECT_FILE]
    required = {"board.yaml", "variants.yaml", "toolchain.lock.json", "manufacturing/export.yaml",
                "manufacturing/waivers.yaml", "manufacturing/supplier.yaml", BOARD, PROJECT_FILE}
    rels = set()
    for rel in fixed:
        if (project / rel).is_file() or rel in required:
            rels.add(rel)
    rels.update(sheet_paths(project, ROOT_SCH))
    for pattern in ("kicad/*.kicad_dru", "kicad/fp-lib-table", "kicad/sym-lib-table", "kicad/*.kicad_sym",
                    "kicad/*.pretty/*.kicad_mod"):
        for hit in glob.glob(str(project / pattern)):
            rels.add(Path(hit).relative_to(project).as_posix())
    rels.update(library_closure(project))
    if op == "sim":
        rels.update(Path(p).relative_to(project).as_posix() for p in glob.glob(str(project / "simulations/*.cir")))
        rels.add("simulations/assertions.json")
    out = []
    for rel in sorted(rels):
        path = PIO.confine(project, rel)
        if not path.is_file():
            if rel in required or (op == "sim" and rel == "simulations/assertions.json"):
                raise Refusal("pcb.input_missing", f"The file {rel} is missing.", INVOCATION)
            continue
        out.append(rel)
    return out


def hash_closure(project: Path, rels: list[str]) -> dict[str, str]:
    return {rel: sha(PIO.confine(project, rel, must_exist=True).read_bytes()) for rel in rels}


def current_closure(project: Path, op: str) -> dict[str, str]:
    return hash_closure(project, closure_paths(project, op))


# --------------------------------------------------------------------------- records


def load_record(project: Path, rel: str) -> dict:
    path = PIO.confine(project, rel, must_exist=True)
    return VAL.load_record(path)


def board_revision(project: Path) -> str:
    return load_record(project, "board.yaml")["release_revision"]


STAGING: list[Path] = []


def stage_snapshot(project: Path, op: str) -> tuple[Path, dict[str, str]]:
    """Read each closure file once, write those bytes into a new staging directory, and hash the same bytes.

    The returned closure is the evidence of what the tool saw. A later live hash that differs means the
    source changed, and the caller refuses to publish.
    """
    rels = closure_paths(project, op)
    token = os.urandom(6).hex()
    stage = PIO.confine(project, f"out/staging/{op}-{token}")
    stage.mkdir(parents=True, exist_ok=False)
    STAGING.append(stage)
    closure = {}
    for rel in rels:
        data = PIO.confine(project, rel, must_exist=True).read_bytes()
        target = stage / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
        closure[rel] = sha(data)
    return stage, closure


# --------------------------------------------------------------------------- runtime


def image_id(ref: str | None) -> str | None:
    if ref is None:
        return None
    proc = subprocess.run(["podman", "image", "inspect", ref, "--format", "{{.Id}}"],
                          capture_output=True, text=True)
    if proc.returncode != 0:
        return None
    return proc.stdout.strip()


def container_argv(image: str | None, workdir: Path, argv: list[str], worker: Path | None = None) -> list[str]:
    """The command for one tool. With an image, podman runs it. With image None (native route), the
    /work and /worker paths of the tool arguments map to the staged directories and the tool runs directly."""
    if image is None:
        mapped = []
        for arg in argv:
            if arg == "/work" or arg.startswith("/work/"):
                arg = str(workdir) + arg[len("/work"):]
            elif worker is not None and (arg == "/worker" or arg.startswith("/worker/")):
                arg = str(worker) + arg[len("/worker"):]
            mapped.append(arg)
        return mapped
    cmd = ["podman", "run", "--rm", "--pull=never", "--network", "none", "--security-opt", "label=disable",
           "-w", "/work", "-v", f"{workdir}:/work"]
    if worker is not None:
        cmd += ["-v", f"{worker}:/worker:ro"]
    return cmd + [image] + argv


def run_in_container(image: str, workdir: Path, argv: list[str], log_stem: Path) -> int:
    """Run one tool. Keep stdout and stderr next to the staged files. Return the tool exit."""
    proc = subprocess.run(container_argv(image, workdir, argv), capture_output=True, timeout=1800)
    log_stem.with_suffix(".stdout").write_bytes(proc.stdout)
    log_stem.with_suffix(".stderr").write_bytes(proc.stderr)
    return proc.returncode


def runtime_lock(project: Path) -> dict:
    lock = load_record(project, "toolchain.lock.json")
    if lock["execution"] != "container":
        raise Refusal("runtime.native_unsupported",
                      "The lock asks for native execution. This checkpoint supports the container runtime only.",
                      INVOCATION)
    return lock


def select_runtime(lock: dict, requested: str | None) -> str:
    """Apply --runtime auto|container|native (section 4). Return the execution route. Nothing falls back silently."""
    execution = lock["execution"]
    choice = requested or "auto"
    if choice == "container" and execution != "container":
        raise Refusal("runtime.conflict", f"--runtime container conflicts with the lock (execution is {execution}).",
                      INVOCATION)
    if choice == "native" and execution != "native":
        raise Refusal("runtime.conflict", f"--runtime native conflicts with the lock (execution is {execution}).",
                      INVOCATION)
    return execution


# Tools that each operation needs on the native route. A missing tool blocks only the operations that use it.
OP_TOOLS = {"erc": ("kicad-cli",), "drc": ("kicad-cli",), "sim": ("ngspice",), "export": ("kicad-cli", "pcbnew"),
            "update": ("kicad-cli",), "settings": (), "interface": (), "check": ()}


def native_check(op: str | None = None) -> None:
    """Check the native prerequisites of one operation. op None (env) checks every tool."""
    tools = OP_TOOLS[op] if op else ("kicad-cli", "ngspice", "pcbnew")
    missing = [name for name in tools if name != "pcbnew" and shutil.which(name) is None]
    if "pcbnew" in tools:
        probe = subprocess.run(["/usr/bin/python3", "-c", "import pcbnew"], capture_output=True, text=True)
        if probe.returncode != 0:
            missing.append("pcbnew")
    if missing:
        raise Refusal("runtime.native_unavailable",
                      f"The native route needs {', '.join(missing)} for this operation.", INVOCATION)


def native_versions_ok(lock: dict, op: str | None) -> None:
    """Measure only the tools of this operation and compare them with the lock (section 4).

    A tool that the operation needs but that cannot be measured is refused with exit 2, never a traceback.
    """
    needed = OP_TOOLS[op] if op else ("kicad-cli", "ngspice", "pcbnew")
    measured = measure_tools(None, tools=needed)
    for tool in needed:
        if measured[tool]["exit"] != 0 or measured[tool]["version"] is None:
            raise Refusal("runtime.native_unavailable",
                          f"{tool} could not be measured for this operation.", INVOCATION)
    checks = {"kicad-cli": ("kicad", measured["kicad-cli"]["version"] if "kicad-cli" in measured else None),
              "ngspice": ("ngspice", (measured["ngspice"]["version"] or "").split("-")[-1] if "ngspice" in measured else None),
              "pcbnew": ("kicad", (measured["pcbnew"]["version"] or "").split("-")[0] if "pcbnew" in measured else None)}
    for tool in needed:
        lock_name, found = checks[tool]
        entry = lock["tools"].get(lock_name, {})
        if not entry.get("used") or "version" not in entry:
            continue
        if found != entry["version"]:
            raise Refusal("runtime.version_mismatch",
                          f"{tool} measures {found!r} but the lock names {entry['version']!r}. Revise the lock on purpose.",
                          INVOCATION)


def container_image(project: Path, explicit: str | None, runtime: str | None = None, op: str | None = None) -> str | None:
    """The runtime for a command with a project. Return the image, or None for the native route.
    The lock decides. A different image is a refusal."""
    lock = load_record(project, "toolchain.lock.json")
    if select_runtime(lock, runtime) == "native":
        if explicit:
            raise Refusal("runtime.conflict", "--image does not apply to the native route.", INVOCATION)
        native_check(op)
        native_versions_ok(lock, op)
        return None
    ref = lock["container"]["image"]
    if explicit and explicit != ref:
        raise Refusal("runtime.conflict", f"--image {explicit} differs from the lock image {ref}.", INVOCATION)
    found = image_id(ref)
    if found is None:
        raise Refusal("runtime.image_missing", f"The image {ref} is not present. Build it (references/runtime.md).", INVOCATION)
    if found.split(":")[-1] != lock["container"]["digest"].split(":")[-1]:
        raise Refusal("runtime.image_mismatch",
                      f"The image ID {found} differs from the lock digest. Revise toolchain.lock.json on purpose.",
                      INVOCATION)
    return ref


VERSION_COMMANDS = {
    "kicad-cli": ["kicad-cli", "version"],
    "ngspice": ["sh", "-c", "ngspice --version | grep -o 'ngspice-[0-9.]*' | head -n 1"],
    "uv": ["uv", "--version"],
    "pcbnew": ["/usr/bin/python3", "-c", "import pcbnew; print(pcbnew.GetBuildVersion())"],
}


def measure_tools(image: str | None, tools: tuple | None = None) -> dict:
    """Run the version commands of the named tools only (all tools when tools is None).

    A missing executable is a recorded result (exit 127, version None), never an uncaught exception.
    """
    names = tools if tools is not None else tuple(VERSION_COMMANDS)
    out = {}
    with tempfile.TemporaryDirectory(prefix="pcb-env-") as tmp:
        for name in names:
            try:
                proc = subprocess.run(container_argv(image, Path(tmp), VERSION_COMMANDS[name]),
                                      capture_output=True, text=True, timeout=300)
            except OSError:
                out[name] = {"exit": 127, "version": None}
                continue
            text = proc.stdout.strip().splitlines()
            out[name] = {"exit": proc.returncode, "version": text[-1] if text and proc.returncode == 0 else None}
    return out


# --------------------------------------------------------------------------- findings


def findings_of(report: dict, list_keys: tuple[str, ...]) -> list[dict]:
    """Flatten the violation lists of an ERC or DRC report. Each finding has a rule and object UUIDs."""
    entries = []
    for key in list_keys:
        if key == "sheets":
            for sheet in report.get("sheets", []):
                entries.extend(sheet.get("violations", []))
        else:
            entries.extend(report.get(key, []))
    out = []
    for item in entries:
        objects = []
        for obj in item.get("items", []):
            objects.append(obj.get("uuid"))
        out.append({"rule": item.get("type", ""), "severity": item.get("severity", ""),
                    "description": item.get("description", ""), "objects": objects})
    return out


def uuid_occurrences(project: Path, closure: dict[str, str]) -> dict[str, int]:
    """Count the text occurrences of each UUID in the schematic and board files of the closure."""
    text = ""
    for rel in closure:
        if rel.endswith((".kicad_sch", ".kicad_pcb")):
            text += PIO.confine(project, rel).read_text(encoding="utf-8", errors="replace") + "\n"
    counts: dict[str, int] = {}
    for uid in set(re.findall(r"[0-9a-fA-F]{8}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{4}-[0-9a-fA-F]{12}", text)):
        counts[uid] = len(re.findall(re.escape(uid), text))
    return counts


def judge(project: Path, op: str, findings: list[dict], tool_exit: int, closure: dict[str, str],
          waivers: list[dict], revision: str, refs: dict) -> tuple[dict, int]:
    """Apply the waiver rules (section 7). Return (result body, exit status)."""
    violations = [f for f in findings if f["severity"] in VIOLATION_SEVERITIES]
    if (tool_exit == 5 and not violations) or (tool_exit == 0 and violations):
        raise Refusal("tool.exit_mismatch", f"The {op} exit {tool_exit} does not match its findings.", TOOL)
    if tool_exit not in (0, 5):
        raise Refusal("tool.exit_unexpected", f"The {op} tool exited with {tool_exit}.", TOOL)
    counts = uuid_occurrences(project, closure)
    kind_waivers = [w for w in waivers if w["kind"] == op]
    used, touched, waived, unwaived = set(), set(), [], []
    for f in violations:
        objects = f["objects"]
        if not objects or any(o is None or not UUID_RE.match(o) or o == NIL_UUID for o in objects):
            unwaived.append({**f, "reason": "waiver.object_unidentifiable"})
            continue
        if any(counts.get(o, 0) == 0 for o in objects):
            unwaived.append({**f, "reason": "waiver.object_absent"})
            continue
        if any(counts[o] > 1 for o in objects):
            unwaived.append({**f, "reason": "waiver.ambiguous_object"})
            continue
        matched = [i for i, w in enumerate(kind_waivers) if w["rule"] == f["rule"]
                   and len(w["objects"]) == len(set(w["objects"])) and set(w["objects"]) == set(objects)]
        if not matched:
            unwaived.append({**f, "reason": "unwaived"})
            continue
        touched.update(matched)
        valid = []
        for i in matched:
            w = kind_waivers[i]
            if w["revision"] != revision or w["board_sha256"] != refs["board"]:
                continue
            if op == "erc" and w["schematic_sha256"] != refs["schematic"]:
                continue
            if op == "drc" and w["schematic_sha256"] is not None and w["schematic_sha256"] != refs["schematic"]:
                continue
            valid.append(i)
        if valid:
            used.update(valid)
            waived.append({**f, "waiver": kind_waivers[valid[0]]["id"]})
        else:
            unwaived.append({**f, "reason": "waiver.stale"})
    unused = [w["id"] for i, w in enumerate(kind_waivers) if i not in touched]
    if unused:
        for uid in unused:
            unwaived.append({"rule": "waiver.unused", "severity": "error", "description": f"Waiver {uid} matches no finding.",
                             "objects": [], "reason": "waiver.unused"})
    if unwaived:
        status, code = "fail", VIOLATION
    elif waived:
        status, code = "pass_with_waivers", OK
    else:
        status, code = "pass", OK
    body = {"status": status, "exit_code": code, "tool_exit": tool_exit, "findings": findings,
            "waived": waived, "unwaived": unwaived}
    return body, code


def load_waivers(project: Path) -> list[dict]:
    return load_record(project, "manufacturing/waivers.yaml")["waivers"]


# --------------------------------------------------------------------------- publication


def publish_report(project: Path, op: str, raw: bytes, options: dict, closure: dict[str, str],
                   image: str, tool_exit: int, body: dict, tool_versions: dict) -> None:
    """Write raw, binding, result in that order. The caller holds the lock."""
    raw_rel = f"out/reports/raw/{op}-{sha(raw)}.{'log' if op == 'sim' else 'json'}"
    write_bytes(project, raw_rel, raw)
    binding = {"record": "pcb-design/binding", "version": "1", "operation": op, "options": options,
               "runtime": {"execution": "native" if image is None else "container", "image": image,
                           "image_id": image_id(image)}, "tool_versions": tool_versions,
               "tool_exit": tool_exit, "raw_file": raw_rel, "raw_sha256": sha(raw), "closure": closure}
    binding_bytes = write_json(project, f"out/reports/{op}.binding.json", binding)
    result = {"record": "pcb-design/result", "version": "1", "operation": op,
              "binding_sha256": sha(binding_bytes), **body}
    write_json(project, f"out/reports/{op}.result.json", result)


def check_report(project: Path, op: str) -> tuple[bool, str]:
    """Return (ok, reason) for one stored operation. Ok needs a current, pass-status result."""
    rdir = PIO.confine(project, "out/reports")
    result_path, binding_path = rdir / f"{op}.result.json", rdir / f"{op}.binding.json"
    if not result_path.is_file() or not binding_path.is_file():
        return False, "missing"
    binding_bytes = binding_path.read_bytes()
    result = json.loads(result_path.read_text())
    if result.get("binding_sha256") != sha(binding_bytes):
        return False, "binding_mismatch"
    binding = json.loads(binding_bytes)
    raw_path = PIO.confine(project, binding["raw_file"], must_exist=True) if (project / binding["raw_file"]).is_file() else None
    if raw_path is None or sha(raw_path.read_bytes()) != binding["raw_sha256"]:
        return False, "raw_missing"
    if binding["closure"] != current_closure(project, op):
        return False, "stale"
    if result["status"] not in ("pass", "pass_with_waivers"):
        return False, "failed"
    return True, result["status"]


# --------------------------------------------------------------------------- commands


def project_arg(path: str) -> Path:
    project = Path(path).resolve()
    if not project.is_dir():
        raise Refusal("pcb.project_missing", f"The project directory {path} does not exist.", INVOCATION)
    return project


def cmd_env(args) -> int:
    report = {"podman": shutil.which("podman") is not None, "image": None, "image_id": None, "tools": None,
              "lock": None}
    if args.project:
        route = select_runtime(load_record(project_arg(args.project), "toolchain.lock.json"), args.runtime)
    else:
        route = "native" if args.runtime == "native" else "container"
    if route == "native":
        native_check()
        report.update({"execution": "native", "image": None, "image_id": None, "status": "measured",
                       "tools": measure_tools(None)})
        return emit(report, args.json, OK)
    image = args.image or DEFAULT_IMAGE
    if args.project:
        project = project_arg(args.project)
        lock = load_record(project, "toolchain.lock.json")
        report["lock"] = {"image": lock["container"]["image"], "digest": lock["container"]["digest"]}
        image = args.image or lock["container"]["image"]
    report["image"] = image
    report["image_id"] = image_id(image) if report["podman"] else None
    if report["image_id"] is None:
        report["status"] = "image_missing"
        say("runtime.image_missing", f"The image {image} is not present. Build it (references/runtime.md).")
        return emit(report, args.json, INVOCATION)
    report["tools"] = measure_tools(image)
    report["status"] = "measured"
    if args.project and report["lock"]:
        matches = report["lock"]["digest"].split(":")[-1] == report["image_id"].split(":")[-1]
        report["lock_matches_image"] = matches
        if not matches:
            report["status"] = "lock_mismatch"
            return emit(report, args.json, INVOCATION)
    return emit(report, args.json, OK)


def emit(report: dict, as_json: bool, status: int) -> int:
    if as_json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")
    return status


def tool_versions_of(image_ref: str | None, op: str | None = None) -> dict:
    """The measured versions of the tools of one operation, for the binding (publication, Pi section 13)."""
    names = OP_TOOLS[op] if op else tuple(VERSION_COMMANDS)
    return {k: v["version"] for k, v in measure_tools(image_ref, tools=names).items()}


def cmd_erc(args) -> int:
    project = project_arg(args.project)
    with PIO.project_lock(project, "erc"):
        image = container_image(project, args.image, getattr(args, "runtime", None), "erc")
        stage, closure = stage_snapshot(project, "erc")
        argv = ["kicad-cli", "sch", "erc", "--exit-code-violations", "--severity-all", "--format", "json",
                "-o", "/work/erc.json", "/work/" + ROOT_SCH]
        tool_exit = run_in_container(image, stage, argv, stage / "run")
        raw_path = stage / "erc.json"
        if not raw_path.is_file():
            raise Refusal("tool.output_missing", "The ERC tool wrote no report.", TOOL)
        raw = raw_path.read_bytes()
        findings = findings_of(json.loads(raw), ("sheets",))
        if current_closure(project, "erc") != closure:
            raise Refusal("pcb.source_changed", "A source changed during the ERC run. Nothing is published.", VIOLATION)
        refs = {"board": closure[BOARD], "schematic": closure[ROOT_SCH]}
        body, code = judge(project, "erc", findings, tool_exit, closure, load_waivers(project),
                           board_revision(project), refs)
        publish_report(project, "erc", raw, {"command": argv}, closure, image, tool_exit, body,
                       tool_versions_of(image, "erc"))
    say_result("erc", body)
    return code


def say_result(op: str, body: dict) -> None:
    print(f"{op}: {body['status']} (findings {len(body['findings'])}, waived {len(body['waived'])}, "
          f"unwaived {len(body['unwaived'])})")
    for item in body["unwaived"]:
        print(f"  unwaived {item['rule']} {item.get('reason', '')} {item['objects']}")


# ---- board replacement (refill, settings) ----


def canonical_board(text: str, *, drop_fill: bool, plot: bool) -> tuple[list, dict]:
    """Parse a board and normalize it. Return (tree, plot values). Only the allowed forms change."""
    tree = sexp.parse(text)
    plot_values: dict = {}

    def walk(node):
        if not isinstance(node, list):
            return
        if node and node[0] == "pcbplotparams" and plot:
            kept = []
            for child in node:
                if isinstance(child, list) and child and child[0] in PLOT_CONTRACT:
                    plot_values.setdefault(child[0], []).append(child[1])
                    continue
                kept.append(child)
            node[:] = kept
        if node and node[0] == "zone" and drop_fill:
            node[:] = [c for c in node if not (isinstance(c, list) and c and c[0] == "filled_polygon")]
        for child in node:
            walk(child)

    walk(tree)
    return tree, plot_values


def board_equal(prior: str, current: str, *, fill: bool, plot: bool) -> tuple[bool, dict]:
    """Compare two boards after the allowed normalization. Return (equal, plot values of the current board)."""
    a, pa = canonical_board(prior, drop_fill=fill, plot=plot)
    b, pb = canonical_board(current, drop_fill=fill, plot=plot)
    return json.dumps(a) == json.dumps(b), pb


def replace_board(project: Path, new_bytes: bytes, op: str, *, fill: bool, plot: bool, expect: dict) -> None:
    """Preserve the prior board, then replace the live board. The caller holds the lock."""
    live = PIO.confine(project, BOARD, must_exist=True).read_bytes()
    equal, _ = board_equal(live.decode("utf-8"), new_bytes.decode("utf-8"), fill=fill, plot=plot)
    if not equal:
        raise Refusal("board.unexpected_change", f"The {op} result changes the board beyond the allowed forms.", VIOLATION)
    if plot:
        for text in (live.decode("utf-8"), new_bytes.decode("utf-8")):
            _, values = canonical_board(text, drop_fill=False, plot=True)
            if any(len(values.get(k, [])) != 1 for k in PLOT_CONTRACT):
                raise Refusal("settings.unsupported_board", "Each plot setting must occur once in the board.", INVOCATION)
    history = PIO.confine(project, f"out/history/boards/{sha(live)}.kicad_pcb")
    history.parent.mkdir(parents=True, exist_ok=True)
    if not history.exists():
        with open(history, "xb") as handle:
            handle.write(live)
    if PIO.confine(project, BOARD, must_exist=True).read_bytes() != live:
        raise Refusal("board.changed_during_op", "The live board changed during the operation.", VIOLATION)
    expect_bytes = (json.dumps(expect, indent=2, sort_keys=True) + "\n").encode("utf-8")
    write_bytes(project, f"out/reports/{op}.expect.json", expect_bytes)
    write_bytes(project, BOARD, new_bytes)
    record_board_change(project, op, live, new_bytes, expect_bytes)


def cmd_drc(args) -> int:
    project = project_arg(args.project)
    with PIO.project_lock(project, "drc"):
        image = container_image(project, args.image, getattr(args, "runtime", None), "drc")
        stage, closure = stage_snapshot(project, "drc")
        argv = ["kicad-cli", "pcb", "drc"] + (["--refill-zones", "--save-board"] if args.refill_zones else []) + \
            ["--schematic-parity", "--exit-code-violations", "--severity-all", "--format", "json",
             "-o", "/work/drc.json", "/work/" + BOARD]
        tool_exit = run_in_container(image, stage, argv, stage / "run")
        raw_path = stage / "drc.json"
        if not raw_path.is_file():
            raise Refusal("tool.output_missing", "The DRC tool wrote no report.", TOOL)
        raw = raw_path.read_bytes()
        findings = findings_of(json.loads(raw), ("violations", "unconnected_items", "schematic_parity"))
        if current_closure(project, "drc") != closure:
            raise Refusal("pcb.source_changed", "A source changed during the DRC run. Nothing is published.", VIOLATION)
        if args.refill_zones:
            refilled = (stage / BOARD).read_bytes()
            if refilled != PIO.confine(project, BOARD, must_exist=True).read_bytes():
                replace_board(project, refilled, "refill", fill=True, plot=False,
                              expect={"differences": []})
                closure = current_closure(project, "drc")
        refs = {"board": closure[BOARD], "schematic": closure[ROOT_SCH]}
        body, code = judge(project, "drc", findings, tool_exit, closure, load_waivers(project),
                           board_revision(project), refs)
        publish_report(project, "drc", raw, {"command": argv, "refill_zones": args.refill_zones},
                       closure, image, tool_exit, body, tool_versions_of(image, "drc"))
    say_result("drc", body)
    return code


ASSERTION_FIELDS = {"circuit", "measurement", "expected", "tolerance"}
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*")
CIRCUIT = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.-]*\.cir")
SIM_RANGE = 1e12  # the supported magnitude of a simulation measurement; larger values are input defects
DEPENDENCY_DIRECTIVE = re.compile(r"(?im)^\s*\.(include|inc|lib|hdl|osdi|load)\b")


def finite_number(value) -> bool:
    """A finite number inside the supported simulation range. A value too large for a float is a defect, not a crash."""
    if not isinstance(value, (int, float)) or isinstance(value, bool):
        return False
    try:
        number = float(value)
    except OverflowError:
        return False
    return math.isfinite(number) and abs(number) <= SIM_RANGE


def load_assertions(path: Path) -> list[dict]:
    """Parse and validate the assertion records of one staged file. Every defect is exit 1, never a traceback."""
    rel = "simulations/assertions.json"
    try:
        data = strict_json(path.read_text(encoding="utf-8"))
    except (OSError, UnicodeDecodeError, ValueError) as err:
        raise Refusal("assertion.malformed", f"{rel} is not readable JSON: {err}", VIOLATION)
    if not isinstance(data, list) or not data:
        raise Refusal("assertion.malformed", f"{rel} must hold a non-empty list.", VIOLATION)
    seen = set()
    for i, item in enumerate(data):
        if not isinstance(item, dict) or set(item) != ASSERTION_FIELDS:
            raise Refusal("assertion.malformed", f"{rel} entry {i} must have exactly the four fields.", VIOLATION)
        circuit, measurement = item["circuit"], item["measurement"]
        if not isinstance(circuit, str) or CIRCUIT.fullmatch(circuit) is None:
            raise Refusal("assertion.malformed", f"{rel} entry {i}: circuit must be a file name ending in .cir.", VIOLATION)
        if not isinstance(measurement, str) or IDENT.fullmatch(measurement) is None:
            raise Refusal("assertion.malformed", f"{rel} entry {i}: measurement must be an identifier.", VIOLATION)
        if not finite_number(item["expected"]):
            raise Refusal("assertion.malformed", f"{rel} entry {i}: expected must be a finite number in the supported range.", VIOLATION)
        if not finite_number(item["tolerance"]) or item["tolerance"] < 0:
            raise Refusal("assertion.malformed", f"{rel} entry {i}: tolerance must be finite, not negative and in the supported range.", VIOLATION)
        key = (circuit, measurement)
        if key in seen:
            raise Refusal("assertion.malformed", f"{rel}: the pair {key} occurs two times.", VIOLATION)
        seen.add(key)
    return data


def refuse_dependencies(stage: Path, circuits: list[str]) -> None:
    """Refuse circuit directives that name files outside the input closure (Codex finding 3)."""
    for circuit in circuits:
        text = (stage / "simulations" / circuit).read_text(encoding="utf-8", errors="replace")
        found = DEPENDENCY_DIRECTIVE.search(text)
        if found:
            raise Refusal("sim.unsupported_dependency",
                          f"simulations/{circuit} uses the directive {found.group(0).strip()}. The dependency is not in "
                          "the input closure, so the run is refused.", INVOCATION)


def measured_value(log: str, name: str) -> float:
    matches = re.findall(rf"(?m)^\s*{re.escape(name)}\s*=\s*([-+]?[0-9.]+(?:[eE][-+]?[0-9]+)?)", log)
    if not matches:
        raise Refusal("sim.missing_value", f"The log has no value {name}.", TOOL)
    return float(matches[-1])


def cmd_sim(args) -> int:
    project = project_arg(args.project)
    with PIO.project_lock(project, "sim"):
        image = container_image(project, args.image, getattr(args, "runtime", None), "sim")
        stage, closure = stage_snapshot(project, "sim")
        assertions = load_assertions(stage / "simulations/assertions.json")
        circuits = sorted({a["circuit"] for a in assertions})
        for circuit in circuits:
            if f"simulations/{circuit}" not in closure:
                raise Refusal("sim.circuit_missing", f"The circuit simulations/{circuit} is missing.", INVOCATION)
        refuse_dependencies(stage, circuits)
        logs, exits = [], {}
        for circuit in circuits:
            name = f"simulations/{circuit}"
            base = Path(circuit).stem
            exits[circuit] = run_in_container(image, stage, ["ngspice", "-b", f"/work/{name}", "-o",
                                                            f"/work/{base}.log"], stage / f"run-{base}")
            log_path = stage / f"{base}.log"
            if not log_path.is_file():
                raise Refusal("tool.output_missing", f"ngspice wrote no log for {circuit}.", TOOL)
            logs.append(f"== circuit {circuit} ==\n".encode() + log_path.read_bytes())
        raw = b"".join(logs)
        if any(code not in (0,) for code in exits.values()):
            raise Refusal("tool.exit_unexpected", f"ngspice exited with {exits}.", TOOL)
        if current_closure(project, "sim") != closure:
            raise Refusal("pcb.source_changed", "A source changed during the simulation. Nothing is published.", VIOLATION)
        findings, failed = [], False
        for item in assertions:
            log_text = (stage / f"{Path(item['circuit']).stem}.log").read_text(errors="replace")
            value = measured_value(log_text, item["measurement"])
            ok = abs(value - item["expected"]) <= item["tolerance"]
            failed = failed or not ok
            findings.append({"rule": "sim.assertion", "severity": "error" if not ok else "info",
                             "description": f"{item['circuit']} {item['measurement']} = {value} "
                                            f"(expected {item['expected']}, tolerance {item['tolerance']})",
                             "objects": []})
        body = {"status": "fail" if failed else "pass", "exit_code": VIOLATION if failed else OK, "tool_exit": 0,
                "findings": findings, "waived": [], "unwaived": [f for f in findings if f["severity"] == "error"]}
        publish_report(project, "sim", raw, {"command": ["ngspice", "-b"], "circuits": circuits},
                       closure, image, 0, body, tool_versions_of(image, "sim"))
    say_result("sim", body)
    return body["exit_code"]


def cmd_settings(args) -> int:
    project = project_arg(args.project)
    text = PIO.confine(project, BOARD, must_exist=True).read_text(encoding="utf-8")
    _, plot = canonical_board(text, drop_fill=False, plot=True)
    problems = []
    for key, want in PLOT_CONTRACT.items():
        got = plot.get(key, [])
        if len(got) != 1:
            problems.append(f"{key} occurs {len(got)} times")
        elif str(got[0]) != want:
            problems.append(f"{key} is {got[0]!r}, expected {want!r}")
    if not args.apply:
        for p in problems:
            say("settings.plot_mismatch", p)
        print("settings: ok" if not problems else "settings: mismatch")
        return VIOLATION if problems else OK
    with PIO.project_lock(project, "settings"):
        new_text = text
        for key, want in PLOT_CONTRACT.items():
            pattern = re.compile(rf"\({re.escape(key)} [^()\s]+\)")
            if len(pattern.findall(new_text)) != 1:
                raise Refusal("settings.unsupported_board", f"{key} must occur once in the board.", INVOCATION)
            new_text = pattern.sub(f"({key} {want})", new_text)
        new_bytes = new_text.encode("utf-8")
        if new_bytes == text.encode("utf-8"):
            print("settings: already applied")
            return OK
        expect = {"differences": []}
        replace_board(project, new_bytes, "settings", fill=False, plot=True, expect=expect)
    print("settings: applied")
    return OK


def cmd_check(args) -> int:
    project = project_arg(args.project)
    problems = []
    records = VAL.build_report([], SCHEMAS, project, None)
    code, report = records
    for f in report["findings"]:
        problems.append((f["code"], f["file"], f["message"]))
    if code == INVOCATION or code == TOOL:
        for code_, file, message in problems:
            say(code_, f"{file}: {message}")
        return code if code >= 2 else INVOCATION
    for comp in sorted(glob.glob(str(project / "components" / "*.yaml"))):
        c_code, c_report = VAL.build_report([comp], SCHEMAS, None, None)
        for f in c_report["findings"]:
            problems.append((f["code"], f["file"], f["message"]))
    targets = ["erc", "drc", "sim"] if args.for_ == "ready" else [args.for_]
    if args.for_ == "ready":
        ok_iface, reason_iface = interface_ready(project)
        if not ok_iface:
            problems.append((f"interface.{reason_iface}", INTERFACE, "The interface is not ready."))
    if args.for_ == "export":
        targets = ["export"]
    for op in targets:
        if op == "sim" and not (project / "simulations").is_dir():
            continue
        ok, reason = check_report(project, op)
        if not ok:
            problems.append((f"report.{reason}", op, f"The {op} result is {reason}."))
        elif op == "export":
            for code_, message in export_problems(project):
                problems.append((code_, "export", message))
    staging = PIO.confine(project, "out/staging")
    if staging.is_dir():
        for residual in sorted(p for p in staging.iterdir() if p.is_dir()):
            problems.append(("staging.residual", residual.relative_to(project).as_posix(),
                             "A disposable staging directory remains from an interrupted run. Remove it."))
    for code_, file, message in problems:
        say(code_, f"{file}: {message}")
    print("check: ready" if not problems else "check: not ready")
    return VIOLATION if problems else OK


def export_problems(project: Path) -> list[tuple[str, str]]:
    """Compare the published export files with the output hashes bound in the export result (Codex and Pi)."""
    result = json.loads(PIO.confine(project, "out/reports/export.result.json").read_text())
    published = result.get("published")
    if not published:
        return [("export.not_published", "The export result names no published directory.")]
    out = []
    folder = PIO.confine(project, published)
    if not folder.is_dir():
        return [("export.missing_directory", f"The published directory {published} is missing.")]
    for rel, digest in sorted(result.get("outputs", {}).items()):
        path = folder / Path(rel).name
        if not path.is_file():
            out.append(("export.file_missing", f"{rel} is missing from {published}."))
        elif sha(path.read_bytes()) != digest:
            out.append(("export.file_changed", f"{rel} differs from the bound output hash."))
    return out


# Image IDs on which the gui adapter was measured. A new image is not certified by its version alone.
GUI_IMAGE_IDS = {"b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f"}


def gui_preflight(image: str) -> None:
    """Refuse the gui adapter unless this exact image ID was measured, and the KiCad, Xvfb and tool set exist (section 11)."""
    found = image_id(image)
    if found not in GUI_IMAGE_IDS:
        raise Refusal("update.adapter_unavailable",
                      f"The gui adapter is certified only for the measured image IDs. The image {image} has ID {found}. "
                      "Use the manual route, or measure this image first.", INVOCATION)
    measured = measure_tools(image)
    if measured["kicad-cli"]["version"] != "10.0.5":
        raise Refusal("update.adapter_unavailable",
                      f"The gui adapter is measured for KiCad 10.0.5 only; the image has {measured['kicad-cli']['version']}.",
                      INVOCATION)
    with tempfile.TemporaryDirectory(prefix="pcb-gui-") as tmp:
        proc = subprocess.run(container_argv(image, Path(tmp), ["sh", "-c",
                              "command -v Xvfb && command -v xdotool && command -v import && command -v kicad"]),
                              capture_output=True, text=True, timeout=300)
    if proc.returncode != 0:
        raise Refusal("update.adapter_unavailable", "Xvfb, xdotool, ImageMagick import or kicad is missing.", INVOCATION)


def cmd_update_gui(args, project: Path) -> int:
    with PIO.project_lock(project, "update-gui"):
        image = container_image(project, args.image, getattr(args, "runtime", None), "update")
        gui_preflight(image)
        if not args.expect:
            raise Refusal("update.expectation_missing", "The gui adapter needs --expect FILE, the predeclared identity "
                          "expectation. Write it before the update.", INVOCATION)
        expect_bytes = PIO.confine(project, args.expect, must_exist=True).read_bytes()
        expect = json.loads(expect_bytes)
        requested = {"relink": args.relink, "replace": args.replace, "delete": args.delete}
        stage, closure = stage_snapshot(project, "update")
        worker = stage / "worker"
        worker.mkdir()
        shutil.copyfile(HERE / "gui_update.py", worker / "gui_update.py")
        argv = ["uv", "run", "--no-project", "--no-config", "--offline", "--python", "/usr/bin/python3", "python", "/worker/gui_update.py", "--project", "/work/kicad", "--name", "board",
                "--label", "update", "--shots", "/work/out/gui-shots"]
        for name, value in requested.items():
            argv += [f"--{name}", value]
        proc = subprocess.run(container_argv(image, stage, argv, worker=worker), capture_output=True, text=True,
                              timeout=GUI_TIMEOUT)
        (stage / "gui.stdout").write_text(proc.stdout)
        (stage / "gui.stderr").write_text(proc.stderr)
        trace = PIO.confine(project, f"out/reports/update-trace/{sha(proc.stdout.encode())[:16]}")
        trace.mkdir(parents=True, exist_ok=True)
        for name in ("gui.stdout", "gui.stderr"):
            shutil.copyfile(stage / name, trace / name)
        if (stage / "out/gui-shots").is_dir():
            shutil.copytree(stage / "out/gui-shots", trace / "gui-shots", dirs_exist_ok=True)
        if proc.returncode != 0:
            raise Refusal("update.gui_failed", f"The GUI driver exited with {proc.returncode}.", TOOL)
        try:
            summary = json.loads(proc.stdout)
            if not isinstance(summary, dict) or not isinstance(summary.get("kicad_exit"), dict) \
                    or not isinstance(summary.get("options_measured"), dict):
                raise ValueError("the summary has no kicad_exit or options_measured object")
            for name in requested:
                if not isinstance(summary["options_measured"].get(name), dict) \
                        or not isinstance(summary["options_measured"][name].get("after"), bool):
                    raise ValueError(f"the summary has no measured state for {name}")
        except (ValueError, KeyError, TypeError) as err:
            raise Refusal("update.summary_malformed", f"The GUI summary is absent or malformed: {err}.", TOOL)
        if summary["kicad_exit"] != {"state": "exited", "code": 0}:
            raise Refusal("update.kicad_exit", f"KiCad did not exit normally: {summary['kicad_exit']}.", TOOL)
        for name, want in requested.items():
            measured = summary["options_measured"][name]["after"]
            if measured != (want == "on"):
                raise Refusal("update.option_mismatch", f"The {name} option is {measured}, requested {want}.", TOOL)
        prior_bytes = PIO.confine(project, BOARD, must_exist=True).read_bytes()
        new_bytes = (stage / BOARD).read_bytes()
        try:
            ident = IDN.compare(IDN.snapshot_text(prior_bytes.decode("utf-8")),
                                IDN.snapshot_text(new_bytes.decode("utf-8")), expect["differences"])
        except IDN.Unparsed as err:
            raise Refusal("identity.unparsed", str(err), TOOL)
        if ident["status"] != "equal":
            raise Refusal("update.identity_mismatch",
                          f"The saved board differs from the predeclared expectation: unexpected {ident['unexpected']}, "
                          f"missing {ident['missing']}. Nothing is published.", VIOLATION)
        drc_argv = ["kicad-cli", "pcb", "drc", "--schematic-parity", "--severity-all", "--format", "json",
                    "-o", "/work/update-drc.json", "/work/" + BOARD]
        code = run_in_container(image, stage, drc_argv, stage / "update-drc")
        if code != 0 or not (stage / "update-drc.json").is_file():
            raise Refusal("tool.drc_failed", f"The DRC after the update exited with {code}.", TOOL)
        drc = json.loads((stage / "update-drc.json").read_text())
        if drc.get("schematic_parity"):
            raise Refusal("update.parity", "The updated board has schematic parity findings. Nothing is published.",
                          VIOLATION)
        if current_closure(project, "update") != closure:
            raise Refusal("pcb.source_changed", "A source changed during the GUI update. Nothing is published.", VIOLATION)
        history = PIO.confine(project, f"out/history/boards/{sha(prior_bytes)}.kicad_pcb")
        history.parent.mkdir(parents=True, exist_ok=True)
        if not history.exists():
            with open(history, "xb") as handle:
                handle.write(prior_bytes)
        expect_out = (json.dumps(expect, indent=2, sort_keys=True) + "\n").encode("utf-8")
        write_bytes(project, "out/reports/update.expect.json", expect_out)
        write_bytes(project, BOARD, new_bytes)
        record_board_change(project, "update", prior_bytes, new_bytes, expect_out)
        diagnostics = [{"rule": item.get("type", ""), "severity": item.get("severity", ""),
                        "description": item.get("description", ""), "objects": [o.get("uuid") for o in item.get("items", [])]}
                       for key in ("violations", "unconnected_items") for item in drc.get(key, [])]
        state = "ready" if not diagnostics else "not_ready"
        body = {"status": "pass", "exit_code": OK, "tool_exit": 0, "findings": diagnostics, "waived": [], "unwaived": [],
                "state": state, "options": requested, "identity": ident["status"]}
        raw = json.dumps({"summary": summary, "drc": drc}, sort_keys=True).encode("utf-8")
        publish_report(project, "update", raw, {"command": argv, "options": requested}, closure, image, 0, body,
                       tool_versions_of(image, "update"))
    print(f"update: pass (state {state}, diagnostics {len(diagnostics)}); run drc, erc and sim next")
    return OK


def cmd_update(args) -> int:
    project = project_arg(args.project)
    if args.adapter == "gui":
        return cmd_update_gui(args, project)
    with PIO.project_lock(project, "update"):
        live = PIO.confine(project, BOARD, must_exist=True).read_bytes()
        history = PIO.confine(project, f"out/history/boards/{sha(live)}.kicad_pcb")
        history.parent.mkdir(parents=True, exist_ok=True)
        if not history.exists():
            with open(history, "xb") as handle:
                handle.write(live)
        handoff = {"record": "pcb-design/handoff", "version": "1", "adapter": "manual",
                   "board_sha256": sha(live), "preserved_board": history.relative_to(project).as_posix(),
                   "pending": "Save the board in KiCad, then run drc (parity) and the identity comparison.",
                   "closure": current_closure(project, "drc")}
        write_json(project, "out/handoff/manual.json", handoff)
    say("update.manual_required", "Save the board in KiCad. Then run drc. The handoff is out/handoff/manual.json.")
    return INVOCATION


# --------------------------------------------------------------------------- export


EXPORT_FUNCTIONS = {"mask_top": "Soldermask,Top", "mask_bottom": "Soldermask,Bot", "silk_top": "Legend,Top",
                    "silk_bottom": "Legend,Bot", "paste_top": "Paste,Top", "paste_bottom": "Paste,Bot",
                    "outline": "Profile,NP"}


def export_subset(contract: dict, copper: list[str]) -> dict[str, str]:
    """Return the expected file function of each role. Refuse a setting outside the measured subset."""
    def refuse(detail):
        raise Refusal("export.unsupported_setting", f"The export contract is outside the measured subset: {detail}.",
                      INVOCATION)

    if contract["x2"] is not False:
        refuse("x2 must be false")
    if contract["origin"] != "absolute":
        refuse("origin must be absolute")
    if contract["drill"]["zero_suppression"] != "leading":
        refuse("drill zero suppression must be leading")
    if contract["gerber"]["decimal_places"] != 6 or contract["drill"]["decimal_places"] != 3:
        refuse("gerber decimals must be 6 and drill decimals must be 3")
    if contract["drill"]["plated_suffix"] != "-PTH.drl" or contract["drill"]["nonplated_suffix"] != "-NPTH.drl":
        refuse("drill suffixes must be -PTH.drl and -NPTH.drl")
    if len(copper) < 2:
        refuse("the board must have at least two copper layers")
    inner_board = copper[1:-1]
    inner_contract = sorted(l["kicad_layer"] for l in contract["layers"] if l["role"] == "copper_inner")
    if sorted(inner_board) != inner_contract:
        refuse("the copper_inner layers of the contract must name every inner copper layer of the board")
    functions = {}
    for layer in contract["layers"]:
        role, name = layer["role"], layer["kicad_layer"]
        if layer["suffix"] != "-" + name.replace(".", "_") + ".gbr":
            refuse(f"suffix of {name} must be the KiCad name")
        if role == "copper_top":
            if name != copper[0]:
                refuse("copper_top must name the first copper layer")
            functions[name] = "Copper,L1,Top"
        elif role == "copper_bottom":
            if name != copper[-1]:
                refuse("copper_bottom must name the last copper layer")
            functions[name] = f"Copper,L{len(copper)},Bot"
        elif role == "copper_inner":
            # Stack order: the inner layer at index i is layer i+1 of the stackup (measured copper order, Pi F1).
            index = copper.index(name)
            functions[name] = f"Copper,L{index + 1},Inr"
        elif role in EXPORT_FUNCTIONS:
            functions[name] = EXPORT_FUNCTIONS[role]
        else:
            refuse(f"role {role} is not in the measured subset")
    return functions


def excellon(text: str) -> tuple[list[str], list[tuple]]:
    """Return (header comment lines, holes as (diameter, x, y) rounded to 3 decimals)."""
    header = [line for line in text.splitlines() if line.startswith(";")]
    tools, holes, current = {}, [], None
    for line in text.splitlines():
        s = line.strip()
        m = re.fullmatch(r"T(\d+)C([\d.]+)", s)
        if m:
            tools[m.group(1)] = float(m.group(2))
            continue
        m = re.fullmatch(r"T(\d+)", s)
        if m and m.group(1) in tools:
            current = tools[m.group(1)]
            continue
        m = re.fullmatch(r"X(-?\d+)Y(-?\d+)", s)
        if m and current is not None:
            holes.append((round(current, 3), round(int(m.group(1)) / 1000, 3), round(int(m.group(2)) / 1000, 3)))
    return header, sorted(holes)


def placement_filter(footprints: list[dict]) -> list[dict]:
    """The one placement filter of export and inventory. The CLI placement output lists every footprint,
    mounting holes included, so the expected rows are every inventoried footprint."""
    return [dict(f) for f in footprints]


def check_export_outputs(project: Path, export: Path, contract: dict, inv: dict, functions: dict[str, str],
                         board_text: str) -> list[dict]:
    """Run the seven export checks of section 10. Return one entry for each check."""
    results = []

    def add(name, ok, detail=""):
        results.append({"check": name, "status": "pass" if ok else "fail", "detail": detail})

    _, plot = canonical_board(board_text, drop_fill=False, plot=True)
    plot_ok = all(plot.get(k) == [v] for k, v in PLOT_CONTRACT.items())
    add("export.plot_settings", plot_ok, f"saved {plot}")
    expected_gerbers = sorted("board" + layer["suffix"] for layer in contract["layers"])
    found = sorted(p.name for p in export.glob("*.gbr"))
    add("export.file_set", found == expected_gerbers, f"expected {expected_gerbers}, found {found}")
    bad_attr, bad_fn = [], []
    for layer in contract["layers"]:
        name = "board" + layer["suffix"]
        path = export / name
        if not path.is_file():
            bad_fn.append(f"{name}: missing")
            continue
        lines = path.read_text(errors="replace").splitlines()
        if any(re.match(r"^%T[FAOD]", line) for line in lines):
            bad_attr.append(name)
        declared = [m.group(1) for m in (re.match(r"^G04 #@! TF\.FileFunction,(.*)\*$", x) for x in lines) if m]
        if declared != [functions[layer["kicad_layer"]]]:
            bad_fn.append(f"{name}: declared {declared}, expected {[functions[layer['kicad_layer']]]}")
    add("export.gerber_attributes", not bad_attr, f"active attributes in {bad_attr}")
    add("export.file_function", not bad_fn, "; ".join(bad_fn))
    dp = contract["drill"]["decimal_places"]
    expect_plated = sorted((round(o["diameter"], 3), round(o["x"], 3), round(-o["y"], 3))
                           for o in inv["holes"] if o["attr"] == "pth")
    expect_npth = sorted((round(o["diameter"], 3), round(o["x"], 3), round(-o["y"], 3))
                         for o in inv["holes"] if o["attr"] == "npth")
    for label, fname, want in (("plated", "board" + contract["drill"]["plated_suffix"], expect_plated),
                               ("nonplated", "board" + contract["drill"]["nonplated_suffix"], expect_npth)):
        path = export / fname
        if not path.is_file():
            add(f"export.drill_{label}", False, f"{fname} missing")
            continue
        header, got = excellon(path.read_text(errors="replace"))
        want_header = f"FORMAT={{{dp}:{dp}/ absolute / metric / suppress leading zeros}}"
        add(f"export.drill_header_{label}", any(want_header in h for h in header), f"expected {want_header}")
        add(f"export.drill_holes_{label}", got == want, f"expected {want}, got {got}")
    pos = export / "board-pos.csv"
    rows = list(csv.DictReader(pos.open())) if pos.is_file() else []
    refs = [r["Ref"] for r in rows]
    expect_rows = sorted((f["ref"], round(f["x"], 6), round(-f["y"], 6), round(f["rot"], 6), f["side"])
                         for f in placement_filter(inv["footprints"]))
    got_rows = sorted((r["Ref"], round(float(r["PosX"]), 6), round(float(r["PosY"]), 6), round(float(r["Rot"]), 6),
                       r["Side"]) for r in rows)
    add("export.placement_rows", len(refs) == len(set(refs)) and got_rows == expect_rows,
        f"expected {expect_rows}, got {got_rows}")
    return results


def cmd_export(args) -> int:
    project = project_arg(args.project)
    with PIO.project_lock(project, "export"):
        image = container_image(project, args.image, getattr(args, "runtime", None), "export")
        for op in ("erc", "drc"):
            ok, reason = check_report(project, op)
            if not ok:
                raise Refusal("export.not_ready", f"The {op} result is {reason}. Run {op} first.", VIOLATION)
        if (project / "simulations").is_dir():
            ok, reason = check_report(project, "sim")
            if not ok:
                raise Refusal("export.not_ready", f"The sim result is {reason}. Run sim first.", VIOLATION)
        contract = load_record(project, "manufacturing/export.yaml")
        stage, closure = stage_snapshot(project, "export")
        worker = stage / "worker"
        worker.mkdir()
        shutil.copyfile(HERE / "board_inventory.py", worker / "board_inventory.py")
        proc = subprocess.run(container_argv(image, stage, ["uv", "run", "--no-project", "--no-config", "--offline", "--python", "/usr/bin/python3", "python", "/worker/board_inventory.py",
                                                            "/work/" + BOARD], worker=worker),
                              capture_output=True, text=True, timeout=600)
        if proc.returncode == 2:
            info = json.loads(proc.stdout or "{}")
            raise Refusal("export.unsupported_geometry", f"Unsupported geometry: {info.get('unsupported', info)}",
                          INVOCATION)
        if proc.returncode != 0:
            raise Refusal("tool.inventory_failed", f"The inventory worker exited with {proc.returncode}.", TOOL)
        inv = json.loads(proc.stdout)
        functions = export_subset(contract, inv["copper_layers"])
        export_dir = stage / "export"
        export_dir.mkdir()
        commands = [
            ["kicad-cli", "pcb", "export", "gerbers", "--output", "/work/export/",
             "--layers", ",".join(layer["kicad_layer"] for layer in contract["layers"]),
             "--no-x2", "--precision", "6", "--board-plot-params", "/work/" + BOARD],
            ["kicad-cli", "pcb", "export", "drill", "--output", "/work/export/", "--format", "excellon",
             "--drill-origin", "absolute", "--excellon-zeros-format", "suppressleading", "-u", "mm",
             "--excellon-separate-th", "--generate-report", "--report-path", "/work/export/drill-report.txt",
             "/work/" + BOARD],
            ["kicad-cli", "pcb", "export", "pos", "--output", "/work/export/board-pos.csv", "--side", "both",
             "--format", "csv", "--units", "mm", "/work/" + BOARD],
        ]
        for i, argv in enumerate(commands):
            code = run_in_container(image, stage, argv, stage / f"export-cmd-{i}")
            if code != 0:
                raise Refusal("tool.export_failed", f"Export command {i} exited with {code}.", TOOL)
        board_text = (stage / BOARD).read_text(encoding="utf-8")
        checks = check_export_outputs(project, export_dir, contract, inv, functions, board_text)
        failed = [c for c in checks if c["status"] != "pass"]
        outputs = {f"export/{p.name}": sha(p.read_bytes()) for p in sorted(export_dir.iterdir()) if p.is_file()}
        raw = json.dumps(inv, sort_keys=True).encode()
        if current_closure(project, "export") != closure:
            raise Refusal("pcb.source_changed", "A source changed during the export. Nothing is published.", VIOLATION)
        status = "pass" if not failed else "fail"
        dest_rel = None
        if status == "pass":
            if args.dest:
                dest_rel = args.dest
                if os.path.lexists(PIO.confine(project, dest_rel)):
                    raise Refusal("export.destination_exists", f"The destination {dest_rel} exists.", INVOCATION)
            else:
                n = 1
                while os.path.lexists(PIO.confine(project, f"out/export/{sha(raw)[:12]}-{n}")):
                    n += 1
                dest_rel = f"out/export/{sha(raw)[:12]}-{n}"
            PIO.publish_dir(project, stage.relative_to(project).as_posix() + "/export", dest_rel)
        body = {"status": status, "exit_code": OK if status == "pass" else VIOLATION, "tool_exit": 0,
                "findings": checks, "waived": [], "unwaived": failed, "published": dest_rel,
                "outputs": outputs if status == "pass" else {}}
        publish_report(project, "export", raw, {"command": commands}, closure,
                       image, 0, body, tool_versions_of(image, "export"))
    print(f"export: {status} (checks {len(checks)}, failed {len(failed)}, published {dest_rel})")
    for item in failed:
        print(f"  failed {item['check']}: {item['detail']}")
    return body["exit_code"]


# --------------------------------------------------------------------------- interface (section 13)

REVIEW_RECORD = "pcb-design/interface-review"
INTERFACE = "mechanical/board-interface.json"
REVIEW = "mechanical/interface-review.json"


def record_board_change(project: Path, op: str, prior: bytes, current: bytes, expect_bytes: bytes) -> None:
    """Remember a board change with its predeclared expectation. The caller holds the lock."""
    path = PIO.confine(project, "out/reports/board-changes.json")
    changes = json.loads(path.read_text()) if path.is_file() else []
    changes.append({"op": op, "prior_sha256": sha(prior), "current_sha256": sha(current),
                    "expect_sha256": sha(expect_bytes), "expect_file": f"out/reports/{op}.expect.json"})
    write_json(project, "out/reports/board-changes.json", changes)


def normalized_equal(prior: str, current: str, declared: dict) -> tuple[bool, str]:
    """Compare two boards with the three allowed normalizations (section 13). Return (equal, reason)."""
    def canon(text, side):
        tree = sexp.parse(text)
        values_fixed = declared_values(tree, declared, side)
        return json.dumps(strip_allowed(tree)), values_fixed

    a, _ = canon(prior, "before")
    b, _ = canon(current, "after")
    return a == b, "" if a == b else "the boards differ outside the allowed forms"


def declared_values(tree, declared: dict, side: str):
    """Replace the Value text of each declared footprint that has the expected text. Return the replaced refs."""
    replaced = []

    def walk(node):
        if not isinstance(node, list) or not node:
            return
        if node[0] == "footprint":
            ref = prop(node, "Reference")
            value_node = next((c for c in node if isinstance(c, list) and c and c[0] == "property" and len(c) > 2
                               and c[1] == "Value"), None)
            if ref in declared and value_node is not None:
                want = declared[ref][side]
                if value_node[2] == want:
                    value_node[2] = "<declared value>"
                    replaced.append(ref)
        for child in node:
            walk(child)
    walk(tree)
    return replaced


def prop(node, name):
    for c in node:
        if isinstance(c, list) and c and c[0] == "property" and len(c) > 2 and c[1] == name:
            return c[2]
    return None


def strip_allowed(tree):
    """Remove the forms that section 13 allows to differ: plot values and zone fill cache."""
    def walk(node):
        if not isinstance(node, list):
            return node
        if node and node[0] == "pcbplotparams":
            node[:] = [c for c in node if not (isinstance(c, list) and c and c[0] in PLOT_CONTRACT)]
        if node and node[0] == "zone":
            node[:] = [c for c in node if not (isinstance(c, list) and c and c[0] == "filled_polygon")]
        return [walk(c) if isinstance(c, list) else c for c in node]
    return walk(tree)


def pointers_differing(a, b, prefix="") -> list[str]:
    """JSON pointers where two interface values differ, including added and removed keys."""
    if isinstance(a, dict) and isinstance(b, dict):
        out = []
        for key in sorted(set(a) | set(b)):
            p = f"{prefix}/{key}"
            if key not in a or key not in b:
                out.append(p)
            else:
                out.extend(pointers_differing(a[key], b[key], p))
        return out
    if isinstance(a, list) and isinstance(b, list) and len(a) == len(b):
        out = []
        for i, (x, y) in enumerate(zip(a, b)):
            out.extend(pointers_differing(x, y, f"{prefix}/{i}"))
        return out
    return [] if a == b else [prefix or "/"]


def resolve_pointer(doc, pointer: str) -> bool:
    node = doc
    if pointer in ("", "/"):
        return True
    for part in pointer.split("/")[1:]:
        if isinstance(node, dict) and part in node:
            node = node[part]
        elif isinstance(node, list) and part.isdigit() and int(part) < len(node):
            node = node[int(part)]
        else:
            return False
    return True


HEX64_RE = re.compile(r"[0-9a-f]{64}")
REVIEW_FIELDS = {"record", "version", "board_sha256", "interface_sha256", "prior_interface_sha256", "reviewer",
                 "examined", "statement"}
RESULT_FIELDS = {"record", "version", "status", "prior_board_sha256", "board_sha256", "expect_sha256", "interface_sha256"}


def strict_json(text: str):
    """Parse JSON. A duplicate key or a non-finite number is an error, never a silent replacement."""
    def pairs(items):
        out = {}
        for key, value in items:
            if key in out:
                raise ValueError(f"duplicate key {key!r}")
            out[key] = value
        return out

    def constant(name):
        raise ValueError(f"non-finite number {name}")
    return json.loads(text, object_pairs_hook=pairs, parse_constant=constant)


def is_hash(value) -> bool:
    """A full SHA-256 value: exactly 64 lowercase hexadecimal characters, no line break."""
    return isinstance(value, str) and HEX64_RE.fullmatch(value) is not None


def preserved_interface(project: Path, digest: str) -> bytes | None:
    """The preserved interface bytes for a full hash, or None when absent or altered."""
    path = PIO.confine(project, f"out/history/interfaces/{digest}.json")
    if not path.is_file():
        return None
    data = path.read_bytes()
    return data if sha(data) == digest else None


def read_changes(project: Path) -> list:
    path = PIO.confine(project, "out/reports/board-changes.json")
    if not path.is_file():
        return []
    data = strict_json(path.read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise ValueError("board-changes must be a list")
    return data


def review_problems(project: Path, record, iface: dict, iface_bytes: bytes, live_sha: str) -> list[str]:
    """Every defect of a manual review record. Coverage is checked against the preserved prior interface."""
    if not isinstance(record, dict) or set(record) != REVIEW_FIELDS:
        return ["the review record must have exactly the eight fields"]
    out = []
    if record["record"] != REVIEW_RECORD or record["version"] != "1":
        out.append("the record or version is wrong")
    if record["board_sha256"] != live_sha:
        out.append("the board hash differs from the saved board")
    if record["interface_sha256"] != sha(iface_bytes):
        out.append("the interface hash differs from the interface bytes")
    prior = record["prior_interface_sha256"]
    if prior is not None and not is_hash(prior):
        out.append("prior_interface_sha256 must be a full SHA-256 value or null")
    if not isinstance(record["reviewer"], str) or not record["reviewer"].strip():
        out.append("the reviewer must be a nonempty string")
    if not isinstance(record["statement"], str) or not record["statement"].strip():
        out.append("the statement must be a nonempty string")
    examined = record["examined"]
    if not isinstance(examined, list) or not examined:
        out.append("examined must be a nonempty list of JSON pointers")
    else:
        for pointer in examined:
            if not isinstance(pointer, str) or not pointer.startswith("/") or not resolve_pointer(iface, pointer):
                out.append(f"the pointer {pointer!r} is not a JSON pointer into the interface")
    if out:
        return out
    if prior is None:
        changed = sorted(f"/{k}" for k in iface)
    else:
        prior_bytes = preserved_interface(project, prior)
        if prior_bytes is None:
            return ["the named prior interface is missing or altered"]
        try:
            prior_doc = strict_json(prior_bytes.decode("utf-8"))
        except (ValueError, UnicodeDecodeError):
            return ["the preserved prior interface is malformed"]
        changed = pointers_differing(prior_doc, iface)
    missing = [p for p in changed if p not in examined]
    if missing:
        out.append(f"examined does not cover the changed pointers {missing}")
    return out


def automatic_problems(project: Path, data, live_sha: str, iface_bytes: bytes) -> list[str]:
    """Every defect of an automatic rebinding result. Its prior board and expectation bytes are checked."""
    if not isinstance(data, dict) or set(data) != RESULT_FIELDS:
        return ["the interface result must have exactly the seven fields"]
    out = []
    if data["record"] != "pcb-design/interface-result" or data["version"] != "1":
        out.append("the interface result has the wrong record or version")
    if data["status"] != "pass":
        out.append("the interface result is not a pass")
    if data["board_sha256"] != live_sha:
        out.append("the rebinding is for another board")
    if data["interface_sha256"] != sha(iface_bytes):
        out.append("the interface changed after the rebinding (the result is stale)")
    for key in ("prior_board_sha256", "expect_sha256"):
        if not is_hash(data[key]):
            out.append(f"{key} is not a full SHA-256 value")
    if out:
        return out
    prior_path = PIO.confine(project, f"out/history/boards/{data['prior_board_sha256']}.kicad_pcb")
    if not prior_path.is_file() or sha(prior_path.read_bytes()) != data["prior_board_sha256"]:
        return ["the preserved prior board is missing or altered"]
    try:
        changes = read_changes(project)
    except (ValueError, UnicodeDecodeError):
        return ["the board-change record is malformed"]
    match = next((c for c in changes if isinstance(c, dict) and c.get("prior_sha256") == data["prior_board_sha256"]
                  and c.get("current_sha256") == live_sha and c.get("expect_sha256") == data["expect_sha256"]), None)
    if match is None:
        return ["no board-change record matches the rebinding"]
    expect_path = PIO.confine(project, match.get("expect_file", ""))
    if not expect_path.is_file() or sha(expect_path.read_bytes()) != data["expect_sha256"]:
        return ["the expectation file is missing or altered"]
    return []


def cmd_interface(args) -> int:
    project = project_arg(args.project)
    with PIO.project_lock(project, "interface"):
        live = PIO.confine(project, BOARD, must_exist=True).read_bytes()
        live_sha = sha(live)
        iface_bytes = PIO.confine(project, INTERFACE, must_exist=True).read_bytes()
        try:
            iface = strict_json(iface_bytes.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as err:
            raise Refusal("interface.evidence_invalid", f"The interface is not strict JSON: {err}", VIOLATION)
        if args.record_review:
            return record_review(project, args, live_sha, iface_bytes, iface)
        if not args.expect:
            raise Refusal("interface.expectation_missing", "--apply needs --expect FILE.", INVOCATION)
        prior_sha = iface["board_sha256"]
        if prior_sha == live_sha:
            print("interface: already bound to the current board")
            return OK
        if not is_hash(prior_sha):
            raise Refusal("interface.prior_missing", "The interface names no full board hash.", VIOLATION)
        prior_path = PIO.confine(project, f"out/history/boards/{prior_sha}.kicad_pcb")
        if not prior_path.is_file() or sha(prior_path.read_bytes()) != prior_sha:
            raise Refusal("interface.prior_missing", "The prior board is missing or does not match its name.", VIOLATION)
        expect_path = PIO.confine(project, args.expect, must_exist=True)
        expect_bytes = expect_path.read_bytes()
        try:
            changes = read_changes(project)
        except (ValueError, UnicodeDecodeError) as err:
            raise Refusal("interface.evidence_invalid", f"The board-change record is malformed: {err}", VIOLATION)
        record = next((c for c in changes if c.get("prior_sha256") == prior_sha and c.get("current_sha256") == live_sha), None)
        if record is None or record.get("expect_sha256") != sha(expect_bytes):
            raise Refusal("interface.expectation_missing",
                          "The expectation file is not the one recorded before the board changed.", VIOLATION)
        try:
            expect = strict_json(expect_bytes.decode("utf-8"))
        except (ValueError, UnicodeDecodeError) as err:
            raise Refusal("interface.evidence_invalid", f"The expectation file is not strict JSON: {err}", VIOLATION)
        declared = {}
        for d in expect["differences"]:
            if d.get("op") == "changed" and d.get("class") == "footprint" and d.get("field") == "value":
                declared[d["ident"]] = {"before": d["before"], "after": d["after"]}
        equal, reason = normalized_equal(prior_path.read_text(), live.decode("utf-8"), declared)
        if not equal:
            raise Refusal("interface.geometry_changed", reason, VIOLATION)
        iface["board_sha256"] = live_sha
        iface_out = (json.dumps(iface, indent=2, sort_keys=True) + "\n").encode()
        write_bytes(project, INTERFACE, iface_out)
        write_json(project, "out/reports/interface.result.json",
                   {"record": "pcb-design/interface-result", "version": "1", "status": "pass",
                    "prior_board_sha256": prior_sha, "board_sha256": live_sha, "expect_sha256": sha(expect_bytes),
                    "interface_sha256": sha(iface_out)})
    print(f"interface: rebound to {live_sha}")
    return OK


def record_review(project: Path, args, live_sha: str, iface_bytes: bytes, iface: dict) -> int:
    if iface["board_sha256"] != live_sha:
        raise Refusal("interface.board_stale", "The interface names another board hash. Examine it first.", VIOLATION)
    if not args.reviewer or not args.examined:
        raise Refusal("interface.review_incomplete", "--reviewer and at least one --examined are needed.", INVOCATION)
    for p in args.examined:
        if not resolve_pointer(iface, p):
            raise Refusal("interface.pointer_missing", f"The pointer {p} does not exist in the interface.", INVOCATION)
    review_path = PIO.confine(project, REVIEW)
    prior = None
    if review_path.is_file():
        try:
            previous = strict_json(review_path.read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError) as err:
            raise Refusal("interface.review_invalid", f"The existing review is not strict JSON: {err}", VIOLATION)
        prior = previous.get("interface_sha256") if isinstance(previous, dict) else None
        if not is_hash(prior):
            raise Refusal("interface.review_invalid", "The existing review names no full interface hash.", VIOLATION)
    record = {"record": REVIEW_RECORD, "version": "1", "board_sha256": live_sha, "interface_sha256": sha(iface_bytes),
              "prior_interface_sha256": prior, "reviewer": args.reviewer, "examined": list(args.examined),
              "statement": args.statement or "Examined the listed pointers against the saved board."}
    problems = review_problems(project, record, iface, iface_bytes, live_sha)
    if problems:
        raise Refusal("interface.review_invalid", "; ".join(problems), VIOLATION)
    hist = PIO.confine(project, f"out/history/interfaces/{sha(iface_bytes)}.json")
    hist.parent.mkdir(parents=True, exist_ok=True)
    if not hist.exists():
        with open(hist, "xb") as handle:
            handle.write(iface_bytes)
    write_json(project, REVIEW, record)
    print(f"interface: review recorded for {live_sha}")
    return OK


def interface_ready(project: Path) -> tuple[bool, str]:
    """A valid manual review or a valid automatic rebinding result makes the interface ready (section 13)."""
    live = sha(PIO.confine(project, BOARD, must_exist=True).read_bytes())
    iface_bytes = PIO.confine(project, INTERFACE, must_exist=True).read_bytes()
    try:
        iface = strict_json(iface_bytes.decode("utf-8"))
    except (ValueError, UnicodeDecodeError):
        return False, "evidence_invalid"
    rev = PIO.confine(project, REVIEW)
    if rev.is_file():
        try:
            record = strict_json(rev.read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError):
            record = None
        if record is not None and not review_problems(project, record, iface, iface_bytes, live):
            return True, "review"
    res = PIO.confine(project, "out/reports/interface.result.json")
    if res.is_file():
        try:
            data = strict_json(res.read_text(encoding="utf-8"))
        except (ValueError, UnicodeDecodeError):
            data = None
        if data is not None and not automatic_problems(project, data, live, iface_bytes) \
                and iface.get("board_sha256") == live:
            return True, "automatic"
    return False, "review_stale" if rev.is_file() else "geometry_stale"

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="pcb.py", description="Checks and tool runs for a KiCad board project.")
    sub = parser.add_subparsers(dest="command", required=True)

    def common(p):
        p.add_argument("--project", default=".", help="the project directory (default: the current directory)")
        p.add_argument("--image", default=None, help="the runtime image; it must equal the lock image")
        p.add_argument("--runtime", default="auto", choices=["auto", "container", "native"],
                       help="runtime selection (section 4 of the proposal); auto follows the lock")

    p = sub.add_parser("env", help="report the measured runtime")
    p.add_argument("--project", default=None)
    p.add_argument("--image", default=None)
    p.add_argument("--runtime", default="auto", choices=["auto", "container", "native"])
    p.add_argument("--json", action="store_true")
    p.set_defaults(func=cmd_env)
    p = sub.add_parser("check", help="examine the records and the stored results")
    common(p)
    p.add_argument("--for", dest="for_", default="ready", choices=["erc", "drc", "sim", "export", "ready"])
    p.set_defaults(func=cmd_check)
    p = sub.add_parser("erc", help="run the ERC")
    common(p)
    p.set_defaults(func=cmd_erc)
    p = sub.add_parser("drc", help="run the DRC with schematic parity")
    common(p)
    p.add_argument("--refill-zones", action="store_true", help="refill the zones and save the board")
    p.set_defaults(func=cmd_drc)
    p = sub.add_parser("sim", help="run the circuits and compare the assertions")
    common(p)
    p.set_defaults(func=cmd_sim)
    p = sub.add_parser("settings", help="examine or apply the three saved plot settings")
    common(p)
    p.add_argument("--apply", action="store_true")
    p.set_defaults(func=cmd_settings)
    p = sub.add_parser("export", help="write the neutral exports and run their checks")
    common(p)
    p.add_argument("--dest", default=None, help="a new destination inside the project (default: out/export/)")
    p.set_defaults(func=cmd_export)
    p = sub.add_parser("interface", help="rebind the interface or record its review")
    common(p)
    p.add_argument("--apply", action="store_true", help="rebind after the whole-board comparison")
    p.add_argument("--expect", default=None, help="the predeclared expectation file")
    p.add_argument("--record-review", action="store_true", help="write the review record")
    p.add_argument("--reviewer", default=None)
    p.add_argument("--examined", action="append", default=None, help="a JSON pointer into the interface")
    p.add_argument("--statement", default=None)
    p.set_defaults(func=cmd_interface)
    p = sub.add_parser("mechanical", help="B11 mechanical fit: contract checks, export, fit and release")
    p.add_argument("action", choices=["check", "readiness", "export", "fit", "release"])
    p.add_argument("path", type=Path, help="the fixture directory (check) or the project (other actions)")
    p.add_argument("--image", default=None, help="export only: the local image reference (optional)")
    p.set_defaults(func=cmd_mechanical)
    p = sub.add_parser("update", help="update the board from the schematic (manual handoff or gui adapter)")
    common(p)
    p.add_argument("--adapter", required=True, choices=["manual", "gui"])
    p.add_argument("--expect", default=None, help="gui: the predeclared identity expectation file (project-relative)")
    p.add_argument("--relink", choices=["on", "off"], default="off")
    p.add_argument("--replace", choices=["on", "off"], default="off")
    p.add_argument("--delete", choices=["on", "off"], default="off")
    p.set_defaults(func=cmd_update)
    return parser


def cmd_mechanical(args) -> int:
    """Thin dispatch to the local mechanical module (B11). The module runs under its own PEP 723
    header, which lists CadQuery. This route does not import it."""
    import subprocess  # noqa: PLC0415
    module = str(Path(__file__).resolve().parent / "mechanical.py")
    if args.action == "check":
        argv = ["check", "--fixture", str(args.path)]
    elif args.action == "readiness":
        argv = ["readiness", "--project", str(args.path)]
    else:
        argv = [args.action, "--project", str(args.path)]
        if args.action == "export" and args.image:
            argv += ["--image", args.image]
    proc = subprocess.run(["uv", "run", module, *argv])
    return proc.returncode


def keep_failure(code: str, message: str) -> None:
    """Keep the tool logs of a refused run under out/history/failures (Pi F2). Staging is then removed."""
    for stage in STAGING:
        if not stage.is_dir():
            continue
        project = stage.parents[2]
        target = PIO.confine(project, f"out/history/failures/{stage.name}")
        target.mkdir(parents=True, exist_ok=True)
        for log in stage.glob("*.std*"):
            shutil.copyfile(log, target / log.name)
        (target / "failure.json").write_text(json.dumps({"code": code, "message": message}, indent=2) + "\n")


def cleanup_staging() -> None:
    for stage in STAGING:
        shutil.rmtree(stage, ignore_errors=True)
    STAGING.clear()


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    try:
        status = args.func(args)
        cleanup_staging()
        return status
    except Refusal as err:
        keep_failure(err.code, str(err))
        cleanup_staging()
        say(err.code, str(err))
        return err.status
    except PIO.LockHeld as err:
        say("lock.held", f"The project lock is held: {err}")
        return VIOLATION
    except PIO.PostReplaceError as err:
        say("publish.post_replace", str(err))
        return TOOL
    except PIO.PathEscape as err:
        say("path.escape", str(err))
        return VIOLATION


if __name__ == "__main__":
    sys.exit(main())
