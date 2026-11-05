-- Scenario: financial impact of +10% / +20% lead times on inventory holding cost
-- Assumptions (documented in README): annual demand value = total spend over window,
-- holding cost rate = 22%/yr of inventory value, extra pipeline inventory = demand * extra days.
CREATE OR REPLACE TABLE rpt_scenario AS
WITH base AS (
  SELECT SUM(order_value_eur) AS annual_spend_eur,
         AVG(actual_lead_days) AS base_lt,
         COUNT(*) AS orders
  FROM erp_orders
),
daily AS (SELECT annual_spend_eur / 365.0 AS daily_demand_eur, base_lt FROM base)
SELECT scenario, base_lt, extra_days,
  ROUND(extra_days * daily_demand_eur, 0) AS extra_pipeline_inventory_eur,
  ROUND(extra_days * daily_demand_eur * 0.22 / 365, 0) AS annual_holding_cost_impact_eur
FROM (
  SELECT 'Base' AS scenario, base_lt, 0.0 AS extra_days, daily_demand_eur FROM daily
  UNION ALL SELECT '+10% lead time', base_lt, base_lt * 0.10, daily_demand_eur FROM daily
  UNION ALL SELECT '+20% lead time', base_lt, base_lt * 0.20, daily_demand_eur FROM daily
) ORDER BY extra_days;

-- scenario by region (which regions hurt most)
CREATE OR REPLACE TABLE rpt_scenario_by_region AS
WITH reg AS (
  SELECT region, SUM(order_value_eur) AS spend, AVG(actual_lead_days) AS lt FROM erp_orders GROUP BY 1
)
SELECT region, ROUND(lt,1) AS base_lt, ROUND(spend/365,0) AS daily_demand_eur,
  ROUND(lt*0.10 * spend/365 * 0.22/365, 0) AS impact_10pct_eur,
  ROUND(lt*0.20 * spend/365 * 0.22/365, 0) AS impact_20pct_eur
FROM reg ORDER BY impact_20pct_eur DESC;
