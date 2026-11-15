# B5 design review: Pi

Date: 2026-11-14.

Proposal: `docs/reviews/b5-trial-proposal-claude.md`, revision 4.

Proposal SHA-256: `458ff984c4a552f2a7a339ec937f6a066b187bb61ea2c210b3cfdba8dea5c0f6`.

Context: `docs/reviews/b5-design-codex.md`, B5-1 to B5-6 and the revision-3 review. The body sections below record the revision-3 review. Revision 4 applies those corrections. Section 9 records the final confirmation.

**Decision**

I agree with B5-1 to B5-6 and with revision 3. I agree with the three Codex revision-3 corrections. Two of them match my N1 and N2. The third is new and correct. One remaining concrete execution detail is not a blocker. The corrections concern exact commands and the completion gate. They do not add a feature or a framework.

B5 must use the corrected B234 validator and package rules.

**1. Agreement**

- The independent native writer with its own generator name.
- Separate schematic and PCB format versions with installed KiCad output as evidence.
- The two-correction limit and the "untested" result for a generator failure.
- The separate phase A identity experiments and phase B final reference board.
- The field-specific identity comparison and the expected-difference file.
- The distinct U3 netlist import with an input-dependent test.
- The separate U4 result rows for U1, U2 and U3.
- The explicit stop conditions and the manual handoff.
- The draft package with `fab.profile_evidence` pending.

**2. `sch upgrade` and `pcb upgrade` exist — verified**

The root concern is resolved. I ran the fixed base image offline on this host.

Container image ID: `8390a3360c566e2f325630aad6840795feae46c36e1f2be27e7f4f9826331042`.

| Command | Result |
|---|---|
| `kicad-cli sch upgrade --help` | Exit 0. Usage: `sch upgrade [--help] [--force] INPUT_FILE`. It upgrades the schematic format. |
| `kicad-cli pcb upgrade --help` | Exit 0. Usage: `pcb upgrade [--help] [--force] INPUT_FILE`. It upgrades the board format. |
| `kicad-cli sch erc --help` | Exit 0. It lists `--severity-all`, `--format` and `--exit-code-violations`. |
| `kicad-cli pcb drc --help` | Exit 0. It lists `--schematic-parity`, `--refill-zones`, `--save-board` and `--exit-code-violations`. |

T2 and T3 can use the upgrade commands. The proposal states the commands correctly.

**3. Narrow correction N1: normalize the derived image ID prefix**

On this host, `podman image inspect --format '{{.Id}}'` prints a bare hexadecimal ID. The proposal sets `container.digest` to `sha256:` followed by that ID. That is correct here.

Some podman versions print `sha256:<hex>` from the same format. The proposal would then store `sha256:sha256:<hex>`.

Correction:

1. Read the ID into a variable.
2. Remove one optional `sha256:` prefix.
3. Set the run ID to the bare hexadecimal text.
4. Set the record digest to `sha256:` plus the bare text.
5. Test that `container.digest` has exactly one `sha256:` prefix and 64 hexadecimal characters.
6. Keep the base image digest in the `kicad` tool `notes` and in the trial record, as the proposal states.

**4. Narrow correction N2: include T12 in the completion gate**

The root condition is correct. The analytical simulation and its negative case must belong to C1 to C5.

Correction: extend C4.

- C4 now also requires T12 to agree with the analytic value 2.086 V within 1 percent.
- C4 also requires the deliberately wrong capacitor case to fail the same check.
- No other completion criterion changes.

The wrong-capacitor case must use the same test method as the correct case. Record both results.

**5. Narrow correction N3: U3 is an input-consumption probe with an expected parity difference**

The Codex revision-3 correction is correct. The N1 sentinel netlist intentionally differs from the schematic. The probe exists to prove that the installed netlist import read the input. It cannot also satisfy the general empty-parity requirement.

Correction:

1. Label the U3 result as an input-consumption probe, not a clean-board pass.
2. Record the expected parity difference for that probe. State the exact objects and nets that differ.
3. Restore agreement between the source and the netlist before the ordinary identity gates.
4. Restore agreement before the final clean-board checks.
5. A deliberate sentinel difference must not count as a failed update method or as a clean-board pass.
6. The final reference board keeps the empty-parity criterion. The sentinel difference does not enter it.

This is an acceptance rule. It does not change the experiment.

**6. Execution notes that are not blockers**

- The proposal still does not show the `Containerfile` `FROM` line. Add it as the first line with the fixed base digest `ghcr.io/inti-cmnb/kicad10_auto_full@sha256:96e75f885b15617c6b38aef11db7856a93f4367cab7a0b6c2b30465557619330`. This is a concrete execution detail, not a design blocker.

- Confirm that the base image Debian release provides `ngspice=44.2+ds-1` before the build. S2 stops on failure.
- `uv pip compile --python-version 3.13.5` matches the measured image Python.
- The `COPY` paths match the build context `$TRIAL`.
- `--pull=never` requires the base image and the uv image to be local. S1 and S2 cover a mismatch.
- The `uv run --python ... python` form needs a setup import test. The proposal already has the offline probe.
- The final board checks and the draft package are separate results. The proposal states this.

**7. Limits**

- I ran read-only help commands in the fixed base image. I did not pull an image, build the derived image, install SKiDL, generate a board, or run a GUI update.
- I did not verify the `ipcd356` subcommand or the `--excellon-separate-th` option in this review. The Codex report measured them on the same image.
- The B234 corrections are not in place yet. B5 must wait for their acceptance.

**8. Agreement**

I agree with the B5 design when the three Codex revision-3 corrections are applied. My N1 and N2 are the same as Codex correction 1 and 2. The U3 sentinel rule is Codex correction 3. They do not change the experiment.

**9. Revision 4 confirmation**

Final hash: `458ff984c4a552f2a7a339ec937f6a066b187bb61ea2c210b3cfdba8dea5c0f6`.

Decision: the revision-4 diff matches the agreed B5 design.

- The three Codex corrections are present. The derived image identity removes one optional `sha256:` prefix, checks 64 hexadecimal characters, and records exactly one prefix. T12 and the negative capacitor case are in C4. The U3 sentinel probe is an input-consumption probe with an expected parity difference, and the final board keeps the empty-parity rule.
- The `Containerfile` shows the complete two-stage `FROM` lines. The first stage supplies `/uv`. The second stage uses the fixed base image digest.
- The prose repairs are present.

One narrow execution correction remains. The setup block shows a comment that says the malformed ID stops the setup, but a comment alone does not enforce it. The `podman build` command and the `grep` test also do not stop the script by themselves.

Correction: enforce fail-fast setup. Use one of these forms.

```bash
set -euo pipefail
podman build -t localhost/cad-skills-trial:b5 -f "$TRIAL/Containerfile" "$TRIAL"
RAW_ID=$(podman image inspect --format '{{.Id}}' localhost/cad-skills-trial:b5)
IMAGE_ID=${RAW_ID#sha256:}
printf '%s' "$IMAGE_ID" | grep -Eqx '[0-9a-f]{64}'
RECORD_DIGEST="sha256:$IMAGE_ID"
```

Or add an explicit exit to each command.

```bash
podman build -t localhost/cad-skills-trial:b5 -f "$TRIAL/Containerfile" "$TRIAL" || { echo "The image build failed." >&2; exit 1; }
RAW_ID=$(podman image inspect --format '{{.Id}}' localhost/cad-skills-trial:b5) || { echo "Cannot read the image ID." >&2; exit 1; }
IMAGE_ID=${RAW_ID#sha256:}
if ! printf '%s' "$IMAGE_ID" | grep -Eqx '[0-9a-f]{64}'; then
  echo "Malformed image ID: $RAW_ID" >&2
  exit 1
fi
RECORD_DIGEST="sha256:$IMAGE_ID"
```

The check must run before the first container run that uses `$IMAGE_ID`. This is the existing S2 and digest rule. It is not a new design.

B5 waits for both B234 acceptances. The Pi B234 correction review is accepted. The Codex acceptance is still necessary.

This review changes only this report. It makes no implementation edit.
