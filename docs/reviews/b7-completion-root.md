# B7 and B8 completion

Date: 2026-11-15 UTC. Author: skill-dev-lead.

This record supersedes the partial status in `b7-completion-partial-claude.md`.
The earlier records retain their historical bytes and limits.
The accepted geometry algorithms, B6 worker and publication rules remain closed.
The lead implemented the remaining work while the author held at the provider limit.
No model changed. No provider evaluation ran.

## Product changes

The package compares its fabrication drawing with the deterministic PDF from captured drawing facts.
The facts must agree with the captured inventory, board and supplier profile.
A substituted layer PDF refuses before publication.

The supplier measures via spans with an owned pcbnew worker in the locked local image.
The mandatory row is `service.via_construction_prohibited` throughout the profile, evidence and result.
A blind or buried span gives a failed supplier precondition with exit 1.
That precondition cannot qualify a package. The B6 unsupported-geometry exit remains 2.
The requested process comes from `board.yaml` at `extensions.fabrication.via_process`.
A declared prohibited process fails. Missing or unconfirmed declarations remain pending when the board contains vias.
An unknown declaration refuses with exit 2. A zero count establishes the no-via case.
The declaration does not establish physical construction.

The five profiles now record the published cutter diameters under process facts.
The inch values are 0.068 for the outline and 0.040 for cutouts.
Each fact binds its source URL and retained page hash.
The comparison derives the tool radius as half the diameter. It does not add supplier minima to `limits`.
An owned pcbnew worker measures supported concave corners and closed contours.
The guide states the geometry subset and topology bounds.
The supplier reports derived tool compatibility, not general manufacturing approval.
Both new reports bind captured board bytes, worker bytes and the measured image identity.
The supplier output binding and the package include both reports.

The dimension tests exposed stroke-width inflation in the B7 inventory.
The derivative now sets Edge.Cuts widths to zero in memory before the bounding-box call.
It includes board graphics and footprint graphics and never saves the source.
Twelve pinned-image checks prove exact 406.4 by 6.35 mm bounds at three stroke widths.
The drawing facts use the corrected inventory.
The B6 worker and hole geometry remain unchanged.

## Acceptance cases

| Remaining row | Evidence |
|---|---|
| 3 | `test_pcb_fab_small_gaps.py` refuses a unit on a text limit. |
| 6 | `test_pcb_fab_rule_boundaries.py` measures spacing and annular-ring boundaries with generated rules. |
| 7a, 7b | `test_pcb_fab_dimensions.py` measures width, height and minimum edge through design and supplier commands. |
| 8 | The small-gap suite compares exported slots at 20.0 and 20.1 mil. |
| 13, 13c | The small-gap suite refuses clear polarity, strokes and another macro name. |
| 16 | `test_pcb_fab_required_evidence.py` removes `fab.supplier_rules` from a generated package. The full validator refuses it. |
| 22 | The acceptance suite refuses a missing schematic PDF and a missing fabrication drawing. |
| 23, 24 | The accepted 40-file internal-copper record retains the same-net exception and the 9.9, 10 and 10.1 mil boundaries. |
| 25 | The rule suite measures edge clearance at 14.9, 15 and 15.1 mil. |
| 26 | `test_pcb_fab_manual_silk.py` measures three boards and supplies bound manual evidence at 2.9, 3 and 3.1 mil. |
| 28 | `test_pcb_fab_corners.py` measures the six radius boundaries and the unsupported cases. |
| 29 | `test_pcb_fab_vias.py` exercises the declarations, spans, zero count and package refusal. |
| 31 | `test_pcb_fab_large_drills.py` measures 250 and 251 mil drills through the product commands. Neither fails an invented maximum. |
| 32 | The acceptance suite exercises quantities 1, 2, 3 and 4 through the supplier command. |
| 36 | The acceptance suite refuses a changed stored page through source review. |
| 41 | The acceptance suite measures the B6 refusal and the positive B7 slot inventory. |
| 44 | The acceptance suite refuses changed facts and a substituted layer PDF. |
| 45 | The acceptance suite compares drawing facts with the captured pcbnew inventory and board hash. |
| Standalone | `test_pcb_fab_standalone.py` runs seven installed commands and the full installed validator with the repository hidden. |

The silk trial exercises manual evidence. It does not add automatic silk inspection.
The separate setup guidance retains the supplier 5 mil minimum.
The large-drill boards and some dimension boards fail unrelated design conditions.
Their records claim only the named supplier condition, not an overall board pass.

## Tests and limits

| Suite | Passed |
|---|---:|
| Small gaps | 6 |
| Rule boundaries | 18 |
| Board dimensions | 18 |
| Outline stroke independence | 12 |
| Manual silk | 9 |
| Corners | 16 |
| Vias | 16 |
| Large drills | 6 |
| Required evidence | 2 |
| Acceptance cases | 35 |
| Package geometry | 101 |
| Source retrieval | 56 |
| Skill packages | 8 |

The evidence directory is `docs/reviews/b7-completion-evidence`.
The workflow result after the centerline correction appears in the final freeze addendum.
The retained boundary fixtures have independent geometric formulas.
The first dimension run remains as failure evidence. The corrected run passes all 18 checks.

The standalone trial restores five retained pages through an offline transport.
It then runs profile, judge, design, supplier, review-source, review-gate and package. All return exit 0.
The full installed validator returns exit 0. All loaded product modules come from the installed skill.
Its qualified test package uses synthetic manual evidence and offline source observations.
This trial does not establish physical results or a current supplier review.
The Python process cannot read the repository. The local container service retains host access.
The native Podman route reported an internal-state defect. The existing local service supplied the same locked image.
`b7-standalone-runtime-root.md` records the route and its limits.
The lead did not stop unrelated containers or change their metadata.

## Integration boundary

The source manifest remains `fd415dc58ab60455c022112105905ede674ce389ba26b025ead80651dbee488f`.
The page bytes remain unchanged. The retrieval implementation remains at its accepted alias correction.
The process facts change the profile content hashes. Projects must bind the new profile hash before use.
The release A2 fixture needs a separate refresh after acceptance because its profile and declaration precede these changes.
The historical A2 fixture stays unchanged until that release.
No complete integration or live-provider claim follows from this batch.
