B6 design probe (read-only, not an implementation). Logs B6probe_plain_199, B6probe_mut_200, B6probe_drill_201, B6probe_tht_202.
Question: can the installed pcbnew bindings give hole and placement geometry, including rotation and the bottom side?
plain: corrected final board. mut: J1 rotated 90 degrees and C1 flipped to the bottom (in memory, saved copy).
tht: J1 (through-hole header) rotated 90 degrees and flipped to the bottom.
Each JSON is the pcbnew inventory. The *_plain/_mut/_tht .drl and .csv files are kicad-cli exports of the same saved board.
Result: the hole multisets (type, diameter, x, -y) equal the Excellon files in all three cases. The pos files agree with the pcbnew side, rotation and position.
Limits: circular drills only, one fixture, no slot, no blind or buried via, no inner layers.
The pcbnew import prints assertion messages on stderr (known, harmless here).
