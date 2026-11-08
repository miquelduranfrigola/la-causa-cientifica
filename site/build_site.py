#!/usr/bin/env python3
"""Build the *La causa científica* static website into ``_site/``.

The single source of truth is each ``content/<slug>/`` folder: this reads every
``metadata.yml``. A piece with a ``page:`` key is served from its self-contained
``index.html`` verbatim; otherwise ``poem.md`` is rendered. The home page is a
catalogue with a drawn legend; a piece is a plain page at ``<slug>/`` with the
masthead, prev/next links and a "next piece" ending added (see DESIGN.md); the
About page is ``sobre/``. Authors never edit HTML.

Poetry-aware rendering (the important part)
-------------------------------------------
Plain Markdown collapses single line breaks, which destroys verse and stanza
structure. Instead we render ``poem.md`` ourselves:

* a blank line separates **estrofes** (stanzas) -> each becomes its own block,
* every line inside a stanza is a **verse** -> kept on its own line,
* fenced ``` code blocks are preserved verbatim (used by poems whose body is a
  generated diagram, e.g. the mutation tree), and
* the leading ``# Title`` and HTML comments are stripped (the title comes from
  ``metadata.yml``).

Usage
-----
    python site/build_site.py                 # -> ./_site
    python site/build_site.py --out public
"""

from __future__ import annotations

import argparse
import html
import json
import re
import shutil
from dataclasses import dataclass
from pathlib import Path

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

SITE_DIR = Path(__file__).resolve().parent
REPO_ROOT = SITE_DIR.parent
POEMS_DIR = REPO_ROOT / "content"
TEMPLATES_DIR = SITE_DIR / "templates"
STATIC_DIR = SITE_DIR / "static"
BOOK_DIR = SITE_DIR.parent / "book"
DESIGN_DIR = REPO_ROOT / "shared" / "design"
SOCIAL_DIR = REPO_ROOT / "social"

SITE_TITLE = "La causa científica"
SITE_AUTHOR = "Miquel Duran-Frigola"
SITE_INTRO = (
    "Poemes i imatges fets amb codi, que amplien el llibre La causa científica. "
    "Cada peça explica com es va fer i on és al llibre."
)
REPO_URL = "https://github.com/miquelduranfrigola/la-causa-cientifica"
SITE_URL = "https://miquelduranfrigola.github.io/la-causa-cientifica"

_COMMENT_RE = re.compile(r"<!--.*?-->", re.DOTALL)
_TITLE_RE = re.compile(r"^\s*#\s+.*$", re.MULTILINE)


@dataclass
class Poem:
    """One piece of the collection, as read from its ``metadata.yml``."""
    slug: str
    title: str
    date: str
    order: int | None
    author: str
    language: str
    summary: str
    excerpt: list[str]
    description_html: str
    tools: list[dict]
    tags: list[str]
    poem_html: str
    page_src: Path | None = None  # optional self-contained page to serve verbatim


# --------------------------------------------------------------------------- #
# Poetry-aware rendering
# --------------------------------------------------------------------------- #
def render_poem_body(markdown_text: str) -> str:
    """Render a ``poem.md`` body into HTML that preserves verses and estrofes."""
    text = _COMMENT_RE.sub("", markdown_text)
    text = _TITLE_RE.sub("", text, count=1)
    lines = text.replace("\r\n", "\n").split("\n")

    blocks: list[str] = []
    i = 0
    n = len(lines)
    while i < n:
        stripped = lines[i].strip()

        # Fenced code block -> <pre> preserved verbatim (e.g. a mutation tree).
        if stripped.startswith("```"):
            code: list[str] = []
            i += 1
            while i < n and not lines[i].strip().startswith("```"):
                code.append(lines[i])
                i += 1
            i += 1  # consume the closing fence
            escaped = html.escape("\n".join(code))
            blocks.append(f'<pre class="poem-figure">{escaped}</pre>')
            continue

        # Blank line -> stanza separator.
        if stripped == "":
            i += 1
            continue

        # Gather one stanza (consecutive non-blank, non-fence lines).
        verses: list[str] = []
        while i < n and lines[i].strip() != "" and not lines[i].strip().startswith("```"):
            verses.append(html.escape(lines[i].rstrip()))
            i += 1
        stanza = '<br>\n'.join(verses)
        blocks.append(f'<p class="estrofa">{stanza}</p>')

    return "\n".join(blocks)


def render_paragraphs(text: str | None) -> str:
    """Render a prose field (e.g. description) into <p> paragraphs.

    Unlike a poem, prose reflows: single newlines (YAML line-wrapping) are joined
    with a space; only blank lines start a new paragraph.
    """
    if not text:
        return ""
    chunks = [c.strip() for c in text.replace("\r\n", "\n").split("\n\n")]
    out = []
    for chunk in chunks:
        if not chunk:
            continue
        flowed = " ".join(line.strip() for line in chunk.split("\n"))
        out.append(f"<p>{html.escape(flowed)}</p>")
    return "\n".join(out)


# --------------------------------------------------------------------------- #
# Loading
# --------------------------------------------------------------------------- #
def load_poem(folder: Path) -> Poem | None:
    meta_path = folder / "metadata.yml"
    poem_path = folder / "poem.md"
    if not meta_path.exists() or not poem_path.exists():
        return None

    meta = yaml.safe_load(meta_path.read_text(encoding="utf-8")) or {}
    for required in ("title", "slug", "date"):
        if not meta.get(required):
            raise SystemExit(f"{meta_path}: missing required field '{required}'")
    if meta["slug"] != folder.name:
        raise SystemExit(f"{meta_path}: slug '{meta['slug']}' != folder '{folder.name}'")

    # Optional: a poem may ship a self-contained HTML page (an immersive gallery)
    # to serve instead of the templated poem.md — e.g. the mutation animation.
    page_src = None
    if meta.get("page"):
        candidate = (folder / str(meta["page"])).resolve()
        if candidate.exists():
            page_src = candidate
        else:
            raise SystemExit(f"{meta_path}: page '{meta['page']}' not found at {candidate}")

    order = meta.get("order")
    return Poem(
        slug=str(meta["slug"]),
        title=str(meta["title"]),
        date=str(meta["date"]),
        order=int(order) if order is not None else None,
        author=str(meta.get("author", "")),
        language=str(meta.get("language", "ca")),
        summary=str(meta.get("summary") or "").strip(),
        excerpt=[str(x) for x in (meta.get("excerpt") or [])],
        description_html=render_paragraphs(meta.get("description")),
        tools=list(meta.get("tools") or []),
        tags=list(meta.get("tags") or []),
        poem_html=render_poem_body(poem_path.read_text(encoding="utf-8")),
        page_src=page_src,
    )


def discover_poems() -> list[Poem]:
    poems = []
    for folder in sorted(p for p in POEMS_DIR.iterdir() if p.is_dir()):
        poem = load_poem(folder)
        if poem is not None:
            poems.append(poem)
    # Explicit `order` (ascending) wins; poems without it fall back to newest-first
    # by ISO date. Two stable passes: date desc, then order (None sorts last).
    poems.sort(key=lambda p: p.date, reverse=True)
    poems.sort(key=lambda p: (p.order is None, p.order if p.order is not None else 0))
    return poems


def share_head(poem: Poem, poem_url: str, prev: Poem | None, nxt: Poem | None) -> str:
    """Return the link-preview tags and the prev/next/up links for a piece page."""
    title = html.escape(f"{poem.title} — {SITE_TITLE}", quote=True)
    desc = html.escape(poem.summary or SITE_INTRO, quote=True)
    image = f"{poem_url}og.png"
    links = '<link rel="up" href="../">\n'
    if prev:
        links += f'<link rel="prev" href="../{prev.slug}/">\n'
    if nxt:
        links += f'<link rel="next" href="../{nxt.slug}/">\n'
    return (
        f'<meta name="description" content="{desc}">\n'
        f'<link rel="canonical" href="{poem_url}">\n'
        '<link rel="icon" href="../favicon.svg" type="image/svg+xml">\n'
        '<meta name="theme-color" content="#fbfbf9">\n'
        f'<meta property="og:site_name" content="{SITE_TITLE}">\n'
        '<meta property="og:type" content="article">\n'
        '<meta property="og:locale" content="ca_ES">\n'
        f'<meta property="og:title" content="{title}">\n'
        f'<meta property="og:description" content="{desc}">\n'
        f'<meta property="og:url" content="{poem_url}">\n'
        f'<meta property="og:image" content="{image}">\n'
        '<meta property="og:image:width" content="1200">\n'
        '<meta property="og:image:height" content="630">\n'
        '<meta name="twitter:card" content="summary_large_image">\n'
        f'<meta name="twitter:title" content="{title}">\n'
        f'<meta name="twitter:description" content="{desc}">\n'
        f'<meta name="twitter:image" content="{image}">\n'
        + links
    )


# --------------------------------------------------------------------------- #
# Building
# --------------------------------------------------------------------------- #
def book_context() -> dict:
    """Facts about the printed book for the About page (from ``book/book.yml``)."""
    cfg = yaml.safe_load((BOOK_DIR / "book.yml").read_text(encoding="utf-8")) or {}
    size_file = BOOK_DIR / "cover-photo.json"
    size = json.loads(size_file.read_text(encoding="utf-8")) if size_file.exists() else {}
    return {
        "book_pages": cfg.get("pages"),
        "publisher_url": cfg.get("catalogue_url"),
        "cover_w": size.get("width"),
        "cover_h": size.get("height"),
    }



def write_crawler_files(out_dir: Path, poems: list[Poem], env: Environment, common: dict) -> None:
    """Write robots.txt, sitemap.xml, llms.txt and the 404 page."""
    (out_dir / "robots.txt").write_text(
        f"User-agent: *\nAllow: /\n\nSitemap: {SITE_URL}/sitemap.xml\n", encoding="utf-8"
    )
    urls = [f"{SITE_URL}/", f"{SITE_URL}/sobre/"] + [f"{SITE_URL}/{p.slug}/" for p in poems]
    entries = "\n".join(f"  <url><loc>{u}</loc></url>" for u in urls)
    (out_dir / "sitemap.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f"{entries}\n</urlset>\n",
        encoding="utf-8",
    )
    lines = [f"# {SITE_TITLE}", "", f"> {SITE_INTRO}", "", f"- [Sobre el llibre]({SITE_URL}/sobre/)", "", "## Peces", ""]
    lines += [f"- [{p.title}]({SITE_URL}/{p.slug}/): {p.summary}".rstrip(": ") for p in poems]
    lines += ["", "## Codi", "", f"- [Repositori a GitHub]({REPO_URL}): textos, dades i codi en Python de totes les peces", ""]
    (out_dir / "llms.txt").write_text("\n".join(lines), encoding="utf-8")
    (out_dir / "404.html").write_text(
        env.get_template("notfound.html").render(root=f"{SITE_URL}/", page_url=f"{SITE_URL}/", page_image=f"{SITE_URL}/og.png", **common),
        encoding="utf-8",
    )


def build(out_dir: Path) -> None:
    poems = discover_poems()

    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        autoescape=select_autoescape(["html"]),
        trim_blocks=True,
        lstrip_blocks=True,
    )

    if out_dir.exists():
        shutil.rmtree(out_dir)
    out_dir.mkdir(parents=True)

    # Static assets: the site's own CSS plus the shared design layer.
    if STATIC_DIR.exists():
        shutil.copytree(STATIC_DIR, out_dir / "static")
    for name in ("fonts.css", "tokens.css", "base.css"):
        shutil.copyfile(DESIGN_DIR / name, out_dir / "static" / name)
    if (BOOK_DIR / "cover-photo.webp").exists():
        shutil.copyfile(BOOK_DIR / "cover-photo.webp", out_dir / "static" / "cover.webp")

    # Social assets are generated by scripts/make_social.py and committed in social/.
    shutil.copytree(SOCIAL_DIR, out_dir / "social")
    for name in ("favicon.svg", "apple-touch-icon.png", "icon-192.png", "icon-512.png"):
        shutil.copyfile(SOCIAL_DIR / "brand" / name, out_dir / name)
    shutil.copyfile(SOCIAL_DIR / "og" / "index.png", out_dir / "og.png")
    (out_dir / "site.webmanifest").write_text(
        json.dumps(
            {
                "name": SITE_TITLE,
                "short_name": SITE_TITLE,
                "lang": "ca",
                "start_url": "./",
                "display": "standalone",
                "background_color": "#fbfbf9",
                "theme_color": "#fbfbf9",
                "icons": [
                    {"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
                    {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"},
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    common = {
        "site_title": SITE_TITLE,
        "site_author": SITE_AUTHOR,
        "site_intro": SITE_INTRO,
        "site_description": SITE_INTRO,
        "repo_url": REPO_URL,
        **book_context(),
    }
    index_tmpl = env.get_template("index.html")
    (out_dir / "index.html").write_text(
        index_tmpl.render(
            poems=poems,
            root="",
            page_title=SITE_TITLE,
            page_description=SITE_INTRO,
            page_url=f"{SITE_URL}/",
            page_image=f"{SITE_URL}/og.png",
            **common,
        ),
        encoding="utf-8",
    )

    about_dir = out_dir / "sobre"
    about_dir.mkdir()
    (about_dir / "index.html").write_text(
        env.get_template("sobre.html").render(
            root="../",
            page_title=f"Sobre el llibre — {SITE_TITLE}",
            page_description=SITE_INTRO,
            page_url=f"{SITE_URL}/sobre/",
            page_image=f"{SITE_URL}/og.png",
            **common,
        ),
        encoding="utf-8",
    )

    poem_tmpl = env.get_template("poem.html")
    next_tmpl = env.get_template("next.html")
    for i, poem in enumerate(poems):
        prev = poems[i - 1] if i > 0 else None
        nxt = poems[i + 1] if i + 1 < len(poems) else None
        poem_out = out_dir / poem.slug
        poem_out.mkdir(parents=True, exist_ok=True)
        card = SOCIAL_DIR / "og" / f"{poem.slug}.png"
        if not card.exists():
            print(f"warning: no share card for {poem.slug}; using the collection card "
                  "(run scripts/make_social.py)")
            card = SOCIAL_DIR / "og" / "index.png"
        shutil.copyfile(card, poem_out / "og.png")
        poem_url = f"{SITE_URL}/{poem.slug}/"
        if poem.page_src is not None:
            # Serve the piece's self-contained page, adding the link-preview tags, the
            # prev/next links and the "next piece" ending.
            page = poem.page_src.read_text(encoding="utf-8")
            if "<head>" not in page:
                raise SystemExit(f"{poem.page_src}: no <head> to add share tags to")
            page = page.replace("<head>", "<head>\n" + share_head(poem, poem_url, prev, nxt), 1)
            page = re.sub(r"<title>[^<]*</title>", f"<title>{html.escape(poem.title)} — {SITE_TITLE}</title>", page, count=1)
            ending = next_tmpl.render(nxt=nxt, root_up="../")
            page, n = re.subn(r"(</main>\s*)(</div>)", lambda m: m.group(1) + ending + m.group(2), page, count=1)
            if n != 1:
                raise SystemExit(f"{poem.page_src}: expected '</main></div>' to place the next-piece ending")
            (poem_out / "index.html").write_text(page, encoding="utf-8")
        else:
            (poem_out / "index.html").write_text(
                poem_tmpl.render(
                    poem=poem,
                    nxt=nxt,
                    root="../",
                    root_up="../",
                    page_title=f"{poem.title} — {SITE_TITLE}",
                    page_description=poem.summary or SITE_INTRO,
                    page_url=poem_url,
                    page_image=f"{poem_url}og.png",
                    **common,
                ),
                encoding="utf-8",
            )

    write_crawler_files(out_dir, poems, env, common)
    print(f"Built {len(poems)} poem(s) into {out_dir}/")


def main() -> None:
    parser = argparse.ArgumentParser(description="Build the La causa científica website.")
    parser.add_argument("--out", type=Path, default=REPO_ROOT / "_site", help="output directory")
    args = parser.parse_args()
    build(args.out)


if __name__ == "__main__":
    main()
