# Preservation test for arc, via and zone (unfrozen trial script). Source trial_env.sh first, run in $TRIAL.
#   vz_gate NAME OP
# The start board is the saved KiCad board expected/fixtures/vz_saved_by_kicad.kicad_pcb. The expected differences are
# the edit only, so an arc, via or zone that the update changes or removes is an unexpected difference.
vz_gate() {
  local name=$1 op=$2 d=out/$1
  [ -e $d ] && { echo "vz_gate: $d exists" >&2; return 5; }
  mkdir -p $d; cp native/trial.kicad_pro native/fp-lib-table $d/
  uv run --no-project --no-config --offline python scripts/edit_native.py $op --in native/trial.kicad_sch --out $d/trial.kicad_sch || return 4
  cp expected/fixtures/vz_saved_by_kicad.kicad_pcb $d/trial.kicad_pcb
  uv run --no-project --no-config --offline python scripts/identity.py snapshot $d/trial.kicad_pcb -o $d/before.snap.json || return 4
  step GUI_$name RUN uv run --no-project --no-config --offline --python /usr/bin/python3 python scripts/gui_update.py --project $d --label $name --replace on --delete off --relink off || return 4
  cp $LOG/$LASTID.out $d/gui_summary.json
  uv run --no-project --no-config --offline python scripts/identity.py snapshot $d/trial.kicad_pcb -o $d/after.snap.json || return 4
  uv run --no-project --no-config --offline python scripts/identity.py compare $d/before.snap.json $d/after.snap.json --expect out/g/expected/$op.json > $d/compare.json; local rc=$?
  echo "vz_gate $name op=$op expect=$op.json compare_rc=$rc" | tee -a $LOG/gates.txt
  return $rc
}
