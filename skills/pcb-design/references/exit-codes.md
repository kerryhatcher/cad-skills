# Exit codes

| Exit | Meaning | Examples |
|---:|---|---|
| 3 | Tool execution or result failure | Unexpected tool exit, missing output, unparsable report, missing measured value, failed publication after a replacement, `update.summary_malformed`, `update.kicad_exit`, `update.option_mismatch` |
| 2 | Incorrect invocation, missing prerequisite, runtime mismatch, or a recognized unsupported source, geometry, setting or adapter | `runtime.image_mismatch`, `runtime.version_mismatch`, `runtime.native_unavailable`, `runtime.conflict`, `export.unsupported_setting`, `export.unsupported_geometry`, `sim.unsupported_dependency`, `pcb.external_library`, `pcb.library_missing`, `update.adapter_unavailable`, `update.expectation_missing`, `update.manual_required`, `interface.review_invalid` |
| 1 | Invalid record, unwaived violation, failed assertion or comparison, stale or missing evidence, lock refusal | `report.stale`, `report.binding_mismatch`, `waiver.stale`, `sim.assertion`, `assertion.malformed`, `interface.geometry_changed`, `update.identity_mismatch`, `update.parity`, `export.file_missing`, `export.file_changed` |
| 0 | Complete success under the operation's policy | `pass` or `pass_with_waivers` |

The highest status wins when several conditions occur. A raw ERC or DRC exit 5 maps to exit 0 only when every violation has a valid waiver. The raw exit stays in the binding file.
