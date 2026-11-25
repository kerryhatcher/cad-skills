# B11 end-to-end run log

Image: `localhost/cad-skills-pcb:b6`, ID `b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f`, KiCad CLI 10.0.5. No pull. Podman runs with `--pull=never --network none`.

Fresh fixture: `uv run templates/mech-fit-a/make_fixture.py --out DIR`. Board SHA-256 `37105cf50e2bb0c997f7b9f6a02affef2f101a6b0684a4024d5a78541f8e20ba`.

## Positive flow (fixture flow3, final code)

| Step | Command | Exit |
|---|---|---|
| export | `uv run scripts/mechanical.py export --project DIR` | 0 (kicad steps: step 0, dxf 0, drill 0) |
| fit | `uv run scripts/mechanical.py fit --project DIR` | 0 (geometry pass, fit pass) |
| release | `uv run scripts/mechanical.py release --project DIR` | 0 (release_id b11-mech-fit-a-r1) |

All fourteen results pass: C01, C02, C02d, C03, C04, C05, C06, C07, C08, C09, C10, C11, C12, and the closed hole set.

Output hashes (SHA-256, then file name; the last line is the release record):

```
c4d0ad1b04743f111455992260f188172fcbfbe952febe841430a9e0f6052d16  board.step
7f78d95024454e3e64793cc114c04e4c97c867e04bff04c0592230df1f066fcd  outline.dxf
3fc41a56fbc1c42bbbcca618d908a5a8fa64c4d9323f0fe6a981e92de4936aaf  board.drl
42efb59e7c9ba0aa0b7afdb9257dd1bc96109b1863e3382068ce68fcbfd9329f  fit-assembly.step
16e6c1864f494e11206008e76b56f892e9077dd643fc71cd54190e1d837124fe  mech-release.json
```

Release record SHA-256 `6ac66633ef82b6ac…` (record_sha256). The drill file holds both plated and non-plated hits, so its one role is `drill_pth`.

## Measured negatives (through the real export)

| Case | Export | Fit | Release | Named failure |
|---|---|---|---|---|
| extra hole at (125,125) | 0 | 1 | 1 | C02d count 4 vs 3; C02 count 4 vs 3; C04 4 hits vs 3; closed hole set |
| H1 made plated | 0 | 1 | 1 | C04 H1 plated flag |
| B1 height 5.0 mm | 0 | 1 | 1 | C08 B1 over bottom_mm by 1.0 |
| blocker U9 in the CN1 insertion box | 0 | 1 | 1 | C07 intersects U9 (C09 also: outside the outline) |
| CN1 frame rotated 180 degrees | 0 | 1 | 1 | C06 CN1 position or rotation differs |
| B1 evidence unconfirmed | 0 | 1 | 1 | C10 unconfirmed |
| wrong pinned image ID | 2 | - | - | runtime.image_mismatch (exit 2 at export) |
| board changed after export | 0 | 1 | 2 | stale.input board.kicad_pcb (fit exit 1) |
| STEP changed after export | 0 | 1 | 2 | export.altered board.step (fit exit 1) |

The release refuses when the report is not a complete pass (exit 1). It refuses when the report is missing (exit 2). Full results: `negatives/negatives.json` and `negatives/<name>/report.json`.

## Defects the runs found and fixed

1. The Excellon reader expected the plating on the tool line. KiCad writes it on the AperFunction comment above the tool. Fixed. The real drill file is a test fixture.
2. Connector proxies took their angle and position from the interface frame under test, so a rotated frame passed C06. Fixed: the proxy uses the source record through the accepted transform.
3. C09 treated corners on the mating edge as outside the outline. Fixed: a boundary point counts as inside, and only the declared mating edge is exempt.
4. C07 needed CadQuery shapes, not measured dictionaries. Fixed.
5. The CLI lacked CadQuery in its PEP 723 header. Fixed.
6. The first blocker mutant sat outside the insertion box, so C07 correctly passed it. The mutant was moved inside the box and re-run.

## Limits

- An inch DXF or extra pad thickness cannot be chosen through the command. The settings check refuses those switches. The real exporter was not run with them.
- The release record has one drill role. The combined drill file uses `drill_pth`.
- The C09 mating-edge exemption and the proxy connector body length are implementation rules. They are not reviewed.
- A slot or oval is not read as a hole and is not refused. The `excluded_through_holes` reason is not checked.
