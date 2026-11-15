# B7 geometry correction authorization

Date: 2026-11-14 UTC.

Both reviewers agree on six corrections to the frozen geometry checkpoint.
The reports are `b7-geometry-review-codex.md`, `b7-geometry-review-pi.md`, and `b7-geometry-review-root.md`.

1. Validate the macro definition that the Gerber parser uses. Refuse the inline and whitespace bypass cases.
2. Parse and hash one byte snapshot. Return its hash with the result. Compare that hash before publication.
3. Enforce the two-second bound across parsing and geometry inspection. The pair cap can remain as an additional bound.
4. Refuse unmeasured aperture holes. Do not treat a holed aperture as a solid shape.
5. Validate the RoundRect parameters and supported rectangle geometry. Refuse unsupported or malformed corner order and geometry.
6. Require the Excellon terminal record. Refuse records after `M30` and add the missing-terminal regression.

Claude can now change the six frozen geometry files for these corrections and their focused regressions.
Preserve the original checkpoint as history. Make a replacement manifest and record after the affected tests pass.
Do not repeat unrelated tests or expand either parser.
Continue the separate workflow implementation. Full B7/B8 acceptance remains pending.

## Evidence clarification

The root timing probe uses constant X with increasing Y:

```python
f'X10000000Y{10000000+i*300000}D03*\n'
```

This is a column. The inspector's X-only window retains the candidate pairs.
Pi's probe uses increasing X with constant Y. That is a row, and its X window excludes the separated pairs.
The probes therefore measure different inputs. Neither measured time exceeds two seconds.
The missing enforcement remains the agreed finding. No new timing run is necessary to resolve this distinction.

The prerequisite record already establishes the source-exclusion format and staged restoration.
The geometry review does not repeat or reverse that accepted prerequisite result.
