# Supplier source evidence

Retrieval date: 2026-11-14 UTC.

The lead read the five public OSH Park service pages and saved their HTML response bytes. Each HTTPS request succeeded. The files are temporary research evidence. No supplier received project data.

Directory: `/tmp/cad-skills-supplier-evidence/`. Each HTML file has a separate `.headers` file from the same request. The hashes below cover HTML bytes only.

| Source and file | Bytes | SHA-256 |
|---|---:|---|
| [Single-layer service](https://docs.oshpark.com/services/single-layer/), `single-layer.html` | 12845 | `e937f343e7d4ce37d75770df6aff567c71de430b5421a1c34d63f430ffbacbc1` |
| [Two-layer service](https://docs.oshpark.com/services/two-layer/), `two-layer.html` | 20498 | `d757495f505f67436d6e9dc3b15d724c3d513d256372cbf7eb69523ae5913e25` |
| [Two-layer HHDC service](https://docs.oshpark.com/services/two-layer-hhdc/), `two-layer-hhdc.html` | 20695 | `641310abcd61e5b6c588b8f12554990e07941399f3d6cefce07c5602e16f1471` |
| [Four-layer service](https://docs.oshpark.com/services/four-layer/), `four-layer.html` | 28556 | `566570a807c779c60841a44c773e1f40f9ff4abc961c1d6b960025a7e22d3e38` |
| [Six-layer service](https://docs.oshpark.com/services/six-layer/), `six-layer.html` | 29228 | `e174c3a58bfa776f6f860b4fd2441174520dd7c20f6c51f4af273beb95060cfa` |

The current pages agree with the fabrication limits in plan section 7. The single-layer design uses the two-layer process. The 250 mil drill threshold changes tolerances. It is not a maximum accepted drill diameter. The multilayer services specify positive internal-plane images. The plan keeps these distinctions.

The four-layer HTML contains two historical stackup notices in comments. One refers to January 2026 and one to June 2026. The rendered page does not present those comments as current notices. Its changelog retains the January entry. Do not treat hidden historical comments as current fabrication limits. Use the applicable published stackup for impedance work.

The two-layer HHDC page identifies Ventec VT-47 with a nominal 28 mil core. Its August 2025 changelog states that this corrected the documentation. It did not change production. Keep substrate data separate from the nominal finished-board thickness.

These hashes identify retrieved bytes. They do not prove supplier acceptance of a board or a later order. A later retrieval can give different bytes. Recompute the hash when the evidence changes.

Keep full supplier pages in local evidence or generated output. The repository can contain source links, hashes, and factual profile values. The lead did not copy full pages into the repository.
