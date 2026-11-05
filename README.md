# End-to-End Automotive Analytics Platforms — Portfolio Project

Two BI platforms for a (synthetic) global automotive manufacturer:

- **Project A — Financials & Logistics:** Raw Materials Logistics & Financial
  Performance (5-year historical analysis 2022–2026 + 2027 forecast).
- **Project B — Sales & CX:** Regional Sales & Customer Sentiment Analysis.

All data is **synthetic** (fixed RNG seeds, fully reproducible offline).


## Quick start
```bash
cd /home/lucky/automotive-analytics
PY="env -u PYTHONPATH venv/bin/python"     # PYTHONPATH guard: the shell leaks another env
$PY scripts/gen_automotive.py      # synthetic raw data (CSV/JSON/JSONL/parquet) -> data/raw/
$PY scripts/parse_raw.py           # flatten nested JSON, parse free-text notes/reviews -> data/parsed/
$PY scripts/build_reports.py       # DuckDB SQL cleaning + reports -> data/processed/ (parquet+csv)
$PY scripts/make_excel.py          # Excel staging workbooks -> excel/
$PY scripts/make_dashboards.py     # accessible HTML dashboards -> powerbi/
```
Open `powerbi/projectA_dashboard.html` and `powerbi/projectB_dashboard.html` in a browser.

## Layout
```
data/raw/        synthetic raw sources (incl. nested JSON logs, JSONL reviews, free-text notes)
data/parsed/     Phase-1 parsed clean tables (gitignored, regenerate via parse_raw.py)
data/processed/  Phase-3/4 report tables (parquet + csv) — the Power BI import source
sql/             01 cleaning & star schema (ROW_NUMBER dedup, 5y window views, DQ gates),
                 02 Project A reports, 03 Project B reports
scripts/         gen_automotive.py, parse_raw.py, build_reports.py, make_excel.py, make_dashboards.py
excel/           automotive_financials.xlsx, automotive_sales_cx.xlsx (tables, formats, charts)
powerbi/         projectA/B_dashboard.html (2 pages each: multicard+gauge+bar/treemap/ribbon
                 + drillthrough page), BUILD_SPEC_AUTOMOTIVE.md, measures_automotive.dax,
                 powerquery/ETL_automotive.m
docs/            PROJECT_SCOPE.md, STORYTELLING_REPORT.md
```

## Design principle
Simplicity & readability everywhere: no wide tables, high-contrast palette (no
red/green-only cues), body ≥14pt, callouts ≥24pt, Past→Present→Future narrative.

## Power BI (Windows)
Power BI Desktop is Windows-only. Import CSVs from `data/processed/`, load
`powerbi/powerquery/ETL_automotive.m`, measures from `powerbi/measures_automotive.dax`,
build pages per `powerbi/BUILD_SPEC_AUTOMOTIVE.md` (each page = multicard + gauge +
bar/treemap/ribbon, drillthrough page), then publish to workspaces with scheduled
refresh + mobile layout.

## Publish
```bash
git remote add origin https://github.com/<you>/automotive-analytics.git
git push -u origin main
```
