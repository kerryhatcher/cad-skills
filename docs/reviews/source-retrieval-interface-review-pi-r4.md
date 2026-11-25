# Source retrieval interface review, revision 4 (pi-skill-dev)

Date: 2026-11-15 UTC. Scope: the revised proposal
`docs/reviews/proposals/source-retrieval-interface-claude.md`,
SHA-256 `17683ffd50a7d017e9fc1acac04e2ddfe5b0f94d75cb42da1b244839bf94fc44`.
I changed no product file. I ran no broad suite. This is a review of a proposal.

## Confirmed corrections

All r3 findings are addressed:

- When `profile_binding` is not `null`, `path` must equal it. The destination is
  `DIR/<profile_binding>`. A differing `path` is refused with exit 2 before any fetch.
  Test 38 covers the refusal. Test 39 covers the valid write.
- The overall result states are defined in one place. The `Multi-entry result` section no
  longer keeps a second list.
- Test 10 names a duplicate resolved destination.

The proposal now covers the exit precedence, the write failure before and after the replace,
the result states, the non-2xx response, the resolved duplicate check, the `profile_binding`
rule, the real-date check and the complete offline test set. The manifest schema, the field
types and the validation order are consistent.

## Minor wording

- `Manifest and roots` says `profile_binding is optional`. The schema section says the key is
  required and the value may be `null`. Make the wording agree. Write: the key is required,
  and its value may be `null`.
- The `exclude-local-evidence` text says `Their bytes are captured once as evidence`. The
  command does not fetch them, so the command does not capture them. Name the separate step
  that captures the bytes. The outcome bullet already says the command does not read, fetch
  or verify them.

## Verdict

The proposal is accepted. The two wording items above are minor and can be corrected in the
same pass as the implementation or the freeze record. The design meets the assigned scope:
one command, the manifest root as the destination, no accepted changed bytes, no profile
revision, no license gate, a strict parse, confinement, atomic writes, an explicit
multi-entry outcome, and offline tests.

No product edit. I hold for the frozen implementation.