# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
import json
import pathlib
import sys

sys.path.insert(0, 'skills/pcb-fab-package/scripts')
import fab

for pid in ("oshpark-single-layer", "oshpark-two-layer", "oshpark-two-layer-hhdc", "oshpark-four-layer", "oshpark-six-layer"):
    path = f"skills/pcb-fab-package/supplier/profiles/{pid}.yaml"
    rec = fab.check_profile(path)
    print(json.dumps({"requested": pid, "id": rec["id"], "limits": len(rec["limits"]),
                      "kicad_dru": sorted(rec["division"]["kicad_dru"]),
                      "layers": rec["extensions"]["service.layers"]["value"],
                      "evidence_pages": sorted(rec["extensions"]["evidence_pages"])}))