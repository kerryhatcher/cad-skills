"""Update a PCB from its schematic with the KiCad GUI in Xvfb, driven by xdotool.

Worker for the container runtime. It runs with /usr/bin/python3 on a staged copy of the project,
never on the live project. pcb.py calls it:

  python3 /worker/gui_update.py --project /work/kicad --name board --relink off --replace off \
      --delete off --label update --shots /work/out/shots

The script writes one JSON summary to standard output. It never reports a pass. pcb.py judges
the saved board with the identity reader and the parity check.

How it works (measured with KiCad 10.0.5):
  * Stand-alone `pcbnew` refuses the update ("opened in stand-alone mode"). The script starts the
    project manager (`kicad PROJECT.kicad_pro`), opens the PCB editor with Ctrl+P, and presses F8.
  * It sets the three dialog options (it reads the check box state from the screen pixels),
    clicks "Update PCB", reads the change list from a screenshot saved for the record, closes the
    dialog, saves the board with Ctrl+S, and closes KiCad.
  * It never reports a pass from keystrokes. The caller examines the saved file (identity reader)
    and the parity result. The JSON summary lists the options, the windows seen, the exit state of the
    KiCad process, the screenshots, and the file hashes before and after.
  * Repairs against the B5 driver: the project basename is an argument (no fixed `trial`), the work is
    a staged copy, and the summary holds the measured options and the KiCad exit for the caller.

The coordinates are absolute for a 1600x1000 screen with no window manager. They come from the
screenshots of the first probe (`out/shots2/`). A different KiCad version needs new coordinates.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import signal
import subprocess
import sys
import time
from pathlib import Path

DISPLAY = ":99"
# Dialog "Update PCB from Schematic" (screen coordinates) and the default state of each option.
CHECKBOXES = {"relink": (298, 66, False), "replace": (298, 178, True), "delete": (298, 204, False)}
BUTTON_UPDATE = (936, 669)
BUTTON_CLOSE = (832, 669)


def sh(*args, check=True, **kw):
    env = dict(os.environ, DISPLAY=DISPLAY)
    return subprocess.run(args, capture_output=True, text=True, check=check, env=env, **kw)


def windows() -> list[str]:
    out = sh("xdotool", "search", "--name", "", check=False).stdout.split()
    names = []
    for wid in out:
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


def shot(path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    sh("import", "-window", "root", str(path))
    return str(path)


def is_checked(x: int, y: int) -> bool:
    """A checked box is blue (about 75,146,231). The test counts blue pixels in a 12 by 12 area.

    `import` reads the screen. `convert x:root` does not work in the container.
    """
    text = sh("import", "-window", "root", "-crop", f"12x12+{x - 6}+{y - 6}", "-depth", "8", "txt:-").stdout
    blue = 0
    for line in text.splitlines():
        if "#" in line and line[:1].isdigit():
            rgb = line.split("#")[1][:6]
            r, b_ = int(rgb[0:2], 16), int(rgb[4:6], 16)
            blue += 1 if b_ > 180 and r < 120 else 0
    return blue > 20


def wait_for_manager(summary: dict, timeout: float = 40.0) -> str:
    """Wait for the project manager. Answer the first-run setup dialog if it appears.

    The container user has no `kicad_common.json`, so KiCad asks for its first-run setup.
    Escape and the answer Yes to "Are you sure?" choose the default settings.
    """
    end = time.time() + timeout
    answered = False
    while time.time() < end:
        setup = find("KiCad Setup")
        if setup and not answered:
            summary["first_run_setup"] = "dismissed with Escape and Return (default settings)"
            key(setup, "Escape")
            time.sleep(2)
            confirm = wait_for("Confirmation", 10)
            key(confirm, "Return")
            answered = True
            time.sleep(4)
        wid = find("KiCad 10.0")
        if wid:
            return wid
        time.sleep(0.5)
    raise SystemExit(f"timeout: no project manager window. Windows: {windows()}")


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--project", required=True, help="a staged directory with NAME.kicad_pro, .kicad_sch and .kicad_pcb (it is changed)")
    parser.add_argument("--name", required=True, help="the KiCad project basename, for example board")
    parser.add_argument("--relink", choices=("on", "off"), default="off")
    parser.add_argument("--replace", choices=("on", "off"), default="on")
    parser.add_argument("--delete", choices=("on", "off"), default="off")
    parser.add_argument("--label", required=True)
    parser.add_argument("--shots", default="out/shots", help="the screenshot directory (a staged path)")
    parser.add_argument("--skip-update", action="store_true", help="open the dialog, record it, and close it without the update")
    args = parser.parse_args(argv)
    project = Path(args.project).resolve()
    pro, pcb = project / f"{args.name}.kicad_pro", project / f"{args.name}.kicad_pcb"
    shots = Path(args.shots) / args.label
    config = Path("/root/.config/kicad/10.0")
    config.mkdir(parents=True, exist_ok=True)
    (config / "design-block-lib-table").write_text("(design_block_lib_table\n\t(version 7)\n)\n")
    summary = {"label": args.label, "options_requested": {"relink": args.relink, "replace": args.replace, "delete": args.delete},
               "pcb_sha256_before": sha256(pcb), "windows": {}, "shots": []}
    xvfb = subprocess.Popen(["Xvfb", DISPLAY, "-screen", "0", "1600x1000x24"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    time.sleep(2)
    kicad = subprocess.Popen(["kicad", str(pro)], env=dict(os.environ, DISPLAY=DISPLAY), stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        manager = wait_for_manager(summary)
        summary["windows"]["after_start"] = windows()
        key(manager, "ctrl+p")
        editor = wait_for("PCB Editor")
        time.sleep(3)
        key(editor, "F8")
        dialog = wait_for("Update PCB from Schematic")
        time.sleep(4)
        summary["windows"]["dialog_open"] = windows()
        summary["shots"].append(shot(shots / "01_dialog.png"))
        states = {}
        for name, (x, y, default) in CHECKBOXES.items():
            states[name] = {"default": default, "before": is_checked(x, y)}
            want = getattr(args, name) == "on"
            if states[name]["before"] != want:
                click(x, y)
                time.sleep(1)
            states[name]["after"] = is_checked(x, y)
        summary["options_measured"] = states
        summary["shots"].append(shot(shots / "02_options.png"))
        if not args.skip_update:
            click(*BUTTON_UPDATE)
            time.sleep(6)
            summary["shots"].append(shot(shots / "03_after_update.png"))
        click(*BUTTON_CLOSE)
        time.sleep(2)
        key(find("PCB Editor") or editor, "ctrl+s")
        time.sleep(4)
        summary["shots"].append(shot(shots / "04_after_save.png"))
        summary["windows"]["after_save"] = windows()
        for title in ("PCB Editor", "Schematic Editor", "KiCad 10.0"):
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
    summary["pcb_sha256_after"] = sha256(pcb)
    summary["pcb_changed"] = summary["pcb_sha256_before"] != summary["pcb_sha256_after"]
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())
