# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Rerun the source DRC with two exclusion spellings to find why the exclusion did not apply."""
import json, pathlib, shutil, subprocess
ROOT = pathlib.Path(__file__).resolve().parent
KEY = "track_width|115825000|118000000|9024f436-90ab-541e-847d-e2efb7de6a0d|00000000-0000-0000-0000-000000000000"
for name, excl in [("nocomment", [[KEY]]), ("comment", [[KEY, "staging proof exclusion"]])]:
    d = ROOT / ("rerun_" + name)
    if d.exists(): shutil.rmtree(d)
    shutil.copytree(ROOT / "source", d)
    p = json.loads((d / "board.kicad_pro").read_text())
    p["board"]["design_settings"]["drc_exclusions"] = excl
    (d / "board.kicad_pro").write_text(json.dumps(p, indent=2))
    r = subprocess.run(["podman", "run", "--rm", "--pull=never", "--network", "none", "--security-opt", "label=disable",
                        "-v", f"{d}:/work", "-w", "/work", "localhost/cad-skills-pcb:b6",
                        "kicad-cli", "pcb", "drc", "--severity-all", "--format", "json", "-o", "/work/drc.json", "/work/board.kicad_pcb"],
                       capture_output=True, text=True)
    dj = json.loads((d / "drc.json").read_text())
    tw = [q for q in dj["violations"] if q["type"] == "track_width"]
    print(name, "exit", r.returncode, "track_width", len(tw), "excluded_flag", sum(1 for q in tw if q.get("excluded")))
