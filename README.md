# PFISTERER Winterbach — Data Analyst Portfolio Project

Two usecase-based analytics projects built with **synthetic data** (no real company data):

1. **Renewable Energy & Offshore Substation Load Analysis** (energy grid focus)
2. **Global Supply Chain & Raw Material Logistics Dashboard**

## Hardware used
AMD Ryzen AI MAX+ 395 (16C/32T @ 5.2 GHz), 121 GB RAM, Radeon 8060S iGPU (ROCm),
588 GB free NVMe, Ubuntu 26.04. Dedicated venv: `./venv` (Python 3.12, uv-created).

## Quick start
```bash
cd /home/lucky/pfisterer-analytics
source venv/bin/activate
python scripts/gen_energy.py        # synthetic offshore grid data -> data/raw/
python scripts/gen_supplychain.py   # synthetic ERP + LME prices  -> data/raw/
python scripts/build_reports.py     # DuckDB SQL reports          -> data/processed/
python scripts/make_charts.py       # static dashboard PNGs       -> analysis/
```

## Layout
```
data/raw/          synthetic source data (parquet + csv)
data/processed/    report tables (parquet + csv) — the Power BI import source
sql/               01 energy profiling, 02 maintenance stress, 03 supply chain, 04 scenario
scripts/           generators, report builder, chart renderer
analysis/          rendered dashboard PNGs (mirror the Power BI pages)
powerbi/           DAX measures + exact dashboard build spec for Power BI Desktop
docs/              methodology
```

## Power BI note (important)
Power BI Desktop runs on **Windows only** — it cannot run on this Linux machine.
Everything the Desktop needs is ready here: the processed CSVs in `data/processed/`,
the DAX measures in `powerbi/*.dax`, and the page-by-page build spec in
`powerbi/BUILD_SPEC.md`. Open Desktop → Get Data → Text/CSV → follow the spec →
Publish. `powerbi/INTERACTIVE_DASHBOARDS.html` is a browser version that works
immediately on this machine.

**Scope & how to run:** see `docs/PROJECT_SCOPE.md` (full scope, in/out of scope,
step-by-step run commands, Power BI steps, deferred GitHub publish).

## Use case 1 — Offshore grid load & connector maintenance
- Dataset: 128,448 hourly rows, 8 export cables (320/525 kV), 2025-01 → 2026-10,
  weather-driven wind generation, storm derating, overload hours.
- Deliverables: seasonal/intraday peak profiling (SQL 01), peak-to-average ratios,
  utilization buckets, maintenance stress index with priority classes (SQL 02).

## Use case 2 — Supply chain & raw materials
- Dataset: 60,000 ERP order lines, 40 suppliers, 10 port-to-port lanes, daily
  synthetic LME copper/aluminum index (730 days).
- Deliverables: OTIF / lead-time variance / stockout risk (SQL 03), route
  bottlenecks, delay reasons, SLA compliance, +10%/+20% lead-time scenario with
  holding-cost impact in EUR (SQL 04).

## Publish to GitHub
Repo is initialized locally. When you are ready:
```bash
git remote add origin https://github.com/<you>/pfisterer-analytics.git
git push -u origin main
```
(GitHub auth to be set up separately — deferred per instruction.)
