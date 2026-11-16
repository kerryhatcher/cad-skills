"""U3: import a netlist into a PCB with the KiCad GUI in Xvfb, driven by xdotool.

Run it inside the trial container (system Python through uv):

  uv run --no-project --no-config --offline --python /usr/bin/python3 python scripts/gui_import.py \
      --project out/u3/RUN --netlist out/net/OP/trial.net --label RUN --replace on --delete off

How it works (measured with KiCad 10.0.5, the same image as `gui_update.py`):
  * The script starts the project manager (`kicad PROJECT.kicad_pro`) and opens the PCB editor with Ctrl+P.
  * It opens File > Import > Netlist. KiCad 10.0.5 has no default hotkey for this dialog.
  * It types the absolute netlist path, selects the link method "component tstamps", and sets the options
    "Delete footprints with no components in netlist" and "Replace footprints with those specified in netlist".
    It reads the state of each radio button and check box from the screen pixels, before and after the change.
  * It clicks "Load and Test Netlist", then "Update PCB", then "Close". It saves with Ctrl+S and closes KiCad.
  * It never reports a pass from keystrokes. The caller examines the saved file (identity reader) and the
    pad nets (`u3_netcheck.py`). The JSON summary lists the options, the windows seen, the KiCad exit state,
    the screenshots, and the hash and modification time of the board before and after.

The coordinates are absolute for a 1600x1000 screen with no window manager. They come from the screenshot
`results/skidl_u3/shots/dialog_empty.png` of the first U3 probe. A different KiCad version needs new coordinates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

DISPLAY = ":99"
MENU_FILE, MENU_IMPORT, MENU_NETLIST = (19, 12), (52, 165), (320, 165)
NETLIST_FIELD = (670, 130)
# (x, y, default) of each control in the dialog "Import Netlist".
RADIO_TSTAMP = (270, 196, True)
CHECKBOXES = {
    "delete": (658, 196, False),
    "replace": (658, 222, True),
    "group": (658, 248, True),
    "locked": (658, 274, False),
    "delete_shorting_tracks": (658, 300, False),
}
BUTTON_LOAD, BUTTON_UPDATE, BUTTON_CLOSE = (931, 593), (685, 593), (797, 593)


def sh(*args, check=True, **kw):
    env = dict(os.environ, DISPLAY=DISPLAY)
    return subprocess.run(args, capture_output=True, text=True, check=check, env=env, **kw)


def windows() -> list[str]:
    names = []
    for wid in sh("xdotool", "search", "--name", "", check=False).stdout.split():
        name = sh("xdotool", "getwindowname", wid, check=False).stdout.strip()
        if name:
            names.append(name)
    return sorted(set(names))


def find(name: str) -> str | None:
    out = sh("xdotool", "search", "--name", name, check=False).stdout.split()
    return out[0] if out else None


def wait_for(name: str, timeout: float = 30.0) -> str:
    end = time.time() + timeout
    while time.time() < end:
        wid = find(name)
        if wid:
            return wid
        time.sleep(0.5)
    raise SystemExit(f"timeout: no window named {name!r}. Windows: {windows()}")


def key(window: str, *keys: str):
    sh("xdotool", "windowfocus", window)
    time.sleep(0.5)
    sh("xdotool", "key", *keys)


def click(x: int, y: int):
    sh("xdotool", "mousemove", str(x), str(y))
    time.sleep(0.3)
    sh("xdotool", "click", "1")


def shot(path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    sh("import", "-window", "root", str(path))
    return str(path)


def is_on(x: int, y: int) -> bool:
    """A checked box or a selected radio button is blue (about 75,146,231). Count blue pixels in a 12 by 12 area."""
    text = sh("import", "-window", "root", "-crop", f"12x12+{x - 6}+{y - 6}", "-depth", "8", "txt:-").stdout
    blue = 0
    for line in text.splitlines():
        if "#" in line and line[:1].isdigit():
            rgb = line.split("#")[1][:6]
            r, b_ = int(rgb[0:2], 16), int(rgb[4:6], 16)
            blue += 1 if b_ > 180 and r < 120 else 0
    return blue > 20


def wait_for_manager(summary: dict, timeout: float = 40.0) -> str:
    """Wait for the project manager. Answer the first-run setup dialog with the default settings if it appears."""
    end = time.time() + timeout
    answered = False
    while time.time() < end:
        setup = find("KiCad Setup")
        if setup and not answered:
            summary["first_run_setup"] = "dismissed with Escape and Return (default settings)"
            key(setup, "Escape")
            time.sleep(2)
            key(wait_for("Confirmation", 10), "Return")
            answered = True
            time.sleep(4)
        wid = find("KiCad 10.0")
        if wid:
            return wid
        time.sleep(0.5)
    raise SystemExit(f"timeout: no project manager window. Windows: {windows()}")


def file_state(path: Path) -> dict:
    return {"sha256": hashlib.sha256(path.read_bytes()).hexdigest(), "mtime_ns": path.stat().st_mtime_ns}


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", required=True, help="a directory with trial.kicad_pro and trial.kicad_pcb (the board is changed)")
    parser.add_argument("--netlist", required=True, help="the netlist to import")
    parser.add_argument("--name", default="trial")
    parser.add_argument("--replace", choices=("on", "off"), default="on")
    parser.add_argument("--delete", choices=("on", "off"), default="off")
    parser.add_argument("--label", required=True)
    parser.add_argument("--shots", default="out/shots")
    args = parser.parse_args(argv)
    project = Path(args.project).resolve()
    netlist = Path(args.netlist).resolve()
    pro, pcb = project / f"{args.name}.kicad_pro", project / f"{args.name}.kicad_pcb"
    if not netlist.is_file():
        print(f"gui_import: the netlist {netlist} does not exist. Give the path of a netlist file.", file=sys.stderr)
        return 2
    shots = Path(args.shots) / args.label
    config = Path("/root/.config/kicad/10.0")
    config.mkdir(parents=True, exist_ok=True)
    (config / "design-block-lib-table").write_text("(design_block_lib_table\n\t(version 7)\n)\n")
    summary = {"label": args.label, "netlist": str(netlist),
               "netlist_sha256": hashlib.sha256(netlist.read_bytes()).hexdigest(),
               "options_requested": {"link": "tstamp", "replace": args.replace, "delete": args.delete},
               "pcb_before": file_state(pcb), "windows": {}, "shots": []}
    xvfb = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "1600x1000x24"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    kicad = subprocess.Popen(["kicad", str(pro)], env=dict(os.environ, DISPLAY=DISPLAY), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        manager = wait_for_manager(summary)
        summary["windows"]["after_start"] = windows()
        key(manager, "ctrl+p")
        editor = wait_for("PCB Editor")
        time.sleep(4)
        sh("xdotool", "windowfocus", editor)
        for point in (MENU_FILE, MENU_IMPORT, MENU_NETLIST):
            click(*point)
            time.sleep(2)
        wait_for("Import Netlist")
        time.sleep(3)
        summary["windows"]["dialog_open"] = windows()
        click(*NETLIST_FIELD)
        sh("xdotool", "key", "ctrl+a")
        sh("xdotool", "type", "--delay", "40", str(netlist))
        time.sleep(1)
        states = {"link_tstamp": {"default": RADIO_TSTAMP[2], "before": is_on(*RADIO_TSTAMP[:2])}}
        if not states["link_tstamp"]["before"]:
            click(*RADIO_TSTAMP[:2])
            time.sleep(1)
        states["link_tstamp"]["after"] = is_on(*RADIO_TSTAMP[:2])
        for name, (x, y, default) in CHECKBOXES.items():
            states[name] = {"default": default, "before": is_on(x, y)}
            requested = getattr(args, name, None)
            if requested is not None and states[name]["before"] != (requested == "on"):
                click(x, y)
                time.sleep(1)
            states[name]["after"] = is_on(x, y)
        summary["options_measured"] = states
        summary["shots"].append(shot(shots / "01_options.png"))
        click(*BUTTON_LOAD)
        time.sleep(5)
        summary["shots"].append(shot(shots / "02_loaded.png"))
        click(*BUTTON_UPDATE)
        time.sleep(6)
        summary["shots"].append(shot(shots / "03_updated.png"))
        summary["windows"]["after_update"] = windows()
        click(*BUTTON_CLOSE)
        time.sleep(3)
        editor = find("PCB Editor") or editor
        summary["editor_title_before_save"] = sh("xdotool", "getwindowname", editor, check=False).stdout.strip()
        key(editor, "ctrl+s")
        time.sleep(5)
        summary["editor_title_after_save"] = sh("xdotool", "getwindowname", editor, check=False).stdout.strip()
        summary["shots"].append(shot(shots / "04_saved.png"))
        summary["windows"]["after_save"] = windows()
        for title in ("PCB Editor", "KiCad 10.0"):
            wid = find(title)
            if wid:
                key(wid, "ctrl+q")
                time.sleep(2)
        try:
            kicad.wait(timeout=15)
            summary["kicad_exit"] = {"state": "exited", "code": kicad.returncode}
        except subprocess.TimeoutExpired:
            kicad.send_signal(signal.SIGTERM)
            kicad.wait(timeout=10)
            summary["kicad_exit"] = {"state": "stopped by the script after 15 s", "code": kicad.returncode}
    finally:
        if kicad.poll() is None:
            kicad.kill()
        xvfb.terminate()
    summary["pcb_after"] = file_state(pcb)
    summary["pcb_saved"] = summary["pcb_after"]["mtime_ns"] != summary["pcb_before"]["mtime_ns"]
    summary["pcb_changed"] = summary["pcb_after"]["sha256"] != summary["pcb_before"]["sha256"]
    print(json.dumps(summary, indent=2))
    return 0 if summary["pcb_saved"] else 4


if __name__ == "__main__":
    sys.exit(main())
