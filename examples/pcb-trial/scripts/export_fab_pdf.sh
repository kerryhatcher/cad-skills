#!/bin/sh
# Fabrication drawing of the final board (trial container, offline). Usage: sh scripts/export_fab_pdf.sh DIR
d=/work/$1
kicad-cli pcb export pdf --output $d/export/fabrication.pdf --layers Edge.Cuts,F.Fab,F.Cu --include-border-title $d/trial.kicad_pcb > $d/export/fabpdf.log 2>&1
echo fabpdf=$? >> $d/export/exit.txt
