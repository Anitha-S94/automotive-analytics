# Methodology

All data is **synthetic**, generated deterministically (seeds 42 and 7) so the
project is fully reproducible offline. No real PFISTERER or third-party data.

## Use case 1 — Offshore grid load
- 8 export cables (320/525 kV) at 8 offshore substations, hourly, 2025-01-01 → 2026-10-31 (128,448 rows).
- Wind speed per location = seasonal + diurnal + AR noise; power curve with cut-in 3 m/s,
  rated 12 m/s, cut-out 25 m/s; storms (ws>21 m/s) derate output randomly.
- Cable flow = cluster generation × fixed share + noise, clipped at 112% of rating →
  realistic overload hours (923 h total across cables).
- Reports (DuckDB SQL): seasonal/hourly profiles, peak-to-average ratio, utilization
  buckets, maintenance stress index = high-load hours (>90%) + 3 × overload hours (>100%),
  priority classes CRITICAL/HIGH/MEDIUM/LOW.

## Use case 2 — Supply chain
- 60,000 ERP order lines over 40 suppliers in 4 regions, 10 port→plant lanes, 2025-01 → 2026-10.
- Lead time = supplier base (EU 18d, APAC 42d, Americas 30d, ME 35d) × 0.80–0.95 + gamma
  delay noise + port-congestion / customs / strike events. Promised LT = quoted base.
- OTIF = on-time (actual ≤ promised) AND in-full (3.5% short-ship rate). Result ≈ 89%.
- Synthetic LME-style index: copper & aluminum daily prices, 2024-11 → 2026-10, trend + seasonality + random walk.
- Scenario: extra pipeline inventory = extra lead days × daily demand value;
  annual holding-cost impact = extra inventory × 22% / yr.

## Assumptions
- Holding cost rate 22%/yr of inventory value; demand = total order value / 365.
- Storm threshold 21 m/s; stress thresholds 90% (high load) and 100% (overload).
- Currency EUR for spend; metal index in USD/t (LME-style).
