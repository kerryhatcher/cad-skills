# B5 checkpoint 1 review: Pi

Date: 2026-11-14.

**Decision: checkpoint 1 accepted for setup. The native checker has three blocking gaps.**

The setup, the native generation and the container adjustment pass the agreed B5 design. I confirm the narrow `Containerfile.uv` adjustment. I found two non-blocking record or process items. The Codex native-checker gaps N1 to N3 are correct. The native checker is not accepted until they are corrected. See section 11.

Final B5 acceptance still needs the corrected native checker and the SKiDL, identity and GUI results.

**1. Reviewed identity**

| Item | Value |
|---|---|
| Manifest | `docs/reviews/b5-setup-files.sha256` |
| Manifest SHA-256 | `317f73269e6326043ab6c692fd94cb8f56782472ecaaa5eb831b4d1856eca1b0` |
| Proposal revision 4 SHA-256 | `458ff984c4a552f2a7a339ec937f6a066b187bb61ea2c210b3cfdba8dea5c0f6` |
| Derived image for focused probes | `d881df4ef3e2ec76995f4070596550db118b23e7f6db9017f09a418c44c4b1c2` |

All 15 manifest entries passed before the focused probes and after the focused probes. `git status` shows `examples/pcb-trial/` as a new directory in the working tree. The files are frozen.

**2. Frozen file hashes**

| File | SHA-256 |
|---|---|
| `examples/pcb-trial/Containerfile` | `8e36799120a05ae787986dea8401464478e3d1ae5a6d7f4e0fdee3d603174751` |
| `examples/pcb-trial/Containerfile.uv` | `169f3c4f2d226f76ae08d7aa19d4552a93b873b43adc80bab354d56541603d16` |
| `examples/pcb-trial/requirements.in` | `e3845d86e3a4c5bf893877bc896859db6421c2126599493b5c4094c800b6ea12` |
| `examples/pcb-trial/requirements.lock` | `f505b04d9bc3588c10d66954aba4b7eab6f6f8ad0cbf517b39b97fa544b7de15` |
| `examples/pcb-trial/scripts/sexp.py` | `2dfc36f2bc4141c870de2eb4edb2bc83fd692dedf7c31241aa084f3927e8669a` |
| `examples/pcb-trial/scripts/trial_native_writer.py` | `fd84b82dec55fa24deb959c380148dec36fe163e46bc641de056012d17cce3a3` |
| `examples/pcb-trial/scripts/check_native.py` | `9d8ddf4cb77c67b879d6903d6e01be52b0771191de0d999b140068de9923131d` |
| `examples/pcb-trial/expected/pins.json` | `7e30aa03beea01f1d8ca675d6a008dd5fbc2292d4f139920ef9112dce5425c30` |
| `examples/pcb-trial/expected/netlist.json` | `56db2c74fb63bac9c4f24071c61988b27c5744bda18f7c814673b42989881a7b` |
| `examples/pcb-trial/native/trial.kicad_sch` | `a07579562689394465aea162c87d6a4d00d241162579c584d83b78bfa8e6fd98` |
| `examples/pcb-trial/native/trial.kicad_pcb` | `2e1bbf49d1d301a1d24ea8a5db01be1d7e265d867cdaadb5fd7deb75ff19b0dd` |
| `examples/pcb-trial/native/trial.kicad_pro` | `960ae85830b8a79fdbd10688eecf7cde2ba2f1a4a9af050556729b404fc1d5c6` |
| `examples/pcb-trial/native/fp-lib-table` | `0c050ebfb4cc1da7401fa11c9b6350d084d526f57bb73e1de602171387b96ce4` |
| `examples/pcb-trial/native/format_versions.json` | `4bbb7d3f323a81cb26db57c64ac62bebdf6b70e3eb02b61bf3c259a9673ba048` |
| `examples/pcb-trial/native/pin_points.json` | `e937819500b58fa43ddad2feb4058d561ae3c2cb770d7db07902ffb84d1ef736` |

**3. Fixed-image setup and the `Containerfile.uv` adjustment — confirmed**

The two fixed images are local. `podman image exists` returned true for the base image and the derived image.

- `Containerfile` starts from the fixed base image and copies `/uv` from the fixed uv image. It installs the pinned `ngspice`, copies the lock file, creates the venv, and syncs with `--require-hashes`.
- `Containerfile.uv` uses the same two fixed images. It adds only the `uv` binary. It adds no other base, package source, or tool.

The record states that T0a as written failed with exit 2 because the uv image has no libc and no Python interpreter. The adjustment runs `uv pip compile` inside `Containerfile.uv` with `--python /usr/bin/python3`. This uses the base image Python and the allowed PyPI source.

I confirm the adjustment. It is necessary, narrow, and within the allowed source list. It does not change the derived image or the trial.

**4. Dependency lock — confirmed, with one record correction**

- `requirements.in` holds `skidl==3.0.0`.
- `requirements.lock` pins 29 packages. Every package entry has at least one `--hash=sha256:`. The file has 736 hash lines.
- The lock includes `skidl==3.0.0`, `numpy==2.5.4`, `matplotlib==3.11.2`, `kinet2pcb==1.1.4`, and `inspice==1.7.0.7`.
- `uv pip sync --require-hashes` installs the lock into the venv. The offline import probe confirms the result.

Record correction: the checkpoint record says 28 pinned packages. The lock file has 29 package entries. This is a documentation count error. It does not affect the setup.

**5. Interpreter choice — confirmed**

- KiCad scripts use `/usr/bin/python3`.
- SKiDL uses `/opt/trial-venv/bin/python`.
- The venv is created with `--system-site-packages`, so `pcbnew` imports from the system.
- The offline import probe used `/opt/trial-venv/bin/python` and imported both `skidl` and `pcbnew`.

The choice matches the agreed design.

**6. Offline imports — confirmed**

I ran the derived image with `--network none` and a temporary copy of `examples/pcb-trial`.

```text
uv run --no-project --no-config --offline --python /opt/trial-venv/bin/python python -c "import skidl, pcbnew"
```

Result: exit 0, `import-ok`. The output keeps the three `PROPERTY_ENUM` assertion messages and the `fp-lib-table` warnings. The import does not set `KICAD10_SYMBOL_DIR`. T4 must set that variable for schematic generation. The record states this.

**7. Native fixture — confirmed**

I re-exported the netlist from the frozen schematic and ran the checker in the derived image with `--network none`.

| Check | Result |
|---|---|
| `kicad-cli sch export netlist --format kicadxml` | Exit 0. |
| `check_native.py` | 7 instances, 10 pins compared, 10 nets compared, no problems. |
| `kicad-cli sch erc --exit-code-violations --severity-all` | Exit 0, 0 violations. |
| Schematic version | `(version 20260306)`. |
| PCB version | `(version 20260206)`. |

The schematic and PCB versions differ from the symbol-library header `20251024`. The native path learns the two format versions from installed KiCad output. This matches the agreed design.

The empty PCB DRC result is in the record. I did not repeat it. It is not a blocking item for this checkpoint.

**8. Recorded setup deviation and process items**

- T0a failed as written. The record keeps the failed log and describes the `Containerfile.uv` repair. This is the main setup deviation.
- The unsplit-argument loop, the `T3` typo, the missing `/work` mount, and the one-layer PCB stub were corrected. The records keep them as evidence.
- One JSON read used the host `python3` and not `uv`. This is a process violation of the repository rule. It was an exploratory read and not part of a result. It must not repeat. A result that depends on it must use `uv`.
- `scripts/gui_probe.sh` is an exploration script. It is not in the manifest and is not a result.

**9. Limits**

- I used one host, one base image, and one derived image.
- I did not rebuild or pull an image. I did not relabel the repository. I used temporary copies with `:Z`.
- I did not run the GUI, SKiDL, identity or full trial steps.
- The focused probes used `--network none`.
- The native fixture has not been through an update experiment.

**10. Verdict**

Checkpoint 1 is accepted. The fixed-image setup, the `Containerfile.uv` adjustment, the dependency lock, the interpreter choice, the offline imports, and the native fixture agree with the agreed B5 design.

Two non-blocking items:
1. Correct the package count in the checkpoint record from 28 to 29.
2. Do not repeat the host `python3` read. Use `uv` for every Python command.

Final B5 acceptance still needs the SKiDL, identity and GUI results.

**11. Codex N1 to N3 confirmation**

I agree with N1, N2 and N3. They are concrete gaps in `scripts/check_native.py`.

N1: duplicate references and missing references.

- The checker builds `instances` and `positions` dictionaries before it counts. A duplicate reference overwrites an earlier entry. The `len(instances) != 7` test counts dictionary keys, not parsed instances. A missing expected reference causes a `KeyError` at `positions[ref]`.
- Correction: collect the parsed instances in a list first. Count the list. Detect a duplicate reference and report it. Catch a missing mandatory field and report it. Guard the pin loop after a missing-reference finding. Do not raise a traceback.
- Tests: a duplicate reference, a missing expected reference, and missing mandatory instance data. The exactly-seven test must concern the parsed instance list, not dictionary keys.

N2: duplicate pin membership and net-name normalization.

- The checker writes `found[ref.pin] = net`. A later membership overwrites an earlier one. `name.lstrip("/")` removes all leading slashes. A net named `//VIN` becomes `VIN` and passes.
- Correction: reject a duplicate `ref.pin` key before assignment. Apply this rule to a repeat in the same net and to a repeat in a different net. Preserve the exact net name except for at most one optional leading slash.
- Tests: duplicate pin membership, a double-leading-slash net, the nominal single-prefix case, and the renamed-label negative case.

N3: the pin-position test trusts a generated sidecar.

- The checker reads computed pin points from `pin_points.json`. That sidecar comes from the writer. The checker does not measure the pin points in the generated schematic. A changed embedded symbol definition can pass with an unchanged sidecar.
- Correction: measure the pin points from the embedded `lib_symbols` definitions and the instance transforms. Compare those measured points with the independent expected data. Keep `pin_points.json` as diagnostic output only. Reject an unsupported rotation or transform explicitly. A general renderer is not necessary.
- Tests: a changed embedded pin definition with matching labels, and a changed instance orientation. A nominal schematic keeps the present connectivity and pin-point results.

Keep the independent expected constants. Do not derive the expected values from the output under test.

The container setup stays accepted. The native checker gaps are blocking for final B5 acceptance.

This review changes only this report. It makes no implementation edit.
