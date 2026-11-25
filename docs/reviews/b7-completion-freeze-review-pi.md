# Complete B7/B8 freeze review (pi-skill-dev)

Date: 2026-11-15 UTC. Reviewer: pi-skill-dev, pane `w1P:p6`.
Scope: `docs/reviews/b7-completion-freeze-root.md` and
`docs/reviews/b7-completion-freeze-root.sha256`.
I changed no product file. I reran no accepted geometry or publication decision.
I used the existing local Podman service through
`CONTAINER_HOST=unix:///run/user/1000/podman/podman.sock`.
I ran no `podman system migrate` and no service restart. The model stays unchanged.

## Frozen identity and before/after hashes

- Record: `d299cc5517fffd1ad99bbc215d31d999b5ea813f8b1822244bcf87c21f423a30`.
- Manifest: `3f5904c28ba21ee8f09f4c480ff02a439741d59cceacff300ca9925ed0e4a411`.
- Entries: 239. All unique.
- Before review: `sha256sum -c` reports 239 of 239 `OK`.
- After review: `sha256sum -c` reports 239 of 239 `OK`.
- The record hash, the manifest hash and all entry hashes are the same before and after.

## Reproduced results

| Suite | Reported | Reproduced |
|---|---:|---:|
| Outline stroke independence | 12 | 12 |
| Vias | 16 | 16 |
| Corners | 16 | 16 |
| Board dimensions | 18 | 18 |
| Small gaps | 6 | 6 |
| Rule boundaries | 18 | 18 |
| Manual silk | 9 | 9 |
| Large drills | 6 | 6 |
| Required evidence | 2 | 2 |
| Acceptance cases | 35 | 35 |
| Package geometry | 101 | 101 |
| Workflow after centerline | 132 | 132 |
| Standalone | 7 commands + validator | 7 commands + validator |

The standalone run reports `repository_hidden: true`, `validator_exit: 0` and
`package_status: qualified`. The installed validator loads product modules from the installed skill.
I did not rerun source retrieval (56) or skill packages (8). Those suites are unchanged and accepted.
All suite logs are in `/tmp/pi-<suite>.log`.

## Zero-stroke concern

The concern is closed with explicit pinned-image proof.

`tests/test_pcb_fab_outline.py` measures a 406.4 by 6.35 mm Edge.Cuts shape for a board graphic
and for a footprint graphic, at stroke widths 0, 0.05 and 1.0 mm. Each case gives the exact
centerline bounds `{"x": 0.0, "y": 0.0, "width": 406.4, "height": 6.35}`. The worker gets this
result with `drawing.SetWidth(0)` in memory. Each case also proves that the source bytes stay
unchanged. The image is `b2731833711a1df0d955038c10582f1893d27743df5d9fcd52e107cb35892a5f`
(`kicad-cli` 10.0.5). All 12 checks pass.

## Examined changes

- **Via route.** `via_inventory.py` measures spans from captured bytes with pcbnew. It classifies
  through, blind and buried spans. `measure_vias` binds the worker bytes, the image, the board
  bytes and the board record. A blind or buried span or a declared prohibited process gives a
  failed precondition with exit 1 and no success binding. A missing or `unconfirmed` declaration
  stays pending. An unknown declaration gives exit 2. A measured zero count gives pass. The B6
  worker stays unchanged.
- **Corner facts.** The five profiles record the published cutter diameters as process facts
  (0.068 in outline, 0.040 in cutout) with the source URL and the retained page hash. The test
  proves the exact derived radii: 863600 nm outline and 508000 nm cutout. It gives fail at
  0.033 and 0.019 in, and pass at 0.034, 0.035, 0.020 and 0.021 in. Convex, open and polygon
  fixtures refuse with exit 2. An incorrect source hash refuses.
- **Drawing comparison.** `drawing_problem` rebuilds the facts from the captured inventory, board
  and profile. It compares the facts bytes and the PDF bytes. A substituted PDF or changed facts
  refuses before publication. The acceptance suite proves exit 1 and no destination.
- **Dimension correction.** The B7 derivative zeroes the Edge.Cuts widths in memory, then calls
  `GetBoardEdgesBoundingBox()`. It includes board and footprint graphics. It does not save the
  board. The width at 406.4 mm and the minimum edge at 6.35 mm give the expected result.
- **Acceptance gaps and standalone.** The acceptance suite covers rows 22, 23, 24, 26, 31, 32,
  36, 41, 44 and 45. The standalone trial runs seven installed commands and the full validator
  with the repository hidden and offline retrieval.

## Findings

No blocking finding. The frozen bytes match the record and the manifest.
The new route keeps the accepted exit precedence. The B6 worker, the slot algorithm, the mask
algorithm and the publication rules stay unchanged.

## Scope limits

- The standalone trial does not measure a physical result and makes no current supplier claim.
- The local container service keeps host access. The trial hides the repository from the Python
  process only.
- The native Podman host-state defect remains outside this review.
- The large-drill boards and some dimension boards fail unrelated design conditions. Their
  records claim only the named supplier condition.
- The A2 fixture refresh follows acceptance and is outside this freeze.

## Verdict

Accept the complete B7/B8 freeze. The before/after hashes are identical.
