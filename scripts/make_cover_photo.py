#!/usr/bin/env python3
"""Render a studio-style packshot of the book from the cover image.

The book stands slightly turned so that the page block shows on the right, as in
a publisher's product photograph: a flat cover with a paperback hinge crease, paper
grain, a lit page block and soft contact shadows, on a transparent ground so
the image melts into the page. Writes ``book/cover-photo.webp`` with a transparent background.

Usage
-----
    pip install pillow numpy
    python scripts/make_cover_photo.py [--cover book/source/cover.jpg]
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

REPO = Path(__file__).resolve().parent.parent
PAPER = (251, 251, 249)
SCALE = 2  # supersampling for clean edges


def perspective_coeffs(dst: list[tuple[float, float]], src: list[tuple[float, float]]) -> list[float]:
    """Solve the 8 coefficients PIL needs to map output points back to source points."""
    rows, rhs = [], []
    for (x, y), (u, v) in zip(dst, src, strict=True):
        rows.append([x, y, 1, 0, 0, 0, -u * x, -u * y])
        rows.append([0, 0, 0, x, y, 1, -v * x, -v * y])
        rhs += [u, v]
    return np.linalg.solve(np.array(rows, float), np.array(rhs, float)).tolist()


def grain(size: tuple[int, int], amount: float, seed: int) -> Image.Image:
    """Fine paper grain as a mid-grey layer (128 = neutral)."""
    rng = np.random.default_rng(seed)
    noise = rng.normal(0, amount, (size[1], size[0]))
    soft = np.array(Image.fromarray(np.clip(128 + noise, 0, 255).astype("uint8")).filter(ImageFilter.GaussianBlur(0.6)))
    return Image.fromarray(soft).convert("L")


def prepare_cover(path: Path, width: int, height: int) -> Image.Image:
    """Return the cover with hinge crease, edge wear, light fall-off and grain."""
    cover = Image.open(path).convert("RGB").resize((width, height), Image.LANCZOS)
    shade = np.ones((height, width), float)
    x = np.arange(width)[None, :] / width
    y = np.arange(height)[:, None] / height
    shade *= 1.04 - 0.07 * x - 0.04 * y  # soft light from the upper left
    hinge = int(width * 0.062)
    for dx, k in ((-3, 0.05), (0, -0.11), (2, 0.06), (5, 0.025)):  # groove: highlight, shadow, highlight
        shade[:, max(hinge + dx, 0) : hinge + dx + 2] *= 1 + k
    a = np.array(cover, float) * shade[..., None]
    g = np.array(grain((width, height), 5.0, 7), float)[..., None] - 128
    a = a + g * 0.55
    out = Image.fromarray(np.clip(a, 0, 255).astype("uint8"))
    d = ImageDraw.Draw(out)
    d.rectangle([0, 0, width - 1, height - 1], outline=(255, 255, 255, 0))
    edge = Image.new("L", (width, height), 0)
    ImageDraw.Draw(edge).rectangle([0, 0, width - 1, height - 1], outline=255, width=3)
    edge = edge.filter(ImageFilter.GaussianBlur(1.2))
    light = Image.new("RGB", (width, height), (255, 255, 255))
    return Image.composite(Image.blend(out, light, 0.0), out, Image.eval(edge, lambda v: 0)) if False else Image.composite(
        Image.blend(out, light, 0.28), out, edge
    )


def render(cover_path: Path, out_path: Path, turn_deg: float = 24.0) -> None:
    """Compose the packshot and save it."""
    canvas_w, canvas_h = 1500 * SCALE, 1500 * SCALE
    book_w, book_h, thick = 700 * SCALE, 1056 * SCALE, 62 * SCALE
    theta = math.radians(turn_deg)
    cover = prepare_cover(cover_path, 1100, 1658)

    fw = book_w * math.cos(theta)  # foreshortened front width
    bw = thick * math.sin(theta)  # visible page-block width
    k = 0.045  # perspective: the right edge is nearer, so taller
    cx, cy = canvas_w * 0.47, canvas_h * 0.5
    left = cx - (fw + bw) / 2
    hl, hr = book_h * (1 - k / 2), book_h * (1 + k / 2)
    front = [(left, cy - hl / 2), (left + fw, cy - hr / 2), (left + fw, cy + hr / 2), (left, cy + hl / 2)]
    hb = hr * (1 + k * 0.4)
    block = [front[1], (left + fw + bw, cy - hb / 2 + 8), (left + fw + bw, cy + hb / 2 - 8), front[2]]

    # --- shadows (drawn first, on the paper) -------------------------------------
    base = Image.new("RGBA", (canvas_w, canvas_h), (0, 0, 0, 0))
    sh = Image.new("L", (canvas_w, canvas_h), 0)
    sd = ImageDraw.Draw(sh)
    a_pt, b_pt, c_pt = front[3], front[2], block[2]  # the bottom edge follows the perspective
    sd.polygon(
        [(a_pt[0] + 10 * SCALE, a_pt[1] - 6), (c_pt[0], c_pt[1] - 6),
         (c_pt[0] + 150 * SCALE, c_pt[1] + 22 * SCALE), (a_pt[0] + 140 * SCALE, a_pt[1] + 30 * SCALE)],
        fill=200,
    )
    wide = sh.filter(ImageFilter.GaussianBlur(34 * SCALE))
    sh2 = Image.new("L", (canvas_w, canvas_h), 0)
    ImageDraw.Draw(sh2).polygon(
        [(a_pt[0], a_pt[1] - 6), (b_pt[0], b_pt[1] - 6), (c_pt[0] + 6 * SCALE, c_pt[1] - 6),
         (c_pt[0] + 14 * SCALE, c_pt[1] + 6 * SCALE), (a_pt[0] + 10 * SCALE, a_pt[1] + 6 * SCALE)],
        fill=255,
    )
    tight = sh2.filter(ImageFilter.GaussianBlur(5 * SCALE))
    # The shadows live in the alpha channel, so the photo melts into any background.
    alpha = 1 - (1 - 0.30 * np.array(wide, float) / 255) * (1 - 0.45 * np.array(tight, float) / 255)
    shadow = np.zeros((canvas_h, canvas_w, 4), "uint8")
    shadow[..., 3] = np.clip(alpha * 255, 0, 255).astype("uint8")
    base = Image.fromarray(shadow, "RGBA")

    # --- page block: lit cream with fine leaf lines ------------------------------------
    bx0, bx1 = int(min(p[0] for p in block)), int(max(p[0] for p in block)) + 1
    by0, by1 = int(min(p[1] for p in block)) - 2, int(max(p[1] for p in block)) + 2
    bimg = Image.new("RGB", (bx1 - bx0, by1 - by0), (240, 236, 226))
    rng = np.random.default_rng(3)
    arr = np.array(bimg, float)
    xs = np.linspace(0, 1, arr.shape[1])[None, :, None]
    arr *= 1.0 - 0.18 * xs  # the far edge falls into shade
    rows = rng.normal(0, 3.5, (arr.shape[0], 1, 1))
    rows = np.array(Image.fromarray(np.clip(128 + rows[:, 0, :].repeat(3, 1), 0, 255).astype("uint8")).filter(ImageFilter.GaussianBlur(0.4)), float)[:, None, :] - 128
    arr = arr + rows * 0.9
    bimg = Image.fromarray(np.clip(arr, 0, 255).astype("uint8"))
    mask = Image.new("L", bimg.size, 0)
    ImageDraw.Draw(mask).polygon([(x - bx0, y - by0) for x, y in block], fill=255)
    base.paste(bimg, (bx0, by0), mask.filter(ImageFilter.GaussianBlur(0.8)))

    # --- front cover warped into place ---------------------------------------------------
    cw, ch = cover.size
    coeffs = perspective_coeffs(front, [(0, 0), (cw, 0), (cw, ch), (0, ch)])
    warped = cover.transform((canvas_w, canvas_h), Image.PERSPECTIVE, coeffs, Image.BICUBIC)
    fmask = Image.new("L", (canvas_w, canvas_h), 0)
    ImageDraw.Draw(fmask).polygon(front, fill=255)
    base.paste(warped, (0, 0), fmask.filter(ImageFilter.GaussianBlur(0.8)))

    # --- thin light rim where cover meets the page block --------------------------------
    rim = ImageDraw.Draw(base)
    rim.line([front[1], front[2]], fill=(214, 209, 196, 255), width=2 * SCALE)

    out = base.resize((canvas_w // SCALE, canvas_h // SCALE), Image.LANCZOS)
    bbox = content_bbox(out)
    out = out.crop(bbox)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out.save(out_path, "WEBP", quality=92, method=6)
    out_path.with_suffix(".json").write_text(json.dumps({"width": out.width, "height": out.height}), encoding="utf-8")
    print(f"ok {out_path} {out.size}")


def content_bbox(img: Image.Image) -> tuple[int, int, int, int]:
    """Crop box around everything visible (alpha above a small threshold), with a margin."""
    x0, y0, x1, y1 = img.getchannel("A").point(lambda v: 255 if v > 3 else 0).getbbox()
    m = 90
    return max(x0 - m, 0), max(y0 - m, 0), min(x1 + m, img.width), min(y1 + m, img.height)


def main() -> None:
    """Parse arguments and render."""
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--cover", type=Path, default=REPO / "book" / "source" / "cover.jpg")
    ap.add_argument("--out", type=Path, default=REPO / "book" / "cover-photo.webp")
    ap.add_argument("--turn", type=float, default=24.0, help="degrees the book is turned")
    args = ap.parse_args()
    render(args.cover, args.out, args.turn)


if __name__ == "__main__":
    main()
