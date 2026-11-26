#!/usr/bin/env bash
# Tell the agent where the plugin files are.
# The skill documents show paths such as skills/NAME/scripts/FILE.py.
# These paths are relative to the root of the plugin, not to the project of the user.
set -eu

root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd -P)"

context="The cad-skills plugin is installed at ${root}. The skill documents show script paths such as skills/NAME/scripts/FILE.py. Resolve these paths against ${root}, not against the current directory. Run all Python with uv."

# Escape backslashes and double quotes for JSON.
context="${context//\\/\\\\}"
context="${context//\"/\\\"}"

printf '{"hookSpecificOutput":{"hookEventName":"SessionStart","additionalContext":"%s"}}\n' "$context"
