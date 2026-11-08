#!/usr/bin/env python3
# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Slice parts for Prusa printers (MK4 / MK4S by default) with the PrusaSlicer CLI.

Why this wrapper exists: `prusa-slicer --printer-profile NAME ...` silently falls
back to "- default FFF -" (generic RepRap printer, 200 C PLA, no MK4 start
G-code) unless the GUI has "installed" that printer and filament in its
datadir. This script instead resolves the official Prusa vendor bundle
(`PrusaResearch.ini`) itself -- following `inherits` chains -- into one flat
config, slices with `--load`, then reads the result back and verifies that the
printer model, nozzle, temperatures and settings really are what was asked for.

Subcommands
  find                         locate PrusaSlicer and the Prusa profile bundle
  profiles [--printer MK4S]    list printer presets, or the print/filament
                               presets compatible with one printer
  config   -o out.ini ...      write the flattened config only
  slice    part.stl ...        slice -> .bgcode/.gcode, verify, report stats
  info     file.bgcode         report stats/settings of an existing G-code file

Examples
  uv run slice.py profiles
  uv run slice.py profiles --printer MK4 --print STRUCTURAL
  uv run slice.py slice part.stl --printer MK4 --filament "Prusament PETG" \
      --print "0.20mm STRUCTURAL" --set perimeters=4 --set fill_density=40% \
      -o out/part.bgcode
  uv run slice.py slice a.3mf --printer MK4S --supports organic --brim 5 --json
  uv run slice.py info out/part.bgcode

Printer aliases: MK4 / MK4IS -> "Original Prusa MK4 Input Shaper 0.4 nozzle",
MK4S -> "Original Prusa MK4S HF0.4 nozzle", "MK4S 0.4" -> "Original Prusa
MK4S 0.4 nozzle", "MK4 0.6" -> "Original Prusa MK4 Input Shaper 0.6 nozzle" ...
Print / filament names may be given as a prefix ("0.20mm STRUCTURAL",
"Prusament PETG"); the compatible preset that matches is chosen.

Exit status is non-zero if slicing fails or verification finds a mismatch.
"""

from __future__ import annotations

import argparse
import json
import os
import platform
import re
import shutil
import struct
import subprocess
import sys
import tempfile
import zlib
from pathlib import Path

FLATPAK_ID = "com.prusa3d.PrusaSlicer"
META_KEYS = {
    "inherits", "renamed_from", "alias", "compatible_printers",
    "compatible_printers_condition", "compatible_prints",
    "compatible_prints_condition", "printer_variant", "default_print_profile",
    "default_filament_profile", "default_sla_print_profile",
    "default_sla_material_profile", "thumbnail", "visible", "printer_vendor",
}
PRINTER_ALIASES = {
    "MK4": "Original Prusa MK4 Input Shaper {n} nozzle",
    "MK4IS": "Original Prusa MK4 Input Shaper {n} nozzle",
    "MK4S": "Original Prusa MK4S {n} nozzle",
    "MK3.9": "Original Prusa MK3.9 Input Shaper {n} nozzle",
    "MK3.9S": "Original Prusa MK3.9S {n} nozzle",
    "COREONE": "Prusa CORE One {n} nozzle",
    "MINI": "Original Prusa MINI Input Shaper {n} nozzle",
}
DEFAULT_NOZZLE = {"MK4S": "HF0.4", "MK3.9S": "HF0.4", "COREONE": "HF0.4"}


# --------------------------------------------------------------------------- #
# Locating PrusaSlicer and the vendor bundle
# --------------------------------------------------------------------------- #
def find_slicer() -> list[str] | None:
    """Return the command prefix that runs the PrusaSlicer CLI."""
    env = os.environ.get("PRUSA_SLICER")
    if env:
        return env.split() if " " in env and not Path(env).exists() else [env]
    for name in ("prusa-slicer", "PrusaSlicer", "prusa-slicer-console"):
        p = shutil.which(name)
        if p:
            return [p]
    mac = Path("/Applications/Original Prusa Drivers/PrusaSlicer.app/Contents/MacOS/PrusaSlicer")
    for cand in (mac, Path("/Applications/PrusaSlicer.app/Contents/MacOS/PrusaSlicer"),
                 Path(r"C:\Program Files\Prusa3D\PrusaSlicer\prusa-slicer-console.exe")):
        if cand.exists():
            return [str(cand)]
    for appimage in sorted(Path.home().glob("**/PrusaSlicer*.AppImage"))[:1] if os.name != "nt" else []:
        return [str(appimage)]
    if shutil.which("flatpak"):
        r = subprocess.run(["flatpak", "info", FLATPAK_ID], capture_output=True, text=True)
        if r.returncode == 0:
            return ["flatpak", "run", "--command=prusa-slicer", FLATPAK_ID]
    return None


def is_flatpak(cmd: list[str]) -> bool:
    return bool(cmd) and Path(cmd[0]).name == "flatpak"


def run_slicer(cmd: list[str], args: list[str], paths: list[Path]) -> subprocess.CompletedProcess:
    full = list(cmd)
    if is_flatpak(cmd):
        dirs = sorted({str(Path(p).resolve().parent if not Path(p).is_dir() else Path(p).resolve())
                       for p in paths})
        full = ["flatpak", "run"] + [f"--filesystem={d}" for d in dirs] + cmd[2:]
    return subprocess.run(full + args, capture_output=True, text=True)


def slicer_version(cmd: list[str]) -> str:
    r = run_slicer(cmd, ["--help"], [])
    first = (r.stdout or r.stderr).splitlines()[:1]
    return first[0].strip() if first else "unknown"


def _bundle_version(path: Path) -> tuple:
    try:
        with open(path, encoding="utf-8", errors="replace") as fh:
            for _, line in zip(range(40), fh):
                m = re.match(r"config_version\s*=\s*([\d.]+)", line)
                if m:
                    return tuple(int(x) for x in m.group(1).split(".") if x.isdigit())
    except OSError:
        pass
    return ()


def find_bundle(cmd: list[str] | None, explicit: str | None = None, vendor: str = "PrusaResearch") -> Path | None:
    """Newest PrusaResearch.ini among user datadirs and the installation."""
    if explicit:
        return Path(explicit)
    home = Path.home()
    cands = [
        home / ".config/PrusaSlicer/vendor",
        home / ".PrusaSlicer/vendor",
        home / f".var/app/{FLATPAK_ID}/config/PrusaSlicer/vendor",
        home / "Library/Application Support/PrusaSlicer/vendor",
        Path(os.environ.get("APPDATA", home / "AppData/Roaming")) / "PrusaSlicer/vendor",
    ]
    if cmd and not is_flatpak(cmd):
        exe = Path(cmd[0]).resolve()
        for up in (exe.parent, *exe.parents[:3]):
            cands += [up / "resources/profiles", up / "share/PrusaSlicer/profiles",
                      up / "Resources/profiles"]
    cands += [Path("/usr/share/PrusaSlicer/profiles"), Path("/usr/local/share/PrusaSlicer/profiles")]
    found = [d / f"{vendor}.ini" for d in cands if (d / f"{vendor}.ini").is_file()]
    if cmd and is_flatpak(cmd):
        cache = home / ".cache/cad-skills" / f"{vendor}-flatpak.ini"
        r = subprocess.run(["flatpak", "run", "--command=cat", FLATPAK_ID,
                            f"/app/share/PrusaSlicer/profiles/{vendor}.ini"],
                           capture_output=True)
        if r.returncode == 0 and r.stdout:
            cache.parent.mkdir(parents=True, exist_ok=True)
            if not cache.exists() or cache.read_bytes() != r.stdout:
                cache.write_bytes(r.stdout)
            found.append(cache)
    if not found:
        return None
    return max(found, key=_bundle_version)


# --------------------------------------------------------------------------- #
# Vendor bundle parsing and inheritance
# --------------------------------------------------------------------------- #
def parse_bundle(path: Path) -> dict[str, dict[str, dict[str, str]]]:
    """{'printer': {name: {k: v}}, 'print': {...}, 'filament': {...}, ...}"""
    sections: dict[str, dict[str, dict[str, str]]] = {}
    cur = None
    with open(path, encoding="utf-8", errors="replace") as fh:
        for raw in fh:
            line = raw.rstrip("\n")
            if not line.strip() or line.lstrip().startswith("#"):
                continue
            if line.startswith("[") and line.rstrip().endswith("]"):
                head = line.strip()[1:-1]
                kind, _, name = head.partition(":")
                cur = sections.setdefault(kind, {}).setdefault(name, {})
                continue
            if cur is not None and "=" in line:
                k, _, v = line.partition("=")
                cur[k.strip()] = v.strip()
    return sections


def resolve(kind_presets: dict[str, dict[str, str]], name: str, _seen=None) -> dict[str, str]:
    """Flatten a preset: parents applied left to right, then its own keys."""
    _seen = _seen or set()
    if name in _seen:
        raise ValueError(f"inheritance cycle at {name!r}")
    if name not in kind_presets:
        raise KeyError(name)
    own = kind_presets[name]
    out: dict[str, str] = {}
    parents = [p.strip().strip('"') for p in own.get("inherits", "").split(";") if p.strip()]
    for p in parents:
        out.update(resolve(kind_presets, p, _seen | {name}))
    out.update(own)
    out.pop("inherits", None)
    return out


# --------------------------------------------------------------------------- #
# compatible_*_condition evaluator (PrusaSlicer's small expression language)
# --------------------------------------------------------------------------- #
_TOK = re.compile(r"""\s*(?:
    (?P<num>-?\d+(?:\.\d+)?) |
    (?P<str>"(?:[^"\\]|\\.)*") |
    (?P<op>==|!=|<=|>=|=~|!~|\|\||&&|[()!<>\[\]]) |
    (?P<id>[A-Za-z_][A-Za-z0-9_]*)
)""", re.X)


def _tokenize(src: str):
    i, toks = 0, []
    while i < len(src):
        if src[i].isspace():
            i += 1
            continue
        if src[i] == "/" and toks and toks[-1] in (("op", "=~"), ("op", "!~")):
            j = i + 1
            while j < len(src) and src[j] != "/":
                j += 2 if src[j] == "\\" else 1
            toks.append(("re", src[i + 1:j]))
            i = j + 1
            continue
        m = _TOK.match(src, i)
        if not m:
            raise ValueError(f"cannot parse condition at: {src[i:i+30]!r}")
        kind = m.lastgroup
        toks.append((kind, m.group(kind)))
        i = m.end()
    return toks


def _cfg_value(cfg: dict[str, str], key: str, idx: int | None):
    raw = cfg.get(key)
    if raw is None:
        return ""
    raw = raw.strip()
    if raw.startswith('"') and raw.endswith('"'):
        raw = raw[1:-1]
    if idx is not None:
        parts = [p.strip().strip('"') for p in re.split(r"[,;]", raw)]
        raw = parts[idx] if idx < len(parts) else (parts[-1] if parts else "")
    raw = raw.replace("\\n", "\n")
    try:
        return float(raw.rstrip("%"))
    except ValueError:
        return raw


def evaluate(cond: str, cfg: dict[str, str]) -> bool:
    if not cond or not cond.strip().strip('"'):
        return True
    cond = cond.strip()
    if cond.startswith('"') and cond.endswith('"'):
        cond = cond[1:-1]
    toks = _tokenize(cond)
    pos = 0

    def peek():
        return toks[pos] if pos < len(toks) else (None, None)

    def take():
        nonlocal pos
        pos += 1
        return toks[pos - 1]

    def atom():
        k, v = take()
        if (k, v) == ("op", "("):
            r = expr()
            take()
            return r
        if k == "num":
            return float(v)
        if k == "str":
            return v[1:-1]
        if k == "re":
            return re.compile(v, re.S)
        if k == "id":
            if v in ("true", "false"):
                return v == "true"
            idx = None
            if peek() == ("op", "["):
                take()
                idx = int(float(take()[1]))
                take()
            return _cfg_value(cfg, v, idx)
        raise ValueError(f"unexpected token {v!r} in {cond!r}")

    def truthy(x):
        return bool(x) if not isinstance(x, str) else x not in ("", "0", "false")

    def cmp():
        left = atom()
        k, v = peek()
        if k == "op" and v in ("==", "!=", "<", ">", "<=", ">=", "=~", "!~"):
            take()
            right = atom()
            if v in ("=~", "!~"):
                hit = bool(right.fullmatch(str(left if not isinstance(left, float) else _fmt(left))))
                return hit if v == "=~" else not hit
            if isinstance(left, float) or isinstance(right, float):
                try:
                    left, right = float(left), float(right)
                except (TypeError, ValueError):
                    left, right = str(left), str(right)
            return {"==": left == right, "!=": left != right, "<": left < right,
                    ">": left > right, "<=": left <= right, ">=": left >= right}[v]
        return truthy(left)

    def unary():
        k, v = peek()
        if (k == "op" and v == "!") or (k == "id" and v == "not"):
            take()
            return not unary()
        return cmp()

    def conj():
        r = unary()
        while peek() in (("id", "and"), ("op", "&&")):
            take()
            r = unary() and r
        return r

    def expr():
        r = conj()
        while peek() in (("id", "or"), ("op", "||")):
            take()
            r = conj() or r
        return r

    return bool(expr())


def _fmt(x: float) -> str:
    return str(int(x)) if x == int(x) else str(x)


# --------------------------------------------------------------------------- #
# Preset selection
# --------------------------------------------------------------------------- #
def concrete(presets: dict) -> list[str]:
    return [n for n in presets if not n.startswith("*")]


def pick_printer(bundle, query: str) -> str:
    printers = concrete(bundle.get("printer", {}))
    if query in printers:
        return query
    m = re.fullmatch(r"\s*([A-Za-z0-9.]+)\s*(HF)?\s*([\d.]+)?\s*", query)
    if m and m.group(1).upper() in PRINTER_ALIASES:
        key = m.group(1).upper()
        nozzle = ((m.group(2) or "") + m.group(3)) if m.group(3) else DEFAULT_NOZZLE.get(key, "0.4")
        name = PRINTER_ALIASES[key].format(n=nozzle)
        if name in printers:
            return name
    hits = [p for p in printers if query.lower() in p.lower()]
    if len(hits) == 1:
        return hits[0]
    if not hits:
        sys.exit(f"no printer preset matches {query!r}; run `slice.py profiles`")
    exact_end = [h for h in hits if h.lower().endswith(query.lower())]
    if len(exact_end) == 1:
        return exact_end[0]
    sys.exit(f"printer {query!r} is ambiguous:\n  " + "\n  ".join(hits))


def compatible(bundle, kind: str, printer_cfg: dict, print_cfg: dict | None = None) -> list[str]:
    out = []
    presets = bundle.get(kind, {})
    for name in concrete(presets):
        try:
            cfg = resolve(presets, name)
        except (KeyError, ValueError):
            continue
        if cfg.get("compatible_printers", "").strip().strip('"'):
            names = [s.strip().strip('"') for s in re.findall(r'"[^"]*"|[^;]+', cfg["compatible_printers"])]
            if printer_cfg.get("_name") not in names:
                continue
        elif not evaluate(cfg.get("compatible_printers_condition", ""), printer_cfg):
            continue
        if print_cfg is not None and not evaluate(cfg.get("compatible_prints_condition", ""), print_cfg):
            continue
        out.append(name)
    return out


def pick_from(candidates: list[str], query: str | None, default: str | None, what: str) -> str:
    if query is None:
        if default and default in candidates:
            return default
        query = default or ""
    if query in candidates:
        return query
    q = query.lower()
    hits = [c for c in candidates if c.lower().startswith(q)] or [c for c in candidates if q in c.lower()]
    if not hits:
        sys.exit(f"no compatible {what} preset matches {query!r}. Compatible ones:\n  " +
                 "\n  ".join(candidates))
    return min(hits, key=len)


def build_config(bundle, printer_q: str, print_q: str | None, filament_q: str | None):
    pname = pick_printer(bundle, printer_q)
    pcfg = resolve(bundle["printer"], pname)
    pcfg["_name"] = pname
    prints = compatible(bundle, "print", pcfg)
    default_print = pcfg.get("default_print_profile", "").strip('"')
    if print_q is None:
        structural = [p for p in prints if "STRUCTURAL" in p and p.startswith("0.20mm")]
        print_q = structural[0] if structural else None
    prname = pick_from(prints, print_q, default_print, "print")
    prcfg = resolve(bundle["print"], prname)
    fils = compatible(bundle, "filament", pcfg, prcfg)
    fname = pick_from(fils, filament_q, pcfg.get("default_filament_profile", "").strip('"') or "Prusament PLA",
                      "filament")
    fcfg = resolve(bundle["filament"], fname)
    flat: dict[str, str] = {}
    for part in (pcfg, prcfg, fcfg):
        flat.update({k: v for k, v in part.items() if k not in META_KEYS and not k.startswith("_")})
    flat["printer_settings_id"] = pname
    flat["print_settings_id"] = prname
    flat["filament_settings_id"] = f'"{fname}"'
    return flat, (pname, prname, fname)


def write_ini(flat: dict[str, str], path: Path, names) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(f"# generated by slice.py\n# printer = {names[0]}\n# print = {names[1]}\n"
                 f"# filament = {names[2]}\n")
        for k in sorted(flat):
            fh.write(f"{k} = {flat[k]}\n")


# --------------------------------------------------------------------------- #
# Reading results (.gcode and Prusa binary .bgcode)
# --------------------------------------------------------------------------- #
BG_TYPES = {0: "file_meta", 1: "gcode", 2: "slicer_meta", 3: "printer_meta", 4: "print_meta", 5: "thumbnail"}


def read_bgcode_meta(path: Path) -> dict[str, str]:
    """Metadata of a Prusa binary G-code file (file/printer/print/slicer blocks)."""
    data = path.read_bytes()
    if data[:4] != b"GCDE":
        raise ValueError("not a binary G-code file")
    _ver, checksum = struct.unpack_from("<IH", data, 4)
    pos, out = 10, {}
    while pos + 8 <= len(data):
        btype, comp, usize = struct.unpack_from("<HHI", data, pos)
        pos += 8
        csize = usize
        if comp:
            (csize,) = struct.unpack_from("<I", data, pos)
            pos += 4
        params = 6 if btype == 5 else 2
        payload = data[pos + params: pos + params + csize]
        pos += params + csize + (4 if checksum == 1 else 0)
        if btype in (0, 2, 3, 4):
            if comp == 1:
                payload = zlib.decompress(payload)
            elif comp != 0:
                continue  # heatshrink: not used for metadata in practice
            for line in payload.decode("utf-8", "replace").splitlines():
                k, sep, v = line.partition("=")
                if sep:
                    out[k.strip()] = v.strip()
    return out


def read_gcode_meta(path: Path) -> dict[str, str]:
    if path.read_bytes()[:4] == b"GCDE":
        return read_bgcode_meta(path)
    out = {}
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    for line in lines[:400] + lines[-1500:]:
        m = re.match(r";\s*([^=;]+?)\s*=\s*(.*)$", line.rstrip("\n"))
        if m:
            out[m.group(1)] = m.group(2)
    out.setdefault("_layers", str(sum(1 for l in lines if l.startswith(";LAYER_CHANGE"))))
    return out


SUMMARY_KEYS = [
    ("printer_model", "printer_model"), ("printer", "printer_settings_id"),
    ("print", "print_settings_id"), ("filament", "filament_settings_id"),
    ("filament_type", "filament_type"), ("nozzle_diameter", "nozzle_diameter"),
    ("layer_height", "layer_height"), ("first_layer_height", "first_layer_height"),
    ("perimeters", "perimeters"), ("top_solid_layers", "top_solid_layers"),
    ("bottom_solid_layers", "bottom_solid_layers"), ("fill_density", "fill_density"),
    ("fill_pattern", "fill_pattern"), ("support_material", "support_material"),
    ("support_material_auto", "support_material_auto"), ("support_material_style", "support_material_style"),
    ("brim_width", "brim_width"), ("temperature", "temperature"),
    ("first_layer_temperature", "first_layer_temperature"), ("bed_temperature", "bed_temperature"),
    ("estimated_time", "estimated printing time (normal mode)"),
    ("estimated_time_silent", "estimated printing time (silent mode)"),
    ("filament_used_g", "filament used [g]"), ("filament_used_g_total", "total filament used [g]"),
    ("filament_used_mm", "filament used [mm]"), ("filament_used_cm3", "filament used [cm3]"),
    ("filament_cost", "total filament cost"), ("max_layer_z", "max_layer_z"),
    ("layer_count", "_layers"),
]


def summarize(meta: dict[str, str]) -> dict[str, str]:
    s = {k: meta[src] for k, src in SUMMARY_KEYS if src in meta}
    if "filament_used_g" not in s and "filament_used_g_total" in s:
        s["filament_used_g"] = s["filament_used_g_total"]
    s.pop("filament_used_g_total", None)
    return s


def verify(meta: dict[str, str], flat: dict[str, str], overrides: dict[str, str]) -> list[str]:
    problems = []
    checks = ["printer_model", "nozzle_diameter", "temperature", "first_layer_temperature",
              "bed_temperature", "layer_height", "perimeters", "fill_density", "filament_type",
              "bed_shape", "max_print_height"] + list(overrides)
    for key in checks:
        want = overrides.get(key, flat.get(key))
        got = meta.get(key)
        if want is None or got is None:
            continue
        if want.strip('"') != got.strip('"'):
            problems.append(f"{key}: expected {want!r}, G-code has {got!r}")
    if meta.get("printer_settings_id", "").startswith("- default"):
        problems.append("G-code was sliced with the generic default printer, not a Prusa profile")
    return problems


# --------------------------------------------------------------------------- #
# Commands
# --------------------------------------------------------------------------- #
def load_bundle_or_die(args, cmd):
    path = find_bundle(cmd, args.bundle)
    if not path:
        sys.exit("PrusaResearch.ini profile bundle not found. Install PrusaSlicer, run its "
                 "Configuration Wizard once, or pass --bundle /path/to/PrusaResearch.ini")
    return path, parse_bundle(path)


def cmd_find(args):
    cmd = find_slicer()
    path = find_bundle(cmd, args.bundle)
    info = {
        "slicer": " ".join(cmd) if cmd else None,
        "version": slicer_version(cmd) if cmd else None,
        "bundle": str(path) if path else None,
        "bundle_version": ".".join(map(str, _bundle_version(path))) if path else None,
    }
    if args.json:
        print(json.dumps(info, indent=2))
    else:
        for k, v in info.items():
            print(f"{k:15s} {v}")
    if not cmd:
        print(INSTALL_HELP, file=sys.stderr)
        return 1
    return 0


INSTALL_HELP = """PrusaSlicer not found. Install it, then re-run `slice.py find`:
  Linux:   flatpak install flathub com.prusa3d.PrusaSlicer   (official Linux build)
  macOS:   https://www.prusa3d.com/page/prusaslicer_424/  (or brew install --cask prusaslicer)
  Windows: installer from the same page (CLI is prusa-slicer-console.exe)
Or set PRUSA_SLICER=/path/to/prusa-slicer."""


def cmd_profiles(args):
    cmd = find_slicer()
    _, bundle = load_bundle_or_die(args, cmd)
    if not args.printer:
        pr = concrete(bundle["printer"])
        if args.filter:
            pr = [p for p in pr if args.filter.lower() in p.lower()]
        print("\n".join(pr))
        return 0
    pname = pick_printer(bundle, args.printer)
    pcfg = resolve(bundle["printer"], pname)
    pcfg["_name"] = pname
    prints = compatible(bundle, "print", pcfg)
    out = {"printer": pname, "printer_model": pcfg.get("printer_model"),
           "default_print": pcfg.get("default_print_profile", "").strip('"'),
           "default_filament": pcfg.get("default_filament_profile", "").strip('"'),
           "prints": prints}
    ref_print = pick_from(prints, args.print, out["default_print"], "print") if prints else None
    if ref_print:
        prcfg = resolve(bundle["print"], ref_print)
        fils = compatible(bundle, "filament", pcfg, prcfg)
        if args.filter:
            fils = [f for f in fils if args.filter.lower() in f.lower()]
        out["filaments_for"] = ref_print
        out["filaments"] = fils
    if args.json:
        print(json.dumps(out, indent=2))
        return 0
    print(f"printer: {pname}  (printer_model={out['printer_model']})")
    print(f"default print: {out['default_print']}   default filament: {out['default_filament']}")
    print("\nprint presets:")
    for p in prints:
        print(f"  {p}")
    if ref_print:
        print(f"\nfilament presets compatible with '{ref_print}':")
        for f in out["filaments"]:
            print(f"  {f}")
    return 0


def parse_sets(items: list[str]) -> dict[str, str]:
    out = {}
    for it in items or []:
        if "=" not in it:
            sys.exit(f"--set expects key=value, got {it!r}")
        k, v = it.split("=", 1)
        out[k.strip().replace("-", "_")] = v.strip()
    return out


def shortcut_sets(args) -> dict[str, str]:
    s = {}
    if args.supports:
        if args.supports == "none":
            s.update(support_material="0", support_material_auto="0")
        elif args.supports == "buildplate":
            s.update(support_material="1", support_material_auto="1", support_material_buildplate_only="1")
        else:
            s.update(support_material="1", support_material_auto="1",
                     support_material_style={"organic": "organic", "grid": "grid", "snug": "snug"}[args.supports])
    if args.brim is not None:
        s["brim_width"] = str(args.brim)
    if args.infill is not None:
        s["fill_density"] = args.infill if args.infill.endswith("%") else f"{args.infill}%"
    if args.perimeters is not None:
        s["perimeters"] = str(args.perimeters)
    if args.layer_height is not None:
        s["layer_height"] = str(args.layer_height)
    if args.ascii:
        s["binary_gcode"] = "0"
    return s


def cmd_config(args):
    cmd = find_slicer()
    _, bundle = load_bundle_or_die(args, cmd)
    flat, names = build_config(bundle, args.printer, args.print, args.filament)
    flat.update(shortcut_sets(args))
    flat.update(parse_sets(args.set))
    write_ini(flat, Path(args.output), names)
    print(f"printer:  {names[0]}\nprint:    {names[1]}\nfilament: {names[2]}\nwrote {args.output}")
    return 0


def cmd_slice(args):
    cmd = find_slicer()
    if not cmd:
        print(INSTALL_HELP, file=sys.stderr)
        return 2
    bpath, bundle = load_bundle_or_die(args, cmd)
    flat, names = build_config(bundle, args.printer, args.print, args.filament)
    overrides = {**shortcut_sets(args), **parse_sets(args.set)}
    flat.update(overrides)
    inputs = [Path(p).resolve() for p in args.inputs]
    for p in inputs:
        if not p.is_file():
            sys.exit(f"input not found: {p}")
    binary = flat.get("binary_gcode", "0").strip() == "1"
    ext = ".bgcode" if binary else ".gcode"
    out = Path(args.output) if args.output else inputs[0].with_suffix(ext)
    if out.suffix not in (".gcode", ".bgcode"):
        out = out.with_suffix(ext)
    if (out.suffix == ".bgcode") != binary:
        flat["binary_gcode"] = "1" if out.suffix == ".bgcode" else "0"
    out = out.resolve()
    out.parent.mkdir(parents=True, exist_ok=True)
    ini = Path(args.save_config).resolve() if args.save_config else out.with_suffix(".ini")
    write_ini(flat, ini, names)

    sargs = ["--load", str(ini), "--export-gcode", "--output", str(out), "--loglevel", "2"]
    if args.merge or len(inputs) > 1:
        sargs.append("--merge")
    center = args.center
    if not center and not (args.merge or len(inputs) > 1) and not args.keep_position:
        # 3MF keeps its stored XY position; centre single objects on the bed
        pts = [tuple(float(v) for v in c.split("x")) for c in flat.get("bed_shape", "").split(",") if "x" in c]
        if pts:
            xs, ys = zip(*pts)
            center = f"{(min(xs) + max(xs)) / 2:g},{(min(ys) + max(ys)) / 2:g}"
    if center:
        sargs += ["--center", center]
    for flag in ("rotate", "rotate_x", "rotate_y", "scale", "duplicate"):
        val = getattr(args, flag)
        if val is not None:
            sargs += [f"--{flag.replace('_', '-')}", str(val)]
    sargs += [str(p) for p in inputs]
    r = run_slicer(cmd, sargs, inputs + [out, ini])
    log = (r.stdout or "") + (r.stderr or "")
    warnings = sorted({l.split("]")[-1].strip() for l in log.splitlines()
                       if re.search(r"warning|error|outside|empty layer|stability|floating|"
                                    r"bridge|adhesion|collision|not fit", l, re.I)})
    if r.returncode != 0 or not out.exists():
        print(log[-3000:], file=sys.stderr)
        print(f"\nSLICING FAILED (exit {r.returncode}). Config: {ini}", file=sys.stderr)
        return 1
    meta = read_gcode_meta(out)
    problems = verify(meta, flat, overrides)
    report = {"output": str(out), "config": str(ini), "bundle": str(bpath),
              "presets": dict(zip(("printer", "print", "filament"), names)),
              "overrides": overrides, "summary": summarize(meta),
              "slicer_messages": warnings, "verification_problems": problems}
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"sliced -> {out}  ({out.stat().st_size/1e6:.2f} MB)")
        print(f"config -> {ini}")
        print(f"presets: {names[0]} | {names[1]} | {names[2]}")
        if overrides:
            print("overrides: " + ", ".join(f"{k}={v}" for k, v in overrides.items()))
        for k, v in report["summary"].items():
            print(f"  {k:24s} {v}")
        for w in warnings:
            print(f"SLICER: {w}")
        for p in problems:
            print(f"MISMATCH: {p}")
        print("verification: " + ("OK" if not problems else "FAILED"))
    return 1 if problems else 0


def cmd_info(args):
    meta = read_gcode_meta(Path(args.file))
    if args.keys:
        sel = {k: meta.get(k) for k in args.keys}
        print(json.dumps(sel, indent=2) if args.json else "\n".join(f"{k} = {v}" for k, v in sel.items()))
        return 0
    s = summarize(meta)
    print(json.dumps(s, indent=2) if args.json else "\n".join(f"{k:24s} {v}" for k, v in s.items()))
    return 0


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--bundle", help="path to PrusaResearch.ini (default: newest found)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    f = sub.add_parser("find", help="locate PrusaSlicer and the profile bundle")
    f.add_argument("--json", action="store_true")

    p = sub.add_parser("profiles", help="list printers, or presets compatible with --printer")
    p.add_argument("--printer")
    p.add_argument("--print", help="print preset used to filter filaments (default: printer default)")
    p.add_argument("--filter", help="substring filter")
    p.add_argument("--json", action="store_true")

    def common(sp):
        sp.add_argument("--printer", default="MK4", help="printer preset or alias (default MK4)")
        sp.add_argument("--print", help='print preset or prefix (default "0.20mm STRUCTURAL")')
        sp.add_argument("--filament", help='filament preset or prefix, e.g. "Prusament PETG"')
        sp.add_argument("--set", action="append", default=[], metavar="KEY=VALUE",
                        help="override any config key (see prusa-slicer --help-fff)")
        sp.add_argument("--supports", choices=["none", "organic", "grid", "snug", "buildplate"])
        sp.add_argument("--brim", type=float, help="brim width mm")
        sp.add_argument("--infill", help="fill density, e.g. 40%%")
        sp.add_argument("--perimeters", type=int)
        sp.add_argument("--layer-height", type=float)
        sp.add_argument("--ascii", action="store_true", help="plain .gcode instead of binary .bgcode")

    c = sub.add_parser("config", help="write the flattened config .ini")
    common(c)
    c.add_argument("-o", "--output", required=True)

    s = sub.add_parser("slice", help="slice STL/3MF/STEP/OBJ to G-code and verify")
    s.add_argument("inputs", nargs="+")
    common(s)
    s.add_argument("-o", "--output", help="output .bgcode/.gcode (default next to input)")
    s.add_argument("--save-config", help="where to write the flattened .ini (default next to output)")
    s.add_argument("--merge", action="store_true", help="arrange several inputs on one plate")
    s.add_argument("--center", help="X,Y bed position for the object centre (default: bed centre)")
    s.add_argument("--keep-position", action="store_true", help="keep XY positions stored in a 3MF")
    s.add_argument("--rotate", type=float, help="rotate about Z (deg)")
    s.add_argument("--rotate-x", type=float)
    s.add_argument("--rotate-y", type=float)
    s.add_argument("--scale", help="factor or percent")
    s.add_argument("--duplicate", type=int, help="number of copies")
    s.add_argument("--json", action="store_true")

    i = sub.add_parser("info", help="summarise an existing .gcode/.bgcode")
    i.add_argument("file")
    i.add_argument("--keys", nargs="*", help="print just these config keys")
    i.add_argument("--json", action="store_true")

    args = ap.parse_args(argv)
    return {"find": cmd_find, "profiles": cmd_profiles, "config": cmd_config,
            "slice": cmd_slice, "info": cmd_info}[args.cmd](args)


if __name__ == "__main__":
    sys.exit(main())
