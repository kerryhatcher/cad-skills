# B7 geometry checkpoint review (pi-skill-dev)

Date: 2026-11-14 UTC. Scope: the mask inspector and the slot reader in the six frozen files of
`b7-geometry-checkpoint-claude.md`.

This report gives the review result only. It does not change the frozen files. It does not accept the
remaining fabrication implementation.

## Hash check

The six measured hashes match the checkpoint before and after this review. The last measurement follows.

```text
ade74723a60442ced804686e8784526c283f619064cccf17f842116cad0af328 skills/pcb-fab-package/scripts/inspect_mask.py
c91d475f92bc676780a7fa8a3e9af5991e728f02128eab187ea9699db4e1958d skills/pcb-fab-package/scripts/macro_defs.py
4b1b87dcbb00d69eba86b7192683466e851443dde59a6b78f5cf823bd8ce1f20 skills/pcb-fab-package/scripts/export_inspect.py
9b543eb20390cde8f4811e805b4498bc6ac50dea2140076197f29dda9e3e39dc skills/pcb-fab-package/scripts/inspect_slots.py
ed8a9d74520420255f789c49c5b4464af67e312ca53e4d9f538291ec87870838 skills/pcb-fab-package/scripts/board_inventory_slots.py
182ca9e52faa55cc557e67f57462192b7d36ce2d22e8ec35c1ab44584ae72341 tests/test_pcb_fab_package.py
```

The checkpoint file `docs/reviews/b7-geometry-checkpoint-claude.md` is
`7c7ed0f019bddb5ba453cd17c476419bbbc1ab7f76be0a4d27d90527e1e94122`.

## Measured observations

I ran the declared command one time. It returned exit 0 and 80 of 80 passed. I ran independent negative
probes. I read the retained probe results. The probe inputs and outputs stay in `/tmp/b7-geo-probe*.json` and
`/tmp/b7-geo-probe2-out.txt` on this host. The file `/tmp/b7-geo-probe2-out.txt` holds two concatenated JSON
objects with equal values. I read the first object with `JSONDecoder.raw_decode` and used only those values.

### G1: the macro definition test has a bypass

- Inline macro: the line `%MOMM*%%AMRoundRect*1,1,10,0,0*%` holds the macro on the same line as another
  command. The scanner `macro_blocks` returns no block. The inspector returns exit 0 and `pass`. The two
  flashes are overlapping circles of 10 mm diameter.
- Leading whitespace macro: the line ` %AMRoundRect*1,1,10,0,0*%` has one space before `%AM`. The scanner
  returns no block. The inspector returns exit 0 and `pass`.
- The scanner reads `%AM` only at the start of a line. Gerbonara accepts both forms above.
- Measured: `g1_scanner_blocks_inline` is `[]`, `g1_scanner_blocks_space` is `[]`. Both inspector runs return
  `exit 0` and `result pass`. The `inspect_mask.py` hash is equal before and after.

### G2: the report can identify bytes that the inspector did not examine

- `inspect()` reads the file bytes for the geometry. `main()` reads the same path again for `gerber_sha256`.
- A controlled change between the two reads gives `exit 0` and `result pass` with the hash of the changed
  file. A direct inspection of the changed bytes gives `exit 1` and `result fail`.
- Measured replay through `main()`: `exit 0`, `result pass`, `gerber_sha256`
  `7bacd29048dff6339c2c3c6ee96c670ddd116c128fd0dc9d27cc043d1932b296`, `minimum_web_mm` null. The changed
  bytes have the same hash `7bacd2...`. A direct inspection of the changed bytes gives `exit 1`, `result
  fail`, `minimum_web_mm 0.09905999999999937` mm.
- The `inspect_mask.py` hash is equal before and after.

### G3: no elapsed-time bound

- The source of `inspect_mask.py` has no time limit. The names `import time`, `time.monotonic`, `deadline` and
  `elapsed` are absent. Measured: `g3_source_has_time_limit` is `false`.
- The code stops at 2,000,000 candidate pairs. The pair limit is not a time limit.
- Measured timing on this host, with a tiny aperture and 10,000 flashes:
  - CLI run: `exit 2`, `unsupported "more than 2000000 candidate pairs"`, 1.585 s.
  - In-process run: same refusal, 1.511 s.
- Measured timing with the same aperture and spacing as the root probe, placed in a row (increasing X,
  constant Y) and a 22,000 mil limit: `exit 2`, same refusal, 1.572 s.
- The same row with a 4 mil limit: `exit 0`, 0 pair checks, 0.089 s. The X-only window excludes the separated
  pairs. The root probe places the same flashes in a column (constant X, increasing Y), so its X window keeps
  every pair. See the note below.
- The measured times are below two seconds on this host. The absent enforcement is the finding. This report
  does not claim a measured time violation.

### Aperture with a hole

- The input `%ADD10C,2X1.9*%` parses as a `CircleAperture` with `diameter 2.0` mm and `hole_dia 1.9` mm.
- `shape_of` returns `core [0,0,0,0]` and `radius 1.0`. It ignores `hole_dia`.
- The probe with the 2 mm holed circle and a 1 mm circle at the same centre returns `exit 2` and
  `unsupported "overlapping cluster: objects 0 and 1 overlap by 1.500000 mm"`. The refusal reason is the
  solid disk model, not the hole.
- The frozen subset says "dark flashes of circle apertures". It does not state that a circle aperture with a
  hole is unsupported. The inspector measures the wrong geometry.

### RoundRect parameter geometry

- A valid instance has the points `(0,0),(4,0),(4,4),(0,4)` in order. A malformed instance has the points
  `(0,0),(4,0),(0,4),(4,4)` in order.
- Both instances return `core [0,0,4,4]` and `radius 0.1`. Both inspector runs return `exit 0` and `result
  pass`.
- `shape_of` takes `min` and `max` of the eight point coordinates. It does not examine the point order or the
  rectangle geometry. The macro definition text is equal in both runs, so the definition test does not
  refuse them.

### Excellon terminal state

- A file without `M30` parses. Measured: `accepted true`, one record.
- A file with a coordinate record after `M30` parses. Measured: `accepted true`, two records.
- An empty board and empty drill files without `M30` return slot-inspection `exit 0` with both classes
  `pass`.
- `export_inspect.parse` holds `M30` in `PLAIN_COMMANDS`. It does not require the terminal record and it does
  not stop at it.

### Supported shapes and refused constructs

- Two rectangles that touch on an edge: `merged_opening 1`, `exit 0`.
- Two rectangles that touch at a corner: `merged_opening 1`, `exit 0`.
- Clear polarity: `exit 2`, `unsupported "object 0 has clear polarity"`.
- A region: `exit 2`, `unsupported "object 0 is a Region; only flashes are supported"`.
- An obround aperture: `exit 2`, `unsupported "object 0 uses the unsupported aperture ObroundAperture"`.
- A RoundRect macro definition with one extra space: `exit 2`, `unsupported "the RoundRect macro definition
  differs from the measured definition"`.
- 200 rectangles with 0.05 mm gaps: `exit 1`, `fail 199`, `listed_pairs 100`, `minimum_web_mm
  0.049999999999954525` mm. The stored pair list stops at 100. The pair count stays 199.

### Slot fixture agreement

- The declared command reported the measured 0-degree and 45-degree board fixtures as a match. It also
  reported endpoint reversal, plating class, multiplicity, the 501 nm and 502 nm tolerance cases as the
  expected results.
- I did not repeat these passing probes.

## Agreement on the combined narrow correction scope

I agree with the three root findings and the three Codex findings. The corrections are in scope. Each one
stays narrow.

1. G1: validate the macro definition that the Gerber parser uses. Do not let a difference between the
   scanner and the parser hide a definition. Add the inline and whitespace cases as regressions.
2. G2: hash and parse one byte snapshot. Return that hash with the measurement. Do not read the path again
   for the report. The caller must bind and compare the hash before publication. Add the controlled-change
   regression.
3. G3: enforce the two-second bound across parsing and the inspection. Put the bound in the worker or its
   caller. Keep the pair limit as an additional bound. The bound must not depend on a host-specific pair
   count.
4. Aperture holes: refuse a circle aperture with a hole until the inspector measures its geometry. Add a
   regression.
5. RoundRect parameters: accept only the measured point order and an axis-aligned rectangle. Refuse other
   parameter geometry. Add a malformed-parameter regression.
6. Excellon terminal state: require the terminal `M30`. Refuse every record after it. Add a missing-end
   regression and a trailing-record regression.

The supported subset stays as it is. Do not add a general Gerber parser, a general Excellon parser or a new
framework.

## Note on the root timing probe

The root G3 finding is correct. The root probe and my probe measure different inputs. The root probe keeps X
constant and increases Y. That is a column. The inspector tests the candidate window on X only. A column
therefore keeps every pair in the window. My probe kept Y constant and increased X. That is a row. The X
window excludes the separated pairs, so the pair count stays low. The root column with 0.3 mm spacing reaches
the 2,000,000 pair limit. That result is consistent. The two probes do not disagree. Neither measured time
exceeds two seconds. The missing enforcement stays the finding.

## Unmeasured limits

- No timing probe exceeded two seconds on this host. The worst-case time at the pair limit on a supported host
  is unmeasured.
- The elapsed-time bound is not enforced, so a slower host can exceed two seconds. The exact host list and the
  exact worst case are unmeasured.
- The geometry of a circle aperture with a hole is unmeasured. The scope refuses it.
- The exact distance error for a non-rectangular RoundRect parameter set is unmeasured. The scope refuses it.
- The Excellon behavior for more than one `M30`, for trailing comments after `M30`, and for a missing `M48`
  is unmeasured.

## Verdict

The measured supported geometry cases pass. The checkpoint is not accepted for implementation freeze. The
macro bypass, the file-hash binding, the absent time bound, the aperture-hole geometry, the RoundRect
parameter geometry and the Excellon terminal state need correction and focused regressions first. The six
frozen files stay unchanged.
