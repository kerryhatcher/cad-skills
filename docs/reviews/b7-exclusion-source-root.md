# B7 exclusion source note

Date: 2026-11-14. The source tag is KiCad 10.0.5. The fixed image still needs a measured trial.

For a straight track-width finding, the source uses the track midpoint as the marker position. For an arc, it uses the start point. The item position in a JSON report does not necessarily identify this marker position. [Track-width provider](https://raw.githubusercontent.com/KiCad/kicad-source-mirror/10.0.5/pcbnew/drc/drc_test_provider_track_width.cpp)

The marker serializer records the settings key, marker coordinates, main item UUID, and auxiliary item UUID for this case. The exclusion trial should use that marker position in internal integer units. [Marker source](https://raw.githubusercontent.com/KiCad/kicad-source-mirror/10.0.5/pcbnew/pcb_marker.cpp)

The project issue gives an example of the array entry and an excluded JSON finding. Its reported versions do not establish behavior in our image. [KiCad issue 24264](https://gitlab.com/kicad/code/kicad/-/issues/24264)

Retain the six unsuccessful candidate records. A successful candidate must first mark the finding as excluded. Then the staged copy must remove that exclusion and retain the violation. Compare source bytes before and after the trial.

The lead read `scratchpad/excl/probe4.py`. Its G and H values append a comma and comment to the serialized string. The script then stores that string as a list item. This does not test the intended two-element array. Store the serialized value and comment as separate array elements.

The script also uses a regular expression that can span multiple segment blocks before the target UUID. Read the target track through the existing parser or `pcbnew`. The two failed runs do not establish failure of the source-derived format.
