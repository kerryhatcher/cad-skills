#!/bin/sh
# Netlist and ERC of the sheet-move schematic (trial container, offline). Usage: sh scripts/sheet_move_check.sh DIR
d=/work/$1
cd $d && kicad-cli sch export netlist --format kicadxml -o net.xml trial.kicad_sch > net.log 2>&1; echo $? > net.exit
kicad-cli sch erc --exit-code-violations --severity-all --format json -o erc.json trial.kicad_sch > erc.log 2>&1; echo $? > erc.exit
