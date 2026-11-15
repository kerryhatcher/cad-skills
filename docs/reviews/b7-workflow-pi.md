# B7 workflow paper scope check (pi-skill-dev)

Date: 2026-11-14 UTC. Scope: `b7-workflow-draft-root.md` and `b7-workflow-codex.md` against the accepted
r8/B6 interface. Paper review only. I did not inspect changing code and I ran no probe.

## Result

I agree that the six workflow points restore the accepted r8/B6 interface. I have no scope correction.

| Point | Accepted basis |
|---|---|
| 1. Path and publication | r8 section 3 path policy and `publish_dir`; r8 section 9 package publication; B6 fresh-staging and handled-removal rule |
| 2. Runtime identity | r8 section 3 exit 2 runtime or image mismatch; B6 measured image identity and host refusal |
| 3. Input and result bindings | r8 section 7.4, section 8.2 and section 9.5; B6 "compared again before publication" freshness rule |
| 4. Supplier rules | r8 section 7.1 to 7.3 and acceptance row 15a |
| 5. Complete supplier conditions | r8 section 8.3 and section 9.3; acceptance rows 23 to 32, 42 and 43 |
| 6. Export semantics | r8 section 1 owned derivative; section 9.2 checks; acceptance rows 9 and 38 to 40; the B6 export checks |

The source-review omission and tamper gate (r8 section 8.2, acceptance rows 33 to 37) and the qualification
gate (r8 section 9) are not among the six points. They are enforced by the existing tested `fab.py`
functions. The workflow must call them. They are not a gap in the six restoration points.

The B6 refusal-log and residual-stage reporting are not in the six points. They belong to the existing
staging and check helpers. They are not a gap in the six restoration points either.

The six points add no framework and no new design phase. They keep the accepted negative cases. The record
must show the actual positive workflow and the negative cases.

## Status

I confirmed the two final geometry decisions. I await the final geometry checkpoint. The full workflow
implementation review comes after its freeze.
