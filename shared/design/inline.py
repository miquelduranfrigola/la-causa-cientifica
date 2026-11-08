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
    """Return the ``<script>`` that wires keyboard navigation with the shell."""
    return (HERE / "nav.html").read_text(encoding="utf-8")


def standalone_bar() -> str:
    """Return the small bar shown only when a page is opened outside the shell."""
    return (
        '<div class="standalone"><a href="../index.html">← La causa científica</a></div>'
        "<script>try{if(window.top===window)document.documentElement.classList.add('is-top')}"
        "catch(e){document.documentElement.classList.add('is-top')}</script>"
    )


def add_book_tab(page: str, slug: str, *, section_class: str = "") -> str:
    """Add the "Al llibre" view (facsimile of the printed page) to a finished page.

    Reads ``book/pages/<slug>.json`` (written by ``scripts/make_book_pages.py``).
    Without it the page is returned unchanged, so a piece shows the tab only once
    its book page exists. The tab joins the piece's ``.subnav`` as its last link
    and a ``section#llibre`` before ``</main>``; the piece's own view switcher
    (``[data-sec]`` links, ``section[id]``) then handles it like any other view.
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
            f'<figcaption><span class="label">Al llibre</span>'
            f'<span class="ref">La causa científica, p.&nbsp;{it["page"]}</span>{quote}</figcaption></figure>'
        )
    classes = f"view book {section_class}".strip()
    section = f'<section id="llibre" class="{classes}" hidden><div class="leaves">{"".join(figures)}</div></section>\n'
    link = '<li><a data-sec="llibre" href="#llibre">Al llibre</a></li>\n  '
    if "</ul></nav>" not in page or "</main>" not in page:
        raise ValueError("page has no .subnav or <main> to attach the book view to")
    page = page.replace("</ul></nav>", link + "</ul></nav>", 1)
    return page.replace("</main>", section + "</main>", 1)
