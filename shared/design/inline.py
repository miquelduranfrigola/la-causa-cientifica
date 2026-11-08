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
