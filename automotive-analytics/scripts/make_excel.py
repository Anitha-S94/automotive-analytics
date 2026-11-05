"""Phase 2: Excel staging workbooks (clean tables, standardized formats) for
Project A and Project B. Output: excel/automotive_financials.xlsx, automotive_sales_cx.xlsx
"""
import pandas as pd
from pathlib import Path
from openpyxl import Workbook
from openpyxl.chart import BarChart, LineChart, Reference
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.worksheet.table import Table, TableStyleInfo
from openpyxl.utils import get_column_letter

ROOT = Path(__file__).resolve().parent.parent
PROC = ROOT / "data" / "processed"
OUT = ROOT / "excel"
OUT.mkdir(exist_ok=True)

HDR = Font(bold=True, color="FFFFFF", size=12)
HFILL = PatternFill("solid", fgColor="1F4E79")
BIG = Font(bold=True, size=16, color="1F4E79")

def style_header(ws, ncols, row=1):
    for c in range(1, ncols + 1):
        cell = ws.cell(row=row, column=c)
        cell.font = HDR; cell.fill = HFILL
        cell.alignment = Alignment(horizontal="center")

def add_table(ws, name, ncols, nrows):
    t = Table(displayName=name, ref=f"A1:{get_column_letter(ncols)}{nrows + 1}")
    t.tableStyleInfo = TableStyleInfo(name="TableStyleMedium2", showRowStripes=True)
    ws.add_table(t)

# ---------- Project A workbook ----------
fin_y = pd.read_csv(PROC / "rpt_fin_yearly.csv")
fin_p = pd.read_csv(PROC / "rpt_fin_by_plant.csv")
log_y = pd.read_csv(PROC / "rpt_logistics_yearly.csv")
lt_m = pd.read_csv(PROC / "rpt_leadtime_by_material.csv")
fc = pd.read_csv(PROC / "rpt_forecast_2027.csv")

wb = Workbook()
ws = wb.active; ws.title = "README"
ws["A1"] = "Project A — Financials & Logistics (staging workbook)"; ws["A1"].font = BIG
ws["A3"] = "Synthetic data, 2022-2026 (5-year window). Sheets: Fin_Yearly, Fin_ByPlant, Logistics_Yearly, LeadTime_Material, Forecast_2027."
ws["A4"] = "Formats: dates YYYY-MM, currency EUR millions, percentages with 1 decimal."

ws = wb.create_sheet("Fin_Yearly")
cols = ["year","revenue_eur_m","cogs_eur_m","opex_eur_m","capex_eur_m","op_profit_eur_m","units","gross_margin_pct","op_margin_pct"]
ws.append(cols)
for _, r in fin_y.iterrows(): ws.append([int(r.year)] + [float(r[c]) for c in cols[1:]])
style_header(ws, len(cols)); add_table(ws, "tblFinYearly", len(cols), len(fin_y))
for rr in range(2, len(fin_y) + 2):
    for cc in range(2, 7): ws.cell(row=rr, column=cc).number_format = '#,##0.0'
    for cc in (8, 9): ws.cell(row=rr, column=cc).number_format = '0.0"%"'

ch = LineChart(); ch.title = "Revenue by year (EUR m)"; ch.style = 12
data = Reference(ws, min_col=2, min_row=1, max_row=len(fin_y) + 1)
cats = Reference(ws, min_col=1, min_row=2, max_row=len(fin_y) + 1)
ch.add_data(data, titles_from_data=True); ch.set_categories(cats); ch.height = 8; ch.width = 16
ws.add_chart(ch, "K2")

ws = wb.create_sheet("Fin_ByPlant")
cols = ["plant","year","revenue_eur_m","capex_eur_m","op_margin_pct"]
ws.append(cols)
for _, r in fin_p.iterrows(): ws.append([r.plant, int(r.year), float(r.revenue_eur_m), float(r.capex_eur_m), float(r.op_margin_pct)])
style_header(ws, len(cols)); add_table(ws, "tblFinPlant", len(cols), len(fin_p))

ws = wb.create_sheet("Logistics_Yearly")
cols = ["year","orders","avg_lead_days","lt_variance","otif_pct","spend_eur"]
ws.append(cols)
for _, r in log_y.iterrows(): ws.append([int(r.year), int(r.orders), float(r.avg_lead_days), float(r.lt_variance), float(r.otif_pct), float(r.spend_eur)])
style_header(ws, len(cols)); add_table(ws, "tblLogYearly", len(cols), len(log_y))

ws = wb.create_sheet("LeadTime_Material")
cols = ["material","orders","avg_lead_days","otif_pct","spend_eur"]
ws.append(cols)
for _, r in lt_m.iterrows(): ws.append([r.material, int(r.orders), float(r.avg_lead_days), float(r.otif_pct), float(r.spend_eur)])
style_header(ws, len(cols)); add_table(ws, "tblLeadMat", len(cols), len(lt_m))
ch = BarChart(); ch.type = "col"; ch.title = "Avg lead time by material (days)"
data = Reference(ws, min_col=3, min_row=1, max_row=len(lt_m) + 1)
cats = Reference(ws, min_col=1, min_row=2, max_row=len(lt_m) + 1)
ch.add_data(data, titles_from_data=True); ch.set_categories(cats); ch.height = 8; ch.width = 16
ws.add_chart(ch, "H2")

ws = wb.create_sheet("Forecast_2027")
cols = ["plant","forecast_month","forecast_revenue_eur_m"]
ws.append(cols)
for _, r in fc.iterrows(): ws.append([r.plant, r.forecast_month, float(r.forecast_revenue_eur_m)])
style_header(ws, len(cols)); add_table(ws, "tblForecast", len(cols), len(fc))

wb.save(OUT / "automotive_financials.xlsx")

# ---------- Project B workbook ----------
sal_y = pd.read_csv(PROC / "rpt_sales_yearly.csv")
rank = pd.read_csv(PROC / "rpt_region_rank.csv")
tree = pd.read_csv(PROC / "rpt_treemap_region.csv")
sent_r = pd.read_csv(PROC / "rpt_sentiment_by_region.csv")
sent_o = pd.read_csv(PROC / "rpt_sentiment_overall.csv").iloc[0]

wb = Workbook()
ws = wb.active; ws.title = "README"
ws["A1"] = "Project B — Regional Sales & Customer Sentiment (staging workbook)"; ws["A1"].font = BIG
ws["A3"] = "Synthetic data, 2022-2026. Sheets: Sales_Yearly, Region_Rank, Treemap_Region, Sentiment_Region."
ws["A5"] = "Overall sentiment:"; ws["B5"] = f"{sent_o.pct_positive}% positive, avg rating {sent_o.avg_rating} / 5 ({int(sent_o.reviews)} reviews)"

ws = wb.create_sheet("Sales_Yearly")
cols = ["year","units","revenue_eur_m","avg_asp_eur","yoy_growth_pct"]
ws.append(cols)
for _, r in sal_y.iterrows(): ws.append([int(r.year), int(r.units), float(r.revenue_eur_m), float(r.avg_asp_eur), None if pd.isna(r.yoy_growth_pct) else float(r.yoy_growth_pct)])
style_header(ws, len(cols)); add_table(ws, "tblSalesYearly", len(cols), len(sal_y))
ch = BarChart(); ch.type = "col"; ch.title = "Revenue by year (EUR m)"
data = Reference(ws, min_col=3, min_row=1, max_row=len(sal_y) + 1)
cats = Reference(ws, min_col=1, min_row=2, max_row=len(sal_y) + 1)
ch.add_data(data, titles_from_data=True); ch.set_categories(cats); ch.height = 8; ch.width = 16
ws.add_chart(ch, "H2")

ws = wb.create_sheet("Region_Rank")
cols = ["region","year","revenue_eur_m","revenue_rank"]
ws.append(cols)
for _, r in rank.iterrows(): ws.append([r.region, int(r.year), float(r.revenue_eur_m), int(r.revenue_rank)])
style_header(ws, len(cols)); add_table(ws, "tblRegionRank", len(cols), len(rank))

ws = wb.create_sheet("Treemap_Region")
cols = ["region","revenue_eur_m","revenue_share_pct"]
ws.append(cols)
for _, r in tree.iterrows(): ws.append([r.region, float(r.revenue_eur_m), float(r.revenue_share_pct)])
style_header(ws, len(cols)); add_table(ws, "tblTreemap", len(cols), len(tree))

ws = wb.create_sheet("Sentiment_Region")
cols = ["region","reviews","avg_rating","pct_positive","avg_sentiment_score"]
ws.append(cols)
for _, r in sent_r.iterrows(): ws.append([r.region, int(r.reviews), float(r.avg_rating), float(r.pct_positive), float(r.avg_sentiment_score)])
style_header(ws, len(cols)); add_table(ws, "tblSentiment", len(cols), len(sent_r))

wb.save(OUT / "automotive_sales_cx.xlsx")
print("wrote", [p.name for p in OUT.glob("automotive_*.xlsx")])
