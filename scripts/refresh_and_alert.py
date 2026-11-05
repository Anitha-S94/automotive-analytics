"""Automated refresh + alerting simulation (CV: 'Automatische Refreshes',
' automatisierte Benachrichtigungsmechanismen').

Runs the pipeline end-to-end, then evaluates alert rules and writes
alerts.json + appends to alerts.log. Exit code 1 if any CRITICAL alert fires
(so it can gate a scheduled refresh in Power BI Service / cron).
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
PY = [str(ROOT / "venv" / "bin" / "python")]

def run(script):
    r = subprocess.run(PY + [str(ROOT / "scripts" / script)],
                       capture_output=True, text=True, env={"PATH": "/usr/bin:/bin"})
    if r.returncode != 0:
        print(r.stdout[-2000:], r.stderr[-2000:]); sys.exit(2)
    return r.stdout

def main():
    run("build_reports.py")          # = the "refresh" of the semantic model
    alerts = []

    stress = pd.read_parquet(PROC / "rpt_stress_nodes.parquet")
    for _, r in stress.iterrows():
        if r.maintenance_priority.startswith("CRITICAL"):
            alerts.append({"severity": "CRITICAL", "rule": "connector_overload",
                           "cable": r.cable_id, "detail": f"{int(r.overload_hours)} overload h, stress {int(r.stress_index)}"})
        elif r.maintenance_priority.startswith("HIGH"):
            alerts.append({"severity": "WARNING", "rule": "high_stress_node",
                           "cable": r.cable_id, "detail": f"{int(r.high_load_hours)} h >90%"})

    otif = pd.read_parquet(PROC / "rpt_otif_overview.parquet").iloc[0]
    if otif.otif_pct < 90:
        alerts.append({"severity": "WARNING", "rule": "otif_below_90", "detail": f"OTIF {otif.otif_pct}%"})
    sup = pd.read_parquet(PROC / "rpt_otif_by_supplier.parquet")
    for _, r in sup[sup.sla_status == "BELOW SLA"].iterrows():
        alerts.append({"severity": "WARNING", "rule": "supplier_below_sla",
                       "supplier": r.supplier_id, "detail": f"OTIF {r.otif_pct}% < SLA {r.sla_target_pct}%"})

    risk = pd.read_parquet(PROC / "rpt_stockout_risk.parquet")
    for _, r in risk[risk.stockout_risk == "HIGH STOCKOUT RISK"].iterrows():
        alerts.append({"severity": "CRITICAL", "rule": "stockout_risk",
                       "supplier": r.supplier_id, "material": r.material,
                       "detail": f"{int(r.short_shipments)} short shipments, {int(r.severe_delays)} severe delays"})

    reorder = pd.read_parquet(PROC / "rpt_reorder_points.parquet")
    for _, r in reorder[reorder.reorder_alert != "OK"].iterrows():
        alerts.append({"severity": "WARNING", "rule": "reorder_alert",
                       "material": r.material, "detail": r.reorder_alert})

    dq = pd.read_parquet(PROC / "rpt_data_quality.parquet")
    viol = int(dq[dq.check.isin(["duplicate_order_ids", "orphan_supplier_fks", "invalid_rows"])].violations.sum())
    if viol > 0:
        alerts.append({"severity": "CRITICAL", "rule": "data_quality_violation", "detail": f"{viol} rows failed DQ gates"})

    rec = {"refreshed_at": datetime.now(timezone.utc).isoformat(), "alerts": alerts,
           "n_critical": sum(a["severity"] == "CRITICAL" for a in alerts),
           "n_warning": sum(a["severity"] == "WARNING" for a in alerts)}
    (ROOT / "alerts.json").write_text(json.dumps(rec, indent=2, default=str))
    with open(ROOT / "alerts.log", "a") as f:
        f.write(json.dumps(rec, default=str) + "\n")
    print(f"refresh OK | alerts: {rec['n_critical']} CRITICAL, {rec['n_warning']} WARNING")
    for a in alerts[:10]:
        print(" ", a["severity"], a["rule"], a.get("cable") or a.get("supplier") or a.get("material"), "-", a["detail"])
    return 1 if rec["n_critical"] else 0

if __name__ == "__main__":
    sys.exit(main())
