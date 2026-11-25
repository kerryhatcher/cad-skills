# B12 final local correction record

Date: 2026-11-15 UTC. Author: `claude-release-dev`.
Freeze: `docs/reviews/b12-final-local-repair-freeze-claude.sha256` (41 entries, SHA-256 `efbf8f6144aef87d7cca5f8438ed8f1b94b6a40acbf083d42510ba6e72a1717b`).

## Correction of the count-order sentence

The earlier child-tick test took its first count after the stub returned, and then slept 1.5 s before the second count. It did not sample the tick file while the stub ran. The earlier wording that the first count was taken after the sleep is incorrect. The live observation was not made.

The replacement test samples the tick file while the stub runs. It records the immediate post-return count and the count after the declared 1.5 s interval. It asserts at least two live increases and an unchanged count after the return.

## Applied

- Baseline policy enforced at planning and again before dispatch. The Codex baseline is refused with every other gate open. The refused run does not reach the adapter stub and consumes no budget.
- Pi baseline rejects a nonempty skill path list. `--skill` is attached only in skill mode.
- Live sampling of the child tick file, one attempt, no automatic retry.

Provider authorization remains zero. No provider call, commit, merge or push.
