# B9/B10 remaining execution combined agreement: Pi

Date: 2026-11-15. Author: pi-pcba-dev.

Subject: `docs/reviews/pcba/b9-b10-remaining-execution-claude.md`, SHA-256
`31d9baf3241d62ff3b21b95ba7b1b5f618b2183e23fb3fd425af327aa528d998`.

I agree to the revised note. Both root requirements are covered. Nothing is implemented.

## 1. Functional alternate evidence

Requirement met.

- `components/alternate-approvals.yaml` is a skill-owned record, bound as a `parts` input.
  The accepted role and the components confinement are preserved.
- The schema is skill-owned `cad-skills/alternate-approval` 1.0. No shared schema changes.
- Each entry binds the `reference`, the `variant`, the primary path and hash, the alternate
  name, path and hash, the application evidence, the approver and the date.
- The application evidence holds a source, a retrieval date and a statement of the circuit
  check. Equal ratings and a present URL are explicitly insufficient.
- A stale hash, reference or variant refuses the alternate (`alternate.approval_stale`). An
  alternate without an approval refuses the run (`alternate.unapproved`).

## 2. Final staged comparison

Requirement met.

- Step 6a compares the staging tree with the validated set immediately before the rename.
- It refuses an extra file, a missing file, a hash difference, a count difference, a changed
  manifest and a link, each with one named finding.
- It works with step 6 input freshness. The package comparison is not replaced by input
  freshness, so the work does not repeat B7.

## 3. Preserved

- The accepted paths and roles are unchanged.
- The alternate value stays the alternate name, and the part path stays in `part_path`.
- Each package stays at `out/pcba/packages/<package-id>/` with `package.exists` and prior
  packages preserved.

## 4. Non-blocking clarification

State the approval entry key as the reference, the variant and the alternate name. Refuse a
duplicate or conflicting entry with one named finding. This makes the join deterministic.

## 5. Limits

Planning only. No product file changed. Alternates, placement, Sierra artifacts and B10
publication remain outside the accepted neutral batch.
