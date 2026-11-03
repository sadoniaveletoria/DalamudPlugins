"""Builds pluginmaster.json from every plugin's own repo.json listed in sources.txt.

A source that can't be fetched (a new repo with no repo.json yet, GitHub hiccup) keeps whatever that plugin had in
the previous pluginmaster.json, so one bad fetch never drops a plugin from the list.
"""
import json
import sys
import urllib.request
from pathlib import Path

root = Path(__file__).resolve().parent.parent
out = root / "pluginmaster.json"
previous = {}
if out.exists():
    try:
        previous = {p["InternalName"]: p for p in json.loads(out.read_text(encoding="utf-8-sig"))}
    except Exception:
        previous = {}

sources = [l.strip() for l in (root / "sources.txt").read_text().splitlines() if l.strip() and not l.startswith("#")]
merged, seen = [], set()
for url in sources:
    try:
        with urllib.request.urlopen(url, timeout=30) as r:
            entries = json.loads(r.read().decode("utf-8-sig"))
        if isinstance(entries, dict):
            entries = [entries]
        print(f"ok   {url}: {', '.join(e.get('InternalName', '?') for e in entries)}")
    except Exception as ex:
        # Keep the plugin(s) this source had last time.
        owner_repo = url.split("githubusercontent.com/")[-1].split("/")[1].lower()
        entries = [p for p in previous.values() if owner_repo in p.get("RepoUrl", "").lower()]
        print(f"skip {url}: {ex} (kept {len(entries)} from last time)", file=sys.stderr)
    for e in entries:
        name = e.get("InternalName")
        if not name or name in seen:
            continue
        seen.add(name)
        merged.append(e)

merged.sort(key=lambda p: p.get("Name", p["InternalName"]).lower())
out.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"{len(merged)} plugin(s) in pluginmaster.json")
