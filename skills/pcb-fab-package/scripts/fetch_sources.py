# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///

"""Retrieve the source pages named by a sources.yaml manifest.

The manifest root is the parent directory of the manifest. Each entry writes to DIR/<path>. A write needs DIR to
resolve to the manifest root. A profile binding names a profile under supplier/profiles. It never names a destination.

Validation runs on every selected entry before the first fetch. A failure exits 2 and fetches nothing.
Exit precedence: validation 2, then a fetch or write failure 3, then a candidate, changed, text or magic mismatch 1,
then 0 (a match or a layout change).
The command never edits the manifest, a profile, or a file that a changed outcome would replace.
"""
import argparse
import datetime
import hashlib
import html.parser
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import validate as VAL  # noqa: E402
import project_io as PIO  # noqa: E402

EXIT_OK, EXIT_FAIL, EXIT_ARGS, EXIT_TOOL = 0, 1, 2, 3
SCHEMA = "cad-skills/sources"
SCHEMA_VERSION = 1
TOP_KEYS = {"schema", "schema_version", "sources"}
ENTRY_KEYS = {"id", "path", "url", "retrieved", "sha256", "content_type", "magic", "license_state",
              "distribution_decision", "profile_binding"}
# The optional key text_sha256 holds the SHA-256 of the visible page text. The byte sha256 stays the binding evidence.
OPTIONAL_ENTRY_KEYS = {"text_sha256"}
# The text in these elements is not visible page text.
HIDDEN_TEXT_TAGS = frozenset({"script", "style", "noscript"})
TEXT_KEYS = ("id", "path", "url", "retrieved", "content_type", "license_state", "distribution_decision")
DISTRIBUTION = ("exclude-full-copy", "exclude-local-evidence")
# The exact release tokens. The fourth token is written with a literal backslash in the YAML text.
MAGIC_TOKENS = ("markup", "%PDF", r"PK\u0003\u0004", "OLE2")
OLE2_SIGNATURE = bytes.fromhex("D0CF11E0A1B11AE1")
TIMEOUT_SECONDS = 30
USER_AGENT = "cad-skills-fetch/1"


class Refused(Exception):
    """A validation or argument defect. Nothing is fetched or written."""


class FetchFailed(Exception):
    """A network error, a timeout, a redirect or a non-2xx response."""


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    """Do not follow a redirect. The 3xx response becomes an HTTPError."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def default_fetch(url):
    """Fetch one URL with one GET, no credentials and no redirect. Return the response bytes."""
    opener = urllib.request.build_opener(_NoRedirect)
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with opener.open(request, timeout=TIMEOUT_SECONDS) as response:
            status = response.status
            if not 200 <= status <= 299:
                raise FetchFailed(f"HTTP {status}")
            return response.read()
    except urllib.error.HTTPError as err:
        raise FetchFailed(f"HTTP {err.code}") from err
    except (urllib.error.URLError, OSError) as err:
        raise FetchFailed(str(err)) from err


def magic_status(token, data):
    """Return ok, mismatch, or not-tested for the bytes and the entry magic token."""
    if token is None:
        return "not-tested"
    if token == "markup":
        ok = data.lstrip()[:1] == b"<"
    elif token == "%PDF":
        ok = data.startswith(b"%PDF")
    elif token == r"PK\u0003\u0004":
        ok = data.startswith(b"PK\x03\x04")
    else:  # OLE2
        ok = data.startswith(OLE2_SIGNATURE)
    return "ok" if ok else "mismatch"


class _VisibleText(html.parser.HTMLParser):
    """Collect the visible page text. Each tag, removed element, comment, doctype, processing
    instruction and CDATA section becomes one space."""

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts = []
        self.hidden = 0

    def handle_starttag(self, tag, attrs):
        if tag in HIDDEN_TEXT_TAGS:
            self.hidden += 1
        self.parts.append(" ")

    def handle_endtag(self, tag):
        if tag in HIDDEN_TEXT_TAGS and self.hidden:
            self.hidden -= 1
        self.parts.append(" ")

    def handle_comment(self, data):
        self.parts.append(" ")

    def handle_decl(self, decl):
        self.parts.append(" ")

    def handle_pi(self, data):
        self.parts.append(" ")

    def unknown_decl(self, data):
        self.parts.append(" ")

    def handle_data(self, data):
        if self.hidden == 0:
            self.parts.append(data)


def visible_text(data):
    """Return the visible page text of the bytes.

    Replace each tag, doctype, processing instruction, CDATA section, removed script, style and noscript
    element, and comment, with one space. Their text is not visible page text. Decode HTML entities.
    Collapse each run of whitespace to one space. Remove the whitespace at the two ends. Remove one leading
    U+FEFF before the rule. Decode the bytes as strict UTF-8 and raise UnicodeDecodeError for bytes that
    are not UTF-8.
    """
    parser = _VisibleText()
    text = data.decode("utf-8")
    if text.startswith("\ufeff"):
        text = text[1:]  # one leading U+FEFF is a byte order mark, not page text
    parser.feed(text)
    parser.close()
    return " ".join("".join(parser.parts).split())


def text_sha256(data):
    """Return the SHA-256 of the visible page text, or None when the bytes are not UTF-8."""
    try:
        text = visible_text(data)
    except UnicodeDecodeError:
        return None
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def refuse_links(root, rel):
    """Refuse a link on any component of root/rel, before any read or write."""
    current = root
    for part in pathlib.PurePosixPath(rel).parts:
        current = current / part
        if os.path.islink(current):
            raise Refused(f"{rel} contains a symbolic link at {part}; nothing is read or written")


def check_shape(entry, index):
    """Check one entry's keys, types and values. Raise Refused for a defect."""
    if not isinstance(entry, dict):
        raise Refused(f"entry {index} is not a mapping")
    missing = sorted(ENTRY_KEYS - set(entry))
    unknown = sorted(set(entry) - ENTRY_KEYS - OPTIONAL_ENTRY_KEYS)
    if missing or unknown:
        raise Refused(f"entry {index} has missing keys {missing} or unknown keys {unknown}")
    ident = entry["id"]
    for key in TEXT_KEYS:
        if not isinstance(entry[key], str) or not entry[key]:
            raise Refused(f"entry {ident}: {key} must be a non-empty string")
    sha = entry["sha256"]
    if sha is not None and not (isinstance(sha, str) and re.fullmatch(r"[0-9a-f]{64}", sha)):
        raise Refused(f"entry {ident}: sha256 must be 64 lowercase hexadecimal characters or null")
    if "text_sha256" in entry:
        text = entry["text_sha256"]
        if not (isinstance(text, str) and re.fullmatch(r"[0-9a-f]{64}", text)):
            raise Refused(f"entry {ident}: text_sha256 must be 64 lowercase hexadecimal characters")
        if entry["magic"] != "markup":
            raise Refused(f"entry {ident}: an entry with text_sha256 must have the magic token markup")
        if sha is None:
            raise Refused(f"entry {ident}: an entry with text_sha256 must have a sha256 value")
    if entry["magic"] is not None and entry["magic"] not in MAGIC_TOKENS:
        raise Refused(f"entry {ident}: magic {entry['magic']!r} is not an allowed token")
    if entry["distribution_decision"] not in DISTRIBUTION:
        raise Refused(f"entry {ident}: distribution_decision {entry['distribution_decision']!r} is not allowed")
    try:
        if len(entry["retrieved"]) != 10:
            raise ValueError
        datetime.date.fromisoformat(entry["retrieved"])
    except ValueError as err:
        raise Refused(f"entry {ident}: retrieved must be a real date YYYY-MM-DD") from err
    url = urllib.parse.urlsplit(entry["url"])
    if url.scheme != "https" or not url.netloc:
        raise Refused(f"entry {ident}: url must use https")
    rel = pathlib.PurePosixPath(entry["path"])
    if entry["path"].startswith("/") or rel.is_absolute() or ".." in rel.parts or "\\" in entry["path"]:
        raise Refused(f"entry {ident}: path must be relative and contain no .. segment")
    binding = entry["profile_binding"]
    if binding is not None:
        if not isinstance(binding, str):
            raise Refused(f"entry {ident}: profile_binding must be a string or null")
        bparts = pathlib.PurePosixPath(binding).parts
        if binding.startswith("/") or ".." in bparts or len(bparts) != 3 or bparts[:2] != ("supplier", "profiles") \
                or not binding.endswith(".yaml"):
            raise Refused(f"entry {ident}: profile_binding must be supplier/profiles/<name>.yaml")
        if not entry["path"].startswith("supplier/pages/") or not entry["path"].endswith(".html"):
            raise Refused(f"entry {ident}: a bound page must be under supplier/pages/ and end in .html")
    return entry


def check_binding(root, entry):
    """Confine the profile, read it only after the checks, and compare its page evidence with the entry.

    Refuse a link on any component, a resolved path outside supplier/profiles, a missing page key, or a hash
    difference. The profile is never written."""
    binding = entry["profile_binding"]
    refuse_links(root, binding)
    profile_path = root / binding
    profiles_dir = (root / "supplier" / "profiles").resolve()
    resolved = profile_path.resolve()
    if not resolved.is_relative_to(profiles_dir):
        raise Refused(f"entry {entry['id']}: the profile resolves outside supplier/profiles")
    if not profile_path.is_file():
        raise Refused(f"entry {entry['id']}: the profile {binding} is missing")
    try:
        profile = VAL.parse_record(profile_path.read_bytes(), ".yaml", binding)
        pages = profile["extensions"]["evidence_pages"]
    except (VAL.RecordError, KeyError, TypeError) as err:
        raise Refused(f"entry {entry['id']}: the profile has no evidence_pages") from err
    stem = pathlib.PurePosixPath(entry["path"]).stem
    if stem not in pages:
        raise Refused(f"entry {entry['id']}: page {stem} is not in the profile evidence_pages")
    if entry["sha256"] is not None and pages[stem].get("sha256") != entry["sha256"]:
        raise Refused(f"entry {entry['id']}: the manifest sha256 differs from the profile evidence hash")


def load_manifest(manifest):
    """Parse the manifest and check its top-level schema. Return the parsed mapping."""
    try:
        data = VAL.parse_record(manifest.read_bytes(), ".yaml", str(manifest))
    except (OSError, VAL.RecordError) as err:
        raise Refused(f"the manifest is not a valid record: {err}") from err
    if not isinstance(data, dict) or set(data) != TOP_KEYS:
        raise Refused("the manifest top level must have exactly the keys schema, schema_version and sources")
    if data["schema"] != SCHEMA or type(data["schema_version"]) is not int or data["schema_version"] != SCHEMA_VERSION:
        raise Refused("the manifest schema or schema_version is not cad-skills/sources version 1")
    if not isinstance(data["sources"], list) or not data["sources"]:
        raise Refused("the manifest has no entries")
    return data


def refuse_protected_alias(root, entry, protected):
    """Refuse a destination that names a protected input, before any fetch.

    Protected inputs are the manifest and every profile_binding path. Refuse a destination under supplier/profiles.
    Refuse a destination that resolves to the same file as a protected input, by path or by hard link."""
    dest = root / entry["path"]
    dest_real = os.path.realpath(dest)
    profiles_dir = os.path.realpath(root / "supplier" / "profiles")
    if dest_real == profiles_dir or dest_real.startswith(profiles_dir + os.sep):
        raise Refused(f"entry {entry['id']}: the destination is under supplier/profiles; nothing is fetched")
    dest_stat = os.stat(dest) if os.path.exists(dest) else None
    for name in protected:
        if dest_real == os.path.realpath(name):
            raise Refused(f"entry {entry['id']}: the destination is the protected input {name}; nothing is fetched")
        if dest_stat is not None and os.path.exists(name):
            other = os.stat(name)
            if (other.st_dev, other.st_ino) == (dest_stat.st_dev, dest_stat.st_ino):
                raise Refused(f"entry {entry['id']}: the destination is a hard link to {name}; nothing is fetched")


def validate(root, manifest, data, selected_ids, write):
    """Check every entry, then the selection and the destinations. Return the entries to process.

    Run the protected-alias check in both modes, before any fetch."""
    entries = [check_shape(entry, index) for index, entry in enumerate(data["sources"])]
    ids = [entry["id"] for entry in entries]
    if len(ids) != len(set(ids)):
        raise Refused("two entries share an id")
    protected = [str(manifest)] + [str(root / entry["profile_binding"]) for entry in entries
                                   if entry["profile_binding"] is not None]
    profile_dir = root / "supplier" / "profiles"
    if os.path.isdir(profile_dir) and not os.path.islink(profile_dir):
        for dirpath, _, names in os.walk(profile_dir):
            protected.extend(os.path.join(dirpath, name) for name in names)
    destinations = {}
    for entry in entries:
        key = os.path.normpath(root / entry["path"])
        if key in destinations:
            raise Refused(f"entries {destinations[key]} and {entry['id']} resolve to the same destination")
        destinations[key] = entry["id"]
        if write:
            refuse_links(root, entry["path"])
        if entry["profile_binding"] is not None:
            check_binding(root, entry)
        refuse_protected_alias(root, entry, protected)
    if selected_ids:
        unknown = [ident for ident in selected_ids if ident not in ids]
        if unknown:
            raise Refused(f"unknown entry id {unknown}")
        entries = [entry for entry in entries if entry["id"] in selected_ids]
    return entries


def main(argv, fetch=default_fetch):
    """Run the command. Return (exit status, report). The report holds the statuses of each entry."""
    parser = argparse.ArgumentParser(prog="fetch_sources.py", description="Retrieve the source pages of a manifest.")
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--dest")
    parser.add_argument("--entry", action="append", default=[])
    parser.add_argument("--check-only", action="store_true")
    try:
        args = parser.parse_args(argv)
    except SystemExit:
        return EXIT_ARGS, {"error": "the arguments are not valid"}
    manifest = pathlib.Path(args.manifest).absolute()
    root = manifest.parent
    write = not args.check_only
    try:
        data = load_manifest(manifest)
        if write and args.dest is not None and pathlib.Path(args.dest).resolve() != root.resolve():
            raise Refused("--dest must resolve to the manifest root for a write")
        entries = validate(root, manifest, data, set(args.entry), write)
    except Refused as err:
        return EXIT_ARGS, {"error": str(err)}
    rows = []
    for entry in entries:
        row = {"id": entry["id"], "path": entry["path"], "distribution": entry["distribution_decision"],
               "hash_status": None, "magic_status": None, "written": False, "write_status": None, "fetch_error": None,
               "text_status": None, "observed_text_sha256": None}
        rows.append(row)
        if entry["distribution_decision"] == "exclude-local-evidence":
            continue  # not fetched, not verified
        try:
            body = fetch(entry["url"])
        except FetchFailed as err:
            row["fetch_error"] = str(err)
            continue
        digest = hashlib.sha256(body).hexdigest()
        if entry["sha256"] is None:
            row["hash_status"] = "candidate"
            row["candidate_sha256"] = digest
        else:
            row["hash_status"] = "match" if digest == entry["sha256"] else "changed"
            row["observed_sha256"] = digest
        if entry["magic"] == "markup":
            row["observed_text_sha256"] = text_sha256(body)
        recorded_text = entry.get("text_sha256")
        if recorded_text is not None:
            row["text_status"] = "match" if row["observed_text_sha256"] == recorded_text else "changed"
            if row["hash_status"] == "changed" and row["text_status"] == "match":
                row["hash_status"] = "layout"  # only the layout changed. Nothing is written.
        row["magic_status"] = magic_status(entry["magic"], body)
        if write and row["hash_status"] == "match" and row["magic_status"] in ("ok", "not-tested"):
            try:
                PIO.atomic_write(root, root / entry["path"], body)
                row["written"] = True
                row["write_status"] = "written"
            except PIO.PostReplaceError as err:
                row["write_status"] = "write-error-after-replace"
                row["written"] = True
                row["error"] = str(err)
            except Exception as err:  # the old bytes stay; the failure is reported
                row["write_status"] = "write-failure"
                row["error"] = str(err)
    fetched = [row for row in rows if row["hash_status"] is not None or row["fetch_error"] is not None]
    failure = any(row["fetch_error"] or row["write_status"] in ("write-failure", "write-error-after-replace") for row in rows)
    nonmatch = any(row["hash_status"] in ("candidate", "changed") or row["magic_status"] == "mismatch"
                   or row["text_status"] == "changed" for row in rows)
    code = EXIT_TOOL if failure else (EXIT_FAIL if nonmatch else EXIT_OK)
    if not fetched:
        overall = "no entry fetched"
    elif any(row["write_status"] == "write-error-after-replace" for row in rows):
        overall = "write error"
    elif not write:
        if nonmatch or failure:
            overall = "not all match"
        else:
            overall = "match or layout" if any(row["hash_status"] == "layout" for row in rows) else "all match"
    else:
        written = [row for row in fetched if row["written"]]
        all_match = all(row["hash_status"] == "match" and row["magic_status"] in ("ok", "not-tested")
                        and row["text_status"] != "changed" for row in fetched)
        overall = "all match" if all_match and len(written) == len(fetched) else (
            "partial" if written else "none written")
    return code, {"overall": overall, "exit": code, "entries": rows}


if __name__ == "__main__":
    status, result = main(sys.argv[1:])
    if "error" in result:
        print(result["error"], file=sys.stderr)
    else:
        print(json.dumps(result, indent=2, sort_keys=True))
    sys.exit(status)
