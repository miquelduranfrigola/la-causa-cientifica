"""Assemble the self-contained "Poema malalt" page (HTML).

Editorial look (DESIGN.md; shared/design/ inlined, no external requests): serif title
block, an italic descriptor, a text menu ("El poema" / "Metodologia"). The piece is a
poem that *evolves*: starting from a seed poem, one word (a gene) mutates per step by a
single-letter edit; the mutated word is set in the page's one blue as the poem drifts,
looping. Auto-playing, not interactive (no controls); with reduced motion the final
state is shown.

Reads data/evolution.json (the ordered mutation log). Writes index.html (poem-folder
root).
"""

from __future__ import annotations

import html
import json
import sys
from pathlib import Path

POEM_ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
REPO = POEM_ROOT.parent.parent
sys.path.insert(0, str(REPO / "shared" / "design"))
from inline import design_css, nav_script, standalone_bar  # noqa: E402

POS_CA = {"N": "nom", "V": "verb", "A": "adjectiu", "R": "adverbi"}
EDIT_CA = {"substitution": "substitució", "deletion": "deleció", "insertion": "inserció"}


def _highlight(prev_line: str, new_line: str) -> str:
    """new_line as HTML with the changed token(s) wrapped in <span class=mut>."""
    p, n = prev_line.split(" "), new_line.split(" ")
    i = 0
    while i < len(p) and i < len(n) and p[i] == n[i]:
        i += 1
    j = 0
    while j < (len(p) - i) and j < (len(n) - i) and p[-1 - j] == n[-1 - j]:
        j += 1
    pre, mid, suf = n[:i], (n[i: len(n) - j] if j else n[i:]), (n[len(n) - j:] if j else [])
    out = []
    if pre:
        out.append(html.escape(" ".join(pre)))
    out.append('<span class="mut">' + html.escape(" ".join(mid)) + "</span>")
    if suf:
        out.append(html.escape(" ".join(suf)))
    return " ".join(out)


def _payload():
    data = json.loads((POEM_ROOT / "data" / "evolution.json").read_text(encoding="utf-8"))
    cur = list(data["original"])
    steps = []
    for st in data["steps"]:
        li = st["line"]
        hi = _highlight(cur[li], st["line_after"])
        cur[li] = st["line_after"]
        steps.append({
            "n": st["n"], "line": li, "before": st["before"], "after": st["after"],
            "pos": POS_CA.get(st["pos"], st["pos"]), "edit": EDIT_CA.get(st["edit"], st["edit"]),
            "plain": html.escape(st["line_after"]), "hi": hi,
        })
    return {
        "title": data.get("title", "Evolució"),
        "source": data.get("source", {}),
        "conserved": data.get("conserved", {}),
        "initLines": [html.escape(l) for l in data["original"]],
        "steps": steps,
    }


def build() -> Path:
    payload = _payload()
    src = payload["source"]
    # The data note is in English; the page is Catalan, so build the sentence from the words.
    words = payload.get("conserved", {}).get("words", [])
    conserved_note = ""
    if len(words) == 2:
        conserved_note = (f"El vers «Res no és mesquí» no pot mutar: «{words[0]}» no té cap adjectiu "
                          f"vàlid a una sola edició de distància, i «{words[1]}» tampoc no en té. "
                          "És un gen conservat que emergeix per si sol.")

    page = (_TEMPLATE
            .replace("{{DESIGN}}", design_css())
            .replace("{{STANDALONE}}", standalone_bar())
            .replace("{{NAV}}", nav_script())
            .replace("{{AUTHOR}}", html.escape(src.get("author", "")))
            .replace("{{SEED}}", html.escape(src.get("poem", "")))
            .replace("{{CONSERVED}}", html.escape(conserved_note))
            .replace("{{DATA}}", json.dumps(payload, ensure_ascii=False))
            .replace("{{POS}}", json.dumps(POS_CA, ensure_ascii=False))
            .replace("{{EDIT}}", json.dumps(EDIT_CA, ensure_ascii=False)))
    out = POEM_ROOT / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out


_TEMPLATE = r"""<!doctype html>
<html lang="ca">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Poema malalt</title>
<style>
{{DESIGN}}
  .page > section{ margin-top:clamp(24px,4vw,40px); }
  .dims{ margin:0 0 clamp(20px,3vw,32px); font:400 .875rem/1.4 var(--sans); min-height:1.4em; }
  .dims .arrow{ color:var(--accent); }
  .verse .v:empty{ height:1.6em; }
  .verse .v{ overflow-wrap:anywhere; }
  @media (max-width:40rem){ .dims{ min-height:2.8em; } }
  @media (max-width:22rem){ .dims{ min-height:4.2em; } }
  @media (prefers-reduced-motion:reduce){ .dims{ min-height:0; } }
  .mut{ color:var(--accent); }
</style>
</head>
<body>
{{STANDALONE}}
<div class="page">
  <header class="head">
    <h1 class="title">Poema malalt</h1>
    <p class="by">Miquel Duran-Frigola</p>
    <p class="sub">L’evolució d’un poema de {{AUTHOR}}, <span style="font-style:normal">«{{SEED}}»</span>, a força de mutacions</p>
  </header>
  <nav><ul class="subnav">
    <li><a data-sec="poem" class="on" href="#poem">El poema</a></li>
    <li><a data-sec="metode" href="#metode">Metodologia</a></li>
  </ul></nav>
<main>

  <section id="poem">
    <p class="dims" id="dims" aria-live="off"></p>
    <div class="verse" id="poemtext"></div>
  </section>
  <section id="metode" hidden>
    <div class="prose">
      <p>El poema és un genoma i cada paraula, un gen. A cada pas, una
        paraula muta per una sola lletra —substitució, inserció o deleció—, tal com
        les mutacions somàtiques del càncer. La mutació només sobreviu si (1) dona una
        paraula catalana real, (2) manté la categoria gramatical i la concordança, i
        (3) el poema encara té sentit. Cada mot mutat s’encén en <span class="mut">blau</span>.</p>
      <p>{{CONSERVED}}</p>
    </div>
  </section>
</main>
</div>

<script>
  var DATA = {{DATA}};
  (function(){
    var links = [].slice.call(document.querySelectorAll('[data-sec]'));
    var entries = [].slice.call(document.querySelectorAll('section[id]'));
    var N = DATA.steps.length, timer = null, s = 0;
    var reduce = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;
    // Adaptive pace: whole loop ~90s regardless of how many mutations there are.
    var base = Math.max(28, Math.min(240, Math.round(90000 / N)));

    function linesAt(k){
      var lines = DATA.initLines.slice();
      for(var i=0;i<k;i++){ var st=DATA.steps[i]; lines[st.line]=st.plain; }
      return lines;
    }
    // Reserve each verse's tallest variant so mutating words never shift the layout.
    function fit(){
      var box = document.getElementById('poemtext');
      if(!box.offsetParent) return;
      var sets = DATA.initLines.map(function(t){ return [t]; });
      DATA.steps.forEach(function(st){ if(sets[st.line].indexOf(st.plain)<0) sets[st.line].push(st.plain); });
      box.style.minHeight = '';
      var probe = document.createElement('div');
      probe.className = 'verse'; probe.setAttribute('aria-hidden','true');
      probe.style.cssText = 'visibility:hidden;height:0;overflow:hidden';
      box.parentNode.insertBefore(probe, box);
      var total = 0;
      sets.forEach(function(v){
        var span = document.createElement('span'); span.className = 'v'; probe.appendChild(span);
        var h = 0;
        v.forEach(function(t){ span.innerHTML = t; h = Math.max(h, span.getBoundingClientRect().height); });
        total += h;
      });
      probe.remove();
      box.style.minHeight = Math.ceil(total) + 'px';
    }
    var rt = null;
    window.addEventListener('resize', function(){ clearTimeout(rt); rt = setTimeout(fit, 150); });
    if(document.fonts && document.fonts.ready) document.fonts.ready.then(fit);
    function paint(){
      var lines = linesAt(s), box = document.getElementById('poemtext'), dims = document.getElementById('dims');
      box.innerHTML = lines.map(function(t){ return '<span class="v">'+t+'</span>'; }).join('');
      if(s>=1){
        var st = DATA.steps[s-1];
        box.children[st.line].innerHTML = st.hi;
        dims.innerHTML = 'Mutació '+st.n+' de '+N+' &nbsp; '+st.before+' <span class="arrow">→</span> '+
          st.after+' &nbsp; '+st.pos+', '+st.edit;
      } else {
        dims.innerHTML = 'Poema original';
      }
    }
    function loop(){
      paint();
      var dur = (s===0) ? 700 : (s===N ? 1600 : base);
      s = (s>=N) ? 0 : s+1;
      timer = setTimeout(loop, dur);
    }

    function show(id){
      if(!document.getElementById(id)) id = 'poem';
      entries.forEach(function(e){ e.hidden = e.id !== id; });
      links.forEach(function(a){ a.classList.toggle('on', a.dataset.sec===id); });
      if(timer){ clearTimeout(timer); timer=null; }
      if(id==='poem'){ fit(); s=0; if(reduce){ s=N; paint(); } else { loop(); } }
      window.scrollTo({top:0});
    }
    links.forEach(function(a){
      a.addEventListener('click', function(ev){ ev.preventDefault();
        history.replaceState(null,'','#'+a.dataset.sec); show(a.dataset.sec); });
    });
    show((location.hash||'#poem').slice(1) || 'poem');
  })();
</script>
{{NAV}}
</body>
</html>
"""


if __name__ == "__main__":
    print(build())
