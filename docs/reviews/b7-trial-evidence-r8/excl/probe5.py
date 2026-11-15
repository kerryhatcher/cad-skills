import json, subprocess, sys, pathlib
sys.path.insert(0, "/mnt/storage/projects/cad-skills/skills/pcb-design/scripts")
import sexp
E = pathlib.Path(sys.argv[1])
U = "9024f436-90ab-541e-847d-e2efb7de6a0d"
NIL = "00000000-0000-0000-0000-000000000000"
tree = sexp.parse((E/"board.kicad_pcb").read_text())
def walk(node):
    if isinstance(node, list):
        if node and node[0] == "segment":
            uid = [c for c in node if isinstance(c, list) and c and c[0] == "uuid"]
            if uid and uid[0][1] == U:
                return node
        for child in node:
            found = walk(child)
            if found is not None:
                return found
    return None
seg = walk(tree)
assert seg is not None, "target segment not found by the S-expression parser"
start = [c for c in seg if c[0] == "start"][0]; end = [c for c in seg if c[0] == "end"][0]
nm = lambda v: int(round(float(v) * 1e6))
sx, sy, ex, ey = nm(start[1]), nm(start[2]), nm(end[1]), nm(end[2])
mx = int((sx + ex) / 2); my = int((sy + ey) / 2)
print("target segment start nm", sx, sy, "end nm", ex, ey, "midpoint nm", mx, my)
pro = json.loads((E/"board.kicad_pro").read_text())
variants = {
 "I_pair_track_width": [[f"track_width|{mx}|{my}|{U}|{NIL}", "excl-probe"]],
 "J_pair_min_track_probe": [[f"min_track_probe|{mx}|{my}|{U}|{NIL}", "excl-probe"]],
 "K_single_track_width": [[f"track_width|{mx}|{my}|{U}|{NIL}"]],
}
for name, exclusions in variants.items():
    p = json.loads(json.dumps(pro))
    p.setdefault("board", {}).setdefault("design_settings", {})["drc_exclusions"] = exclusions
    (E/"board.kicad_pro").write_text(json.dumps(p, indent=2))
    out = f"{name}.json"
    r = subprocess.run(["podman","run","--rm","--pull=never","--network","none","--security-opt","label=disable",
                        "-v",f"{E}:/work","-w","/work","localhost/cad-skills-pcb:b6",
                        "kicad-cli","pcb","drc","--severity-all","--format","json","-o",f"/work/{out}","/work/board.kicad_pcb"],
                       capture_output=True, text=True)
    d = json.loads((E/out).read_text())
    tw = [q for q in d["violations"] if q["type"] == "track_width"]
    print(name, "exclusions=", json.dumps(exclusions), "exit=", r.returncode, "track_width=", len(tw), "excluded_true=", sum(1 for q in tw if q.get("excluded")))
(E/"board.kicad_pro").write_text(json.dumps(pro, indent=2))
