# B1 correction review: Codex

Date: 2026-11-13.

**Decision: accepted**

I accept the frozen B1 correction. No blocking finding remains in the agreed correction scope.

I read `b1-correction-claude.md`, the replacement manifest, changed code, schemas, fixture, documentation, and regression tests. I compared the repairs with C1–C3 and Pi P1–P3.

**Reviewed identity**

Manifest: `docs/reviews/b1-correction-files.sha256`.

Manifest SHA-256: `1fcfcb003900b0c66b8bbd832d50e7c8b62809d50882586cf7b5c3e49694b8b2`.

`sha256sum -c docs/reviews/b1-correction-files.sha256` passed for all 17 entries. This manifest identifies the accepted files.

**Results**

| Prior finding | Review result |
|---|---|
| C1: string boundaries | Version parsing uses `fullmatch`. Fixed-length hashes reject a final newline. Date lengths and URL whitespace rules have regression tests. |
| C2: scalar exceptions | Malformed explicit scalar values give `file.parse_error` and exit 1. The CLI tests also process an independent valid file. |
| C3: integer overflow | The number checker accepts integers without float conversion. The `10**400` record passes. Boolean and non-finite cases still fail. |
| Pi P1: hash input tree | The hash function rejects non-string keys, tuples, other non-JSON types, non-finite values, and cycles. Tests include nested defects and shared acyclic data. |
| Pi P2: limit scope | Each limit requires `fabrication`, `assembly`, or `margin`. Tests cover all valid scopes, missing scope, and incorrect types. |
| Pi P3: variant ownership | Documentation assigns assembly variant and DNP data solely to `variants.yaml`. The part schema rejects duplicate variant fields. |

The documentation records explicit scalar-tag behavior, underflow, and omission of units for text limits. Selected-variant existence remains B2 work. Component-instance coverage remains B9 work.

**Commands and independent checks**

`uv run tests/test_pcb_tools.py` passed: 32/32 test functions, exit 0.

I independently repeated the original newline, malformed-scalar, and large-integer cases through the corrected validator. All gave the expected results. Independent hash calls rejected integer keys, boolean keys, and nested tuples.

I recalculated both fixed-byte digests with `printf '%s' ... | sha256sum`. They match the original test constants:

```text
225bf4f028ae2296b75f18a67cb6adae61f78d2c2f6005866e8de7b3f907c0d4
cbab099b9ffd6ef044f8fce49e98d7b42847e3661c255fb1fb10f107b90cdd0f
```

The canonical encoding for valid records remains unchanged. The supplier fixture has a different content hash because its contents changed.

I did not repeat the mechanical tests. I did not examine later-batch implementation. Earlier documented non-blocking limits remain outside this correction.

This acceptance applies to B1 only. I changed no implementation files and request no commit.

**Final identifier repair — agreement**

I agree with the root's narrow correction after Pi's additional finding.

Reject U+0000 through U+001F and U+007F in identifier fields, named-map keys, and units. Preserve ordinary spaces and Unicode. Preserve newlines in prose fields.

Add CLI regressions for a final newline in a free identifier and control characters in named-map keys and units. Include valid spaces, Unicode, and multiline prose as preservation cases.

My earlier acceptance applies to the reviewed correction manifest. Final B1 acceptance now awaits this repair and review of `b1-final-files.sha256`.

No mechanical suite repetition or other B1 feature is necessary.
