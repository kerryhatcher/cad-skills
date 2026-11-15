#!/bin/bash
# Executable record of the B7 implementation checks. Every line runs one command with explicit paths.
# Each command writes its exit code to run-record.log. The script changes no frozen file.
set -u
REPO=/mnt/storage/projects/cad-skills
SKILL=$REPO/skills/pcb-fab-package
S=$SKILL/scripts
EV=$REPO/docs/reviews/b7-implementation-evidence
FIX=$REPO/tests/fixtures/pcb-fab-package
PROF=$SKILL/supplier/profiles/oshpark-two-layer.yaml
PROJ=$EV/project
LOG=$EV/run-record.log
: > "$LOG"
run() {
  local label="$1"; shift
  "$@" > "$EV/out-$label.txt" 2>&1
  echo "$? :: $label :: $*" >> "$LOG"
}
# 1. Profiles (exit 0 each)
for p in $SKILL/supplier/profiles/*.yaml; do
  run "profile-$(basename $p .yaml)" uv run $S/fab.py profile --profile $p
done
# 2. Slot fixtures: worker in the B6 image, then the comparison (exit 0 each)
for b in board board_rot45; do
  W=$EV/work-$b; mkdir -p $W; cp $REPO/docs/reviews/b7-trial-evidence-r8/prereq/slot/$b.kicad_pcb $W/board.kicad_pcb
  podman run --rm --pull=never --network none --security-opt label=disable -w /work -v $W:/work -v $S:/worker:ro localhost/cad-skills-pcb:b6 /usr/bin/python3 /worker/board_inventory_slots.py /work/board.kicad_pcb > $EV/inventory-$b.json 2> $EV/inventory-$b.stderr
  echo "$? :: worker-$b :: podman localhost/cad-skills-pcb:b6 /usr/bin/python3 /worker/board_inventory_slots.py /work/board.kicad_pcb" >> "$LOG"
  if [ $b = board ]; then P=board_board-PTH.drl; N=board_board-NPTH.drl; else P=board_rot45_board_rot45-PTH.drl; N=board_rot45_board_rot45-NPTH.drl; fi
  run "inspect-slots-$b" uv run $S/inspect_slots.py --board-inventory $EV/inventory-$b.json --pth $FIX/slot/$P --npth $FIX/slot/$N --report $EV/slots-$b.json
done
# 3. Mask fixtures at 4 mil (exits 1, 1, 0, 1, 2, 2, 2)
for c in m39 m40 m41 rr oval overlap m39merge; do
  run "mask-$c" uv run $S/inspect_mask.py --gerber $FIX/mask/$c.gts --limit-mil 4 --report $EV/mask-$c.json
done
# 4. Project flow on a fresh copy of the bare-board template (accepted B6 template, read only)
rm -rf $PROJ; cp -r $REPO/skills/pcb-design/templates/rc-bare-board $PROJ; rm -rf $PROJ/out
cp $PROF $PROJ/manufacturing/supplier.yaml
HASH=$(grep -o '"content_sha256": "[0-9a-f]*"' $PROF | head -1 | cut -d'"' -f4)
sed -i "s|  id: example-two-layer|  id: oshpark-two-layer|; s|  service: Example two-layer service|  service: OSH Park two-layer service|; s|  profile_sha256: b37b37495cbab698f921e7b229585ea890cefd7298f3615cd15cec02bb00fb77|  profile_sha256: $HASH|" $PROJ/board.yaml
run "design" uv run $S/fab.py design --project $PROJ --profile $PROF
run "supplier-no-manual" uv run $S/fab.py supplier --project $PROJ --profile $PROF
mkdir -p $PROJ/out/fab/manual && printf 'Silk short-text check on the saved silk layer: strokes and text at or above 3 mil.\n' > $PROJ/out/fab/manual/silk-check.txt
run "make-observations" uv run $EV/gen/make_obs.py $PROF $PROJ trial-1 $EV/observations.json
run "review-source" uv run $S/fab.py review-source --project $PROJ --profile $PROF --release trial-1 --observations $EV/observations.json --reviewer "R. Reviewer" --out $PROJ/out/fab/source-review/REVIEW.json
REVIEW_SHA=$(sha256sum $PROJ/out/fab/source-review/REVIEW.json | cut -d' ' -f1)
run "package-no-manual" uv run $S/fab.py package --project $PROJ --profile $PROF --release trial-1 --review $PROJ/out/fab/source-review/REVIEW.json --review-sha256 $REVIEW_SHA --dest $PROJ/out/fab/packages/unqualified
run "make-manual" uv run $EV/gen/make_manual.py $PROJ $PROJ/out/fab/design
run "supplier-manual" uv run $S/fab.py supplier --project $PROJ --profile $PROF --manual $PROJ/out/fab/manual-record.json
run "package-qualified" uv run $S/fab.py package --project $PROJ --profile $PROF --release trial-1 --review $PROJ/out/fab/source-review/REVIEW.json --review-sha256 $REVIEW_SHA --dest $PROJ/out/fab/packages/qualified
# 5. Affected test suites (exit 0 each)
run "test-fab-package-geometry" uv run $REPO/tests/test_pcb_fab_package.py
run "test-fab-workflow" uv run $REPO/tests/test_pcb_fab_workflow.py
run "test-pcb-tools" uv run $REPO/tests/test_pcb_tools.py
run "test-project-io" uv run $REPO/tests/test_project_io.py
run "test-skill-packages" uv run $REPO/tests/test_skill_packages.py
run "test-snippets" uv run $REPO/tests/test_snippets.py
