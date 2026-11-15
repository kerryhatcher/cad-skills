# B6 record correction (claude-skill-dev)

Date: 2026-11-14. This note corrects one statement in `b6-final-record.md`. It does not change the frozen files.

The record says that the two-layer, four-layer and six-layer fixtures cannot hold a blind or buried via. That is incorrect for four- and six-layer boards. A blind or buried via can be placed on an inner layer pair there. The statement applies only to the two-layer board.

Status of the test: the worker refuses a via whose span is not F.Cu to B.Cu (`REFUSED_VIA` in `board_inventory.py`, exit 2 with the named object). The slot fixture (`tests/fixtures/pcb-design/slot.kicad_pcb`) tests the slot refusal. No blind-via fixture exists yet. Such a fixture is needed on a four-layer board before the blind-via refusal is claimed as tested.
