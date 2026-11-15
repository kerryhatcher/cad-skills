# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Staged exclusion restoration proof on KiCad 10.0.5 (image localhost/cad-skills-pcb:b6).

source: the project keeps the confirmed track_width exclusion (probe K form).
staged: the mandatory supplier check removes source drc_exclusions; the rule file is copied unchanged.
Both DRC runs use the same board and rule file. Only the drc_exclusions key differs.
"""
import hashlib, json, pathlib, shutil, subprocess, sys
BASE = pathlib.Path(sys.argv[1])          # scratchpad excl/ directory (temporary fixtures)
ROOT = BASE.parent / "stage-proof"
U = "9024f436-90ab-541e-847d-e2efb7de6a0d"
NIL = "00000000-0000-0000-0000-000000000000"
MID = None
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
# Marker midpoint of the target segment, taken from variant K (sexp parser, probe5.py output).
probe = json.loads((BASE / "K_single_track_width.json").read_text())
tw = [q for q in probe["violations"] if q["type"] == "track_width"]
excluded = [q for q in tw if q.get("excluded")]
assert len(excluded) == 1, f"expected one excluded track_width violation, got {len(excluded)}"
import sys as _sys
_sys.path.insert(0, "/mnt/storage/projects/cad-skills/skills/pcb-design/scripts")
import sexp
def _find_segment(node):
    if isinstance(node, list):
        if node and node[0] == "segment":
            uid = [c for c in node if isinstance(c, list) and c and c[0] == "uuid"]
            if uid and uid[0][1] == U:
                return node
        for child in node:
            found = _find_segment(child)
            if found is not None:
                return found
    return None
_seg = _find_segment(sexp.parse((BASE / "board.kicad_pcb").read_text()))
assert _seg is not None, "target segment not found by the S-expression parser"
_start = [c for c in _seg if c[0] == "start"][0]
_end = [c for c in _seg if c[0] == "end"][0]
sx, sy, ex, ey = (round(float(v) * 1e6) for v in (_start[1], _start[2], _end[1], _end[2]))
MX, MY = (sx + ex) // 2, (sy + ey) // 2   # marker = straight track midpoint in nm
print("segment nm start", sx, sy, "end", ex, ey, "marker nm", MX, MY)
pro = json.loads((BASE / "board.kicad_pro").read_text())
for name, with_excl in [("source", True), ("staged", False)]:
    d = ROOT / name
    if d.exists(): shutil.rmtree(d)
    d.mkdir(parents=True)
    for f in ["board.kicad_pcb", "board.kicad_sch", "board.kicad_prl", "board.kicad_dru"]:
        shutil.copy(BASE / f, d / f)
    p = json.loads(json.dumps(pro))
    ds = p.setdefault("board", {}).setdefault("design_settings", {})
    if with_excl:
        ds["drc_exclusions"] = [[f"track_width|{MX}|{MY}|{U}|{NIL}", "staging proof exclusion"]]
    else:
        ds.pop("drc_exclusions", None)   # mandatory supplier check clears source exclusions in staging
    (d / "board.kicad_pro").write_text(json.dumps(p, indent=2))
    r = subprocess.run(["podman", "run", "--rm", "--pull=never", "--network", "none", "--security-opt", "label=disable",
                        "-v", f"{d}:/work", "-w", "/work", "localhost/cad-skills-pcb:b6",
                        "kicad-cli", "pcb", "drc", "--severity-all", "--format", "json", "-o", "/work/drc.json", "/work/board.kicad_pcb"],
                       capture_output=True, text=True)
    print(f"{name}: drc exit {r.returncode}")
    dj = json.loads((d / "drc.json").read_text())
    tws = [q for q in dj["violations"] if q["type"] == "track_width"]
    active = sum(1 for q in tws if not q.get("excluded"))
    print(f"{name}: track_width total={len(tws)} active={active} excluded={len(tws)-active} all_violations={len(dj['violations'])}")
    print(f"{name}: drc.json sha256 {sha(d/'drc.json')}  board.kicad_pro sha256 {sha(d/'board.kicad_pro')}  board.kicad_dru sha256 {sha(d/'board.kicad_dru')}")
print("source file kept entry:", "drc_exclusions" in json.loads((ROOT/"source"/"board.kicad_pro").read_text())["board"]["design_settings"])
print("staged file cleared entry:", "drc_exclusions" not in json.loads((ROOT/"staged"/"board.kicad_pro").read_text())["board"]["design_settings"])
