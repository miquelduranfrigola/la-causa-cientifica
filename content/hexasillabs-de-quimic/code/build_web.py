"""Assemble the self-contained "Hexasíl·labs de químic" web page (HTML).

Editorial look (DESIGN.md, shared/design/ inlined, no external requests): serif
title block, an italic descriptor, a text menu ("El poema" / "Metodologia") and the
poem running down the page as eight stanzas. Each stanza has ONE plate on its left
that cycles through its four molecules (fading, ink only); the matching verse turns
blue and each verse's gloss (italic) sits in a parallel column to its right.

Each verse is a hexasyllable and each stanza rhymes with its own suffix; at Mort the
metre deliberately collapses into short mineral words. Structures are drawn with RDKit
(CoordGen) in ink and inlined as SVG, resolved from PubChem (English name / CID) or a
SMILES override. Writes index.html (poem-folder root).

Run (needs rdkit + network for PubChem):
  python code/build_web.py
"""
from __future__ import annotations

import html
import json
import os
import re
import sys
import urllib.parse
import urllib.request

from rdkit import Chem
from rdkit.Chem import rdCoordGen
from rdkit.Chem.Draw import rdMolDraw2D

HERE = os.path.dirname(os.path.abspath(__file__))
POEM = os.path.dirname(HERE)
REPO = os.path.dirname(os.path.dirname(POEM))
sys.path.insert(0, os.path.join(REPO, "shared", "design"))
from inline import add_book_section, design_css, nav_script, site_header  # noqa: E402

OUT = os.path.join(POEM, "index.html")

STAGES = [
    {"id": "fetus", "stage": "fetus", "mols": [
        {"ca": "desoxiguanosina", "en": "deoxyguanosine", "g": "una de les quatre lletres amb què t'escriuen"},
        {"ca": "desoxicitidina",  "en": "deoxycytidine",  "g": "la que sempre s'aparella amb la G"},
        {"ca": "desoxitimidina",  "en": "thymidine",      "g": "la que et distingeix d'un virus d'ARN"},
        {"ca": "triiodotironina", "en": "triiodothyronine", "g": "l'hormona que et cabla el cervell abans de tenir-lo"}]},
    {"id": "nado", "stage": "nadó", "mols": [
        {"ca": "colecalciferol",  "en": "cholecalciferol", "g": "vitamina D en gotes, per un os que no ha vist el sol"},
        {"ca": "ergocalciferol",  "en": "ergocalciferol",  "g": "la mateixa vitamina, però treta d'un bolet"},
        {"ca": "fenoxietanol",    "en": "2-phenoxyethanol", "g": "el conservant que va dins la primera vacuna"},
        {"ca": "isoproterenol",   "en": "isoprenaline",    "g": "el primer cop que et costa respirar"}]},
    {"id": "infantesa", "stage": "infantesa", "mols": [
        {"ca": "butanoat d'etil", "en": "ethyl butanoate", "g": "olor de pinya: el xiclet"},
        {"ca": "hexanoat d'etil", "en": "ethyl hexanoate", "g": "olor de poma: la piruleta"},
        {"ca": "butirat de pentil", "en": "pentyl butyrate", "g": "olor de plàtan: el iogurt de colors"},
        {"ca": "salicilat d'etil", "en": "ethyl salicylate", "g": "olor de menta: la primera pasta de dents"}]},
    {"id": "adolescencia", "stage": "adolescència", "mols": [
        {"ca": "metiltestosterona", "en": "methyltestosterone", "g": "la veu que se't trenca i el borrissol"},
        {"ca": "fluoximesterona",   "en": "fluoxymesterone",    "g": "el que algú es punxa al vestidor del gimnàs"},
        {"ca": "espironolactona",   "en": "spironolactone",     "g": "la pastilla contra els grans (i contra el gènere)"},
        {"ca": "desoximetasona",    "en": "desoximetasone",     "g": "la crema per a la cara vermella"}]},
    {"id": "joventut", "stage": "joventut", "mols": [
        {"ca": "feniletilamina",    "smiles": "NCCc1ccccc1", "g": "el que et deixa el cor quan t'enamores (i la xocolata)"},
        {"ca": "dimetiltriptamina", "en": "dimethyltryptamine", "g": "l'univers sencer en cinc minuts"},
        {"ca": "dietiltriptamina",  "en": "diethyltryptamine",  "g": "la cosina de sortida llarga de la DMT"},
        {"ca": "hidroximescalina",  "smiles": "COc1cc(CCN)cc(OC)c1O", "g": "el que porta el peiot, al desert"}]},
    {"id": "adultesa", "stage": "adultesa", "mols": [
        {"ca": "àcid undecanoic",  "en": "undecanoic acid",  "g": "un greix que s'acumula sense avisar"},
        {"ca": "àcid tridecanoic", "en": "tridecanoic acid", "g": "cadena imparella, rara, com tu als quaranta"},
        {"ca": "àcid icosanoic",   "en": "icosanoic acid",   "g": "vint carbonis de sopar tard i seure molt"},
        {"ca": "àcid octandioic",  "en": "octanedioic acid", "g": "fins la teva suor ja fa una altra olor"}]},
    {"id": "vellesa", "stage": "vellesa", "mols": [
        {"ca": "acetazolamida",   "en": "acetazolamide",   "g": "per al glaucoma: la vista que s'estreny"},
        {"ca": "acetohexamida",   "en": "acetohexamide",   "g": "per al sucre que ja no saps controlar"},
        {"ca": "ciclopentiazida", "en": "cyclopenthiazide", "g": "per a la tensió i les nits al lavabo"},
        {"ca": "meticlotiazida",  "en": "methyclothiazide", "g": "i un altre, per les cames que s'inflen"}]},
    {"id": "mort", "stage": "mort", "mols": [
        {"ca": "hidroxiapatita", "smiles": "[OH-].[Ca+2].[Ca+2].[Ca+2].[Ca+2].[Ca+2].[O-]P([O-])([O-])=O.[O-]P([O-])([O-])=O.[O-]P([O-])([O-])=O", "g": "el mineral de l'os: el que de tu perdura"},
        {"ca": "calcita",  "smiles": "[Ca+2].[O-]C([O-])=O",        "g": "el calci, tornat pedra calcària"},
        {"ca": "pirita",   "smiles": "[Fe+2].[S-][S-]",             "g": "l'or dels ximples, avall"},
        {"ca": "hematita", "smiles": "[O-2].[O-2].[O-2].[Fe+3].[Fe+3]", "g": "el ferro de la sang, ara rovell"}]},
]


def _pubchem(path):
    url = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/" + path
    try:
        with urllib.request.urlopen(url, timeout=60) as fh:
            return json.load(fh)
    except Exception:
        return {}


def smiles_for(m):
    if m.get("smiles"):
        return m["smiles"]
    ident = (f"cid/{m['cid']}" if m.get("cid")
             else "name/" + urllib.parse.quote(m["en"]))
    for prop in ("SMILES", "IsomericSMILES", "CanonicalSMILES"):
        data = _pubchem(f"{ident}/property/{prop}/JSON")
        for p in data.get("PropertyTable", {}).get("Properties", []):
            if p.get(prop):
                return p[prop]
    return ""


def mol_svg(smiles, px=360):
    mol = Chem.MolFromSmiles(smiles) if smiles else None
    if mol is None:
        return ""
    rdCoordGen.AddCoords(mol)
    d = rdMolDraw2D.MolDraw2DSVG(px, px)
    opt = d.drawOptions()
    opt.clearBackground = False
    opt.bondLineWidth = 2
    opt.scaleBondWidth = True
    opt.padding = 0.08
    opt.minFontSize = 15
    opt.maxFontSize = 24
    opt.additionalAtomLabelPadding = 0.08
    # Printed plate: every atom label in ink (the page's one blue is reserved for the active verse).
    ink = (0.067, 0.067, 0.067)
    opt.setAtomPalette({k: ink for k in (-1, 6, 7, 8, 9, 11, 15, 16, 17, 19, 20, 24, 25, 26, 35, 53)})
    rdMolDraw2D.PrepareAndDrawMolecule(d, mol)
    d.FinishDrawing()
    return re.sub(r"<\?xml[^>]*\?>\s*", "", d.GetDrawingText()).strip()


def build():
    stanzas, missing = [], []
    for s in STAGES:
        slides, lines = [], []
        for k, m in enumerate(s["mols"]):
            svg = mol_svg(smiles_for(m))
            if not svg:
                missing.append(m["ca"])
            slides.append(f'<div class="slide" data-k="{k}">{svg or "<span>—</span>"}</div>')
            lines.append(f'<div class="line" data-k="{k}">'
                         f'<span class="name">{html.escape(m["ca"])}</span>'
                         f'<span class="gloss">{html.escape(m["g"])}</span></div>')
        stanzas.append(f"""
      <section class="stanza">
        <p class="stage">{html.escape(s['stage'])}</p>
        <div class="split">
          <div class="viewer">{''.join(slides)}</div>
          <div class="verses">{''.join(lines)}</div>
        </div>
      </section>""")

    if missing:
        print("SENSE ESTRUCTURA:", missing)
    page = (_TEMPLATE.replace("{{DESIGN}}", design_css())
            .replace("{{HEADER}}", site_header())
            .replace("{{STANZAS}}", "".join(stanzas))
            .replace("{{NAV}}", nav_script()))
    page = add_book_section(page, os.path.basename(POEM))
    with open(OUT, "w", encoding="utf-8") as fh:
        fh.write(page)
    return OUT


_TEMPLATE = r"""<!doctype html>
<html lang="ca">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Hexasíl·labs de químic</title>
<style>
{{DESIGN}}
  .stanza{ padding:clamp(20px,3vw,32px) 0; border-top:1px solid var(--rule); }
  /* on wide screens the eight ages sit two by two, the molecule above the lines it names */
  @media (min-width:72rem){
    .stanzas{ display:grid; grid-template-columns:repeat(2,minmax(0,1fr)); gap:0 clamp(40px,5vw,80px); }
    .stanza .split{ grid-template-columns:11rem minmax(0,1fr); gap:clamp(20px,2.4vw,32px); align-items:start; }
    .stanza .viewer{ max-width:11rem; }
    .stanza .verses{ grid-template-columns:minmax(0,1fr); }
    .stanza .name{ padding:6px 0 0; } .stanza .gloss{ padding:0 0 4px; }
  }
  .stage{ margin:0 0 clamp(14px,2vw,22px); font:600 .875rem/1.4 var(--sans); }

  .split{ display:grid; grid-template-columns:clamp(13rem,26vw,17.5rem) minmax(0,1fr);
          gap:clamp(28px,4.5vw,64px); align-items:center; }
  @media (max-width:45rem){ .split{ grid-template-columns:1fr; gap:20px; } }

  .viewer{ position:relative; width:100%; max-width:17.5rem; aspect-ratio:1; }
  .slide{ position:absolute; inset:0; display:flex; align-items:center; justify-content:center;
          opacity:0; transition:opacity .7s ease; }
  .slide.on{ opacity:1; }
  .slide svg{ width:100%; height:100%; overflow:visible; }

  .verses{ display:grid; grid-template-columns:minmax(0,12.5rem) minmax(0,1fr);
           column-gap:clamp(18px,3vw,34px); align-items:baseline; }
  .line{ display:contents; }
  .name{ font-size:1.375rem; line-height:1.3; padding:4px 0; overflow-wrap:anywhere; transition:color .4s ease; }
  .gloss{ font-size:1rem; line-height:1.35; padding:4px 0; }
  .line.on .name{ color:var(--accent); }
  @media (max-width:60rem){
    .verses{ grid-template-columns:minmax(0,1fr); }
    .name{ padding:10px 0 0; } .gloss{ padding:0 0 4px; }
  }
  @media (prefers-reduced-motion:reduce){ .slide, .name{ transition:none; } }
  .page > section{ margin-top:clamp(24px,4vw,40px); }
</style>
</head>
<body>
{{HEADER}}
<div class="page">
  <header class="head">
    <h1 class="title">Hexasíl·labs de químic</h1>
    <p class="sub">Una vida en vuit edats, dita amb noms de molècules</p>
    <p class="cue">Els versos s’encenen un a un i, al costat, es dibuixa la molècula que anomenen.</p>
  </header>
  <nav><ul class="subnav">
    <li><a class="on" href="#poema">El poema</a></li>
    <li><a href="#metode">Metodologia</a></li>
  </ul></nav>
<main>

  <section id="poema">
    <div class="prose"><p>Cada vers, un hexasíl·lab; cada estrofa, la seva rima. El plafó va passant les molècules de cada edat.</p></div>
    <div class="stanzas">{{STANZAS}}</div>
  </section>

  <section id="metode" class="sec"><h2 class="label">Metodologia</h2>
    <div class="prose">
      <p>Cada vers és el nom d'una molècula real, en català, i un
        hexasíl·lab (sis síl·labes fins a l'última tònica). Cada estrofa —del fetus
        a la mort— rima amb un sufix diferent. A la mort l'hexasíl·lab es trenca a
        posta: el vers es torna pedra, mineral, curt.</p>
      <p>Estructures dibuixades amb RDKit; els minerals surten esquemàtics.
        Recompte de síl·labes amb el motor de Softcatalà.</p>
    </div>
  </section>
</main>
</div>

<script>
(function(){
  var reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  [].slice.call(document.querySelectorAll('.stanza')).forEach(function(st, si){
    var slides = [].slice.call(st.querySelectorAll('.slide'));
    var lines = [].slice.call(st.querySelectorAll('.line'));
    if(!slides.length) return;
    var k = 0;
    function paint(){
      slides.forEach(function(s, j){ s.classList.toggle('on', j === k); });
      lines.forEach(function(l, j){ l.classList.toggle('on', j === k); });
    }
    paint();
    if(!reduce){ setTimeout(function(){
      setInterval(function(){ k = (k + 1) % slides.length; paint(); }, 2600); }, si * 650); }
  });
})();
</script>
{{NAV}}
</body>
</html>
"""


if __name__ == "__main__":
    print(build())
