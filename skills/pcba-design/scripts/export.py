# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Run the locked KiCad image on private copies of the captured project bytes. Owned by pcba-design.

The module resolves the local image identity and compares it with the toolchain lock. It never pulls
an image. Each tool run uses --pull=never and --network none, a new temporary work directory outside
the project, and the image identity. Every tool argument comes from the captured export settings.
The module returns bytes only. It never writes into the project.
"""

from __future__ import annotations

import subprocess
import tempfile
from pathlib import Path

PODMAN = "podman"
BOARD_NAME = "board"
DRILL_ORIGIN = {"absolute": "absolute", "board": "plot"}
ZERO_FORMAT = {"trailing": "suppresstrailing", "leading": "suppressleading", "none": "decimal"}


class ExportError(Exception):
    """A tool step refused the run. `code` names the refusal, and `message` holds the tool output."""

    def __init__(self, code: str, message: str):
        super().__init__(message)
        self.code = code
        self.message = message


def _podman(args: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run([PODMAN, *args], capture_output=True, text=True)


def resolve_image(reference: str, locked_digest: str) -> str:
    """Return the run identity of the local image `reference`. Refuse when it is not the locked image.

    The local image ID is the identity. The lock stores it as `sha256:<id>`. The tool never pulls.
    """
    proc = _podman(["image", "inspect", "--format", "{{.Id}}", reference])
    if proc.returncode != 0 or not proc.stdout.strip():
        raise ExportError("toolchain.image_missing",
                          f"The local image {reference} is not present. Load the locked image.")
    identity = f"sha256:{proc.stdout.strip()}"
    if identity != locked_digest:
        raise ExportError("toolchain.image_mismatch",
                          f"The local image {reference} is {identity}. The lock names {locked_digest}.")
    return identity


def _container(identity: str, work: Path, argv: list[str]) -> str:
    """Run `argv` in the locked image, with the work directory mounted, no network and no pull."""
    cmd = ["run", "--rm", "--pull=never", "--network", "none", "--security-opt", "label=disable",
           "-v", f"{work}:/work:rw", "-w", "/work", identity, *argv]
    proc = _podman(cmd)
    if proc.returncode != 0:
        raise ExportError("export.failed", f"{' '.join(argv[:3])} failed with exit {proc.returncode}: "
                          f"{(proc.stderr or proc.stdout).strip()[:300]}")
    return proc.stdout


def _kicad(identity: str, work: Path, args: list[str]) -> str:
    """Run one kicad-cli command in the work directory, with no network and no pull."""
    return _container(identity, work, ["kicad-cli", *args])


def run_board_inventory(identity: str, board: bytes, worker: bytes) -> bytes:
    """Return the JSON bytes of the pcbnew worker for the board. The worker runs in the locked image."""
    with tempfile.TemporaryDirectory(prefix="pcba-inventory-") as tmp:
        work = Path(tmp)
        (work / f"{BOARD_NAME}.kicad_pcb").write_bytes(board)
        (work / "board_inventory_worker.py").write_bytes(worker)
        _container(identity, work, ["sh", "-c",
                                    "python3 /work/board_inventory_worker.py /work/board.kicad_pcb > /work/inventory.json"])
        return (work / "inventory.json").read_bytes()


def kicad_version(identity: str) -> str:
    """Return the version that the locked image reports."""
    with tempfile.TemporaryDirectory(prefix="pcba-version-") as tmp:
        return _kicad(identity, Path(tmp), ["version"]).strip().splitlines()[0]


def _collect(work: Path, skip: set) -> dict:
    """Return every file that a tool run wrote, keyed by its path relative to the work directory."""
    files = {}
    for path in sorted(work.rglob("*")):
        if path.is_file():
            rel = path.relative_to(work).as_posix()
            if rel not in skip:
                files[rel] = path.read_bytes()
    return files


def _run(identity: str, inputs: dict, steps: list[list[str]]) -> dict:
    """Write the input bytes into a new work directory, run the steps, and return the new files."""
    with tempfile.TemporaryDirectory(prefix="pcba-export-") as tmp:
        work = Path(tmp)
        for name, data in inputs.items():
            (work / name).write_bytes(data)
        for args in steps:
            _kicad(identity, work, args)
        return _collect(work, set(inputs))


def run_drc(identity: str, board: bytes) -> bytes:
    """Return the DRC report bytes of the board."""
    files = _run(identity, {f"{BOARD_NAME}.kicad_pcb": board},
                 [["pcb", "drc", "--format", "json", "--output", "/work/drc.json",
                   f"/work/{BOARD_NAME}.kicad_pcb"]])
    return files["drc.json"]


def run_erc(identity: str, schematic: bytes) -> bytes:
    """Return the ERC report bytes of the schematic. The report lists every severity."""
    files = _run(identity, {f"{BOARD_NAME}.kicad_sch": schematic},
                 [["sch", "erc", "--format", "json", "--severity-all", "--output", "/work/erc.json",
                   f"/work/{BOARD_NAME}.kicad_sch"]])
    return files["erc.json"]


def run_netlist(identity: str, schematic: bytes) -> bytes:
    """Return the KiCad XML netlist bytes of the schematic."""
    files = _run(identity, {f"{BOARD_NAME}.kicad_sch": schematic},
                 [["sch", "export", "netlist", "--format", "kicadxml", "--output", "/work/netlist.xml",
                   f"/work/{BOARD_NAME}.kicad_sch"]])
    return files["netlist.xml"]


def validate_drill_settings(settings: dict) -> None:
    """Refuse settings that the drill comparison cannot examine."""
    drill = settings["drill"]
    values = {
        "origin": (settings["origin"], "absolute"),
        "drill_units": (settings.get("extensions", {}).get("pcba", {}).get("drill_units"), "in"),
        "zero_suppression": (drill["zero_suppression"], "trailing"),
        "decimal_places": (drill["decimal_places"], 4),
        "separate_files": (drill["separate_files"], True),
    }
    for name, (value, expected) in values.items():
        if value != expected:
            raise ExportError("export.drill_setting_unsupported",
                              f"The drill comparison supports {name}={expected!r}, not {value!r}.")


def fabrication_steps(settings: dict) -> list[list[str]]:
    """Return the kicad-cli steps for the Gerber, drill and image outputs, from the captured settings."""
    validate_drill_settings(settings)
    decimals = settings["gerber"]["decimal_places"]
    if decimals not in (5, 6):
        raise ExportError("export.setting_unsupported", "The Gerber precision must be 5 or 6 digits.")
    drill = settings["drill"]
    origin = DRILL_ORIGIN.get(settings["origin"])
    units = settings.get("extensions", {}).get("pcba", {}).get("drill_units")
    if origin is None or units not in ("in", "mm") or drill["zero_suppression"] not in ZERO_FORMAT:
        raise ExportError("export.setting_unsupported", "The drill settings have no supported KiCad option.")
    layers = [layer["kicad_layer"] for layer in settings["layers"]]
    layers.append(settings["extensions"]["pcba"]["fabrication_drawing"]["kicad_layer"])
    gerber = ["pcb", "export", "gerbers", "--layers", ",".join(layers), "--output", "/work/gerber",
              "--precision", str(decimals)]
    if not settings["x2"]:
        gerber.append("--no-x2")
    gerber.append(f"/work/{BOARD_NAME}.kicad_pcb")
    excellon = ["pcb", "export", "drill", "--format", "excellon", "--drill-origin", origin,
                "--excellon-units", units, "--excellon-zeros-format", ZERO_FORMAT[drill["zero_suppression"]],
                "--excellon-separate-th", "--output", "/work/drill", f"/work/{BOARD_NAME}.kicad_pcb"]
    image = ["pcb", "export", "svg", "--layers", "F.Cu,B.Cu,Edge.Cuts", "--output", "/work/board.svg",
             f"/work/{BOARD_NAME}.kicad_pcb"]
    return [gerber, excellon, image]


def run_fabrication(identity: str, board: bytes, settings: dict) -> dict:
    """Return {"gerber": {name: bytes}, "drill": {name: bytes}, "image": bytes} for the captured settings."""
    files = _run(identity, {f"{BOARD_NAME}.kicad_pcb": board}, fabrication_steps(settings))
    out = {"gerber": {}, "drill": {}, "image": files.get("board.svg", b"")}
    for name, data in files.items():
        if name.startswith("gerber/"):
            out["gerber"][name.split("/", 1)[1]] = data
        elif name.startswith("drill/"):
            out["drill"][name.split("/", 1)[1]] = data
    return out
