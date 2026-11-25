# Source retrieval alias freeze review (codex-skill-dev)

Date: 2026-11-15 UTC. Scope: the narrow alias freeze and current r8 coverage map. No product file changed. No suite ran during this review.

## Hash boundary

The requested freeze record hash is `31f8480fe08195424ccb1f2987ac45d1e72bbd0742303359ea1fd83698afc5aa`.

| File | Before hash | After hash |
|---|---|---|
| `skills/pcb-fab-package/scripts/fetch_sources.py` | `35e21d37dc82e8367a167411b887843f426e0a2f5d1b4708cfe4f5dfad63ab01` | `35e21d37dc82e8367a167411b887843f426e0a2f5d1b4708cfe4f5dfad63ab01` |
| `tests/test_source_retrieval.py` | `1d61a5a2deaa5300087c34e4e5c4be83addfa3a0bc0841d2e74ff9db6f742cd7` | `1d61a5a2deaa5300087c34e4e5c4be83addfa3a0bc0841d2e74ff9db6f742cd7` |

The before and after hashes match the freeze manifest. The review did not change these files.

## Verdict

Accepted. `validate` checks each destination before fetch in write and check-only modes. It refuses resolved aliases of the manifest and protected profiles, destinations under `supplier/profiles`, and hard links to protected files. The check follows the existing link and binding checks. Tests 49 to 56 cover the released cases. The retained probe note correctly explains that the Codex probe writes to its own manifest path before the command runs.

The accepted link messages and outcome and exit-precedence behavior remain unchanged. Pi noted that test 50 exits through the `..` shape check before the alias check. This does not invalidate the test result or block the freeze. Pi also noted that a directory destination fails later with exit 3. This does not replace a protected file and does not block the freeze.

## Current r8 coverage findings

I compared the inventory with the cited retained logs and the corrected review by Pi, SHA-256 `a07743c6df376ed455f32362aeeb9d5b25cbbe44e3b70252710bcb09ef9fc5ec`. The corrected remaining cases are:

- Row 3: unit-on-text profile refusal. A maximum-kind test is optional.
- Row 6: `min_space` boundary tests and `min_annular_ring` positive and boundary tests.
- Rows 7a and 7b: board width and height limit runs.
- Row 8: export comparison at 20.0 and 20.1 mil.
- Rows 13 and 13c: mask clear-polarity and stroke tests; refusal for a different macro name.
- Rows 16 and 22: package with `fab.supplier_rules` removed by name; missing schematic PDF or drawing.
- Rows 23 and 24: four or six layer internal-copper tests. Row 23 tests same-net copper at 0 mil and pass. Row 24 tests unconnected copper at 9.9, 10, and 10.1 mil and expects fail, pass, pass.
- Rows 25 and 26: edge keepout at 14.9, 15, and 15.1 mil; short-text silk at 2.9, 3, and 3.1 mil. Both need judge and board tests.
- Row 28: outline and cutout corner radii.
- Row 29: supplier via-construction checks for blind, buried, and filled-and-plated via-in-pad. Failure exits 1. Keep the B6 worker refusal at exit 2 separate.
- Row 31: process-note check that a 250 mil drill passes and no maximum applies.
- Row 32: workflow tests for quantities 1, 2, 3, and 4.
- Row 36: changed stored page file hash through a separate path.
- Row 41: positive B7 test that the derivative reports an oval or obround drilled pad as a slot. The B6 worker refusal at exit 2 is separate.
- Row 44: refusal when a layer PDF fills the drawing slot.
- Row 45: test that drawing facts come from pcbnew or the S-expression parser, not a regex extractor. The worker uses pcbnew, which is an accepted source.
- Standalone: install the skill outside the repository and run its suite.

Row 14 is covered by mask tests m39, m40, m41, and m39merge. Row 6 has positive `min_space` coverage. The maximum-kind path for row 3 shares the tested branch. The inventory section 2 status is stale because the alias verdict is recorded and accepted. I did not rerun any log or suite.

Manifest normalization remains a separate review item. This verdict does not accept or install the normalized manifest.
