"""Synthetic offshore wind generation + HVDC export-cable load dataset.

Simulates 8 offshore substations (OSS) x 2 export cables, hourly resolution,
2025-01-01 .. 2026-10-31. Weather (wind speed, temperature, storms) drives
farm generation; cable flow is a share of cluster output so some cables run
near capacity at peaks (connector stress).
"""
import numpy as np
import pandas as pd
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
OUT = ROOT / "data" / "raw" / "offshore_grid_hourly.parquet"

rng = np.random.default_rng(42)

SUBSTATIONS = [
    ("OSS-NorthSea-1", "Borkum", 320, 1200), ("OSS-NorthSea-2", "Borkum", 525, 2000),
    ("OSS-NorthSea-3", "Emden", 320, 900),  ("OSS-Baltic-1", "Kriegers Flak", 320, 900),
    ("OSS-Baltic-2", "Kriegers Flak", 525, 1400), ("OSS-NL-1", "Eemshaven", 320, 700),
    ("OSS-UK-1", "Blyth", 320, 1000),        ("OSS-FR-1", "Saint-Nazaire", 320, 800),
]
# cluster capacity (MW) per substation = sum of its cables
start = pd.Timestamp("2025-01-01")
end = pd.Timestamp("2026-10-31 23:00")
ts = pd.date_range(start, end, freq="h")
n = len(ts)
doy = ts.dayofyear.values
hour = ts.hour.values

# --- weather per substation (shared regional signal + local noise) ---
def weather(loc_idx):
    seasonal = 6.5 + 3.5 * np.sin(2 * np.pi * (doy - 30) / 365.0)  # winter windier
    diurnal = 0.6 * np.sin(2 * np.pi * (hour - 9) / 24.0)
    ws = np.clip(seasonal + diurnal + rng.normal(0, 1.6, n) + loc_idx * 0.15, 0.5, 28)
    temp = 10 + 8 * np.sin(2 * np.pi * (doy - 200) / 365.0) + rng.normal(0, 2.5, n)
    storm = (ws > 21) & (rng.random(n) < 0.75)
    return ws, temp, storm

cable_rows = []
sub_info = {}
for oss, loc, kv, cap in SUBSTATIONS:
    sub_info[oss] = (loc, kv, cap)

# one weather series per location
locs = sorted({v[0] for v in sub_info.values()})
wx = {loc: weather(i) for i, loc in enumerate(locs)}

cluster_mw = {}
for oss, (loc, kv, cap) in sub_info.items():
    cluster_mw[oss] = cluster_mw.get(oss, 0) + cap

for oss, (loc, kv, cap) in sub_info.items():
    ws, temp, storm = wx[loc]
    # power curve: cut-in 3, rated 12, cut-out 25 m/s
    cf = np.clip((ws - 3) / (12 - 3), 0, 1) ** 3
    cf = np.where(ws >= 25, 0.0, cf)
    cf *= np.where(storm & (rng.random(n) < 0.4), rng.uniform(0.2, 0.6, n), 1.0)  # storm derating
    gen = cluster_mw[oss] * cf * rng.normal(1.0, 0.03, n)
    gen = np.clip(gen, 0, cluster_mw[oss])
    # split cluster output across the platform's cables with a fixed share + noise
    peers = [o for o in sub_info if sub_info[o][0] == loc]
    share = cap / sum(sub_info[o][2] for o in peers)
    flow = gen * share * rng.normal(1.0, 0.02, n)
    flow = np.clip(flow, 0, cap * 1.12)  # occasional overload beyond rating
    cable_rows.append(pd.DataFrame({
        "timestamp": ts, "substation": oss, "location": loc, "voltage_kv": kv,
        "cable_id": f"{oss}-EXP-{kv}kV", "capacity_mw": cap,
        "wind_speed_mps": np.round(ws, 2), "ambient_temp_c": np.round(temp, 1),
        "storm": storm, "cluster_generation_mw": np.round(gen, 1),
        "cable_flow_mw": np.round(flow, 1),
    }))

df = pd.concat(cable_rows, ignore_index=True)
df["utilization_pct"] = (df.cable_flow_mw / df.capacity_mw * 100).round(2)
df["overload"] = df.utilization_pct > 100
df["near_capacity"] = df.utilization_pct > 90

OUT.parent.mkdir(parents=True, exist_ok=True)
df.to_parquet(OUT, index=False)
print(f"wrote {OUT} rows={len(df):,} cables={df.cable_id.nunique()} "
      f"overload_hours={int(df.overload.sum()):,} near_cap_hours={int(df.near_capacity.sum()):,}")
print(df.groupby("cable_id").utilization_pct.agg(["mean", "max"]).round(1).to_string())
