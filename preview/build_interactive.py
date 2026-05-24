"""Build a tappable, browser-navigable HTML preview of SIGNAL.

Produces preview/web/index.html — open in any browser, no server needed.
Click hotspots to navigate between phone screens like the real app.

Run from /home/user/signal:
    backend/.venv/bin/python preview/build_interactive.py
"""
from __future__ import annotations

import base64
import json
from io import BytesIO
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
OUT = ROOT / "web"
OUT.mkdir(exist_ok=True)


# ---------- fake fashion thumbs (no external assets needed) ----------

PALETTE = [
    ((232, 226, 213), (78, 70, 62)),
    ((226, 220, 207), (47, 48, 46)),
    ((215, 207, 191), (118, 96, 76)),
    ((240, 234, 222), (60, 62, 58)),
    ((202, 196, 184), (74, 70, 62)),
    ((228, 222, 209), (43, 60, 55)),
]


def thumb(w: int, h: int, tone: tuple[int, int, int], accent: tuple[int, int, int]) -> str:
    img = Image.new("RGB", (w, h), tone)
    draw = ImageDraw.Draw(img)
    for y in range(h):
        f = y / h
        r = int(tone[0] * (1 - 0.18 * f))
        g = int(tone[1] * (1 - 0.18 * f))
        b = int(tone[2] * (1 - 0.18 * f))
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    cx = w // 2
    draw.polygon(
        [
            (cx - w * 0.32, h * 0.18),
            (cx + w * 0.32, h * 0.18),
            (cx + w * 0.42, h * 0.35),
            (cx + w * 0.30, h * 0.95),
            (cx - w * 0.30, h * 0.95),
            (cx - w * 0.42, h * 0.35),
        ],
        fill=accent,
    )
    draw.ellipse([(cx - w * 0.10, h * 0.15), (cx + w * 0.10, h * 0.24)], fill=tone)
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


THUMBS = [thumb(220, 280, t, a) for t, a in PALETTE]


# ---------- sample analysis (cached from real pipeline) ----------

def load_report() -> dict:
    fp = Path("/tmp/sample_report.json")
    if fp.exists():
        return json.loads(fp.read_text())
    # Hardcoded fallback so the preview always builds
    return {
        "id": "demo",
        "mode": "product_study",
        "image_count": 3,
        "observation": "Quiet Luxury / Minimal Oversized Tee",
        "summary": "Heavyweight cotton, boxy silhouettes, restrained palette — quiet luxury read.",
        "brand_signals": [
            {"brand": "Massimo Dutti", "similarity": "Strong",   "rationale": "Drop-shoulder, mid-weight jersey, neutral palette — exact alignment with their floor right now."},
            {"brand": "COS",            "similarity": "Adjacent","rationale": "Architectural minimalism overlaps; COS skews more sculptural in the silhouette."},
            {"brand": "Arket",          "similarity": "Moderate","rationale": "Same Scandi minimal lane but at a more functional, basics-first positioning."},
            {"brand": "Uniqlo",         "similarity": "Moderate","rationale": "Shares the neutral palette and oversized fit, but on a value architecture."},
            {"brand": "Prada",          "similarity": "Weak",    "rationale": "Quiet-luxury direction in spirit, but executed at a different fabric and price tier."},
        ],
        "commentary": "The pieces lean into the quiet-luxury direction that has dominated spring 2025 floor sets. Strong overlap with Massimo Dutti and COS; Zara remains the volume play.",
        "directions": [
            {"label": "Safe Commercial",     "title": "Hero the heavyweight tee",      "description": "Run a tight capsule of oversized, neutral, mid-weight tees at a high-street price point. Stick to proven silhouettes — this is volume, not noise."},
            {"label": "Trend Forward",       "title": "Push the proportion",            "description": "Take the same direction and exaggerate one variable — sleeve length, drop shoulder, or hem treatment. Limited drops, premium fabric."},
            {"label": "Differentiated Route","title": "Craft + earthtone story",        "description": "Lean into texture-led knits, hand-feel finishes, undyed naturals. Sells the brand story; lower velocity, higher margin."},
        ],
        "keywords": ["oversized", "neutral", "minimal", "boxy", "drop-shoulder", "heavyweight"],
    }


REPORT = load_report()


# ---------- HTML ----------

CSS = """
:root {
  --bg: #FBF8F2; --surface: #FFFFFF; --surface-muted: #F4EFE5;
  --text: #1F1F1D; --text-muted: #6B6760; --text-subtle: #9A938A;
  --divider: #E6E2D8;
  --emerald: #1F5F4A; --emerald-soft: #E3EDE7;
  --burgundy: #7A2A2A; --burgundy-soft: #F3E3E3;
  --page: #ECE7DB;
}
* { box-sizing: border-box; -webkit-font-smoothing: antialiased; }
html, body { margin: 0; padding: 0; background: var(--page); color: var(--text);
  font-family: -apple-system, 'SF Pro Text', Inter, system-ui, sans-serif; }

.layout {
  min-height: 100vh;
  display: flex; align-items: center; justify-content: center; flex-direction: column;
  padding: 32px 16px;
}
.title { font-size: 13px; letter-spacing: 1.4px; text-transform: uppercase;
  color: var(--text-muted); margin-bottom: 6px; }
.brand { font-size: 28px; font-weight: 800; letter-spacing: -0.5px; margin-bottom: 4px; }
.lede { color: var(--text-muted); font-size: 14px; max-width: 420px;
  text-align: center; margin-bottom: 24px; line-height: 20px; }

.phone-frame {
  width: 412px; height: 866px;
  border-radius: 56px;
  background: #111;
  padding: 11px;
  box-shadow: 0 30px 60px rgba(31,31,29,0.25), 0 8px 18px rgba(31,31,29,0.18);
  position: relative;
}
.phone-frame::before {
  content: ''; position: absolute;
  top: 24px; left: 50%; transform: translateX(-50%);
  width: 120px; height: 30px; background: #000;
  border-radius: 18px; z-index: 30;
}
#screens {
  width: 100%; height: 100%;
  border-radius: 46px; overflow: hidden;
  background: var(--bg);
  position: relative;
}
.screen {
  position: absolute; inset: 0;
  background: var(--bg);
  display: none;
  overflow: hidden;
}
.screen.active { display: block; }

.statusbar {
  height: 56px;
  display: flex; align-items: center; justify-content: space-between;
  padding: 22px 32px 0 32px;
  font-size: 14px; font-weight: 700;
  position: relative; z-index: 2;
}
.statusbar .right { display: flex; gap: 6px; align-items: center; font-size: 11px; }

.kicker {
  font-size: 11px; font-weight: 700; letter-spacing: 1.3px;
  text-transform: uppercase; color: var(--text-muted);
}
.kicker--emerald { color: var(--emerald); }
.kicker--burgundy { color: var(--burgundy); }

.card {
  background: var(--surface); border-radius: 22px; padding: 22px;
  box-shadow: 0 6px 16px rgba(31,31,29,0.06);
}
.card--flat {
  background: var(--surface-muted); border-radius: 14px; padding: 18px;
  box-shadow: none;
}

.btn {
  height: 54px; border-radius: 999px;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; font-weight: 600; letter-spacing: 0.1px;
  cursor: pointer; user-select: none;
  transition: transform 120ms ease, opacity 120ms ease;
}
.btn:active { transform: scale(0.98); opacity: 0.92; }
.btn--primary { background: var(--text); color: #fff; }
.btn--secondary {
  background: var(--surface); color: var(--text); border: 1px solid var(--divider);
}

.nav-row {
  display: flex; padding: 4px 16px 12px 16px; align-items: center;
}
.nav-back {
  width: 48px; height: 32px; display:flex; align-items:center; justify-content:center;
  font-size: 22px; cursor: pointer; color: var(--text);
}
.nav-title { flex: 1; text-align: center; font-size: 16px; font-weight: 600; }
.nav-right { width: 48px; text-align: right; cursor: pointer; }

.pill {
  font-size: 11px; font-weight: 700; letter-spacing: 0.8px;
  padding: 4px 10px; border-radius: 999px;
}
.pill--strong   { background: var(--emerald-soft); color: var(--emerald); }
.pill--adjacent { background: #EFEAE0; color: var(--text); }
.pill--moderate { background: #EFEAE0; color: var(--text-muted); }
.pill--weak     { background: #F4EFE5; color: var(--text-subtle); }

/* Screen-specific layouts */
.scroll { height: calc(100% - 56px); overflow-y: auto; padding: 0 24px 100px; }
.scroll::-webkit-scrollbar { width: 0; }

/* Home */
.home-link {
  position: absolute; top: 60px; right: 32px;
  font-size: 13px; color: var(--text-muted); cursor: pointer;
}
.home-hero {
  position: absolute; left: 32px; right: 32px;
  top: 50%; transform: translateY(-55%);
}
.home-actions {
  position: absolute; bottom: 80px; left: 32px; right: 32px;
}
.home-footer {
  position: absolute; bottom: 30px; left: 32px; right: 32px;
  font-size: 11px; color: var(--text-subtle); text-align: center; line-height: 16px;
}
.brand-display {
  font-size: 64px; line-height: 64px; font-weight: 800;
  letter-spacing: -2.4px; color: var(--text);
}
.tagline {
  font-size: 15px; color: var(--text-muted); line-height: 22px;
  margin-top: 20px; max-width: 320px;
}

/* Upload */
.grid-3 {
  display: grid; grid-template-columns: repeat(3, 1fr); gap: 8px;
}
.tile {
  aspect-ratio: 1; border-radius: 14px; background-size: cover;
  background-position: center; background-color: var(--surface-muted);
}

/* Analysis */
.steps { padding: 220px 32px 0 32px; }
.step {
  display: flex; align-items: center; padding: 12px 0;
}
.step-dot-wrap {
  width: 24px; height: 24px; display: flex; align-items: center;
  justify-content: center; margin-right: 12px; position: relative;
}
.step-dot { width: 8px; height: 8px; border-radius: 50%; }
.step--done .step-dot { background: var(--text); }
.step--done .step-label { color: var(--text-muted); }
.step--active .step-dot { background: var(--emerald); }
.step--active .step-label { color: var(--text); font-weight: 600; }
.step--active .step-dot-wrap::after {
  content: ''; position: absolute; width: 22px; height: 22px;
  border-radius: 50%; background: var(--emerald); opacity: 0.18;
  animation: pulse 1.6s ease-in-out infinite;
}
.step--pending .step-dot { background: var(--divider); }
.step--pending .step-label { color: var(--text-subtle); }
.step-label { font-size: 15px; }
@keyframes pulse {
  0%, 100% { transform: scale(1); opacity: 0.18; }
  50% { transform: scale(1.5); opacity: 0; }
}

/* Results */
.collage {
  width: 88px; height: 88px; border-radius: 14px; overflow: hidden;
  display: grid; grid-template-columns: 1fr 1fr; gap: 2px;
  background: var(--surface-muted); flex-shrink: 0;
}
.collage > div {
  background-size: cover; background-position: center;
}
.brand-row {
  padding: 14px 0;
}
.brand-row + .brand-row { border-top: 1px solid var(--divider); }
.brand-head { display: flex; justify-content: space-between; align-items: center; }
.brand-name { font-size: 16px; font-weight: 600; }
.brand-rationale { font-size: 13px; color: var(--text-muted); margin-top: 4px; line-height: 19px; }

.direction { padding: 14px 0; }
.direction + .direction { border-top: 1px solid var(--divider); }
.dir-label { font-size: 11px; font-weight: 700; color: var(--burgundy); letter-spacing: 1.2px; }
.dir-title { font-size: 18px; font-weight: 600; margin-top: 4px; }
.dir-desc { font-size: 14px; color: var(--text-muted); margin-top: 6px; line-height: 21px; }

.cta-row {
  padding: 0 24px; position: absolute; bottom: 30px; left: 0; right: 0;
}

/* History */
.history-card {
  display: flex; align-items: center; margin-bottom: 12px;
  background: var(--surface); border: 1px solid var(--divider);
  border-radius: 14px; padding: 12px;
  cursor: pointer;
}
.history-card .collage { width: 72px; height: 72px; border-radius: 10px; }
.history-text { flex: 1; margin-left: 14px; }
.history-title { font-size: 16px; font-weight: 600; line-height: 20px; }
.history-meta { font-size: 13px; color: var(--text-muted); margin-top: 4px; }

/* Export */
.input-fake {
  background: var(--surface-muted); height: 50px; border-radius: 14px;
  display: flex; align-items: center; padding: 0 16px;
  color: var(--text-subtle); font-size: 15px;
}
.download-block {
  background: var(--emerald-soft);
}
.share-btn {
  display: inline-block; background: var(--emerald); color: #fff;
  padding: 8px 16px; border-radius: 999px;
  font-size: 13px; font-weight: 600; cursor: pointer;
}

.legend {
  margin-top: 22px; color: var(--text-muted); font-size: 13px;
  text-align: center; max-width: 460px;
}
.legend code {
  background: rgba(31,31,29,0.07); padding: 1px 6px; border-radius: 4px;
  font-size: 12px;
}
"""


def sim_class(s: str) -> str:
    return {"Strong":"pill--strong","Adjacent":"pill--adjacent","Moderate":"pill--moderate","Weak":"pill--weak"}[s]


def screen_home() -> str:
    return f"""
<section class="screen" id="screen-home" data-screen="home">
  <div class="statusbar">
    <span>9:41</span>
    <div class="right"><span>•••</span><span>▮▮▮</span></div>
  </div>
  <div class="home-link" onclick="show('history')">History</div>
  <div class="home-hero">
    <div class="kicker">Fashion Signal Agent</div>
    <div class="brand-display">SIGNAL</div>
    <div class="tagline">Snap products. Understand what brands are doing. Decide what to design next.</div>
  </div>
  <div class="home-actions">
    <div class="btn btn--primary" onclick="show('upload')">Take Photo</div>
    <div style="height:12px"></div>
    <div class="btn btn--secondary" onclick="show('upload')">Upload Images</div>
  </div>
  <div class="home-footer">
    Analysis focuses on apparel &amp; design attributes, not personal identity.<br>
    Images are processed in memory and never stored.
  </div>
</section>
"""


def screen_upload() -> str:
    tiles = "".join(f'<div class="tile" style="background-image:url({t})"></div>' for t in THUMBS)
    return f"""
<section class="screen" id="screen-upload">
  <div class="statusbar"><span>9:41</span><div class="right"><span>•••</span><span>▮▮▮</span></div></div>
  <div class="nav-row">
    <div class="nav-back" onclick="show('home')">←</div>
    <div class="nav-title">Preview</div>
    <div class="nav-right"></div>
  </div>
  <div style="padding: 0 24px 16px 24px;">
    <div class="kicker">We detected</div>
    <div style="font-size: 26px; font-weight: 700; margin-top:4px;">Competitor Store Walk</div>
    <div style="font-size: 13px; color: var(--text-muted); margin-top:4px;">
      6 images · we'll confirm after analysis
    </div>
  </div>
  <div style="padding: 0 24px;"><div class="grid-3">{tiles}</div></div>
  <div style="position:absolute; bottom: 30px; left: 0; right: 0; padding: 0 24px;">
    <div style="text-align:center; padding:12px 0; color: var(--text-muted);
                font-size:13px; text-decoration: underline; cursor:pointer;"
         onclick="show('home')">Change selection</div>
    <div class="btn btn--primary" onclick="show('analysis')">Analyze 6 Images</div>
  </div>
</section>
"""


def screen_analysis() -> str:
    return """
<section class="screen" id="screen-analysis">
  <div class="statusbar"><span>9:41</span><div class="right"><span>•••</span><span>▮▮▮</span></div></div>
  <div class="steps">
    <div class="kicker">Analyzing</div>
    <div style="font-size: 26px; font-weight: 700; margin-top:4px; margin-bottom: 28px;">Reading the floor</div>
    <div class="step step--done"><div class="step-dot-wrap"><div class="step-dot"></div></div><div class="step-label">Reading images</div></div>
    <div class="step step--done"><div class="step-dot-wrap"><div class="step-dot"></div></div><div class="step-label">Detecting context</div></div>
    <div class="step step--active"><div class="step-dot-wrap"><div class="step-dot"></div></div><div class="step-label">Selecting brand cohort</div></div>
    <div class="step step--pending"><div class="step-dot-wrap"><div class="step-dot"></div></div><div class="step-label">Pulling live retailer signals</div></div>
    <div class="step step--pending"><div class="step-dot-wrap"><div class="step-dot"></div></div><div class="step-label">Writing the brief</div></div>
    <div style="position:absolute; bottom: 30px; left: 32px; right: 32px;
                text-align: center; font-size: 12px; color: var(--text-subtle);">
      Auto-advances to Results · tap to continue
    </div>
    <div style="position:absolute; inset: 0; cursor: pointer;" onclick="show('results')"></div>
  </div>
</section>
"""


def screen_results() -> str:
    collage = "".join(f'<div style="background-image:url({THUMBS[i]})"></div>' for i in range(4))
    brand_rows = "".join(
        f'<div class="brand-row">'
        f'  <div class="brand-head"><div class="brand-name">{sig["brand"]}</div>'
        f'  <div class="pill {sim_class(sig["similarity"])}">{sig["similarity"].upper()}</div></div>'
        f'  <div class="brand-rationale">{sig["rationale"]}</div>'
        f'</div>'
        for sig in REPORT["brand_signals"][:4]
    )
    dir_rows = "".join(
        f'<div class="direction">'
        f'  <div class="dir-label">{d["label"].upper()}</div>'
        f'  <div class="dir-title">{d["title"]}</div>'
        f'  <div class="dir-desc">{d["description"]}</div>'
        f'</div>'
        for d in REPORT["directions"]
    )
    mode_label = REPORT["mode"].replace("_", " ").title()
    return f"""
<section class="screen" id="screen-results">
  <div class="statusbar"><span>9:41</span><div class="right"><span>•••</span><span>▮▮▮</span></div></div>
  <div class="nav-row">
    <div class="nav-back" onclick="show('home')">←</div>
    <div class="nav-title"></div>
    <div class="nav-right" style="color: var(--emerald); font-size:13px; font-weight: 600;"
         onclick="show('export')">Export</div>
  </div>
  <div class="scroll">
    <div style="display:flex; align-items:center; margin-bottom: 18px;">
      <div class="collage">{collage}</div>
      <div style="flex:1; margin-left: 16px;">
        <div class="kicker">{mode_label} · {REPORT["image_count"]} images</div>
        <div style="font-size: 24px; font-weight: 700; line-height: 28px; margin-top: 4px;">
          {REPORT["observation"]}
        </div>
      </div>
    </div>
    <div style="font-size:15px; color: var(--text-muted); margin-bottom: 16px;">{REPORT["summary"]}</div>

    <div class="card" style="margin-bottom: 16px;">
      <div class="kicker">Brand Signals</div>
      <div style="height: 6px"></div>
      {brand_rows}
    </div>

    <div class="card" style="margin-bottom: 16px;">
      <div class="kicker">Market Commentary</div>
      <div style="margin-top: 8px; font-size: 15px; line-height: 23px;">{REPORT["commentary"]}</div>
    </div>

    <div class="card">
      <div class="kicker">Recommended Directions</div>
      {dir_rows}
    </div>

    <div style="text-align:center; padding: 22px 0; cursor: pointer;"
         onclick="show('export')">
      <div style="color: var(--emerald); font-size: 13px; text-decoration: underline;">
        See full intelligence
      </div>
    </div>

    <div class="btn btn--primary" onclick="show('export')">Export Report</div>
  </div>
</section>
"""


def screen_history() -> str:
    items_today = [
        (REPORT["observation"], REPORT["mode"], REPORT["image_count"], THUMBS[:4]),
        ("Heritage Denim Revival",  "store_walk",        9,  THUMBS[2:6]),
    ]
    items_yest = [
        ("Sport-Lux Athleisure",    "moodboard",         12, THUMBS[1:5]),
    ]
    def row(obs, mode, count, thumbs):
        coll = "".join(f'<div style="background-image:url({t})"></div>' for t in thumbs[:4])
        mode_label = mode.replace("_", " ").title()
        return (f'<div class="history-card" onclick="show(\'results\')">'
                f'  <div class="collage">{coll}</div>'
                f'  <div class="history-text">'
                f'    <div class="history-title">{obs}</div>'
                f'    <div class="history-meta">{mode_label} · {count} images</div>'
                f'  </div>'
                f'</div>')
    today = "".join(row(*it) for it in items_today)
    yest = "".join(row(*it) for it in items_yest)
    return f"""
<section class="screen" id="screen-history">
  <div class="statusbar"><span>9:41</span><div class="right"><span>•••</span><span>▮▮▮</span></div></div>
  <div class="nav-row">
    <div class="nav-back" onclick="show('home')">←</div>
    <div class="nav-title">History</div>
    <div class="nav-right" style="color: var(--burgundy); font-size:13px;">Clear</div>
  </div>
  <div class="scroll" style="padding-bottom: 60px;">
    <div class="kicker">Today</div><div style="height:8px"></div>
    {today}
    <div style="height: 16px"></div>
    <div class="kicker">Yesterday</div><div style="height:8px"></div>
    {yest}
  </div>
</section>
"""


def screen_export() -> str:
    return f"""
<section class="screen" id="screen-export">
  <div class="statusbar"><span>9:41</span><div class="right"><span>•••</span><span>▮▮▮</span></div></div>
  <div class="nav-row">
    <div class="nav-back" onclick="show('results')">←</div>
    <div class="nav-title">Export</div>
    <div class="nav-right"></div>
  </div>
  <div class="scroll">
    <div class="kicker">This brief</div>
    <div style="font-size: 26px; font-weight: 700; margin-top:4px; margin-bottom: 18px;">
      {REPORT["observation"]}
    </div>
    <div class="card" style="margin-bottom: 16px;">
      <div class="kicker">PDF</div>
      <div style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">
        Generate an editorial PDF you can save or share.
      </div>
      <div style="height:14px"></div>
      <div class="btn btn--primary">Generate PDF</div>
    </div>
    <div class="card" style="margin-bottom: 16px;">
      <div class="kicker">Email</div>
      <div style="font-size: 13px; color: var(--text-muted); margin-top: 4px;">
        We'll prepare the PDF and surface a download link you can share.
      </div>
      <div style="height:14px"></div>
      <div class="input-fake">designer@brand.com</div>
      <div style="height:14px"></div>
      <div class="btn btn--secondary">Prepare for Email</div>
    </div>
    <div class="card--flat download-block">
      <div class="kicker kicker--emerald">Download link</div>
      <div style="font-size:13px; color: var(--emerald); margin-top:4px; word-break:break-all;">
        https://signal-backend.onrender.com/reports/d5deb994-9807-4dd1-93d1-1792bccb4f84
      </div>
      <div style="height:14px"></div>
      <div class="share-btn">Open / Share</div>
    </div>
  </div>
</section>
"""


def build_index() -> str:
    body = (
        screen_home() + screen_upload() + screen_analysis() +
        screen_results() + screen_history() + screen_export()
    )
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SIGNAL — Preview</title>
<style>{CSS}</style>
</head>
<body>
<div class="layout">
  <div class="title">SIGNAL — Tappable Preview</div>
  <div class="brand">Fashion Signal Agent</div>
  <div class="lede">Click around — Home → Upload → Analysis → Results → Export.
    Same design tokens as the React Native app.</div>

  <div class="phone-frame">
    <div id="screens">{body}</div>
  </div>

  <div class="legend">
    Start: <code>Home</code> · Try: <code>Take Photo</code> → <code>Analyze</code> →
    <code>Export</code> · Or tap <code>History</code> top-right
  </div>
</div>

<script>
function show(name) {{
  document.querySelectorAll('.screen').forEach(s => s.classList.remove('active'));
  const el = document.getElementById('screen-' + name);
  if (el) {{
    el.classList.add('active');
    // Reset scroll on new screen
    const sc = el.querySelector('.scroll');
    if (sc) sc.scrollTop = 0;
  }}
}}
show('home');
</script>
</body>
</html>
"""


if __name__ == "__main__":
    (OUT / "index.html").write_text(build_index())
    print(f"wrote {OUT / 'index.html'}  ({(OUT / 'index.html').stat().st_size} bytes)")
