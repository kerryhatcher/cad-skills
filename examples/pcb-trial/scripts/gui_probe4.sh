#!/bin/sh
# Exploration only (not frozen): does the PCB editor of KiCad 10.0.5 have a netlist import? Screenshots only.
set -u
export DISPLAY=:99
mkdir -p /work/out/shots3 /root/.config/kicad/10.0
printf '(design_block_lib_table\n\t(version 7)\n)\n' > /root/.config/kicad/10.0/design-block-lib-table
cp -r /work/native /tmp/p3
Xvfb :99 -screen 0 1600x1000x24 >/dev/null 2>&1 &
sleep 2
kicad /tmp/p3/trial.kicad_pro >/dev/null 2>&1 &
sleep 10
S=$(xdotool search --name "KiCad Setup" | head -1); if [ -n "$S" ]; then xdotool windowfocus $S; sleep 1; xdotool key Escape; sleep 2; C=$(xdotool search --name "Confirmation" | head -1); xdotool windowfocus $C; sleep 1; xdotool key Return; sleep 4; fi
M=$(xdotool search --name "KiCad 10.0" | head -1); xdotool windowfocus $M; sleep 1; xdotool key ctrl+p; sleep 10
P=$(xdotool search --name "PCB Editor" | head -1); xdotool windowfocus $P; sleep 1
xdotool mousemove 19 12; sleep 1; xdotool click 1; sleep 2
import -window root /work/out/shots3/02_file_menu_again.png
xdotool mousemove 52 165; sleep 1; xdotool click 1; sleep 2
import -window root /work/out/shots3/03_import_submenu.png
