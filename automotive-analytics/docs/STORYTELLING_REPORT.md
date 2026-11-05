# Technical & Storytelling Report — Automotive Analytics Platforms

## 1. End-to-end methodology (raw → readable tables)
1. **Ingest (Phase 1):** synthetic raw sources — nested JSON machine logs, JSONL
   free-text reviews, JSON supplier notes, plus tidy CSV facts (financials, orders,
   sales). `scripts/gen_automotive.py` (fixed seed 11) makes it reproducible;
   `scripts/parse_raw.py` flattens nested JSON (`payload.metrics.*` → columns) and
   regex-parses supplier notes (`delayed N days`, `price +N%`); review text is
   cleaned (whitespace) and scored with a small lexicon into Positive/Neutral/Negative.
2. **Stage (Phase 2):** clean CSVs → Excel workbooks (`excel/automotive_*.xlsx`)
   with real Excel tables, standardized formats (YYYY-MM dates, EUR m, 1-decimal %),
   KPI cells and charts — auditable by hand.
3. **Clean (Phase 3, SQL/DuckDB):** `ROW_NUMBER() OVER (PARTITION BY …)` removes
   duplicate natural keys; views `v_*_5y` enforce the strict 5-year rolling window;
   star schema (dim_date/plant/region/material + facts) keeps joins trivial;
   `rpt_data_quality` proves 0 duplicates/orphans.
4. **Model & ETL (Phase 4, Power BI):** narrow star schema, Power Query M enforces
   types and replaces nulls, DAX measures are plain business language
   (`Total Revenue EURm`, `OTIF %`, `5Y CAGR %`, `2027 Target EURm`).
5. **Visualize (Phase 5):** accessible HTML dashboards mirror the PBI pages —
   high contrast, ≥14pt body, ≥24pt callouts, Past→Present→Future arc.

## 2. Visual choice & simplicity rationale
- **Bars** (revenue, CAPEX, lead time, OTIF): instantly readable magnitude comparison.
- **Lines** (margins, forecast vs target): show trend and direction — the "story over time".
- **Multi-card KPIs**: one number per card, no chart-reading skill needed.
- **Gauge-style target card** (2027 target vs forecast): a single glance tells "on track?".
- **Ribbon/rank table with ▲▼** (Project B): shows who overtook whom without axes to read.
- **Treemap-as-bars** (region revenue share): proportional area = share, labeled in €.
- **Sentiment KPI cards**: % positive + avg rating — no word clouds, no jargon.
- No red/green-only cues: palette is navy/orange/blue/gray; arrows + labels carry meaning.

## 3. Executive story arc
- **Past:** 5-year revenue, margin and OTIF lines establish the baseline (2022→2026).
- **Present:** CAPEX by plant, lead time by material, region revenue tree and sentiment
  cards show where the business stands today and where customers feel pain.
- **Future:** 2027 linear-trend forecast per plant vs the +8% GROUP TARGET line —
  the gap between the two lines is the decision the dashboard exists to inform.
