# B9 numeric and stock resolutions: Pi verdict

Date: 2026-11-15. Author: pi-pcba-dev.

## Verdict

I agree to both narrow resolutions.

- Numeric: keep `source_tokens` with the raw x, y and angle strings. The numeric
  fields are derived finite values. The interface section 6 wording is corrected.
- Stock: for one manufacturer and MPN, refuse conflicting stock or lifecycle records
  before a stock claim. Identical repeated records aggregate demand per populated
  reference and do not add stock quantities.
- `assembly_instruction`: agree. It copies the `hand_installed` reason and is empty
  for automatic rows.
- Resolved part paths: agree. The row and the `inputs` record must name the same
  project-relative resolved path.

## One technical conflict

A non-numeric position token is not a non-finite number. `float()` raises `ValueError`.
The step then prints a traceback and exits, not one finding.

Probe:

```bash
# change one footprint to (at abc 10 0)
uv run skills/pcba-design/scripts/pcba.py neutral --project /tmp/b9bad --board board.kicad_pcb \
    --variant base --as-of 2026-11-15
```

Result: `ValueError: could not convert string to float: 'abc'`, exit 1, with a
traceback. The contract says a refusal prints one finding. The rework must turn a
rejected token into one refusal. The finite check covers `nan` and `inf`. It does not
cover a token that `float()` rejects.

I also measured that a `nan` token currently writes output with exit 0. The
`source_tokens` finite refusal covers that case.
