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
from inline import add_book_section, design_css, nav_script, site_header  # noqa: E402
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
      <div class="orig">
        <button type="button" class="otoggle" aria-expanded="false" aria-controls="o-{pid}">Original</button>
        <div class="obody" id="o-{pid}" inert><div class="oin"><div class="verse original">{original}</div></div></div>
      </div>
    </article>"""


def _method_entry() -> str:
    seq = chain()
    maps = "".join(
        f'<li class="map">{html.escape(NAMES[c])}</li>' for c in seq)
    return f"""
      <div class="prose">
        <p>Cada poema d'amor de Neruda ha travessat 104 traduccions
        automàtiques encadenades amb el traductor de Google: del castellà a
        l'estonià, de l'estonià al basc… tota la volta de l'abecedari de llengües
        i, finalment, de tornada al castellà. A cada salt el poema perd una mica
        més; el que en torna és el residu «despoetitzat», el sediment de sentit
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
            .replace("{{HEADER}}", site_header())
            .replace("{{POEMS}}", poems)
            .replace("{{METHOD}}", _method_entry())
            .replace("{{CHAIN}}", chain_json)
            .replace("{{NAV}}", nav_script()))
    out = POEM_ROOT / "index.html"
    page = add_book_section(page, POEM_ROOT.name)
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
  .epigraph{ margin:0 0 clamp(24px,3.5vw,40px); max-width:var(--measure-prose); }
  /* the poems are short: they fill the width in columns, each under its own hairline */
  .poems{ display:grid; grid-template-columns:repeat(auto-fill,minmax(min(100%,22rem),1fr)); gap:0 clamp(32px,4vw,64px); align-items:start; }
  .entry{ padding:clamp(18px,2.4vw,28px) 0 clamp(24px,3vw,36px); border-top:1px solid var(--rule); }
  .etitle{ margin:0 0 clamp(16px,2.4vw,24px); font-weight:400; font-size:clamp(1.5rem,3vw,2rem); line-height:1.15; letter-spacing:-.01em; text-wrap:balance; }
  .orig{ margin-top:clamp(14px,2vw,22px); }
  .otoggle{ cursor:pointer; background:none; border:0; padding:0; color:inherit; font:400 .875rem/1.4 var(--sans); border-bottom:1px solid transparent; transition:color .25s ease; }
  .otoggle::after{ content:" +"; }
  .otoggle[aria-expanded=true]::after{ content:" –"; }
  .otoggle:hover{ color:var(--accent); }
  @media (pointer:coarse){ .otoggle{ padding:13px 0; } }
  .obody{ display:grid; grid-template-rows:0fr; transition:grid-template-rows .45s cubic-bezier(.3,.7,.2,1); }
  .orig.open>.obody{ grid-template-rows:1fr; }
  .oin{ min-height:0; overflow:hidden; opacity:0; transition:opacity .35s ease; }
  .orig.open .oin{ opacity:1; transition-delay:.1s; }
  @media (prefers-reduced-motion:reduce){ .obody,.oin{ transition:none; } }
  .orig .original{ margin-top:16px; }
  .chaincount{ display:inline-block; vertical-align:bottom; max-width:calc(100% - 6rem); white-space:nowrap; overflow:hidden; text-overflow:ellipsis; font:400 .875rem/1.4 var(--sans); margin-left:12px; font-variant-numeric:tabular-nums; color:var(--accent); }
  .how>.label{ position:sticky; top:0; z-index:1; margin:0; padding:.5rem 0; background:var(--paper); }
  .maps{ list-style:none; margin:.5rem 0 0; padding:0; display:grid; grid-template-columns:repeat(auto-fill,minmax(7.5rem,1fr)); gap:.25rem 1rem; max-width:60rem; }
  .map{ font-size:1rem; line-height:1.4; white-space:nowrap; transition:color .14s ease; }
  .map.done{ text-decoration:underline; text-decoration-thickness:1px; text-underline-offset:.22em; }   /* crossed: underlined, never paler */
  @media (prefers-reduced-motion:reduce){ .map{ transition:none; } }
  .map.now{ color:var(--accent); }
  section[hidden]{ display:none; }
</style>
</head>
<body>
{{HEADER}}
<div class="page">
  <header class="head">
    <h1 class="title">El que es perd en la traducció</h1>
    <p class="sub"><i>Veinte poemas de amor y una canción desesperada</i>, de Pablo Neruda, despoetitzat amb 104 traduccions automàtiques</p>
    <p class="cue">Cada poema, després de 104 traduccions. Prem «Original» sota cada poema per veure la versió de Neruda.</p>
  </header>
  <nav><ul class="subnav">
    <li><a class="on" href="#poemes">Els poemes</a></li>
    <li><a href="#meto">Metodologia</a></li>
  </ul></nav>
<main>

  <section id="poemes" style="margin-top:clamp(32px,5vw,56px)">
    <p class="epigraph">«Poetry is what gets lost in translation.» <span style="white-space:nowrap">— Robert Frost</span></p>
    <div class="poems">{{POEMS}}</div>
  </section>
  <section id="meto" class="sec"><h2 class="label">Metodologia</h2>
    {{METHOD}}
  </section>
</main>
</div>
<script>
  var CHAIN = {{CHAIN}};           // [[code, name], ...] es ... es
  [].forEach.call(document.querySelectorAll('.orig'), function(o){
    var b = o.querySelector('.otoggle'), body = o.querySelector('.obody');
    b.addEventListener('click', function(){
      var on = o.classList.toggle('open');
      b.setAttribute('aria-expanded', on); body.inert = !on;
    });
  });
  (function(){
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

    // The method animates while it is on screen.
    var meto = document.getElementById('meto');
    if('IntersectionObserver' in window && meto){
      new IntersectionObserver(function(es){
        es.forEach(function(e){ if(e.isIntersecting) gridStart(); else gridStop(); });
      }, {threshold: .25}).observe(meto);
    } else { gridStart(); }
  })();
</script>
{{NAV}}
</body>
</html>
"""


if __name__ == "__main__":
    print(build())
