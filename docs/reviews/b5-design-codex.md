# B5 draft design review: Codex

Date: 2026-11-14.

Proposal: `docs/reviews/b5-trial-proposal-claude.md`, revision 2.

Reviewed SHA-256: `7b377597bf229facd99bd22e2b398d425a6f79be129570a363f4873b81e4f5ae`.

**Decision: corrections before design agreement**

The independent native path and explicit U1–U6 result rows improve the trial. Keep them. The corrections below concern executable setup, measured identity, and honest acceptance. They add no framework or later skill feature.

B234 correction and acceptance remain first. B5 must use its corrected validator and package rules.

**B5-1: separate native file-format versions**

Do not use the symbol-library version as the schematic and PCB version. These are separate formats with separate headers. The installed `Device.kicad_sym` header says `20251024`. That observation does not establish a compatible board or schematic version.

Select and record each format version independently. Use installed KiCad output or a documented supported version as evidence. Give the generator its own name. Validate symbol instances, pin positions, and the complete exported connectivity map against explicit expectations. A file-load success alone is insufficient. [Schematic format](https://dev-docs.kicad.org/en/file-formats/sexpr-schematic/), [board format](https://dev-docs.kicad.org/en/file-formats/sexpr-pcb/)

Keep the two-correction limit for this generator experiment. If the generator remains invalid, record the native path as untested. Do not count a generator failure as evidence that native KiCad cannot preserve identity.

**B5-2: make dependency setup executable**

T0a uses an abbreviated digest and passes `skidl==3.0.0` as an input filename. `uv pip compile` takes a requirements file or standard input. The uv image's measured entry point is `/uv`. [uv locking documentation](https://docs.astral.sh/uv/pip/compile/)

Supply a `requirements.in` file that contains the pinned SKiDL requirement. A complete replacement command is:

```bash
podman run --pull=never --rm -v "$TRIAL:/work:Z" \
  ghcr.io/astral-sh/uv@sha256:e85be844203885286c60ffad8a858d48afb6c5a5c237ca0e67f12e74b8f174b1 \
  pip compile /work/requirements.in --python-version 3.13.5 \
  --generate-hashes --no-header -o /work/requirements.lock
```

Define `TRIAL` as the absolute temporary trial-copy path before this command. Record target platform and resolved package versions. Do not relabel the repository.

The system-site-packages option belongs to environment creation. It is not an install option. State these separate Containerfile operations with their exact paths:

```bash
uv venv --python /usr/bin/python3 --system-site-packages /opt/trial-venv
uv pip sync --python /opt/trial-venv/bin/python --require-hashes /opt/trial/requirements.lock
```

The Containerfile must first copy the lock file to that location. Validate this sequence during setup. Record that the environment imports both SKiDL and the system KiCad bindings through `uv`.

Lock resolution alone does not make an offline environment. Install all packages and the necessary system tools during the online build. Then run the same import and command probes with `--network none`.

Record the derived image ID and use it for trial runs. Do not rely solely on a mutable local tag. Keep the base digest and derived identity in fields that the toolchain schema supports. Do not claim that an unused field passed schema validation.

**B5-3: use uv consistently and complete the command record**

T1, T3, and T4 contain direct Python commands. Replace them with the agreed uv execution route. Distinguish the system interpreter from `/opt/trial-venv/bin/python` for SKiDL. For example:

```bash
uv run --no-project --no-config --offline --python /usr/bin/python3 python scripts/make_native.py
uv run --no-project --no-config --offline --python /opt/trial-venv/bin/python python skidl/circuit.py
```

These forms run through `uv` without direct PEP 723 dependency resolution. Confirm imports during setup. Give host-only scripts their PEP 723 headers.

The common container command must set its working directory to `/work`. Commands currently refer to `scripts/` and `skidl/` but the common command does not set that directory.

Keep T2 as a discovery step. Before execution, expand T9 into commands with an input filename, output path, layer list, units, origin, and drill settings. Resolve the contract's zero-suppression setting to the installed CLI option. Do not accept a default setting merely because an export exists.

I measured the fixed base image's ERC, DRC, export-group, and drill help offline. The proposed ERC flags, parity flags, `ipcd356` subcommand, and `--excellon-separate-th` exist. The DRC help also supplies `--refill-zones` and `--save-board`. Use the installed 10.0.5 help as command authority. The current online manual describes 10.0.8. [KiCad CLI documentation](https://docs.kicad.org/10.0/en/cli/cli.html)

**B5-4: separate identity experiments from the final reference board**

An unrouted baseline can test footprint identity. Label its outputs as intermediate experiment data. Record the full DRC exit code and findings even when parity passes.

Before final reference exports, finish the routing and applicable zones. Refill zones and save the board. Then run ERC, DRC, and schematic parity against that revision. Require the stated clean criteria, including no unconnected items. Record any explicit waiver against the exact source bytes. Do not suppress all non-parity findings.

Generate the final exports and hashes after the final saved-board checks. Compare exported geometry, layers, drills, and placements with the expected trial values. KiBot agreement alone is insufficient.

T12 must state the manifest status explicitly. A draft that passes consistency checks is not a qualified package. B5 does not select a supplier, so it must not invent a passed supplier-evidence check to obtain qualification. Keep the neutral trial package as draft where supplier evidence is incomplete. A DRC-clean trial board and supplier package qualification are separate results.

**B5-5: constrain identity exceptions by field**

A broad `--allow-changed R1` exception can hide a moved footprint or a lost UUID. Keep the edit table as the authority. Use field-specific comparisons or assertions over the structured differences.

Minimum invariants:

- A value edit changes only the named value.
- A source reorder changes no persistent identity, placement, rotation, layer, connectivity, or routing.
- An addition introduces exactly the expected footprint and connectivity changes.
- A removal changes only the named part and explicitly identified affected routing objects.
- A footprint replacement preserves the agreed position and all unaffected objects.
- A second unchanged update has no persistent difference.

Identify allowed routing changes by object UUID and expected connection. Do not exempt all tracks on a shared net. Retain net names, pads, UUID paths, track geometry, vias, and zone definitions in the comparisons. Normalize only documented volatile fields.

Test the identity reader against real saved KiCad output as well as text fixtures. Add negative fixtures for an unauthorized move, UUID change, pad-net change, and unrelated track deletion. A parser that omits an object class must not report identity preservation for that class.

Compare fresh SKiDL runs structurally. Record the tags and generated identities. Do not assume tags alone control all schematic identifiers before the trial measures that behavior.

**B5-6: distinguish the update inputs and stop outcomes**

U3 needs a netlist-import procedure supported by the installed editor. F8 names the schematic-update workflow. Do not count the same schematic operation as a successful netlist trial without evidence that it consumed the netlist input. If no supported import operation exists, record U3 as unsupported.

Keep U4 as the GUI mechanism and record its result separately for each input. Include dialog options, process exit, saved-file hashes, and parity results. A sequence of successful keystrokes is not a successful update.

For S5, distinguish two failures. No expected ERC finding indicates a fixture or rule problem. A reported violation with exit 0 indicates an exit-behavior problem. Do not declare the flag unreliable from the exit code alone.

If no source path passes all gate edits, stop P2. Preserve experiment logs and partial exports as incomplete evidence. S6 must not promise final reference exports when no update path produced a valid populated board.

If identity passes but the final board fails DRC or export comparisons, B5 remains incomplete. Do not continue B6 under a weaker parity-only gate.

Manual synchronization remains acceptable when the named operator and before-and-after hashes establish the tested operation. A GUI time limit can produce an explicit manual handoff. It must not produce an automated-pass claim.

**Review limits**

I used local help and existing fixed images for read-only probes. I did not pull an image, install SKiDL, build a derived image, generate a board, or run a GUI update.

This report reviews the recorded draft bytes only. A revised proposal must state the executable setup and separate completion criteria before final design agreement. I changed no implementation files.

**Revision 3 review — narrow corrections**

Reviewed SHA-256: `b59d929229fd1f836b3287b1b8abc4e0b3c0f4cebbcbd921fef78db372dcfe45`.

The six earlier corrections now have explicit procedures. Three small consistency corrections remain before final agreement.

1. **Derived image identity.** On this host, `podman image inspect --format '{{.Id}}'` returned 64 hexadecimal characters without `sha256:`. The proposal works for that measured output. Define normalization explicitly: remove an optional existing prefix, validate 64 hexadecimal characters, then add exactly one `sha256:` prefix for `container.digest`. Keep the runtime image selector separate from the recorded digest. Reject malformed output.
2. **Simulation completion.** T12 exists, but C1–C5 do not make it mandatory. Add the nominal simulation and negative capacitor case to C4 or another explicit completion criterion. Require the nominal result within 1% of the fixed 2.086 V target at 1.000 ms. The incorrect capacitor must fail that same assertion. Do not recalculate the expected time or voltage from the incorrect capacitor. Missing measurements or simulation errors keep B5 incomplete.
3. **U3 consumption probe.** The N1 sentinel netlist intentionally differs from the schematic. That probe cannot also satisfy the general empty-parity requirement. Label it an input-consumption probe with an expected parity difference. Restore agreement between the source and netlist before the ordinary identity gates and final clean-board checks. A deliberate sentinel difference must not count as a failed update method or a clean-board pass.

**Upgrade commands confirmed**

I ran both commands in the fixed local base image, offline, with `--pull=never`:

```text
kicad-cli sch upgrade --help
kicad-cli pcb upgrade --help
```

Both commands exist and returned exit 0. Their syntax is `upgrade [--help] [--force] INPUT_FILE`. They document `--force` as a forced save regardless of version. Use it when necessary to obtain a rewritten header from an already current stub.

This confirms command availability, not that an arbitrary stub is valid. T3 and its stated correction limit must still establish that result.

Keep the final reference board DRC-clean and the neutral package explicitly draft. Supplier qualification remains separate. No other design change is necessary. Prose lint corrections can follow the final design.

**Revision 4 — final design agreement**

Reviewed SHA-256: `458ff984c4a552f2a7a339ec937f6a066b187bb61ea2c210b3cfdba8dea5c0f6`.

I examined the diff from revision 3. I agree with revision 4 as the final B5 design. No substantive design conflict remains.

The diff applies digest normalization, mandatory nominal and negative simulation results, and the separate U3 sentinel probe. It also supplies both fixed-image `FROM` stages and the agreed prose corrections.

Execution must enforce S2 and digest validation. A shell comment does not stop a script. Check setup command results explicitly, or use an effective fail-fast script with equivalent behavior. Failed dependency setup, image build, image inspection, or ID validation must stop before any trial command. Do not reuse an older tagged image after a failed build.

This is the existing setup rule, not a new feature. Implementation review will examine that behavior.

B5 execution still waits for both B234 acceptance reports. Keep the clean reference board and draft neutral package separate from supplier qualification. This agreement does not approve execution results.
