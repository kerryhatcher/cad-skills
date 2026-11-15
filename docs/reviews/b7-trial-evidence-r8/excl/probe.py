import json, subprocess, sys, pathlib, shutil
E = pathlib.Path(sys.argv[1])
def run_drc(out_name):
    cmd = ["podman","run","--rm","--pull=never","--network","none","--security-opt","label=disable",
           "-v", f"{E}:/work", "-w","/work","localhost/cad-skills-pcb:b6",
           "kicad-cli","pcb","drc","--severity-all","--format","json","-o",f"/work/{out_name}","/work/board.kicad_pcb"]
    p = subprocess.run(cmd, capture_output=True, text=True)
    return p.returncode, json.loads((E/out_name).read_text())
rc, d = run_drc("base.json")
tw = [v for v in d["violations"] if v["type"] == "track_width"]
print("baseline exit", rc, "track_width", len(tw), "excluded flags", [v.get("excluded") for v in tw][:3])
v = tw[0]
print("first violation item uuids", [i["uuid"] for i in v["items"]], "pos", v["items"][0]["pos"])
print("keys", sorted(v.keys()))
