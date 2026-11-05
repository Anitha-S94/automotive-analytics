-- Reorder-cycle logic (raw-material inventories, from the CV project description):
-- demand statistics per material from order history, safety stock with 95% service
-- level (z=1.65), reorder point = avg daily demand x lead time + safety stock.
CREATE OR REPLACE TABLE rpt_reorder_points AS
WITH daily AS (
  SELECT material, CAST(order_date AS DATE) AS d, SUM(qty_t) AS qty
  FROM fact_orders_clean GROUP BY 1, 2
),
stats AS (
  SELECT f.material,
         AVG(d.qty) AS avg_daily_demand, STDDEV_SAMP(d.qty) AS sigma_daily_demand,
         AVG(f.actual_lead_days) AS avg_lt, MAX(f.actual_lead_days) AS p95_lt,
         SUM(f.order_value_eur) AS annual_spend
  FROM fact_orders_clean f JOIN daily d USING (material) GROUP BY 1
)
SELECT material, ROUND(avg_daily_demand, 1) AS avg_daily_demand_t,
       ROUND(sigma_daily_demand, 1) AS demand_sigma_t,
       ROUND(avg_lt, 1) AS avg_lead_days, ROUND(p95_lt, 1) AS p95_lead_days,
       ROUND(1.65 * sigma_daily_demand * sqrt(p95_lt), 1) AS safety_stock_t,
       ROUND(avg_daily_demand * p95_lt + 1.65 * sigma_daily_demand * sqrt(p95_lt), 1) AS reorder_point_t,
       ROUND(annual_spend / 1e6, 1) AS annual_spend_m_eur,
       CASE WHEN p95_lt > avg_lt * 1.5 THEN 'VOLATILE LEAD TIME - raise safety stock'
            WHEN avg_lt > 40 THEN 'LONG LEAD - dual-source recommended'
            ELSE 'OK' END AS reorder_alert
FROM stats ORDER BY annual_spend DESC;
