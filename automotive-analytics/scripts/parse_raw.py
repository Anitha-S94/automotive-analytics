"""Phase 1 parsing: flatten nested JSON logs + parse free-text supplier notes and
reviews into clean, simple tabular frames (data/parsed/)."""
import json
import re
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
PARSED = ROOT / "data" / "parsed"
PARSED.mkdir(parents=True, exist_ok=True)

# ---- flatten nested machine logs ----
logs = json.loads((RAW / "machine_logs.json").read_text())
flat = pd.DataFrame([{
    "event_id": e["event_id"], "date": e["ts"], "plant": e["payload"]["plant"],
    "line": e["payload"]["line"], "downtime_min": round(e["payload"]["metrics"]["downtime_min"], 1),
    "units_produced": e["payload"]["metrics"]["units"],
    "tag": ",".join(e["payload"]["tags"]),
} for e in logs])
flat.to_csv(PARSED / "machine_events.csv", index=False)

# ---- parse supplier notes (regex entity extraction + text cleaning) ----
notes = json.loads((RAW / "supplier_notes.json").read_text())
pat = re.compile(r"Shipment (\w+) via (\w+): delayed (\d+) days; qty ok, price \+(\d+)%")
rows = []
for n in notes:
    m = pat.search(n["text"])
    if m:
        rows.append({"note_id": n["note_id"], "material": m.group(1), "port": m.group(2),
                     "delay_days": int(m.group(3)), "price_increase_pct": int(m.group(4))})
notes_df = pd.DataFrame(rows)
notes_df.to_csv(PARSED / "supplier_notes_parsed.csv", index=False)

# ---- sentiment scoring on free-text reviews (simple lexicon) ----
POS = {"excellent","great","love","reliable","comfortable","smooth","impressive","happy","perfect","recommend"}
NEG = {"poor","terrible","broke","delay","rude","uncomfortable","noise","issue","problem","disappointed","leak","fault"}
reviews = [json.loads(l) for l in (RAW / "reviews.jsonl").read_text().splitlines() if l.strip()]
rows = []
for r in reviews:
    toks = set(re.findall(r"[a-z]+", r["text"].lower()))
    score = len(toks & POS) - len(toks & NEG)
    label = "Positive" if score > 0 else ("Negative" if score < 0 else "Neutral")
    rows.append({"review_id": r["review_id"], "region": r["region"], "review_date": r["review_date"],
                 "rating": r["rating"], "sentiment_score": score, "sentiment": label,
                 "text_clean": re.sub(r"\s+", " ", r["text"]).strip()})
rev = pd.DataFrame(rows)
rev.to_csv(PARSED / "reviews_scored.csv", index=False)

# ---- copy structured raws into parsed as clean CSVs for staging ----
for name in ["financials_monthly", "logistics_orders", "regional_sales"]:
    df = pd.read_parquet(RAW / f"{name}.parquet")
    df.to_csv(PARSED / f"{name}.csv", index=False)

print(f"parsed: machine_events={len(flat)} notes={len(notes_df)} reviews={len(rev)}")
print(rev.sentiment.value_counts().to_string())
