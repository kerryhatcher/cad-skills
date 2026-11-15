# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3", "gerbonara==1.6.3"]
# ///
"""Exercise the profile, slot and mask cases that the acceptance inventory names."""
import tempfile
from fractions import Fraction
from pathlib import Path
import test_pcb_fab_package as base


def main():
    with tempfile.TemporaryDirectory(prefix="fab-small-gaps-") as directory:
        tmp = Path(directory)
        path = base.mutated_profile(tmp, lambda p: p["limits"]["min_trace"].update(
            kind="recommendation", value_kind="text", value="A process note.", unit="mil"))
        try:
            base.fab.check_profile(path)
            refused = False
        except base.fab.Invalid as err:
            refused = "must not have a unit" in str(err)
        base.check("A text value with a unit refuses through profile validation.", refused)
        for mil, tool in [("20.0", "0.508"), ("20.1", "0.511")]:
            minor = float(Fraction(mil) * Fraction("0.0254"))
            inventory = base.inv([[10.0, 10.0], [12.0, 10.0]], minor, major=minor + 2)
            npth = base.drl([base.export_slot((10000, -10000), (12000, -10000))]).replace("T1C0.508", f"T1C{tool}")
            code, report = base.inspect_slots.inspect(inventory, base.drl([]), npth)
            base.check(f"The {mil} mil slot matches the exported drill within the recorded tolerance.",
                       code == 0 and base.fab.judge("minimum", mil, "20") == "pass", report)
        circle = (base.FIX / "mask/m40.gts").read_text()
        variants = {
            "clear polarity": circle.replace("%LPD*%", "%LPC*%"),
            "stroke": "%FSLAX46Y46*%\n%MOMM*%\n%LPD*%\n%ADD10C,0.2*%\nD10*\nX0Y0D02*\nX1000000Y0D01*\nM02*\n",
            "another macro name": (base.FIX / "mask/rr.gts").read_text().replace("RoundRect", "OtherMacro"),
        }
        for label, data in variants.items():
            code, report = base.mask_text(tmp, label.replace(" ", "-"), data)
            base.check(f"The mask reader refuses {label} with exit 2.", code == 2, report)
    passed = sum(ok for _, ok, _ in base.RESULTS)
    print(f"\n{passed}/{len(base.RESULTS)} passed")
    return 0 if passed == len(base.RESULTS) else 1


if __name__ == "__main__":
    raise SystemExit(main())
