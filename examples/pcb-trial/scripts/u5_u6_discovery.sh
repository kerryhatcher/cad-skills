#!/bin/sh
# U5 (IPC API) and U6 (pcbnew updater) discovery in the trial container (offline). Output only. It changes no board.
echo "== U5: IPC API client package and server settings"
/usr/bin/python3 -c "import kipy; print('kipy', kipy.__file__)" 2>&1 | tail -1
/opt/trial-venv/bin/python -c "import kipy; print('kipy', kipy.__file__)" 2>&1 | tail -1
uv pip list --python /usr/bin/python3 2>/dev/null | grep -i -E "kipy|kicad|protobuf|pynng" ; echo "(uv pip list done)"
ls /usr/lib/python3/dist-packages | grep -i -E "kipy|kicad|pcbnew|protobuf|nng" | head
grep -r -i -l "api" /root/.config/kicad 2>/dev/null | head -3
echo "KICAD_API_SOCKET=${KICAD_API_SOCKET:-unset}"
echo "== U6: pcbnew module and updater functions"
/usr/bin/python3 - <<'PY'
try:
    import pcbnew
    names = [n for n in dir(pcbnew) if any(k in n.lower() for k in ("netlist", "updat", "schematic", "import"))]
    print("pcbnew", pcbnew.GetBuildVersion(), names[:40])
except Exception as err:
    print("pcbnew import:", type(err).__name__, err)
PY
