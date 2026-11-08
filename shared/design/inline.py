"""Inline the shared design (fonts, tokens, base styles, nav script) into a page.

Every poem's ``code/build_web.py`` calls these helpers so that no page copies the
design CSS. Pages stay self-contained: everything is inlined, no external requests.

Example
-------
>>> import sys; sys.path.insert(0, "<repo>/shared/design")
>>> from inline import design_css, nav_script
"""

from __future__ import annotations

from pathlib import Path

HERE = Path(__file__).resolve().parent


def design_css() -> str:
    """Return fonts + tokens + base CSS, ready to place inside a ``<style>`` tag."""
    parts = [
        (HERE / name).read_text(encoding="utf-8")
        for name in ("fonts.css", "tokens.css", "base.css")
    ]
    return "\n".join(parts)


def nav_script() -> str:
    """Return the ``<script>`` with the keyboard shortcuts and the sticky-index behaviour."""
    return (HERE / "nav.html").read_text(encoding="utf-8")


def site_header() -> str:
    """Return the masthead shared by every piece (links are relative to ``/<slug>/``)."""
    return (
        "<script>try{if(window.top!==window)document.documentElement.classList.add('is-embedded')}"
        "catch(e){document.documentElement.classList.add('is-embedded')}</script>"
        '<header class="mast"><a class="word" href="../"><em>La causa científica</em></a>'
        '<nav aria-label="Principal"><a href="../">Peces</a><a href="../#llibre">El llibre</a></nav></header>'
    )


def add_book_section(page: str, slug: str) -> str:
    """Add the "Al llibre" section (facsimile of the printed page) to a finished page.

    Reads ``book/pages/<slug>.json`` (written by ``scripts/make_book_pages.py``).
    Without it the page is returned unchanged, so a piece shows the section only once
    its book page exists. The section joins the page as its last block, with a link to it as
    the last entry of the piece's sticky ``.subnav``.
    """
    import base64
    import html
    import json

    manifest = HERE.parent.parent / "book" / "pages" / f"{slug}.json"
    if not manifest.exists():
        return page
    items = json.loads(manifest.read_text(encoding="utf-8"))
    if not items:
        return page
    figures = []
    for it in items:
        data = base64.b64encode((manifest.parent / it["image"]).read_bytes()).decode()
        alt = f"Pàgina {it['page']} del llibre, amb les frases marcades en groc: " + " ".join(it["marked"])
        quote = "".join(f"<p>«{html.escape(s)}»</p>" for s in it["marked"])
        figures.append(
            f'<figure class="leaf"><img src="data:image/webp;base64,{data}" width="{it["width"]}" '
            f'height="{it["height"]}" alt="{html.escape(alt)}" loading="lazy">'
            f'<figcaption><span class="ref"><em>La causa científica</em>, p.&nbsp;{it["page"]}</span>{quote}</figcaption></figure>'
        )
    section = (
        f'<section id="llibre" class="sec book"><h2 class="label">Al llibre <span class="pg">p.&nbsp;{items[0]["page"]}</span></h2>'
        f'<div class="leaves">{"".join(figures)}</div></section>\n'
    )
    link = '<li><a href="#llibre">Al llibre</a></li>\n  '
    if "</ul></nav>" not in page or "</main>" not in page:
        raise ValueError("page has no .subnav or <main> to attach the book view to")
    page = page.replace("</ul></nav>", link + "</ul></nav>", 1)
    return page.replace("</main>", section + "</main>", 1)
