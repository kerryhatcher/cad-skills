# Native limit probes (unfrozen trial script). Source trial_env.sh first, run in $TRIAL.
#   lp_run NAME BOARD SCHEMATIC_DIR BEFORE_SNAPSHOT EXPECT_FILE
# It copies the project files, runs the GUI update (replace on, delete off, relink off) and writes the snapshot and the comparison.
lp_run() {
  local name=$1 board=$2 schdir=$3 before=$4 expect=$5 d=out/$1
  [ -e $d ] && { echo "lp_run: $d exists" >&2; return 5; }
  mkdir -p $d; cp native/trial.kicad_pro native/fp-lib-table $d/; cp $schdir/*.kicad_sch $d/; cp $board $d/trial.kicad_pcb
  step GUI_$name RUN uv run --no-project --no-config --offline --python /usr/bin/python3 python scripts/gui_update.py --project $d --label $name --replace on --delete off --relink off || return 4
  cp $LOG/$LASTID.out $d/gui_summary.json
  uv run --no-project --no-config --offline python scripts/identity.py snapshot $d/trial.kicad_pcb -o $d/after.snap.json || return 4
  uv run --no-project --no-config --offline python scripts/identity.py compare $before $d/after.snap.json --expect $expect > $d/compare.json; local rc=$?
  echo "limit_probe $name expect=$expect compare_rc=$rc" | tee -a $LOG/gates.txt
  return $rc
}
