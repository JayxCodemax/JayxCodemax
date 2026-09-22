#!/usr/bin/env python3
"""Fill every placeholder in the profile kit from profile.json — in one pass.

    python3 tools/personalize.py            # apply + validate
    python3 tools/personalize.py --check    # validate only (CI-friendly)

It also HTML-escapes values for SVG text, URL-checks nothing you can't fix,
and finishes by regenerating the mini bars and preview.html so what you
validate locally is what renders.
"""
import argparse
import json
import pathlib
import re
import subprocess
import sys
import xml.dom.minidom as minidom
from urllib.parse import quote

ROOT = pathlib.Path(__file__).resolve().parent.parent
# Files that carry {{TOKENS}}. SETUP.md is intentionally excluded (prose, no tokens).
TARGETS = ["README.md", "assets/banner.svg", ".github/workflows/snake.yml",
           ".github/workflows/counters.yml"]
# badges that use shields.io logo= and were verified against simple-icons@latest (Sept 2026)
LOGO_WHITELIST_FILE = ".shields-logos.txt"
PLACEHOLDER = "JAYANT_GITHUB"
# path segments after github.com/ that are never a username
NON_USER_SEGMENTS = {"HEAD", "blob", "tree", "settings", "topics", "about", "features",
                     "enterprise", "issues", "pulls", "discussions", "marketplace", "collections"}


def escape_svg(v: str) -> str:
    return v.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def load() -> dict:
    raw = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
    out = {k: v for k, v in raw.items() if not k.startswith("_")}
    out.setdefault("LOCATION_URL", quote(out["LOCATION"], safe="· "))
    out.setdefault("EMAIL_URL", out["EMAIL"].replace("@", "%40"))
    return out


def apply(values: dict) -> list[str]:
    """Substitute every {{TOKEN}}. A still-placeholder USERNAME is left as the
    token itself, so files stay valid YAML/Markdown until it is filled."""
    if values.get("USERNAME") == PLACEHOLDER:
        values = {**values, "USERNAME": "{{USERNAME}}"}
    changed = []
    for rel in TARGETS:
        p = ROOT / rel
        if not p.exists():
            continue
        text = original = p.read_text(encoding="utf-8")
        for key, val in values.items():
            text = re.sub(r"\{\{\s*%s\s*\}\}" % key, val, text)
            text = re.sub(r"\{\{\s*%s:svg\s*\}\}" % key, escape_svg(val), text)
        # SVG / YAML targets must not receive raw "&" from names like "A & B"
        if rel.endswith(".svg"):
            for key, val in values.items():
                text = text.replace(val, escape_svg(val))
        if text != original:
            p.write_text(text, encoding="utf-8")
            changed.append(rel)
    return changed


def validate(values: dict) -> list[str]:
    problems = []
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    # ignore what a reader never sees: fenced code blocks and HTML comments
    visible = re.sub(r"```.*?```", "", readme, flags=re.S)
    visible = re.sub(r"<!--.*?-->", "", visible, flags=re.S)

    left = sorted(set(re.findall(r"\{\{\s*[A-Z_]+\s*\}\}", readme)))
    for rel in TARGETS:
        p = ROOT / rel
        if not p.exists():
            continue
        t = p.read_text(encoding="utf-8")
        if PLACEHOLDER in t:
            problems.append(f"{rel}: still contains the sentinel handle JAYANT_GITHUB")
        refs = [r for r in re.findall(r"(?:github\.com/|username=|user=)([A-Za-z0-9_\-.]+)", t)
                if r not in NON_USER_SEGMENTS]
        refs = [r for r in refs if not re.search(r"[<>{}]|^(you|your|example|someone)$", r, re.I)]
        if refs and "{{USERNAME}}" not in t and values["USERNAME"] not in refs:
            problems.append(f"{rel}: has username-shaped links but none point at {values['USERNAME']!r} — re-run personalize.py")
    if left:
        problems.append(f"unfilled placeholders in README.md: {left}")

    for name in ["YOUR_USERNAME", "YOUR_LINKEDIN", "you@example.com", "YOUR NAME"]:
        if name in readme:
            problems.append(f"leftover template token {name!r} in README.md")

    if not re.fullmatch(r"[A-Za-z0-9](?:[A-Za-z0-9]|-(?=[A-Za-z0-9])){0,38}", str(values.get("USERNAME", ""))):
        problems.append("profile.json → USERNAME is not a valid GitHub login (2-39 chars, "
                      "letters/digits/hyphens); every stat card and link will 404")

    # every local asset referenced must exist
    for ref in sorted(set(re.findall(r'(?:src|href)="((?!https?:|#|mailto:)[^"]+)"', visible))):
        if not (ROOT / ref).exists():
            problems.append(f"broken local reference in README.md: {ref}")

    # shields.io logos: catch typos before they become grey "invalid" badges
    allowed = None
    wl = ROOT / LOGO_WHITELIST_FILE
    if wl.exists():
        allowed = {l.strip() for l in wl.read_text().splitlines() if l.strip()}
    used = sorted(set(re.findall(r"[?&]logo=([A-Za-z0-9_\-]+)", readme)))
    for slug in used:
        if allowed is not None and slug not in allowed:
            problems.append(f"unverified shields.io logo slug: {slug}")

    # SVG well-formedness (minidom is strict about entities)
    for svg in sorted((ROOT / "assets").glob("*.svg")):
        try:
            minidom.parse(svg.as_posix())
        except Exception as exc:
            problems.append(f"invalid SVG {svg.name}: {exc}")

    # unbalanced tags silently mangle the GitHub render. Count what GitHub actually
    # renders (comments stripped), then separately make sure every comment is closed —
    # a "<!--" nested inside a comment closes it early and leaks raw HTML on the page.
    for tag in ("details", "table", "p", "a"):
        o, c = len(re.findall(rf"<{tag}[\s>]", visible)), len(re.findall(rf"</{tag}>", visible))
        if o != c:
            problems.append(f"tag <{tag}> unbalanced in README.md: {o} open / {c} close (visible markup)")
    for opener, closer in (("<!--", "-->"), ("```", "```")):
        n = len(re.findall(re.escape(opener), readme))
        if closer == opener:
            if n % 2:
                problems.append(f"unbalanced {opener!r} fences in README.md: {n}")
        elif n != len(re.findall(re.escape(closer), readme)):
            problems.append(f"unbalanced comment markers in README.md: {n} openers / "
                            f"{len(re.findall(re.escape(closer), readme))} closers "
                            "(a nested '<!--' inside a comment breaks it)")

    return problems


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="validate without writing")
    ap.add_argument("--username", help="shorthand: set profile.json → USERNAME and apply")
    a = ap.parse_args()

    if a.username:
        pj = ROOT / "profile.json"
        d = json.loads(pj.read_text(encoding="utf-8"))
        d["USERNAME"] = a.username
        pj.write_text(json.dumps(d, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
        print(f"profile.json → USERNAME = {a.username}")

    values = load()
    changed = [] if a.check else apply(values)
    if changed:
        print("updated:", ", ".join(changed))

    if not a.check:
        for script in ("tools/gen_mini_bars.py", ".github/scripts/update_counters.py", "tools/build_preview.py"):
            p = ROOT / script
            if p.exists():
                r = subprocess.run([sys.executable, p.as_posix()], cwd=ROOT, capture_output=True, text=True)
                tail = (r.stdout or r.stderr).strip().splitlines()
                if tail:
                    print(f"[{script}] {tail[-1]}")
                if r.returncode:
                    print(f"[{script}] FAILED\n{r.stderr}")

    problems = validate(values)
    if problems:
        print("\n⚠️  %d issue(s):" % len(problems))
        for p in problems:
            print("   -", p)
        return 1
    print("\n✅ validated: placeholders filled, SVGs parse, tags balanced, links resolve")
    return 0


if __name__ == "__main__":
    sys.exit(main())
