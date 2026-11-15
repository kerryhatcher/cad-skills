# Trial limits

- One fixture board (the B5 RC and LED board, KiCad 10.0.5) and one machine. Four- and six-layer boards are fixtures that `pcbnew` derives from the template. They test copper declarations only.
- Circular drills only. The worker refuses a slot or oval drill and names the object (exit 2). A fixture tests this refusal.
- Through-board vias only. The worker refuses a via that does not span F.Cu to B.Cu (exit 2, named object). Four- and six-layer boards can hold blind and buried vias. The blind-via refusal therefore needs a fixture before it counts as tested. No such fixture exists yet.
- Neutral export settings only: rs274x, mm, no X2, six Gerber decimals, three drill decimals, leading zero suppression and absolute origin. The controller refuses other values (exit 2).
- Copper: the declarations follow the measured copper order, including inner layers. Fixtures with four and six layers test this. The contract must name every inner copper layer of the board.
- The measured drill and placement convention: the Y value in the drill file is the negative of the board Y value (KiCad 10.0.5). The placement file uses the same convention. The placement output lists every footprint, mounting holes included.
- The controller refuses a simulation circuit with include, library or HDL directives (exit 2). The dependency would lie outside the input closure.
- Project-local libraries that the library tables name are in the input closure. The controller refuses any other library path (exit 2). System libraries under `/usr/share/kicad` belong to the runtime identity.
- The native route runs only inside the runtime image. KiCad is not installed on the host, so the host route exits 2.
- We measured the standalone rebuild (`--no-cache`) on this host. Its image ID differs. The gui adapter does not certify it.
- The gui update adapter has one measured dialog layout (KiCad 10.0.5, screen 1600x1000). The controller certifies it only for the measured image IDs.
- The interface check compares the whole saved board conservatively. It does not show that the mechanical design fits an enclosure. An automatic rebinding result binds the exact interface bytes. A changed interface stays not ready until a reviewer examines it again.
- The review record is an acknowledgment by a named reviewer. It is not machine proof. A self-review is not an independent review.
- The supplier record is an example. The supplier qualification is not measured.
