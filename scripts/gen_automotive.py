"""Project: End-to-End Automotive Analytics Platforms — synthetic RAW data.

Project A (Financials & Logistics): monthly plant financials + logistics orders, 2022-01..2026-10.
Project B (Sales & CX): regional sales + free-text customer reviews + nested JSON raw sources.
All synthetic, fixed seeds.
"""
import json
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(11)

MONTHS = pd.date_range("2022-01-01", "2026-10-01", freq="MS")
PLANTS = ["Stuttgart", "Zwickau", "Leipzig", "Sao Jose dos Campos", "Chattanooga"]
REGIONS = ["DACH", "EU-West", "EU-East", "NAFTA", "APAC", "Rest of World"]
MATERIALS = ["Steel", "Aluminum", "Copper", "Rubber", "Plastics", "Semiconductors"]

# ---------- Project A: financials (monthly per plant) ----------
rows = []
for p in PLANTS:
    base = {"Stuttgart": 4200, "Zwickau": 2600, "Leipzig": 2100, "Sao Jose dos Campos": 1400, "Chattanooga": 1700}[p]
    growth = rng.uniform(0.02, 0.055)          # annual growth rate
    for i, m in enumerate(MONTHS):
        seasonal = 1 + 0.08 * np.sin(2 * np.pi * (m.month - 3) / 12)
        rev = base * (1 + growth) ** (i / 12) * seasonal * rng.normal(1, 0.03)
        cogs = rev * rng.uniform(0.58, 0.66)
        opex = rev * rng.uniform(0.12, 0.16)
        capex = rev * rng.uniform(0.04, 0.09) * (1.6 if m.month in (3, 9) else 1.0)
        rows.append({"plant": p, "month": m.date().isoformat()[:7], "revenue_eur_m": round(rev, 1),
                     "cogs_eur_m": round(cogs, 1), "opex_eur_m": round(opex, 1), "capex_eur_m": round(capex, 1),
                     "units_sold": int(rev * rng.uniform(38, 46))})
fin = pd.DataFrame(rows)
fin["gross_margin_pct"] = ((fin.revenue_eur_m - fin.cogs_eur_m) / fin.revenue_eur_m * 100).round(1)
fin["op_profit_eur_m"] = (fin.revenue_eur_m - fin.cogs_eur_m - fin.opex_eur_m - fin.capex_eur_m).round(1)
fin.to_parquet(RAW / "financials_monthly.parquet", index=False)
fin.to_csv(RAW / "financials_monthly.csv", index=False)

# ---------- Project A: logistics orders ----------
N = 30_000
od = rng.choice(MONTHS, N) + pd.to_timedelta(rng.integers(0, 28, N), unit="D")
sel_plant = rng.choice(PLANTS, N)
mat = rng.choice(MATERIALS, N)
base_lt = {"Steel": 21, "Aluminum": 28, "Copper": 35, "Rubber": 18, "Plastics": 14, "Semiconductors": 60}[mat[0]] if False else None
lt_map = {"Steel": 21, "Aluminum": 28, "Copper": 35, "Rubber": 18, "Plastics": 14, "Semiconductors": 60}
base = np.array([lt_map[m] for m in mat])
promised = np.clip(base + rng.normal(0, 2, N), 7, 90).round(0)
actual = np.clip(base * rng.uniform(0.85, 1.0, N) + rng.gamma(1.4, 1.0, N)
                 + (rng.random(N) < 0.05) * rng.uniform(4, 12, N), 5, 150).round(0)
qty = rng.integers(100, 20000, N)
price = {"Steel": 0.9, "Aluminum": 2.6, "Copper": 8.5, "Rubber": 3.1, "Plastics": 2.2, "Semiconductors": 45.0}
unit = np.array([price[m] for m in mat]) * rng.uniform(0.95, 1.15, N)
orders = pd.DataFrame({
    "order_id": [f"LO-{i:06d}" for i in range(1, N + 1)],
    "order_date": pd.Series(od).dt.date.astype(str),
    "plant": sel_plant, "material": mat,
    "promised_lead_days": promised, "actual_lead_days": actual,
    "qty_kg": qty, "unit_price_eur_kg": unit.round(3),
    "order_value_eur": (qty * unit).round(0),
    "late": actual > promised, "in_full": rng.random(N) > 0.04,
})
orders["otif"] = (~orders.late) & orders.in_full
orders.to_parquet(RAW / "logistics_orders.parquet", index=False)
orders.to_csv(RAW / "logistics_orders.csv", index=False)

# ---------- Project B: regional sales ----------
srows = []
for r in REGIONS:
    base_u = {"DACH": 95000, "EU-West": 130000, "EU-East": 70000, "NAFTA": 150000, "APAC": 110000, "Rest of World": 45000}[r]
    g = rng.uniform(0.01, 0.06)
    for i, m in enumerate(MONTHS):
        seasonal = 1 + 0.12 * np.sin(2 * np.pi * (m.month - 2) / 12)   # Q1 strong
        u = base_u * (1 + g) ** (i / 12) * seasonal * rng.normal(1, 0.04)
        asp = rng.uniform(28000, 46000) * (1 + 0.02 * i / 12)
        srows.append({"region": r, "month": m.date().isoformat()[:7], "units": int(u),
                      "asp_eur": round(asp, 0), "revenue_eur_m": round(u * asp / 1e6, 1)})
sales = pd.DataFrame(srows)
sales.to_parquet(RAW / "regional_sales.parquet", index=False)
sales.to_csv(RAW / "regional_sales.csv", index=False)

# ---------- Project B: raw unstructured sources ----------
POS = ["excellent", "great", "love", "reliable", "comfortable", "smooth", "impressive", "happy", "perfect", "recommend"]
NEG = ["poor", "terrible", "broke", "delay", "rude", "uncomfortable", "noise", "issue", "problem", "disappointed", "leak", "fault"]
reviews = []
for i in range(5000):
    r = rng.choice(REGIONS)
    rating = rng.integers(1, 6)
    if rating >= 4:
        words = rng.choice(POS, rng.integers(3, 7)) .tolist() if hasattr(rng.choice(POS, rng.integers(3, 7)), "tolist") else list(rng.choice(POS, rng.integers(3, 7)))
        words = [str(w) for w in words] + ["vehicle", "driving"]
    elif rating == 3:
        words = [str(w) for w in rng.choice(POS + NEG, rng.integers(2, 5))] + ["okay", "average"]
    else:
        words = [str(w) for w in rng.choice(NEG, rng.integers(3, 7))] + ["car", "service"]
    rng.shuffle(words)
    reviews.append({"review_id": f"RV-{i:05d}", "region": r,
                    "review_date": str(pd.Timestamp(rng.choice(MONTHS)) + pd.Timedelta(days=int(rng.integers(0, 28)))).split()[0],
                    "rating": int(rating), "text": " ".join(words) + "."})
with open(RAW / "reviews.jsonl", "w") as f:
    for rv in reviews:
        f.write(json.dumps(rv) + "\n")

# nested JSON machine/supplier logs (unstructured)
logs = []
for i in range(1200):
    logs.append({"event_id": f"EV-{i:05d}", "ts": str(pd.Timestamp(rng.choice(MONTHS)).date()),
                 "payload": {"plant": str(rng.choice(PLANTS)),
                             "line": int(rng.integers(1, 9)),
                             "metrics": {"downtime_min": float(rng.gamma(2, 8)), "units": int(rng.integers(50, 400))},
                             "tags": [str(t) for t in rng.choice(["maintenance", "supply", "quality"], 2)]}})
with open(RAW / "machine_logs.json", "w") as f:
    json.dump(logs, f)

# free-text supplier notes (messy strings to parse)
notes = []
for i in range(400):
    mat = rng.choice(MATERIALS)
    delay = int(rng.integers(0, 20))
    port = rng.choice(["Hamburg", "Shanghai", "Santos", "Houston", "Gdansk"])
    notes.append({"note_id": f"SN-{i:04d}",
                  "text": f"Shipment {mat.lower()} via {port}: delayed {delay} days; qty ok, price +{rng.integers(1,9)}%; note# {i}"})
with open(RAW / "supplier_notes.json", "w") as f:
    json.dump(notes, f)

print(f"financials={len(fin)} logistics={len(orders)} sales={len(sales)} reviews={len(reviews)} logs={len(logs)} notes={len(notes)}")
print("fin years:", sorted(fin.month.str[:4].unique()))
