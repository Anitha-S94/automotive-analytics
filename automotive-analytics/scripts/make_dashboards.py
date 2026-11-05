"""Accessible HTML dashboards for the two automotive projects.
Design rules from the brief: high contrast (no red/green-only cues), body >=14pt,
callouts >=24pt, ample whitespace, Past->Present->Future narrative arc.
Outputs: powerbi/projectA_dashboard.html, projectB_dashboard.html
"""
import json
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
OUT = ROOT / "powerbi"

JS = r"""
function bar(el, o) {
  const W = 920, H = 340, m = {l: 60, r: 20, t: 40, b: 70};
  const max = Math.max(...o.values) * 1.15;
  const bw = (W - m.l - m.r) / o.values.length;
  let s = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="${o.title}">`;
  s += `<text x="${m.l}" y="24" font-size="20" font-weight="700" fill="#111">${o.title}</text>`;
  for (let g = 0; g <= 4; g++) {
    const y = m.t + (H - m.t - m.b) * (1 - g / 4), v = max * g / 4;
    s += `<line x1="${m.l}" y1="${y}" x2="${W - m.r}" y2="${y}" stroke="#bbb" stroke-width="1"/>
          <text x="${m.l - 8}" y="${y + 5}" font-size="13" text-anchor="end" fill="#333">${v.toFixed(0)}</text>`;
  }
  o.values.forEach((v, i) => {
    const h = (H - m.t - m.b) * v / max, x = m.l + i * bw + bw * 0.15, w = bw * 0.7;
    s += `<rect x="${x}" y="${m.t + (H - m.t - m.b) - h}" width="${w}" height="${h}" fill="${o.colors ? o.colors[i] : '#1F4E79'}">
            <title>${o.labels[i]}: ${v.toFixed(1)}${o.unit || ''}</title></rect>`;
    s += `<text x="${x + w / 2}" y="${H - m.b + 20}" font-size="14" text-anchor="middle" fill="#111">${o.labels[i]}</text>`;
    s += `<text x="${x + w / 2}" y="${m.t + (H - m.t - m.b) - h - 6}" font-size="14" font-weight="600" text-anchor="middle" fill="#111">${v.toFixed(1)}</text>`;
  });
  const out = s + "</svg>"; if (el) el.innerHTML = out; return out;
}
function line(el, series, o) {
  const W = 920, H = 340, m = {l: 60, r: 20, t: 40, b: 50};
  const allV = series.flatMap(s => s.values);
  const max = Math.max(...allV) * 1.1, min = Math.min(...allV) * 0.9;
  const X = i => m.l + (W - m.l - m.r) * i / (series[0].x.length - 1);
  const Y = v => m.t + (H - m.t - m.b) * (1 - (v - min) / (max - min));
  let s = `<svg viewBox="0 0 ${W} ${H}" width="100%" role="img" aria-label="${o.title}">`;
  s += `<text x="${m.l}" y="24" font-size="20" font-weight="700" fill="#111">${o.title}</text>`;
  for (let g = 0; g <= 4; g++) {
    const y = m.t + (H - m.t - m.b) * (1 - g / 4), v = min + (max - min) * g / 4;
    s += `<line x1="${m.l}" y1="${y}" x2="${W - m.r}" y2="${y}" stroke="#bbb"/>
          <text x="${m.l - 8}" y="${y + 5}" font-size="13" text-anchor="end" fill="#333">${v.toFixed(0)}</text>`;
  }
  const pal = ['#1F4E79', '#C55A11', '#2E75B6', '#7F7F7F', '#BF8F00', '#548235'];
  series.forEach((sr, k) => {
    const pts = sr.x.map((_, i) => `${X(i)},${Y(sr.values[i])}`).join(' ');
    s += `<polyline points="${pts}" fill="none" stroke="${pal[k % 6]}" stroke-width="3"><title>${sr.name}</title></polyline>`;
    s += `<circle cx="${X(sr.x.length - 1)}" cy="${Y(sr.values[sr.values.length - 1])}" r="5" fill="${pal[k % 6]}"/>`;
    s += `<text x="${W - m.r}" y="${40 + k * 22}" font-size="14" text-anchor="end" fill="${pal[k % 6]}" font-weight="600">${sr.name}</text>`;
  });
  series[0].x.forEach((t, i) => { if (i % Math.ceil(series[0].x.length / 8) === 0)
    s += `<text x="${X(i)}" y="${H - m.b + 22}" font-size="13" text-anchor="middle" fill="#111">${t}</text>`; });
  const out = s + "</svg>"; if (el) el.innerHTML = out; return out;
}
function ribbon(el, data, years) {
  // simple rank-shift table with arrows (accessible alternative to ribbon chart)
  const regions = [...new Set(data.map(d => d.region))];
  let s = `<table style="border-collapse:collapse;font-size:15px;width:100%" role="table" aria-label="Revenue rank by region and year">`;
  s += '<tr><th style="text-align:left;padding:8px;border-bottom:3px solid #111">Region</th>' +
       years.map(y => `<th style="padding:8px;border-bottom:3px solid #111;text-align:right">${y}</th>`).join('') + '</tr>';
  regions.forEach(r => {
    s += `<tr><td style="padding:8px;border-bottom:1px solid #ddd;font-weight:600">${r}</td>`;
    years.forEach(y => {
      const d = data.find(d => d.region === r && d.year === y);
      const prev = data.find(d => d.region === r && d.year === y - 1);
      let arrow = '';
      if (prev) { const diff = prev.revenue_rank - d.revenue_rank; arrow = diff > 0 ? ' ▲' : diff < 0 ? ' ▼' : ' ='; }
      s += `<td style="padding:8px;border-bottom:1px solid #ddd;text-align:right">#${d.revenue_rank} (${d.revenue_eur_m.toFixed(0)} M€)${arrow}</td>`;
    });
    s += '</tr>';
  });
  s += '</table>';
  const out = s; if (el) el.innerHTML = out; return out;
}
function cards(el, items) {
  const out = items.map(i => `<div style="flex:1;min-width:200px;background:#F2F6FB;border:3px solid #1F4E79;border-radius:10px;padding:16px">
    <div style="font-size:15px;color:#333">${i.k}</div><div style="font-size:30px;font-weight:800;color:#1F4E79">${i.v}</div></div>`).join('');
  if (el) el.innerHTML = out; return out;
}
function table(el, cols, rows) {
  let s = `<table style="border-collapse:collapse;font-size:15px;width:100%"><thead><tr>` +
    cols.map(c => `<th style="border-bottom:3px solid #111;padding:8px;text-align:left">${c}</th>`).join('') + `</tr></thead><tbody>` +
    rows.map(r => '<tr>' + cols.map(c => `<td style="border-bottom:1px solid #ddd;padding:8px">${r[c] ?? ''}</td>`).join('') + '</tr>').join('') + '</tbody></table>';
  if (el) el.innerHTML = s; return s;
}
"""

CSS = """body{font-family:'Segoe UI',Arial,sans-serif;font-size:16px;line-height:1.5;margin:24px;color:#111;background:#fff;max-width:1000px}
h1{font-size:28px} h2{font-size:22px;margin:28px 0 8px;color:#1F4E79;border-bottom:2px solid #1F4E79;padding-bottom:4px}
.row{display:flex;gap:14px;flex-wrap:wrap} .panel{border:1px solid #999;border-radius:8px;padding:14px;margin-top:12px}
.note{font-size:14px;color:#444} .callout{font-size:26px;font-weight:800;color:#1F4E79}"""

def page(title, body, js):
    return f'<!doctype html><html lang="en"><head><meta charset="utf-8"><title>{title}</title><style>{CSS}</style></head><body><h1>{title}</h1><div class="note">Synthetic data · 5-year window 2022–2026 · accessible design: high contrast, ≥14pt body, ≥24pt callouts</div>{body}<script>{JS}</script><script>{js}</script></body></html>'

def j(df):
    df = df.copy()
    for c in df.columns:
        if str(df[c].dtype).startswith("datetime64"):
            df[c] = df[c].astype(str)
    return json.dumps(df.to_dict("records"))

# ---------- Project A ----------
fin_y = pd.read_csv(PROC / "rpt_fin_yearly.csv")
growth = pd.read_csv(PROC / "rpt_growth.csv")
fin_p = pd.read_csv(PROC / "rpt_fin_by_plant.csv")
log_y = pd.read_csv(PROC / "rpt_logistics_yearly.csv")
lt_m = pd.read_csv(PROC / "rpt_leadtime_by_material.csv")
fc = pd.read_csv(PROC / "rpt_forecast_2027.csv")
down = pd.read_csv(PROC / "rpt_downtime.csv")
dq = pd.read_csv(PROC / "rpt_data_quality.csv")

last = fin_y.iloc[-1]; first = fin_y.iloc[0]
bodyA = """
<h2>Past — 5-year financial performance</h2><div class="row" id="kA"></div>
<div class="panel" id="c_rev"></div>
<div class="panel" id="c_margin"></div>
<div class="row"><div class="panel" style="flex:1" id="c_capex"></div><div class="panel" style="flex:1" id="c_lt"></div></div>
<h2>Present — logistics & operations</h2>
<div class="panel" id="c_otif"></div>
<div class="panel" id="t_lt"></div>
<div class="panel" id="t_down"></div>
<h2>Future — 2027 forecast vs +8% target</h2>
<div class="panel" id="c_fc"></div>
<div class="panel" id="t_dq"></div>
"""
jsA = f"""
const FY={j(fin_y)}, GR={j(growth)}, FP={j(fin_p)}, LY={j(log_y)}, LM={j(lt_m)}, FC={j(fc)}, DOWN={j(down)}, DQ={j(dq)};
cards(document.getElementById('kA'), [
  {{k:'Revenue {int(fin_y.iloc[-1].year)} (EUR m)', v:'{fin_y.iloc[-1].revenue_eur_m:.0f}'}},
  {{k:'5-yr revenue CAGR', v:'{(( (fin_y.iloc[-1].revenue_eur_m/fin_y.iloc[0].revenue_eur_m) ** 0.25 - 1)*100):.1f}%'}},
  {{k:'Op margin {int(fin_y.iloc[-1].year)}', v:'{fin_y.iloc[-1].op_margin_pct:.1f}%'}},
  {{k:'OTIF {int(log_y.iloc[-1].year)}', v:'{log_y.iloc[-1].otif_pct:.1f}%'}}]);
document.getElementById('c_rev').innerHTML = line(null, [{{name:'Revenue EUR m', x:FY.map(r=>r.year), values:FY.map(r=>r.revenue_eur_m)}}], {{title:'Revenue by year — EUR millions'}});
document.getElementById('c_margin').innerHTML = line(null, [
  {{name:'Gross margin %', x:FY.map(r=>r.year), values:FY.map(r=>r.gross_margin_pct)}},
  {{name:'Operating margin %', x:FY.map(r=>r.year), values:FY.map(r=>r.op_margin_pct)}}], {{title:'Margins by year — %'}});
document.getElementById('c_capex').innerHTML = bar(null, {{labels:FP.filter(r=>r.year===2026).map(r=>r.plant),
  values:FP.filter(r=>r.year===2026).map(r=>r.capex_eur_m), title:'CAPEX 2026 by plant — EUR m'}});
document.getElementById('c_lt').innerHTML = bar(null, {{labels:LY.map(r=>r.year),
  values:LY.map(r=>r.avg_lead_days), title:'Avg lead time by year — days'}});
document.getElementById('c_otif').innerHTML = bar(null, {{labels:LY.map(r=>r.year),
  values:LY.map(r=>r.otif_pct), title:'OTIF % by year', unit:'%'}});
table(document.getElementById('t_lt'), ['material','orders','avg_lead_days','otif_pct','spend_eur'], LM);
table(document.getElementById('t_down'), ['plant','events','avg_downtime_min','units'], DOWN);
const fcP = FC.filter(r=>r.plant==='GROUP TARGET').map(r=>r.forecast_revenue_eur_m);
const fcS = {{}};
FC.filter(r=>r.plant!=='GROUP TARGET').forEach(r=>{{ fcS[r.plant] = fcS[r.plant] || []; fcS[r.plant].push(r.forecast_revenue_eur_m); }});
const fcKeys = Object.keys(fcS);
const fcSum = fcS[fcKeys[0]].map((_, i) => fcKeys.reduce((a, k) => a + fcS[k][i], 0));
const months = FC.filter(r=>r.plant==='GROUP TARGET').map(r=>r.forecast_month);
document.getElementById('c_fc').innerHTML = line(null,
  [{{name:'2027 forecast (sum of plants)', x:months, values:fcSum}},
   {{name:'GROUP TARGET +8% YoY', x:months, values:fcP}}], {{title:'2027 monthly revenue forecast vs target — EUR m'}});
table(document.getElementById('t_dq'), ['check','violations'], DQ);
"""
(OUT / "projectA_dashboard.html").write_text(page("Project A — Financials & Logistics (Automotive Analytics)", bodyA, jsA))

# ---------- Project B ----------
sal_y = pd.read_csv(PROC / "rpt_sales_yearly.csv")
rank = pd.read_csv(PROC / "rpt_region_rank.csv")
tree = pd.read_csv(PROC / "rpt_treemap_region.csv")
sent_r = pd.read_csv(PROC / "rpt_sentiment_by_region.csv")
sent_o = pd.read_csv(PROC / "rpt_sentiment_overall.csv").iloc[0]
sent_y = pd.read_csv(PROC / "rpt_sentiment_by_year.csv")

bodyB = """
<h2>Past — 5-year regional sales</h2><div class="row" id="kB"></div>
<div class="panel" id="c_sal"></div>
<h2>Present — where revenue sits now &amp; who leads</h2>
<div class="panel" id="c_tree"></div>
<div class="panel" id="t_rank"></div>
<h2>Customer voice — sentiment KPIs</h2>
<div class="panel" id="c_sent"></div>
<div class="panel" id="t_sent"></div>
"""
jsB = f"""
const SY={j(sal_y)}, RK={j(rank)}, TR={j(tree)}, SR={j(sent_r)}, SY2={j(sent_y)};
cards(document.getElementById('kB'), [
  {{k:'Revenue {int(sal_y.iloc[-1].year)} (EUR m)', v:'{sal_y.iloc[-1].revenue_eur_m:.0f}'}},
  {{k:'Units {int(sal_y.iloc[-1].year)}', v:'{int(sal_y.iloc[-1].units):,}'}},
  {{k:'Sentiment positive', v:'{sent_o.pct_positive}%'}},
  {{k:'Avg rating', v:'{sent_o.avg_rating} / 5'}}]);
document.getElementById('c_sal').innerHTML = line(null, [{{name:'Revenue EUR m', x:SY.map(r=>r.year), values:SY.map(r=>r.revenue_eur_m)}}], {{title:'Revenue by year — EUR m'}});
document.getElementById('c_tree').innerHTML = bar(null, {{labels:TR.map(r=>r.region),
  values:TR.map(r=>r.revenue_eur_m), title:'Revenue by region, latest year — EUR m (treemap data)'}});
ribbon(document.getElementById('t_rank'), RK, [...new Set(RK.map(r=>r.year))].sort());
document.getElementById('c_sent').innerHTML = line(null, [{{name:'% positive', x:SY2.map(r=>r.year), values:SY2.map(r=>r.pct_positive)}}], {{title:'Positive sentiment share by year — %'}});
table(document.getElementById('t_sent'), ['region','reviews','avg_rating','pct_positive','avg_sentiment_score'], SR);
"""
(OUT / "projectB_dashboard.html").write_text(page("Project B — Regional Sales & Customer Sentiment (Automotive Analytics)", bodyB, jsB))
print("wrote", [p.name for p in OUT.glob("project*_dashboard.html")])
