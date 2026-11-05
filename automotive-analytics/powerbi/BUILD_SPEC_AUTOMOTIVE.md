# Power BI build spec — Automotive Analytics (Projects A & B)

Import CSVs from `automotive-analytics/data/processed/`. Star schema from
`sql/01_cleaning_and_model.sql` (dim_date, dim_plant, dim_region, dim_material +
fact_financials / fact_logistics / fact_sales). Power Query: `powerquery/ETL_automotive.m`.

## Project A — Financials & Logistics (Auto_Financials.pbix), 3 pages
- **Page 1 Past:** line chart revenue by year; line gross vs op margin %; cards:
  revenue, CAGR, op margin (measures in measures_automotive.dax).
- **Page 2 Present:** bar CAPEX by plant (latest year); bar avg lead time by year;
  bar OTIF% by year; table lead time by material; table downtime by plant.
- **Page 3 Future:** line 2027 monthly forecast (sum of plants) vs GROUP TARGET (+8%);
  gauge-style card: target vs forecast; DQ table.
- Visuals per brief: bars, lines, multi-card, gauge (target tracking). Conditional
  formatting on op margin and OTIF bars (threshold colors, not red/green-only —
  use blue/orange/gray ramp).
- Accessibility: theme with high-contrast palette, all visual titles ≥14pt,
  callout cards ≥24pt, generous whitespace.

## Project B — Sales & CX (Auto_SalesCX.pbix), 3 pages
- **Page 1 Past:** line revenue by year; cards units/revenue/yoy.
- **Page 2 Present:** treemap revenue by region (latest year); ribbon chart
  revenue_rank by region over years (rank shifts); bar with conditional formatting.
- **Page 3 Voice of customer:** sentiment KPI cards (% positive, avg rating,
  review count); line % positive by year; table sentiment by region.

## Phase 6 deployment
- Publish both to dedicated workspaces (Auto-Finance, Auto-Sales-CX) with
  simplified viewer access; schedule daily refresh; create Mobile layout
  (single-column, large touch targets) for iOS/Android executive viewing.
