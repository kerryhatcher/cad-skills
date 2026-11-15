S=/tmp/claude-1000/-mnt-storage-projects-cad-skills/31456ff4-3cc5-4474-895e-358d2be1c713/scratchpad
REPO=/mnt/storage/projects/cad-skills
TRIAL=$S/b5/trial
LOG=$S/b5/logs
IMAGE_TAG=localhost/cad-skills-trial:b5
sync_trial() { tar -C $REPO/examples/pcb-trial --exclude=out -cf - . | tar -C $TRIAL -xf -; }
step() { local name=$1; shift; printf '%s\n' "$*" > $LOG/$name.cmd; "$@" > $LOG/$name.out 2>&1; local rc=$?; echo "$(date -u +%H:%M:%S) $name exit=$rc out=$(sha256sum $LOG/$name.out | cut -c1-16)" | tee -a $LOG/steps.txt; return $rc; }
source $S/b5/image_id.env
# Offline trial run in /work with a temporary SELinux mount of the trial copy.
RUN() { podman run --rm --pull=never --network none -w /work -v "$TRIAL:/work:Z" "$IMAGE_ID" "$@"; }
# Online variant for the setup probe only.
RUN_ONLINE() { podman run --rm --pull=never -w /work -v "$TRIAL:/work:Z" "$IMAGE_ID" "$@"; }
UVPY="uv run --no-project --no-config --offline --python /usr/bin/python3 python"
UVSK="uv run --no-project --no-config --offline --python /opt/trial-venv/bin/python python"
# Unique step IDs from now on: NAME_NNN. Logs of failed attempts stay.
step() { local n; n=$(( $(cat $LOG/counter 2>/dev/null || echo 100) + 1 )); echo $n > $LOG/counter; local id=${1}_$n; shift; printf '%s\n' "$*" > $LOG/$id.cmd; "$@" > $LOG/$id.out 2>&1; local rc=$?; echo "$(date -u +%H:%M:%S) $id exit=$rc out=$(sha256sum $LOG/$id.out | cut -c1-16)" | tee -a $LOG/steps.txt; LASTID=$id; return $rc; }
# Gate edit on the native path (run in $TRIAL).
#   gate NAME OP REPLACE DELETE [RELINK] [EXPECT]
# EXPECT is the name of the expected-difference file without ".json". The default is OP. Use an explicit name when the
# option state changes the expected result, for example footprint-r1-replace-off.
# The function returns the result of the comparison: 0 equal, 1 different, 2 incorrect input, 3 unparsed form.
# It returns 4 when the setup or the GUI step fails, and 5 when the run directory already exists (no overwrite).
# Use gate for a supported gate run. Use gate_exploratory for a probe whose difference is the subject of the test.
# Both return the real comparison result. The log line in gates.txt names the kind.
gate_run() {
  local kind=$1 name=$2 op=$3 replace=$4 delete=$5 relink=${6:-off} expect=${7:-$3} d=out/$2
  [ -e $d ] && { echo "gate: the run directory $d exists. Use a new name." >&2; return 5; }
  mkdir -p $d; cp native/trial.kicad_pro native/fp-lib-table $d/
  uv run --no-project --no-config scripts/edit_native.py $op --in native/trial.kicad_sch --out $d/trial.kicad_sch || return 4
  cp out/g/baseline.kicad_pcb $d/trial.kicad_pcb
  step GUI_$name RUN uv run --no-project --no-config --offline --python /usr/bin/python3 python scripts/gui_update.py --project $d --label $name --replace $replace --delete $delete --relink $relink || return 4
  cp $LOG/$LASTID.out $d/gui_summary.json
  uv run --no-project --no-config scripts/identity.py snapshot $d/trial.kicad_pcb -o $d/after.snap.json || return 4
  uv run --no-project --no-config scripts/identity.py compare out/g/baseline.snap.json $d/after.snap.json --expect out/g/expected/$expect.json > $d/compare.json; local rc=$?
  echo "gate kind=$kind $name op=$op replace=$replace delete=$delete relink=$relink expect=$expect.json compare_rc=$rc" | tee -a $LOG/gates.txt
  return $rc
}
gate() { gate_run supported "$@"; }
gate_exploratory() { gate_run exploratory "$@"; }
