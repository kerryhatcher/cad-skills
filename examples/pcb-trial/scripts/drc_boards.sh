#!/bin/sh
# Full DRC and schematic parity of saved boards, in the trial container (offline).
# Usage: sh scripts/drc_boards.sh OUTDIR RUN...   (each RUN is a directory out/RUN with trial.kicad_pcb and trial.kicad_sch)
# For each RUN the script writes OUTDIR/RUN/drc.json, OUTDIR/RUN/exit.txt and OUTDIR/RUN/hashes.txt.
set -u
OUT=$1; shift
for run in "$@"; do
  w=/tmp/drc_$run; rm -rf $w; mkdir -p $w /work/$OUT/$run
  cp /work/out/$run/trial.kicad_pcb /work/out/$run/trial.kicad_sch /work/out/$run/trial.kicad_pro /work/out/$run/fp-lib-table $w/
  kicad-cli pcb drc --schematic-parity --exit-code-violations --severity-all --format json -o /work/$OUT/$run/drc.json $w/trial.kicad_pcb > /work/$OUT/$run/stdout.txt 2>&1
  echo $? > /work/$OUT/$run/exit.txt
  sha256sum $w/trial.kicad_pcb $w/trial.kicad_sch > /work/$OUT/$run/hashes.txt
done
