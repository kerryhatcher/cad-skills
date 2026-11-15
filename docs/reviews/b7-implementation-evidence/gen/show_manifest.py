# /// script
# requires-python = ">=3.10"
# dependencies = []
# ///
"""Print the status, the reasons and the check statuses of a package manifest."""
import json, sys
m = json.load(open(sys.argv[1]))
print("status", m["status"])
print("reasons", m["reasons"])
print("checks", [(c["id"], c["status"]) for c in m["checks"]])
