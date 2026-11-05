# Power BI build spec — Automotive Analytics (Projects A & B)

Import CSVs from `automotive-analytics/data/processed/`. Star schema from
`sql/01_cleaning_and_model.sql` (dim_date, dim_plant, dim_region, dim_material +
fact_financials / fact_logistics / fact_sales). Power Query: `powerquery/ETL_automotive.m`.

## Project A — Financials & Logistics (Auto_Financials.pbix), 3 pages, each = multicard + gauge + bar
- **Page 1 Financial Overview:** 3 KPI cards (revenue, op profit, units), gauge
  "operating margin vs 15% target", bar "revenue by plant" with **conditional
  formatting** (navy ≥115% of avg · blue ≥ avg · orange ≥80% · gray below) —
  **bar is drillthrough** to page 3, plus a **plant slicer** (highlight selection).
- **Page 2 Logistics & Ops:** 3 KPI cards (OTIF, avg lead time, spend), gauge
  "OTIF vs 95% SLA", bar "lead time by material" — **drillthrough** to page 3.
- **Page 3 Drillthrough:** monthly revenue line for the clicked plant (page 1) or
  lead-time-by-year for the clicked material (page 2) + detail table + back button.
- Visuals per brief: bars, gauges (target tracking), multi-card. Conditional
  formatting on bars via threshold color scale (navy/orange, not red/green-only).
- Accessibility: high-contrast palette, visual titles ≥14pt, callout cards ≥24pt,
  whitespace, tabbed navigation.

## Project B — Sales & CX (Auto_SalesCX.pbix), 3 pages, each = multicard + gauge + bar
- **Page 1 Sales Overview:** 3 KPI cards (revenue, units, regions), gauge
  "YoY growth vs +5% target", **treemap** "revenue by region" (area = share, labeled € + %) — **drillthrough** to page 3.
- **Page 2 Customer Voice & Rank Ribbon:** 3 sentiment KPI cards (% positive, avg rating,
  % negative), gauge "positive sentiment vs 60% target", **ribbon chart** (region rank
  over years; **conditional formatting**: band color = rank, dark navy = #1 → gray = last;
  band thickness = revenue; click band = drillthrough), plus **line chart** of % positive
  sentiment by year.
- **Page 3 Drillthrough:** monthly revenue line for the clicked region, or
  % positive by year for the clicked sentiment region + table + back button.


## Phase 6 deployment
- Publish both to dedicated workspaces (Auto-Finance, Auto-Sales-CX) with
  simplified viewer access; schedule daily refresh; create Mobile layout
  (single-column, large touch targets) for iOS/Android executive viewing.
