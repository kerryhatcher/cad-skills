RUN kicad-cli pcb drc --exit-code-violations --severity-all --format json -o native/out/drc_empty.json native/trial.kicad_pcb
