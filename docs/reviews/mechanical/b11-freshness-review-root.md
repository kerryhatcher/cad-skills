# B11 residual freshness findings

Date: 2026-11-15 UTC. Author: skill-dev-lead.

I ran `uv run docs/reviews/mechanical/b11-freshness-probe-root.py`. Exit: 0.
The probe used a temporary fixture and the existing local image. It changed no product file.
The positive fit gave geometry pass and fit pass.

## Export input drift

The probe appended a newline to the source board after the drill command returned.
The exporter returned success and wrote export.json without a final input comparison.

- Recorded board hash: `37105cf50e2bb0c997f7b9f6a02affef2f101a6b0684a4024d5a78541f8e20ba`.
- Current board hash: `c0eefebadbd03641de8fa20f251b1733441b6729759001e4249ce260244d7c2d`.

The exported bytes came from the captured board. The defect is missed source drift before publication.
Compare all consumed inputs with the captured hashes before the first export write.

## Release report and fit drift

The probe appended a newline to the fit assembly and report during the second capture call in release.
The release returned success and wrote mech-release.json.
Its final loop compares only report.outputs. It omits the report and fit assembly that the release also binds.

| Output | Recorded hash | Current hash |
|---|---|---|
| fit-assembly.step | bfcc7f9a94f69ac66e75ac3cd813ad4f38785a859614d90ff54f0734020155ef | 79782912150283f7401c53c20a2440e50c3be5fa2f4f88ed94e314f4e588f51d |
| report.json | 6ba0f8af6c70f7a486410af9baece1e70560b9f5ad3ba76ffd4e55069a694f80 | dfb0145be377f81cd5a44780441d997a273bdea9ed02942e76bffd2d54e6c2a7 |

Compare all bound output bytes and byte counts before the release write, including these two outputs.
Keep the captured bytes as the source for decisions.
Add focused controlled-change regressions. No broad suite is necessary for this finding.

These are controlled in-process changes. The probe makes no claim about operating-system race timing.
The current product set stays frozen until the combined review is complete.
