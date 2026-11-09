#!/usr/bin/env python3
"""Prepare the book cover for the site: the flat cover, sharp, as a publisher shows it.

An earlier version rendered a faux 3D packshot; it never looked credible, so the
cover is now shown flat, only resized and compressed. Writes ``book/cover-photo.webp``
and ``book/cover-photo.json`` (its pixel size, so the page can reserve the space).

Usage
-----
    pip install pillow
    python scripts/make_cover_photo.py [--cover book/source/cover.jpg] [--width 640]
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from PIL import Image

REPO = Path(__file__).resolve().parent.parent


def render(cover: Path, out: Path, width: int) -> None:
    """Resize the cover to ``width`` pixels and save it as WebP with its size.

    Parameters
    ----------
    cover : Path
        Source cover image (the highest resolution available).
    out : Path
        Destination WebP file; a JSON file with the size is written beside it.
    width : int
        Output width in pixels (about twice the largest display width).
    """
    im = Image.open(cover).convert("RGB")
    height = round(im.height * width / im.width)
    im = im.resize((width, height), Image.LANCZOS)
    out.parent.mkdir(parents=True, exist_ok=True)
    im.save(out, "WEBP", quality=92, method=6)
    out.with_suffix(".json").write_text(json.dumps({"width": width, "height": height}), encoding="utf-8")
    print(out, width, height)


def main() -> None:
    """Parse arguments and render."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cover", type=Path, default=REPO / "book" / "source" / "cover.jpg")
    ap.add_argument("--out", type=Path, default=REPO / "book" / "cover-photo.webp")
    ap.add_argument("--width", type=int, default=640)
    args = ap.parse_args()
    render(args.cover, args.out, args.width)


if __name__ == "__main__":
    main()
