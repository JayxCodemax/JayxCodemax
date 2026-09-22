#!/usr/bin/env python3
"""Generate the small animated skill bars used in the README grid.

Usage (from the repo root):  python3 tools/gen_mini_bars.py

Each bar = one learning stage. `level` is 0-5 (see STAGES below), so the
width and the word always agree — no "95% but I've never used it" energy.
"""
import pathlib

W, H, PAD, BH, NAME_Y, BAR_Y = 240, 46, 12, 10, 20, 30
ICON_X, ICON_W = 12, 22
LABEL_X = ICON_X + ICON_W + 8
TRACK_X = LABEL_X
TW = W - TRACK_X - PAD

STAGES = ["just started", "new to it", "building basics", "comfortable", "practised", "teaching it"]

# slug, level 0-5, label, status words, gradient start, gradient end, embedded icon path ("" = bullet)
SKILLS = [
    ("arduinobaro", 2, "Arduino / AVR C++",   "building basics",   "#2563eb", "#0ea5e9", ""),
    ("pythonbar",   2, "Python for hardware", "building basics",     "#f59e0b", "#fbbf24", ""),
    ("cadbar",      3, "2D CAD &amp; drafting",   "comfortable",      "#0d9488", "#22c55e", ""),
    ("autocadbar",  1, "AutoCAD Electrical",  "new to it",         "#e11d48", "#fb7185", ""),
    ("ltspicebar",  1, "LTspice",             "new to it",           "#16a34a", "#84cc16",
     "M9.3267 3.4848c-.7965.627-.9744 1.6212-1.1644 3.3173-.3653 3.257-.641 5.1982-1.0473 8.658-.199 1.705-.388 2.704-.7 3.313m0 0c-.199.388-.462.657-.834.813M6.4 19.44c.7-.32 1.299-1.06 1.878-2.286.948-2.005 2.11-4.94 3.14-7.632 1.033-2.693 1.94-5.148 2.617-6.402.345-.64.71-1.048 1.15-1.226m0 0c-.44.178-.794.586-1.15 1.226"),
    ("simulinkbar", 0, "Simulink / MATLAB",   "just started",     "#dc2626", "#f97316", ""),
    ("webbar",      2, "HTML · CSS · JS",     "building basics",     "#7c3aed", "#c084fc", ""),
    ("iotbar",      1, "IoT & sensors",       "new to it",         "#0284c7", "#38bdf8", ""),
]

TPL = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" role="img" aria-label="{name} — {status}">
  <defs>
    <style><![CDATA[
      :root {{ --panel: rgba(255,255,255,.70); --border: {c1}33; --ink: #0f172a; --sub: #64748b; --track: #e6ebf5; }}
      @media (prefers-color-scheme: dark) {{
        :root {{ --panel: rgba(13,20,38,.66); --border: {c1}55; --ink: #e8eefc; --sub: #93a6c4; --track: #18233c; }}
      }}
      text {{ font-family: 'Segoe UI', ui-sans-serif, system-ui, -apple-system, Roboto, sans-serif; }}
      .name  {{ font-size: 13px; font-weight: 600; fill: var(--ink); }}
      .state {{ font-size: 10px; font-weight: 800; fill: {c1}; letter-spacing: 1px; text-transform: uppercase; }}
      .panel {{ fill: var(--panel); stroke: var(--border); }}
      .track {{ fill: var(--track); }}
      .tick  {{ stroke: var(--panel); stroke-width: 2; }}
      .fill  {{ transform-box: fill-box; transform-origin: left center;
                animation: grow 1.6s cubic-bezier(.22,1,.36,1) .2s both; }}
      @keyframes grow {{ from {{ transform: scaleX(0); }} to {{ transform: scaleX(1); }} }}
      @media (prefers-reduced-motion: reduce) {{ .fill {{ animation: none; }} }}
    ]]></style>
    <linearGradient id="g" x1="0" x2="1"><stop offset="0%" stop-color="{c1}"/><stop offset="100%" stop-color="{c2}"/></linearGradient>
  </defs>
  <rect class="panel" x="0.5" y="0.5" width="{wm}" height="{hm}" rx="12"/>
  {icon}
  <text class="name" x="{lx}" y="{ny}">{name}</text>
  <text class="state" x="{wrm}" y="{ny}" text-anchor="end">{status}</text>
  <rect class="track" x="{tx}" y="{by}" width="{tw}" height="{bh}" rx="{bh2}"/>
  <g class="tick" opacity=".9">{ticks}</g>
  <g class="fill"><rect x="{tx}" y="{by}" width="{fw}" height="{bh}" rx="{bh2}" fill="url(#g)"/></g>
</svg>
"""

ICON_TPL = ('<g transform="translate({ix} 13) scale(0.75)" fill="none" stroke="{c1}" '
            'stroke-width="2.1" stroke-linecap="round" stroke-linejoin="round">'
            '<path d="{d}"/></g>')
BULLET_TPL = '<circle cx="{cx}" cy="28" r="4.5" fill="{c1}" opacity=".85"/>'


def render(slug, level, name, status, c1, c2, icon_path):
    fw = max(6, round(TW * (level + 1) / 6))
    ticks = "".join(
        f'<path d="M{TRACK_X + round(TW * k / 5)} {BAR_Y - 2}v{BH + 4}" stroke="var(--panel)"/>'
        for k in range(1, 5)
    )
    icon = ICON_TPL.format(ix=ICON_X, c1=c1, d=icon_path) if icon_path else \
        BULLET_TPL.format(cx=ICON_X + 4, c1=c1)
    # bullet variant needs the label to start earlier
    lx = LABEL_X if icon_path else LABEL_X - 18
    return TPL.format(w=W, h=H, wm=W - 1, hm=H - 1, icon=icon, lx=lx, ny=NAME_Y,
                      wrm=W - PAD, tx=TRACK_X if icon_path else TRACK_X - 18,
                      by=BAR_Y, bh=BH, bh2=BH / 2,
                      tw=TW if icon_path else TW + 18,
                      fw=fw if icon_path else max(6, round((TW + 18) * (level + 1) / 6)),
                      ticks=ticks, name=name.replace("&", "&amp;"), status=status, c1=c1, c2=c2)


def main() -> None:
    out = pathlib.Path(__file__).resolve().parent.parent / "assets"
    out.mkdir(exist_ok=True)
    for args in SKILLS:
        slug, level, name, status, c1, c2, icon = args
        assert 0 <= level <= 5, f"{slug}: level out of range"
        assert status in STAGES, f"{status!r} is not in STAGES"
        (out / f"{slug}.svg").write_text(render(slug, level, name, status, c1, c2, icon), encoding="utf-8")
        print(f"wrote assets/{slug}.svg  ·  level {level+1}/6 · {status}")


if __name__ == "__main__":
    main()
