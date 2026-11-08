#!/usr/bin/env python3
"""Measure how tall each piece is when framed on the home page.

The home page reserves that height for every frame before it loads, so nothing
below it moves when the piece arrives. Writes ``site/frame_heights.json``
(``{slug: {"wide": px, "narrow": px}}``). Needs Chrome; set ``CHROME`` if it is
not found. Re-run after changing a piece's layout.

Usage
-----
    python scripts/measure_frames.py
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
OUT = REPO / "site" / "frame_heights.json"
WIDTHS = {"wide": (1200, 900), "narrow": (342, 800)}  # frame width, window height
CANDIDATES = [
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
    "google-chrome",
    "chromium",
    "chromium-browser",
]

HARNESS = """<!doctype html><meta charset="utf-8"><body style="margin:0">
<pre id="out"></pre>
<script>
var pieces = %(pieces)s, frame = %(frame)d, vh = %(vh)d, got = {}, frames = [];
pieces.forEach(function (p) {
  var f = document.createElement('iframe');
  f.style.cssText = 'display:block;border:0;width:' + frame + 'px;height:400px';
  f.src = p.url; document.body.appendChild(f); frames.push([p.slug, f]);
  f.addEventListener('load', function () { f.contentWindow.postMessage({ lcc: 'vh', px: vh }, '*'); });
});
window.addEventListener('message', function (e) {
  if (!e.data || e.data.lcc !== 'height') return;
  frames.forEach(function (x) { if (x[1].contentWindow === e.source) { got[x[0]] = e.data.px; x[1].style.height = e.data.px + 'px'; } });
  document.getElementById('out').textContent = 'RESULT' + JSON.stringify(got) + 'END';
});
</script>"""


def find_chrome() -> str:
    """Return a Chrome/Chromium executable path or exit with a clear message."""
    env = os.environ.get("CHROME")
    for cand in ([env] if env else []) + CANDIDATES:
        path = shutil.which(cand) or (cand if Path(cand).exists() else None)
        if path:
            return path
    raise SystemExit("Chrome not found. Set CHROME=/path/to/chrome")


def measure(chrome: str, pieces: list[dict], frame: int, vh: int) -> dict[str, int]:
    """Return ``{slug: height}`` for the pieces framed ``frame`` px wide."""
    with tempfile.TemporaryDirectory() as tmp:
        page = Path(tmp) / "measure.html"
        page.write_text(HARNESS % {"pieces": json.dumps(pieces), "frame": frame, "vh": vh}, encoding="utf-8")
        run = subprocess.run(
            [
                chrome, "--headless=new", "--hide-scrollbars", "--allow-file-access-from-files",
                f"--window-size={frame},{vh}", "--virtual-time-budget=15000", "--dump-dom", page.as_uri(),
            ],
            check=True, capture_output=True, text=True,
        )
    found = re.search(r"RESULT(\{.*?\})END", run.stdout)
    return json.loads(found.group(1)) if found else {}


def main() -> None:
    """Measure every piece at both widths and write the JSON."""
    chrome = find_chrome()
    pieces = [{"slug": d.name, "url": (d / "index.html").as_uri()}
              for d in sorted((REPO / "content").iterdir()) if (d / "index.html").exists()]
    result: dict[str, dict[str, int]] = {p["slug"]: {} for p in pieces}
    for name, (frame, vh) in WIDTHS.items():
        for slug, px in measure(chrome, pieces, frame, vh).items():
            result[slug][name] = px
    missing = [s for s, v in result.items() if len(v) < len(WIDTHS)]
    if missing:
        raise SystemExit(f"No height reported for: {', '.join(missing)}")
    OUT.write_text(json.dumps(result, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}")


if __name__ == "__main__":
    main()
