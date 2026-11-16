# U3 netlist-import edit tests. Source this file. It copies the trial directory and runs offline container steps.
S=/tmp/claude-1000/-mnt-storage-projects-cad-skills/fbbd1c31-73f1-4465-b310-2c58ada868be/scratchpad/u3
REPO=/mnt/storage/projects/cad-skills-u3
TRIAL=$S/trial
LOG=$S/logs
IMAGE_ID=d881df4ef3e2ec76995f4070596550db118b23e7f6db9017f09a418c44c4b1c2
sync_trial() { tar -C $REPO/examples/pcb-trial --exclude=out -cf - . | tar -C $TRIAL -xf -; }
RUN() { podman run --rm --pull=never --network none -w /work -v "$TRIAL:/work:Z" "$IMAGE_ID" "$@"; }
SKENV="export KICAD10_SYMBOL_DIR=/usr/share/kicad/symbols KICAD10_FOOTPRINT_DIR=/usr/share/kicad/footprints; cd /work &&"
UVSK="uv run --no-project --no-config --offline --python /opt/trial-venv/bin/python python"
UVPY="uv run --no-project --no-config --offline --python /usr/bin/python3 python"
step() { local n; n=$(( $(cat $LOG/counter 2>/dev/null || echo 300) + 1 )); echo $n > $LOG/counter; local id=${1}_$n; shift; printf '%s\n' "$*" > $LOG/$id.cmd; "$@" > $LOG/$id.out 2>&1; local rc=$?; echo "$(date -u +%Y-%m-%dT%H:%M:%SZ) $id exit=$rc out=$(sha256sum $LOG/$id.out | cut -c1-16)" | tee -a $LOG/steps.txt; LASTID=$id; return $rc; }
# zsh does not split a variable into words. Use these functions in a step.
runpy() { RUN uv run --no-project --no-config --offline --python /usr/bin/python3 python "$@"; }
