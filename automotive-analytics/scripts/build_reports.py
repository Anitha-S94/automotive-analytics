"""Run automotive SQL against DuckDB, export rpt_*/dq_* to data/processed (parquet+csv)."""
import duckdb
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB = ROOT / "data" / "analytics.duckdb"
PROC = ROOT / "data" / "processed"
PROC.mkdir(parents=True, exist_ok=True)

con = duckdb.connect(DB)
con.execute("PRAGMA threads=4")
for f in sorted((ROOT / "sql").glob("*.sql")):
    print("running", f.name)
    con.execute(f.read_text())

tables = [r[0] for r in con.execute(
    """SELECT table_name FROM information_schema.tables
       WHERE table_name LIKE 'rpt_%' OR table_name LIKE 'dq_%' ORDER BY 1""").fetchall()]
for t in tables:
    con.execute(f"COPY {t} TO '{PROC / (t + '.parquet')}' (FORMAT PARQUET)")
    con.execute(f"COPY {t} TO '{PROC / (t + '.csv')}' (HEADER, DELIMITER ',')")
    n = con.execute(f"SELECT COUNT(*) FROM {t}").fetchone()[0]
    print(f"  {t}: {n} rows")
con.close()
print("OK")
