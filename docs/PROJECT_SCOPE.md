# Automotive Analytics Platforms — Project Scope

Two BI platforms for a (synthetic) global automotive manufacturer, inside this repo
in this repo.

## Project A — Financials & Logistics (5-year history & forecast)
- Synthetic monthly plant financials 2022-01..2026-10 (5 plants), 30k logistics
  orders, plus unstructured sources: nested machine logs (JSON), free-text supplier
  notes (JSON) — parsed and flattened in Phase 1.
- Pipeline: `gen_automotive.py` → raw → `parse_raw.py` → parsed CSVs →
  `sql/01_cleaning_and_model.sql` (ROW_NUMBER/PARTITION BY dedup, 5-year rolling
  window views, star schema dim_date/dim_plant/dim_region/dim_material + facts,
  DQ gates) → `sql/02_projectA_reports.sql` (yearly KPIs, YoY/CAGR, 2027 linear
  forecast + GROUP TARGET +8%, logistics OTIF/lead-time, downtime, supplier notes).
- Deliverables: `excel/automotive_financials.xlsx` (staging), `powerbi/projectA_dashboard.html`,
  Power BI spec + DAX + Power Query in `powerbi/`.

## Project B — Regional Sales & Customer Sentiment
- Synthetic regional sales (6 regions x 58 months) + 5,000 free-text reviews
  (JSONL) scored with a lexicon into Positive/Neutral/Negative.
- `sql/03_projectB_reports.sql`: yearly sales, region rank per year (ribbon data),
  treemap shares (latest year), sentiment KPIs overall/by region/by year.
- Deliverables: `excel/automotive_sales_cx.xlsx`, `powerbi/projectB_dashboard.html`.

## Design constraint (applies everywhere)
Simple, readable, non-technical: no wide tables, high-contrast colors (no
red/green-only cues), body ≥14pt, callouts ≥24pt, whitespace, Past→Present→Future
narrative arc. Charts: A = bars/lines/gauge-style cards/multi-card; B = ribbon
(rank table with arrows), treemap bars, conditional bar coloring, sentiment KPI cards.

## Run
```bash
cd .
PY="env -u PYTHONPATH venv/bin/python"
$PY scripts/gen_automotive.py     # synthetic raw data
$PY scripts/parse_raw.py          # flatten JSON / parse free text -> data/parsed
$PY scripts/build_reports.py      # DuckDB SQL -> data/processed (parquet+csv)
$PY scripts/make_excel.py         # Excel staging workbooks -> excel/
$PY scripts/make_dashboards.py    # accessible HTML dashboards -> powerbi/
```

## Power BI (Windows)
Import CSVs from `data/processed/`, load `powerbi/powerquery/*.m`, measures from
`powerbi/measures_automotive.dax`, pages per `powerbi/BUILD_SPEC_AUTOMOTIVE.md`.
Scheduled refresh + mobile layout per Phase 6 — see BUILD_SPEC.
