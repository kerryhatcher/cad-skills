# Fixtures

- `u1_saved_by_kicad.kicad_pcb`: board that KiCad 10.0.5 saved after the scripted update of the native fixture (run `U4_U1_c_110`).
- `vz_text_input.kicad_pcb`: the board above with one arc, one via and one zone added as text. These objects are not drawn in KiCad.
- `vz_saved_by_kicad.kicad_pcb`: the file above after `kicad-cli pcb upgrade --force` (KiCad 10.0.5, direct container command, no step log ID). KiCad wrote the arc, via and zone.
  This is saved KiCad output for the identity reader. It is not a preservation result. No GUI update ran on this board.
