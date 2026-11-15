import json, re, subprocess, sys, pathlib
E = pathlib.Path(sys.argv[1])
U = "9024f436-90ab-541e-847d-e2efb7de6a0d"
text = (E/"board.kicad_pcb").read_text()
m = re.search(r"\(segment\s+\(start ([-\d.]+) ([-\d.]+)\)\s+\(end ([-\d.]+) ([-\d.]+)\).*?\(uuid \"" + U + r"\"\)", text, re.S)
if not m:
    raise SystemExit("segment with uuid not found")
sx, sy, ex, ey = (float(g) for g in m.groups())
nm = lambda v: int(round(v * 1e6))
mx = int((nm(sx) + nm(ex)) / 2); my = int((nm(sy) + nm(ey)) / 2)
print("segment start", sx, sy, "end", ex, ey, "midpoint nm", mx, my)
NIL = "00000000-0000-0000-0000-000000000000"
pro = json.loads((E/"board.kicad_pro").read_text())
variants = {
 "G_key_track_width": f"track_width|{mx}|{my}|{U}|{NIL}, excl-probe",
 "H_key_min_track_probe": f"min_track_probe|{mx}|{my}|{U}|{NIL}, excl-probe",
}
for name, entry in variants.items():
    p = json.loads(json.dumps(pro))
    p.setdefault("board", {}).setdefault("design_settings", {})["drc_exclusions"] = [entry]
    (E/"board.kicad_pro").write_text(json.dumps(p, indent=2))
    out = f"{name}.json"
    r = subprocess.run(["podman","run","--rm","--pull=never","--network","none","--security-opt","label=disable",
                        "-v",f"{E}:/work","-w","/work","localhost/cad-skills-pcb:b6",
                        "kicad-cli","pcb","drc","--severity-all","--format","json","-o",f"/work/{out}","/work/board.kicad_pcb"],
                       capture_output=True, text=True)
    d = json.loads((E/out).read_text())
    tw = [q for q in d["violations"] if q["type"] == "track_width"]
    print(name, "entry=", entry, "exit=", r.returncode, "track_width=", len(tw), "excluded_true=", sum(1 for q in tw if q.get("excluded")))
(E/"board.kicad_pro").write_text(json.dumps(pro, indent=2))
