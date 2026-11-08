#!/usr/bin/env python3
"""Subset the design fonts and write ``fonts.css`` with base64 ``woff2`` data URIs.

The pages are self-contained (no external requests), so fonts are embedded.
Run this only when the fonts change; ``fonts.css`` is committed.

Sources are the Google Fonts releases (SIL Open Font License 1.1):
Newsreader, Hanken Grotesk and IBM Plex Mono.

Usage
-----
    pip install fonttools brotli
    python shared/design/build_fonts.py --src /path/to/downloaded/ttf
"""

from __future__ import annotations

import argparse
import base64
import io
from pathlib import Path

from fontTools import subset
from fontTools.ttLib import TTFont
from fontTools.varLib import instancer

HERE = Path(__file__).resolve().parent

# Basic Latin, Latin-1, Latin Extended-A (incl. ŀ ĿŀĿ), punctuation, « », middle dot,
# box-drawing characters used by the code figures.
UNICODES = (
    list(range(0x20, 0x7F))
    + list(range(0xA0, 0x180))
    + [
        0x2013,
        0x2014,
        0x2018,
        0x2019,
        0x201C,
        0x201D,
        0x2022,
        0x2026,
        0x2190,
        0x2192,
        0x2197,
    ]
    + list(range(0x2500, 0x2580))
)

# family, source file, CSS weight (or range), style, axis limits for variable fonts
FONTS = [
    ("Newsreader", "Newsreader.ttf", "400 500", "normal", {"wght": (400, 500)}),
    ("Newsreader", "Newsreader-Italic.ttf", "400", "italic", {"wght": 400}),
    ("Hanken Grotesk", "HankenGrotesk.ttf", "400 600", "normal", {"wght": (400, 600)}),
    ("IBM Plex Mono", "PlexMono-Regular.ttf", "400", "normal", None),
]


def to_woff2(path: Path, limits: dict | None) -> bytes:
    """Return a subset ``woff2`` for ``path``, optionally narrowing variable axes."""
    font = TTFont(path)
    if limits:
        font = instancer.instantiateVariableFont(font, limits)
        # Round-trip so the subsetter sees a clean, fully loaded font.
        tmp = io.BytesIO()
        font.save(tmp)
        tmp.seek(0)
        font = TTFont(tmp)
    options = subset.Options()
    options.flavor = "woff2"
    options.layout_features = ["*"]
    options.notdef_outline = True
    sub = subset.Subsetter(options)
    sub.populate(unicodes=UNICODES)
    sub.subset(font)
    buf = io.BytesIO()
    font.flavor = "woff2"
    font.save(buf)
    return buf.getvalue()


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--src", type=Path, required=True, help="folder with the source .ttf files"
    )
    args = parser.parse_args()

    rules = []
    for family, filename, weight, style, limits in FONTS:
        data = to_woff2(args.src / filename, limits)
        b64 = base64.b64encode(data).decode("ascii")
        print(f"{filename}: {len(data) / 1024:.0f} KB")
        rules.append(
            "@font-face{"
            f"font-family:'{family}';font-style:{style};font-weight:{weight};font-display:swap;"
            f"src:url(data:font/woff2;base64,{b64}) format('woff2')"
            "}"
        )
    out = HERE / "fonts.css"
    out.write_text("\n".join(rules) + "\n", encoding="utf-8")
    print(f"wrote {out} ({out.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
