"""Render preview HTML for each SIGNAL screen using the design system,
then screenshot via Playwright at iPhone dimensions.

Run from /home/user/signal:
    backend/.venv/bin/python preview/build.py
"""
from __future__ import annotations

import asyncio
import base64
import json
import subprocess
import sys
from pathlib import Path
from io import BytesIO

from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parent
SCREEN_DIR = ROOT / "screens"
SHOT_DIR = ROOT / "shots"
SCREEN_DIR.mkdir(exist_ok=True)
SHOT_DIR.mkdir(exist_ok=True)

# Phone dimensions (iPhone 14 logical points)
W, H = 390, 844


def load_report() -> dict:
    return json.loads(Path("/tmp/sample_report.json").read_text())


def fake_fashion_thumb(w: int, h: int, tone: tuple[int, int, int], accent: tuple[int, int, int]) -> str:
    """Build a simple gradient + silhouette block as a data URI to mimic
    a fashion photo without needing real assets."""
    img = Image.new("RGB", (w, h), tone)
    draw = ImageDraw.Draw(img)
    # softly darker bottom band — gives photo-like depth
    for y in range(h):
        f = y / h
        r = int(tone[0] * (1 - 0.18 * f))
        g = int(tone[1] * (1 - 0.18 * f))
        b = int(tone[2] * (1 - 0.18 * f))
        draw.line([(0, y), (w, y)], fill=(r, g, b))
    # garment-ish silhouette
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
    # neckline
    draw.ellipse(
        [(cx - w * 0.10, h * 0.15), (cx + w * 0.10, h * 0.24)],
        fill=tone,
    )
    img = img.filter(ImageFilter.GaussianBlur(0.6))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=80)
    return "data:image/jpeg;base64," + base64.b64encode(buf.getvalue()).decode()


PALETTE = [
    ((232, 226, 213), (78, 70, 62)),    # warm sand / chocolate tee
    ((226, 220, 207), (47, 48, 46)),    # stone / charcoal
    ((215, 207, 191), (118, 96, 76)),   # taupe / camel
    ((240, 234, 222), (60, 62, 58)),    # cream / olive
    ((202, 196, 184), (74, 70, 62)),    # mushroom
    ((228, 222, 209), (43, 60, 55)),    # cream / emerald
]


THUMBS = [fake_fashion_thumb(220, 280, t, a) for t, a in PALETTE]

# Shared CSS — locked to the same tokens the RN app uses
BASE_CSS = """
:root {
  --bg: #FBF8F2;
  --surface: #FFFFFF;
  --surface-muted: #F4EFE5;
  --text: #1F1F1D;
  --text-muted: #6B6760;
  --text-subtle: #9A938A;
  --divider: #E6E2D8;
  --emerald: #1F5F4A;
  --emerald-soft: #E3EDE7;
  --burgundy: #7A2A2A;
  --burgundy-soft: #F3E3E3;
}
* { box-sizing: border-box; -webkit-font-smoothing: antialiased; }
html, body { margin: 0; padding: 0; }
body {
  width: 390px; height: 844px;
  background: var(--bg);
  color: var(--text);
  font-family: -apple-system, 'SF Pro Text', Inter, system-ui, sans-serif;
  overflow: hidden;
  position: relative;
}
.kicker {
  font-size: 11px; font-weight: 600; letter-spacing: 1.2px;
  text-transform: uppercase; color: var(--text-muted);
}
.kicker--emerald { color: var(--emerald); }
.kicker--burgundy { color: var(--burgundy); }
.card {
  background: var(--surface);
  border-radius: 22px;
  padding: 22px;
  box-shadow: 0 6px 16px rgba(31,31,29,0.06);
}
.card--flat {
  background: var(--surface-muted);
  border-radius: 14px;
  padding: 18px;
  box-shadow: none;
}
.btn {
  height: 54px;
  border-radius: 999px;
  display: flex; align-items: center; justify-content: center;
  font-size: 16px; font-weight: 600; letter-spacing: 0.1px;
}
.btn--primary { background: var(--text); color: #fff; }
.btn--secondary {
  background: var(--surface);
  color: var(--text);
  border: 1px solid var(--divider);
}
.statusbar {
  height: 44px;
  display: flex; align-items: center; justify-content: space-between;
  padding: 0 24px;
  font-size: 13px; font-weight: 600;
}
.statusbar .right { display: flex; gap: 6px; align-items: center; }
.dot { width: 4px; height: 4px; background: #1F1F1D; border-radius: 50%; }
"""


def html_doc(body: str, extra_css: str = "") -> str:
    return f"""<!doctype html>
<html><head>
<meta charset="utf-8">
<style>{BASE_CSS}{extra_css}</style>
</head><body>{body}</body></html>"""


# ---------- 1. Home ----------
def screen_home() -> str:
    return html_doc(f"""
<div class="statusbar">
  <span>9:41</span>
  <div class="right">
    <span style="font-size:11px">•••</span>
    <span style="font-size:11px">▮▮▮</span>
  </div>
</div>
<div style="padding: 8px 24px 0 24px; display:flex; justify-content:flex-end;">
  <span style="font-size:13px; color: var(--text-muted)">History</span>
</div>
<div style="padding: 0 24px; height: 620px; display: flex; flex-direction: column; justify-content: center;">
  <div class="kicker">Fashion Signal Agent</div>
  <div style="font-size: 64px; line-height: 64px; font-weight: 800;
              color: var(--text); margin-top: 18px; letter-spacing: -2px;">SIGNAL</div>
  <div style="font-size: 15px; line-height: 22px; color: var(--text-muted);
              margin-top: 22px; max-width: 320px;">
    Snap products. Understand what brands are doing. Decide what to design next.
  </div>
</div>
<div style="padding: 0 24px; position:absolute; bottom: 60px; left:0; right:0;">
  <div class="btn btn--primary">Take Photo</div>
  <div style="height: 12px"></div>
  <div class="btn btn--secondary">Upload Images</div>
</div>
<div style="position:absolute; bottom: 20px; left:0; right:0; text-align:center;
            font-size: 11px; color: var(--text-subtle); padding: 0 24px; line-height: 15px;">
  Analysis focuses on apparel &amp; design attributes, not personal identity.<br>
  Images are processed in memory and never stored.
</div>
""")


# ---------- 2. Upload Preview ----------
def screen_upload() -> str:
    tiles = "".join(
        f'<div style="background-image:url({t});background-size:cover;background-position:center;'
        f'aspect-ratio:1;border-radius:14px"></div>'
        for t in THUMBS
    )
    return html_doc(f"""
<div class="statusbar"><span>9:41</span></div>
<div style="display:flex; padding: 4px 16px 12px 16px; align-items:center;">
  <div style="width:48px; font-size: 22px; color: var(--text);">←</div>
  <div style="flex:1; text-align:center; font-size:16px; font-weight:600;">Preview</div>
  <div style="width:48px"></div>
</div>
<div style="padding: 0 24px 16px 24px;">
  <div class="kicker">We detected</div>
  <div style="font-size: 26px; font-weight: 700; color: var(--text); margin-top:4px;">Competitor Store Walk</div>
  <div style="font-size: 13px; color: var(--text-muted); margin-top:4px;">
    6 images · we'll confirm after analysis
  </div>
</div>
<div style="padding: 0 24px; display:grid; grid-template-columns: repeat(3, 1fr);
            gap: 8px;">
  {tiles}
</div>
<div style="position:absolute; bottom:24px; left:0; right:0; padding: 0 24px;">
  <div style="text-align:center; padding: 12px 0; color: var(--text-muted);
              font-size: 13px; text-decoration: underline;">Change selection</div>
  <div class="btn btn--primary">Analyze 6 Images</div>
</div>
""")


# ---------- 3. Analysis (mid-stream) ----------
def screen_analysis() -> str:
    steps = [
        ("Reading images", "done"),
        ("Detecting context", "done"),
        ("Selecting brand cohort", "active"),
        ("Pulling live retailer signals", "pending"),
        ("Writing the brief", "pending"),
    ]
    def render(label: str, state: str) -> str:
        color = {"done": "var(--text)", "active": "var(--emerald)", "pending": "var(--divider)"}[state]
        text_color = {"done": "var(--text-muted)", "active": "var(--text)", "pending": "var(--text-subtle)"}[state]
        weight = "600" if state == "active" else "400"
        ring = ""
        if state == "active":
            ring = ('<div style="position:absolute; width:20px; height:20px; border-radius:50%;'
                    'background: var(--emerald); opacity:0.18"></div>')
        return f"""
<div style="display:flex; align-items:center; padding: 12px 0;">
  <div style="width:24px; display:flex; justify-content:center; align-items:center;
              position:relative; margin-right:12px;">
    {ring}
    <div style="width:8px; height:8px; border-radius:50%; background:{color};"></div>
  </div>
  <div style="font-size:15px; color:{text_color}; font-weight:{weight};">{label}</div>
</div>
"""
    rows = "".join(render(lbl, st) for lbl, st in steps)
    return html_doc(f"""
<div class="statusbar"><span>9:41</span></div>
<div style="padding: 200px 32px 0 32px;">
  <div class="kicker">Analyzing</div>
  <div style="font-size: 26px; font-weight: 700; color: var(--text);
              margin-top:4px; margin-bottom: 32px;">Reading the floor</div>
  {rows}
</div>
""")


# ---------- 4. Results ----------
def screen_results(report: dict) -> str:
    sim_palette = {
        "Strong":   ("var(--emerald-soft)",  "var(--emerald)"),
        "Adjacent": ("#EFEAE0",              "var(--text)"),
        "Moderate": ("#EFEAE0",              "var(--text-muted)"),
        "Weak":     ("#F4EFE5",              "var(--text-subtle)"),
    }
    # hero collage (4 thumbs in a 2x2)
    collage_tiles = "".join(
        f'<div style="background-image:url({THUMBS[i]}); background-size:cover; background-position:center;"></div>'
        for i in range(4)
    )
    brand_rows = []
    for i, sig in enumerate(report["brand_signals"]):
        bg, fg = sim_palette[sig["similarity"]]
        divider = "border-bottom: 1px solid var(--divider);" if i < len(report["brand_signals"]) - 1 else ""
        brand_rows.append(f"""
<div style="padding: 14px 0; {divider}">
  <div style="display:flex; justify-content:space-between; align-items:center;">
    <div style="font-size:16px; font-weight:600;">{sig['brand']}</div>
    <div style="background:{bg}; color:{fg}; font-size:11px; font-weight:600;
                letter-spacing:0.6px; padding: 4px 10px; border-radius: 999px;">
      {sig['similarity'].upper()}
    </div>
  </div>
  <div style="font-size:13px; color:var(--text-muted); margin-top:4px; line-height:18px;">
    {sig['rationale']}
  </div>
</div>
""")
    direction_rows = []
    for i, d in enumerate(report["directions"]):
        divider = "border-bottom: 1px solid var(--divider);" if i < len(report["directions"]) - 1 else ""
        direction_rows.append(f"""
<div style="padding: 14px 0; {divider}">
  <div style="font-size:11px; font-weight:700; color: var(--burgundy);
              letter-spacing:1.2px;">{d['label'].upper()}</div>
  <div style="font-size:18px; font-weight:600; margin-top:4px;">{d['title']}</div>
  <div style="font-size:14px; color: var(--text-muted); margin-top:6px; line-height:21px;">
    {d['description']}
  </div>
</div>
""")
    mode_label = report["mode"].replace("_", " ").title()
    return html_doc(f"""
<div class="statusbar"><span>9:41</span></div>
<div style="display:flex; padding: 4px 16px 12px 16px; align-items:center;">
  <div style="width:48px; font-size: 22px; color: var(--text);">←</div>
  <div style="flex:1"></div>
  <div style="color: var(--emerald); font-size:13px; font-weight:600;">Export</div>
</div>
<div style="padding: 0 24px 100px 24px; overflow:hidden;">
  <div style="display:flex; align-items:center; margin-bottom: 18px;">
    <div style="width:88px; height:88px; border-radius:14px; overflow:hidden;
                display:grid; grid-template-columns: 1fr 1fr; gap:2px; background: var(--surface-muted);">
      {collage_tiles}
    </div>
    <div style="flex:1; margin-left:16px;">
      <div class="kicker">{mode_label} · {report["image_count"]} images</div>
      <div style="font-size:24px; font-weight:700; line-height:28px; margin-top:4px;">
        {report["observation"]}
      </div>
    </div>
  </div>
  <div style="font-size:15px; color: var(--text-muted); margin-bottom: 16px;">
    {report["summary"]}
  </div>

  <div class="card" style="margin-bottom:16px;">
    <div class="kicker">Brand Signals</div>
    <div style="height: 8px"></div>
    {''.join(brand_rows[:3])}
  </div>

  <div class="card">
    <div class="kicker">Recommended Directions</div>
    {''.join(direction_rows)}
  </div>
</div>
""")


# ---------- 5. History ----------
def screen_history(report: dict) -> str:
    today_items = [
        {"obs": report["observation"], "mode": report["mode"], "count": report["image_count"], "thumbs": THUMBS[:4]},
        {"obs": "Heritage Denim Revival", "mode": "store_walk", "count": 9, "thumbs": THUMBS[2:6]},
    ]
    yesterday_items = [
        {"obs": "Sport-Lux Athleisure", "mode": "moodboard", "count": 12, "thumbs": THUMBS[1:5]},
    ]
    def entry(it):
        thumbs = it["thumbs"]
        # 2x2 collage
        tiles = "".join(
            f'<div style="background-image:url({t}); background-size:cover; background-position:center;"></div>'
            for t in thumbs[:4]
        )
        mode_label = it["mode"].replace("_", " ").title()
        return f"""
<div class="card--flat" style="display:flex; align-items:center; margin-bottom:12px;
                                background: var(--surface); border: 1px solid var(--divider);
                                border-radius: 14px; padding: 12px;">
  <div style="width:72px; height:72px; border-radius:10px; overflow:hidden;
              display:grid; grid-template-columns: 1fr 1fr; gap:2px; background: var(--surface-muted);">
    {tiles}
  </div>
  <div style="flex:1; margin-left: 14px;">
    <div style="font-size:16px; font-weight:600; line-height:20px;">{it["obs"]}</div>
    <div style="font-size:13px; color: var(--text-muted); margin-top:4px;">
      {mode_label} · {it["count"]} images
    </div>
  </div>
</div>
"""
    return html_doc(f"""
<div class="statusbar"><span>9:41</span></div>
<div style="display:flex; padding: 4px 16px 12px 16px; align-items:center;">
  <div style="width:48px; font-size: 22px; color: var(--text);">←</div>
  <div style="flex:1; text-align:center; font-size:16px; font-weight:600;">History</div>
  <div style="width:48px; text-align:right; color: var(--burgundy); font-size:13px;">Clear</div>
</div>
<div style="padding: 0 24px;">
  <div class="kicker">Today</div>
  <div style="height:8px"></div>
  {''.join(entry(it) for it in today_items)}
  <div style="height:16px"></div>
  <div class="kicker">Yesterday</div>
  <div style="height:8px"></div>
  {''.join(entry(it) for it in yesterday_items)}
</div>
""")


# ---------- 6. Export ----------
def screen_export(report: dict) -> str:
    return html_doc(f"""
<div class="statusbar"><span>9:41</span></div>
<div style="display:flex; padding: 4px 16px 12px 16px; align-items:center;">
  <div style="width:48px; font-size: 22px; color: var(--text);">←</div>
  <div style="flex:1; text-align:center; font-size:16px; font-weight:600;">Export</div>
  <div style="width:48px"></div>
</div>
<div style="padding: 0 24px;">
  <div class="kicker">This brief</div>
  <div style="font-size:26px; font-weight:700; margin-top:4px; margin-bottom:18px;">
    {report["observation"]}
  </div>

  <div class="card" style="margin-bottom:16px;">
    <div class="kicker">PDF</div>
    <div style="font-size:13px; color: var(--text-muted); margin-top:4px;">
      Generate an editorial PDF you can save or share.
    </div>
    <div style="height:14px"></div>
    <div class="btn btn--primary">Generate PDF</div>
  </div>

  <div class="card" style="margin-bottom:16px;">
    <div class="kicker">Email</div>
    <div style="font-size:13px; color: var(--text-muted); margin-top:4px;">
      We'll prepare the PDF and surface a download link you can share.
    </div>
    <div style="height:14px"></div>
    <div style="background: var(--surface-muted); height: 50px; border-radius: 14px;
                display:flex; align-items:center; padding: 0 16px; color: var(--text-subtle);
                font-size: 15px;">
      designer@brand.com
    </div>
    <div style="height:14px"></div>
    <div class="btn btn--secondary">Prepare for Email</div>
  </div>

  <div class="card--flat" style="background: var(--emerald-soft);">
    <div class="kicker kicker--emerald">Download link</div>
    <div style="font-size:13px; color: var(--emerald); margin-top:4px;
                word-break:break-all;">https://signal.app/reports/d5deb994-9807</div>
    <div style="height:14px"></div>
    <div style="display:inline-block; background: var(--emerald); color: #fff;
                padding: 8px 16px; border-radius: 999px;
                font-size:13px; font-weight:600;">Open / Share</div>
  </div>
</div>
""")


async def main() -> None:
    report = load_report()

    pages: dict[str, str] = {
        "1_home.html":     screen_home(),
        "2_upload.html":   screen_upload(),
        "3_analysis.html": screen_analysis(),
        "4_results.html":  screen_results(report),
        "5_history.html":  screen_history(report),
        "6_export.html":   screen_export(report),
    }
    for name, html in pages.items():
        (SCREEN_DIR / name).write_text(html)

    # Use Playwright to screenshot at iPhone dimensions
    from playwright.async_api import async_playwright

    async with async_playwright() as p:
        chrome = "/opt/pw-browsers/chromium-1194/chrome-linux/chrome"
        browser = await p.chromium.launch(executable_path=chrome)
        context = await browser.new_context(
            viewport={"width": W, "height": H},
            device_scale_factor=2,
        )
        for name in pages:
            page = await context.new_page()
            await page.goto(f"file://{SCREEN_DIR / name}")
            shot = SHOT_DIR / name.replace(".html", ".png")
            await page.screenshot(path=str(shot), full_page=False)
            print(f"shot {shot}")
            await page.close()
        await browser.close()


if __name__ == "__main__":
    try:
        from playwright.async_api import async_playwright  # noqa: F401
    except ImportError:
        print("Installing playwright...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "playwright"])
        subprocess.check_call([sys.executable, "-m", "playwright", "install", "chromium"])
    asyncio.run(main())
