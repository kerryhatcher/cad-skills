# /// script
# requires-python = ">=3.10"
# dependencies = ["pyyaml==6.0.3"]
# ///
"""Release packaging inventory and exclusion checks for supplier evidence. Local only.

Authority: the supplier-profile content and evidence hashes and the source-review record bind the
supplier data. The manifests in this repository name URLs and expected hashes. They do not approve
anything. A changed hash needs a new recorded review and a profile binding. It is not accepted
automatically.

Findings, one per defect. Each finding has a code, a file and a message:

- D-1 a stored supplier source has no manifest entry.
- D-2 a manifest entry lacks a required field.
- D-3 a full supplier copy is in the distributed set.
- D-4 local evidence is in the distributed set.
- D-5 a changed hash has no recorded review and profile binding.
- D-6 a supplier file is in the distributed set and not on the allowlist.
- D-7 a fixture holds the bytes of a supplier source.
- D-8 the file magic does not match the recorded magic value. Magic identifies the format only.
- D-9 a profile binding escapes its manifest directory or uses a symbolic link. The checker refuses it before any read.
- R-regression a distributed file matches an excluded pattern.
"""

from __future__ import annotations

import fnmatch
from pathlib import Path

import yaml

from common import sha256_file

REQUIRED_FIELDS = ("id", "path", "retrieved", "sha256", "content_type", "license_state",
                   "distribution_decision")
# Document types whose format must be checked. A null magic value is refused for these (P-6).
MAGIC_REQUIRED_TYPES = {"text/html", "application/pdf",
                        "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                        "application/vnd.ms-excel"}
# The OLE2 signature contains eight bytes. The parser compares the file prefix with this signature.
OLE2_PREFIX = bytes.fromhex("d0cf11e0a1b11ae1")
EXCLUDE_DECISIONS = {"exclude-full-copy", "exclude-local-evidence"}
SKILLS_ROOT = "skills"


def _is_supplier_path(rel: str) -> bool:
    """A path under any skill's supplier directory, or under the Sierra evidence directory."""
    parts = Path(rel).parts
    skill_source = len(parts) >= 4 and parts[0] == "skills" and parts[2] == "supplier"
    return skill_source or rel.startswith("docs/reviews/sierra-source-evidence/")


def merged_distribution(root: Path, distribution: dict) -> dict:
    """Add every skill-level source entry to the repository-level list, with repository paths.

    A skill-level manifest lives in its skill directory. Its paths are relative to that directory.
    """
    merged = {**distribution, "sources": list(distribution.get("sources", []))}
    for manifest in sorted(Path(root).glob(f"{SKILLS_ROOT}/*/sources.yaml")):
        base = manifest.parent.relative_to(root).as_posix()
        for entry in load_yaml(manifest).get("sources", []):
            merged["sources"].append({**entry, "path": f"{base}/{entry['path']}"})
    return merged


def finding(code: str, file: str, message: str) -> dict:
    return {"code": code, "file": file, "message": message}


def load_yaml(path: Path) -> dict:
    with open(path, encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def _magic_ok(magic: str | None, content: bytes) -> bool:
    if magic is None:
        return True
    if magic == "markup":
        head = content[:4096].lower()
        return b"<html" in head or b"<!doctype" in head or b"<head" in head
    if magic == "%PDF":
        return content.startswith(b"%PDF")
    if magic == "PK\u0003\u0004":
        return content.startswith(b"PK\x03\x04")
    if magic == "OLE2":
        return content.startswith(OLE2_PREFIX)
    return False


def _has_link_component(path: Path) -> bool:
    """Return True when a prefix of the absolute path is a symbolic link."""
    parts = path.absolute().parts
    return any(Path(*parts[:i]).is_symlink() for i in range(1, len(parts) + 1))


def confined_profile(manifest_dir: Path, binding: str) -> Path | None:
    """Return the profile path under the manifest directory, or None when the checker must refuse it.

    The function reads no file. It refuses an absolute binding, a '..' part, a symbolic link in the
    full manifest directory path or in the binding path, and a candidate that resolves outside the
    resolved manifest directory. The caller reads the profile only when a path is returned.
    """
    rel = Path(binding)
    if rel.is_absolute() or ".." in rel.parts or not rel.parts:
        return None
    base = Path(manifest_dir).absolute()
    if _has_link_component(base):
        return None
    candidate = base.joinpath(*rel.parts)
    if _has_link_component(candidate):
        return None
    if not candidate.resolve().is_relative_to(base.resolve()):
        return None
    return candidate


def check_entries(root: Path, manifest_dir: Path, manifest: dict, manifest_name: str) -> list[dict]:
    """Check the fields, the hashes, the profile binding and the magic of each entry."""
    findings: list[dict] = []
    for entry in manifest.get("sources", []):
        entry_id = entry.get("id", "<no id>")
        for field in REQUIRED_FIELDS:
            if entry.get(field) in (None, ""):
                findings.append(finding("D-2", manifest_name, f"{entry_id} lacks field {field}"))
        if "magic" not in entry:
            findings.append(finding("D-2", manifest_name, f"{entry_id} lacks the magic key (null is allowed)"))
        elif entry.get("magic") is None and entry.get("content_type") in MAGIC_REQUIRED_TYPES:
            # P-6. A null magic value would disable the format check for a document type.
            findings.append(finding("D-8", entry.get("path", ""),
                                    f"magic null is not allowed for {entry.get('content_type')}"))
        if entry.get("url") in (None, "") and not entry.get("url_state"):
            findings.append(finding("D-2", manifest_name, f"{entry_id} has neither url nor url_state"))
        path = manifest_dir / entry.get("path", "")
        if not path.is_file():
            findings.append(finding("D-2", manifest_name, f"{entry_id} points to a missing file"))
            continue
        actual = sha256_file(path)
        if actual != entry.get("sha256"):
            findings.append(finding("D-5", entry.get("path", ""),
                                    "changed bytes need a new recorded review and profile binding"))
        binding = entry.get("profile_binding")
        if binding:
            profile = confined_profile(Path(manifest_dir), binding)
            if profile is None:
                findings.append(finding("D-9", binding, "The profile binding escapes its manifest directory or uses a symbolic link."))
            elif not profile.is_file():
                findings.append(finding("D-5", binding, "profile binding file is missing"))
            else:
                bound = load_yaml(profile).get("evidence_sha256")
                if bound != entry.get("sha256"):
                    findings.append(finding("D-5", binding, "profile evidence hash differs from the source hash"))
        if not _magic_ok(entry.get("magic"), path.read_bytes()):
            findings.append(finding("D-8", entry.get("path", ""),
                                    "file magic does not match the recorded magic value"))
    return findings


def supplier_sources(root: Path, distribution: dict) -> list[str]:
    """Stored supplier sources on disk, as repository-relative paths.

    Allowlisted probes and manifests are not supplier sources. Every other file under a
    supplier directory is one.
    """
    allowlist = distribution.get("allowlist", [])
    found = []
    for path in sorted(Path(root).glob("skills/*/supplier/**/*")):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            if not _allowed(rel, allowlist):
                found.append(rel)
    for path in sorted(Path(root).glob("docs/reviews/sierra-source-evidence/*")):
        if path.is_file():
            rel = path.relative_to(root).as_posix()
            if not _allowed(rel, allowlist):
                found.append(rel)
    return found


def _allowed(rel: str, allowlist) -> bool:
    return any(fnmatch.fnmatch(rel, pattern) for pattern in allowlist)


def check_coverage(root: Path, distribution: dict, entry_paths: set[str]) -> list[dict]:
    """D-1: each stored supplier source must have a manifest entry."""
    return [finding("D-1", rel, "stored supplier source has no manifest entry")
            for rel in supplier_sources(root, distribution) if rel not in entry_paths]


def build_distribution(tracked: list[str], distribution: dict) -> tuple[list[str], list[str]]:
    """Return (distributed, excluded) for a candidate list of tracked files.

    A file is excluded when an entry marks it as full copy or local evidence, or when it matches a
    regression pattern. Every other file stays in the distributed set. The findings check that set.
    """
    exclude_paths = {e["path"] for e in distribution.get("sources", [])
                     if e.get("distribution_decision") in EXCLUDE_DECISIONS}
    patterns = distribution.get("excluded_patterns", [])
    distributed, excluded = [], []
    for rel in tracked:
        if rel in exclude_paths or any(fnmatch.fnmatch(rel, p) for p in patterns):
            excluded.append(rel)
        else:
            distributed.append(rel)
    return distributed, excluded


def check_distribution(distributed: list[str], distribution: dict, root: Path | None = None) -> list[dict]:
    """Check the distributed set against the decisions, the allowlist, the patterns and the bytes.

    With a root, each distributed file is hashed. Its bytes are compared with the excluded hashes.
    A copy at an unrelated path is caught this way (P-7). Paths alone are not enough.
    """
    findings: list[dict] = []
    allowlist = distribution.get("allowlist", [])
    patterns = distribution.get("excluded_patterns", [])
    decisions = {e["path"]: e.get("distribution_decision") for e in distribution.get("sources", [])}
    excluded_hashes = {e["sha256"]: e.get("distribution_decision") for e in distribution.get("sources", [])
                       if e.get("distribution_decision") in EXCLUDE_DECISIONS and e.get("sha256")}
    for rel in distributed:
        if root is not None and (Path(root) / rel).is_file():
            digest = sha256_file(Path(root) / rel)
            decision = excluded_hashes.get(digest)
            if decision == "exclude-full-copy":
                findings.append(finding("D-3", rel, "distributed bytes match a full-copy hash"))
            elif decision == "exclude-local-evidence":
                findings.append(finding("D-4", rel, "distributed bytes match a local evidence hash"))
        decision = decisions.get(rel)
        if decision == "exclude-full-copy":
            findings.append(finding("D-3", rel, "full supplier copy is in the distributed set"))
        elif decision == "exclude-local-evidence":
            findings.append(finding("D-4", rel, "local evidence is in the distributed set"))
        if _is_supplier_path(rel) and not _allowed(rel, allowlist):
            findings.append(finding("D-6", rel, "supplier file is not on the allowlist"))
        if any(fnmatch.fnmatch(rel, p) for p in patterns):
            findings.append(finding("R-regression", rel, "distributed file matches an excluded pattern"))
    return findings


def check_fixtures(root: Path, fixture_dirs: list[str], entry_hashes: set[str]) -> list[dict]:
    """D-7: a fixture must not hold the bytes of any supplier source."""
    findings = []
    for directory in fixture_dirs:
        for path in sorted((Path(root) / directory).rglob("*")):
            if path.is_file() and sha256_file(path) in entry_hashes:
                findings.append(finding("D-7", path.relative_to(root).as_posix(),
                                        "fixture holds the bytes of a supplier source"))
    return findings
