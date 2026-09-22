#!/usr/bin/env python3
"""Push the whole kit to your profile repo WITHOUT git installed.

    export GH_TOKEN=github_pat_...        # fine-grained PAT, see below
    python3 tools/upload_via_api.py

Fine-grained token: github.com/settings/personal-access-tokens/new
  ▸ Resource owner: JayxCodemax   ▸ Repository: only "JayxCodemax/JayxCodemax"
  ▸ Permissions → Contents: Read and write     (nothing else)
It commits every file in one atomic commit, so the page never renders half-loaded.
"""
import base64
import json
import os
import pathlib
import sys
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parent.parent
REPO = os.environ.get("REPO", "JayxCodemax/JayxCodemax")
BRANCH = os.environ.get("BRANCH", "main")
TOKEN = os.environ.get("GH_TOKEN") or os.environ.get("GITHUB_TOKEN")
SKIP = {"preview.html", "draft-original.md"}          # local-only files


def api(path, data=None, method=None):
    req = urllib.request.Request(
        f"https://api.github.com{path}", data=json.dumps(data).encode() if data else None,
        method=method or ("POST" if data else "GET"),
        headers={"Authorization": f"Bearer {TOKEN}", "Accept": "application/vnd.github+json",
                 "User-Agent": "profile-upload",
                 "Content-Type": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=40) as r:
            raw = r.read()
            return json.loads(raw) if raw else {}
    except urllib.error.HTTPError as e:
        sys.exit(f"HTTP {e.code} on {path}\n{e.read().decode()[:400]}")


def main() -> None:
    if not TOKEN:
        sys.exit("Set GH_TOKEN first (fine-grained PAT with Contents: read+write on one repo).")

    me = api("/user")["login"]
    head = api(f"/repos/{REPO}/git/ref/heads/{BRANCH}")["object"]["sha"]
    print(f"authed as {me} · {REPO}@{BRANCH} head {head[:8]}")

    actions = []
    for f in sorted(p for p in ROOT.rglob("*") if p.is_file()):
        rel = f.relative_to(ROOT).as_posix()
        if rel in SKIP or "__pycache__" in rel:
            continue
        try:
            content = base64.b64encode(f.read_bytes()).decode()
        except Exception as exc:
            sys.exit(f"{rel}: {exc}")
        entry = {"action": "update", "path": rel, "content": content}
        try:
            entry["sha"] = api(f"/repos/{REPO}/contents/{rel}?ref={BRANCH}")["sha"]
        except SystemExit:
            entry["action"] = "create"
        actions.append(entry)
        print(f"  {entry['action']:6s} {rel}")

    tree = api(f"/repos/{REPO}/git/trees", {"base_tree": head, "tree": actions})["sha"]
    commit = api(f"/repos/{REPO}/git/commits", {
        "message": "profile: animated README kit (banner, skill bars, counters, workflows)",
        "parents": [head], "tree": tree})
    api(f"/repos/{REPO}/git/ref/heads/{BRANCH}", {"sha": commit["sha"]}, method="PATCH")
    print(f"\n✅ pushed commit {commit['sha'][:8]} → https://github.com/{me}")


if __name__ == "__main__":
    main()
