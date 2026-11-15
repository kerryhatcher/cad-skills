#!/bin/sh
# Exploration only (not frozen): import a netlist into a board with the PCB editor dialog.
# Arguments: input board, netlist, output directory, shots directory, delete option (0 or 1).
set -u
BOARD=$1; NET=$2; OUT=$3; SHOTS=$4; DEL=$5
export DISPLAY=:99
mkdir -p /work/$SHOTS /work/$OUT /root/.config/kicad/10.0
printf '(design_block_lib_table\n\t(version 7)\n)\n' > /root/.config/kicad/10.0/design-block-lib-table
rm -rf /tmp/p5; mkdir /tmp/p5
cp /work/native/trial.kicad_pro /work/native/fp-lib-table /tmp/p5/
cp /work/$BOARD /tmp/p5/trial.kicad_pcb
cp /work/$NET /tmp/p5/trial.net
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
xdotool type --delay 40 "/tmp/p5/trial.net"; sleep 1
if [ "$DEL" = 1 ]; then xdotool mousemove 658 196; sleep 1; xdotool click 1; sleep 1; fi
xdotool mousemove 931 593; sleep 1; xdotool click 1; sleep 5
import -window root /work/$SHOTS/02_loaded.png
xdotool mousemove 685 593; sleep 1; xdotool click 1; sleep 5
import -window root /work/$SHOTS/03_updated.png
xdotool mousemove 797 593; sleep 1; xdotool click 1; sleep 3
P=$(xdotool search --name "PCB Editor" | head -1); xdotool windowfocus $P; sleep 1
xdotool mousemove 640 400; sleep 1; xdotool key ctrl+s; sleep 6
import -window root /work/$SHOTS/04_saved.png
cp /tmp/p5/trial.kicad_pcb /work/$OUT/trial.kicad_pcb
