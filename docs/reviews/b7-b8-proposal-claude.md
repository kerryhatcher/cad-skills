# B7/B8 compact proposal (claude-skill-dev)

Date: 2026-11-14. Status: proposal only. No implementation starts before B6 acceptance and B7/B8 design agreement. B6 revision 3 stays frozen (`b6-final-files.sha256`).

Basis: `b7-rule-research-root.md`, `b7-rule-research-codex.md`, `b7-rule-research-pi.md`, `b7-b8-preparation-codex.md` and `b7-b8-preparation-pi.md`. The five OSH Park profiles are the scope.

## B7: supplier rules as staged, checked artifacts

1. Two results. The project DRC result stays as it is. The supplier-rule result is separate. Neither replaces the other.
2. Disposable copy. The supplier run works on a staged copy. The source PCB bytes, the source rule file and the source severity settings are not changed. Their hashes are checked before and after the run.
3. Staged artifacts. The generated rule file and the staged severity mapping are explicit files. The result records their hashes, the profile hash, the source PCB hash and the command.
4. No refill during inspection. A design that needs a refill is refilled and checked first. The supplier run then inspects that new source revision.
5. Rule selectors. The plated-drill clearance to internal copper uses `hole_clearance` (different-net copper only; same-net connections stay valid). `physical_hole_clearance` is not used where a same-net connection must pass. The `inner` layer selector covers internal copper.
6. Slot and oval holes. `hole_size` checks the minor dimension against a minimum and the major dimension against a maximum. Slot width and length are tested separately. The 250 mil threshold is not a maximum drill size.
7. Order and severity. Mandatory rules are ordered so that no later matching rule shadows them. A project severity of `ignore` or a source exclusion cannot produce a supplier pass. The source settings stay unchanged.
8. Exceptions. A supplier exception is a profile decision backed by supplier evidence. A local DRC waiver never establishes supplier acceptance.
9. Fixed image. The fixed runtime image must execute the generated rules. Documentation alone does not establish support.

Necessary tests (B7): a weaker matching rule after a mandatory rule; project `ignore` severity; an applicable source exclusion; a same-net connection at 0 mil that passes; an unconnected internal feature at 9.9 mil that fails and at 10 mil that passes; slot width and length tested separately; unchanged source PCB bytes and recorded staged-file hashes.

## B8: package qualification from the five profiles

1. Profiles. One profile per service: single-layer (a two-layer process), two-layer, two-layer HHDC, four-layer, six-layer. Each keeps its own URL, evidence hash and retrieval date.
2. Values. Each limit keeps its source value and unit. Lengths convert at exactly 0.0254 mm per mil. Substrate values are kept separate from the finished thickness (the HHDC core is 28 mil; its finished board is 0.8 mm).
3. Evidence freshness. A stored hash identifies retrieved bytes. It is not proof of current terms or order acceptance. A material change blocks qualification until it is resolved. Harmless page changes do not block after review.
4. Rule boundaries. Measurable fabrication rules go to `kicad_dru`. Stackup and net-class choices go to project settings. Outline and slot geometry go to geometric tests. Non-measurable terms go to manual evidence. Lead times are not design rules.
5. Process capability. Mask alignment, plating and finished tolerances are recorded policy with evidence. The CAD board supplies no measured values for them, and no physical measurement is claimed.
6. Internal clearance. The three published mitigation methods stay alternatives. An annular ring on every unconnected layer is not a universal rule.
7. Copper filenames. Prefer the published copper pattern with X2 off. Check the layer content independently. Do not add an untested X2 path only for names.
8. Qualification. The existing manifest and package validator are used. A qualified package lists every applicable output role with passing evidence. Unsupported checks are never reported as pass. Unresolved conditions keep the package unqualified, with a reason.

## Open decisions for the reviewers

- Whether the supplier-rule result is a separate record in the package manifest or a separate file beside it.
- Whether B8 uses the existing `evidence` records for the supplier note, or a new check identifier.

## Limits of this proposal

Paper proposal. No KiCad custom rule was run, and no rule file was tested. The fixed image must execute the rules before any B7 support claim.
