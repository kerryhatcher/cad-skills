#!/bin/sh
# T11 follow-up: which plot option causes the drill marks in the kicad-cli copper and mask files? (trial container, offline)
# A: kicad-cli gerbers WITHOUT --board-plot-params (the board stores drillshape 1).
# B: KiBot with drill_marks: small.   C: KiBot with drill_marks: none.
set -u
d=/work/out/t11c; rm -rf $d; mkdir -p $d/A $d/B $d/C
cp /work/out/final2/trial.kicad_pcb /work/out/final2/trial.kicad_sch /work/out/final2/trial.kicad_pro /work/out/final2/fp-lib-table $d/
L=F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts
kicad-cli pcb export gerbers --output $d/A/ --layers $L --no-x2 --precision 6 $d/trial.kicad_pcb > $d/A.log 2>&1; echo A_exit=$? > $d/exit.txt
for mode in small none; do
  case $mode in small) x=B;; none) x=C;; esac
  sed "s/gerber_precision: 4.6/gerber_precision: 4.6\n      drill_marks: $mode/" /work/trial.kibot.yaml > $d/kibot_$mode.yaml
  (cd $d && kibot -c kibot_$mode.yaml -b trial.kicad_pcb -e trial.kicad_sch -d kibot_$x > $d/$x.log 2>&1); echo ${x}_exit=$? >> $d/exit.txt
done
