-- Supply chain: OTIF, lead-time variance, stockout risk
CREATE OR REPLACE TABLE erp_orders AS
SELECT o.*, s.region, s.country, s.primary_material AS supplier_material,
  s.base_lead_days AS supplier_base_lt, s.sla_otif_target
FROM read_parquet('data/raw/erp_orders.parquet') o
JOIN read_csv('data/raw/suppliers.csv', header=true) s USING (supplier_id);

CREATE OR REPLACE TABLE rpt_otif_overview AS
SELECT COUNT(*) AS orders, ROUND(100.0*AVG(otif::INT),2) AS otif_pct,
  ROUND(100.0*AVG(late::INT),2) AS late_pct, ROUND(100.0*AVG((NOT in_full)::INT),2) AS short_ship_pct,
  ROUND(AVG(actual_lead_days),1) AS avg_actual_lt, ROUND(AVG(promised_lead_days),1) AS avg_promised_lt,
  ROUND(AVG(actual_lead_days - promised_lead_days),1) AS avg_lt_variance_days,
  SUM(order_value_eur) AS total_spend_eur
FROM erp_orders;

CREATE OR REPLACE TABLE rpt_otif_by_supplier AS
SELECT supplier_id, region, country, COUNT(*) AS orders,
  ROUND(100.0*AVG(otif::INT),1) AS otif_pct, MAX(sla_otif_target)*100 AS sla_target_pct,
  CASE WHEN AVG(otif::INT) >= MAX(sla_otif_target) THEN 'MEETS SLA' ELSE 'BELOW SLA' END AS sla_status,
  ROUND(AVG(actual_lead_days - promised_lead_days),1) AS lt_variance_days,
  SUM(order_value_eur) AS spend_eur
FROM erp_orders GROUP BY 1,2,3 HAVING COUNT(*) >= 50 ORDER BY otif_pct ASC;

CREATE OR REPLACE TABLE rpt_route_bottlenecks AS
SELECT origin_port, dest_port, plant, COUNT(*) AS shipments,
  ROUND(100.0*AVG(otif::INT),1) AS otif_pct,
  ROUND(AVG(actual_lead_days),1) AS avg_lt,
  ROUND(AVG(actual_lead_days - promised_lead_days),1) AS lt_variance,
  ROUND(100.0*AVG((delay_reason <> 'On time')::INT),1) AS delayed_pct
FROM erp_orders GROUP BY 1,2,3 ORDER BY otif_pct ASC, lt_variance DESC;

CREATE OR REPLACE TABLE rpt_delay_reasons AS
SELECT delay_reason, COUNT(*) AS orders, ROUND(100.0*COUNT(*)/(SELECT COUNT(*) FROM erp_orders),2) AS share_pct,
  ROUND(AVG(actual_lead_days - promised_lead_days),1) AS avg_extra_days
FROM erp_orders GROUP BY 1 ORDER BY orders DESC;

CREATE OR REPLACE TABLE rpt_stockout_risk AS
SELECT supplier_id, region, material, COUNT(*) AS orders,
  SUM(CASE WHEN NOT in_full THEN 1 ELSE 0 END) AS short_shipments,
  SUM(CASE WHEN actual_lead_days > promised_lead_days + 7 THEN 1 ELSE 0 END) AS severe_delays,
  ROUND(100.0*SUM((NOT in_full)::INT)/COUNT(*),1) AS short_pct,
  CASE WHEN SUM((NOT in_full)::INT) > 10 OR SUM(CASE WHEN actual_lead_days > promised_lead_days + 7 THEN 1 ELSE 0 END) > 15
       THEN 'HIGH STOCKOUT RISK' WHEN SUM((NOT in_full)::INT) > 4 THEN 'MEDIUM' ELSE 'LOW' END AS stockout_risk
FROM erp_orders GROUP BY 1,2,3 ORDER BY short_shipments DESC;

-- metal price trend joined to spend
CREATE OR REPLACE TABLE rpt_price_trend AS
SELECT date_trunc('month', date::TIMESTAMP) AS month,
  AVG(copper_usd_t) AS avg_copper, AVG(aluminum_usd_t) AS avg_aluminum,
  ROUND(AVG(copper_usd_t)/FIRST(AVG(copper_usd_t)) OVER (ORDER BY date_trunc('month', date::TIMESTAMP)) - 1, 4) AS cu_vs_start
FROM read_csv('data/raw/lme_metal_prices.csv', header=true) GROUP BY 1 ORDER BY 1;
