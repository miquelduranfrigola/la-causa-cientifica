#!/usr/bin/env python3
"""Render the book pages that the pieces point to, trimmed and marker-highlighted.

For each ``content/<slug>/metadata.yml`` with a ``book:`` block, renders every
listed printed page from ``book/source/la-causa-cientifica.pdf``, cuts away the
printer's marks (see ``book/book.yml``), draws a raw yellow marker over each
listed sentence and writes ``book/pages/<slug>-p<page>.webp`` plus a JSON
manifest. A provisional excerpt without sentences gets one random sentence,
chosen deterministically from the slug, so the output is stable between runs.

Usage
-----
    pip install pymupdf pillow pyyaml
    python scripts/make_book_pages.py [--pdf PATH] [--only SLUG] [--dpi 170]
"""

from __future__ import annotations

import argparse
import hashlib
import json
import random
import re
import sys
from pathlib import Path

import pymupdf
import yaml
from PIL import Image, ImageChops, ImageDraw, ImageFilter

REPO = Path(__file__).resolve().parent.parent
BOOK = REPO / "book"
MARKER = (255, 226, 40)  # a raw yellow highlighter


def tokens(text: str) -> list[str]:
    """Lower-case word tokens without punctuation, for tolerant matching."""
    return re.findall(r"[\w·]+", text.lower().replace("’", "'").replace("'", " "))


def page_for(doc: pymupdf.Document, printed: int, cfg: dict) -> pymupdf.Page:
    """Return the PDF page that carries a printed page number."""
    index = printed - 1 + int(cfg.get("page_offset", 1)) - 1
    if not 0 <= index < len(doc):
        raise SystemExit(f"printed page {printed} is outside the PDF ({len(doc)} pages)")
    return doc[index]


def trim_rect(page: pymupdf.Page, cfg: dict) -> pymupdf.Rect:
    """Return the visible page area, without the printer's marks."""
    if cfg.get("trim", "trimbox") == "trimbox":
        return page.trimbox if page.trimbox != page.mediabox else page.cropbox
    m = float(cfg.get("margin_mm", 0)) * 72 / 25.4
    r = page.mediabox
    return pymupdf.Rect(r.x0 + m, r.y0 + m, r.x1 - m, r.y1 - m)


def find_runs(page: pymupdf.Page, sentence: str, clip: pymupdf.Rect) -> list[pymupdf.Rect]:
    """Return one rectangle per printed line that the sentence runs over."""
    words = page.get_text("words", clip=clip)  # x0, y0, x1, y1, word, block, line, wordno
    flat: list[tuple[str, tuple]] = []
    for w in words:
        for t in tokens(w[4]):
            flat.append((t, w))
    want = tokens(sentence)
    if not want:
        return []
    for i in range(len(flat) - len(want) + 1):
        if [t for t, _ in flat[i : i + len(want)]] == want:
            lines: dict[tuple, pymupdf.Rect] = {}
            for _, w in flat[i : i + len(want)]:
                key = (w[5], w[6])
                rect = pymupdf.Rect(w[:4])
                lines[key] = lines[key] | rect if key in lines else rect
            return list(lines.values())
    return []


def sentences_of(page: pymupdf.Page, clip: pymupdf.Rect) -> list[str]:
    """Split a page's text into sentences long enough to be worth marking."""
    text = " ".join(page.get_text("text", clip=clip).split())
    text = re.sub(r"^\d{1,3}\s+", "", text)  # running page number
    parts = re.split(r"(?<=[.!?…»])\s+(?=[«\"A-ZÀ-Ý])", text)
    return [p for p in parts if len(tokens(p)) >= 6]


def marker_layer(size: tuple[int, int], boxes: list[tuple[float, float, float, float]], seed: str) -> Image.Image:
    """Draw uneven, slightly overshooting marker strokes (white = no marker)."""
    rnd = random.Random(seed)
    layer = Image.new("L", size, 0)
    d = ImageDraw.Draw(layer)
    for x0, y0, x1, y1 in boxes:
        h = y1 - y0
        pad = h * 0.08
        wob = lambda: rnd.uniform(-h * 0.05, h * 0.05)  # noqa: E731
        poly = [
            (x0 - pad * 2 + wob(), y0 + h * 0.10 + wob()),
            (x1 + pad * 2 + wob(), y0 + h * 0.06 + wob()),
            (x1 + pad * 2 + wob(), y1 - h * 0.04 + wob()),
            (x0 - pad * 2 + wob(), y1 - h * 0.08 + wob()),
        ]
        d.polygon(poly, fill=255)
    return layer.filter(ImageFilter.GaussianBlur(0.8))


def render(doc: pymupdf.Document, printed: int, sentences: list[str], cfg: dict, dpi: int, seed: str):
    """Render one trimmed page with its sentences marked; return image and what was marked."""
    page = page_for(doc, printed, cfg)
    clip = trim_rect(page, cfg)
    scale = dpi / 72
    pix = page.get_pixmap(matrix=pymupdf.Matrix(scale, scale), clip=clip, alpha=False)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)
    chosen = list(sentences)
    if not chosen:
        pool = sentences_of(page, clip)
        if pool:
            chosen = [random.Random(seed).choice(pool)]
    boxes, marked = [], []
    for s in chosen:
        runs = find_runs(page, s, clip)
        if not runs:
            print(f"  warning: sentence not found on p. {printed}: {s[:60]!r}", file=sys.stderr)
            continue
        marked.append(s)
        for r in runs:
            boxes.append(((r.x0 - clip.x0) * scale, (r.y0 - clip.y0) * scale, (r.x1 - clip.x0) * scale, (r.y1 - clip.y0) * scale))
    if boxes:
        yellow = Image.new("RGB", img.size, MARKER)
        mask = marker_layer(img.size, boxes, seed)
        multiplied = ImageChops.multiply(img, yellow)
        img = Image.composite(multiplied, img, mask)
    return img, marked


def main() -> int:
    """Render all pieces' excerpts."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--pdf", type=Path, default=BOOK / "source" / "la-causa-cientifica.pdf")
    ap.add_argument("--out", type=Path, default=BOOK / "pages")
    ap.add_argument("--only", help="only this slug")
    ap.add_argument("--dpi", type=int, default=170)
    args = ap.parse_args()
    if not args.pdf.exists():
        print(f"No PDF at {args.pdf}. Put the book there (see book/README.md).", file=sys.stderr)
        return 1
    cfg = yaml.safe_load((BOOK / "book.yml").read_text(encoding="utf-8"))
    doc = pymupdf.open(args.pdf)
    args.out.mkdir(parents=True, exist_ok=True)
    for meta_path in sorted((REPO / "content").glob("*/metadata.yml")):
        meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
        slug = meta.get("slug")
        if not meta.get("book") or (args.only and args.only != slug):
            continue
        manifest = []
        for ex in meta["book"].get("excerpts", []):
            printed = int(ex["page"])
            seed = hashlib.sha1(f"{slug}:{printed}".encode()).hexdigest()
            img, marked = render(doc, printed, ex.get("sentences") or [], cfg, args.dpi, seed)
            name = f"{slug}-p{printed:03d}.webp"
            img.save(args.out / name, "WEBP", quality=82, method=6)
            manifest.append({"page": printed, "image": name, "width": img.width, "height": img.height, "marked": marked})
            print(f"ok {name} ({len(marked)} marked)")
        (args.out / f"{slug}.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
