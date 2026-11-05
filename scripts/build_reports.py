"""Run all SQL files against a DuckDB file and export every rpt_* / dq_* / agg_*
table to data/processed/*.parquet (+ CSV for Power BI ingestion)."""
import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "analytics.duckdb"
PROC = ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(DB)
con.execute("SET TimeZone='UTC'")
for f in sorted((ROOT / "sql").glob("*.sql")):
    print(f"running {f.name}")
    con.execute(f.read_text())

tables = [r[0] for r in con.execute(
    """SELECT table_name FROM information_schema.tables
       WHERE table_name LIKE 'rpt_%' OR table_name LIKE 'dq_%' OR table_name LIKE 'agg_%'
       ORDER BY 1""").fetchall()]
for t in tables:
    pq = PROC / f"{t}.parquet"
    csv = PROC / f"{t}.csv"
    con.execute(f"COPY {t} TO '{pq}' (FORMAT PARQUET)")
    con.execute(f"COPY {t} TO '{csv}' (HEADER, DELIMITER ',')")
    n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t}: {n} rows -> {pq.name}, {csv.name}")
con.close()
print("OK")
