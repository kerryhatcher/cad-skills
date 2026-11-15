# B7 geometry candidates

Date: 2026-11-14. These are research candidates, not measured dependencies.

Gerbonara documents Gerber and Excellon parsing, aperture macros, graphic primitives, and SVG output. Its primitives can separate file parsing from geometry work. This does not establish a mask-web algorithm or its error bound. [Official documentation](https://gerbolyze.gitlab.io/gerbonara/)

PyGerber documents a Shapely renderer that applies Boolean operations to geometry. This is a candidate for effective mask openings. The cited page describes the development API. Measure a pinned release before its use. Establish the curve approximation error and resource limits. [Official guide](https://argmaster.github.io/pygerber/dev/40_gerber/20_quick_start/01_single_file.html)

The revision-6 polygon method does not establish an exact RoundRect distance. Polygon approximation error is separate from Gerber coordinate precision. A macro name alone does not establish its geometry. Compare the macro definition and its parameters.

The final opening geometry also depends on overlap. A pairwise aperture distance can include a gap that another aperture removes. A merged opening can contain a narrow channel of mask. Test these cases before a general web claim. A smaller supported subset must refuse ambiguous overlap explicitly.

Do not write a general Gerber parser for this batch. A bounded dependency trial can compare an existing parser with the retained nominal exports. Use temporary files and pinned dependencies through `uv`. Keep network access in dependency setup only. Record the version and dependency hashes. The accepted B6 image and files stay unchanged.
