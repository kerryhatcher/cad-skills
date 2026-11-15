import json, pathlib, hashlib
E = pathlib.Path("/tmp/claude-1000/-mnt-storage-projects-cad-skills/338648c2-5719-486b-b8c3-0bfb3fce6649/scratchpad/excl")
for name in ["I_pair_track_width", "K_single_track_width"]:
    d = json.loads((E/f"{name}.json").read_text())
    ex = [(q["items"][0]["uuid"], q["items"][0]["pos"]) for q in d["violations"] if q["type"] == "track_width" and q.get("excluded")]
    print(name, "excluded violation", ex, "output sha256", hashlib.sha256((E/f"{name}.json").read_bytes()).hexdigest())
