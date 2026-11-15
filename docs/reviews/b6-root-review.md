# B6 lead review

Date: 2026-11-14. Scope: the final record, prose, and the independent RC assertion. The two code reviews remain separate.

The manifest hash is `d700afd728a13cd42948058cb6b1386bab8b69de0b6a15bcb409bf251160aebe`. All 154 entries matched before this review. The record hash is `7d198aff5a8b8a24d362ec165365386fc6ea40805db8de8ebe2306c1b3f9a758`.

## Independent RC result

The final A4 project circuit uses R2 at 20 kohm and C1 at 100 nF. Its own assertion measures at 2 ms. It does not encode the agreed 1 ms target.

The lead copied that circuit to a temporary directory. The copy changed only the measurement time from 2 ms to 1 ms. The existing B6 image ran ngspice with no network. The source circuit stayed unchanged.

The result is 1.298448 V. The predeclared target is 1.2984 V, with an absolute tolerance of 0.012984 V. The independent assertion passes. The source circuit hash is `a56f78963daff2d4198472c538c4ea27bd17c15270d5f82ebd0200daa63fd147`.

Evidence: `b6-rc-review-root.json` and `b6-rc-review-root.log`. The probe is `/tmp/cad-skills-b6-rc-review.py`. This result closes the independent numerical assertion. It does not establish the other B6 acceptance conditions.

## Prose corrections

The existing local linter runs without network access:

```bash
uv run /tmp/cad-skills-ste-lint.py skills/pcb-design/SKILL.md skills/pcb-design/references/*.md skills/pcb-design/runtime/BUILD.md skills/pcb-design/examples/rc-edit/README.md skills/pcb-design/templates/rc-bare-board/README.md
```

It reports 42 findings. Some synonym findings concern technical names or quoted commands. Examine them individually. The semicolon, long sentences, and known-actor passive sentences need correction under AGENTS.md. The linter output does not establish STE certification.

Correct the blind-via statement in the final record and `references/trial-limits.md`. Four-layer and six-layer boards can represent blind and buried vias. The slot fixture satisfies the agreed slot-or-blind-via refusal test. A separate blind-via test remains unmeasured, not impossible.

Correct the final record's statement that STE tools need a network or dictionary download. The local structural linter exists and ran successfully.

## Remaining readiness defects

The lead ran `/tmp/cad-skills-b6-final-probe.py` through `uv` on two temporary A4 copies. Both commands returned exit 0 and `check: ready`.

1. The manual review had valid fields and current hashes, but `examined` contained only `/thickness_mm`. No prior interface or automatic result existed. The agreed fallback needs all top-level keys.
2. The automatic path had no manual review and no `out/reports/update.expect.json`. The command still accepted its automatic result. It must compare the preserved expectation bytes with the recorded hash.

Evidence: `b6-final-probe-root.json`. These are CLI measurements, not only helper calls. Both defects block B6 acceptance. They complete the previously agreed correction scope.

## Assertion parser defects

The lead ran `/tmp/cad-skills-b6-assertion-probe.py` through `uv`. The frozen parser accepts duplicate JSON keys and a final newline in the measurement identifier. An expected value of `10**400` raises an uncaught `OverflowError`.

Evidence: `b6-assertion-probe-root.json`. These are parser measurements. Reject duplicate keys and prohibited identifier characters. Use whole-string validation. Handle numbers outside the simulation measurement range with an input finding, not a traceback. Add CLI regressions for the three cases. Do not change the accepted general contract parser's large-integer behavior.

## Review limits

No implementation file changed during this review. No broad suite ran. Keep B6 frozen until the combined correction decision. The new independent assertion record does not justify another agent trial.
