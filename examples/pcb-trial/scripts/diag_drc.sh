#!/bin/sh
# Full DRC and schematic parity of saved boards in the trial container (offline). Supplement to drc_boards.sh:
# it copies all .kicad_sch files of the run directory, so a hierarchical project works.
# Usage: sh scripts/diag_drc.sh OUTDIR RUN...   (each RUN is a directory out/RUN)
# Command: kicad-cli pcb drc --schematic-parity --exit-code-violations --severity-all --format json
# Per RUN it writes OUTDIR/RUN/drc.json, exit.txt (the exit code of kicad-cli), stdout.txt and hashes.txt (SHA-256 of the board and each schematic).
set -u
OUT=$1; shift
for run in "$@"; do
  w=/tmp/diag_$run; rm -rf $w; mkdir -p $w /work/$OUT/$run
  cp /work/out/$run/*.kicad_sch /work/out/$run/trial.kicad_pcb /work/out/$run/trial.kicad_pro /work/out/$run/fp-lib-table $w/
  kicad-cli pcb drc --schematic-parity --exit-code-violations --severity-all --format json -o /work/$OUT/$run/drc.json $w/trial.kicad_pcb > /work/$OUT/$run/stdout.txt 2>&1
  echo $? > /work/$OUT/$run/exit.txt
  (cd $w && sha256sum trial.kicad_pcb *.kicad_sch) > /work/$OUT/$run/hashes.txt
done
