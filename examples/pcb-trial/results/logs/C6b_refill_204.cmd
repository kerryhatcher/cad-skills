RUN sh -c cd /work/out/c6b && kicad-cli pcb drc --refill-zones --save-board --exit-code-violations --severity-all --format json -o drc.json trial.kicad_pcb; echo exit=$?
