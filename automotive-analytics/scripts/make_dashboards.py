"""Accessible, presentable dashboards for the automotive projects.

Layout per project (2 pages + drillthrough):
  Page 1: multicard KPIs + gauge (vs target) + bar chart (clickable -> drillthrough)
  Page 2: multicard KPIs + gauge (vs target) + bar chart (clickable -> drillthrough)
  Drillthrough page: detail for the clicked item (trend + table)
Design: high contrast, >=14pt body, >=24pt callouts, nav tabs, hover states.
"""
import json
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
OUT = ROOT / "powerbi"

CSS = """
:root{--navy:#1F4E79;--orange:#C55A11;--blue:#2E75B6;--gray:#7F7F7F;--bg:#F7F9FC;--card:#fff;--line:#D5DEE8}
*{box-sizing:border-box}
body{font-family:'Segoe UI',Arial,sans-serif;font-size:16px;line-height:1.55;margin:0;color:#111;background:var(--bg)}
header{background:var(--navy);color:#fff;padding:18px 28px;display:flex;align-items:baseline;gap:18px;flex-wrap:wrap}
header h1{font-size:28px;margin:0}
header .sub{font-size:15px;opacity:.85}
nav{display:flex;gap:8px;padding:10px 28px 0;background:var(--navy)}
nav button{font-size:16px;font-weight:600;padding:10px 22px;border:none;border-radius:10px 10px 0 0;background:#163A5C;color:#CFE0F0;cursor:pointer}
nav button.active{background:var(--bg);color:var(--navy)}
main{padding:24px 28px;max-width:1100px}
.page{display:none}.page.active{display:block}
h2{font-size:22px;color:var(--navy);margin:6px 0 14px;border-bottom:2px solid var(--navy);padding-bottom:6px}
.grid{display:grid;gap:16px}
.g3{grid-template-columns:repeat(3,1fr)}
@media(max-width:900px){.g3{grid-template-columns:1fr}}
.panel{background:var(--card);border:1px solid var(--line);border-radius:12px;padding:16px;box-shadow:0 1px 3px rgba(20,40,70,.08)}
.panel h3{font-size:17px;margin:0 0 10px;color:#333}
.cards{display:flex;gap:14px;flex-wrap:wrap}
.mcard{flex:1;min-width:200px;background:linear-gradient(135deg,#fff, #EEF4FB);border:2px solid var(--navy);border-radius:12px;padding:16px 18px;transition:transform .12s}
.mcard:hover{transform:translateY(-3px)}
.mcard .k{font-size:15px;color:#444}
.mcard .v{font-size:32px;font-weight:800;color:var(--navy);margin-top:2px}
.mcard .d{font-size:14px;color:#555;margin-top:2px}
svg text{font-family:'Segoe UI',Arial,sans-serif}
.bar-rect{cursor:pointer}
.bar-rect:hover{opacity:.8}
.drill-hint{font-size:14px;color:var(--orange);font-weight:600;margin-top:6px}
table{border-collapse:collapse;font-size:15px;width:100%}
th{border-bottom:3px solid var(--navy);padding:8px;text-align:left;background:#EAF1F9}
td{border-bottom:1px solid var(--line);padding:8px}
.back{font-size:16px;font-weight:700;color:#fff;background:var(--orange);border:none;border-radius:8px;padding:10px 18px;cursor:pointer;margin-bottom:14px}
.note{font-size:14px;color:#555}
"""

JS = r"""
const state = {sel: null, back: 'p1'};
function show(id, btn) {
  document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
  document.getElementById(id).classList.add('active');
  document.querySelectorAll('nav button').forEach(b => b.classList.remove('active'));
  (btn || document.querySelector('nav button[data-page="' + id + '"]')).classList.add('active');
  window.scrollTo(0, 0);
}
function cards(el, items) {
  el.innerHTML = items.map(i => '<div class="mcard"><div class="k">' + i.k + '</div><div class="v">' + i.v + '</div>' + (i.d ? '<div class="d">' + i.d + '</div>' : '') + '</div>').join('');
}
function gauge(el, o) {
  const W = 320, H = 200, cx = W/2, cy = 170, r = 130;
  const frac = Math.max(0, Math.min(1, o.value / o.max));
  const tFrac = Math.max(0, Math.min(1, (o.target || 0) / o.max));
  const ang = f => Math.PI * (1 - f);
  const pt = (f, rr) => [cx + rr * Math.cos(ang(f)), cy - rr * Math.sin(ang(f))];
  const arc = (f0, f1, rr, color, w) => {
    const p0 = pt(f0, rr), p1 = pt(f1, rr);
    return '<path d="M ' + p0[0] + ' ' + p0[1] + ' A ' + rr + ' ' + rr + ' 0 ' + (f1 - f0 > 0.5 ? 1 : 0) + ' 1 ' + p1[0] + ' ' + p1[1] + '" fill="none" stroke="' + color + '" stroke-width="' + w + '" stroke-linecap="round"/>';
  };
  let s = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" role="img" aria-label="' + o.title + ': ' + o.value + o.unit + ' of target ' + o.target + o.unit + '">';
  s += '<text x="' + cx + '" y="26" font-size="17" font-weight="700" text-anchor="middle" fill="#111">' + o.title + '</text>';
  s += arc(0, 1, r, '#E3E9F0', 26);
  s += arc(0, frac, r, frac >= tFrac ? '#1F4E79' : '#C55A11', 26);
  const tp = pt(tFrac, r);
  s += '<line x1="' + (cx + (r-20)*Math.cos(ang(tFrac))) + '" y1="' + (cy - (r-20)*Math.sin(ang(tFrac))) + '" x2="' + tp[0] + '" y2="' + tp[1] + '" stroke="#C55A11" stroke-width="4"/><title>target ' + o.target + o.unit + '</title>';
  s += '<text x="' + cx + '" y="' + (cy - 30) + '" font-size="34" font-weight="800" text-anchor="middle" fill="#111">' + o.value + o.unit + '</text>';
  s += '<text x="' + cx + '" y="' + (cy - 8) + '" font-size="14" text-anchor="middle" fill="#555">target ' + o.target + o.unit + ' · scale max ' + o.max + o.unit + '</text>';
  s += '<text x="' + cx + '" y="' + (H - 8) + '" font-size="15" text-anchor="middle" font-weight="700" fill="' + (frac >= tFrac ? '#1F4E79' : '#C55A11') + '">' + (frac >= tFrac ? '● ON TARGET' : '● BELOW TARGET') + '</text>';
  s += '</svg>';
  if (el) el.innerHTML = s; return s;
}
function bar(el, o) {
  const W = 460, H = 330, m = {l: 64, r: 16, t: 42, b: 78};
  const max = Math.max(...o.values) * 1.15;
  const bw = (W - m.l - m.r) / o.values.length;
  let s = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" role="img" aria-label="' + o.title + '">';
  s += '<text x="' + m.l + '" y="26" font-size="17" font-weight="700" fill="#111">' + o.title + '</text>';
  for (let g = 0; g <= 4; g++) {
    const y = m.t + (H - m.t - m.b) * (1 - g / 4), v = max * g / 4;
    s += '<line x1="' + m.l + '" y1="' + y + '" x2="' + (W - m.r) + '" y2="' + y + '" stroke="#D5DEE8"/>' +
         '<text x="' + (m.l - 8) + '" y="' + (y + 5) + '" font-size="13" text-anchor="end" fill="#444">' + v.toFixed(0) + '</text>';
  }
  o.values.forEach((v, i) => {
    const h = (H - m.t - m.b) * v / max, x = m.l + i * bw + bw * 0.14, w = bw * 0.72;
    s += '<rect class="bar-rect" data-i="' + i + '" x="' + x + '" y="' + (m.t + (H - m.t - m.b) - h) + '" width="' + w + '" height="' + h + '" rx="4" fill="' + (o.colors ? o.colors[i] : '#1F4E79') + '">' +
         '<title>' + o.labels[i] + ': ' + v.toFixed(1) + (o.unit || '') + ' — click to drill through</title></rect>';
    s += '<text x="' + (x + w / 2) + '" y="' + (H - m.b + 22) + '" font-size="13" text-anchor="middle" fill="#111" transform="rotate(-24 ' + (x + w / 2) + ' ' + (H - m.b + 22) + ')">' + o.labels[i] + '</text>';
    s += '<text x="' + (x + w / 2) + '" y="' + (m.t + (H - m.t - m.b) - h - 6) + '" font-size="14" font-weight="700" text-anchor="middle" fill="#111">' + v.toFixed(1) + '</text>';
  });
  s += '</svg>';
  if (el) {
    el.innerHTML = s;
    el.querySelectorAll('.bar-rect').forEach(r => r.addEventListener('click', () => { if (o.onDrill) o.onDrill(o.labels[+r.dataset.i]); }));
  }
  return s;
}
function line(el, series, o) {
  const W = 920, H = 300, m = {l: 56, r: 16, t: 40, b: 44};
  const allV = series.flatMap(s => s.values);
  const max = Math.max(...allV) * 1.1, min = Math.min(...allV) * 0.92;
  const X = i => m.l + (W - m.l - m.r) * i / (series[0].x.length - 1);
  const Y = v => m.t + (H - m.t - m.b) * (1 - (v - min) / (max - min));
  let s = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" role="img" aria-label="' + o.title + '">';
  s += '<text x="' + m.l + '" y="26" font-size="17" font-weight="700" fill="#111">' + o.title + '</text>';
  for (let g = 0; g <= 4; g++) {
    const y = m.t + (H - m.t - m.b) * (1 - g / 4), v = min + (max - min) * g / 4;
    s += '<line x1="' + m.l + '" y1="' + y + '" x2="' + (W - m.r) + '" y2="' + y + '" stroke="#D5DEE8"/>' +
         '<text x="' + (m.l - 8) + '" y="' + (y + 5) + '" font-size="13" text-anchor="end" fill="#444">' + v.toFixed(0) + '</text>';
  }
  const pal = ['#1F4E79', '#C55A11'];
  series.forEach((sr, k) => {
    const pts = sr.x.map((_, i) => X(i) + ',' + Y(sr.values[i])).join(' ');
    s += '<polyline points="' + pts + '" fill="none" stroke="' + pal[k % 2] + '" stroke-width="3.5"/>';
    sr.values.forEach((v, i) => s += '<circle cx="' + X(i) + '" cy="' + Y(v) + '" r="4" fill="' + pal[k % 2] + '"><title>' + sr.x[i] + ': ' + v.toFixed(1) + '</title></circle>');
    s += '<text x="' + (W - m.r) + '" y="' + (44 + k * 22) + '" font-size="14" text-anchor="end" font-weight="700" fill="' + pal[k % 2] + '">' + sr.name + '</text>';
  });
  series[0].x.forEach((t, i) => { if (i % Math.ceil(series[0].x.length / 10) === 0)
    s += '<text x="' + X(i) + '" y="' + (H - m.b + 20) + '" font-size="12" text-anchor="middle" fill="#111">' + t + '</text>'; });
  s += '</svg>';
  if (el) el.innerHTML = s; return s;
}

function treemap(el, o) {
  // squarified-ish treemap: proportional rectangles, label + value + share
  const W = 460, H = 300, m = {l: 8, r: 8, t: 36, b: 8};
  const total = o.values.reduce((a, b) => a + b, 0);
  const pal = ['#1F4E79', '#2E75B6', '#C55A11', '#7F7F7F', '#BF8F00', '#548235'];
  let s = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" role="img" aria-label="' + o.title + '">';
  s += '<text x="' + m.l + '" y="24" font-size="17" font-weight="700" fill="#111">' + o.title + '</text>';
  // simple slice layout: rows proportional to value
  let y = m.t;
  const innerH = H - m.t - m.b;
  o.values.forEach((v, i) => {
    const h = innerH * v / total;
    s += '<rect class="bar-rect" data-i="' + i + '" x="' + m.l + '" y="' + y + '" width="' + (W - m.l - m.r) + '" height="' + Math.max(h - 3, 14) + '" rx="5" fill="' + pal[i % pal.length] + '">' +
         '<title>' + o.labels[i] + ': ' + v.toFixed(1) + (o.unit || '') + ' (' + (100 * v / total).toFixed(1) + '%) — click to drill</title></rect>';
    s += '<text x="' + (m.l + 10) + '" y="' + (y + Math.max(h - 3, 14) / 2 + 5) + '" font-size="15" font-weight="700" fill="#fff">' + o.labels[i] + ' — ' + v.toFixed(0) + (o.unit || '') + ' (' + (100 * v / total).toFixed(0) + '%)</text>';
    y += h;
  });
  s += '</svg>';
  if (el) {
    el.innerHTML = s;
    el.querySelectorAll('.bar-rect').forEach(r => r.addEventListener('click', () => { if (o.onDrill) o.onDrill(o.labels[+r.dataset.i]); }));
  }
  return s;
}
function ribbon(el, data, years) {
  // rank-shift ribbon: lanes per region, band width = revenue, color shifts with rank
  const regions = [...new Set(data.map(d => d.region))];
  const W = 920, H = 320, m = {l: 110, r: 20, t: 40, b: 40};
  const pal = ['#1F4E79', '#2E75B6', '#C55A11', '#7F7F7F', '#BF8F00', '#548235'];
  const colW = (W - m.l - m.r) / years.length;
  const maxRev = Math.max(...data.map(d => d.revenue_eur_m));
  const laneH = (H - m.t - m.b) / regions.length;
  let s = '<svg viewBox="0 0 ' + W + ' ' + H + '" width="100%" role="img" aria-label="Revenue rank ribbon by region">';
  s += '<text x="' + m.l + '" y="24" font-size="17" font-weight="700" fill="#111">Region rank ribbon — band thickness = revenue, color = rank (dark = #1)</text>';
  years.forEach((y, yi) => {
    s += '<text x="' + (m.l + yi * colW + colW / 2) + '" y="' + (H - m.b + 22) + '" font-size="14" text-anchor="middle" font-weight="600" fill="#111">' + y + '</text>';
    const col = data.filter(d => d.year === y).sort((a, b) => a.revenue_rank - b.revenue_rank);
    col.forEach((d, ri) => {
      const h = Math.max((H - m.t - m.b) * d.revenue_eur_m / maxRev, 6);
      const yc = m.t + (H - m.t - m.b) / 2 + (ri - (col.length - 1) / 2) * laneH * 0.9;
      // conditional formatting color by rank: rank1 dark navy -> last light gray
      const shade = pal[Math.min(ri, pal.length - 1)];
      s += '<rect class="bar-rect" data-region="' + d.region + '" x="' + (m.l + yi * colW + 3) + '" y="' + (yc - h / 2) + '" width="' + (colW - 6) + '" height="' + h + '" rx="4" fill="' + shade + '" opacity="' + (0.55 + 0.45 * d.revenue_rank / col.length) + '">' +
           '<title>' + d.region + ' ' + y + ': rank #' + d.revenue_rank + ', ' + d.revenue_eur_m.toFixed(0) + ' M€ — click to drill</title></rect>';
    });
  });
  regions.forEach((r, i) => {
    s += '<text x="' + (m.l - 8) + '" y="' + (m.t + i * laneH + laneH / 2 + 5) + '" font-size="13" text-anchor="end" fill="#111">' + r + '</text>';
  });
  s += '</svg>';
  if (el) {
    el.innerHTML = s;
    el.querySelectorAll('.bar-rect').forEach(r => r.addEventListener('click', () => { if (window._ribbonDrill) window._ribbonDrill(r.dataset.region); }));
  }
  return s;
}
function slicer(el, items, onPick) {
  // horizontal pill slicer: single-select buttons
  el.innerHTML = '<div style="display:flex;gap:8px;flex-wrap:wrap">' + items.map((it, i) =>
    '<button class="slicer-btn" data-i="' + i + '" style="font-size:15px;font-weight:600;padding:8px 16px;border-radius:20px;border:2px solid #1F4E79;background:' + (i === 0 ? '#1F4E79' : '#fff') + ';color:' + (i === 0 ? '#fff' : '#1F4E79') + ';cursor:pointer">' + it + '</button>').join('') + '</div>';
  el.querySelectorAll('.slicer-btn').forEach(b => b.addEventListener('click', () => {
    el.querySelectorAll('.slicer-btn').forEach(x => { x.style.background = '#fff'; x.style.color = '#1F4E79'; });
    b.style.background = '#1F4E79'; b.style.color = '#fff';
    if (onPick) onPick(items[+b.dataset.i]);
  }));
}
function table(el, cols, rows) {
  const s = '<table><thead><tr>' + cols.map(c => '<th>' + c + '</th>').join('') + '</tr></thead><tbody>' +
    rows.map(r => '<tr>' + cols.map(c => '<td>' + (r[c] ?? '') + '</td>').join('') + '</tr>').join('') + '</tbody></table>';
  if (el) el.innerHTML = s; return s;
}
"""

def page(title, sub, nav, body, js):
    return ('<!doctype html><html lang="en"><head><meta charset="utf-8">'
            '<meta name="viewport" content="width=device-width,initial-scale=1">'
            '<title>' + title + '</title><style>' + CSS + '</style></head><body>'
            '<header><h1>' + title + '</h1><span class="sub">' + sub + '</span></header>'
            '<nav>' + nav + '</nav><main>' + body + '</main>'
            '<script>' + JS + '</script><script>' + js + '</script></body></html>')

def j(df):
    df = df.copy()
    for c in df.columns:
        if str(df[c].dtype).startswith("datetime64"):
            df[c] = df[c].astype(str)
    return json.dumps(df.to_dict("records"))

# ============================= PROJECT A =============================
fin_y = pd.read_csv(PROC / "rpt_fin_yearly.csv")
fin_p = pd.read_csv(PROC / "rpt_fin_by_plant.csv")
fin_m = pd.read_csv(ROOT / "data" / "parsed" / "financials_monthly.csv")
log_y = pd.read_csv(PROC / "rpt_logistics_yearly.csv")
lt_m = pd.read_csv(PROC / "rpt_leadtime_by_material.csv")
log_raw = pd.read_csv(ROOT / "data" / "parsed" / "logistics_orders.csv")

last_y = int(fin_y.iloc[-1].year)
ly = pd.read_csv(PROC / "rpt_logistics_yearly.csv").iloc[-1]
navA = ('<button data-page="p1" class="active" onclick="show(\'p1\',this)">1 · Financial Overview</button>'
        '<button data-page="p2" onclick="show(\'p2\',this)">2 · Logistics &amp; Operations</button>'
        '<button data-page="drill" onclick="show(\'drill\',this)">3 · Drillthrough</button>')
bodyA = """
<section class="page active" id="p1">
  <h2>Page 1 — Financial Overview (Past → Present)</h2>
  <div class="panel"><h3>Key figures</h3><div class="cards" id="kA1"></div></div>
  <div class="grid g3" style="margin-top:16px">
    <div class="panel"><h3>Operating margin vs 15% target</h3><div id="gA1"></div></div>
    <div class="panel" style="grid-column:span 2"><h3>Revenue by plant (click a bar to drill through)</h3><div id="bA1"></div><div class="drill-hint">⤵ click a bar → Page 3 drillthrough</div>
    <h3 style="margin-top:14px">Slicer — highlight plant</h3><div id="sA1"></div></div>
  </div>
</section>
<section class="page" id="p2">
  <h2>Page 2 — Logistics &amp; Operations</h2>
  <div class="panel"><h3>Key figures</h3><div class="cards" id="kA2"></div></div>
  <div class="grid g3" style="margin-top:16px">
    <div class="panel"><h3>OTIF vs 95% SLA target</h3><div id="gA2"></div></div>
    <div class="panel" style="grid-column:span 2"><h3>Avg lead time by material, days (click to drill)</h3><div id="bA2"></div><div class="drill-hint">⤵ click a bar → Page 3 drillthrough</div></div>
  </div>
</section>
<section class="page" id="drill">
  <h2>Page 3 — Drillthrough</h2>
  <button class="back" onclick="show(state.back, document.querySelector('nav button[data-page=\\'' + state.back + '\\']'))">← back</button>
  <div class="panel"><h3 id="drillTitle">Select a bar on page 1 or 2</h3><div id="drillChart"></div><div id="drillTable" style="margin-top:14px"></div></div>
</section>
"""
jsA = "const FY=" + j(fin_y) + ", FP=" + j(fin_p) + ", FM=" + j(fin_m) + ", LY=" + j(log_y) + ", LM=" + j(lt_m) + ", LR=" + j(log_raw) + ";\n" + f"""
const last = FY[FY.length-1], first = FY[0];
cards(document.getElementById('kA1'), [
  {{k:'Revenue {last_y} — EUR m', v:last.revenue_eur_m.toFixed(0), d:'5-yr CAGR ' + (((last.revenue_eur_m/first.revenue_eur_m)**0.25-1)*100).toFixed(1) + '%'}},
  {{k:'Operating profit {last_y} — EUR m', v:last.op_profit_eur_m.toFixed(0), d:'margin ' + last.op_margin_pct.toFixed(1) + '%'}},
  {{k:'Units sold {last_y}', v:last.units.toLocaleString(), d:'CAPEX ' + last.capex_eur_m.toFixed(0) + ' EUR m'}}]);
gauge(document.getElementById('gA1'), {{title:'Operating margin {last_y} %', value:last.op_margin_pct, target:15, max:40, unit:'%'}});
// conditional formatting: color by performance vs group average
const plants = [...new Set(FP.map(r=>r.plant))];
const rev26 = plants.map(p=>{{const r=FP.find(x=>x.plant===p && x.year==={last_y}); return r?r.revenue_eur_m:0;}});
const avgRev = rev26.reduce((a,b)=>a+b,0)/rev26.length;
const palCF = v => v >= avgRev*1.15 ? '#1F4E79' : v >= avgRev ? '#2E75B6' : v >= avgRev*0.8 ? '#C55A11' : '#7F7F7F';
bar(document.getElementById('bA1'), {{labels:plants, values:rev26, colors:rev26.map(palCF), title:'Revenue {last_y} by plant — EUR m (color = vs avg)', unit:' M€', onDrill: drillPlant}});
slicer(document.getElementById('sA1'), plants, name => {{ state.sel=name; }});
cards(document.getElementById('kA2'), [
  {{k:'OTIF {int(ly.year)}', v:'{ly.otif_pct:.1f}%', d:'SLA target 95%'}},
  {{k:'Avg lead time', v:'{ly.avg_lead_days:.1f} d', d:'variance {ly.lt_variance:+.1f} d'}},
  {{k:'Logistics spend {int(ly.year)}', v:'€{ly.spend_eur/1e6:.0f} M', d:'{int(ly.orders):,} orders'}}]);
gauge(document.getElementById('gA2'), {{title:'OTIF % {int(ly.year)}', value:{ly.otif_pct}, target:95, max:100, unit:'%'}});
bar(document.getElementById('bA2'), {{labels:LM.map(r=>r.material), values:LM.map(r=>r.avg_lead_days), title:'Avg lead time by material — days', unit:' d', onDrill: drillMaterial}});
function drillPlant(name) {{
  state.back='p1'; state.sel=name;
  const g = FM.filter(r=>r.plant===name);
  document.getElementById('drillTitle').textContent = 'Plant: ' + name + ' — monthly revenue 2022–2026';
  line(document.getElementById('drillChart'), [{{name:'Revenue EUR m', x:g.map(r=>r.month), values:g.map(r=>r.revenue_eur_m)}}], {{title:'Monthly revenue — ' + name}});
  table(document.getElementById('drillTable'), ['month','revenue_eur_m','op_profit_eur_m','margin'],
        g.map(r=>({{month:r.month, revenue_eur_m:r.revenue_eur_m.toFixed(1), op_profit_eur_m:r.op_profit_eur_m.toFixed(1), margin:((r.op_profit_eur_m/r.revenue_eur_m)*100).toFixed(1)+'%'}})) );
  show('drill', document.querySelector('nav button[data-page="drill"]'));
}}
function drillMaterial(name) {{
  state.back='p2'; state.sel=name;
  const g = LR.filter(r=>r.material===name);
  const byYear = {{}};
  g.forEach(r=>{{const y=r.order_date.slice(0,4); byYear[y]=byYear[y]||{{n:0,lt:0}}; byYear[y].n++; byYear[y].lt+=r.actual_lead_days;}});
  const years = Object.keys(byYear).sort();
  document.getElementById('drillTitle').textContent = 'Material: ' + name + ' — ' + g.length + ' orders';
  bar(document.getElementById('drillChart'), {{labels:years, values:years.map(y=>+(byYear[y].lt/byYear[y].n).toFixed(1)), title:'Avg lead time by year — ' + name, unit:' d'}});
  table(document.getElementById('drillTable'), ['year','orders','avg_lead_days'],
        years.map(y=>({{year:y, orders:byYear[y].n, avg_lead_days:(byYear[y].lt/byYear[y].n).toFixed(1)}})) );
  show('drill', document.querySelector('nav button[data-page="drill"]'));
}}
"""
(OUT / "projectA_dashboard.html").write_text(
    page("Project A — Financials & Logistics", "Automotive analytics · synthetic · 2022–2026", navA, bodyA, jsA))

# ============================= PROJECT B =============================
sal_y = pd.read_csv(PROC / "rpt_sales_yearly.csv")
sal_r = pd.read_csv(PROC / "rpt_sales_by_region.csv")
sal_m = pd.read_csv(ROOT / "data" / "parsed" / "regional_sales.csv")
rank = pd.read_csv(PROC / "rpt_region_rank.csv")
sent_y = pd.read_csv(PROC / "rpt_sentiment_by_year.csv")
sent_r = pd.read_csv(PROC / "rpt_sentiment_by_region.csv")
sent_o = pd.read_csv(PROC / "rpt_sentiment_overall.csv").iloc[0]
rev = pd.read_csv(ROOT / "data" / "parsed" / "reviews_scored.csv")

navB = ('<button data-page="p1" class="active" onclick="show(\'p1\',this)">1 · Sales Overview</button>'
        '<button data-page="p2" onclick="show(\'p2\',this)">2 · Customer Voice</button>'
        '<button data-page="drill" onclick="show(\'drill\',this)">3 · Drillthrough</button>')
bodyB = """
<section class="page active" id="p1">
  <h2>Page 1 — Regional Sales (Past → Present)</h2>
  <div class="panel"><h3>Key figures</h3><div class="cards" id="kB1"></div></div>
  <div class="grid g3" style="margin-top:16px">
    <div class="panel"><h3>Revenue growth vs +5% target</h3><div id="gB1"></div></div>
    <div class="panel" style="grid-column:span 2"><h3>Revenue by region — treemap, area = share (click to drill through)</h3><div id="bB1"></div><div class="drill-hint">⤵ click a tile → Page 3 drillthrough</div></div>
  </div>
</section>
<section class="page" id="p2">
  <h2>Page 2 — Customer Sentiment &amp; Rank Ribbon</h2>
  <div class="panel"><h3>Sentiment KPIs</h3><div class="cards" id="kB2"></div></div>
  <div class="grid g3" style="margin-top:16px">
    <div class="panel"><h3>Positive sentiment vs 60% target</h3><div id="gB2"></div></div>
    <div class="panel" style="grid-column:span 2"><h3>Region rank ribbon (color = rank, thickness = revenue; click to drill)</h3><div id="bB2"></div><div class="drill-hint">⤵ click a band → Page 3 drillthrough</div></div>
  </div>
  <div class="panel" style="margin-top:16px"><h3>Sentiment trend (line)</h3><div id="lB2"></div></div>
</section>
<section class="page" id="drill">
  <h2>Page 3 — Drillthrough</h2>
  <button class="back" onclick="show(state.back, document.querySelector('nav button[data-page=\\'' + state.back + '\\']'))">← back</button>
  <div class="panel"><h3 id="drillTitle">Select a bar on page 1 or 2</h3><div id="drillChart"></div><div id="drillTable" style="margin-top:14px"></div></div>
</section>
"""
yoy_d = ('yoy %+.1f%%' % sal_y.iloc[-1].yoy_growth_pct) if not pd.isna(sal_y.iloc[-1].yoy_growth_pct) else 'yoy n/a'
jsB = "const SY=" + j(sal_y) + ", SR=" + j(sal_r) + ", SM=" + j(sal_m) + ", SENR=" + j(sent_r) + ", REV=" + j(rev) + ", RK=" + j(rank) + ", SY2=" + j(sent_y) + ";\n" + f"""
const last = SY[SY.length-1];
cards(document.getElementById('kB1'), [
  {{k:'Revenue {int(sal_y.iloc[-1].year)} — EUR m', v:'{sal_y.iloc[-1].revenue_eur_m:.0f}', d:'{yoy_d}'}},
  {{k:'Units {int(sal_y.iloc[-1].year)}', v:'{int(sal_y.iloc[-1].units):,}', d:'avg price €{sal_y.iloc[-1].avg_asp_eur:,.0f}'}},
  {{k:'Regions covered', v:6, d:'5-year window 2022–2026'}}]);
gauge(document.getElementById('gB1'), {{title:'YoY revenue growth {int(sal_y.iloc[-1].year)} %', value:{0 if pd.isna(sal_y.iloc[-1].yoy_growth_pct) else float(sal_y.iloc[-1].yoy_growth_pct)}, target:5, max:15, unit:'%'}});
const regions = [...new Set(SR.map(r=>r.region))];
const revR = regions.map(r=>{{const x=SR.find(q=>q.region===r && q.year==={int(sal_y.iloc[-1].year)}); return x?x.revenue_eur_m:0;}});
treemap(document.getElementById('bB1'), {{labels:regions, values:revR, title:'Revenue {int(sal_y.iloc[-1].year)} by region — treemap (EUR m, share %)', unit:' M€', onDrill: drillRegion}});
cards(document.getElementById('kB2'), [
  {{k:'Positive sentiment', v:'{sent_o.pct_positive}%', d:'{int(sent_o.reviews)} reviews'}},
  {{k:'Avg rating', v:'{sent_o.avg_rating} / 5', d:'score {sent_o.avg_sentiment_score}'}},
  {{k:'Negative share', v:'{sent_o.pct_negative}%', d:'watch regions below 40% positive'}}]);
gauge(document.getElementById('gB2'), {{title:'Positive sentiment %', value:{sent_o.pct_positive}, target:60, max:100, unit:'%'}});
window._ribbonDrill = drillRegion;
ribbon(document.getElementById('bB2'), RK, [...new Set(RK.map(r=>r.year))].sort());
line(document.getElementById('lB2'), [{{name:'% positive', x:SY2.map(r=>r.year), values:SY2.map(r=>r.pct_positive)}}], {{title:'Positive sentiment trend by year — %'}});
function drillRegion(name) {{
  state.back='p1'; state.sel=name;
  const g = SM.filter(r=>r.region===name);
  document.getElementById('drillTitle').textContent = 'Region: ' + name + ' — monthly revenue';
  line(document.getElementById('drillChart'), [{{name:'Revenue EUR m', x:g.map(r=>r.month), values:g.map(r=>r.revenue_eur_m)}}], {{title:'Monthly revenue — ' + name}});
  const byYear = {{}};
  g.forEach(r=>{{const y=r.month.slice(0,4); byYear[y]=byYear[y]||{{u:0,rev:0}}; byYear[y].u+=r.units; byYear[y].rev+=r.revenue_eur_m;}});
  const years = Object.keys(byYear).sort();
  table(document.getElementById('drillTable'), ['year','units','revenue_eur_m'],
        years.map(y=>({{year:y, units:byYear[y].u, revenue_eur_m:byYear[y].rev.toFixed(1)}})) );
  show('drill', document.querySelector('nav button[data-page="drill"]'));
}}
function drillSent(name) {{
  state.back='p2'; state.sel=name;
  const g = REV.filter(r=>r.region===name);
  const byYear = {{}};
  g.forEach(r=>{{const y=r.review_date.slice(0,4); byYear[y]=byYear[y]||{{n:0,pos:0,neg:0,rat:0}}; byYear[y].n++; byYear[y].rat+=r.rating; if(r.sentiment==='Positive')byYear[y].pos++; if(r.sentiment==='Negative')byYear[y].neg++;}});
  const years = Object.keys(byYear).sort();
  document.getElementById('drillTitle').textContent = 'Region: ' + name + ' — ' + g.length + ' reviews';
  bar(document.getElementById('drillChart'), {{labels:years, values:years.map(y=>+(100*byYear[y].pos/byYear[y].n).toFixed(1)), title:'% positive by year — ' + name, unit:'%'}});
  table(document.getElementById('drillTable'), ['year','reviews','avg_rating','pct_positive','pct_negative'],
        years.map(y=>({{year:y, reviews:byYear[y].n, avg_rating:(byYear[y].rat/byYear[y].n).toFixed(2), pct_positive:(100*byYear[y].pos/byYear[y].n).toFixed(1)+'%', pct_negative:(100*byYear[y].neg/byYear[y].n).toFixed(1)+'%'}})) );
  show('drill', document.querySelector('nav button[data-page="drill"]'));
}}
"""
(OUT / "projectB_dashboard.html").write_text(
    page("Project B — Regional Sales & Sentiment", "Automotive analytics · synthetic · 2022–2026", navB, bodyB, jsB))
print("wrote", [p.name for p in OUT.glob("project*_dashboard.html")])
