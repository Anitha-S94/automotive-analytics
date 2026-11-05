-- Load & utilization profiling: peaks by season, time of day, weather
CREATE OR REPLACE TABLE energy_hourly AS
SELECT * FROM read_parquet('data/raw/offshore_grid_hourly.parquet');

-- Seasonal + intraday profile per cable
CREATE OR REPLACE TABLE rpt_season_profile AS
SELECT cable_id, substation,
  CASE WHEN month(timestamp) IN (12,1,2) THEN 'Winter'
       WHEN month(timestamp) IN (3,4,5) THEN 'Spring'
       WHEN month(timestamp) IN (6,7,8) THEN 'Summer'
       ELSE 'Autumn' END AS season,
  AVG(utilization_pct) AS avg_util, MAX(utilization_pct) AS peak_util,
  AVG(cable_flow_mw) AS avg_flow_mw, MAX(cable_flow_mw) AS peak_flow_mw,
  SUM(near_capacity) AS near_cap_hours, SUM(overload) AS overload_hours
FROM energy_hourly GROUP BY 1,2,3 ORDER BY cable_id, season;

CREATE OR REPLACE TABLE rpt_hourly_profile AS
SELECT cable_id, CAST(hour(timestamp) AS INT) AS hour_of_day,
  AVG(utilization_pct) AS avg_util, MAX(utilization_pct) AS peak_util
FROM energy_hourly GROUP BY 1,2 ORDER BY cable_id, hour_of_day;

-- Peak-to-average ratio (PAR) per cable + weather-conditioned stress
CREATE OR REPLACE TABLE rpt_peak_to_avg AS
SELECT cable_id, capacity_mw,
  AVG(cable_flow_mw) AS avg_mw, MAX(cable_flow_mw) AS peak_mw,
  ROUND(MAX(cable_flow_mw)/NULLIF(AVG(cable_flow_mw),0), 2) AS peak_to_avg_ratio,
  ROUND(AVG(utilization_pct),1) AS avg_util_pct, ROUND(MAX(utilization_pct),1) AS max_util_pct,
  SUM(overload) AS overload_hours,
  ROUND(100.0*SUM(CASE WHEN storm THEN 1 ELSE 0 END)/COUNT(*),1) AS storm_share_pct
FROM energy_hourly GROUP BY 1,2 ORDER BY peak_to_avg_ratio DESC;

-- utilization distribution buckets per cable
CREATE OR REPLACE TABLE rpt_util_buckets AS
SELECT cable_id,
  SUM(utilization_pct < 50) AS lt50, SUM(utilization_pct BETWEEN 50 AND 75) AS b50_75,
  SUM(utilization_pct BETWEEN 75 AND 90) AS b75_90, SUM(utilization_pct BETWEEN 90 AND 100) AS b90_100,
  SUM(utilization_pct > 100) AS gt100
FROM energy_hourly GROUP BY 1 ORDER BY cable_id;
