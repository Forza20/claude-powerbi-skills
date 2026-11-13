# Layout: AdventureWorks-rapportskabelonen

Skabelonen er en rigtig rapport – `adventureworks_report.pbix`, gemt som PBIP i Power BI Desktop – skilt ad
af `scripts/extract-template.js` i [templates/adventureworks/](templates/adventureworks/): hvert faneblad,
visual, bogmærke og navigationsikon, med hver farve erstattet af en farvenøgle ([colors.md](colors.md)).
`scripts/gen-report.js` bygger de faneblade, brugeren vælger, ind i en rapport og kobler dem til
projektets egen model. Fanebladene er **1280 × 720**; tal beholder skabelonens formater og visningsenheder
(K, M). Logoet bliver til rapportens titel eller brugerens eget logo.

## Faneblade (brugeren vælger altid hvilke)

| Nøgle | Faneblad | Viser | Kræver i modellen |
|---|---|---|---|
| `exec` | Exec Dashboard | 4 KPI-fliser, omsætningstrend (trendlinje, forecast, anomalier), ordrer pr. kategori, topprodukter (ordrer, omsætning, rate), 3 månedlige KPI'er mod sidste måned, 2 "top"-fliser, et filterpanel (filterikon, bogmærker) | omsætning, ordrer, profit, en rate, et tredje antal; dato; kategori, underkategori, produkt; region/land til filterpanelet |
| `map` | Map | ordrer pr. land på et kort, kontinent-filter | en geografikolonne (land/by) og en regionskolonne |
| `product` | Product Detail | **drillthrough** fra et produkt: 3 målere mod targets, profittrend med prisjustering (what-if), en trend hvor brugeren vælger measure (feltparameter), en opsummeringstekst | produkt; targets (eller sidste måned + vækst); en prisjusteringsparameter; en feltparameter til produktmål |
| `customer` | Customer Detail | kunde-KPI'er, kundetrend med valg af mål (feltparameter), ordrer pr. to kundeattributter (donuts), top 100 kunder, topkunden, en indsigtsknap (bogmærker) | kunde-id og navn, to kundeattributter, kunde-measure, omsætning pr. kunde; en feltparameter til kundemål |
| `tooltip` | Category Tooltip | skjult tooltip-side på kategorisøjlerne: KPI-liste og ugentlige ordrer | exec-measures; en ugestart-kolonne. Uden den viser søjlerne det normale tooltip |
| `qna` | Q&A | Q&A-visualet (spørgsmål på naturligt sprog) og ordrer pr. kategori og en attribut | kategori, en produktattribut |
| `decomp` | Decomposition Tree | ordrer nedbrudt på kategori → underkategori → produkt, og et ordrekort | kategori, underkategori, produkt |
| `influencers` | Key Influencers | hvad der driver en kundeattribut; hvad der driver en gennemsnitspris | en kundeattribut at forklare og attributter der forklarer den; en talkolonne pr. produkt |

Navigation: den mørke skinne til venstre har en knap pr. faneblad (Exec, Map, Product, Customer). Et
faneblad brugeren fravælger mister sin knap på alle faneblade, og knapperne under rykker op. Product
Detail nås med sin knap eller med drillthrough på et produkt.

## Skabelonfelter → modellen

`config.json → fields` kobler hvert felt de valgte faneblade bruger (template.json → `fields`, med de
faneblade der bruger det) til `Tabel[Felt]` i modellen, eller `null` når modellen intet har der passer:
`null` fjerner feltet fra et visual med flere felter (Key Influencers' forklaringsliste) og fjerner et visual
der har brug for det (et kort uden placering). Generatoren lister hver manglende kobling og hvert udeladt
visual. Vælg i denne rækkefølge: det forventede indhold, så reserveløsningen.

### Measures

| Skabelonfelt | Forventet | Reserveløsning / sådan laves den |
|---|---|---|
| `Measure Table[Total Revenue]` | omsætning | — (påkrævet) |
| `Measure Table[Total Orders]` | antal ordrer (distinkte ordre-id'er) | antal rækker / transaktioner |
| `Measure Table[Total Profit]` | profit, dækningsbidrag | omsætning efter rabat |
| `Measure Table[Return Rate]` | en rate hvor **høj er dårlig** (returer, churn, annulleringer) | margin % – ret så teksterne (`Most Returned Product Type:` …); tabellens farveskala læser "lav = rød" (skabelonen: høj = rød) |
| `Measure Table[Total Returns]` | returer, reklamationer | kunder (så: `Monthly Returns` → `Monthly Customers`) |
| `Measure Table[Total Customers]` | distinkte kunder med en ordre | — (kundefanebladet) |
| `Measure Table[Previous Month Revenue/Orders/Returns]` | measuren en måned tilbage | laves – measures.md "Forrige måned" |
| `Measure Table[Revenue Target]`, `[Order Target]`, `[Profit Target]` | targets fra modellen (en targettabel) | sidste måned × (1 + vækst) – measures.md "Targets"; spørg brugeren om væksten (skabelonen: 10 %) |
| `Measure Table[… Target Gap]` | measure − target | laves – measures.md |
| `Measure Table[Adjusted Profit]` | profit med prisjusteringen | laves – measures.md "Prisjustering" |
| `Measure Table[Average Revenue per Customer]` | omsætning ÷ kunder | laves |
| `Measure Table[Average Retail Price]` | gennemsnitspris pr. produkt | gennemsnitlig ordreværdi, gennemsnitlig listepris |

### Kolonner

| Skabelonfelt | Forventet | Reserveløsning |
|---|---|---|
| `Calendar Lookup[Date]`, `[Year]`, `[Month]`, `[Start of Month]`, `[Start of Week]` | datotabellens dato, år, månedsnavn, månedsstart, ugestart | — (pipeline-power-bi's datotabel har dem alle) |
| `Calendar Lookup[Date Hierarchy.Year/Start of Month/Start of Week/Date]` | skabelonens drill-niveauer → de almindelige kolonner ovenfor | — |
| `Calendar Lookup[Start of Quarter]` | kvartalsstart (kun i filterpanelets bogmærker) | `null` |
| `Product Categories Lookup[CategoryName]`, `Product Subcategories Lookup[SubcategoryName]`, `Product Lookup[ProductName]` | kategori, underkategori, produkt | segment / kanal / kunde for en model uden produkter |
| `Product Lookup[ProductColor]` | en produktattribut (Q&A-tabellen) | brand, størrelse |
| `Product Lookup[ProductCost]` | et tal pr. produkt (Key Influencers) | listepris |
| `Territory Lookup[Country]` | en placering kortet kan finde | by; `null` udelader kortet |
| `Territory Lookup[Continent]` | regionen over den | region, land |
| `Customer Lookup[CustomerKey]`, `[Full Name]` | kunde-id og navn | — (kundefanebladet) |
| `Customer Lookup[Income Level]`, `[Occupation]` | to kundeattributter (donuts) | segment, region, betalingsbetingelser |
| `Customer Lookup[HomeOwner]` | kundeattributten Key Influencers forklarer | segment, betalingsbetingelser |
| `Customer Lookup[AnnualIncome]`, `[EducationLevel]`, `[Is Parent?]`, `[MaritalStatus]` | attributter der kan forklare den | andre kundekolonner; `null` udelader én |
| `Price Adjustment (%)[Price Adjustment (%)]` | what-if-parameteren | laves – measures.md "Prisjustering" |
| `Product Metric Selection[…]`, `Customer Metric Selection[…]` (og `… Fields`) | feltparametre (brugeren vælger en measure) | laves – measures.md "Feltparametre" |

Navne på siden: `labels` sætter navnet for et felt (standard: modellens navn gjort læsbart, `total_sales`
→ `Total sales`). `texts` erstatter skabelonens titler og tekstbokse – template.json → `pages[].texts`
lister dem præcist (`Most Returned Product Type:` med kolon). Ret en tekst, når en reserveløsning ændrer
betydningen.

## Hvad generatoren ændrer, og hvad den beholder

- Kun de valgte faneblade (nye side-id'er), deres bogmærker og ikoner skrives; rapportens egne faneblade
  bliver. Faneblade fra en tidligere kørsel (og det gamle enkeltsidede layout) erstattes.
- Rapportens basistema bliver skabelonens (`CY23SU04`), og et farvetema (`pbip-layout-theme.json`, kun
  farver) registreres, så standardfarverne på serier matcher skabelonen.
- Kilderapportens data følger ikke med: valgte slicer-værdier, drillthrough-produktet, formatering bundet
  til enkelte værdier og en tekst der citerer en kunde blev fjernet, da skabelonen blev lavet, eller ryddes
  af generatoren.
- Smart narrative ("Report Summary") beholder kun første sætning ("Total orders for <produkt> were
  <ordrer>"); AI-trendsætningerne hørte til kildedataene.
