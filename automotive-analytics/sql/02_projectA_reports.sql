-- Phase 4/5 KPI reports — Project A (Financials & Logistics), 5-year history + forecast.

-- yearly financial KPIs per plant + total
CREATE OR REPLACE TABLE rpt_fin_yearly AS
SELECT year, SUM(revenue_eur_m) AS revenue_eur_m, SUM(cogs_eur_m) AS cogs_eur_m,
  SUM(opex_eur_m) AS opex_eur_m, SUM(capex_eur_m) AS capex_eur_m, SUM(op_profit_eur_m) AS op_profit_eur_m,
  SUM(units_sold) AS units,
  ROUND(100.0*SUM(revenue_eur_m - cogs_eur_m)/SUM(revenue_eur_m),1) AS gross_margin_pct,
  ROUND(100.0*SUM(op_profit_eur_m)/SUM(revenue_eur_m),1) AS op_margin_pct
FROM fact_financials GROUP BY 1 ORDER BY 1;

CREATE OR REPLACE TABLE rpt_fin_by_plant AS
SELECT plant, year, SUM(revenue_eur_m) AS revenue_eur_m, SUM(capex_eur_m) AS capex_eur_m,
  ROUND(100.0*SUM(op_profit_eur_m)/SUM(revenue_eur_m),1) AS op_margin_pct
FROM fact_financials GROUP BY 1,2 ORDER BY plant, year;

-- YoY growth + 5-year CAGR
CREATE OR REPLACE TABLE rpt_growth AS
SELECT year, revenue_eur_m,
  ROUND(100.0*(revenue_eur_m / LAG(revenue_eur_m) OVER (ORDER BY year) - 1),1) AS yoy_growth_pct
FROM rpt_fin_yearly;

-- simple linear-trend forecast 2027 (per plant, monthly) + group target = +8% YoY
CREATE OR REPLACE TABLE rpt_forecast_2027 AS
WITH trend AS (
  SELECT plant, regr_slope(revenue_eur_m, CAST(strftime((month || '-01')::DATE, '%Y') AS DOUBLE)*12 + CAST(strftime((month || '-01')::DATE, '%m') AS DOUBLE)) AS slope,
         regr_intercept(revenue_eur_m, CAST(strftime((month || '-01')::DATE, '%Y') AS DOUBLE)*12 + CAST(strftime((month || '-01')::DATE, '%m') AS DOUBLE)) AS intercept
  FROM fact_financials GROUP BY 1
)
SELECT t.plant, m.month_key AS forecast_month,
  ROUND(t.intercept + t.slope * (2027*12 + m.month_num), 1) AS forecast_revenue_eur_m
FROM trend t, (SELECT month_key, month_num FROM dim_date WHERE year = 2026) m
UNION ALL
SELECT 'GROUP TARGET', month, ROUND(SUM(revenue_eur_m)*1.08/12,1) FROM fact_financials WHERE year=2026 GROUP BY month ORDER BY 1,2;

-- logistics KPIs by year (lead time efficiency, OTIF)
CREATE OR REPLACE TABLE rpt_logistics_yearly AS
SELECT year, COUNT(*) AS orders,
  ROUND(AVG(actual_lead_days),1) AS avg_lead_days, ROUND(AVG(actual_lead_days - promised_lead_days),1) AS lt_variance,
  ROUND(100.0*AVG(otif::INT),1) AS otif_pct, SUM(order_value_eur) AS spend_eur
FROM fact_logistics GROUP BY 1 ORDER BY 1;

CREATE OR REPLACE TABLE rpt_leadtime_by_material AS
SELECT material, COUNT(*) AS orders, ROUND(AVG(actual_lead_days),1) AS avg_lead_days,
  ROUND(100.0*AVG(otif::INT),1) AS otif_pct, SUM(order_value_eur) AS spend_eur
FROM fact_logistics GROUP BY 1 ORDER BY avg_lead_days DESC;

-- supplier note insights (parsed free text)
CREATE OR REPLACE TABLE rpt_supplier_notes AS
SELECT material, COUNT(*) AS notes, ROUND(AVG(delay_days),1) AS avg_delay_days, ROUND(AVG(price_increase_pct),1) AS avg_price_increase_pct
FROM notes_raw GROUP BY 1 ORDER BY avg_delay_days DESC;

-- machine downtime by plant (parsed nested logs)
CREATE OR REPLACE TABLE rpt_downtime AS
SELECT plant, COUNT(*) AS events, ROUND(AVG(downtime_min),1) AS avg_downtime_min, SUM(units_produced) AS units
FROM mach_raw GROUP BY 1 ORDER BY avg_downtime_min DESC;
