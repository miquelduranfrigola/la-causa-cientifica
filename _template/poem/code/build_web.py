"""Build this poem's self-contained web page -> index.html (poem-folder root).

A starting point in the shared editorial design (see DESIGN.md): a title block, a
text menu with two views ("El poema" and "Metodologia") and the poem set as verse.
The shared CSS, fonts and keyboard script are inlined from shared/design/, so the
page needs no external requests. Replace the content as the piece needs; add the
piece's own figures and interactions to the page CSS below, never design rules.

Usage
-----
    pip install pyyaml
    python code/build_web.py
Then uncomment ``page: index.html`` in metadata.yml.
"""

from __future__ import annotations

import html
import re
import sys
from pathlib import Path

import yaml

POEM_ROOT = Path(__file__).resolve().parent.parent
REPO = POEM_ROOT.parent.parent
sys.path.insert(0, str(REPO / "shared" / "design"))
from inline import add_book_tab, design_css, nav_script, standalone_bar  # noqa: E402

_TEMPLATE = r"""<!doctype html>
<html lang="ca">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{{TITLE}}</title>
<style>
{{DESIGN}}
  section[hidden]{ display:none; }
  .view{ padding-top:clamp(24px,4vw,40px); }
</style>
</head>
<body>
{{STANDALONE}}
<div class="page">
  <header class="head">
    <h1 class="title">{{TITLE}}</h1>
    <p class="sub">{{SUMMARY}}</p>
  </header>
  <nav><ul class="subnav">
    <li><a data-sec="poem" class="on" href="#poem">El poema</a></li>
    <li><a data-sec="method" href="#method">Metodologia</a></li>
  </ul></nav>
<main>
  <section id="poem" class="view"><div class="verse">{{VERSE}}</div></section>
  <section id="method" class="view" hidden><div class="prose">{{METHOD}}</div></section>
</main>
</div>
<script>
(function(){
  var links=[].slice.call(document.querySelectorAll('[data-sec]'));
  var secs=[].slice.call(document.querySelectorAll('section[id]'));
  function show(id){
    secs.forEach(function(s){ s.hidden = s.id!==id; });
    links.forEach(function(a){ a.classList.toggle('on', a.dataset.sec===id); });
  }
  links.forEach(function(a){ a.addEventListener('click', function(e){
    e.preventDefault(); show(a.dataset.sec); window.scrollTo(0,0); }); });
  show('poem');
})();
</script>
{{NAV}}
</body>
</html>
"""


def verses(markdown: str) -> str:
    """Render poem.md as verse: one block per line, a gap between stanzas."""
    body = re.sub(r"<!--.*?-->", "", markdown, flags=re.DOTALL)
    body = re.sub(r"^\s*#\s+.*$", "", body, count=1, flags=re.MULTILINE)
    out = []
    for line in body.strip().splitlines():
        out.append(f'<span class="v">{html.escape(line)}</span>' if line.strip() else '<span class="br"></span>')
    return "\n".join(out)


def prose(text: str | None) -> str:
    """Render a YAML description as paragraphs (a blank line starts a new one)."""
    chunks = [" ".join(c.split()) for c in (text or "").split("\n\n") if c.strip()]
    return "\n".join(f"<p>{html.escape(c)}</p>" for c in chunks)


def build() -> Path:
    """Write index.html next to metadata.yml and return its path."""
    meta = yaml.safe_load((POEM_ROOT / "metadata.yml").read_text(encoding="utf-8"))
    poem = (POEM_ROOT / "poem.md").read_text(encoding="utf-8")
    page = (
        _TEMPLATE.replace("{{DESIGN}}", design_css())
        .replace("{{STANDALONE}}", standalone_bar())
        .replace("{{NAV}}", nav_script())
        .replace("{{TITLE}}", html.escape(meta["title"]))
        .replace("{{SUMMARY}}", html.escape(meta.get("summary", "")))
        .replace("{{VERSE}}", verses(poem))
        .replace("{{METHOD}}", prose(meta.get("description")))
    )
    out = POEM_ROOT / "index.html"
    page = add_book_tab(page, POEM_ROOT.name)
    out.write_text(page, encoding="utf-8")
    return out


if __name__ == "__main__":
    print(build())
