#!/usr/bin/env python3
"""Generate the social-media visuals and site icons into ``social/``.

Every card is an HTML page in the site's own design (``DESIGN.md``: Newsreader,
Hanken Grotesk, paper, ink and one ultramarine accent) rendered to PNG with
headless Chrome. Titles and summaries come from each ``metadata.yml``.

Outputs (committed, so the site build needs neither Chrome nor fonts):

* ``social/og/<slug>.png`` and ``social/og/index.png``: 1200x630 link previews.
* ``social/square/<slug>.png``: 1080x1080 posts (Instagram, LinkedIn, Mastodon).
* ``social/story/<slug>.png``: 1080x1920 stories and reels covers.
* ``social/verse/<slug>.png``: a verse card, for poems that define ``excerpt:``.
* ``social/brand/``: avatar, favicon, Apple touch icon, banner.

Usage
-----
    pip install pyyaml fonttools
    python scripts/make_social.py                # everything
    python scripts/make_social.py --only el-que-es-perd-en-la-traduccio

Set ``CHROME`` to the Chrome/Chromium binary if it is not found automatically.
"""

from __future__ import annotations

import argparse
import html
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO / "site"))
sys.path.insert(0, str(REPO / "shared" / "design"))

from build_site import (  # noqa: E402
    SITE_AUTHOR,
    SITE_TITLE,
    SITE_URL,
    discover_poems,
)

OUT = REPO / "social"
FONTS_CSS = (REPO / "shared" / "design" / "fonts.css").read_text(encoding="utf-8")
DISPLAY_URL = SITE_URL.replace("https://", "")

PAPER, INK, ACCENT = "#fbfbf9", "#111111", "#1d2fd1"

CHROME_CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome",
    "chromium",
    "chromium-browser",
]

# Per-format geometry: canvas, outer padding, title size range, summary size.
FORMATS = {
    "og": dict(w=1200, h=630, pad=64, title=(54, 104), summary=32, small=22, top=30),
    "square": dict(w=1080, h=1080, pad=72, title=(72, 150), summary=40, small=26, top=34),
    "story": dict(w=1080, h=1920, pad=80, title=(80, 168), summary=46, small=28, top=36),
}

BASE_CSS = f"""
{FONTS_CSS}
*{{box-sizing:border-box;margin:0;padding:0}}
html,body{{background:{PAPER};color:{INK};}}
body{{font-family:'Newsreader',Georgia,serif;-webkit-font-smoothing:antialiased;
  font-optical-sizing:auto;overflow:hidden}}
.sans{{font-family:'Hanken Grotesk','Helvetica Neue',Arial,sans-serif}}
.card{{position:relative;display:flex;flex-direction:column;justify-content:space-between}}
.rule{{border-top:2px solid {INK}}}
"""

FIT_JS = """
<script>
/* Shrink the title until it fits its box (long titles wrap to several lines). */
(function(){
  var t=document.getElementById('title'), box=document.getElementById('titlebox');
  var s=+t.dataset.max, min=+t.dataset.min;
  function fits(){ return t.scrollHeight<=box.clientHeight && t.scrollWidth<=box.clientWidth; }
  t.style.fontSize=s+'px';
  while(!fits() && s>min){ s-=2; t.style.fontSize=s+'px'; }
})();
</script>
"""


def find_chrome() -> str:
    """Return a Chrome/Chromium executable path or exit with a clear message."""
    env = os.environ.get("CHROME")
    for cand in ([env] if env else []) + CHROME_CANDIDATES:
        path = shutil.which(cand) or (cand if Path(cand).exists() else None)
        if path:
            return path
    raise SystemExit("Chrome not found. Set CHROME=/path/to/chrome")


def render(chrome: str, page: str, w: int, h: int, out: Path) -> None:
    """Render an HTML string to a PNG of size ``w`` x ``h``."""
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp) / "card.html"
        src.write_text(page, encoding="utf-8")
        subprocess.run(
            [
                chrome,
                "--headless=new",
                "--disable-gpu",
                "--hide-scrollbars",
                "--force-device-scale-factor=1",
                f"--window-size={w},{h}",
                "--virtual-time-budget=3000",
                f"--screenshot={out}",
                src.as_uri(),
            ],
            check=True,
            capture_output=True,
        )


def title_card(fmt: str, number: str, title: str, summary: str, author: str, blue: bool = False) -> str:
    """Return the HTML of a title card (paper, or the blue brand field)."""
    g = FORMATS[fmt]
    bg, fg, num = (ACCENT, PAPER, PAPER) if blue else (PAPER, INK, ACCENT)
    rule = f"2px solid {fg}"
    tmin, tmax = g["title"]
    title_html = html.escape(title).replace("’", "’")
    summary_html = f'<p class="sum">{html.escape(summary)}</p>' if summary else ""
    return f"""<!doctype html><html lang="ca"><meta charset="utf-8"><style>
{BASE_CSS}
body{{background:{bg};color:{fg}}}
.card{{width:{g['w']}px;height:{g['h']}px;padding:{g['pad']}px}}
.top{{display:flex;justify-content:space-between;align-items:baseline;padding-bottom:{g['top']//2}px;border-bottom:{rule}}}
.word{{font-size:{g['top']}px;font-weight:500;letter-spacing:-.005em}}
.num{{font-size:{g['small']+4}px;color:{num};font-variant-numeric:tabular-nums}}
.mid{{flex:1;display:flex;flex-direction:column;justify-content:flex-end;padding:{g['pad']//2}px 0 {g['pad']//2}px;min-height:0}}
#titlebox{{flex:1;min-height:0;display:flex;align-items:flex-end}}
#title{{font-weight:400;line-height:1.02;letter-spacing:-.02em;text-wrap:balance;max-width:100%}}
.sum{{margin-top:{g['pad']//2}px;font-size:{g['summary']}px;line-height:1.28;max-width:24em;text-wrap:balance}}
.bot{{display:flex;justify-content:space-between;align-items:baseline;padding-top:{g['top']//2}px;border-top:{rule};font-size:{g['small']}px}}
</style>
<div class="card">
  <div class="top"><span class="word">{html.escape(SITE_TITLE)}</span><span class="num sans">{html.escape(number)}</span></div>
  <div class="mid"><div id="titlebox"><h1 id="title" data-min="{tmin}" data-max="{tmax}">{title_html}</h1></div>{summary_html}</div>
  <div class="bot sans"><span>{html.escape(author)}</span><span>{html.escape(DISPLAY_URL)}</span></div>
</div>{FIT_JS}</html>"""


def verse_card(title: str, lines: list[str], author: str, number: str) -> str:
    """Return the HTML of a verse card (1080x1080)."""
    body = "<br>".join(html.escape(ln) for ln in lines)
    size = 74 if max(len(ln) for ln in lines) <= 22 else 60
    return f"""<!doctype html><html lang="ca"><meta charset="utf-8"><style>
{BASE_CSS}
.card{{width:1080px;height:1080px;padding:72px}}
.top{{display:flex;justify-content:space-between;align-items:baseline;padding-bottom:17px;border-bottom:2px solid {INK}}}
.word{{font-size:34px;font-weight:500;letter-spacing:-.005em}}
.num{{font-size:30px;color:{ACCENT}}}
.verse{{flex:1;display:flex;align-items:center;font-size:{size}px;line-height:1.3;letter-spacing:-.01em}}
.bot{{display:flex;justify-content:space-between;align-items:baseline;padding-top:17px;border-top:2px solid {INK};font-size:22px;white-space:nowrap;gap:24px}}
</style>
<div class="card">
  <div class="top"><span class="word">{html.escape(SITE_TITLE)}</span><span class="num sans">{html.escape(number)}</span></div>
  <div class="verse"><p>{body}</p></div>
  <div class="bot sans"><span>{html.escape(author)} · {html.escape(title)}</span><span>{html.escape(DISPLAY_URL)}</span></div>
</div></html>"""


def brand_cards() -> dict[str, tuple[str, int, int]]:
    """Return HTML for the avatar and banner on the blue brand field."""
    avatar = f"""<!doctype html><meta charset="utf-8"><style>
{BASE_CSS}
body{{background:{ACCENT};color:{PAPER}}}
.card{{width:800px;height:800px;align-items:center;justify-content:center}}
.c{{font-size:760px;line-height:1;font-weight:400;letter-spacing:-.04em;transform:translateY(-6%)}}
</style><div class="card"><span class="c">c</span></div>"""
    banner = f"""<!doctype html><html lang="ca"><meta charset="utf-8"><style>
{BASE_CSS}
body{{background:{ACCENT};color:{PAPER}}}
.card{{width:1584px;height:396px;padding:56px 72px;justify-content:space-between}}
.t{{font-size:112px;line-height:1;font-weight:400;letter-spacing:-.025em}}
.s{{font-size:36px;line-height:1.25}}
.u{{font-size:24px}}
</style><div class="card"><div class="t">{html.escape(SITE_TITLE)}</div>
<div style="display:flex;justify-content:space-between;align-items:baseline"><div class="s">Poemes en català escrits amb l’ajuda de l’ordinador.</div><div class="u sans">{html.escape(DISPLAY_URL)}</div></div></div></html>"""
    return {"avatar": (avatar, 800, 800), "banner": (banner, 1584, 396)}


def favicon_svg() -> str:
    """Return an SVG favicon: the Newsreader ``c`` as a path on the brand blue."""
    from fontTools.pens.boundsPen import BoundsPen
    from fontTools.pens.svgPathPen import SVGPathPen
    from fontTools.pens.transformPen import TransformPen
    from fontTools.ttLib import TTFont
    from fontTools.varLib import instancer

    src = os.environ.get("NEWSREADER_TTF")
    if not src or not Path(src).exists():
        raise SystemExit("Set NEWSREADER_TTF=/path/to/Newsreader.ttf to build the favicon")
    font = instancer.instantiateVariableFont(TTFont(src), {"wght": 400, "opsz": 72})
    gs = font.getGlyphSet()
    name = font.getBestCmap()[ord("c")]
    bp = BoundsPen(gs)
    gs[name].draw(bp)
    x0, y0, x1, y1 = bp.bounds
    size, target = 64, 40.0
    scale = target / (y1 - y0)
    tx = (size - (x1 - x0) * scale) / 2 - x0 * scale
    ty = size - ((size - target) / 2 + (-y0) * scale)
    pen = SVGPathPen(gs)
    gs[name].draw(TransformPen(pen, (scale, 0, 0, -scale, tx, ty)))
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {size} {size}">'
        f'<rect width="{size}" height="{size}" fill="{ACCENT}"/>'
        f'<path d="{pen.getCommands()}" fill="{PAPER}"/></svg>\n'
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--only", help="generate only this poem slug (plus nothing else)")
    parser.add_argument("--skip-brand", action="store_true", help="skip avatar, banner and icons")
    args = parser.parse_args()

    chrome = find_chrome()
    poems = discover_poems()
    for i, p in enumerate(poems, start=1):
        if args.only and p.slug != args.only:
            continue
        number = f"{i:02d}"
        for fmt, folder in (("og", "og"), ("square", "square"), ("story", "story")):
            g = FORMATS[fmt]
            page = title_card(fmt, number, p.title, p.summary, p.author or SITE_AUTHOR)
            render(chrome, page, g["w"], g["h"], OUT / folder / f"{p.slug}.png")
        if p.excerpt:
            render(chrome, verse_card(p.title, p.excerpt, p.author or SITE_AUTHOR, number), 1080, 1080,
                   OUT / "verse" / f"{p.slug}.png")
        print("ok", p.slug)

    if args.only or args.skip_brand:
        return

    # Collection card (link preview of the home page) on the brand blue.
    intro = "Poemes en català escrits amb l’ajuda de l’ordinador. Cada peça va acompanyada del codi que la va produir."
    for fmt, folder, name in (("og", "og", "index"), ("square", "square", "index"), ("story", "story", "index")):
        g = FORMATS[fmt]
        render(chrome, title_card(fmt, f"{len(poems)} peces", SITE_TITLE, intro, SITE_AUTHOR, blue=True),
               g["w"], g["h"], OUT / folder / f"{name}.png")
    for name, (page, w, h) in brand_cards().items():
        render(chrome, page, w, h, OUT / "brand" / f"{name}.png")
    # Icons derived from the avatar.
    avatar = OUT / "brand" / "avatar.png"
    for name, px in (("apple-touch-icon", 180), ("icon-192", 192), ("icon-512", 512)):
        icon = f'<!doctype html><style>*{{margin:0}}body{{background:{ACCENT}}}img{{width:{px}px;height:{px}px;display:block}}</style><img src="{avatar.as_uri()}">'
        render(chrome, icon, px, px, OUT / "brand" / f"{name}.png")
    (OUT / "brand" / "favicon.svg").write_text(favicon_svg(), encoding="utf-8")
    print("ok brand")


if __name__ == "__main__":
    main()
