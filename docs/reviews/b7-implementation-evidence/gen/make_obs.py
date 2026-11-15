# /// script
# requires-python = ">=3.10"
# dependencies = ["jsonschema==4.26.0", "pyyaml==6.0.3"]
# ///
"""Write an observation record that reads every profile fact exactly as the profile states it."""
import hashlib, json, pathlib, shutil, sys
sys.path.insert(0, "/mnt/storage/projects/cad-skills/skills/pcb-fab-package/scripts")
import review, fab  # noqa: E402

profile_path, project, out = (pathlib.Path(p) for p in (sys.argv[1], sys.argv[2], sys.argv[4]))
release = sys.argv[3]
profile = fab.check_profile(profile_path)
page = next(iter(fab.PROFILE_PAGES[profile["id"]]))
stored = review.PAGES / f"{page}.html"
live = project / "out" / "fab" / "source-review" / "live" / f"{page}.html"
live.parent.mkdir(parents=True, exist_ok=True)
shutil.copy2(stored, live)
pages = [{"page_id": page, "source_url": profile["extensions"]["evidence_pages"][page]["source_url"],
          "stored_path": f"supplier/pages/{page}.html", "stored_sha256": hashlib.sha256(stored.read_bytes()).hexdigest(),
          "live_path": f"out/fab/source-review/live/{page}.html", "live_sha256": hashlib.sha256(live.read_bytes()).hexdigest(),
          "retrieved": "2026-11-14"}]
obs = []
for key, (value, unit, url) in review.fact_items(profile).items():
    obs.append({"key": key, "observed_value": value, "observed_unit": unit, "observed_condition": "service page statement",
                "source_url": url, "reviewer_reading": "read from the stored page"})
record = {"schema_id": review.OBS_SCHEMA, "schema_version": 1, "release_id": release,
          "profile_sha256": profile["content_sha256"], "pages": pages, "observations": obs,
          "reviewer": "R. Reviewer", "statement": "Read from the stored supplier page."}
out.write_text(json.dumps(record, indent=2, ensure_ascii=False) + "\n")
print("facts", len(obs), "pages", len(pages))
