#!/bin/sh
# Phase B: refill the zones, save the board, then run full DRC with schematic parity (trial container, offline).
# Usage: sh scripts/final_drc.sh DIR   (DIR holds trial.kicad_pcb, trial.kicad_sch, trial.kicad_pro, fp-lib-table)
set -u
d=/work/$1
kicad-cli pcb drc --refill-zones --save-board --schematic-parity --exit-code-violations --severity-all --format json -o $d/drc.json $d/trial.kicad_pcb > $d/drc_stdout.txt 2>&1
echo $? > $d/drc_exit.txt
kicad-cli sch erc --exit-code-violations --severity-all --format json -o $d/erc.json $d/trial.kicad_sch > $d/erc_stdout.txt 2>&1
echo $? > $d/erc_exit.txt
