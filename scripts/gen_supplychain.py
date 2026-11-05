"""Synthetic ERP supply-chain dataset for PFISTERER-style global logistics.

Tables:
  data/raw/lme_metal_prices.csv   daily copper/aluminum index (synthetic, USD/t)
  data/raw/suppliers.csv          40 suppliers across regions
  data/raw/erp_orders.parquet     ~60k purchase-order lines, 2025-01..2026-10
"""
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)
rng = np.random.default_rng(7)

# ---------- LME-style metal price index ----------
days = pd.date_range("2024-11-01", "2026-10-31", freq="D")
n = len(days)
trend = np.linspace(0, 1, n)
copper = 8200 + 1800 * trend + 500 * np.sin(2 * np.pi * np.arange(n) / 365) + rng.normal(0, 90, n).cumsum() * 0.3
alum = 2300 + 420 * trend + 120 * np.sin(2 * np.pi * np.arange(n) / 250 + 1) + rng.normal(0, 25, n).cumsum() * 0.3
lme = pd.DataFrame({"date": days.date, "copper_usd_t": copper.round(0), "aluminum_usd_t": alum.round(0)})
lme.to_csv(RAW / "lme_metal_prices.csv", index=False)

# ---------- suppliers ----------
regions = {"EU": 14, "Asia-Pacific": 14, "Americas": 8, "Middle East": 4}
materials = ["Copper rod", "Aluminum conductor", "Silicone rubber", "Epoxy resin", "HV components", "Steel hardware"]
suppliers = []
i = 0
for region, cnt in regions.items():
    for _ in range(cnt):
        i += 1
        base_lt = {"EU": 18, "Asia-Pacific": 42, "Americas": 30, "Middle East": 35}[region]
        suppliers.append({
            "supplier_id": f"SUP-{i:03d}", "supplier_name": f"Supplier {i:03d} ({region})",
            "region": region, "primary_material": materials[i % len(materials)],
            "base_lead_days": base_lt + rng.integers(-4, 6),
            "sla_otif_target": 0.95, "country": rng.choice(["DE", "PL", "CN", "IN", "VN", "US", "BR", "TR", "AE"]) if region == "EU" or True else "DE",
        })
sup = pd.DataFrame(suppliers)
sup.to_csv(RAW / "suppliers.csv", index=False)

# ---------- route table (origin port -> destination plant) ----------
routes = [
    ("Shanghai", "Hamburg"), ("Shanghai", "Nuremberg"), ("Shenzhen", "Hamburg"),
    ("Mumbai", "Hamburg"), ("Houston", "Nuremberg"), ("Sao Paulo", "Hamburg"),
    ("Gdansk", "Nuremberg"), ("Mersin", "Hamburg"), ("Busan", "Hamburg"), ("Verona", "Nuremberg"),
]
plants = {"Hamburg": 0.45, "Nuremberg": 0.40, "Other EU": 0.15}

# ---------- ERP orders ----------
N = 60_000
order_dates = pd.date_range("2025-01-01", "2026-10-15", freq="h")
od = rng.choice(order_dates, N)
od = pd.to_datetime(od) + pd.to_timedelta(rng.integers(0, 24, N), unit="h")
sel = rng.choice(len(sup), N, p=None)
route_idx = rng.integers(0, len(routes), N)

base_lt = sup.base_lead_days.values[sel] * rng.uniform(0.80, 0.95, N)  # actual beats quoted base
delay_extra = rng.gamma(shape=1.5, scale=0.45, size=N)
weather_port = rng.random(N) < 0.04
customs = rng.random(N) < 0.03
strike = rng.random(N) < 0.006
actual_lt = np.clip(base_lt + delay_extra + weather_port * rng.uniform(1.5, 5, N)
                    + customs * rng.uniform(1, 4, N) + strike * rng.uniform(6, 14, N), 3, 120).round(0)
promised_lt = np.clip(sup.base_lead_days.values[sel] + rng.normal(0, 1.2, N), 5, 90).round(0)

mat = sup.primary_material.values[sel]
unit_price = np.where(np.isin(mat, ["Copper rod"]), lme.copper_usd_t.mean() / 1000 * rng.uniform(1.05, 1.3, N),
              np.where(np.isin(mat, ["Aluminum conductor"]), lme.aluminum_usd_t.mean() / 1000 * rng.uniform(1.05, 1.35, N),
                       rng.uniform(40, 900, N))).round(2)
qty = rng.integers(50, 5000, N)

reason = np.where(actual_lt > promised_lt + 2,
                  np.select([strike > 0, customs > 0, weather_port > 0], ["Strike/lockout", "Customs delay", "Port congestion"],
                            default="Supplier delay"), "On time")

# LME index at order date
lme_idx = lme.set_index("date")
od_date = pd.Series(pd.to_datetime(od)).dt.date
cu = lme_idx.copper_usd_t.reindex(pd.to_datetime(od_date)).values
al = lme_idx.aluminum_usd_t.reindex(pd.to_datetime(od_date)).values

orders = pd.DataFrame({
    "order_id": [f"PO-{i:06d}" for i in range(1, N + 1)],
    "order_date": pd.Series(pd.to_datetime(od)).dt.date,
    "supplier_id": sup.supplier_id.values[sel],
    "material": mat,
    "origin_port": [routes[r][0] for r in route_idx],
    "dest_port": [routes[r][1] for r in route_idx],
    "plant": rng.choice(list(plants), N, p=list(plants.values())),
    "promised_lead_days": promised_lt, "actual_lead_days": actual_lt,
    "qty_t": qty, "unit_price_eur": unit_price,
    "order_value_eur": (qty * unit_price).round(0),
    "copper_index_usd_t": cu.round(0), "aluminum_index_usd_t": al.round(0),
    "delay_reason": reason,
    "late": actual_lt > promised_lt,
    "in_full": rng.random(N) > 0.035,   # 3.5% short-shipped
})
orders["otif"] = (~orders.late) & orders.in_full
orders.to_parquet(RAW / "erp_orders.parquet", index=False)

print(f"lme rows={len(lme)} suppliers={len(sup)} orders={len(orders):,} "
      f"OTIF={orders.otif.mean():.1%} late={orders.late.mean():.1%} avg_lt={orders.actual_lead_days.mean():.1f}d")
