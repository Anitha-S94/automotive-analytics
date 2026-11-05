// Power Query (M) — ETL for the ENERGY dataset in Power BI Desktop.
// Paste into: Power Query Editor -> Home -> Advanced Editor (replace existing).
// Mirrors scripts/gen_energy.py output cleaning + the star-schema load in sql/05.
let
    // 1. Source: raw parquet (or CSV export) from data/raw/
    Source = Csv.Document(File.Contents("data/raw/offshore_grid_hourly.csv"),[Delimiter=",", Encoding=65001, QuoteStyle=QuoteStyle.None]),
    // 2. Promote headers, set types (data cleaning / type casting)
    #"Promoted Headers" = Table.PromoteHeaders(Source, [PromoteAllScalars=true]),
    #"Changed Types" = Table.TransformColumnTypes(#"Promoted Headers",{
        {"timestamp", type datetime}, {"substation", type text}, {"location", type text},
        {"voltage_kv", Int64.Type}, {"cable_id", type text}, {"capacity_mw", type number},
        {"wind_speed_mps", type number}, {"ambient_temp_c", type number}, {"storm", type logical},
        {"cluster_generation_mw", type number}, {"cable_flow_mw", type number},
        {"utilization_pct", type number}, {"overload", type logical}, {"near_capacity", type logical}}),
    // 3. DATA QUALITY: remove exact duplicates (duplicate-removal gate from sql/05)
    #"Removed Duplicates" = Table.Distinct(#"Changed Types"),
    // 4. Derived columns: season + hour (replaces computed dim_date columns)
    #"Added Season" = Table.AddColumn(#"Removed Duplicates", "season", each
        if Date.Month([timestamp]) in {12,1,2} then "Winter"
        else if Date.Month([timestamp]) in {3,4,5} then "Spring"
        else if Date.Month([timestamp]) in {6,7,8} then "Summer" else "Autumn", type text),
    #"Added Hour" = Table.AddColumn(#"Added Season", "hour_of_day", each Date.Hour([timestamp]), Int64.Type),
    // 5. Derived flags used by the maintenance visuals
    #"Added Flags" = Table.AddColumn(#"Added Hour", "high_load_flag", each [utilization_pct] > 90, type logical),
    #"Added Overload" = Table.AddColumn(#"Added Flags", "overload_flag", each [utilization_pct] > 100, type logical),
    // 6. OPTIMIZATION: keep only columns the report uses (narrow projection before load)
    #"Kept Report Columns" = Table.SelectColumns(#"Added Overload",
        {"timestamp","cable_id","substation","location","capacity_mw","wind_speed_mps","ambient_temp_c",
         "storm","season","hour_of_day","cable_flow_mw","utilization_pct","high_load_flag","overload_flag"})
in
    #"Kept Report Columns"
