// Power Query (M) — ETL for the SUPPLY CHAIN dataset in Power BI Desktop.
// Paste into Advanced Editor. Implements: duplicate removal, type casting, joins to
// dimension tables (suppliers), derived OTIF/late flags, narrow projection.
let
    Orders = Csv.Document(File.Contents("data/raw/erp_orders.csv"),[Delimiter=",", Encoding=65001]),
    #"Headers" = Table.PromoteHeaders(Orders, [PromoteAllScalars=true]),
    #"Types" = Table.TransformColumnTypes(#"Headers",{
        {"order_id", type text}, {"order_date", type date}, {"supplier_id", type text},
        {"material", type text}, {"origin_port", type text}, {"dest_port", type text},
        {"plant", type text}, {"promised_lead_days", Int64.Type}, {"actual_lead_days", Int64.Type},
        {"qty_t", Int64.Type}, {"unit_price_eur", type number}, {"order_value_eur", type number},
        {"delay_reason", type text}, {"late", type logical}, {"in_full", type logical}, {"otif", type logical}}),
    Suppliers = Csv.Document(File.Contents("data/raw/suppliers.csv"),[Delimiter=",", Encoding=65001]),
    #"Sup Headers" = Table.PromoteHeaders(Suppliers, [PromoteAllScalars=true]),
    #"Sup Types" = Table.TransformColumnTypes(#"Sup Headers",{
        {"supplier_id", type text}, {"supplier_name", type text}, {"region", type text},
        {"primary_material", type text}, {"base_lead_days", Int64.Type},
        {"sla_otif_target", type number}, {"country", type text}}),
    // DATA QUALITY gate: remove duplicate order_ids before any aggregation
    #"Dedup" = Table.NestedJoin(#"Types", {"order_id"}, Table.Distinct(#"Types", {"order_id"}), {"order_id"}, "dup", JoinKind.Inner),
    // JOIN to supplier dimension (star/snowflake model, sql/05)
    #"Merged Suppliers" = Table.NestedJoin(#"Dedup", {"supplier_id"}, #"Sup Types", {"supplier_id"}, "sup", JoinKind.LeftOuter),
    #"Expanded Suppliers" = Table.ExpandTableColumn(#"Merged Suppliers", "sup",
        {"supplier_name","region","country","base_lead_days","sla_otif_target"},
        {"supplier_name","region","country","supplier_base_lt","sla_otif_target"}),
    // Derived columns
    #"Added LT Variance" = Table.AddColumn(#"Expanded Suppliers", "lt_variance_days",
        each [actual_lead_days] - [promised_lead_days], Int64.Type),
    #"Added OTIF" = Table.AddColumn(#"Added LT Variance", "otif_calc",
        each not [late] and [in_full], type logical),
    // OPTIMIZATION: narrow projection
    #"Final" = Table.SelectColumns(#"Added OTIF",
        {"order_id","order_date","supplier_id","supplier_name","region","country","material",
         "origin_port","dest_port","plant","promised_lead_days","actual_lead_days","lt_variance_days",
         "qty_t","order_value_eur","delay_reason","late","in_full","otif_calc","sla_otif_target"})
in
    #"Final"
