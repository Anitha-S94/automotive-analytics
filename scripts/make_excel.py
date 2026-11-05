"""Excel workbook (XVERWEIS/XLOOKUP + Pivot + dynamic chart) built with openpyxl.
Output: excel/supply_chain_workbook.xlsx
Sheets: Orders (data), Suppliers (lookup), Dashboard (XLOOKUP live formulas + chart).
"""
import pandas as pd
from pathlib import Path
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
OUT = ROOT / "excel"
OUT.mkdir(exist_ok=True)

sup = pd.read_csv(PROC / "rpt_otif_by_supplier.csv")
rt = pd.read_csv(PROC / "rpt_route_bottlenecks.csv")
ov = pd.read_csv(PROC / "rpt_otif_overview.csv").iloc[0]

wb = Workbook()

# ---- Suppliers sheet (lookup source for XVERWEIS) ----
ws = wb.active
ws.title = "Suppliers"
cols = ["supplier_id", "region", "country", "orders", "otif_pct", "sla_target_pct", "sla_status", "lt_variance_days", "spend_eur"]
ws.append(cols)
for _, r in sup.iterrows():
    ws.append([r.supplier_id, r.region, r.country, int(r.orders), float(r.otif_pct),
               float(r.sla_target_pct), r.sla_status, float(r.lt_variance_days), float(r.spend_eur)])
t = Table(displayName="tblSuppliers", ref=f"A1:{get_column_letter(len(cols))}{len(sup)+1}")
t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
ws.add_table(t)

# ---- Routes sheet ----
ws2 = wb.create_sheet("Routes")
rcols = ["origin_port", "dest_port", "plant", "shipments", "otif_pct", "avg_lt", "lt_variance", "delayed_pct"]
ws2.append(rcols)
for _, r in rt.iterrows():
    ws2.append([r.origin_port, r.dest_port, r.plant, int(r.shipments), float(r.otif_pct),
                float(r.avg_lt), float(r.lt_variance), float(r.delayed_pct)])
t2 = Table(displayName="tblRoutes", ref=f"A1:{get_column_letter(len(rcols))}{len(rt)+1}")
t2.tableStyleInfo = TableStyleInfo(name="TableStyleMedium4", showRowStripes=True)
ws2.add_table(t2)

# ---- Dashboard sheet: XVERWEIS live lookups + KPI cells + chart ----
d = wb.create_sheet("Dashboard")
d["A1"] = "Supply Chain KPI Dashboard (Excel — XVERWEIS + Pivot-style tables + chart)"
d["A1"].font = d["A1"].font.copy(bold=True, size=14)
d["A3"] = "Overall OTIF %";        d["B3"] = float(ov.otif_pct)
d["A4"] = "Late %";                d["B4"] = float(ov.late_pct)
d["A5"] = "Avg lead-time variance (d)"; d["B5"] = float(ov.avg_lt_variance_days)
d["A6"] = "Total spend EUR";       d["B6"] = float(ov.total_spend_eur)
d["A8"] = "Supplier ID:";          d["B8"] = "SUP-001"
d["A9"] = "Region (XVERWEIS):";    d["B9"] = '=XVERWEIS(B8,Suppliers!A:A,Suppliers!B:B,"n/a")'
d["A10"] = "OTIF % (XVERWEIS):";   d["B10"] = '=XVERWEIS(B8,Suppliers!A:A,Suppliers!E:E,"n/a")'
d["A11"] = "SLA status (XVERWEIS):"; d["B11"] = '=XVERWEIS(B8,Suppliers!A:A,Suppliers!G:G,"n/a")'
d["A12"] = "Spend EUR (XVERWEIS):";  d["B12"] = '=XVERWEIS(B8,Suppliers!A:A,Suppliers!I:I,"n/a")'
d["A13"] = "Supplier name (XVERWEIS):"; d["B13"] = '=XVERWEIS(B8,Suppliers!A:A,Suppliers!A:A,"n/a")'
for r in range(3, 14):
    d[f"A{r}"].font = d[f"A{r}"].font.copy(bold=True)

# chart data block (top-10 bottleneck lanes) + dynamic bar chart
d["A16"] = "Lane"; d["B16"] = "OTIF %"
lanes = rt.sort_values("otif_pct").head(10)
for i, (_, r) in enumerate(lanes.iterrows()):
    d.cell(row=17 + i, column=1, value=f"{r.origin_port}→{r.dest_port}")
    d.cell(row=17 + i, column=2, value=float(r.otif_pct))
ch = BarChart(); ch.type = "bar"; ch.title = "10 bottleneck lanes by OTIF %"
ch.y_axis.title = "OTIF %"; ch.x_axis.title = "Lane"
data = Reference(d, min_col=2, min_row=16, max_row=16 + len(lanes))
cats = Reference(d, min_col=1, min_row=17, max_row=16 + len(lanes))
ch.add_data(data, titles_from_data=True); ch.set_categories(cats)
ch.height = 10; ch.width = 20
d.add_chart(ch, "D3")

# pivot-style summary block (manual pivot equivalent, labeled)
d["A30"] = "Pivot-style summary: OTIF by region"
d["A31"] = "Region"; d["B31"] = "Orders"; d["C31"] = "Avg OTIF %"
reg = sup.groupby("region").agg(orders=("orders", "sum"), otif=("otif_pct", "mean")).reset_index()
for i, (_, r) in enumerate(reg.iterrows()):
    d.cell(row=32 + i, column=1, value=r.region)
    d.cell(row=32 + i, column=2, value=int(r.orders))
    d.cell(row=32 + i, column=3, value=round(float(r.otif), 1))

wb.save(OUT / "supply_chain_workbook.xlsx")
print("wrote", OUT / "supply_chain_workbook.xlsx")
