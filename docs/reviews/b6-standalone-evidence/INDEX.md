# Standalone rebuilt-image evidence (B6 correction)

Host: kudzu. Image: localhost/cad-skills-pcb:b6-rebuild, ID 032582d4298bfe68b07fde9942c5a92148de90b4a7fe911c095799ffc1eb2285 (built with --no-cache).
Isolated project (absolute): /tmp/claude-1000/-mnt-storage-projects-cad-skills/338648c2-5719-486b-b8c3-0bfb3fce6649/scratchpad/standalone-logged/project
Negative lock copy (absolute): /tmp/claude-1000/-mnt-storage-projects-cad-skills/338648c2-5719-486b-b8c3-0bfb3fce6649/scratchpad/standalone-logged/mismatch
Skill copy used for the commands (absolute): /tmp/claude-1000/-mnt-storage-projects-cad-skills/338648c2-5719-486b-b8c3-0bfb3fce6649/scratchpad/standalone-logged/skill

| Step | Command | Exit | Log (stdout / stderr) |
|---|---|---|---|
| env_rebuilt | `uv run scripts/pcb.py env --project PROJECT --json` | 0 | logs/env_rebuilt.stdout, logs/env_rebuilt.stderr |
| erc | `uv run scripts/pcb.py erc --project PROJECT` | 0 | logs/erc.stdout, logs/erc.stderr |
| drc | `uv run scripts/pcb.py drc --project PROJECT` | 0 | logs/drc.stdout, logs/drc.stderr |
| sim | `uv run scripts/pcb.py sim --project PROJECT` | 0 | logs/sim.stdout, logs/sim.stderr |
| export | `uv run scripts/pcb.py export --project PROJECT` | 0 | logs/export.stdout, logs/export.stderr |
| check_ready | `uv run scripts/pcb.py check --project PROJECT --for ready` | 0 | logs/check_ready.stdout, logs/check_ready.stderr |
| check_export | `uv run scripts/pcb.py check --project PROJECT --for export` | 0 | logs/check_export.stdout, logs/check_export.stderr |
| gui_on_rebuilt | `uv run scripts/pcb.py update --project PROJECT --adapter gui --expect expect/r2-value.json (no expectation file yet)` | 2 | logs/gui_on_rebuilt.stdout, logs/gui_on_rebuilt.stderr |
| negative_lock_digest_env | `uv run scripts/pcb.py env --project MISMATCH --json (lock digest = B6 image ID, tag = rebuilt tag)` | 2 | logs/negative_lock_digest_env.stdout, logs/negative_lock_digest_env.stderr |
| negative_lock_digest_erc | `uv run scripts/pcb.py erc --project MISMATCH` | 2 | logs/negative_lock_digest_erc.stdout, logs/negative_lock_digest_erc.stderr |
| negative_explicit_other_image | `uv run scripts/pcb.py env --project PROJECT --image localhost/cad-skills-pcb:b6 --json` | 2 | logs/negative_explicit_other_image.stdout, logs/negative_explicit_other_image.stderr |
| gui_on_rebuilt_with_expect | `uv run scripts/pcb.py update --project PROJECT --adapter gui --expect expect/r2-value.json` | 2 | logs/gui_on_rebuilt_with_expect.stdout, logs/gui_on_rebuilt_with_expect.stderr |

The exits are the command exit codes captured directly, not a filter's exit. The simulation binding names the raw log under project-out/reports/raw/.
