import json, subprocess, sys, pathlib
E = pathlib.Path(sys.argv[1])
base = json.loads((E/"base.json").read_text())
v = [x for x in base["violations"] if x["type"] == "track_width"][0]
uuid = v["items"][0]["uuid"]; x = v["items"][0]["pos"]["x"]; y = v["items"][0]["pos"]["y"]
pro = json.loads((E/"board.kicad_pro").read_text())
variants = {
 "A_rule_xy_uuid": f"track_width|{x}|{y}|{uuid}|, excl-probe",
 "B_rule_xy_uuid_nosep": f"track_width|{x}|{y}|{uuid}, excl-probe",
 "C_xy_only_uuid": f"{x}|{y}|{uuid}|, excl-probe",
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
    excluded = sum(1 for q in tw if q.get("excluded"))
    print(name, "entry=", entry, "exit=", r.returncode, "track_width=", len(tw), "excluded_true=", excluded)
(E/"board.kicad_pro").write_text(json.dumps(pro, indent=2))
