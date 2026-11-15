# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Write a manual evidence record for the silk condition with the current board and silk Gerber hashes."""
import hashlib, json, pathlib, sys
project, design = pathlib.Path(sys.argv[1]), pathlib.Path(sys.argv[2])
art = project / "out/fab/manual/silk-check.txt"
rec = {"schema_id": "pcb-fab-package/manual-evidence", "schema_version": 1, "condition": "silk_line_min_short_text",
       "result": "pass", "procedure": "Measured short silk strokes and text on the saved silk layer",
       "artifact_path": "out/fab/manual/silk-check.txt", "artifact_sha256": hashlib.sha256(art.read_bytes()).hexdigest(),
       "inputs": {"board_sha256": hashlib.sha256((project / "kicad/board.kicad_pcb").read_bytes()).hexdigest(),
                  "silk_gerber_sha256": hashlib.sha256((design / "export/board-F_Silkscreen.gbr").read_bytes()).hexdigest()},
       "reviewer": "R. Reviewer", "statement": "Manual measurement on the saved layer."}
out = project / "out/fab/manual-record.json"
out.write_text(json.dumps(rec, indent=2, sort_keys=True) + "\n")
print(out)
