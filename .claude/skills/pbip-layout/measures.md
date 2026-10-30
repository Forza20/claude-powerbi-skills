# DAX-skabeloner til layoutet

Erstat `<Fact>`, `<DateTable>`, `<Base>` osv. med modellens navne. Opret i modellens
measure-tabel; hjælpe-measures i display folder `Dashboard`. Test hver measure med DAX
efter oprettelse.

> Brug **ikke** variabelnavnet `LastDate` – det kolliderer med DAX-funktionen `LASTDATE`.

## Månedsakse (kalkuleret kolonne på datotabellen, hvis den mangler)
```dax
MonthStart = DATE(YEAR(<DateTable>[Date]), MONTH(<DateTable>[Date]), 1)
```
formatString `mmm yyyy`. Kør derefter en Calculate-refresh af datotabellen.

## Seneste måned / forrige måned (én pr. månedskort)
```dax
<base>_cm =
VAR MaxSalesDate = CALCULATE(MAX(<Fact>[<OrderDate>]), REMOVEFILTERS(<DateTable>))
RETURN CALCULATE([<Base>], REMOVEFILTERS(<DateTable>),
    <DateTable>[Date] > EOMONTH(MaxSalesDate, -1),
    <DateTable>[Date] <= EOMONTH(MaxSalesDate, 0))

<base>_pm =
VAR MaxSalesDate = CALCULATE(MAX(<Fact>[<OrderDate>]), REMOVEFILTERS(<DateTable>))
RETURN CALCULATE([<Base>], REMOVEFILTERS(<DateTable>),
    <DateTable>[Date] > EOMONTH(MaxSalesDate, -2),
    <DateTable>[Date] <= EOMONTH(MaxSalesDate, -1))

<base>_label =
VAR cm = [<base>_cm]
VAR pm = [<base>_pm]
RETURN "Forrige måned: " & FORMAT(pm, "#,0") & " (" & FORMAT(DIVIDE(cm - pm, pm), "+0.0%;-0.0%;0.0%") & ")"

<base>_cm_color = IF([<base>_cm] < [<base>_pm], "#D64550", "#252423")
```

For nøgletal, hvor lavere er bedre (returer, annulleringer, churn), vendes farven: en stigning er
`#D64550`, et fald `#252423`:
```dax
<base>_cm_color = IF([<base>_cm] > [<base>_pm], "#D64550", "#252423")
```

**Slutter data midt i en måned** (fx sidste dato 7. september): sammenlign seneste *hele* måned med
måneden før – flyt vinduerne ovenfor én måned tilbage, eller brug modellens "seneste hele måned"-measure.
Det samme gælder **sparklinen** (`sparkMeasure` i config): ellers ender kurven med et brat fald i den
ufuldstændige måned. Brug datotabellens `is_complete_month`, hvis den findes, ellers:
```dax
<base>_spark =
VAR MaxSalesDate = CALCULATE(MAX(<Fact>[<OrderDate>]), REMOVEFILTERS(<DateTable>))
VAR LastFullDay  = IF(MaxSalesDate = EOMONTH(MaxSalesDate, 0), MaxSalesDate, EOMONTH(MaxSalesDate, -1))
RETURN IF(MAX(<DateTable>[Date]) <= LastFullDay, [<Base>])
```
Ét `_spark`-measure pr. månedskort; trend-grafen bruger samme regel.

## Margin (hvis der findes kostpris)
```dax
total_cost       = SUMX(<Fact>, <Fact>[quantity] * <Fact>[cost])     -- tjek om cost er pr. stk. eller pr. linje
gross_margin     = [<Revenue>] - [total_cost]
gross_margin_pct = DIVIDE([gross_margin], [<Revenue>])               -- formatString 0.0%
```

## "Top"-tekst til fremhævningsfliser
```dax
top_<dim> =
VAR Items = FILTER(VALUES(<DimTable>[<Column>]), NOT ISBLANK(<DimTable>[<Column>]))
VAR Top1  = TOPN(1, Items, [<Measure>], DESC)
RETURN CONCATENATEX(Top1, <DimTable>[<Column>], ", ")
```

## Format
Alle tal-measures: `#,0` (hele tal). Procenter: `0.0%`.
