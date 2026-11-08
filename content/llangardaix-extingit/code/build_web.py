"""Build the self-contained web page for "Llangardaix extingit" -> index.html (poem-folder root).

A text menu ("El genoma" / "Metodologia") under the title, in the shared editorial
design (DESIGN.md) inlined from shared/design/ (no external requests). Served
verbatim via `page:`.
"""

from __future__ import annotations

import sys
import textwrap
from pathlib import Path

POEM_ROOT = Path(__file__).resolve().parent.parent
REPO = POEM_ROOT.parent.parent
RESULTS = POEM_ROOT / "results"
sys.path.insert(0, str(REPO / "shared" / "design"))
from inline import design_css, nav_script, standalone_bar  # noqa: E402

LINE_WIDTH = 60

METHOD = """\
<p>Reconstrucció de seqüències ancestrals (ASR) del genoma mitocondrial de
l'avantpassat comú de la sargantana de paret (<i>Podarcis muralis</i>) i el varà
aquàtic (<i>Varanus salvator</i>), a partir de sis espècies vives.</p>
<p>Es descarreguen els mitogenomes complets de GenBank (NCBI&nbsp;Entrez /
Biopython), s'alineen gen a gen i s'infereix l'avantpassat per màxima
versemblança amb el model <i>HKY85</i> i la poda de Felsenstein. Cada base
s'escriu en majúscula quan el posterior de la millor base supera 0,90; si no,
s'escriu amb el codi d'ambigüitat IUPAC del conjunt mínim de bases que cobreix el
90&nbsp;% del posterior —l'alfabet del dubte allà on el temps ha esborrat el
senyal.</p>
"""


_TEMPLATE = r"""<!doctype html>
<html lang="ca">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Llangardaix extingit</title>
<style>
{{DESIGN}}
  .seqbox{ margin-top:clamp(28px,4vw,48px); }
  .fasta-head{ margin:0 0 14px; word-break:break-all; }
  pre.seq{ font-size:.875rem; line-height:2; letter-spacing:.02em; white-space:pre; }
  .prose{ font-size:1.25rem; }
  section[hidden]{ display:none; }
</style>
</head>
<body>
{{STANDALONE}}
<div class="page">
  <header class="head">
    <h1 class="title">Llangardaix extingit</h1>
    <p class="by">Miquel Duran-Frigola</p>
    <p class="sub">Genoma mitocondrial inferit de l’avantpassat de <i>Podarcis muralis</i> i <i>Varanus salvator</i></p>
  </header>
  <nav><ul class="subnav">
    <li><a data-sec="obra" class="on" href="#obra">El genoma</a></li>
    <li><a data-sec="meto" href="#meto">Metodologia</a></li>
  </ul></nav>

  <section id="obra" style="margin-top:clamp(24px,4vw,40px)">
    <p class="label">{{LEN}} parells de bases · reconstrucció per màxima versemblança</p>
    <div class="seqbox how" style="margin-top:0">
      <p class="code fasta-head">&gt;sargantana_avi_ancestor mitogenome | ML reconstruction (HKY85)</p>
<pre class="seq">{{SEQ}}</pre>
    </div>
  </section>
  <section id="meto" hidden style="margin-top:clamp(24px,4vw,40px)">
    <div class="prose">{{METHOD}}</div>
  </section>
</div>
<script>
(function(){
  var links=[].slice.call(document.querySelectorAll('[data-sec]'));
  var secs=[].slice.call(document.querySelectorAll('section[id]'));
  function show(id){
    if(!document.getElementById(id)) id='obra';
    secs.forEach(function(s){ s.hidden = s.id!==id; });
    links.forEach(function(a){ a.classList.toggle('on', a.dataset.sec===id); });
  }
  links.forEach(function(a){ a.addEventListener('click', function(e){ e.preventDefault(); show(a.dataset.sec); window.scrollTo(0,0); }); });
  show('obra');
})();
</script>
{{NAV}}
</body>
</html>
"""


def build() -> Path:
    lines = (RESULTS / "ancestor.fasta").read_text().splitlines()
    seq = "".join(ln.strip() for ln in lines if not ln.startswith(">"))
    wrapped = "\n".join(textwrap.wrap(seq, LINE_WIDTH))
    page = (
        _TEMPLATE.replace("{{DESIGN}}", design_css())
        .replace("{{STANDALONE}}", standalone_bar())
        .replace("{{LEN}}", f"{len(seq):,}".replace(",", "."))
        .replace("{{SEQ}}", wrapped)
        .replace("{{METHOD}}", METHOD)
        .replace("{{NAV}}", nav_script())
    )
    out = POEM_ROOT / "index.html"
    out.write_text(page, encoding="utf-8")
    return out


if __name__ == "__main__":
    print(build())
