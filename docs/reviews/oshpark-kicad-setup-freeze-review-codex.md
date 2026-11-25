# OSH Park setup document review (codex-skill-dev)

Date: 2026-11-15 UTC. This review covers the frozen setup documentation only. It does not cover the B7 publication correction.

## Freeze

The freeze record `docs/reviews/b7-doc-setup-freeze-claude.md` has SHA-256 `a3fed526c4b05a40baf2ac3a3ddd1e0ae4bdd03b807eb502a0e8f4db19e93cb8`.

All six entries in `docs/reviews/b7-doc-setup-files.sha256` passed before this review. The installed guide hash is `f755a28d19b797c954e2d8f8156cdc981cd6501a3e3831f031b7411b9aad557e`. This review did not change a frozen file.

## Findings

### Blocker: supplier limits become recommendations

The guide labels the two-layer copper-to-hole clearance, hole-to-hole clearance, minimum via diameter, minimum connection width, and silkscreen thickness as recommendations. It then says that the first four values remain recommendations until the repository records a measurement.

The official OSH Park design rules list these values in the Constraints table. The page names minimum via diameter, minimum connection width, and minimum silkscreen thickness as minimums. Its two-layer values are 20 mil, 6 mil, and 5 mil. The page also lists 5 mil for copper-to-hole and hole-to-hole clearance. The local lack of an automated check does not change the supplier's stated value or status. See [OSH Park Design Rule Setup](https://docs.oshpark.com/design-tools/kicad/kicad-design-rules/).

Separate two facts for each row: the supplier's limit or constraint, and the repository's enforcement method. State `not checked by the repository` where applicable. Do not call a supplier minimum a recommendation.

The silkscreen row needs a direct correction. It lists 5 mil as a supplier minimum, but says the profile requires 3 mil by manual evidence. This wording can imply that 3 mil satisfies the supplier minimum. State the 5 mil supplier limit and describe the local 3 mil test separately. Explain that the local test does not demonstrate compliance with the supplier limit.

### Blocker: margin direction claims safety

The guide says that a larger minimum margin is safer and a smaller maximum margin is safer. This broad claim does not account for other design effects. Keep the pass direction, but remove the safety claim. State that a project value must meet the supplier limit. Tell the reader to assess related design effects before selecting a margin.

## Confirmed coverage

The frozen guide has the requested direct links. It distinguishes checked values from manual steps and unmeasured settings. It states the tested Gerber route and the unconfirmed status of native KiCad 10 acceptance. It covers optional tenting, paste ownership, stackup authority, native font embedding, font review, the physical mask web, and the manual Plot On All Layers setting.

The guide correctly states that an explicit layer list does not prove that Plot On All Layers is off. It names the source manifest target as `skills/pcb-fab-package/sources.yaml`. The four-layer and six-layer profiles already exist. No profile or code change is part of this review.

The author log reports `uv run tests/test_skill_packages.py` passed 8 of 8 checks with exit 0. This review did not run a test suite.

## Scope and next action

The setup guide needs a focused text correction for supplier status, repository enforcement, the 3 mil silkscreen statement, and margin wording. Keep the export contract and existing profiles unchanged. This review does not approve the frozen guide for release until these text findings are corrected and reviewed.
