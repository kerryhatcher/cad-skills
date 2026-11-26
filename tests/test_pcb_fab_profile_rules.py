# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Tests for the profile-driven supplier rules of pcb-fab-package (issue #8). Run with: uv run tests/test_pcb_fab_profile_rules.py

The tests start no container job. They use the fixture skill and temporary directories.
"""
import copy
import json
import sys
import tempfile
from fractions import Fraction
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "tests"))
from fab_fixture import fixture_skill  # noqa: E402

REPO = ROOT / "skills" / "pcb-fab-package"
SKILL = fixture_skill(REPO)
sys.path.insert(0, str(SKILL / "scripts"))
import fab  # noqa: E402
import validate as VAL  # noqa: E402
import workflow  # noqa: E402

OSHPARK = ("oshpark-single-layer", "oshpark-two-layer", "oshpark-two-layer-hhdc", "oshpark-four-layer",
           "oshpark-six-layer")
DATA_ONLY = ("jlcpcb-two-layer", "jlcpcb-four-layer", "pcbway-two-layer", "pcbway-four-layer")


def expect(condition, message):
    """Raise AssertionError with the message when the condition is false."""
    if not condition:
        raise AssertionError(message)


def repo_profile(pid):
    """Return the checked record of a repository profile. No page is read."""
    return VAL.load_record(REPO / "supplier" / "profiles" / f"{pid}.yaml")


def stop_of(fn, *args):
    """Return (code, message) for a workflow.Stop, or (None, None)."""
    try:
        fn(*args)
    except workflow.Stop as err:
        return err.code, str(err)
    return None, None


def profile_copy(pid="oshpark-two-layer"):
    return copy.deepcopy(repo_profile(pid))


# ------------------------------------------------------------------ step 2: the units of the supplier rules
def test_rules_text_units_equal():
    """The same length in in, mil and mm gives the same rule text."""
    for value, unit in ((0.005, "in"), (5, "mil"), (0.127, "mm")):
        profile = profile_copy()
        profile["limits"]["min_trace"] = dict(profile["limits"]["min_trace"], value=value, unit=unit)
        text = workflow.supplier_rules_text(profile)
        expect('(rule "supplier_min_trace" (constraint track_width (min 0.127mm)))' in text,
               f"The rule text for min_trace in {unit} is incorrect:\n{text}")


def test_rules_text_no_exponent():
    """A value in mm with a zero after the point gives no exponent in the rule text."""
    profile = profile_copy()
    profile["limits"]["edge_keepout"] = dict(profile["limits"]["edge_keepout"], value=10, unit="mm")
    text = workflow.supplier_rules_text(profile)
    expect("(min 10mm)" in text, f"The edge_keepout text is not 10mm:\n{text}")
    expect("E+" not in text, f"The rule text has an exponent:\n{text}")


def test_rules_text_unknown_unit():
    """A unit that is not mm, mil or in gives exit 2."""
    profile = profile_copy()
    profile["limits"]["min_trace"] = dict(profile["limits"]["min_trace"], unit="cm")
    code, _ = stop_of(workflow.supplier_rules_text, profile)
    expect(code == workflow.EXIT_UNSUPPORTED, f"The unit cm gives the code {code}, not 2.")


def test_rules_text_unknown_rule():
    """A kicad_dru key without a KiCad constraint gives exit 2, not KeyError."""
    profile = profile_copy()
    profile["division"]["kicad_dru"].append("min_thing")
    profile["limits"]["min_thing"] = copy.deepcopy(profile["limits"]["min_trace"])
    code, _ = stop_of(workflow.supplier_rules_text, profile)
    expect(code == workflow.EXIT_UNSUPPORTED, f"The unknown rule gives the code {code}, not 2.")


def test_rules_text_bad_value():
    """A rule value that is not a finite number greater than 0 gives exit 2."""
    for value in ("abc", "NaN", "Infinity", 0, -1):
        profile = profile_copy()
        profile["limits"]["min_trace"] = dict(profile["limits"]["min_trace"], value=value)
        code, _ = stop_of(workflow.supplier_rules_text, profile)
        expect(code == workflow.EXIT_UNSUPPORTED, f"The value {value!r} gives the code {code}, not 2.")


def test_unit_tables_agree():
    """The workflow and fab tables give the same factor for each unit."""
    expect(set(workflow.RULE_UNIT_MM) == set(fab.UNIT_MM), "The two unit tables have different units.")
    for unit in ("mm", "mil", "in"):
        expect(Fraction(workflow.RULE_UNIT_MM[unit]) == fab.UNIT_MM[unit],
               f"The factor of {unit} is not equal in the two unit tables.")


TESTS = [value for name, value in list(globals().items()) if name.startswith("test_") and callable(value)]


def main():
    failed = 0
    for fn in TESTS:
        try:
            fn()
            print(f"ok   {fn.__name__}")
        except Exception as err:  # noqa: BLE001
            failed += 1
            print(f"FAIL {fn.__name__}: {type(err).__name__}: {err}")
    print(f"\n{len(TESTS) - failed}/{len(TESTS)} passed")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
