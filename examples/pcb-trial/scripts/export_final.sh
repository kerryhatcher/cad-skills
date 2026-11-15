#!/bin/sh
# T10 exports of the final board (trial container, offline). Usage: sh scripts/export_final.sh DIR
# DIR holds trial.kicad_pcb (the saved final board). The output goes to DIR/export.
# Contract setting -> CLI option -> effective value (installed 10.0.5 help and measured output):
#   format rs274x           -> pcb export gerbers (always RS-274X)
#   units mm                -> Gerber always mm; pos --units mm; drill -u mm
#   x2 false                -> --no-x2 (explicit intent) AND the saved board settings usegerberattributes no and usegerberadvancedattributes no.
#                              --board-plot-params takes the saved settings and they override --no-x2. Test: no active %TF %TA %TO %TD command.
#   gerber.decimal_places 6 -> --precision 6
#   drill marks (no contract field) -> saved drillshape 0 (no marks). The Excellon files define the holes.
#   drill zero_suppression leading -> --excellon-zeros-format suppressleading
#   drill separate_files    -> --excellon-separate-th
#   origin absolute         -> --drill-origin absolute, and no --use-drill-file-origin
#   layer suffixes          -> file names trial-LAYER.gbr (no Protel extensions: --board-plot-params, saved usegerberextensions no)
#   layers                  -> --layers with the nine KiCad layer names
set -u
d=/work/$1; o=$d/export; mkdir -p $o
b=$d/trial.kicad_pcb
kicad-cli pcb export gerbers --output $o/ --layers F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts --no-x2 --precision 6 --board-plot-params $b > $o/gerbers.log 2>&1; echo gerbers=$? > $o/exit.txt
kicad-cli pcb export drill --output $o/ --format excellon --drill-origin absolute --excellon-zeros-format suppressleading -u mm --excellon-separate-th --generate-report --report-path $o/drill-report.txt $b > $o/drill.log 2>&1; echo drill=$? >> $o/exit.txt
kicad-cli pcb export pos --output $o/trial-pos.csv --side both --format csv --units mm $b > $o/pos.log 2>&1; echo pos=$? >> $o/exit.txt
kicad-cli pcb export step --output $o/trial.step --subst-models $b > $o/step.log 2>&1; echo step=$? >> $o/exit.txt
kicad-cli sch export pdf --output $o/schematic.pdf $d/trial.kicad_sch > $o/pdf.log 2>&1; echo schpdf=$? >> $o/exit.txt
