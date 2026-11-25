# Supplier rule boundaries

These owned boards test three generated supplier rules.
One mil equals 0.0254 mm.

| Rule | Test values (mil) | Independent geometry |
|---|---|---|
| `min_space` | 5.9, 6, 6.1 | Track center distance minus the two half-widths |
| `min_annular_ring` | 4.9, 5, 5.1 | Half the difference between copper diameter and drill diameter |
| `edge_keepout` | 14.9, 15, 15.1 | Track center distance from the edge minus the track half-width |

The first value fails. The boundary and the last value pass.
The test uses the profile rules without a relaxed limit.
The retained boards use the same bytes as the test inputs.
