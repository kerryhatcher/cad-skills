# Frozen B1 implementation review: Codex

Date: 2026-11-13.

**Decision: blocking corrections**

I do not accept this B1 revision. Three concrete findings remain below. They concern the agreed B1 contract only.

I first ran `sha256sum -c docs/reviews/b1-files.sha256`. All 17 entries passed. I read the implementation record, both design reports, the corrected proposal, code, schemas, fixtures, and tests.

**C1: exact string boundaries fail**

Locations: `contracts/validate.py:258`, `contracts/validate.py:319`, and hash patterns in the board and supplier-profile schemas.

The version parser uses `match` with `$`. It accepts a final newline as the end boundary. A valid board with `schema_version` set to the JSON string `"1.0\n"` gives exit 3. Its finding is `tool.validator_failure`, with `KeyError: '1.0\\n'`. The agreed result is exit 1 with `schema.version_malformed`.

The same boundary error affects hash fields. Set the board's `supplier.profile_sha256` to 64 lowercase `a` characters plus a newline. The board passes with exit 0 and no findings. That value is not a 64-character SHA-256 string.

Use a full-string match for versions. Add exact string-length constraints to hashes, or use an equivalent strict pattern. Examine other fields that use `$` for exact boundaries.

Add regression cases for the version newline and the hash newline. Preserve the exact field location in each finding.

**C2: malformed YAML scalars become tool failures**

Location: `contracts/validate.py:197`.

The constructor catches `yaml.YAMLError` only. Accepted scalar tags can raise other exceptions when their values are invalid.

| Input | Measured result |
|---|---|
| `a: !!int bad` | Exit 3, `tool.validator_failure`, `ValueError` |
| `a: !!float bad` | Exit 3, `tool.validator_failure`, `ValueError` |
| `a: !!bool maybe` | Exit 3, `tool.validator_failure`, `KeyError` |

These inputs are malformed records. They are not validator failures. Return exit 1 and a record finding, such as `file.parse_error`.

Handle these exceptions at the scalar-construction boundary. Do not convert all unexpected validator exceptions to record errors. Add tests for all three inputs through the CLI. Include an independent valid input to prove continued processing.

**C3: the number type checker overflows on an integer**

Location: `contracts/validate.py:249`.

The number checker calls `math.isfinite` on integers. A valid board with `mechanical.width_mm` set to `10**400` gives exit 3. The finding is `tool.validator_failure`, with `OverflowError: int too large to convert to float`.

The JSON parser accepts this integer. The agreed number type includes integers and finite floats. No B1 schema sets an upper bound on this field.

Accept non-boolean integers without float conversion. Apply the finiteness test to floats. Keep the agreed `TypeChecker` extension. Do not add another schema interpreter or arbitrary physical bounds.

Add a direct type-checker test and a record test with this integer. The unbounded numeric field must pass. Existing non-finite and boolean cases must still fail.

**Tests and coverage**

I ran `uv run tests/test_pcb_tools.py`. All 24 test functions passed.

I ran independent adversarial checks through `uv run --with jsonschema==4.26.0 --with pyyaml==6.0.3 python -`. The checks imported the frozen validator and used temporary records. They reproduced all cases above through `build_report`.

The supplied suite covers the principal agreed rules: duplicate keys, aliases, explicit timestamps, finite values, exact quantities, declared schema versions, fixed hash bytes, exit precedence, and deterministic JSON reports. The three findings identify gaps in otherwise useful coverage.

I did not repeat the mechanical suites. B1 does not change their implementations. Claude reports their successful runs. I did not run KiCad or review later-batch behavior.

The STE lint tools did not run in this review. This report does not establish full STE compliance of the implementation.

**Reviewed hashes**

The hash manifest itself has SHA-256 `04a8ef4f4a05f4adf1303c6d33eaa23683c49305f2d1c8128499e9490d179b31`.

Additional reviewed records:

```text
5ae60100a82b256bca4d35abf52dcd69646850f287ffa842b09264dbe5bea3ab  docs/reviews/b1-implementation-claude.md
f12950018251beb5bcd51d5915fbebddee7dd5a199a26d1e686b9afb79a6f821  docs/reviews/b1-design-codex.md
9af63496da79f4db5ab9759b75408e57316a97086a54eee8098e27817ab080da  docs/reviews/b1-design-pi.md
```

Frozen manifest entries:

```text
cff2b7454554dfe8886f30c46b4646034842f0204f20fa09b2c4128ef730912e  .github/workflows/test.yml
fb9ae245c827aa88162e0c4a7bcf4b336a06f46c45fcf4ce9f97a536e3a08f6f  AGENTS.md
95f6528c941a54010aca2e36fdf7e80675f14804221f213b84b44c9c5bd493ad  README.md
bf27f15bcecca96a57779f36574bef7070ced560767e24a57b6901a44758e77d  ste-glossary.yaml
8b4fc7fc4d915fb4c9d57e67901a2d7de060c568cdd8972c930c73736d219304  contracts/README.md
dec8456da0953187ffdfd1b423f435920c1aa1fa28ee6718b558a19914deb4da  contracts/validate.py
0569f758f83b0e3f3e1652e40eea8e373780993b1f65ecaeaef902a88aab0121  contracts/schemas/registry.json
812c58cc52f5c43d50524eb71f80abd31dbf5e6298c5ecd88c5cd58af5b940c9  contracts/schemas/board.schema.json
6db486543952c62e8bd8f732696db1229fec7b1a8943610dbc21c9234d2941e0  contracts/schemas/part.schema.json
ceaf2e7d61c538a4e0cc8e859276c72f540dbc15c627052ec017e3a285eef988  contracts/schemas/supplier-profile.schema.json
53755cd7d4f79e604329b1e8369bce34fa4f9d820b6002bff3ff9e34b9755901  contracts/schemas/variants.schema.json
fdd057e5e6cfe987cdb83f3a476e919ccb1f5dafca48b5e468167e2d920be163  tests/test_pcb_tools.py
91b45de6c27e9bf7aa1b374804fda06759fa0c9f8efd2b4cb74e372ee9aba164  tests/fixtures/pcb/board.yaml
d0ed30f2a583cd50d280db68b2cc0d24dd98f0f8e6749167a2feb88b25ccd0a2  tests/fixtures/pcb/part.yaml
e6054d96ac64aeb17c2ed538e3b7883b15061d4a18046c60adeec461ade08c9c  tests/fixtures/pcb/supplier-profile.yaml
3ee364f38d83f1a9a8671d719e003474c5da170096c2ca4c72d8b03a9f895ac5  tests/fixtures/pcb/variants.yaml
6b1c8dd331ea3d365e0188322e6d76937e002c6a496c006e09b3667d903aa729  docs/reviews/implementation-proposal-claude.md
```

Correct C1–C3 and supply the regression results and replacement hashes. I will re-review the affected files. This review changes no implementation files and requests no commit.

**Agreement on the B1 repair scope**

I agree with the root's repair choices after review of Pi P1–P3 and updated plan section 4.

- Correct C1–C3 with their regression tests.
- Validate the complete input tree before canonical hashing. Reject non-string keys and non-JSON types without silent conversion.
- Preserve the fixed hash bytes for valid records. Keep the root-only hash-field exclusion.
- Give each supplier limit a mandatory `scope`: `fabrication`, `assembly`, or `margin`. Keep enforcement location separate.
- Keep `variants.yaml` as the sole owner of assembly variant and DNP data. Do not duplicate these fields in part records.
- Test selected-variant existence in B2. Test component-instance and reference coverage in B9.

Include Pi's focused tests for invalid hash inputs and missing, unknown, and valid limit scopes. Brief STE and document corrections remain in scope. No other B1 feature is necessary.

This agreement concerns repair choices only. B1 acceptance remains pending the replacement hashes, code review, and regression results. I will re-review the final frozen replacement when it is ready.
