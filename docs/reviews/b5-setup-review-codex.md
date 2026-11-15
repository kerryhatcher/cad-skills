# B5 checkpoint 1 review: Codex

Date: 2026-11-14.

**Decision: checkpoint corrections necessary**

The setup adjustment and nominal native generation are acceptable. The native checker has three blocking gaps below. Do not count this checkpoint as final B5 acceptance.

Manifest: `docs/reviews/b5-setup-files.sha256`.

Manifest SHA-256: `317f73269e6326043ab6c692fd94cb8f56782472ecaaa5eb831b4d1856eca1b0`.

All 15 entries passed before and after review. All probes used temporary copies. Container runs used `--pull=never`, `--network none`, and this existing derived image:

```text
d881df4ef3e2ec76995f4070596550db118b23e7f6db9017f09a418c44c4b1c2
```

Image inspection returned that ID and 4415434534 bytes. I did not rebuild, pull, or relabel repository files.

**Positive results and setup adjustment**

I ran the native writer through uv in the derived image. It returned exit 0 and wrote schematic version `20260306`, PCB version `20260206`, and 10 pin points.

A fresh KiCad XML export and the nominal checker both returned exit 0. The checker reported 7 references, 10 pin comparisons, and 10 pin-to-net comparisons.

I agree with `Containerfile.uv`. It uses the same two fixed bases and copies the same uv binary. It supplies the interpreter for lock resolution without a new package source or a different Python environment. The final Containerfile uses the pinned ngspice package, hashed requirements, and the system-site-packages environment as agreed.

The lock file has 29 pinned package entries, not 28. Correct that record count. This is a documentation correction, not a dependency change.

**N1: duplicate instances disappear before the count**

Location: `scripts/check_native.py`, the `instances` and `positions` dictionaries.

Reproduction on a temporary generated schematic:

1. Copy the `MH1` symbol instance.
2. Give the copy a new symbol UUID but keep reference `MH1` and its properties.
3. Export a fresh XML netlist with the existing image.
4. Run the native checker against that export.

The schematic has eight instances. KiCad exported it with exit 0 and an annotation warning. The checker returned exit 0 and reported seven instances with no problems. The dictionary overwrote the first `MH1` entry.

Count parsed instances before conversion to a dictionary. Reject duplicate references explicitly. Reject an instance with missing mandatory fields rather than silently omit it.

A second probe removed `R2`. The checker returned exit 1 through an uncaught `KeyError` at `positions[ref]`. Guard the pin loop after a missing-reference finding. Emit the ordinary problem report without a traceback.

Add negative tests for a duplicate reference, a missing expected reference, and missing mandatory instance data. The exactly-seven assertion must concern instances, not dictionary keys.

**N2: the netlist comparison loses duplicate memberships and net-name text**

Location: `scripts/check_native.py`, the `found` dictionary and leading-slash normalization.

Two independent false passes occurred:

- Add `R1.1` to the `/GND` net in an XML export. Keep its correct `/VIN` occurrence later in the file. The checker returned exit 0. The later membership overwrote the earlier one.
- Change the schematic's `VIN` labels to `/VIN`. KiCad exported the net as `//VIN`. The fresh export passed the checker because `lstrip('/')` removed both slashes.

Reject a duplicate pin key before a dictionary assignment, including repeated membership in the same net. Preserve the exact net name except for the single optional leading slash documented by this fixture. Remove at most one prefix slash.

Add negative tests for duplicate pin membership and a double-leading-slash net. Keep the nominal single-prefix case and the existing renamed-label negative test.

These are complete-map boundary checks. They do not call for a general circuit parser.

**N3: the pin-position test trusts a generated sidecar**

Location: `scripts/check_native.py`, the `pin_points.json` comparison.

The checker reads symbol positions from the schematic, but it reads computed pin points from the writer's sidecar. It does not measure pin points in the generated schematic.

I changed a temporary schematic as follows:

1. In the embedded `Device:R` definition, move pin 1 from library Y = 3.81 to Y = 6.35.
2. Move the matching labels at `R1` and `R2` by 2.54 mm to keep the intended connections.
3. Leave `pin_points.json` unchanged.
4. Export a fresh KiCad XML netlist and run the checker.

Both commands returned exit 0. The checker reported ten successful pin comparisons, although the schematic's pin geometry differs from the independent expected data.

Measure pin points from the schematic's embedded symbol definitions and instance transforms. Compare those measured points with the independent expected data. The sidecar can remain diagnostic output, but it cannot establish the result.

This fixture can reject unsupported rotations or transformations explicitly. It does not need a general symbol-rendering engine.

Add the changed-definition and matching-label negative test above. Also test a changed instance orientation. A nominal schematic must retain the present expected connectivity and pin-point results.

**Parser limits and negative-test scope**

The S-expression reader parsed the generated native files and a quoted string with an escaped quote in my probes. An extra closing parenthesis and an unterminated string raised `IndexError`.

Those malformed inputs fail closed. I do not add a separate blocker for their exception type at this checkpoint. Add small boundary tests when the checker gains the focused negative tests. Do not claim a general KiCad parser from this fixture reader.

The independent expected pin offsets and pin-to-net map are useful. N1–N3 concern how the checker compares the generated files with those expectations. Keep the independent constants rather than derive them from the output under test.

**Reviewed file hashes before and after**

The following hashes were identical before and after the probes:

```text
8e36799120a05ae787986dea8401464478e3d1ae5a6d7f4e0fdee3d603174751  examples/pcb-trial/Containerfile
169f3c4f2d226f76ae08d7aa19d4552a93b873b43adc80bab354d56541603d16  examples/pcb-trial/Containerfile.uv
e3845d86e3a4c5bf893877bc896859db6421c2126599493b5c4094c800b6ea12  examples/pcb-trial/requirements.in
f505b04d9bc3588c10d66954aba4b7eab6f6f8ad0cbf517b39b97fa544b7de15  examples/pcb-trial/requirements.lock
2dfc36f2bc4141c870de2eb4edb2bc83fd692dedf7c31241aa084f3927e8669a  examples/pcb-trial/scripts/sexp.py
fd84b82dec55fa24deb959c380148dec36fe163e46bc641de056012d17cce3a3  examples/pcb-trial/scripts/trial_native_writer.py
9d8ddf4cb77c67b879d6903d6e01be52b0771191de0d999b140068de9923131d  examples/pcb-trial/scripts/check_native.py
7e30aa03beea01f1d8ca675d6a008dd5fbc2292d4f139920ef9112dce5425c30  examples/pcb-trial/expected/pins.json
56db2c74fb63bac9c4f24071c61988b27c5744bda18f7c814673b42989881a7b  examples/pcb-trial/expected/netlist.json
a07579562689394465aea162c87d6a4d00d241162579c584d83b78bfa8e6fd98  examples/pcb-trial/native/trial.kicad_sch
2e1bbf49d1d301a1d24ea8a5db01be1d7e265d867cdaadb5fd7deb75ff19b0dd  examples/pcb-trial/native/trial.kicad_pcb
960ae85830b8a79fdbd10688eecf7cde2ba2f1a4a9af050556729b404fc1d5c6  examples/pcb-trial/native/trial.kicad_pro
0c050ebfb4cc1da7401fa11c9b6350d084d526f57bb73e1de602171387b96ce4  examples/pcb-trial/native/fp-lib-table
4bbb7d3f323a81cb26db57c64ac62bebdf6b70e3eb02b61bf3c259a9673ba048  examples/pcb-trial/native/format_versions.json
e937819500b58fa43ddad2feb4058d561ae3c2cb770d7db07902ffb84d1ef736  examples/pcb-trial/native/pin_points.json
```

The manifest hash also remained unchanged. I did not repeat unrelated tests or examine the separate SKiDL, identity, and GUI implementations. Correct N1–N3 and supply focused results with replacement hashes. The remaining trial results still control final B5 acceptance.
