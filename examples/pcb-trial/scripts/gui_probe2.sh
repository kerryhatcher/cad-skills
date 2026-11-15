#!/bin/sh
# Exploration only: start the KiCad project manager (not stand-alone pcbnew), answer the first-run dialog, take screenshots.
set -eu
export DISPLAY=:99
mkdir -p /work/out/shots2 /root/.config/kicad/10.0
printf '(design_block_lib_table\n\t(version 7)\n)\n' > /root/.config/kicad/10.0/design-block-lib-table
rm -rf /tmp/guiproj; cp -r /work/native /tmp/guiproj
Xvfb :99 -screen 0 1600x1000x24 >/tmp/xvfb.log 2>&1 &
sleep 2
cd /tmp/guiproj
kicad /tmp/guiproj/trial.kicad_pro >/tmp/kicad.log 2>&1 &
sleep 10
S=$(xdotool search --name "KiCad Setup" | head -1 || true)
if [ -n "$S" ]; then xdotool windowfocus "$S"; sleep 1; xdotool key Escape; sleep 2; C=$(xdotool search --name "Confirmation" | head -1); xdotool windowfocus "$C"; sleep 1; xdotool key Return; sleep 4; fi
xdotool search --name "" getwindowname %@ 2>/dev/null | sort | uniq -c | head -12 || true
import -window root /work/out/shots2/01_manager.png
head -5 /tmp/kicad.log
M=$(xdotool search --name "KiCad 10.0" | head -1); xdotool windowfocus "$M"; sleep 1; xdotool key ctrl+p
sleep 10
xdotool search --name "" getwindowname %@ 2>/dev/null | sort | uniq -c | head -12 || true
import -window root /work/out/shots2/02_pcbeditor.png
P=$(xdotool search --name "PCB Editor" | head -1)
xdotool windowfocus "$P"; sleep 1; xdotool key F8; sleep 6
xdotool search --name "" getwindowname %@ 2>/dev/null | sort | uniq -c | head -12 || true
import -window root /work/out/shots2/03_f8.png
