# Run the U3 gate edits. Each run: copy the gate baseline, import the netlist of OP, save, compare, check the nets.
#   u3_gate NAME OP REPLACE DELETE EXPECT
# Return: 0 equal, 1 different, 2 or 3 reader problem, 4 setup or GUI failure, 5 the run directory exists.
source /tmp/claude-1000/-mnt-storage-projects-cad-skills/fbbd1c31-73f1-4465-b310-2c58ada868be/scratchpad/u3/env.sh
cd $TRIAL
EXP=results/skidl_u3/edits/expected
u3_gate() {
  local name=$1 op=$2 replace=$3 delete=$4 expect=$5 d=out/u3/$1
  [ -e $d ] && { echo "u3_gate: $d exists" >&2; return 5; }
  mkdir -p $d; cp native/trial.kicad_pro native/fp-lib-table out/g/baseline.kicad_pcb $d/ && mv $d/baseline.kicad_pcb $d/trial.kicad_pcb || return 4
  step GUI_$name runpy scripts/gui_import.py --project $d --netlist out/net/$op/trial.net --label $name --replace $replace --delete $delete >/dev/null || { cp $LOG/$LASTID.out $d/gui_summary.json; return 4; }
  cp $LOG/$LASTID.out $d/gui_summary.json
  uv run --no-project --no-config scripts/identity.py snapshot $d/trial.kicad_pcb -o $d/after.snap.json || return 4
  uv run --no-project --no-config scripts/identity.py compare out/g/baseline.snap.json $d/after.snap.json --expect $EXP/$expect.json > $d/compare.json; local rc=$?
  uv run --no-project --no-config scripts/u3_netcheck.py $d/trial.kicad_pcb out/net/$op/trial.net > $d/netcheck.json; local nc=$?
  echo "$(date -u +%H:%M:%SZ) u3_gate $name op=$op replace=$replace delete=$delete expect=$expect.json compare_rc=$rc netcheck_rc=$nc" | tee -a $LOG/gates.txt
  return $rc
}
for r in r1 r2; do
  u3_gate none_$r none on off none
  u3_gate reorder_$r reorder on off reorder
  u3_gate value-r2_$r value-r2 on off value-r2
  u3_gate add-c2_$r add-c2 on off add-c2
  u3_gate remove-d1_$r remove-d1 on on remove-d1
  u3_gate remove-d1-delete-off_$r remove-d1 on off remove-d1-delete-off
  u3_gate footprint-r1_$r footprint-r1 on off footprint-r1
  u3_gate footprint-r1-replace-off_$r footprint-r1 off off footprint-r1-replace-off
  u3_gate rename-c1_$r rename-c1 on off rename-c1
  u3_gate line-shift_$r line-shift on off line-shift
done
echo DONE
