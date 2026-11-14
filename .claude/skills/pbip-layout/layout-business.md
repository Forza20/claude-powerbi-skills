# Layout: Business-skabelonen (Marketing, Sales, Finance)

Skabelonen er *Power BI Dashboard Template Library – Marketing, Sales, Finance* (PBIP, 7 faneblade) skilt
ad af `scripts/extract-template.js --keys business` i [templates/business/](templates/business/). Én rapport
på én model: et fælles **Home** og tre selvstændige **moduler** med et overblik og en drillthrough-side hver.
Brugeren vælger modulerne; et fravalgt modul forsvinder helt (faneblade, knapper, Home-kort og -flise),
og resten flytter sammen. Fanebladene er **1280 × 720** med samme fem bånd: navigation til venstre,
header med datoslicer, 4 KPI-kort, analysebånd (trend 60 % + sammensætning 40 %), detaljebånd
(fokus-visual 40 % + rangeret tabel 60 % med drillthrough).

## Faneblade og moduler (brugeren vælger altid)

| Nøgle | Faneblad | Modul | Viser | Kræver i modellen (datakontrakt) |
|---|---|---|---|---|
| `home` | Home | fælles | 1 headline-KPI pr. modul + Marketing CAC (kræver Marketing og Sales), omsætning mod driftsomkostninger (Finance), en flise pr. modul med knap | dato + mindst ét modul |
| `marketing` | Marketing | Marketing | MQLs, MQL→SQL-rate, CPL, Marketing ROI %; MQLs mod sidste år, leads pr. kanal, indholdstyper, topkampagner | leads, MQLs, SQLs, spend (+ konverteringer, attribueret omsætning, kanal, kampagne, indholdstype) |
| `campaign` | Campaign Detail | Marketing | **drillthrough** fra en kampagne: KPI-strip, funnel Leads → MQLs → SQLs → Conversions, spend mod omsætning, kanal og indhold | kampagnenavn; funnel-trinene laves af `gen-measures.js` |
| `sales` | Sales | Sales | lukket-vundet omsætning, win rate, nye kunder, salgscyklus; omsætning mod sidste år, pr. kategori og kvartal, kvoteopfyldelse pr. sælger, seneste aftaler | beløb og stadie pr. opportunity (+ kunde, ny-kunde-flag, cyklusdage, sælger, kvote, kategori) |
| `opportunity` | Opportunity Detail | Sales | **drillthrough** fra en sælger eller kunde: åben pipeline, win rate, gennemsnitlig aftalestørrelse og -alder, pipeline pr. stadie, aldersgrupper, aftaleliste | sælger, kundenavn (+ pipelinestadie, alder, aldersgruppe) |
| `finance` | Finance | Finance | omsætning, nettomargin %, driftsomkostninger, driftscashflow; omsætning mod omkostninger, margin pr. kvartal, omkostninger pr. kategori, seneste posteringer | beløb pr. postering og kontotype (Revenue, COGS, OpEx, Other) (+ status, cashbevægelse, omkostningskategori) |
| `pnl` | P&L Detail | Finance | **drillthrough** fra en omkostningskategori: KPI-strip, resultatopgørelse (konti × måned), posteringerne | kontonavn, omkostningskategori |

Regler (generatoren håndhæver dem):
- Et modul er valgt, når et af dets faneblade er valgt. En drillthrough-side kræver sit overblik
  (`campaign` → `marketing`, `opportunity` → `sales`, `pnl` → `finance`). Home alene afvises.
- Felter fra et fravalgt modul skal ikke kobles: de udelades af sig selv (`leftOutByModule`), og med dem
  modulets Home-kort, -flise og navigationsknap. Home-kortene og -fliserne fordeles over rækken igen; uden
  Finance rykker fliserne op, hvor omsætningslinjen stod. Home-undertitlen nævner de valgte moduler.
  ([templates/business/modules.json](templates/business/modules.json)).
- Anbefal kun et modul, modellen har data til (de påkrævede kolonner nedenfor). Home anbefales altid,
  når mindst ét modul er valgt.

## Datakontrakt → measures (i stedet for at koble 86 felter i hånden)

Skabelonens 100 measures (`templates/business/measures/*.tmdl`: KPI, PY, YoY %, YoY pp for rater, YoY
Status og YoY Colour) bygger på ca. 40 kontraktkolonner
([templates/business/contract.json](templates/business/contract.json)). Kobl **kolonnerne**, så laver
`gen-measures.js` measures og felter:

1. `suggest-fields.js "<.SemanticModel>" --config <config.json>` (config med `template: "business"` og
   `pages`) foreslår `config.contract` ud fra navne og skriver `how` pr. kolonne (`name`, `none`, `none –
   derive: …`) og `requiredMissing`.
2. Tjek koblingen kolonne for kolonne – betydning, enhed og **værdier**. Measures sammenligner med faste
   tekster: `Fact_Opportunity[Stage]` = `Closed Won` / `Closed Lost` / `Open`, `Dim_Account[AccountType]` =
   `Revenue` / `COGS` / `OpEx` / `Other`, `Fact_Finance[Status]` = `Reversed` (udelades). Staver modellen dem
   anderledes: `config.values` (`{ "Fact_Opportunity[Stage]": { "Closed Won": "Won" } }`). Kør DAX på de
   distinkte værdier, før du gætter.
3. `gen-measures.js <config.json> --write-config` og
   - en pipeline-power-bi-kørsel: `--spec runs/<run-id>/choices.json` → `build.measures[]` (snake_case:
     `closed_won_revenue_yoy_pct`, mappe `Marketing`/`Sales`/`Finance`/`Home`, filterkontrakt på PY-measures)
     og funnel-trinene som `build.parameters[]` (`kind: "list"`); kør derefter `rebuild.js`;
   - andre projekter (Desktop lukket): `--tmdl "<.SemanticModel>"` → tabellen `_layout_measures` (+
     `Funnel stage`) med skabelonens navne.
   En measure laves kun, når alle dens kolonner er koblet og alle measures den bruger er lavet; resten står
   i `skipped` med årsagen, og deres felter bliver `null` (visuals udelades). Et navn modellen allerede har,
   får modulet foran (`finance_revenue`).
4. `currencyFormat` sætter beløbsformatet (skabelonen: `\$#,0`), fx `#,0 "kr."`.

### Påkrævet pr. modul

| Modul | Påkrævet | Ellers bliver det tomt / udelades |
|---|---|---|
| fælles | `Dim_Date[Date]` (markeret datotabel, hele år – PY bruger `SAMEPERIODLASTYEAR`) | `[Year]` (filterkontrakt), `[MonthLabel]` → månedsstart-kolonnen (`dim_date[month_start]`), `[Month]`, `[Quarter]` |
| Marketing | – (hvert KPI for sig) | uden `Spend`: CPL, ROI %, CAC; uden `AttributedRevenue`: ROI % |
| Sales | `Fact_Opportunity[Amount]`, `[Stage]` | uden `IsNewCustomer`: nye kunder og Marketing CAC; uden `CycleDays`/`AgeDays`: cyklus/alder; uden `Fact_SalesTarget[Quota]`: kvotebjælken |
| Finance | `Fact_Finance[Amount]` (positive beløb), `Dim_Account[AccountType]` | uden `Status`: tilbageførte posteringer tælles med – fjern filteret med `values` eller acceptér det som en beslutning |

`derive` i contract.json siger, hvordan en manglende kolonne laves (cyklusdage = lukkedato − oprettelsesdato,
ny kunde = kundens første vundne aftale, aldersgrupper 0–30/31–60/61–90/90+). I en pipeline-power-bi-kørsel
er det et rensetrin eller en kolonne i build-spec'en – en **beslutning** (SKILL.md trin 7): lav kolonnen
(anbefalet, når kilden har delene) eller udelad KPI'en.

### Beslutninger, der typisk opstår
- En statuskolonne med andre værdier end `Closed Won/Closed Lost/Open` (fx `Paid`/`Cancelled`): hvilken
  værdi er "vundet"? Anbefal ud fra de distinkte værdier og deres beløb.
- Omkostninger gemt som negative tal: skabelonen forventer positive beløb og lader kontotypen give
  fortegnet – vend fortegnet i Power Query (anbefalet); ellers bliver omkostnings-KPI'erne og nettoresultatet forkerte.
- En retail-model uden opportunities: Sales kan bruge ordrer (beløb, en status som "vundet"), men win rate
  og pipeline mister mening – anbefal at udelade `opportunity` eller sæt `texts`.

## Farver (business)

| Nøgle | Bruges til | Skabelon |
|---|---|---|
| `primary` | KPI-kort 1, nuværende serie, overskrifter, knapperne på Home | `#1B2A4A` |
| `secondary` | KPI-kort 2, anden serie, temaets accent | `#1A7F7C` |
| `tertiary` | KPI-kort 3, tredje serie | `#5F6F86` |
| `highlight` | KPI-kort 4, fjerde serie, valgt tilstand | `#7FB3D9` |
| `prior` | sidste års linjer og søjler | `#A9B4C6` |
| `sidebar` | navigationsskinnen | `#12212B` |
| `navActive` | knappen for det aktive faneblad | `#24475C` |
| `ink` | mørk tekst på det lyse KPI-kort | `#12212B` |
| `subtle` | undertitler | `#475569` |
| `canvas` | fanebladets baggrund | `#F2F5F8` |
| `panel` | kort- og grafbaggrunde | `#FFFFFF` |
| `onDark` | tekst på mørke og farvede baggrunde | `#FFFFFF` |
| `line` | kanter | `#D5DCE6` |

**Good / bad / neutral (`#197A4C` / `#C0392B` / `#6B7280`) er faste** – de ligger i `… YoY Colour`-measures og
i temaet og ændres aldrig af et farvevalg. Temaet er skabelonens eget (skrifttyper, tekstklasser,
gitterlinjer, tabelhoveder) med farvenøglerne udfyldt. Fra `palette.ps1`: `dark` → `primary`/`sidebar`,
`teal` → `secondary`, `gold` → `tertiary`.

## Rettelser i forhold til udkastet
`extract-template.js` retter to fejl i kilderapporten (`powerbi-report-author validate`): drillthrough-filtrene
var markeret `Drill` i stedet for `Drillthrough` (drillthrough virkede ikke), og tekstboksene var for lave
til deres skriftstørrelse (polstring top/bund 0). Rapportens årsfilter (`Year = 2024`, eksempeldata) følger
ikke med.

## config.json (eksempel)
[config.example-business.json](config.example-business.json).
