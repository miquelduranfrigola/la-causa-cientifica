"""Assemble the self-contained "El que es perd en la traducció" page (HTML).

Editorial look (DESIGN.md): shared tokens and base styles inlined from
shared/design/, serif text on near-white paper, ink plus one blue accent, no rail.
Title block first, then a text menu with two views the reader switches between
("Els poemes" and "Metodologia").

Each poem is its title, the despoetized residue set in serif (this is what is
read) and a fold-away toggle for Neruda's original. The concept is illustrated once,
in "Metodologia": the 104-language chain animates a sweep (es -> et -> eu -> ... ->
es), the language being crossed in the accent, those already crossed in ink at a
lighter weight, looping while the view is on screen.

Reads: data/_meta.json, data/originals/*.txt, data/despoetized/*.txt, the language
chain from code/languages.py and the shared design. Writes index.html
(poem-folder root).
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

POEM_ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
REPO = POEM_ROOT.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(REPO / "shared" / "design"))
from inline import design_css, nav_script, standalone_bar  # noqa: E402
from languages import NAMES, chain  # noqa: E402

DATA = POEM_ROOT / "data"


def _verses_html(text: str) -> str:
    """Render a poem body: one span per verse, blank lines become stanza breaks."""
    out = []
    for line in text.replace("\r\n", "\n").split("\n"):
        if line.strip() == "":
            if out and not out[-1].startswith('<span class="br"'):
                out.append('<span class="br"></span>')
            continue
        out.append(f'<span class="v">{html.escape(line.rstrip())}</span>')
    while out and out[-1].startswith('<span class="br"'):
        out.pop()
    return "\n".join(out)


def _read(kind: str, pid: str) -> str:
    return (DATA / kind / f"{pid}.txt").read_text(encoding="utf-8")


def _entry(m: dict) -> str:
    pid, title = m["id"], m["title"]
    original = _verses_html(_read("originals", pid))
    despo = _verses_html(_read("despoetized", pid))
    return f"""
    <article class="entry" id="p-{pid}">
      <h2 class="etitle">{html.escape(title)}</h2>
      <div class="verse despo">{despo}</div>
      <details class="orig">
        <summary>Original</summary>
        <div class="verse original">{original}</div>
      </details>
    </article>"""


def _method_entry() -> str:
    seq = chain()
    maps = "".join(
        f'<li class="map"><i>{html.escape(NAMES[c])}</i></li>' for c in seq)
    return f"""
      <div class="prose">
        <p>Cada poema d'amor de Neruda ha travessat 104 traduccions
        automàtiques encadenades amb el traductor de Google: del castellà a
        l'estonià, de l'estonià al basc… tota la volta de l'abecedari de llengües
        i, finalment, de tornada al castellà. A cada salt el poema perd una mica
        més; el que en torna és el residu <i>despoetitzat</i> —el sediment de sentit
        que sobreviu al viatge.</p>
        <p>Es mostra el resultat sense cap modificació, més enllà de
        petites correccions gramaticals. Els resultats són els de la tirada
        original de 2016; una nova tirada donaria un residu diferent, perquè el
        traductor no para de canviar.</p>
      </div>
      <div class="how">
        <p class="label">La cadena <span class="chaincount">original → despoetitzat</span></p>
        <ol class="maps">{maps}</ol>
      </div>"""


def build() -> Path:
    meta = json.loads((DATA / "_meta.json").read_text(encoding="utf-8"))
    poems = "".join(_entry(m) for m in meta)
    chain_json = json.dumps([[c, NAMES[c]] for c in chain()], ensure_ascii=False)
    page = (_TEMPLATE
            .replace("{{DESIGN}}", design_css())
            .replace("{{STANDALONE}}", standalone_bar())
            .replace("{{POEMS}}", poems)
            .replace("{{METHOD}}", _method_entry())
            .replace("{{CHAIN}}", chain_json)
            .replace("{{NAV}}", nav_script()))
    out = POEM_ROOT / "index.html"
    out.write_text(page, encoding="utf-8")
    return out


_TEMPLATE = r"""<!doctype html>
<html lang="ca">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>El que es perd en la traducció</title>
<style>
{{DESIGN}}
  .epigraph{ margin:0 0 clamp(40px,6vw,72px); font-style:italic; max-width:var(--measure-prose); }
  .entry{ padding:clamp(32px,5vw,56px) 0; border-top:1px solid var(--rule); }
  .entry:first-of-type{ border-top:0; padding-top:0; }
  .etitle{ margin:0 0 clamp(16px,2.4vw,24px); font-weight:400; font-size:clamp(1.5rem,3vw,2rem); line-height:1.15; letter-spacing:-.01em; text-wrap:balance; }
  .orig{ margin-top:clamp(20px,3vw,32px); }
  .orig>summary{ cursor:pointer; list-style:none; font:400 .875rem/1.4 var(--sans); display:inline-block; border-bottom:1px solid transparent; }
  .orig>summary::-webkit-details-marker{ display:none; }
  .orig>summary::after{ content:" +"; }
  .orig[open]>summary::after{ content:" –"; }
  .orig>summary:hover{ color:var(--accent); }
  @media (pointer:coarse){ .orig>summary{ padding:13px 0; } }
  .orig .original{ margin-top:16px; font-style:italic; }
  .chaincount{ font:400 .875rem/1.4 var(--sans); margin-left:12px; font-variant-numeric:tabular-nums; color:var(--accent); }
  .maps{ list-style:none; margin:16px 0 0; padding:0; display:grid; grid-template-columns:repeat(auto-fill,minmax(150px,1fr)); gap:4px 24px; max-width:60rem; }
  .map{ font-size:1rem; line-height:1.4; white-space:nowrap; transition:color .14s ease; }
  .map.done{ opacity:.35; }
  .map.now{ color:var(--accent); }
  section[hidden]{ display:none; }
</style>
</head>
<body>
{{STANDALONE}}
<div class="page">
  <header class="head">
    <h1 class="title">El que es perd en la traducció</h1>
    <p class="by">Miquel Duran-Frigola</p>
    <p class="sub"><i>Veinte poemas de amor y una canción desesperada</i>, de Pablo Neruda, despoetitzat amb 104 traduccions automàtiques</p>
  </header>
  <nav><ul class="subnav">
    <li><a data-sec="poemes" class="on" href="#poemes">Els poemes</a></li>
    <li><a data-sec="meto" href="#meto">Metodologia</a></li>
  </ul></nav>

  <section id="poemes" style="margin-top:clamp(32px,5vw,56px)">
    <p class="epigraph">«Poetry is what gets lost in translation.» — Robert Frost</p>
    {{POEMS}}
  </section>
  <section id="meto" hidden style="margin-top:clamp(24px,4vw,40px)">
    {{METHOD}}
  </section>
</div>
<script>
  var CHAIN = {{CHAIN}};           // [[code, name], ...] es ... es
  (function(){
    var links = [].slice.call(document.querySelectorAll('[data-sec]'));
    var secs = [].slice.call(document.querySelectorAll('section[id]'));
    var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

    // Sweep a highlight through the 104-language chain, looping while on screen.
    var chips = [].slice.call(document.querySelectorAll('#meto .map'));
    var count = document.querySelector('#meto .chaincount');
    var steps = chips.length - 1;
    var timer = null, running = false;

    function gridReset(){
      chips.forEach(function(c){ c.className = 'map'; });
      if(count) count.textContent = 'original → despoetitzat';
    }
    function gridStep(i){
      if(!running) return;
      if(i > steps){
        if(count) count.textContent = 'original → despoetitzat';
        timer = setTimeout(gridCycle, 3200);
        return;
      }
      chips.forEach(function(c, k){
        c.className = 'map' + (k < i ? ' done' : (k === i ? ' now' : ''));
      });
      if(count) count.textContent = CHAIN[i][1] + ' · ' + i + ' / ' + steps;
      timer = setTimeout(function(){ gridStep(i + 1); }, 58);
    }
    function gridCycle(){ gridReset(); timer = setTimeout(function(){ gridStep(0); }, 600); }
    function gridStart(){ if(running || reduce || !chips.length) return; running = true; gridCycle(); }
    function gridStop(){ running = false; clearTimeout(timer); gridReset(); }

    function show(id){
      if(!document.getElementById(id)) id = 'poemes';
      secs.forEach(function(s){ s.hidden = s.id !== id; });
      links.forEach(function(a){ a.classList.toggle('on', a.dataset.sec === id); });
      if(id === 'meto') gridStart(); else gridStop();
    }
    links.forEach(function(a){
      a.addEventListener('click', function(e){ e.preventDefault(); show(a.dataset.sec); window.scrollTo(0,0); });
    });
    show('poemes');
  })();
</script>
{{NAV}}
</body>
</html>
"""


if __name__ == "__main__":
    print(build())
