# Review of the B9/B10 helper list

Date: 2026-11-15 UTC.

Reviewed file: `docs/reviews/b9-b10-interface-claude.md`.

The latest revision resolves the two acceptance conflicts from my prior review. AC-10 distinguishes the draft XY file from the later `unqualified` manifest status. AC-02 keeps the excluded mechanical reference in neutral data only. R1 and R2 are closed.

## Required corrections

1. Correct the registry source path. The repository path is `contracts/schemas/registry.json`, not `contracts/registry.json`.
2. List every schema file copied for the validator. The current list names board, variants, part, supplier profile, manifest, and evidence schemas. The registry also lists board-interface, export-settings, toolchain-lock, and waivers schemas. The validator loads each schema listed in the registry.
3. Complete the bound-input table. The copied validator requires the schematic, export settings, toolchain lock, and board interface inputs. Name their project paths and manifest roles. Also name any required waiver input when the package uses waivers.

## Acceptance recommendation

Accept after these paths and roles are explicit. Record each copied file's source path and SHA-256 when the author copies it. No product file or shared contract changed in this review.
