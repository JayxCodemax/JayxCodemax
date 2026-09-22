# 🚀 SETUP — push this to `jayant…/jayant…` and watch it light up

Everything here is **self-contained**: the animations are your own SVG files in `assets/`,
not a third-party generator, so nothing expires. Only the stat cards and shields.io badges
are external services (they can rate-limit; they always self-heal).

---

## 1. One field to fill: your GitHub username

> **Done:** handle = `JayxCodemax`, B.Tech batch 2025 → graduation 2029-06-30. Re-run
> `python3 tools/personalize.py` any time you change `profile.json` — it rewrites and re-validates.

`katariyajayant95@gmail.com`, Jaipur, the college and the RTU line are already wired in.
The **username is the only thing I couldn't look up for you** — `github.com/katariyajayant95` and three similar guesses all returned 404.

1. Open `profile.json` — `USERNAME` is already `JayxCodemax`.
2. Adjust anything else you like (dates, college line, banner kicker).
3. Run:
   ```bash
   python3 tools/personalize.py
   ```
   (Needs no extra packages. If `markdown` is absent it silently uses a built-in
   fallback renderer for `preview.html`; `pip install markdown` for the exact GitHub-style render.)
   It rewrites `README.md`, `assets/banner.svg` and both workflow files from that one source,
   regenerates the bars, rebuilds `preview.html`, and then **validates itself**:
   - no unfilled `{{TOKENS}}` or leftover placeholders
   - every local `src`/`href` points at a file that exists
   - every `logo=` slug is in the verified `.shields-logos.txt` allow-list
   - all SVGs parse (strict XML) and `<details>`/`<table>`/`<p>`/`<a>` tags are balanced
4. If it prints `⚠️`, fix what it names and re-run. If it prints `✅`, commit.

> No Python handy? Search & replace the literal `{{USERNAME}}` in `README.md`, `assets/banner.svg`
and the two workflow files. Everything else is already yours.

---

## 2. Create the repo (GitHub calls this a "profile repository")

1. **New repository** → name it **exactly your username**: `JayxCodemax/JayxCodemax`
   (case must match your login — GitHub is strict about it).
   Public. Tick *Add a README* → Create.
2. Upload this folder's contents (keep the `assets/` and `tools/` folder names):
   ```bash
   git clone https://github.com/JayxCodemax/JayxCodemax.git && cp -r github-profile/* JayxCodemax/
   cd JayxCodemax && git add -A && git commit -m "profile: animated day-1 README" && git push
   ```
3. Open `https://github.com/JayxCodemax` → banner pulses, bars animate, cards load.

---

## 3. The bits that only live on GitHub

### 🐍 Contribution-graph snake
1. Repo → **Settings → Actions → General → Workflow permissions** → *Read and write permissions*.
2. **Actions → "── 🐍 Generate GitHub Snake" → Run workflow** (~30 s).
3. Un-comment the snake `<p>` block in the "…and the snake" `<details>` of `README.md`. It re-runs daily.

### 🎓 Journey counters (`assets/badges.json` + `assets/degree-clock.json`)
`.github/workflows/counters.yml` recomputes three files every day and commits them
(`assets/badges.json`, `assets/degree-clock.json`, `assets/account-age.json`):
*"4y 0m on the bench · 1,482 days since Sep 2022"* and *"70% through · 647 days to Jun 2028"*.
The third one queries `api.github.com/users/JayxCodemax` for `created_at`, so it needs nothing from you.
Both dates live in **`profile.json`** (`JOURNEY_START`, `GRADUATION`) — nowhere else; the workflow
and `update_counters.py` read them from there. After editing, run
`python3 tools/personalize.py` and commit `assets/*.json` once so the numbers appear immediately.

### 🎵 Spotify "currently playing" (optional, needs login)
Add under the badges at the top:
```markdown
[![spotify-github-profile](https://spotify-github-profile.kititin.tech/api/view?basic=true&cover_image=true&theme=novatorem&show_offline=false&background_color=0d1117&interchange=false&bar_color=22c55e&bar_color_cover=false)](https://github.com/kittinan/spotify-github-profile)
```

### 🌗 Light / dark
`banner.svg`, `skill-bars.svg`, `now-coding.svg` and every mini bar carry
`@media (prefers-color-scheme: dark)` rules — they recolour themselves with the visitor's GitHub theme.
Want a different brand colour? Change `--accent` / `--blue` / `--green` once at the top of the file.

---

## 4. Skill bars: the honest way

There are **no percentage levels** here, because "80% LTspice" is meaningless without a repo behind it.
Bars encode a **learning stage (1-6)** and the label prints it:

`1 = just started · 2 = new to it · 3 = building basics · 4 = comfortable · 5 = practised · 6 = teaching it`

- **Big grouped chart:** edit the `<rect width="…">` in `assets/skill-bars.svg`.
  `width = 820 × stage ÷ 6` → 137 / 273 / 410 / 546 / 683 / 820. Update the `· N/6` label beside it.
- **Small grid bars:** edit `tools/gen_mini_bars.py` → `SKILLS` (label, `level` 0-5, status), then
  `python3 tools/gen_mini_bars.py`. The script refuses a status word that isn't in `STAGES`,
  so the chart and the legend can never drift apart.
- The **Featured Projects** cards say "on the bench / planned" and ship **zero links** — swap in a repo
  URL the day it exists. The `✅ public repos shipped-0` badge is deliberately there; delete it once it reads `-1`.

---

## 5. Monthly 10-minute maintenance

- [ ] Tick a roadmap checkbox, nudge `phase N-%` badge numbers.
- [ ] Promote one skill's stage the day you can *show* it.
- [ ] Re-run the snake workflow after a heavy week.
- [ ] Replace a "planned" project card with a real one (template is in the `<details>`).
- [ ] Delete a badge the moment it becomes a lie. A shorter, truer list reads better to every reviewer.

## File map

```
profile.json                ← your single source of truth
README.md                   ← the profile page (tokens filled by personalize.py)
SETUP.md                    ← this file
preview.html                ← animated local preview; regenerate, never hand-edit
assets/
  banner.svg                ← animated hero: circuit traces, MCU, robot, your name
  skill-bars.svg            ← grouped bars labelled with learning stages
  now-coding.svg            ← sketch.ino typing itself
  8× mini bars (.svg)       ← regenerated by tools/gen_mini_bars.py
  badges.json               ← written by the counters workflow (journey length)
  degree-clock.json         ← written by the counters workflow (degree %)
  snake.svg                 ← created by the snake workflow (optional)
tools/
  personalize.py            ← fill + validate the whole kit
  gen_mini_bars.py          ← regenerate the small bars
  build_preview.py          ← rebuild preview.html from README.md
.shields-logos.txt          ← verified shields.io logo allow-list (personalize.py checks against it)
.github/workflows/
  snake.yml                 ← daily contribution-graph snake
  counters.yml              ← daily journey-counter refresh
.github/scripts/update_counters.py
draft-original.md           ← your original plain-text section, kept as reference
```
