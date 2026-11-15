# B6 replacement review: Pi

Date: 2026-11-14.

**Final B6 verdict: accepted, with the stated limits.** The replacement resolves the native version-probe gap and the template Git inclusion. The corrected scope from the 210-file review is retained.

## 1. Reviewed bytes

| Item | Value |
|---|---|
| Replacement manifest | `docs/reviews/b6-replacement-files.sha256`, 211 entries, `f93454c545a355e43be3e447b41baa334299dbf09bb08fff4c57ab3f234aca39` |
| Manifest check | 211 of 211 `OK`, before and after this review |
| Repair record | `docs/reviews/b6-native-repair-record.md`, `2e8f4e2031a19bbf552ee366f0c5f38ce591890dff416f5f684fe52108f73481` |
| Controller | `skills/pcb-design/scripts/pcb.py`, `0928be463f6503b41d5c7ba02c076556c0ac750630da63ac8c86866cf664cabe` |
| Tests | `tests/test_pcb_design.py`, `242176ead31847772750c58b224933178e2e1bc265ca8245909912de87aebe6c` |
| Ignore file | `.gitignore`, `6b3a6acf3bb8b3ee922cbf3b7e9c57224a86226b04fae0b0ea5a9f89b1ac2a0c` |
| Prior corrected scope | `b6-correction-files.sha256` `ab6a32f6...`; `b6-correction-review-pi.md` `207bb0f8...` |

Changed against the 210-file manifest: `pcb.py`, `tests/test_pcb_design.py`. Added: `.gitignore`. No path removed.

## 2. Native repair

`native_versions_ok(lock, op)` probes only `OP_TOOLS[op]` through `measure_tools(None, tools=needed)`. A needed tool that cannot be measured is `runtime.native_unavailable`, exit 2. `measure_tools` catches `OSError` and records exit 127 with version `None`. `tool_versions_of(image, op)` records only the operation's tools. The five publication callers pass `erc`, `drc`, `sim`, `update` and `export`.

Focused stub probe, no container:

| Case | Result |
|---|---|
| Native `sim`, kicad-cli absent, ngspice present | `native_check("sim")` passes. `native_versions_ok(lock, "sim")` passes with no kicad-cli probe. `tool_versions_of(None, "sim")` returns `{"ngspice": "ngspice-44.2"}` and no `FileNotFoundError`. |
| Native `sim`, ngspice missing | `native_versions_ok(lock, "sim")` gives `runtime.native_unavailable`, exit 2, not `FileNotFoundError`. |
| Native `erc`, ngspice absent, kicad-cli present | `native_check("erc")` passes. `native_versions_ok(lock, "erc")` passes. |

The new test `test_native_probes_are_per_operation_and_never_traceback` covers the same cases and the missing-executable record.

## 3. Publication probes

`tool_versions_of(image, op)` is called with the operation in all five paths: `erc` (line 600), `drc` (697), `sim` (806), `update` (1015) and `export` (1245). On the native route `image` is `None`. The binding records only the operation's tools. The focused probe confirms that a native `sim` binding does not run `kicad-cli` and does not raise.

## 4. Real Git inclusion and exclusion

The real repository was checked with `git check-ignore -q`. The required template interface file is not ignored (exit 1). The other paths are ignored (exit 0).

| Path | Exit |
|---|---:|
| `skills/pcb-design/templates/rc-bare-board/out/history/interfaces/5254508d...json` | 1 (not ignored) |
| `.../out/history/interfaces/notes.txt` | 0 |
| `.../out/history/interfaces/sub/y.json` | 0 |
| `.../out/history/boards/x.kicad_pcb` | 0 |
| `.../out/reports/a.json` | 0 |
| `.../out/export/z.json` | 0 |
| `out/history/interfaces/h.json` | 0 |
| `examples/pcb-trial/out/history/interfaces/h.json` | 0 |

`git ls-files --others --exclude-standard` lists the required file, so it is untracked and not ignored. The new test `test_gitignore_exception_is_template_history_only` covers the same table. The exception is template-only and does not unignore the general `out/`.

## 5. Retained corrected-scope acceptance

I retain the acceptance of the 210-file correction. The readiness corrections (`review_problems` coverage, `automatic_problems` expectation bytes), the strict parser (`strict_json`, `fullmatch`, `SIM_RANGE`), the `staging.residual` policy and the prose corrections are unchanged in the replacement. The root readiness and assertion probes pass at the 210 revision; my re-runs at that revision gave the same results.

The corrected interface and parser evidence is covered by `b6-correction-review-pi.md` (210 review) and the root probes `b6-final-probe-root.json` and `b6-assertion-probe-root.json`. Codex did not write a 210 review, so it must use this evidence and focused source reads. Do not assume a check that the evidence does not show.

## 6. Final limitations

- The native route is tested inside the runtime image only. The host has no KiCad installation, and no host installation was made.
- The GUI adapter is certified only for the measured image ID `b2731833...`. The rebuilt image `032582d4...` is not certified.
- The blind-via fixture is not measured. The slot fixture covers the slot-or-blind-via refusal request. A blind or buried via on a four- or six-layer board is possible and the worker refuses it; the refusal is untested, not impossible.
- The local structural linter is not an STE certification.
- The `.gitignore` exception is not committed.
- The 41-test suite and the GUI were not rerun for this review, as instructed. The 41-test result is the record's captured log.
- The template history file is a generated artifact; the negation keeps only `*.json` under `out/history/interfaces/`.

## 7. Verdict

B6 is accepted with the limits in section 6. The native version-probe gap and the template Git inclusion are repaired. The corrected scope is retained. No implementation edit was made.
