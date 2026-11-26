# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Make or examine the standalone KiCad rule files of this skill.

Each profile in `supplier/profiles/` gives one rule file in `supplier/rules/`.
The file name is `<profile-id>.kicad_dru`. A person puts a rule file into a KiCad project.
Then the person runs the design rule check (DRC) in KiCad.

The workflow does not read these files. The workflow makes its rules from the profile when it runs,
with `workflow.supplier_rules_text`. This generator uses the same function. Thus both rule texts are equal.

The generator does not examine the supplier pages. A clean checkout has no pages.
Relative paths start at the skill directory.

Exit status:
  0  the files agree with the profiles, or the write mode wrote every file that was different.
  1  the check found a difference or a missing file. Or a rule file has no profile.
  2  a profile, an argument or a path is not acceptable. A symbolic link is at the path.
  3  a file cannot be read or written, or the schema registry is not usable.
"""

import argparse
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))

import fab  # noqa: E402
import project_io as PIO  # noqa: E402
import validate as VAL  # noqa: E402
import workflow  # noqa: E402

SKILL = HERE.parent
PROFILES = SKILL / "supplier" / "profiles"
RULES = SKILL / "supplier" / "rules"
SCHEMAS = SKILL / "contracts" / "schemas"
SUFFIX = ".kicad_dru"
RULE_UNITS = ("mm", "mil")
PREFIX = "make_rules: "
EXIT_OK, EXIT_DIFF, EXIT_INVALID, EXIT_TOOL = 0, 1, 2, 3


class Invalid(Exception):
    """A profile, an argument or a path is not acceptable. The generator exits 2."""


def describe(findings):
    """Return the findings as one text. Each item gives the location and the message."""
    return " ".join(f"{item['location'] or '/'} {item['message']}" for item in findings)


def shown(path):
    """Return the path relative to the skill directory, when it is inside the skill."""
    try:
        return str(pathlib.Path(path).relative_to(SKILL))
    except ValueError:
        return str(path)


def load_profile(path, registry):
    """Return the checked profile record. Refuse a symbolic link, a schema violation, an incorrect hash or id."""
    if path.is_symlink():
        raise Invalid(f"{path.name} is a symbolic link. Replace it with the profile file.")
    try:
        record = VAL.load_record(path)
    except VAL.RecordError as err:
        raise Invalid(f"{path.name}: {describe(err.findings)}")
    findings = VAL.validate_record(record, registry, str(path))
    if findings:
        raise Invalid(f"{path.name} does not match the profile schema. {describe(findings)}")
    if record.get("schema_id") != "cad-skills/supplier-profile":
        raise Invalid(f"{path.name} has the schema_id {record.get('schema_id')!r}. "
                      "The generator needs the schema cad-skills/supplier-profile.")
    if record.get("content_sha256") != fab.content_hash(record):
        raise Invalid(f"{path.name}: content_sha256 does not match the record content. "
                      "Correct the hash, then run make_rules.py again.")
    if record["id"] != path.stem:
        raise Invalid(f"{path.name}: the profile id is different from the file name. "
                      "Rename the file or change the id.")
    return record


def check_rule_limits(record):
    """Refuse a rule that the generator cannot write exactly. Each rule needs a minimum limit in mil or mm."""
    pid = record["id"]
    for key in record["division"].get("kicad_dru", []):
        if key not in workflow.RULE_CONSTRAINT:
            raise Invalid(f"{pid}: the rule {key} has no constraint in the workflow. "
                          "Add it to RULE_CONSTRAINT or remove the key from division.kicad_dru.")
        limit = record["limits"].get(key)
        if limit is None:
            raise Invalid(f"{pid}: the rule {key} names no limit.")
        if limit.get("kind") != "minimum" or limit.get("value_kind") != "number":
            raise Invalid(f"{pid}: the limit {key} must be a minimum with a number value.")
        if limit.get("unit") not in RULE_UNITS:
            raise Invalid(f"{pid}: the limit {key} must use the unit mil or mm.")


def rules_text(record):
    """Return the rule file bytes of one profile. The workflow function makes the text."""
    check_rule_limits(record)
    return workflow.supplier_rules_text(record).encode("utf-8")


def expected_files(profiles_dir, registry):
    """Return {file name: bytes} for each profile. Raise Invalid if no profile is found."""
    paths = sorted(profiles_dir.glob("*.yaml"))
    if not paths:
        raise Invalid(f"No profile is in {shown(profiles_dir)}. Examine the --profiles argument.")
    expected = {}
    for path in paths:
        record = load_profile(path, registry)
        expected[f"{record['id']}{SUFFIX}"] = rules_text(record)
    return expected


def differences(rules_dir, expected):
    """Compare the rule directory with the expected bytes. Return (kind, path, message) for each difference.

    The kinds are missing, different and additional. A symbolic link in the directory is refused.
    """
    if os.path.islink(rules_dir):
        raise Invalid(f"{shown(rules_dir)} is a symbolic link. Replace it with a directory in the skill.")
    present = {}
    if rules_dir.is_dir():
        for path in sorted(rules_dir.iterdir()):
            if path.is_symlink():
                raise Invalid(f"{shown(path)} is a symbolic link. Remove it. The generator does not follow it.")
            if path.suffix == SUFFIX and path.is_dir():
                raise Invalid(f"{shown(path)} is a directory. The generator cannot compare it with a "
                              "profile. Remove it.")
            if path.suffix == SUFFIX:
                present[path.name] = path
    found = []
    for name, data in sorted(expected.items()):
        path = rules_dir / name
        if name not in present:
            found.append(("missing", path, f"{shown(path)} is missing. Run make_rules.py without --check."))
        elif present[name].read_bytes() != data:
            found.append(("different", path, f"{shown(path)} is different from the profile. "
                          "Run make_rules.py without --check."))
    for name in sorted(set(present) - set(expected)):
        path = present[name]
        found.append(("additional", path, f"{shown(path)} has no profile. "
                      "Remove the file, or add its profile."))
    return found


def build_parser():
    parser = argparse.ArgumentParser(
        prog="make_rules.py",
        description="Make or examine the standalone KiCad rule files. Relative paths start at the skill directory.")
    parser.add_argument("--profiles", type=pathlib.Path, default=PROFILES,
                        help="directory of the supplier profiles (default: supplier/profiles)")
    parser.add_argument("--out", type=pathlib.Path, default=RULES,
                        help="directory of the rule files (default: supplier/rules). It must stay in the skill.")
    parser.add_argument("--check", action="store_true",
                        help="write nothing. Report each difference and exit 1.")
    return parser


def main(argv=None):
    args = build_parser().parse_args(argv)
    profiles = args.profiles if args.profiles.is_absolute() else SKILL / args.profiles
    out = args.out if args.out.is_absolute() else SKILL / args.out
    try:
        registry = VAL.load_registry(SCHEMAS)
    except VAL.ToolError as err:
        print(PREFIX + describe(err.findings), file=sys.stderr)
        return EXIT_TOOL
    try:
        expected = expected_files(profiles, registry)
        PIO.confine(SKILL, out)
        found = differences(out, expected)
    except (Invalid, PIO.PathEscape) as err:
        print(PREFIX + str(err), file=sys.stderr)
        return EXIT_INVALID
    except OSError as err:
        print(PREFIX + f"cannot read the rule files: {err}. Examine the permissions.", file=sys.stderr)
        return EXIT_TOOL

    if args.check:
        for _, _, message in found:
            print(PREFIX + message, file=sys.stderr)
        return EXIT_DIFF if found else EXIT_OK

    try:
        for kind, path, _ in found:
            if kind != "additional":
                PIO.atomic_write(SKILL, path, expected[path.name])
                print(PREFIX + f"wrote {shown(path)}.")
    except PIO.PathEscape as err:
        print(PREFIX + str(err), file=sys.stderr)
        return EXIT_INVALID
    except OSError as err:
        print(PREFIX + f"cannot write the rule files: {err}. Examine the permissions of the rule directory.",
              file=sys.stderr)
        return EXIT_TOOL
    additional = [message for kind, _, message in found if kind == "additional"]
    for message in additional:
        print(PREFIX + message, file=sys.stderr)
    return EXIT_DIFF if additional else EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
