# Measures og parametre skabelonen skal bruge

Skabelonens faneblade bruger measures, en model ofte mangler (sidste måned, targets, afvigelser,
prisjustering), og tre parametre. Lav kun det, de valgte faneblade skal bruge (template.json → `fields`,
filtreret på faneblad), og som modellen ikke har. Navne: modellens konvention – snake_case i en
pipeline-power-bi-kørsel (`previous_month_sales`), ellers som modellens egne measures. Test hver ny measure
med DAX.

**Hvor de skal hen:**
- **En pipeline-power-bi-kørsel** (kørselsmappen har `choices.json` med `build`): tilføj measures til
  `build.measures[]` (mappe `Template`) og parametrene til `build.parameters[]` (pipeline-power-bi
  `references/build-spec.md`), og kør `node .claude\skills\pipeline-power-bi\scripts\rebuild.js runs\<run-id>`.
  Skriv dem aldrig i hånden i TMDL'en dér – næste rebuild ville fjerne dem.
- **Andre projekter:** powerbi-modeling-mcp (`measure_operations`, `table_operations` til parametrene),
  eller TMDL'en direkte med Desktop lukket (SKILL.md → "Uden powerbi-modeling-mcp").

`<Revenue>`, `<Orders>`, `<Profit>`, `<Returns>`, `<Customers>`, `<Cost>` er de measures, der er koblet til
skabelonens `Total Revenue`, `Total Orders` …; `<Date>` er datotabellens datokolonne.

> Brug **ikke** variabelnavnet `LastDate` – det kolliderer med DAX-funktionen `LASTDATE`.

## Forrige måned (Exec: de tre månedlige KPI'er; Product: targets)
```dax
previous_month_sales  = CALCULATE ( [<Revenue>], DATEADD ( <Date>, -1, MONTH ) )
previous_month_orders = CALCULATE ( [<Orders>], DATEADD ( <Date>, -1, MONTH ) )
previous_month_<x>    = CALCULATE ( [<Returns>], DATEADD ( <Date>, -1, MONTH ) )   -- den tredje månedlige KPI
previous_month_<p>    = CALCULATE ( [<Profit>], DATEADD ( <Date>, -1, MONTH ) )    -- til profit-target
```
Format som basis-measuren. KPI-visuals sammenligner seneste måned med måneden før; slutter dataene midt i
en måned, så sæt KPI'ens datofilter til hele måneder (`is_complete_month = TRUE` på datotabellen, når den
har den).

## Targets (Product Detail: de tre målere)
Brug modellens egne targets, når den har dem (en targettabel: `target_revenue`). Ellers skabelonens regel –
sidste måned plus en vækst, brugeren bekræfter (skabelonen: 10 %):
```dax
order_target   = [previous_month_orders] * ( 1 + 0.10 )
sales_target   = [previous_month_sales] * ( 1 + 0.10 )
profit_target  = [previous_month_<p>] * ( 1 + 0.10 )
order_target_gap  = [<Orders>] - [order_target]
sales_target_gap  = [<Revenue>] - [sales_target]       -- eller - [target_revenue]
profit_target_gap = [<Profit>] - [profit_target]
```

## Prisjustering (Product Detail: profittrend med what-if-skyder)
Parameter (pipeline-spec):
```json
{ "kind": "whatIf", "name": "price_adjustment_pct", "min": -1, "max": 1, "step": 0.1, "default": 0, "format": "0%" }
```
Den laver tabellen `price_adjustment_pct` (én kolonne, GENERATESERIES) og measuren
`price_adjustment_pct_value`. Derefter:
```dax
adjusted_sales        = [<Revenue>] * ( 1 + [price_adjustment_pct_value] )
adjusted_gross_margin = [adjusted_sales] - [<Cost>]
```
Kobl `Price Adjustment (%)[Price Adjustment (%)]` → `price_adjustment_pct[price_adjustment_pct]` og
`Measure Table[Adjusted Profit]` → `adjusted_gross_margin`.

## Feltparametre (Product og Customer Detail: "hvilken measure ser jeg")
```json
{ "kind": "fields", "name": "product_metric_selection", "items": [ { "label": "Orders", "measure": "orders" },
  { "label": "Revenue", "measure": "total_sales" }, { "label": "Profit", "measure": "gross_margin" },
  { "label": "Margin %", "measure": "gross_margin_pct" } ] }
{ "kind": "fields", "name": "customer_metric_selection", "items": [ { "label": "Customers", "measure": "customers" },
  { "label": "Revenue per customer", "measure": "sales_per_customer" } ] }
```
Hver laver en tabel med `<navn>` (sliceren), `<navn>_fields` og `<navn>_order` (skjulte). Kobl
`Product Metric Selection[Product Metric Selection]` → `product_metric_selection[product_metric_selection]`
og `… Fields` → `product_metric_selection[product_metric_selection_fields]` (det samme for Customer). Uden
for en pipeline-kørsel: lav dem i Desktop (Modellering → Ny parameter → Felter) eller som beregnede tabeller
med `NAMEOF`, som skabelonens kilderapport gør.

## Kunder (Customer Detail)
```dax
customers          = DISTINCTCOUNT ( <Fact>[<kundenøgle>] )
sales_per_customer = DIVIDE ( [<Revenue>], [customers] )
```

## Formater
Behold modellens formater; skabelonens visuals sætter selv visningsenheder (K, M) som kilderapporten.
Rater `0.0%`, beløb med modellens valuta (`\$#,0`).
