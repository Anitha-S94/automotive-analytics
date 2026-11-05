// Power Query (M) — Automotive ETL for Power BI Desktop (Advanced Editor).
// Type enforcement + missing-value handling; keep the model narrow (star schema).
let
    Fin = Csv.Document(File.Contents("automotive-analytics/data/processed/rpt_fin_by_plant.csv"),[Delimiter=",", Encoding=65001]),
    #"F1" = Table.PromoteHeaders(Fin, [PromoteAllScalars=true]),
    #"F2" = Table.TransformColumnTypes(#"F1",{{"plant",type text},{"year",Int64.Type},{"revenue_eur_m",type number},{"capex_eur_m",type number},{"op_margin_pct",type number}}),
    #"F3" = Table.ReplaceValue(#"F2", null, 0, Replacer.ReplaceValue, {"revenue_eur_m","capex_eur_m","op_margin_pct"}),
    Log = Csv.Document(File.Contents("automotive-analytics/data/processed/rpt_logistics_yearly.csv"),[Delimiter=",", Encoding=65001]),
    #"L1" = Table.PromoteHeaders(Log, [PromoteAllScalars=true]),
    #"L2" = Table.TransformColumnTypes(#"L1",{{"year",Int64.Type},{"orders",Int64.Type},{"avg_lead_days",type number},{"lt_variance",type number},{"otif_pct",type number},{"spend_eur",type number}}),
    Sal = Csv.Document(File.Contents("automotive-analytics/data/processed/rpt_region_rank.csv"),[Delimiter=",", Encoding=65001]),
    #"S1" = Table.PromoteHeaders(Sal, [PromoteAllScalars=true]),
    #"S2" = Table.TransformColumnTypes(#"S1",{{"region",type text},{"year",Int64.Type},{"revenue_eur_m",type number},{"revenue_rank",Int64.Type}}),
    Sen = Csv.Document(File.Contents("automotive-analytics/data/processed/rpt_sentiment_by_region.csv"),[Delimiter=",", Encoding=65001]),
    #"N1" = Table.PromoteHeaders(Sen, [PromoteAllScalars=true]),
    #"N2" = Table.TransformColumnTypes(#"N1",{{"region",type text},{"reviews",Int64.Type},{"avg_rating",type number},{"pct_positive",type number},{"avg_sentiment_score",type number}})
in
    #"N2"  // load all four via separate queries in Desktop; this is the pattern for each
