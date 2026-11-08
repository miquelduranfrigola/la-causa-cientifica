#!/usr/bin/env python3
"""Check the site against the rules in DESIGN.md. Exits 1 if any rule is broken.

Checks the committed piece pages (``content/*/index.html``), the shell templates
and styles, and every ``metadata.yml``. It looks only at CSS inside ``<style>``
blocks and at page structure, so minified libraries inlined in a page do not
trigger false alarms.

Usage
-----
    python scripts/check_design.py
"""

from __future__ import annotations

import re
import sys
from pathlib import Path

import yaml

REPO = Path(__file__).resolve().parent.parent
FORBIDDEN = ("#f0ebe6", "#c7513b", "#2f7d68", "space mono", "spacemono")

STYLE_RE = re.compile(r"<style[^>]*>(.*?)</style>", re.DOTALL | re.IGNORECASE)
EXTERNAL_RE = re.compile(
    r"""(?:<link[^>]+href=|<script[^>]+src=|<img[^>]+src=|@import\s+|url\()\s*["']?https?://""",
    re.IGNORECASE,
)

errors: list[str] = []


def fail(where: str, message: str) -> None:
    """Record one broken rule."""
    errors.append(f"{where}: {message}")


def css_blocks(text: str) -> str:
    """Return the CSS of all ``<style>`` blocks, without base64 font payloads."""
    css = "\n".join(STYLE_RE.findall(text))
    css = re.sub(r"url\(data:[^)]*\)", "url(data:)", css)
    css = re.sub(r"@font-face\s*\{[^}]*\}", "", css)
    # The shared base legitimately styles the semantic tags <em>, <i> and <cite>.
    return re.sub(r"\bem\s*,\s*i\s*,\s*cite\s*\{[^}]*\}", "", css)


def check_css(where: str, css: str, *, allow_italic_rule: bool = False) -> None:
    """Apply the visual rules to a piece of CSS."""
    low = css.lower()
    for bad in FORBIDDEN:
        if bad in low:
            fail(where, f"forbidden value {bad!r}")
    for m in re.finditer(r"border-radius\s*:\s*([^;}]+)", low):
        value = m.group(1).strip()
        if value not in ("0", "0px", "inherit"):
            fail(where, f"rounded corners ({value})")
    for prop in ("box-shadow", "text-shadow", "linear-gradient", "radial-gradient", "backdrop-filter"):
        if prop in low:
            fail(where, f"{prop} is not allowed")
    if re.search(r"text-transform\s*:\s*uppercase", low):
        fail(where, "uppercase labels are not allowed")
    if not allow_italic_rule and re.search(r"font-style\s*:\s*italic", low):
        fail(where, "italic is only allowed through <em>, <i> or <cite>, not as a style")


def check_page(path: Path) -> None:
    """Check one self-contained piece page."""
    where = str(path.relative_to(REPO))
    text = path.read_text(encoding="utf-8")
    check_css(where, css_blocks(text))
    if EXTERNAL_RE.search(text):
        fail(where, "external request (pages must be self-contained)")
    if not re.search(r"<html[^>]+lang=\"ca\"", text):
        fail(where, 'missing <html lang="ca">')
    if not re.search(r"<title>[^<]+</title>", text):
        fail(where, "missing <title>")
    if len(re.findall(r"<h1[\s>]", text)) != 1:
        fail(where, "needs exactly one <h1>")
    if not re.search(r"<main[\s>]", text):
        fail(where, "missing <main> landmark")
    if "<meta name=\"viewport\"" not in text:
        fail(where, "missing viewport meta")


def check_metadata(folder: Path) -> None:
    """Check one poem's metadata and its share image."""
    where = f"content/{folder.name}/metadata.yml"
    meta = yaml.safe_load((folder / "metadata.yml").read_text(encoding="utf-8")) or {}
    for key in ("title", "slug", "date", "summary"):
        if not meta.get(key):
            fail(where, f"missing '{key}'")
    if meta.get("slug") != folder.name:
        fail(where, "slug does not match the folder name")
    if not (REPO / "social" / "og" / f"{folder.name}.png").exists():
        fail(where, "missing social/og card (run scripts/make_social.py)")
    if len(str(meta.get("summary", ""))) > 90:
        fail(where, "summary should fit on one line (90 characters or fewer)")


def main() -> int:
    """Run all checks and print a short report."""
    folders = sorted(p for p in (REPO / "content").iterdir() if (p / "metadata.yml").exists())
    for folder in folders:
        check_metadata(folder)
        page = folder / "index.html"
        if page.exists():
            check_page(page)
        build = folder / "code" / "build_web.py"
        if build.exists():
            text = build.read_text(encoding="utf-8")
            tmpl = re.search(r'_TEMPLATE\s*=\s*r?"""(.*?)"""', text, re.DOTALL)
            if tmpl:
                check_css(f"content/{folder.name}/code/build_web.py", css_blocks(tmpl.group(1)))

    for css in ("shared/design/tokens.css", "shared/design/base.css", "site/static/style.css"):
        check_css(css, re.sub(r"\bem\s*,\s*i\s*,\s*cite\s*\{[^}]*\}", "", (REPO / css).read_text(encoding="utf-8")))
    for tmpl in (REPO / "site" / "templates").glob("*.html"):
        check_css(f"site/templates/{tmpl.name}", css_blocks(tmpl.read_text(encoding="utf-8")))

    if errors:
        print(f"{len(errors)} design problem(s):")
        for line in errors:
            print(f"  - {line}")
        return 1
    print(f"Design check passed ({len(folders)} pieces).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
