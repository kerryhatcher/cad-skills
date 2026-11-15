#!/bin/sh
# T5: ERC exit code of a good and a defective schematic (trial container, offline). Usage: sh scripts/erc_exit.sh DIR
# DIR holds good.kicad_sch and bad.kicad_sch. The script writes DIR/good.json, bad.json and exit codes.
d=/work/$1
for n in good bad; do
  kicad-cli sch erc --exit-code-violations --severity-all --format json -o $d/$n.json $d/$n.kicad_sch > $d/$n.stdout 2>&1
  echo $? > $d/$n.exit
done
