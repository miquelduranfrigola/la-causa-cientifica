"""Assemble the self-contained "Versos proteics" gallery (HTML).

Editorial treatment (see DESIGN.md): a title block, a text menu of the four poems
plus the methodology, and one piece at a time. Each poem entry loops through its
words: as each word darkens, the residues it produced colour in the protein
sequence (the N-to-C rainbow is this page's only colour exception) and in the 3D
structure (grey cartoon), synchronised. Structures are live 3Dmol.js viewers
(inlined), so residues can be recoloured on the fly; they auto-spin.

Merges results/globularity.csv + data/poems/_meta.json + the folded PDBs (from the
cache, or, when the cache is not on disk, from the structures embedded in the
previously built index.html) + inlined 3Dmol.js + the shared design from
shared/design/. The rubric table is read live from main.py. Writes index.html
(poem-folder root; everything inlined; no external requests).
"""

from __future__ import annotations

import csv
import html
import json
import re
import sys
from pathlib import Path

POEM_ROOT = Path(__file__).resolve().parent.parent
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
from folding import DEFAULT_CACHE, _seq_hash  # noqa: E402
from main import ESCAPE, PAIRS, SINGLES  # noqa: E402
from pipeline import poem_chunks, to_sequence  # noqa: E402

REPO = POEM_ROOT.parent.parent
sys.path.insert(0, str(REPO / "shared" / "design"))
from inline import add_book_section, design_css, nav_script, site_header  # noqa: E402

POEMS_DIR = POEM_ROOT / "data" / "poems"

# Amino-acid one-letter code -> Catalan name.
AA_CA = {
    "A": "alanina", "R": "arginina", "N": "asparagina", "D": "aspartat",
    "C": "cisteïna", "E": "glutamat", "Q": "glutamina", "G": "glicina",
    "H": "histidina", "I": "isoleucina", "L": "leucina", "K": "lisina",
    "M": "metionina", "F": "fenilalanina", "P": "prolina", "S": "serina",
    "T": "treonina", "W": "triptòfan", "Y": "tirosina", "V": "valina",
}


def _load():
    with (POEM_ROOT / "results" / "globularity.csv").open(encoding="utf-8") as fh:
        glob = {r["poem"]: r for r in csv.DictReader(fh)}
    meta_raw = json.loads((POEMS_DIR / "_meta.json").read_text("utf-8"))
    meta = {name: (title, author) for name, title, author in meta_raw}
    return glob, meta


def _embedded_pdbs() -> dict:
    """Return ``{entry id: [pdb, ...]}`` embedded in the previously built index.html.

    Used when the folding cache is not on disk (it is regenerable and git-ignored).
    """
    page = POEM_ROOT / "index.html"
    if not page.exists():
        return {}
    m = re.search(r"var DATA = (\{.*?\});\n\s*var DEFAULT_ID", page.read_text("utf-8"), re.DOTALL)
    if not m:
        return {}
    return {k: v["pdbs"] for k, v in json.loads(m.group(1)).items()}


def _pdb_text(seq: str) -> str:
    """Backbone-only PDB (N, CA, C, O) — all 3Dmol needs for a cartoon, ~half the size."""
    raw = (DEFAULT_CACHE / f"{_seq_hash(seq.strip().upper())}.pdb").read_text(encoding="utf-8")
    keep = []
    for line in raw.splitlines():
        if line.startswith("ATOM"):
            if line[12:16].strip() in ("N", "CA", "C", "O"):
                keep.append(line)
        elif line.startswith(("TER", "END")):
            keep.append(line)
    return "\n".join(keep) + "\n"


def _poem_payload(text: str, stem: str, embedded: dict):
    """Return (data, verses_html, sequence_html).

    data = {"pdbs": [...per domain...], "words": [{dom,a,b}...]} where a..b are
    1-based residue numbers within that domain (0 if the word yields no residues).
    Word spans in the verses and residue spans in the sequence share `data-w`.
    """
    chunks = poem_chunks(text)
    cum = [0]
    for c in chunks:
        cum.append(cum[-1] + len(c))
    tot = cum[-1] or 1
    cached = all((DEFAULT_CACHE / f"{_seq_hash(c.strip().upper())}.pdb").exists() for c in chunks)
    pdbs = [_pdb_text(c) for c in chunks] if cached else embedded[f"poem-{stem}"]

    words, verses, seqspans = [], [], []
    wi, g = 0, 0
    for line in text.splitlines():
        if not line.strip():
            if verses and not verses[-1].startswith('<span class="br"'):
                verses.append('<span class="br"></span>')  # stanza break
            continue
        toks = line.split()
        parts = []
        for ti, tok in enumerate(toks):
            res = to_sequence(tok)
            L = len(res)
            a, b = g, g + L
            g = b
            eol = 1 if ti == len(toks) - 1 else 0
            if L > 0:
                d = 0
                while d + 1 < len(cum) and a >= cum[d + 1]:
                    d += 1
                words.append({"dom": d, "a": a - cum[d] + 1, "b": b - cum[d], "n": L, "eol": eol})
                hue = round(240 * ((a + b) / 2) / tot)  # N-term red -> C-term blue
                style = f' style="--c:hsl({hue},62%,36%)"'
            else:
                words.append({"dom": -1, "a": 0, "b": 0, "n": 0, "eol": eol})
                style = ""
            parts.append(f'<span class="wd" data-w="{wi}">{html.escape(tok.replace(chr(39), "’"))}</span>')
            seqspans.append(f'<span class="res" data-w="{wi}"{style}>{html.escape(res)}</span>')
            wi += 1
        verses.append('<span class="v">' + " ".join(parts) + "</span>")

    return ({"pdbs": pdbs, "words": words, "off": cum[:-1], "tot": tot},
            "\n".join(verses), "".join(seqspans))


def _viewers_html(n: int) -> str:
    return "".join(f'<div class="viewer" data-dom="{i}"></div>' for i in range(n))


def _entry(stem, glob, meta, data_out, embedded) -> str:
    title, author = meta.get(stem, (stem, ""))
    text = (POEMS_DIR / f"{stem}.txt").read_text("utf-8")
    payload, verses_html, seq_html = _poem_payload(text, stem, embedded)
    data_out[f"poem-{stem}"] = payload
    return f"""
    <section class="entry" id="poem-{stem}" hidden>
      <h2 class="ptitle">{html.escape(title.replace(chr(39), "’"))}</h2>
      <p class="pauthor">{html.escape(author)}</p>
      <div class="split">
        <div class="structures">{_viewers_html(len(payload["pdbs"]))}</div>
        <div class="verse">{verses_html}</div>
      </div>
      <div class="how">
        <h3 class="label">Seqüència d’aminoàcids</h3>
        <div class="seq code">{seq_html}</div>
      </div>
    </section>"""


def _rubric_section() -> str:
    directs = "".join(
        f'<span class="map"><b class="code">{html.escape(k)}</b> → {v} {AA_CA[v]}</span>'
        for k, v in SINGLES.items())
    escapes = "".join(f'<span class="map"><b class="code">{html.escape(k)}</b> → {v}</span>'
                      for k, v in PAIRS.items())
    return f"""
    <section class="sec" id="rubric"><h2 class="label">Metodologia</h2>
      <div class="prose">
        <p>Cada lletra que ja és un codi d’aminoàcid es mapa a si mateixa;
        la resta s’escapa amb <b class="code">{ESCAPE}</b> seguida d’un aminoàcid.</p>
      </div>

      <div class="how">
        <h3 class="label">Correspondència directa</h3>
        <div class="maps">{directs}</div>
      </div>

      <div class="how">
        <h3 class="label">Escapaments amb {ESCAPE} ({AA_CA[ESCAPE]})</h3>
        <div class="maps">{escapes}</div>
      </div>
    </section>"""


def build() -> Path:
    glob, meta = _load()
    embedded = _embedded_pdbs()
    lib_js = (HERE / "vendor" / "3Dmol-min.js").read_text(encoding="utf-8")

    poems = [s for s in glob if (POEMS_DIR / f"{s}.txt").exists()]
    catalog = sorted(poems, key=lambda k: float(glob[k]["score"]), reverse=True)

    def title_of(stem):
        return meta.get(stem, (stem, ""))[0]

    menu = [f'<li><a data-sec="poem-{s}" href="#poem-{s}">{html.escape(title_of(s).replace(chr(39), "’"))}</a></li>'
            for s in catalog]
    menu.append('<li><a href="#rubric">Metodologia</a></li>')
    default = f"poem-{catalog[0]}" if catalog else ""

    data_out: dict = {}
    entries = "".join(_entry(s, glob, meta, data_out, embedded) for s in catalog) + _rubric_section()
    entries = entries.replace(f'id="{default}" hidden', f'id="{default}"', 1)  # shown from the first paint, so nothing jumps

    page = (_TEMPLATE
            .replace("{{DESIGN}}", design_css())
            .replace("{{HEADER}}", site_header())
            .replace("{{DEFAULT}}", default)
            .replace("{{MENU}}", "\n".join(menu))
            .replace("{{ENTRIES}}", entries)
            .replace("{{LIB}}", lib_js)
            .replace("{{NAV}}", nav_script())
            .replace("{{DATA}}", json.dumps(data_out, ensure_ascii=False)))
    out = POEM_ROOT / "index.html"
    page = add_book_section(page, POEM_ROOT.name)
    out.write_text(page, encoding="utf-8")
    return out


_TEMPLATE = r"""<!doctype html>
<html lang="ca">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Versos proteics</title>
<style>
{{DESIGN}}
  .entry[hidden]{ display:none; }
  .entry{ padding-top:clamp(28px,4vw,48px); animation:appear .25s ease both; }
  @keyframes appear{ from{ opacity:0; } to{ opacity:1; } }

  .ptitle{ margin:0; font-weight:400; font-size:clamp(1.75rem,3.6vw,2.75rem); line-height:1.1;
           letter-spacing:-.015em; text-wrap:balance; }
  .pauthor{ margin:8px 0 0; font-size:1.125rem; }

  /* structures (left, stacked) · poem (right, sized to its longest verse so no line is cut) */
  .split{ display:grid; grid-template-columns:17.5rem max-content; gap:clamp(24px,4vw,64px);
          align-items:start; margin:clamp(28px,4vw,48px) 0 0; }
  .structures{ display:flex; flex-direction:column; gap:clamp(14px,3vw,22px); align-items:center; }
  /* phones: the poem comes first, the folds follow as a compact row (no 600px of empty plate before the verse) */
  @media (max-width:760px){
    .split{ grid-template-columns:minmax(0,1fr); }
    .verse{ order:-1; }
    .structures{ display:grid; grid-template-columns:repeat(auto-fit,minmax(7.5rem,1fr)); gap:12px; }
    .structures .viewer{ justify-self:center; }
  }
  .viewer{ position:relative; width:100%; max-width:17.5rem; aspect-ratio:1; pointer-events:none; }
  .viewer canvas{ pointer-events:none; }

  @media (min-width:761px){
    .verse{ max-width:none; overflow-x:auto; }
    .verse .v{ white-space:nowrap; }
  }
  /* Every word stays in full ink (readable at rest); the words reached turn blue. */
  .wd{ color:var(--ink); transition:color .25s ease; }
  .wd.on{ color:var(--accent); }

  /* the sequence is machine text: mono, filling in the N-to-C rainbow */
  .seq{ line-height:1.7; word-break:break-all; letter-spacing:.02em; }
  .res{ color:rgba(17,17,17,.62); transition:color .25s ease; }
  .res.on{ color:var(--c); }

  .prose{ font-size:1.25rem; }
  .maps{ display:grid; grid-template-columns:repeat(auto-fill,minmax(min(100%,11.25rem),1fr)); gap:8px 24px; max-width:47.5rem; }
  .map{ overflow-wrap:anywhere; }
  @media (prefers-reduced-motion:reduce){
    .entry{ animation:none; }
    .wd,.res{ transition:none; }
    .wd.on{ color:var(--ink); }
  }
</style>
</head>
<body>
{{HEADER}}
<div class="page">
  <header class="head">
    <h1 class="title">Versos proteics</h1>
    <p class="sub">Cada poema, plegat com una proteïna amb ESMFold</p>
    <p class="cue">Cada paraula s’il·lumina mentre es llegeix, i la proteïna que dibuixa el poema gira al costat. Tria un poema aquí a sota.</p>
  </header>
  <nav><ul class="subnav">{{MENU}}</ul></nav>
  <main>
    {{ENTRIES}}
  </main>
</div>

<script>{{LIB}}</script>
<script>
  var DATA = {{DATA}};
  var DEFAULT_ID = "{{DEFAULT}}";
  (function(){
    var links = [].slice.call(document.querySelectorAll('[data-sec]'));
    var entries = [].slice.call(document.querySelectorAll('.entry'));
    var active = null;

    function teardown(){
      if(!active) return;
      if(active.st){ active.st.stop = true; clearTimeout(active.st.timer); }
      (active.viewers || []).forEach(function(v){ try{ v.spin(false); v.clear(); }catch(e){} });
      var el = document.getElementById(active.id);
      if(el){
        el.querySelectorAll('.viewer canvas').forEach(function(c){ c.remove(); });
        el.querySelectorAll('.on').forEach(function(h){ h.classList.remove('on'); });
      }
      active = null;
    }

    var GREY = 0xc9c9c4, BG = 0xfbfbf9;
    var REDUCED = window.matchMedia && matchMedia('(prefers-reduced-motion: reduce)').matches;

    function initEntry(id){
      var el = document.getElementById(id), d = DATA[id];
      if(!el || !d || !window.$3Dmol) return;
      var conts = [].slice.call(el.querySelectorAll('.viewer'));
      var viewers = [];
      var made = 0;
      (function make(){   // one viewer per task, so the page never freezes while the structures build
        var idx = made++, pdb = d.pdbs[idx], c = conts[idx];
        if(pdb === undefined){ if(REDUCED) paint(); return; }
        if(active && active.id !== id) return;
        if(c){
          var v = $3Dmol.createViewer(c, {backgroundColor:BG});
          v.setBackgroundColor(BG, 0);
          v.addModel(pdb, 'pdb');
          v.setStyle({}, {cartoon:{color:GREY}});
          v.zoomTo(); v.render(); v.resize(); v.render();
          if(!REDUCED) v.spin('y', 0.5);
          viewers.push(v);
        }
        setTimeout(make, 0);
      })();

      var wd = [], res = [];
      el.querySelectorAll('.wd').forEach(function(s){ wd[+s.dataset.w] = s; });
      el.querySelectorAll('.res').forEach(function(s){ res[+s.dataset.w] = s; });
      var words = d.words, off = d.off, tot = d.tot, i = 0, fDom = -1, fB = 0;

      function grad(idx){  // fixed rainbow along the whole protein (N->C), per domain
        return {cartoon:{colorscheme:{prop:'resi', gradient:'roygb',
                min:1 - off[idx], max:tot - off[idx]}}};
      }
      function paint(){  // reveal the rainbow cumulatively from the N-terminus
        viewers.forEach(function(v, idx){
          if(idx < fDom){
            v.setStyle({}, grad(idx));
          } else if(idx === fDom && fB > 0){
            v.setStyle({}, {cartoon:{color:GREY}});
            var arr = []; for(var r = 1; r <= fB; r++) arr.push(r);
            v.setStyle({resi:arr}, grad(idx));
          } else {
            v.setStyle({}, {cartoon:{color:GREY}});
          }
          v.render();
        });
      }
      var st = {stop:false, timer:null};
      if(REDUCED){  // no looping: show the whole poem and the finished fold at once
        words.forEach(function(w, k){ if(wd[k]) wd[k].classList.add('on'); if(res[k]) res[k].classList.add('on'); });
        fDom = off.length; fB = 0; paint();
        active = {id:id, viewers:viewers, st:st};
        return;
      }
      function step(){
        if(st.stop) return;
        if(i === 0){  // restart the fill
          el.querySelectorAll('.on').forEach(function(x){ x.classList.remove('on'); });
          fDom = -1; fB = 0; paint();
        }
        var w = words[i];
        if(wd[i]) wd[i].classList.add('on');
        if(res[i]) res[i].classList.add('on');
        if(w && w.a > 0){ fDom = w.dom; fB = w.b; paint(); }
        var dur = 250 + 28 * (w ? w.n : 0) + ((w && w.eol) ? 300 : 0);  // reading pace
        i = (i + 1) % words.length;
        st.timer = setTimeout(step, dur);
      }
      active = {id:id, viewers:viewers, st:st};
      step();
    }

    function show(id){
      var found = false;
      entries.forEach(function(e){ var on = e.id === id; e.hidden = !on; if(on) found = true; });
      if(!found){ id = DEFAULT_ID; document.getElementById(id).hidden = false; }
      links.forEach(function(a){ a.classList.toggle('on', a.dataset.sec === id); });
      teardown();
      if(DATA[id]) requestAnimationFrame(function(){ initEntry(id); });
    }

    links.forEach(function(a){
      a.addEventListener('click', function(ev){
        ev.preventDefault();
        history.replaceState(null, '', '#' + a.dataset.sec);
        show(a.dataset.sec);
        window.scrollTo(0, 0);
      });
    });
    window.addEventListener('resize', function(){
      if(active){ active.viewers.forEach(function(v){ try{ v.resize(); v.render(); }catch(e){} }); }
    });
    if(location.hash) show(location.hash.slice(1));
    else setTimeout(function(){ show(DEFAULT_ID); }, 250);   // the poem is already on the page; the 3D follows once it has painted
  })();
</script>
{{NAV}}
</body>
</html>
"""


if __name__ == "__main__":
    print(build())
