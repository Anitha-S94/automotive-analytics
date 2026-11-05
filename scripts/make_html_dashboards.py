"""Generate self-contained interactive HTML dashboards (no external deps/CDN)
from data/processed/*.parquet -> powerbi/*_dashboard.html
"""
import json
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
OUT = ROOT / "powerbi"

CHART_JS = r"""
function bar(el, data, opts) {
  const {labels, values, colors, title, ylab} = opts;
  const W = (el && el.clientWidth) || 900, H = 320, m = {l: 46, r: 12, t: 30, b: 60};
  const max = Math.max(...values) * 1.15, min = 0;
  const bw = (W - m.l - m.r) / values.length;
  let s = `<svg viewBox="0 0 ${W} ${H}" width="100%" style="max-height:340px">`;
  s += `<text x="${m.l}" y="18" font-size="13" font-weight="600">${title||''}</text>`;
  for (let g = 0; g <= 4; g++) {
    const y = m.t + (H - m.t - m.b) * (1 - g / 4);
    const v = min + (max - min) * g / 4;
    s += `<line x1="${m.l}" y1="${y}" x2="${W - m.r}" y2="${y}" stroke="#ddd"/>
          <text x="${m.l - 6}" y="${y + 4}" font-size="10" text-anchor="end">${v.toFixed(0)}</text>`;
  }
  values.forEach((v, i) => {
    const h = (H - m.t - m.b) * (v - min) / (max - min);
    const x = m.l + i * bw + bw * 0.12, w = bw * 0.76;
    s += `<rect x="${x}" y="${m.t + (H - m.t - m.b) - h}" width="${w}" height="${h}"
            fill="${colors ? colors[i] : '#1f6fb2'}"><title>${labels[i]}: ${v.toFixed(1)}${ylab||''}</title></rect>`;
    s += `<text x="${x + w / 2}" y="${H - m.b + 14}" font-size="9" text-anchor="middle"
            transform="rotate(-32 ${x + w / 2} ${H - m.b + 14})">${labels[i]}</text>`;
    s += `<text x="${x + w / 2}" y="${m.t + (H - m.t - m.b) - h - 4}" font-size="9" text-anchor="middle">${v.toFixed(1)}</text>`;
  });
  const out = s + "</svg>";
  if (el) el.innerHTML = out;
  return out;
}
function line(el, series, opts) {
  const {title} = opts; const W = (el && el.clientWidth) || 900, H = 300, m = {l: 46, r: 12, t: 30, b: 34};
  const allV = series.flatMap(s => s.values);
  const max = Math.max(...allV) * 1.1, min = Math.min(0, ...allV);
  const X = i => m.l + (W - m.l - m.r) * i / (series[0].x.length - 1);
  const Y = v => m.t + (H - m.t - m.b) * (1 - (v - min) / (max - min));
  let s = `<svg viewBox="0 0 ${W} ${H}" width="100%" style="max-height:320px">`;
  s += `<text x="${m.l}" y="18" font-size="13" font-weight="600">${title||''}</text>`;
  for (let g = 0; g <= 4; g++) {
    const y = m.t + (H - m.t - m.b) * (1 - g / 4), v = min + (max - min) * g / 4;
    s += `<line x1="${m.l}" y1="${y}" x2="${W - m.r}" y2="${y}" stroke="#ddd"/>
          <text x="${m.l - 6}" y="${y + 4}" font-size="10" text-anchor="end">${v.toFixed(0)}</text>`;
  }
  const pal = ['#1f6fb2', '#d9822b', '#c0392b', '#2e8b57', '#8e44ad', '#c9a227', '#16a085', '#e67e22'];
  series.forEach((sr, k) => {
    const pts = sr.x.map((_, i) => `${X(i)},${Y(sr.values[i])}`).join(' ');
    s += `<polyline points="${pts}" fill="none" stroke="${pal[k % 8]}" stroke-width="2"><title>${sr.name}</title></polyline>`;
    s += `<text x="${W - m.r - 4}" y="${20 + k * 14}" font-size="10" text-anchor="end" fill="${pal[k % 8]}">${sr.name}</text>`;
  });
  const ticks = sr0 => sr0.x.filter((_, i) => i % Math.ceil(sr0.x.length / 8) === 0);
  ticks(series[0]).forEach((t, i) => {
    const x = m.l + (W - m.l - m.r) * series[0].x.indexOf(t) / (series[0].x.length - 1);
    s += `<text x="${x}" y="${H - m.b + 16}" font-size="9" text-anchor="middle">${String(t).slice(0, 7)}</text>`;
  });
  const out = s + "</svg>";
  if (el) el.innerHTML = out;
  return out;
}
function table(el, cols, rows) {
  let s = `<table style="border-collapse:collapse;width:100%;font-size:12px"><thead><tr>` +
    cols.map(c => `<th style="border-bottom:2px solid #999;padding:4px 8px;text-align:left;cursor:pointer" data-c="${c}">${c} ⇅</th>`).join('') +
    `</tr></thead><tbody>`;
  rows.forEach(r => { s += '<tr>' + cols.map(c => `<td style="border-bottom:1px solid #eee;padding:3px 8px">${r[c] ?? ''}</td>`).join('') + '</tr>'; });
  s += '</tbody></table>';
  el.innerHTML = s;
  el.querySelectorAll('th').forEach(th => th.onclick = () => {
    const c = th.dataset.c, asc = th.dataset.dir !== '1';
    el.querySelectorAll('th').forEach(t => t.dataset.dir = '');
    th.dataset.dir = asc ? '1' : '0';
    rows.sort((a, b) => {
      const av = a[c], bv = b[c];
      const cmp = (typeof av === 'number' ? av - bv : String(av).localeCompare(String(bv)));
      return asc ? cmp : -cmp;
    });
    el.querySelector('tbody').innerHTML = rows.map(r =>
      '<tr>' + cols.map(cc => `<td style="border-bottom:1px solid #eee;padding:3px 8px">${r[cc] ?? ''}</td>`).join('') + '</tr>').join('');
  });
}
function cards(el, items) {
  el.innerHTML = items.map(i => `<div style="flex:1;min-width:150px;background:#f4f7fb;border:1px solid #d5e0ec;
    border-radius:8px;padding:12px 14px"><div style="font-size:11px;color:#556">${i.k}</div>
    <div style="font-size:22px;font-weight:700;color:#123">${i.v}</div></div>`).join('');
}
"""

def page(title, body, data_js):
    return f"""<!doctype html><html><head><meta charset="utf-8"><title>{title}</title>
<style>body{{font-family:Segoe UI,system-ui,sans-serif;margin:18px;color:#1a2733;background:#fff}}
h1{{font-size:20px}} h2{{font-size:15px;margin:18px 0 6px;color:#234}} .row{{display:flex;gap:10px;flex-wrap:wrap}}
.panel{{border:1px solid #d5e0ec;border-radius:8px;padding:10px;margin-top:10px}}
.note{{font-size:11px;color:#667}}</style></head><body>
<h1>{title}</h1><div class="note">Synthetic data · generated locally · mirrors the Power BI build spec in this repo</div>
{body}
<script>{CHART_JS}</script><script>{data_js}</script></body></html>"""

def df_json(df):
    df = df.copy()
    for c in df.columns:
        if str(df[c].dtype).startswith("datetime64"):
            df[c] = df[c].astype(str)
    return json.dumps(df.to_dict("records"))

# ---------------- ENERGY ----------------
pt = pd.read_parquet(PROC / "rpt_peak_to_avg.parquet")
season = pd.read_parquet(PROC / "rpt_season_profile.parquet")
hp = pd.read_parquet(PROC / "rpt_hourly_profile.parquet")
stress = pd.read_parquet(PROC / "rpt_stress_nodes.parquet")
monthly = pd.read_parquet(PROC / "rpt_monthly_stress.parquet")
buckets = pd.read_parquet(PROC / "rpt_util_buckets.parquet")

prio_color = {"CRITICAL - inspect connectors": "#c0392b", "HIGH - schedule visual inspection": "#d9822b",
              "MEDIUM - monitor": "#c9a227", "LOW": "#2e8b57"}
body = """
<h2>Executive overview</h2><div class="row" id="kpi1"></div>
<div class="row"><div class="panel" style="flex:1" id="c_par"></div>
<div class="panel" style="flex:1" id="c_max"></div></div>
<h2>Load &amp; utilization profiling</h2>
<div class="row"><div class="panel" style="flex:1" id="c_season"></div>
<div class="panel" style="flex:1" id="c_hourly"></div></div>
<div class="panel" id="c_buckets"></div>
<h2>Maintenance scheduling</h2>
<div class="panel" id="c_stress"></div>
<div class="panel" id="c_monthly"></div>
<div class="panel" id="t_stress"></div>
"""
js = f"""
const PT = {df_json(pt)}, SEASON = {df_json(season)}, HP = {df_json(hp)},
STRESS = {df_json(stress)}, MONTHLY = {df_json(monthly)}, BUCK = {df_json(buckets)};
cards(document.getElementById('kpi1'), [
  {{k:'Avg utilization (all cables)', v:(PT.reduce((a,r)=>a+r.avg_util_pct,0)/PT.length).toFixed(1)+'%'}} ,
  {{k:'Max peak-to-avg ratio', v:Math.max(...PT.map(r=>r.peak_to_avg_ratio)).toFixed(2)+'x'}},
  {{k:'Total overload hours', v:PT.reduce((a,r)=>a+r.overload_hours,0).toLocaleString()+' h'}},
  {{k:'Cables with overloads', v:PT.filter(r=>r.overload_hours>0).length+' / '+PT.length}},
]);
document.getElementById('c_par').innerHTML = bar(null, null, {{labels:PT.map(r=>r.cable_id),
  values:PT.map(r=>r.peak_to_avg_ratio), title:'Peak-to-average power ratio by export cable'}});
const sorted = [...PT].sort((a,b)=>b.peak_to_avg_ratio-a.peak_to_avg_ratio);
document.getElementById('c_par').innerHTML = bar(null, null, {{labels:sorted.map(r=>r.cable_id),
  values:sorted.map(r=>r.peak_to_avg_ratio), title:'Peak-to-average power ratio (PAR) by cable'}});
document.getElementById('c_max').innerHTML = bar(null, null, {{labels:PT.map(r=>r.cable_id),
  values:PT.map(r=>r.max_util_pct), title:'Max utilization vs rating (%)',
  colors:PT.map(r=>r.max_util_pct>100?'#c0392b':r.max_util_pct>90?'#d9822b':'#1f6fb2'), ylab:'%'}});
const sp = SEASON.filter(r=>['Winter','Summer'].includes(r.season));
const seasons = ['Winter','Spring','Summer','Autumn'];
document.getElementById('c_season').innerHTML = bar(null, null, {{labels:seasons,
  values:seasons.map(s=>{{const g=SEASON.filter(r=>r.season===s); return g.reduce((a,r)=>a+r.peak_util,0)/g.length;}}),
  title:'Average seasonal peak utilization across cables (%)', ylab:'%'}});
const hot = HP.filter(r=>['OSS-FR-1-EXP-320kV','OSS-NorthSea-3-EXP-320kV','OSS-UK-1-EXP-320kV'].includes(r.cable_id));
const series = [...new Set(hot.map(r=>r.cable_id))].map(cid=>{{const g=hot.filter(r=>r.cable_id===cid).sort((a,b)=>a.hour_of_day-b.hour_of_day);
  return {{name:cid, x:g.map(r=>r.hour_of_day), values:g.map(r=>r.avg_util)}};}});
document.getElementById('c_hourly').innerHTML = line(null, series, {{title:'Intraday avg utilization — highest-stress cables'}});
document.getElementById('c_buckets').innerHTML = bar(null, null, {{labels:BUCK.map(r=>r.cable_id),
  values:BUCK.map(r=>r.gt100), title:'Overload hours (>100% of rating) per cable', colors:BUCK.map(()=>'#c0392b'), ylab:' h'}});
const srt = [...STRESS].sort((a,b)=>b.stress_index-a.stress_index);
document.getElementById('c_stress').innerHTML = bar(null, null, {{labels:srt.map(r=>r.cable_id),
  values:srt.map(r=>r.stress_index), title:'Maintenance stress index (high-load h + 3×overload h)',
  colors:srt.map(r=>({json.dumps(prio_color)})[r.maintenance_priority]||'#1f6fb2')}});
const mseries = [...new Set(MONTHLY.map(r=>r.cable_id))].slice(0,4).map(cid=>{{const g=MONTHLY.filter(r=>r.cable_id===cid);
  return {{name:cid, x:g.map(r=>r.month), values:g.map(r=>r.high_load_hours)}};}});
document.getElementById('c_monthly').innerHTML = line(null, mseries, {{title:'Monthly high-load hours (>90%) — first 4 cables'}});
table(document.getElementById('t_stress'),
  ['cable_id','location','voltage_kv','high_load_hours','overload_hours','stress_index','maintenance_priority'],
  STRESS.map(r=>({{...r, maintenance_priority:'<b style="color:'+( {json.dumps(prio_color)}[r.maintenance_priority]||'#333')+'">'+r.maintenance_priority+'</b>'}})));
"""
(OUT / "energy_dashboard.html").write_text(page("Offshore Grid Load & Maintenance — Energy & Supply Chain Analytics", body, js))

# ---------------- SUPPLY CHAIN ----------------
ov = pd.read_parquet(PROC / "rpt_otif_overview.parquet").iloc[0]
sup = pd.read_parquet(PROC / "rpt_otif_by_supplier.parquet")
rt = pd.read_parquet(PROC / "rpt_route_bottlenecks.parquet")
dr = pd.read_parquet(PROC / "rpt_delay_reasons.parquet")
sc = pd.read_parquet(PROC / "rpt_scenario.parquet")
screg = pd.read_parquet(PROC / "rpt_scenario_by_region.parquet")
pr = pd.read_parquet(PROC / "rpt_price_trend.parquet")
risk = pd.read_parquet(PROC / "rpt_stockout_risk.parquet")
reorder = pd.read_parquet(PROC / "rpt_reorder_points.parquet")
dq = pd.read_parquet(PROC / "rpt_data_quality.parquet")
alerts = json.loads((ROOT / "alerts.json").read_text()) if (ROOT / "alerts.json").exists() else {"alerts": [], "n_critical": 0, "n_warning": 0}

body = """
<h2>Executive overview</h2><div class="row" id="kpi2"></div>
<div class="panel" id="c_alerts"></div>
<div class="row"><div class="panel" style="flex:1" id="c_otif_reg"></div>
<div class="panel" style="flex:1" id="c_price"></div></div>
<h2>Supplier &amp; SLA performance</h2>
<div class="row"><div class="panel" style="flex:1" id="c_sup"></div>
<div class="panel" style="flex:1" id="c_delay"></div></div>
<div class="panel" id="t_risk"></div>
<h2>Logistics network &amp; bottlenecks</h2>
<div class="panel" id="c_route"></div>
<h2>Reorder points &amp; raw-material inventory (reorder cycles)</h2>
<div class="panel" id="t_reorder"></div>
<h2>Data quality gates (ETL)</h2>
<div class="panel" id="t_dq"></div>
<h2>Scenario: lead time +10% / +20%</h2>
<div class="row"><div class="panel" style="flex:1" id="c_scen"></div>
<div class="panel" style="flex:1" id="c_screg"></div></div>
"""
js = f"""
const SUP={df_json(sup)}, RT={df_json(rt)}, DR={df_json(dr)}, SC={df_json(sc)},
SCREG={df_json(screg)}, PR={df_json(pr)}, RISK={df_json(risk)},
REORDER={df_json(reorder)}, DQ={df_json(dq)}, ALERTS={json.dumps(alerts['alerts'])};
cards(document.getElementById('kpi2'), [
  {{k:'OTIF', v:{ov.otif_pct}+'%'}}, {{k:'Late orders', v:{ov.late_pct}+'%'}},
  {{k:'Avg lead-time variance', v:'+'+{ov.avg_lt_variance_days}+' d'}},
  {{k:'Total spend', v:'€'+( {ov.total_spend_eur}/1e6).toFixed(1)+'M'}},
  {{k:'Active alerts', v:ALERTS.length+' ('+{alerts['n_critical']}+' CRITICAL)'}},
]);
document.getElementById('c_alerts').innerHTML = '<b>Automated refresh alerts (refresh_and_alert.py)</b><br>' +
  (ALERTS.length ? '<ul style="font-size:12px;max-height:140px;overflow:auto">' +
   ALERTS.slice(0,15).map(a=>'<li style="color:' + (a.severity==='CRITICAL'?'#c0392b':'#d9822b') + '">' +
     '<b>'+a.severity+'</b> '+a.rule+' — '+(a.cable||a.supplier||a.material||'')+' '+a.detail+'</li>').join('') + '</ul>'
   : 'no alerts');
const regs = [...new Set(SUP.map(r=>r.region))];
document.getElementById('c_otif_reg').innerHTML = bar(null,null,{{labels:regs,
  values:regs.map(g=>{{const x=SUP.filter(r=>r.region===g); return 100*x.reduce((a,r)=>a+r.otif_pct,0)/x.length;}}),
  title:'OTIF % by region', ylab:'%'}});
document.getElementById('c_price').innerHTML = line(null, [
  {{name:'Copper USD/t', x:PR.map(r=>r.month), values:PR.map(r=>r.avg_copper)}},
  {{name:'Aluminum USD/t (÷3.4)', x:PR.map(r=>r.month), values:PR.map(r=>r.avg_aluminum/3.4)}}],
  {{title:'Metal price index (aluminum scaled for display)'}});
const worst = [...SUP].sort((a,b)=>a.otif_pct-b.otif_pct).slice(0,12);
document.getElementById('c_sup').innerHTML = bar(null,null,{{labels:worst.map(r=>r.supplier_id),
  values:worst.map(r=>r.otif_pct), title:'12 worst suppliers by OTIF % (SLA 95%)',
  colors:worst.map(r=>r.otif_pct<90?'#c0392b':r.otif_pct<95?'#d9822b':'#2e8b57'), ylab:'%'}});
document.getElementById('c_delay').innerHTML = bar(null,null,{{labels:DR.map(r=>r.delay_reason),
  values:DR.map(r=>r.share_pct), title:'Delay reason share of all orders (%)', ylab:'%'}});
const lanes = [...RT].sort((a,b)=>a.otif_pct-b.otif_pct).slice(0,10);
document.getElementById('c_route').innerHTML = bar(null,null,{{labels:lanes.map(r=>r.origin_port+'→'+r.dest_port),
  values:lanes.map(r=>r.otif_pct), title:'10 bottleneck lanes by OTIF %',
  colors:lanes.map(r=>r.otif_pct<85?'#c0392b':'#d9822b'), ylab:'%'}});
document.getElementById('c_scen').innerHTML = bar(null,null,{{labels:SC.map(r=>r.scenario),
  values:SC.map(r=>r.annual_holding_cost_impact_eur/1e6), title:'Holding-cost impact (€M/yr)',
  colors:['#1f6fb2','#d9822b','#c0392b'], ylab:'M€'}});
document.getElementById('c_screg').innerHTML = bar(null,null,{{labels:SCREG.map(r=>r.region),
  values:SCREG.map(r=>r.impact_20pct_eur/1e3), title:'Impact of +20% lead time by region (€k/yr)',
  colors:SCREG.map(()=>'#c0392b'), ylab:'k€'}});
table(document.getElementById('t_risk'),
  ['supplier_id','region','material','orders','short_shipments','severe_delays','stockout_risk'],
  [...RISK].sort((a,b)=>b.short_shipments-a.short_shipments).slice(0,15));
table(document.getElementById('t_reorder'),
  ['material','avg_daily_demand_t','avg_lead_days','p95_lead_days','safety_stock_t','reorder_point_t','annual_spend_m_eur','reorder_alert'],
  REORDER);
table(document.getElementById('t_dq'), ['check','violations'], DQ);
"""
(OUT / "supplychain_dashboard.html").write_text(page("Global Supply Chain & Raw Materials — Energy & Supply Chain Analytics", body, js))
print("wrote", [p.name for p in OUT.glob("*_dashboard.html")])
