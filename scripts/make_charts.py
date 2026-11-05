"""Render static dashboard panels (PNG) for both use cases.
Outputs to analysis/ — these mirror the Power BI pages and go into the README.
"""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
OUT = ROOT / "analysis"
OUT.mkdir(exist_ok=True)
plt.rcParams.update({"figure.dpi": 130, "axes.grid": True, "grid.alpha": 0.3,
                     "axes.titlesize": 12, "font.size": 9})
C = {"main": "#1f6fb2", "warn": "#d9822b", "bad": "#c0392b", "ok": "#2e8b57"}

# ---------- ENERGY ----------
pt = pd.read_parquet(PROC / "rpt_peak_to_avg.parquet")
fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
pt.sort_values("peak_to_avg_ratio").plot.barh(x="cable_id", y="peak_to_avg_ratio",
    color=C["main"], ax=ax[0], legend=False)
ax[0].set_title("Peak-to-average power ratio by export cable")
ax[0].set_xlabel("PAR (x)")
ax[1].bar(pt.cable_id, pt.max_util_pct, color=[C["bad"] if v > 100 else C["warn"] if v > 90 else C["main"] for v in pt.max_util_pct])
ax[1].axhline(100, color=C["bad"], ls="--", lw=1, label="rated capacity")
ax[1].axhline(90, color=C["warn"], ls="--", lw=1, label="90% stress threshold")
ax[1].set_title("Max utilization vs cable rating"); ax[1].legend(fontsize=8)
plt.xticks(rotation=45, ha="right"); fig.tight_layout()
fig.savefig(OUT / "energy_peak_ratios.png"); plt.close(fig)

season = pd.read_parquet(PROC / "rpt_season_profile.parquet")
piv = season.pivot(index="cable_id", columns="season", values="peak_util")
fig, ax = plt.subplots(1, 2, figsize=(12, 4.2))
piv[["Winter", "Spring", "Summer", "Autumn"]].plot(kind="bar", ax=ax[0])
ax[0].set_title("Seasonal peak utilization by cable"); ax[0].tick_params(axis="x", rotation=45)
hp = pd.read_parquet(PROC / "rpt_hourly_profile.parquet")
hp2 = hp[hp.cable_id.isin(["OSS-FR-1-EXP-320kV", "OSS-NorthSea-3-EXP-320kV", "OSS-UK-1-EXP-320kV"])]
for cid, g in hp2.groupby("cable_id"):
    ax[1].plot(g.hour_of_day, g.avg_util, marker="o", ms=3, label=cid)
ax[1].set_title("Average intraday utilization (highest-stress cables)")
ax[1].set_xlabel("hour"); ax[1].legend(fontsize=7)
fig.tight_layout(); fig.savefig(OUT / "energy_seasonal_daily.png"); plt.close(fig)

stress = pd.read_parquet(PROC / "rpt_stress_nodes.parquet")
fig, ax = plt.subplots(figsize=(10, 4))
colors = {"CRITICAL - inspect connectors": C["bad"], "HIGH - schedule visual inspection": C["warn"],
          "MEDIUM - monitor": "#c9a227", "LOW": C["ok"]}
ax.barh(stress.cable_id, stress.stress_index,
        color=[colors[p] for p in stress.maintenance_priority])
ax.set_title("Maintenance stress index (high-load hours, overloads weighted 3x)")
for i, (p, h) in enumerate(zip(stress.maintenance_priority, stress.high_load_hours)):
    ax.text(stress.stress_index.iloc[i] + 5, i, f"{p} ({h} h >90%)", va="center", fontsize=8)
ax.set_xlim(0, stress.stress_index.max() * 1.65)
fig.tight_layout(); fig.savefig(OUT / "energy_maintenance_priority.png"); plt.close(fig)

# ---------- SUPPLY CHAIN ----------
otif = pd.read_parquet(PROC / "rpt_otif_by_supplier.parquet")
fig, ax = plt.subplots(1, 2, figsize=(12, 4.4))
s = otif.sort_values("otif_pct").head(12)
ax[0].barh(s.supplier_id + " " + s.region, s.otif_pct,
           color=[C["bad"] if v < 90 else C["warn"] if v < 95 else C["ok"] for v in s.otif_pct])
ax[0].axvline(95, color="k", ls="--", lw=1); ax[0].set_title("Worst 12 suppliers by OTIF% (SLA 95%)")
ax[0].set_xlim(0, 105)
rt = pd.read_parquet(PROC / "rpt_route_bottlenecks.parquet")
rt["lane"] = rt.origin_port + " → " + rt.dest_port
rt = rt.sort_values("otif_pct").head(10)
ax[1].barh(rt.lane, rt.otif_pct, color=[C["bad"] if v < 85 else C["warn"] for v in rt.otif_pct])
ax[1].set_title("Bottleneck lanes by OTIF%"); ax[1].set_xlim(0, 105)
fig.tight_layout(); fig.savefig(OUT / "supply_otif_suppliers_routes.png"); plt.close(fig)

dr = pd.read_parquet(PROC / "rpt_delay_reasons.parquet")
fig, ax = plt.subplots(1, 2, figsize=(12, 4))
ax[0].pie(dr.orders, labels=dr.delay_reason, autopct="%1.1f%%", textprops={"fontsize": 8})
ax[0].set_title("Delay reason mix (delayed orders)")
sc = pd.read_parquet(PROC / "rpt_scenario.parquet")
ax[1].bar(sc.scenario, sc.annual_holding_cost_impact_eur / 1e6, color=[C["main"], C["warn"], C["bad"]])
ax[1].set_title("Inventory holding-cost impact of lead-time increase (€M/yr)")
for i, v in enumerate(sc.annual_holding_cost_impact_eur / 1e6):
    ax[1].text(i, v, f"€{v:.1f}M", ha="center", va="bottom", fontsize=9)
fig.tight_layout(); fig.savefig(OUT / "supply_delays_scenario.png"); plt.close(fig)

pr = pd.read_parquet(PROC / "rpt_price_trend.parquet")
fig, ax = plt.subplots(figsize=(10, 3.6))
ax.plot(pr.month, pr.avg_copper, label="Copper (USD/t)")
ax.plot(pr.month, pr.avg_aluminum * 3.4, label="Aluminum (USD/t, scaled x3.4)")
ax.set_title("LME-style metal price index trend"); ax.legend()
fig.tight_layout(); fig.savefig(OUT / "supply_metal_prices.png"); plt.close(fig)

print("charts:", sorted(p.name for p in OUT.glob("*.png")))
