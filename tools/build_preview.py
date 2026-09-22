#!/usr/bin/env python3
"""Build a self-contained local preview of the profile README.

The GitHub *renderer* strips <style> tags from inline SVG, so this script:
  1. reads README.md
  2. inlines assets/*.svg referenced via <img> (so animations actually run)
  3. emits preview.html (GitHub-ish styling, dark-mode aware)

Usage:  python3 tools/build_preview.py
"""
import pathlib
import re
import sys

try:
    import markdown  # type: ignore
    HAVE_MD = True
except ImportError:
    markdown = None
    HAVE_MD = False

ROOT = pathlib.Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"


def inline_svg(md: str) -> str:
    """Replace <img src="assets/x.svg"> with the actual SVG so CSS animates."""
    def swap(m):
        src = m.group(1)
        p = ROOT / src
        if not src.endswith(".svg") or not p.exists():
            return m.group(0)
        svg = p.read_text(encoding="utf-8")
        svg = re.sub(r'^<\?xml.*?\?>\s*', '', svg)
        svg = svg.replace("<svg ", '<svg style="width:100%;height:auto;display:block" ', 1)
        alt = re.search(r'alt="([^"]*)"', m.group(0))
        alt = f' aria-label="{alt.group(1)}"' if alt else ""
        return svg.rstrip()[:-len("</svg>")] + f"<title>{alt}</title></svg>"
    return re.sub(r'<img src="([^"]+)"[^>]*/?>', swap, md)


CSS = """
:root { --bg:#ffffff; --fg:#1f2328; --muted:#59636e; --border:#d1d9e0; --code:#f6f8fa; --accent:#2563eb; }
@media (prefers-color-scheme: dark) { :root { --bg:#0d1117; --fg:#e6edf3; --muted:#9198a1; --border:#3d444d; --code:#151b23; --accent:#60a5fa; } }
* { box-sizing: border-box }
body { margin:0; background:var(--bg); color:var(--fg);
  font:16px/1.6 -apple-system,BlinkMacSystemFont,"Segoe UI",Helvetica,Arial,sans-serif; }
.wrap { max-width:1012px; margin:0 auto; padding:32px 24px 80px; }
h1,h2,h3,h4 { font-weight:700; line-height:1.25; margin:24px 0 12px }
h1 { font-size:2em; padding-bottom:.3em } h2 { font-size:1.5em; border-bottom:1px solid var(--border); padding-bottom:.3em }
h1,h2 { text-align:left } h1 + p, h2 + * { margin-top:0 }
img { max-width:100%; }
a { color:var(--accent); text-decoration:none } a:hover { text-decoration:underline }
table { border-collapse:collapse; margin:12px 0 }
td,th { padding:8px 12px; vertical-align:top }
code, pre { font-family:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace; font-size:85% }
pre { background:var(--code); padding:14px 16px; border-radius:8px; overflow:auto; border:1px solid var(--border) }
code { background:var(--code); padding:.15em .35em; border-radius:4px }
pre code { background:none; padding:0 }
details { border:1px solid var(--border); border-radius:8px; padding:10px 16px; margin:12px 0; background:color-mix(in srgb, var(--code) 45%, transparent) }
summary { cursor:pointer; font-weight:600 }
blockquote { margin:0 0 12px; padding:0 1em; color:var(--muted); border-left:.25em solid var(--border) }
hr { height:1px; background:var(--border); border:0; margin:24px 0 }
p { margin:10px 0 }
.badge-strip img, p img { display:inline-block; margin:3px 2px }
h1 { text-align:center } h1 + p { text-align:center }
.note { text-align:center; color:var(--muted); font-size:13px; border:1px dashed var(--border); border-radius:10px; padding:10px 14px; margin:0 0 24px }
svg { margin:4px 0 }
"""


def _esc(t: str) -> str:
    return t.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def _inline(t: str) -> str:
    """Just enough inline markdown for the preview: links, images, code, bold."""
    t = re.sub(r"!\[([^\]]*)\]\(([^)\s]+)[^)]*\)", r'<img src="\2" alt="\1"/>', t)
    t = re.sub(r"\[([^\]]+)\]\(([^)\s]+)[^)]*\)", r'<a href="\2">\1</a>', t)
    t = re.sub(r"`([^`]+)`", r"<code>\1</code>", t)
    t = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", t)
    return t


def fallback_render(md: str) -> str:
    """Offline renderer: used when python-markdown isn't installed. Handles the
    constructs this README actually uses; <p align>/<table>/<details> pass through."""
    out: list[str] = []
    in_code = False
    for raw in md.split("\n"):
        line = raw.rstrip()
        if line.startswith("```"):
            out.append("</code></pre>" if in_code else "<pre><code>")
            in_code = not in_code
            continue
        if in_code:
            out.append(_esc(raw))
            continue
        if not line.strip():
            out.append("")
            continue
        if set(line.strip()) <= {"-", "_", "*"} and len(line.strip()) >= 3:
            out.append("<hr/>")
            continue
        m = re.match(r"^(#{1,4})\s+(.*)$", line)
        if m:
            n = len(m.group(1))
            out.append(f"<h{n}>{_inline(_esc(m.group(2)))}</h{n}>")
            continue
        m = re.match(r"^>\s?(.*)$", line)
        if m:
            out.append(f"<blockquote>{_inline(_esc(m.group(1)))}</blockquote>")
            continue
        m = re.match(r"^[-*]\s+(?:\[( |x)\]\s+)?(.*)$", line)
        if m and not line.startswith("<"):
            box = "" if m.group(1) is None else f"<b>[{m.group(1)}]</b> "
            out.append(f"<p>• {box}{_inline(_esc(m.group(2)))}</p>")
            continue
        out.append(_inline(_esc(line)) if line.lstrip().startswith("<") else f"<p>{_inline(_esc(line))}</p>")
    return "\n".join(out)


def main() -> None:
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    if "{{USERNAME}}" in readme:  # username not filled in yet → use local JSON for the preview
        readme = re.sub(
            r'https://img\.shields\.io/endpoint\?url=https://raw\.githubusercontent\.com/[^"]*badges\.json[^"]*',
            'https://img.shields.io/badge/journey%20counters-see%20assets/badges.json-7c3aed',
            readme,
        )
    readme = inline_svg(readme)
    if HAVE_MD:
        body = markdown.markdown(readme, extensions=["extra", "sane_lists", "nl2br"],
                                 output_format="html5")
        renderer = "python-markdown"
    else:
        body = fallback_render(readme)
        renderer = "offline fallback renderer (pip install markdown for the full one)"
    print(f"[preview] renderer: {renderer}")
    html = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"/>
<meta name="viewport" content="width=device-width, initial-scale=1"/>
<title>GitHub Profile · preview</title>
<style>{CSS}</style></head>
<body><div class="wrap">
<p class="note">Local preview — the animated SVGs below are the exact files in <code>assets/</code>.<br/>
On GitHub the SVGs render as images (animation depends on the client); the external stat cards load live there.</p>
{body}
</div></body></html>
"""
    out = ROOT / "preview.html"
    out.write_text(html, encoding="utf-8")
    print(f"wrote {out.relative_to(ROOT.parent)}  ({len(html):,} bytes)")


if __name__ == "__main__":
    main()
