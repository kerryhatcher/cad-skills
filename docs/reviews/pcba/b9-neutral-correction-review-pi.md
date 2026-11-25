# B9 corrected neutral batch review: Pi

Date: 2026-11-15. Author: pi-pcba-dev. Reviewer for the B9 bounded start.

Subject: `docs/reviews/pcba/b9-neutral-correction-claude.md`, the frozen corrected batch
for interface sections 4 to 8. Authorization: `docs/reviews/pcba/b9-neutral-correction-root.md`.

Scope: all 15 agreed repairs. Sierra conversion, B10 publication, alternates and the
placement fields stay outside. I changed no product file.

## 1. Result

The 15 agreed repairs are present and correct. I accept the batch in this scope.

- `uv run tests/test_pcba_design.py`: 35 passed, 0 failed, exit 0.
- All 30 listed file hashes match.
- `sha256sum -c skills/pcba-design/COPY_SHA256.txt`: 15 of 15 copies OK. The copies are
  byte-identical to their sources.
- The snippet routing failure is the known pending integration item. It is not a defect
  of this batch. Release owns it.

One blocker is outside the 15 items but inside the examined output-refusal area. It is
item B1 in section 5.

## 2. Before and after hashes

The batch changed three files. The other 27 files are unchanged.

| Path | Before | After |
|---|---|---|
| `docs/reviews/b9-b10-interface-claude.md` | `0be00806d483b138fa9155229b4a5977330f1775493debac2479ad82dc5049cb` | `36d7e1b0917417d6e537db57fd46a92d4b949303e1d13d5f40b93e0a29b1d361` |
| `skills/pcba-design/scripts/pcba.py` | `6f9b56a912bf699b07ff83d2e2893cc566b8954df22f45e3728bef9cd365c0c7` | `1e69b6f3bced2cb9b30556829a6ced51b6d8330a0a1c1353239e2033bc3471a4` |
| `tests/test_pcba_design.py` | `1efb62f0c00706ebeb9fa0dccbd20fed7c3fdfc18c58d4ac01f587cb6b625ca1` | `123592419d4cbe7a7ee3953a8e1ffb09bccc0e8cac6912c8326689efc905b454` |

Every other row in the file table matches the earlier batch byte for byte.

## 3. The 15 items

| Item | Result | Evidence |
|---|---|---|
| 1 lock before capture | Pass | `main` holds `project_lock` around `build`. An external lock gives `project.locked`, exit 1. A normal run leaves no lock file. |
| 2 confinement by resolved path | Pass | A `components/` link to `../outside.yaml` gives `map.path_escape`. |
| 3 one snapshot per file, relative paths | Pass | Two spellings of one file give one `parts` input. |
| 4 same resolved path in rows and inputs | Pass | The row `part_path` and the input record name the same resolved path. |
| 5 output alias refusal | Pass | `--out board.yaml` and a hard link give `output.aliases_input`. The input bytes do not change. |
| 6 rehash before write | Pass | A changed input gives `input.changed` before the write. |
| 7 raw tokens | Pass | `source_tokens.x` keeps `10.123456789012345678` exactly. |
| 8 finite values, named refusals | Pass | `abc` gives `board.malformed_token`. `nan` and `1e400` give `board.nonfinite_token`. One finding, no traceback. |
| 9 implicit zero angle | Pass | `(at 10 10)` gives `angle_source` `implicit_zero` and a null angle token. |
| 10 kept row fields | Pass | `datum`, `midpoint_mapping`, per-row `board_quantity`, empty `selected_alternate`. |
| 11 zero per-board quantity | Pass | Excluded rows have `per_board_quantity` 0. |
| 12 `assembly_instruction` | Pass | The hand reason is copied. Automatic rows are empty. |
| 13 BOM key | Pass | Two hand reasons make two groups. |
| 14 conflicting stock refusal | Pass | A different stock quantity and a different lifecycle each give `stock.conflicting_records`. |
| 15 demand once per reference | Pass | Four populated references at five boards give demand 20. Identical records share one stock result. |

## 4. Independent probes

I ran these probes outside the frozen test file.

- Snapshot reuse: a link inside `components/` resolves to one file. Two spellings,
  `components/resistor-10k.yaml` and `components/./resistor-10k.yaml`, give one `parts`
  input and the same row `part_path`.
- Output alias: a symlink output to an input gives `output.aliases_input`.
- Lock: a held external lock gives one finding, exit 1.
- Freshness: a changed part file after capture gives `input.changed`, and no output.
- Numeric: the four token classes match item 8 exactly.

## 5. Findings

### B1. Blocker: output path errors are uncaught

An output path outside the project, or an output path that is a directory, prints a
traceback. It does not print one finding.

Probes:

```bash
uv run skills/pcba-design/scripts/pcba.py neutral --project /tmp/p2 --board board.kicad_pcb \
    --variant base --as-of 2026-11-15 --out ../escape.json
# project_io.PathEscape: The path ../escape.json is outside the project root.

uv run skills/pcba-design/scripts/pcba.py neutral --project /tmp/p3 --board board.kicad_pcb \
    --variant base --as-of 2026-11-15 --out components
# IsADirectoryError: ... -> '/tmp/p3/components'
```

Both runs exit 1 with a traceback. Interface section 3 says a refusal prints one finding.
The earlier batch had the same uncaught structure, so this is not a regression. It is in
the examined output-refusal area, and it is cheap to correct. Wrap the output
confinement and write in the same handling and emit one finding, for example
`output.path_escape` and `output.not_a_file`.

### F1. Minor: the alias finding names the default output path

`check_output_alias` reports `DEFAULT_OUT` in the finding `file` field. With a custom
`--out`, the field does not name the requested path. Probe: `--out out/link.json` reports
`out/pcba/assembly-neutral.json`.

## 6. Limits

- Alternates remain incomplete. The map schema rejects an `alternates` key.
- The placement fields (`export_rotation_deg`, midpoint estimates) are not produced.
- The snippet routing test fails only on the missing `pcba-design` entry. Release owns it.
- No supplier file and no manifest is written.
- This acceptance covers the 15 items. It does not cover Sierra conversion or B10.
