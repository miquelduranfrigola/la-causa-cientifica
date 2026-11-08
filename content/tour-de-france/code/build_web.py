"""Assemble the self-contained "Tour de França" page (index.html).

An animated map that plays through every edition of the Tour de France from 1985
to 2026. Europe is drawn once as a hairline ink outline on paper; a 1985->2026
timeline scrubs the years, and for each year the day's stages trace onto the map as
bowed arcs between their start and finish towns. The route being drawn and the
year readout are in the single blue accent; earlier years either accumulate as
faint ink ghosts (a palimpsest of four decades) or clear.

Editorial look (DESIGN.md): shared tokens and base styles are inlined from
shared/design/; only the map figure and its controls (square, 1px ink borders, sans
labels) are styled here. The year readout is serif with tabular figures. Three
views under a text menu: "El mapa", "El poema", "Metodologia". Everything is inlined
-- the computed routes (results/routes.json) and the simplified basemap
(data/europe.geojson) -- so the page makes no external requests.
"""

from __future__ import annotations

import html as _html
import json
import sys
from pathlib import Path

POEM_ROOT = Path(__file__).resolve().parent.parent
REPO = POEM_ROOT.parent.parent
sys.path.insert(0, str(REPO / "shared" / "design"))
from inline import design_css, nav_script, standalone_bar  # noqa: E402

ROUTES = POEM_ROOT / "results" / "routes.json"
GEOJSON = POEM_ROOT / "data" / "europe.geojson"
POEM_MD = POEM_ROOT / "poem.md"


def _poem_html() -> str:
    """Render poem.md (skipping its H1 title) as verse/stanza HTML."""
    lines = POEM_MD.read_text(encoding="utf-8").splitlines()
    out, seen_title = [], False
    for line in lines:
        if line.startswith("# ") and not seen_title:
            seen_title = True
            continue
        if not line.strip():
            out.append('<span class="br"></span>')
        else:
            out.append('<span class="v">' + _html.escape(line.strip()) + "</span>")
    return "\n".join(out)


def build() -> Path:
    routes = json.loads(ROUTES.read_text(encoding="utf-8"))
    geo = json.loads(GEOJSON.read_text(encoding="utf-8"))
    meta = routes["meta"]

    page = (_TEMPLATE
            .replace("{{FIRST}}", str(meta["first_year"]))
            .replace("{{LAST}}", str(meta["last_year"]))
            .replace("{{NYEARS}}", str(meta["n_years"]))
            .replace("{{NSTAGES}}", str(meta["n_stages"]))
            .replace("{{POEM}}", _poem_html())
            .replace("{{ROUTES}}", json.dumps(routes, ensure_ascii=False, separators=(",", ":")))
            .replace("{{GEO}}", json.dumps(geo, ensure_ascii=False, separators=(",", ":")))
            .replace("{{DESIGN}}", design_css())
            .replace("{{STANDALONE}}", standalone_bar())
            .replace("{{NAV}}", nav_script()))

    out = POEM_ROOT / "index.html"
    out.write_text(page, encoding="utf-8")
    return out


_TEMPLATE = r"""<!doctype html>
<html lang="ca">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Tour de França</title>
<style>
{{DESIGN}}
  .readout{ display:flex; align-items:baseline; gap:8px 32px; flex-wrap:wrap; padding:clamp(20px,3vw,32px) 0 8px; }
  .yr{ font-size:clamp(3rem,8vw,5.5rem); line-height:1; letter-spacing:-.02em; font-variant-numeric:tabular-nums lining-nums; color:var(--accent); }
  .stat{ margin:0; font-size:1.125rem; line-height:1.4; }
  .stat i{ font-style:italic; }
  .mapbox{ margin:0 calc(-1 * var(--edge) + 8px); padding:0; }
  svg.map{ width:100%; height:auto; max-height:78vh; display:block; }
  .land path{ fill:rgba(17,17,17,.035); stroke:var(--ink); stroke-opacity:.45; stroke-width:.6; vector-effect:non-scaling-stroke; }
  .route{ fill:none; stroke:var(--ink); stroke-width:1.2; stroke-linecap:round; stroke-linejoin:round; vector-effect:non-scaling-stroke; }
  .route.ghost{ stroke:rgba(17,17,17,.12); stroke-width:1; }
  .route.head{ stroke:var(--accent); stroke-width:2; }
  .draw{ transition:stroke-dashoffset var(--dur,.5s) ease; }

  .controls{ display:flex; align-items:center; gap:12px 20px; flex-wrap:wrap; padding:16px 0 0; border-top:1px solid var(--rule); font:400 .875rem/1.4 var(--sans); }
  .play{ font:inherit; background:var(--paper); color:var(--ink); border:1px solid var(--ink); border-radius:0; padding:6px 16px; min-width:7.5em; cursor:pointer; }
  .play:hover{ background:var(--ink); color:var(--paper); }
  .rail{ font-variant-numeric:tabular-nums; }
  input[type=range]{ flex:1; min-width:160px; height:24px; margin:0; background:transparent; accent-color:var(--accent); cursor:pointer; }
  input[type=range]{ -webkit-appearance:none; appearance:none; }
  input[type=range]::-webkit-slider-runnable-track{ height:1px; background:var(--ink); }
  input[type=range]::-webkit-slider-thumb{ -webkit-appearance:none; width:12px; height:20px; margin-top:-10px; background:var(--accent); border:0; border-radius:0; }
  input[type=range]::-moz-range-track{ height:1px; background:var(--ink); }
  input[type=range]::-moz-range-thumb{ width:12px; height:20px; background:var(--accent); border:0; border-radius:0; }
  .toggle{ display:flex; align-items:center; gap:8px; cursor:pointer; user-select:none; }
  .toggle input{ width:16px; height:16px; margin:0; accent-color:var(--accent); border-radius:0; }

  .verse{ margin-top:clamp(8px,2vw,16px); }
  .note{ margin-top:2em; padding-top:12px; border-top:1px solid var(--rule); }
  .note p{ margin:0; }
  section[hidden]{ display:none; }
  @media (max-width:600px){ .mapbox{ margin:0 -16px; } }
</style>
</head>
<body>
{{STANDALONE}}
<div class="page">
  <header class="head">
    <h1 class="title">Tour de França</h1>
    <p class="by">Miquel Duran-Frigola</p>
    <p class="sub">{{NYEARS}} edicions, de {{FIRST}} a {{LAST}}, traçades etapa a etapa</p>
  </header>
  <nav><ul class="subnav">
    <li><a data-sec="map" class="on" href="#map">El mapa</a></li>
    <li><a data-sec="poem" href="#poem">El poema</a></li>
    <li><a data-sec="method" href="#method">Metodologia</a></li>
  </ul></nav>

  <section id="map">
    <div class="readout">
      <div class="yr" id="yr" aria-live="off">{{FIRST}}</div>
      <p class="stat"><span id="ns">0</span> etapes · <span id="km">0</span> km</p>
      <p class="stat"><i>Gran Sortida</i> <span id="dep">—</span></p>
    </div>
    <div class="mapbox"><svg class="map" id="svg" role="img" aria-label="Mapa d'Europa amb els recorreguts del Tour de França" preserveAspectRatio="xMidYMid meet">
      <g class="land" id="land"></g>
      <g id="routes"></g>
    </svg></div>
    <div class="controls">
      <button class="play" id="play" type="button">Reprodueix</button>
      <span class="rail" id="y0">{{FIRST}}</span>
      <input type="range" id="slider" min="0" value="0" step="1" aria-label="Any">
      <span class="rail" id="y1">{{LAST}}</span>
      <label class="toggle"><input type="checkbox" id="acc" checked> Acumula els anys</label>
    </div>
  </section>

  <section id="poem" hidden style="margin-top:clamp(24px,4vw,40px)">
    <div class="verse">{{POEM}}</div>
  </section>

  <section id="method" hidden style="margin-top:clamp(24px,4vw,40px)">
    <div class="prose">
      <p>Cada dia de cada Tour, de {{FIRST}} a {{LAST}} —{{NSTAGES}} etapes en
         total—, es dibuixa com un arc entre la vila de sortida i la d'arribada.</p>
      <p class="label" style="margin-top:2em">Com es fa</p>
      <p>Les etapes s'extreuen dels articles de la Viquipèdia de cada edició
         (vila de sortida, vila d'arribada, distància i tipus). Cada vila es
         geocodifica amb OpenStreetMap (<i>Nominatim</i>) i el traçat de cada etapa és
         una corba de Bézier quadràtica entre els dos punts, corbada lleugerament
         perquè els recorreguts repetits se superposin i el mapa sembli un
         palimpsest. Les contrarellotges i pròlegs en circuit es dibuixen com un
         petit bucle al voltant de la vila.</p>
      <div class="note">
        <p class="label">Una advertència honesta</p>
        <p>Els arcs són reconstruccions que uneixen la sortida i
           l'arribada, <i>no</i> les carreteres reals. Els traçats GPS només
           existeixen a partir del 2014 aproximadament; per als anys anteriors mai
           es van registrar. El que veus és la forma d'un record, no un mapa de
           ruta.</p>
      </div>
    </div>
  </section>
</div>
<script>
  var ROUTES = {{ROUTES}};
  var GEO = {{GEO}};
  (function(){
    var years = ROUTES.years;
    var svg = document.getElementById('svg');
    var W = 1000, PAD = 26;

    // ---- projection: fixed extent from the basemap bbox ----
    var minLon=1e9, maxLon=-1e9, minLat=1e9, maxLat=-1e9;
    function scan(c){ if(c[0]<minLon)minLon=c[0]; if(c[0]>maxLon)maxLon=c[0];
                      if(c[1]<minLat)minLat=c[1]; if(c[1]>maxLat)maxLat=c[1]; }
    GEO.features.forEach(function(f){
      var g=f.geometry, polys=g.type==='Polygon'?[g.coordinates]:g.coordinates;
      polys.forEach(function(poly){ poly.forEach(function(ring){ ring.forEach(scan); }); });
    });
    var k = Math.cos((minLat+maxLat)/2 * Math.PI/180);
    var spanX = (maxLon-minLon)*k, spanY = (maxLat-minLat);
    var H = Math.round((W-2*PAD) * spanY/spanX) + 2*PAD;
    svg.setAttribute('viewBox', '0 0 '+W+' '+H);
    function px(lon){ return PAD + (lon-minLon)*k/spanX * (W-2*PAD); }
    function py(lat){ return PAD + (maxLat-lat)/spanY * (H-2*PAD); }
    function dpath(pts){  // pts are [lat,lon]
      var d=''; for(var i=0;i<pts.length;i++){ d+=(i?'L':'M')+px(pts[i][1]).toFixed(1)+','+py(pts[i][0]).toFixed(1); }
      return d;
    }

    // ---- draw the land once ----
    var land = document.getElementById('land'), lp='';
    GEO.features.forEach(function(f){
      var g=f.geometry, polys=g.type==='Polygon'?[g.coordinates]:g.coordinates;
      polys.forEach(function(poly){ poly.forEach(function(ring){
        var d=''; for(var i=0;i<ring.length;i++){ d+=(i?'L':'M')+px(ring[i][0]).toFixed(1)+','+py(ring[i][1]).toFixed(1); }
        lp += '<path d="'+d+'Z"/>';
      }); });
    });
    land.innerHTML = lp;

    // ---- state ----
    var routesG = document.getElementById('routes');
    var SVGNS = 'http://www.w3.org/2000/svg';
    var cur = 0, playing = false, timer = null, accumulate = true;
    var slider = document.getElementById('slider');
    slider.max = years.length - 1;

    var elYr=document.getElementById('yr'), elNs=document.getElementById('ns'),
        elKm=document.getElementById('km'), elDep=document.getElementById('dep');

    function fmt(n){ return String(Math.round(n)).replace(/\B(?=(\d{3})+(?!\d))/g,' '); }

    function readout(y){
      elYr.textContent = y.year; elNs.textContent = y.n_stages;
      elKm.textContent = fmt(y.total_km); elDep.textContent = y.grand_depart || '—';
    }

    function drawStages(stages, animate, ghost, idx){
      stages.forEach(function(s, i){
        var p = document.createElementNS(SVGNS,'path');
        p.setAttribute('d', dpath(s.points));
        p.setAttribute('class', ghost ? 'route ghost' : 'route live');
        routesG.appendChild(p);
        if(animate){
          var len = p.getTotalLength();
          p.style.strokeDasharray = len; p.style.strokeDashoffset = len;
          p.classList.add('head');
          setTimeout(function(){
            if(cur!==idx) return;              // year changed under us: abort
            p.classList.add('draw');
            p.style.setProperty('--dur', Math.min(.7, .28 + s.km/1400)+'s');
            p.style.strokeDashoffset = 0;
            setTimeout(function(){ p.classList.remove('head'); }, 700);
          }, i * 70);
        }
      });
    }

    function showYear(idx, animate){
      cur = idx; slider.value = idx; readout(years[idx]);
      if(animate){
        // demote what is already drawn to ghost (or wipe), then trace this year in
        if(!accumulate){ routesG.innerHTML=''; }
        else [].slice.call(routesG.children).forEach(function(p){ p.setAttribute('class','route ghost'); });
        drawStages(years[idx].stages, true, false, idx);
      } else {
        // static (re)build: full palimpsest up to idx when accumulating
        routesG.innerHTML = '';
        if(accumulate){ for(var j=0;j<idx;j++) drawStages(years[j].stages, false, true, j); }
        drawStages(years[idx].stages, false, false, idx);
      }
    }

    function stop(){ playing=false; clearTimeout(timer);
      document.getElementById('play').textContent='Reprodueix'; }
    function play(){
      playing=true; document.getElementById('play').textContent='Pausa';
      if(cur >= years.length-1) showYear(0, true); else showYear(cur, true);
      function tick(){
        if(!playing) return;
        var y = years[cur];
        var span = 700 + y.n_stages*70 + 500;  // draw time + hold
        timer = setTimeout(function(){
          if(!playing) return;
          if(cur >= years.length-1){ stop(); return; }
          showYear(cur+1, true); tick();
        }, span);
      }
      tick();
    }

    document.getElementById('play').addEventListener('click', function(){
      if(playing) stop(); else play();
    });
    slider.addEventListener('input', function(){ stop(); showYear(+slider.value, false); });
    document.getElementById('acc').addEventListener('change', function(e){
      accumulate = e.target.checked; showYear(cur, false);
    });

    // ---- views (text menu) ----
    var links = [].slice.call(document.querySelectorAll('[data-sec]'));
    var secs = [].slice.call(document.querySelectorAll('section[id]'));
    function route(id){
      if(!document.getElementById(id)) id = 'map';
      secs.forEach(function(s){ s.hidden = s.id !== id; });
      links.forEach(function(a){ a.classList.toggle('on', a.dataset.sec === id); });
      if(id !== 'map') stop();
    }
    links.forEach(function(a){ a.addEventListener('click', function(ev){
      ev.preventDefault(); route(a.dataset.sec); window.scrollTo(0,0);
    }); });

    showYear(0, false);
    route('map');
  })();
</script>
{{NAV}}
</body>
</html>
"""


if __name__ == "__main__":
    print(build())
