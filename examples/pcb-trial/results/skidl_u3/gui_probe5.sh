#!/bin/sh
# Exploration only (not frozen): open the netlist import dialog of the PCB editor. Screenshots only.
set -u
export DISPLAY=:99
mkdir -p /work/out/shots4 /root/.config/kicad/10.0
printf '(design_block_lib_table\n\t(version 7)\n)\n' > /root/.config/kicad/10.0/design-block-lib-table
rm -rf /tmp/p5; mkdir /tmp/p5
cp /work/native/trial.kicad_pro /work/native/fp-lib-table /tmp/p5/
cp /work/out/stub.kicad_pcb /tmp/p5/trial.kicad_pcb
cp /work/out/skn_g/trial.net /tmp/p5/trial.net
Xvfb :99 -screen 0 1600x1000x24 >/dev/null 2>&1 &
sleep 2
kicad /tmp/p5/trial.kicad_pro >/dev/null 2>&1 &
sleep 10
S=$(xdotool search --name "KiCad Setup" | head -1); if [ -n "$S" ]; then xdotool windowfocus $S; sleep 1; xdotool key Escape; sleep 2; C=$(xdotool search --name "Confirmation" | head -1); xdotool windowfocus $C; sleep 1; xdotool key Return; sleep 4; fi
M=$(xdotool search --name "KiCad 10.0" | head -1); xdotool windowfocus $M; sleep 1; xdotool key ctrl+p; sleep 10
P=$(xdotool search --name "PCB Editor" | head -1); xdotool windowfocus $P; sleep 1
xdotool mousemove 19 12; sleep 1; xdotool click 1; sleep 2
xdotool mousemove 52 165; sleep 1; xdotool click 1; sleep 2
xdotool mousemove 320 165; sleep 1; xdotool click 1; sleep 4
import -window root /work/out/shots4/01_netlist_dialog.png
xdotool search --name "" getwindowname %@ 2>/dev/null | sort -u > /work/out/shots4/windows.txt
