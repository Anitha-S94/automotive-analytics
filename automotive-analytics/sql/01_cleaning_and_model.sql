-- Phase 3: SQL cleaning & transformation.
-- Dedup with ROW_NUMBER() PARTITION BY, 5-year rolling window view, DQ gates, star schema.

CREATE OR REPLACE TABLE fin_raw AS SELECT * FROM read_csv('data/parsed/financials_monthly.csv', header=true);
CREATE OR REPLACE TABLE log_raw AS SELECT * FROM read_csv('data/parsed/logistics_orders.csv', header=true);
CREATE OR REPLACE TABLE sales_raw AS SELECT * FROM read_csv('data/parsed/regional_sales.csv', header=true);
CREATE OR REPLACE TABLE rev_raw AS SELECT * FROM read_csv('data/parsed/reviews_scored.csv', header=true);
CREATE OR REPLACE TABLE notes_raw AS SELECT * FROM read_csv('data/parsed/supplier_notes_parsed.csv', header=true);
CREATE OR REPLACE TABLE mach_raw AS SELECT * FROM read_csv('data/parsed/machine_events.csv', header=true);

-- DQ: duplicates by natural key, removed via ROW_NUMBER() PARTITION BY
CREATE OR REPLACE TABLE dq_dup_fin AS
SELECT month, plant, COUNT(*) cnt FROM fin_raw GROUP BY 1,2 HAVING COUNT(*) > 1;
CREATE OR REPLACE TABLE dq_dup_orders AS
SELECT order_id, COUNT(*) cnt FROM log_raw GROUP BY 1 HAVING COUNT(*) > 1;

CREATE OR REPLACE TABLE fin_clean AS
SELECT * FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY month, plant ORDER BY revenue_eur_m DESC) rn FROM fin_raw) WHERE rn = 1;
CREATE OR REPLACE TABLE orders_clean AS
SELECT * FROM (SELECT *, ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY actual_lead_days) rn FROM log_raw) WHERE rn = 1;

-- 5-year rolling historical window view (strictly last 5 years from max date)
CREATE OR REPLACE VIEW v_fin_5y AS
SELECT * FROM fin_clean WHERE month >= (SELECT CAST(MAX(month::DATE) - INTERVAL 5 YEAR AS VARCHAR) FROM fin_clean);
CREATE OR REPLACE VIEW v_orders_5y AS
SELECT * FROM orders_clean WHERE order_date >= (SELECT MAX(order_date) - INTERVAL 5 YEAR FROM orders_clean);
CREATE OR REPLACE VIEW v_sales_5y AS
SELECT * FROM sales_raw WHERE month >= (SELECT CAST(MAX(month::DATE) - INTERVAL 5 YEAR AS VARCHAR) FROM sales_raw);

-- Star schema: dim_date, dim_plant, dim_region, dim_material + facts
CREATE OR REPLACE TABLE dim_date AS
SELECT DISTINCT month AS month_key, substr(month,1,4)::INT AS year, substr(month,6,2)::INT AS month_num,
  CASE WHEN substr(month,6,2)::INT IN (12,1,2) THEN 'Winter' WHEN substr(month,6,2)::INT IN (3,4,5) THEN 'Spring'
       WHEN substr(month,6,2)::INT IN (6,7,8) THEN 'Summer' ELSE 'Autumn' END AS season
FROM fin_clean;
CREATE OR REPLACE TABLE dim_plant AS SELECT DISTINCT plant FROM fin_clean;
CREATE OR REPLACE TABLE dim_region AS SELECT DISTINCT region FROM sales_raw;
CREATE OR REPLACE TABLE dim_material AS SELECT DISTINCT material FROM log_raw;

CREATE OR REPLACE TABLE fact_financials AS
SELECT f.*, d.year FROM fin_clean f JOIN dim_date d ON d.month_key = f.month;
CREATE OR REPLACE TABLE fact_logistics AS
SELECT o.*, EXTRACT(YEAR FROM o.order_date)::INT AS year FROM orders_clean o;
CREATE OR REPLACE TABLE fact_sales AS
SELECT s.*, d.year FROM sales_raw s JOIN dim_date d ON d.month_key = s.month;

-- DQ gate summary
CREATE OR REPLACE TABLE rpt_data_quality AS
SELECT 'dup_financials' AS check, COUNT(*) violations FROM dq_dup_fin
UNION ALL SELECT 'dup_orders', COUNT(*) FROM dq_dup_orders
UNION ALL SELECT 'fin_rows_raw', COUNT(*) FROM fin_raw
UNION ALL SELECT 'fin_rows_clean', COUNT(*) FROM fin_clean
UNION ALL SELECT 'orders_rows_raw', COUNT(*) FROM log_raw
UNION ALL SELECT 'orders_rows_clean', COUNT(*) FROM orders_clean;
