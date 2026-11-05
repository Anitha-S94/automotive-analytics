-- Maintenance scheduling logic: accumulated high-stress load hours per node
CREATE OR REPLACE TABLE rpt_stress_nodes AS
WITH stress AS (
  SELECT cable_id, substation, location, voltage_kv, capacity_mw,
    SUM(CASE WHEN utilization_pct > 90 THEN 1 ELSE 0 END) AS high_load_hours,
    SUM(CASE WHEN utilization_pct > 100 THEN 1 ELSE 0 END) AS overload_hours,
    SUM(CASE WHEN utilization_pct > 90 AND storm THEN 1 ELSE 0 END) AS storm_stress_hours,
    AVG(utilization_pct) AS avg_util
  FROM energy_hourly GROUP BY 1,2,3,4,5
)
SELECT *,
  high_load_hours + overload_hours * 3 AS stress_index,
  CASE WHEN overload_hours > 20 OR high_load_hours > 400 THEN 'CRITICAL - inspect connectors'
       WHEN high_load_hours > 200 THEN 'HIGH - schedule visual inspection'
       WHEN high_load_hours > 80 THEN 'MEDIUM - monitor'
       ELSE 'LOW' END AS maintenance_priority,
  date_trunc('month', (SELECT MIN(timestamp) FROM energy_hourly)) AS window_start,
  date_trunc('month', (SELECT MAX(timestamp) FROM energy_hourly)) AS window_end
FROM stress ORDER BY stress_index DESC;

-- monthly stress accumulation for the forecast view
CREATE OR REPLACE TABLE rpt_monthly_stress AS
SELECT cable_id, date_trunc('month', timestamp) AS month,
  SUM(CASE WHEN utilization_pct > 90 THEN 1 ELSE 0 END) AS high_load_hours,
  SUM(CASE WHEN utilization_pct > 100 THEN 1 ELSE 0 END) AS overload_hours,
  ROUND(AVG(utilization_pct),1) AS avg_util
FROM energy_hourly GROUP BY 1,2 ORDER BY cable_id, month;
