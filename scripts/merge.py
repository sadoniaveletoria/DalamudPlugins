"""Builds pluginmaster.json from every plugin's own repo.json listed in sources.txt.

A source that can't be fetched (a new repo with no repo.json yet, GitHub hiccup) keeps whatever that plugin had in
the previous pluginmaster.json, so one bad fetch never drops a plugin from the list.
"""
import json
import os
import re
import sys
import urllib.request
from pathlib import Path


def gh_json(url):
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json", "User-Agent": "plugin-list-builder"})
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        req.add_header("Authorization", f"Bearer {token}")
    with urllib.request.urlopen(req, timeout=30) as r:
        return json.loads(r.read().decode("utf-8"))


def fetch_repo_json(url):
    """
    A plugin's repo.json. raw.githubusercontent.com links are read through the GitHub API instead, because the raw
    CDN caches for ~5 minutes: right after a release (when this job is triggered) it would still serve the old version.
    """
    m = re.match(r"https://raw\.githubusercontent\.com/([^/]+)/([^/]+)/([^/]+)/(.+)$", url)
    if m:
        owner, repo, ref, path = m.groups()
        req = urllib.request.Request(f"https://api.github.com/repos/{owner}/{repo}/contents/{path}?ref={ref}",
                                     headers={"Accept": "application/vnd.github.raw+json", "User-Agent": "plugin-list-builder"})
        token = os.environ.get("GITHUB_TOKEN")
        if token:
            req.add_header("Authorization", f"Bearer {token}")
    else:
        req = urllib.request.Request(url, headers={"User-Agent": "plugin-list-builder"})
    with urllib.request.urlopen(req, timeout=30) as r:
        entries = json.loads(r.read().decode("utf-8-sig"))
    return entries


def same_version(tag, version):
    """v0.0.5 matches 0.0.5.0; v1.11.0.0 matches 1.11.0.0."""
    a = [int(x) for x in re.findall(r"\d+", tag)]
    b = [int(x) for x in re.findall(r"\d+", version)]
    n = max(len(a), len(b))
    return a + [0] * (n - len(a)) == b + [0] * (n - len(b))


def pin_downloads(entry):
    """
    Point the download links at the release whose tag matches the listed AssemblyVersion, instead of "latest".
    Dalamud refuses an install when the file's version differs from the listed one, and the list is cached for a
    while — so with "latest" links, a new release breaks installs until every cache refreshes.
    """
    link = entry.get("DownloadLinkInstall", "")
    m = re.match(r"https://github\.com/([^/]+)/([^/]+)/releases/latest/download/(.+)$", link)
    if not m:
        return
    owner, repo, asset = m.groups()
    try:
        releases = gh_json(f"https://api.github.com/repos/{owner}/{repo}/releases?per_page=50")
    except Exception as ex:
        print(f"     {entry['InternalName']}: couldn't read releases ({ex}); keeping latest links", file=sys.stderr)
        return
    for rel in releases:
        if rel.get("draft") or not same_version(rel["tag_name"], entry.get("AssemblyVersion", "")):
            continue
        names = {a["name"]: a["browser_download_url"] for a in rel.get("assets", [])}
        url = names.get(asset) or next(iter(names.values()), None)
        if url:
            for k in ("DownloadLinkInstall", "DownloadLinkUpdate", "DownloadLinkTesting"):
                entry[k] = url
            print(f"     {entry['InternalName']} {entry['AssemblyVersion']} -> {rel['tag_name']}")
        return
    print(f"     {entry['InternalName']}: no release for {entry.get('AssemblyVersion')}; keeping latest links", file=sys.stderr)

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
        entries = fetch_repo_json(url)
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
        pin_downloads(e)
        merged.append(e)

merged.sort(key=lambda p: p.get("Name", p["InternalName"]).lower())
out.write_text(json.dumps(merged, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
print(f"{len(merged)} plugin(s) in pluginmaster.json")
