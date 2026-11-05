-- Project B (Sales & CX): regional sales, rank shifts (ribbon), sentiment KPIs.

CREATE OR REPLACE TABLE rpt_sales_yearly AS
SELECT year, SUM(units) AS units, SUM(revenue_eur_m) AS revenue_eur_m,
  ROUND(AVG(asp_eur),0) AS avg_asp_eur,
  ROUND(100.0*(SUM(revenue_eur_m)/LAG(SUM(revenue_eur_m)) OVER (ORDER BY year)-1),1) AS yoy_growth_pct
FROM fact_sales GROUP BY 1 ORDER BY 1;

CREATE OR REPLACE TABLE rpt_sales_by_region AS
SELECT region, year, SUM(units) AS units, SUM(revenue_eur_m) AS revenue_eur_m, ROUND(AVG(asp_eur),0) AS asp_eur
FROM fact_sales GROUP BY 1,2 ORDER BY region, year;

-- ribbon chart data: revenue rank per region per year (rank shifts over time)
CREATE OR REPLACE TABLE rpt_region_rank AS
SELECT region, year, revenue_eur_m,
  RANK() OVER (PARTITION BY year ORDER BY revenue_eur_m DESC) AS revenue_rank
FROM (SELECT region, year, SUM(revenue_eur_m) AS revenue_eur_m FROM fact_sales GROUP BY 1,2);

-- treemap data: share of revenue by region (latest year)
CREATE OR REPLACE TABLE rpt_treemap_region AS
SELECT region, revenue_eur_m,
  ROUND(100.0*revenue_eur_m / SUM(revenue_eur_m) OVER (), 1) AS revenue_share_pct
FROM (SELECT region, SUM(revenue_eur_m) AS revenue_eur_m FROM fact_sales WHERE year = (SELECT MAX(year) FROM fact_sales) GROUP BY 1)
ORDER BY revenue_eur_m DESC;

-- sentiment KPIs by region + overall
CREATE OR REPLACE TABLE rpt_sentiment_overall AS
SELECT COUNT(*) AS reviews, ROUND(AVG(rating),2) AS avg_rating,
  ROUND(100.0*SUM(CASE WHEN sentiment='Positive' THEN 1 ELSE 0 END)/COUNT(*),1) AS pct_positive,
  ROUND(100.0*SUM(CASE WHEN sentiment='Negative' THEN 1 ELSE 0 END)/COUNT(*),1) AS pct_negative,
  ROUND(AVG(sentiment_score),2) AS avg_sentiment_score
FROM rev_raw;

CREATE OR REPLACE TABLE rpt_sentiment_by_region AS
SELECT region, COUNT(*) AS reviews, ROUND(AVG(rating),2) AS avg_rating,
  ROUND(100.0*SUM(CASE WHEN sentiment='Positive' THEN 1 ELSE 0 END)/COUNT(*),1) AS pct_positive,
  ROUND(AVG(sentiment_score),2) AS avg_sentiment_score
FROM rev_raw GROUP BY 1 ORDER BY pct_positive DESC;

CREATE OR REPLACE TABLE rpt_sentiment_by_year AS
SELECT EXTRACT(YEAR FROM review_date::DATE)::INT AS year, COUNT(*) AS reviews,
  ROUND(100.0*SUM(CASE WHEN sentiment='Positive' THEN 1 ELSE 0 END)/COUNT(*),1) AS pct_positive,
  ROUND(AVG(rating),2) AS avg_rating
FROM rev_raw GROUP BY 1 ORDER BY 1;
