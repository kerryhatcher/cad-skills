RUN sh -c cd /work/out/c6 && kicad-cli pcb drc --refill-zones --save-board --schematic-parity --exit-code-violations --severity-all --format json -o drc.json trial.kicad_pcb; echo exit=$?
