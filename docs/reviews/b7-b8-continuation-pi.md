# Pi continuation report: B7/B8

Date: 2026-11-14.

Role: reports-only reviewer. No product edit. No broad test. Use the existing image and temporary copies. All Python with `uv`. Measure hashes before and after. Keep the current model and harness.

## Accepted batches

| Batch | State | Evidence |
|---|---|---|
| B1 | Accepted | `b1-final-files.sha256`, `b1-final-review-pi.md` |
| B2 to B4 | Accepted | `b234-final-files.sha256`, `b234-final-review-pi.md` |
| B5 | Accepted with explicit limits | `b5-correction-files-v2.sha256` `00297fd7...c8c188`, `b5-acceptance-root.md` |
| B6 | Accepted within limits | `b6-replacement-files.sha256` `f93454c5...caca39`, `b6-native-repair-record.md` `2e8f4e20...f3481` |

## Current B7/B8 interface (r8 plus agreed errata)

| Item | SHA-256 |
|---|---|
| `b7-b8-proposal-claude-r8.md` | `8ff1da0d452902edfc8bc93129ce26e27d861340fb5a5c75deba813be83e09e5` |
| `b7-prereq-evidence-r8.sha256` (195 entries, path base `docs/reviews`) | `2ef5503dd2fc86c2e300536e3c75b74a9c88e8e6031de87d819fb524827773d9` |
| `b7-prereq-trials-claude.md` | `183f2c98ebe897bcb9b551950788405d253be99bd89fb9e0ee93c387a5d13047` |
| `b7-r8-errata-root.md` | `08eecbedee4be4e63326803b44e9202d2a163f4d9f03045b5dbf33a7e27584ad` |
| `b7-b8-design-pi.md` (my verdict, section 18) | `09f60628f4cd789172c849415a974446fc8b559ae70b892a1bd4aa8f821acec2` |

r8 plus the agreed errata is the implementation interface. Key decisions: scope `fabrication`, integer copper layers 2/2/2/4/6, order multiple 3, source nominal values beside the metric label, the 250 mil note is a process note, and the slot tolerance is 0.000501 mm (accepted) with the exact boundary test. Unknown macros, overlapping clusters and unsupported constructs are product refusal tests, not a prerequisite loop.

B9/B10 source-addendum decision: `b9-b10-preparation-pi.md` `7b1838b20e1e103cf1874a419a556f914766d191d0fb3f2682d3c68d6e15b5e3`.

## Pending review

Wait for Claude's corrected and frozen B7/B8 implementation checkpoint. Then review it and write a report. Do not review product code before the freeze. The B7/B8 checkpoint review has priority over other work. The B6 acceptance is closed (`b6-replacement-review-pi.md` `df0f3714...`). No B6 test repeat.

## Herdr channel

- Recipient: `w1P:p3`, agent label `skill-dev-lead`.
- The installed `herdr` 0.9.5 speaks protocol 22. The running server speaks protocol 19. The normal client fails with `protocol_mismatch`.
- Use the running server binary: `/proc/482044/exe agent prompt w1P:p3 "<message>"`. It speaks protocol 19. Do not restart the server. Do not stop the panes.
- Start each message with `[YYYY-MM-DD - HH:MM:SS UTC] To: skill-dev-lead; From: pi-skill-dev - `.

## Reporting rules

- STE text. Reports only. No implementation edit.
- Focused probes only, with the existing image and temporary copies. No pull, no broad suite, no GUI repeat.
- Record the tested hashes and the report hash. State limits.
