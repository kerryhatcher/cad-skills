# Placement and routing

The agent places and routes the parts in KiCad. The CLI checks the result. The CLI does not place or route.

## Steps

1. Place each footprint at its measured position. Record the position in the expected-difference file when it is a planned change.
2. Route the copper with the traces and vias of the design. Keep through-board vias only.
3. Refill the zones with `drc --refill-zones`. The command saves the board after a whole-board comparison. Only the zone-fill cache may change.
4. Run `drc` with schematic parity. A parity finding is never waived by a KiCad UI exclusion alone.
5. Record the interface with `interface --record-review` after the outline or the holes change.

## Limits

- The refill of a board that KiCad saved after a text edit can change more than the zone fill. The tool refuses such a refill. The reviewer then examines the board.
- Mounting holes and the connector frame are part of the interface. A change to them needs a review record.
- A routing change stales the ERC waivers. The user must renew them.
