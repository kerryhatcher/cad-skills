#!/bin/sh
# T11 follow-up 2: one variable test. The board stores `(drillshape 1)` in its plot parameters (0 none, 1 small, 2 full).
# Export the Gerbers with kicad-cli and --board-plot-params from copies of the final board with drillshape 0, 1 and 2. (trial container, offline)
set -u
d=/work/out/t11d; rm -rf $d; mkdir -p $d
L=F.Cu,B.Cu,F.Mask,B.Mask,F.Paste,B.Paste,F.Silkscreen,B.Silkscreen,Edge.Cuts
for s in 0 1 2; do
  mkdir -p $d/s$s
  sed "s/(drillshape 1)/(drillshape $s)/" /work/out/final2/trial.kicad_pcb > $d/s$s/trial.kicad_pcb
  cp /work/out/final2/trial.kicad_sch /work/out/final2/trial.kicad_pro /work/out/final2/fp-lib-table $d/s$s/
  kicad-cli pcb export gerbers --output $d/s$s/gerbers/ --layers $L --no-x2 --precision 6 --board-plot-params $d/s$s/trial.kicad_pcb > $d/s$s/log.txt 2>&1; echo drillshape$s=$? >> $d/exit.txt
done
