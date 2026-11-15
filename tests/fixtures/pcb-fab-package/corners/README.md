# Corner fixtures

The generator uses explicit dimensions. It writes no production board.
Run it with `uv run generate.py` from this directory.

The outline fixtures have one concave quarter-circle corner at 0.033, 0.034 and 0.035 inch.
The cutout fixtures have four quarter-circle corners at 0.019, 0.020 and 0.021 inch.
The expected sequence is fail, pass, pass for each group.
The comparison uses the tool radius derived from the published cutter diameter.
It does not treat that derived radius as a quoted supplier minimum.

The square has only convex outer corners. The tool-radius comparison does not apply to them.
The open contour and the polygon shape exercise named unsupported-geometry refusals.
The worker supports segments, rectangles, circles and quarter-circle arcs only.
It uses exact endpoint connections and the pcbnew radius in integer nanometers.
The topology polygon has a circular chord bound of one micrometer.
The worker refuses separate contours within 0.01 mm and refuses invalid or nested cutout topology.
These limits do not change the exact radius comparison.
