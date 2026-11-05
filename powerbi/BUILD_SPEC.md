# Power BI build spec — exact pages, visuals, measures

Import **all** CSVs from `data/processed/` (Get Data → Text/CSV, keep headers, UTF-8).
Star schema: `rpt_*` report tables are small and independent; the two fact tables
(`offshore_grid_hourly`, `erp_orders` in data/raw) can be added for drill-down.

## Project 1 — "Offshore Grid Load & Maintenance" (Energy_Grid.pbix)

**Page 1 — Executive overview**
- Card: avg utilization % (measure below), Card: peak-to-average ratio (max),
  Card: total overload hours, Card: cables near capacity (>90%).
- Bar chart: `peak_to_avg_ratio` by `cable_id` (table rpt_peak_to_avg).
- Line chart: monthly avg utilization + high-load hours (rpt_monthly_stress), x = month.

**Page 2 — Load & utilization profiling**
- Clustered column: avg vs peak utilization by `season` and `cable_id` (rpt_season_profile).
- Line chart: avg utilization by `hour_of_day` per cable (rpt_hourly_profile), legend = cable.
- Stacked bar: utilization buckets (<50, 50–75, 75–90, 90–100, >100) per cable (rpt_util_buckets).
- Matrix: cable × season peak_util with conditional formatting (red > 90).

**Page 3 — Maintenance scheduling**
- Bar chart: `stress_index` by `cable_id`, color = `maintenance_priority` (rpt_stress_nodes).
- Table: cable, location, voltage_kv, high_load_hours, overload_hours, priority.
- Line: monthly high_load_hours + overload_hours per cable (rpt_monthly_stress).
- Slicer: substation / location / voltage.

### DAX (create as measures on the energy model) — see `measures_energy.dax`

## Project 2 — "Global Supply Chain & Raw Materials" (Supply_Chain.pbix)

**Page 1 — Executive overview**
- Cards from rpt_otif_overview: OTIF %, late %, avg lead-time variance (days), total spend €.
- Line: monthly copper & aluminum index (rpt_price_trend).
- Bar: OTIF% by region (aggregate rpt_otif_by_supplier or join to erp_orders).

**Page 2 — Supplier & SLA performance**
- Bar (top 12 worst): OTIF% by supplier with SLA 95% reference line (rpt_otif_by_supplier).
- Scatter: lt_variance_days (x) vs spend_eur (y), color = sla_status.
- Table: stockout risk (rpt_stockout_risk) sorted by short_shipments.

**Page 3 — Logistics network**
- Map visual: origin_port → dest_port sized by shipments, colored by OTIF% (rpt_route_bottlenecks).
- Bar: OTIF% by lane (origin → dest).
- Pie/bar: delay reason share (rpt_delay_reasons).

**Page 4 — Scenario analysis (lead time +10% / +20%)**
- Column chart: annual holding-cost impact € by scenario (rpt_scenario).
- Bar: impact by region (rpt_scenario_by_region).
- Card: extra pipeline inventory € per scenario.

### DAX — see `measures_supplychain.dax`
