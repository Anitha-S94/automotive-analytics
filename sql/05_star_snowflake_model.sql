-- Star schema (energy) + snowflake schema (supply chain) + ETL data-quality gates.
-- This is the relational model behind the Power BI datasets (see powerbi/BUILD_SPEC.md).

-- ============ ENERGY: STAR SCHEMA ============
-- dim_date
CREATE OR REPLACE TABLE dim_date AS
SELECT CAST(strftime(generate_series, '%Y%m%d') AS INTEGER) AS date_key,
       generate_series::DATE AS full_date,
       EXTRACT(YEAR FROM generate_series) AS year,
       EXTRACT(MONTH FROM generate_series) AS month,
       EXTRACT(DAY FROM generate_series) AS day,
       CASE WHEN EXTRACT(MONTH FROM generate_series) IN (12,1,2) THEN 'Winter'
            WHEN EXTRACT(MONTH FROM generate_series) IN (3,4,5) THEN 'Spring'
            WHEN EXTRACT(MONTH FROM generate_series) IN (6,7,8) THEN 'Summer'
            ELSE 'Autumn' END AS season,
       CAST(EXTRACT(DOW FROM generate_series) AS INTEGER) AS day_of_week,
       CAST(strftime(generate_series, '%H') AS INTEGER) AS hour_of_day
FROM generate_series(TIMESTAMP '2025-01-01', TIMESTAMP '2026-10-31 23:00', INTERVAL 1 HOUR) AS generate_series;

-- dim_cable (conformed dimension: substation attributes snowflaked out of the cable)
CREATE OR REPLACE TABLE dim_location AS
SELECT DISTINCT location, MAX(voltage_kv) AS platform_kv FROM energy_hourly GROUP BY 1;

CREATE OR REPLACE TABLE dim_cable AS
SELECT DISTINCT cable_id, substation, location, voltage_kv, capacity_mw FROM energy_hourly;

-- fact table (grain: cable x hour)
CREATE OR REPLACE TABLE fact_load_hourly AS
SELECT CAST(strftime(timestamp, '%Y%m%d%H') AS BIGINT) AS datetime_key,
       cable_id, wind_speed_mps, ambient_temp_c, storm,
       cluster_generation_mw, cable_flow_mw, utilization_pct,
       (utilization_pct > 90) AS high_load_flag, (utilization_pct > 100) AS overload_flag
FROM energy_hourly;

-- ============ SUPPLY CHAIN: SNOWFLAKE SCHEMA ============
-- dim_region -> dim_country -> dim_supplier (normalized = snowflake)
CREATE OR REPLACE TABLE dim_region AS SELECT DISTINCT region FROM erp_orders;
CREATE OR REPLACE TABLE dim_country AS
SELECT DISTINCT country, region FROM erp_orders;
CREATE OR REPLACE TABLE dim_supplier AS
SELECT DISTINCT o.supplier_id, s.supplier_name, o.country, o.region,
       o.material AS primary_material, s.base_lead_days, s.sla_otif_target
FROM erp_orders o JOIN read_csv('data/raw/suppliers.csv', header=true) s USING (supplier_id);
CREATE OR REPLACE TABLE dim_route AS
SELECT DISTINCT origin_port, dest_port, plant FROM erp_orders;
CREATE OR REPLACE TABLE dim_material AS
SELECT DISTINCT material FROM erp_orders;

CREATE OR REPLACE TABLE fact_orders AS
SELECT order_id, order_date::DATE AS order_date,
       supplier_id, material, origin_port, dest_port, plant,
       promised_lead_days, actual_lead_days, qty_t, unit_price_eur, order_value_eur,
       delay_reason, late, in_full, otif FROM erp_orders;

-- ============ ETL DATA-QUALITY GATES (duplicate removal / quarantine) ============
-- DQ1: duplicate order_ids (must be 0; duplicates would double-count spend/OTIF)
CREATE OR REPLACE TABLE dq_duplicate_orders AS
SELECT order_id, COUNT(*) AS cnt FROM fact_orders GROUP BY 1 HAVING COUNT(*) > 1;

-- DQ2: orphan foreign keys (orders whose supplier is not in dim_supplier)
CREATE OR REPLACE TABLE dq_orphan_suppliers AS
SELECT DISTINCT f.supplier_id FROM fact_orders f
LEFT JOIN dim_supplier d USING (supplier_id) WHERE d.supplier_id IS NULL;

-- DQ3: negative/zero values and impossible lead times
CREATE OR REPLACE TABLE dq_invalid_rows AS
SELECT order_id, 'nonpositive_value' AS issue FROM fact_orders WHERE order_value_eur <= 0 OR qty_t <= 0
UNION ALL
SELECT order_id, 'impossible_lead_time' FROM fact_orders WHERE actual_lead_days < 1 OR actual_lead_days > 365
UNION ALL
SELECT cable_id || '@' || CAST(datetime_key AS VARCHAR), 'impossible_utilization'
FROM fact_load_hourly WHERE utilization_pct < 0 OR utilization_pct > 200;

-- clean fact used downstream (excludes DQ failures)
CREATE OR REPLACE TABLE fact_orders_clean AS
SELECT f.* FROM fact_orders f
WHERE NOT EXISTS (SELECT 1 FROM dq_duplicate_orders d WHERE d.order_id = f.order_id AND d.cnt > 1)
  AND NOT EXISTS (SELECT 1 FROM dq_invalid_rows i WHERE i.order_id = f.order_id);

CREATE OR REPLACE TABLE rpt_data_quality AS
SELECT 'duplicate_order_ids' AS check, COUNT(*) AS violations FROM dq_duplicate_orders
UNION ALL SELECT 'orphan_supplier_fks', COUNT(*) FROM dq_orphan_suppliers
UNION ALL SELECT 'invalid_rows', COUNT(*) FROM dq_invalid_rows
UNION ALL SELECT 'raw_order_rows', COUNT(*) FROM fact_orders
UNION ALL SELECT 'clean_order_rows', COUNT(*) FROM fact_orders_clean;
