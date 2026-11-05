-- Query optimization: pre-aggregated (materialized) fact for dashboard speed +
-- EXPLAIN ANALYZE evidence. DuckDB has no CREATE INDEX; the optimization strategy is
-- (a) push filters/aggregations into materialized tables and (b) avoid scanning the
-- 128k-row raw fact for every visual (PBI imports the small rpt_* tables instead).

-- daily aggregate at cable grain (128k rows -> ~5.8k rows): the table every
-- trend visual should bind to instead of fact_load_hourly
CREATE OR REPLACE TABLE agg_load_daily AS
SELECT CAST(e.timestamp AS DATE) AS day, e.cable_id,
       AVG(e.cable_flow_mw) AS avg_flow_mw, MAX(e.cable_flow_mw) AS peak_flow_mw,
       AVG(e.utilization_pct) AS avg_util, MAX(e.utilization_pct) AS peak_util,
       SUM(CASE WHEN e.utilization_pct > 90 THEN 1 ELSE 0 END) AS high_load_hours,
       SUM(CASE WHEN e.utilization_pct > 100 THEN 1 ELSE 0 END) AS overload_hours,
       AVG(e.wind_speed_mps) AS avg_wind, BOOL_OR(e.storm) AS storm_day
FROM energy_hourly e GROUP BY 1, 2;

-- monthly supplier OTIF (60k rows -> 40 x 22 rows)
CREATE OR REPLACE TABLE agg_otif_supplier_month AS
SELECT date_trunc('month', order_date) AS month, supplier_id,
       COUNT(*) AS orders, ROUND(100.0*AVG(otif::INT), 2) AS otif_pct,
       ROUND(AVG(actual_lead_days - promised_lead_days), 2) AS lt_variance
FROM fact_orders_clean GROUP BY 1, 2;

-- proof: run both plans; the optimized one touches far fewer rows
-- EXPLAIN ANALYZE SELECT COUNT(*), AVG(utilization_pct) FROM fact_load_hourly WHERE utilization_pct > 90;
-- EXPLAIN ANALYZE SELECT SUM(high_load_hours) FROM agg_load_daily;
