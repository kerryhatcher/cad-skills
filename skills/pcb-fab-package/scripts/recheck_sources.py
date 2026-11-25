# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Release re-check of the supplier pages named by a sources.yaml manifest.

The command runs fetch_sources.py in check-only mode. It compares the live page bytes with the recorded hashes.
It writes no file and changes no profile. It prints a report. It is a release step, not a CI step.
Exit codes: 2 for a problem in the arguments or the manifest, 3 for a fetch failure, 1 for a page that does not match, 0 when every page matches.
"""
import argparse
import datetime
import hashlib
import json
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fetch_sources as FS  # noqa: E402

EXIT_OK, EXIT_CHANGED, EXIT_ARGS, EXIT_FETCH = 0, 1, 2, 3
REPORT_SCHEMA = "cad-skills/source-recheck"
REPORT_VERSION = 1
FORMATS = ("markdown", "json")
# The watch items. Each item dates a note on a supplier page. A hash cannot examine the note.
# The dates come from the "Preferred vendor" instruction of issue #1 and from issue #7.
WATCH_ITEMS = (
    {"entry": "oshpark-four-layer-html", "since": "2026-01-28",
     "note": "Examine the temporary alternate stackup note on the page."},
    {"entry": "oshpark-six-layer-html", "since": "2025-12-15",
     "note": "Examine the lead time on the page. It changed on 2025-12-15."},
)
FALLBACK_PROFILE = "the profile that uses this page"
ACTION_CHANGED = ("Record a new source review with fab.py review-source before you change {profile}. "
                  "Do not edit the profile or sources.yaml from this report.")
ACTION_FETCH = "Run the re-check again. If the failure continues, examine the URL by hand."
CI_REFUSAL = ("This command contacts the supplier pages. It is a release step, not a CI step. "
              "Use --allow-ci only for a manual run.")


class _ArgumentError(Exception):
    """A problem in the command line. The message names the problem."""


class _Parser(argparse.ArgumentParser):
    """Raise an error. Do not print the usage text and exit."""

    def error(self, message):
        raise _ArgumentError(message)


def parse_args(argv):
    """Return the parsed options. Raise _ArgumentError for a problem in the command line."""
    parser = _Parser(prog="recheck_sources.py",
                     description="Compare the live supplier pages with the manifest hashes. Writes no file.")
    parser.add_argument("--manifest", required=True, help="the sources.yaml file to examine")
    parser.add_argument("--entry", action="append", default=[], metavar="ID",
                        help="examine only this entry. Repeat the option for more entries")
    parser.add_argument("--format", choices=FORMATS, default="markdown", help="the report format")
    parser.add_argument("--allow-ci", action="store_true",
                        help="run when the CI variable is set. Use this only for a manual run")
    return parser.parse_args(argv)


def check_watch(entries, watch):
    """Return an error text when a watch item is not in the manifest. Return None when all are present.

    The check uses the whole manifest, not the selected entries, so a selection never hides a missing item."""
    # An entry that is not a mapping is skipped here. fetch_sources.main refuses it with exit 2.
    ids = {row.get("id") for row in entries if isinstance(row, dict)}
    missing = [item["entry"] for item in watch if item["entry"] not in ids]
    if not missing:
        return None
    return (f"recheck_sources.py: the watch item {', '.join(missing)} is not in the manifest. "
            "Restore the entry in sources.yaml. Do not remove a watch item without a code change.")


def classify(row):
    """Return one status for a row from fetch_sources.main."""
    if row["distribution"] == "exclude-local-evidence":
        return "skipped-local-evidence"
    if row["fetch_error"]:
        return "fetch-error"
    if row["magic_status"] == "mismatch":
        return "magic-mismatch"
    return row["hash_status"]


def action_for(status, binding):
    """Return the action text for a status, or None when no action is needed."""
    if status in ("changed", "candidate", "magic-mismatch"):
        return ACTION_CHANGED.format(profile=binding or FALLBACK_PROFILE)
    if status == "fetch-error":
        return ACTION_FETCH
    return None


def build_report(code, fs_report, entries, watch, selected, now, manifest_bytes):
    """Return the report as a mapping. It holds hashes and statuses, and no page text."""
    meta = {row["id"]: row for row in entries}
    rows = []
    for row in fs_report["entries"]:
        spec = meta[row["id"]]
        status = classify(row)
        rows.append({
            "id": row["id"],
            "url": spec["url"],
            "retrieved": spec["retrieved"],
            "recorded_sha256": spec["sha256"],
            "observed_sha256": row.get("observed_sha256"),
            "candidate_sha256": row.get("candidate_sha256"),
            "magic_status": row["magic_status"],
            "status": status,
            "profile_binding": spec["profile_binding"],
            "fetch_error": row["fetch_error"],
            "action": action_for(status, spec["profile_binding"]),
        })
    by_id = {row["id"]: row for row in rows}
    watch_rows = []
    for item in watch:
        ident = item["entry"]
        status = "not-selected" if selected and ident not in selected else by_id[ident]["status"]
        watch_rows.append({"entry": ident, "since": item["since"], "note": item["note"], "status": status})
    return {
        "schema": REPORT_SCHEMA,
        "schema_version": REPORT_VERSION,
        "run_utc": now.astimezone(datetime.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "manifest_sha256": hashlib.sha256(manifest_bytes).hexdigest(),
        "overall": fs_report["overall"],
        "exit": code,
        "entries": rows,
        "watch": watch_rows,
        "actions": sorted({row["action"] for row in rows if row["action"]}),
    }


def _cell(value):
    """Return a table cell text. A missing value is a dash. A bar is escaped."""
    if value is None or value == "":
        return "-"
    return str(value).replace("|", "\\|")


def render_markdown(report):
    """Return the report as Markdown. The text has the run time, the entries, the watch items and the actions."""
    lines = [
        "# Source re-check",
        "",
        f"Run (UTC): {report['run_utc']}",
        f"Manifest SHA-256: {report['manifest_sha256']}",
        f"Overall: {report['overall']}",
        f"Exit code: {report['exit']}",
        "",
        "## Entries",
        "",
        "| Entry | Status | Recorded SHA-256 | Observed SHA-256 | Magic | Fetch error |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for row in report["entries"]:
        observed = row["observed_sha256"] or row["candidate_sha256"]
        lines.append("| " + " | ".join(_cell(v) for v in (
            row["id"], row["status"], row["recorded_sha256"], observed, row["magic_status"], row["fetch_error"]))
            + " |")
    lines += ["", "## Watch items", "", "| Entry | Since | Status | What to examine |", "| --- | --- | --- | --- |"]
    for item in report["watch"]:
        lines.append("| " + " | ".join(_cell(v) for v in (
            item["entry"], item["since"], item["status"], item["note"])) + " |")
    lines += ["", "## Actions", ""]
    if report["actions"]:
        lines += [f"{number}. {text}" for number, text in enumerate(report["actions"], 1)]
    else:
        lines.append("No action. Each fetched page matches the recorded hash.")
    return "\n".join(lines) + "\n"


def render_json(report):
    """Return the report as JSON text with sorted keys."""
    return json.dumps(report, indent=2, sort_keys=True) + "\n"


def main(argv, fetch=None, environ=None, now=None, watch=None):
    """Run the re-check. Return (exit status, text). The text is the report, or an error message for status 2.

    The fetch function defaults to fetch_sources.default_fetch, read at call time. Tests inject their own.
    The watch list defaults to WATCH_ITEMS. Tests on fixture manifests pass an empty list.
    The command never passes a destination to fetch_sources, and always runs it in check-only mode."""
    env = os.environ if environ is None else environ
    stamp = now if now is not None else datetime.datetime.now(datetime.timezone.utc)
    watch = WATCH_ITEMS if watch is None else watch
    try:
        args = parse_args(argv)
    except _ArgumentError as err:
        return EXIT_ARGS, f"recheck_sources.py: the arguments are not valid: {err}. Run the command with --help."
    except SystemExit:  # the --help option. argparse has printed the help text.
        return EXIT_OK, ""
    if env.get("CI") and not args.allow_ci:
        return EXIT_ARGS, CI_REFUSAL
    manifest = pathlib.Path(args.manifest)
    try:
        data = FS.load_manifest(manifest)
    except FS.Refused as err:
        return EXIT_ARGS, f"recheck_sources.py: {err}"
    missing = check_watch(data["sources"], watch)
    if missing:
        return EXIT_ARGS, missing  # checked before the first fetch, so no page is requested
    fs_argv = ["--manifest", args.manifest, "--check-only"]
    for ident in args.entry:
        fs_argv += ["--entry", ident]
    code, fs_report = FS.main(fs_argv, fetch=FS.default_fetch if fetch is None else fetch)
    if code == EXIT_ARGS:
        return EXIT_ARGS, f"recheck_sources.py: {fs_report.get('error', 'the run was refused')}"
    report = build_report(code, fs_report, data["sources"], watch, args.entry, stamp, manifest.read_bytes())
    text = render_json(report) if args.format == "json" else render_markdown(report)
    return code, text


if __name__ == "__main__":
    status, output = main(sys.argv[1:])
    if status == EXIT_ARGS:
        print(output, file=sys.stderr)
    elif output:
        sys.stdout.write(output)
    sys.exit(status)
