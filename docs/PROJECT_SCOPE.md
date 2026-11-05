# Project Scope — PFISTERER Winterbach Data Analyst Portfolio

## 1. Purpose
A workable, reproducible analytics portfolio for a data analyst application at
PFISTERER Winterbach, built entirely on **synthetic data** (no real company or
third-party data). Two usecases under one project heading set.

## 2. In scope

### Use case 1 — Renewable Energy & Offshore Substation Load Analysis (energy grid)
- Synthetic hourly dataset: 8 offshore export cables (320/525 kV), 8 substations,
  2025-01-01 → 2026-10-31 (128,448 rows), weather-driven generation, storm
  derating, overload hours (`data/raw/offshore_grid_hourly.parquet`).
- Load & utilization profiling in SQL: peaks by season, time of day, weather;
  peak-to-average ratios; utilization buckets (`sql/01_energy_load_profiling.sql`).
- Maintenance scheduling logic: accumulated high-stress load hours per node,
  stress index, priority classes CRITICAL/HIGH/MEDIUM/LOW (`sql/02_maintenance_stress.sql`).
- Executive dashboard: Power BI spec + runnable HTML dashboard + PNG panels.

### Use case 2 — Global Supply Chain & Raw Material Logistics
- Synthetic ERP dataset: 60,000 order lines, 40 suppliers, 4 regions, 10 port→plant
  lanes, 2025-01 → 2026-10; synthetic LME-style copper/aluminum daily index
  (`data/raw/erp_orders.parquet`, `suppliers.csv`, `lme_metal_prices.csv`).
- Data pipeline (Python + DuckDB SQL): OTIF, lead-time variance, stockout risk,
  route bottlenecks, delay reasons, supplier SLA compliance (`sql/03_supply_chain_metrics.sql`).
- Supply chain dashboard: Power BI spec + HTML dashboard + PNG panels.
- Scenario analysis: inventory holding-cost impact of +10%/+20% lead times
  (`sql/04_scenario_analysis.sql`).
- Reorder-cycle logic: safety stock (95% service level, z=1.65), reorder points per
  material, dual-source alerts for long/volatile lead times (`sql/07_reorder_cycles.sql`).
- Relational modeling: star schema (energy) and snowflake schema (supply chain) with
  ETL data-quality gates — duplicate removal, orphan-FK and invalid-row checks
  (`sql/05_star_snowflake_model.sql`); query optimization via pre-aggregated tables
  replacing full-fact scans (`sql/06_query_optimization.sql`).
- Power Query (M) ETL scripts for Power BI Desktop (`powerbi/powerquery/*.m`).
- Excel workbook with XVERWEIS lookups, Excel tables, KPI cells and a bottleneck-lane
  chart (`excel/supply_chain_workbook.xlsx`).
- Automated refresh + alerting: `scripts/refresh_and_alert.py` re-runs the pipeline and
  fires CRITICAL/WARNING alerts (connector overload, stockout risk, SLA breach,
  OTIF < 90%, DQ violations) → `alerts.json`/`alerts.log`.

### Shared deliverables
- Power BI deliverables: page-by-page build spec (`powerbi/BUILD_SPEC.md`),
  DAX measures (`powerbi/measures_*.dax`), processed CSV/Parquet import tables
  (`data/processed/`). Power BI Desktop itself is Windows-only and out of scope
  on this Linux machine; the HTML dashboards in `powerbi/` are the runnable equivalent.
- Local git repository with all artifacts committed (GitHub publish explicitly
  deferred — out of scope until the user asks).

## 3. Out of scope
- Real PFISTERER data, real ENTSO-E/Open Power System Data downloads, any PII.
- Power BI Desktop installation/refresh on Linux; publishing to Power BI Service.
- GitHub remote creation/push (deferred by user instruction).
- Production pipelines, scheduling, alerting; this is a portfolio, not an ops system.

## 4. Environment / prerequisites
- Hardware used: AMD Ryzen AI MAX+ 395 (16C/32T), 121 GB RAM, Radeon 8060S iGPU,
  Ubuntu 26.04, 588 GB free disk.
- Python 3.12 venv created with `uv` at `/home/lucky/pfisterer-analytics/venv`
  (deps: pandas, numpy, duckdb, pyarrow, matplotlib).
- **Gotcha:** the shell exports a PYTHONPATH pointing at another env — run all
  project commands with `env -u PYTHONPATH venv/bin/python ...` (or
  `source venv/bin/activate` after unsetting PYTHONPATH).

## 5. How to run (end to end, from scratch)
```bash
cd /home/lucky/pfisterer-analytics

# 0. venv (already created; recreate with: uv venv venv --python 3.12 &&
#    uv pip install -p venv/bin/python pandas numpy duckdb pyarrow matplotlib)

# 1. generate synthetic raw data
env -u PYTHONPATH venv/bin/python scripts/gen_energy.py        # -> data/raw/offshore_grid_hourly.parquet
env -u PYTHONPATH venv/bin/python scripts/gen_supplychain.py   # -> data/raw/{erp_orders.parquet,suppliers.csv,lme_metal_prices.csv}

# 2. run SQL reports (DuckDB) -> data/processed/*.parquet + *.csv
env -u PYTHONPATH venv/bin/python scripts/build_reports.py

# 3. static dashboard PNGs -> analysis/
env -u PYTHONPATH venv/bin/python scripts/make_charts.py

# 4. interactive HTML dashboards -> powerbi/*.html
env -u PYTHONPATH venv/bin/python scripts/make_html_dashboards.py

# 5. open the dashboards in any browser
#    powerbi/energy_dashboard.html  |  powerbi/supplychain_dashboard.html
```

Expected output: 14 `rpt_*` report tables, 6 PNGs, 2 HTML dashboards.
Verified results on this machine: OTIF 89.4%, late 7.3%, lead-time variance −3.0 d,
total spend ≈ €48.4 bn (synthetic); 923 overload hours across 4 CRITICAL cables;
+10% lead time → €374M extra pipeline inventory / €225k per yr holding cost.

## 6. Power BI (on a Windows machine)
1. Open Power BI Desktop → Get Data → Text/CSV → select all CSVs in `data/processed/`.
2. Create measures from `powerbi/measures_energy.dax` / `measures_supplychain.dax`.
3. Build pages per `powerbi/BUILD_SPEC.md` (3 pages energy, 4 pages supply chain).
4. Publish to Power BI Service when ready.

## 7. Reproduce / verify
```bash
git log --oneline                 # committed state
git status                        # clean tree
ls data/processed | wc -l         # 28 files (14 tables x parquet+csv)
```

## 8. GitHub (deferred — run when approved)
```bash
git remote add origin https://github.com/<user>/pfisterer-analytics.git
git push -u origin main
```
