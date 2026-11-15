#!/bin/sh
# Exploration only: start Xvfb and pcbnew, take screenshots. Not part of the trial result.
set -eu
export DISPLAY=:99
mkdir -p /work/out/shots /root/.config/kicad/10.0
printf '(design_block_lib_table\n\t(version 7)\n)\n' > /root/.config/kicad/10.0/design-block-lib-table
rm -rf /tmp/guiproj; cp -r /work/native /tmp/guiproj
Xvfb :99 -screen 0 1600x1000x24 >/tmp/xvfb.log 2>&1 &
sleep 2
cd /tmp/guiproj
pcbnew /tmp/guiproj/trial.kicad_pcb >/tmp/pcbnew.log 2>&1 &
sleep 12
xdotool search --name "" getwindowname %@ 2>/dev/null | sort | uniq -c | head -20 || true
import -window root /work/out/shots/02_after_tables.png
W=$(xdotool search --name "KiCad Setup" | head -1 || true)
echo "setup window: $W"
if [ -n "$W" ]; then xdotool windowfocus "$W"; sleep 1; xdotool key Escape; sleep 3; fi
xdotool search --name "" getwindowname %@ 2>/dev/null | sort | uniq -c | head -10 || true
import -window root /work/out/shots/03_after_escape.png
ls /root/.config/kicad/10.0
C=$(xdotool search --name "Confirmation" | head -1 || true)
echo "confirmation window: $C"
if [ -n "$C" ]; then xdotool windowfocus "$C"; sleep 1; xdotool key Return; sleep 4; fi
xdotool search --name "" getwindowname %@ 2>/dev/null | sort | uniq -c | head -10 || true
import -window root /work/out/shots/04_after_confirm.png
P=$(xdotool search --name "PCB Editor" | head -1)
xdotool windowfocus "$P"; sleep 1; xdotool key F8; sleep 6
xdotool search --name "" getwindowname %@ 2>/dev/null | sort | uniq -c | head -12 || true
import -window root /work/out/shots/05_after_f8.png
cat /tmp/pcbnew.log | head -10
