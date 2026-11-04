# Format: catalog.xlsx, lineage.md og model.dbml

## Nøgler
| Type | Nøgle | Eksempel |
|---|---|---|
| Tabel | `<tabel>` | `fact_sales` |
| Kolonne | `<tabel>[<kolonne>]` | `fact_sales[order_date]` |
| Measure | `<tabel>[<measure>]` | `_Measures[Omsætning]` |

Samme format som felterne i pbip-layouts `config.json`. Nøglen bruges til at flette rettelser
mellem kørsler — omdøbes et felt i modellen, havner den gamle række på fanen **Fjernet**, så
beskrivelsen ikke forsvinder i stilhed.

## Redigerbare kolonner (turkise)
| Kolonne | Brug |
|---|---|
| Beskrivelse | Forretningsbeskrivelse. Skrives tilbage som `///` når Status = Godkendt. |
| Ejer | Dataejer / ansvarlig. |
| Følsomhed | Fx Offentlig, Intern, Fortrolig, PII. Forudfyldes "Mulig PII - vurdér" ud fra kolonnenavn. |
| Opstrøms kilde | Hvor data kommer fra før Power BI. Udfyldes automatisk (se nedenfor); egen tekst bevares. |
| Status | `Mangler` · `Bør oversættes` · `AI-forslag` · `Fra model` · `Redigeret` · `Godkendt` |

`Beskrivelseskilde` (Excel / TMDL / AI) viser hvor teksten kom fra i denne kørsel.

### Opstrøms kilde (automatisk)
| Oprindelse | Eksempel på tekst |
|---|---|
| Fil (Excel/CSV) | `Silver_Excel.xlsx › CUST_MASTER › CustomerName` (append af flere ark: `ORDERS_2025 + ORDERS_2026`) |
| Database uden SQL | `gold.dim_customers.country (PostgreSQL)` |
| Database med `--sql` | `silver.erp_loc_a101.cntry ← bronze.erp_loc_a101.cntry (afledt: case when …)` |
| Surrogatnøgle | `Surrogatnøgle genereret i Power Query` / `Surrogatnøgle fra dim_customer (genereret i Power Query)` |
| Beregnet i Power Query | `Beregnet i Power Query (fact_sales): Number.Round([Quantity] * [UnitPrice], 2)` |
| Fast liste (`#table`) | `Fast liste i Power Query` / `Opslag i fast liste i Power Query (dim_channel)` |
| Beregnet kolonne (DAX) | `Beregnet kolonne (DAX) i Power BI` |

Tabeller får kildefil og ark (`Silver_Excel.xlsx › products, subcategories`), SQL-lagene
(`silver.crm_prd_info, silver.erp_px_cat_g1v2 ← bronze.… (filter: …)`), eller for brotabeller de
ark rækkerne kommer fra (`… › campaign_skus (nøgler slået op i dim_campaign, dim_product)`).

Kolonnen **Opstrøms kilde (auto)** gemmer den automatiske tekst fra kørslen. Ved næste kørsel
opdateres Opstrøms kilde kun, hvis den er tom eller stadig er lig med den sidste automatiske
tekst — har du skrevet noget selv, bevares det.

### Status-livscyklus
```
Mangler ──AI-forslag──► AI-forslag ──bruger retter──► Redigeret ──► Godkendt ──writeback──► (TMDL ///)
          TMDL ///  ──► Fra model ───────────────────────────────► Godkendt
```
Præcedens ved hver kørsel: tekst i Excel (status ≠ Fra model / Bør oversættes) > TMDL `///` > AI-forslag.
Rækker med `Fra model` følger altid modellen, så ændringer i TMDL slår igennem.

**Bør oversættes**: TMDL-beskrivelsen er på engelsk. Det afgøres af en ordtælling (`looks_english`)
af engelske og danske småord og ord med æ/ø/å. Rækken kommer med i `missing_descriptions.json` med
feltet `translate`. Et AI-forslag på dansk erstatter den engelske tekst (status `AI-forslag`,
kilde `AI (oversat fra TMDL)`). Først writeback af en godkendt række ændrer modellen.

## Faner
- **Oversigt** – antal, beskrivelsesstatus, kilde til dashboard-pladser, vejledning.
- **Tabeller** – type (Fakta/Dimension/Dato/Bro/Measures/Hjælpe), kilde, kildeobjekter, opstrøms queries, lagring.
- **Kolonner** – datatype, nøglefelt, beregnet, mulig PII, oprindelse (kildeobjekt.kolonne), Power Query-trin, DAX.
- **Measures** – DAX, direkte afhængigheder, alle kildekolonner (transitivt), bruges af.
- **Dashboard** – én række pr. felt pr. plads på pbip-layout-siden (KPI 1–4, Trend, Månedskort 1–3, Søjler, Top 10-tabel, Fremhævning 1–2).
- **Relationer** – kardinalitet, krydsfilter, aktiv/inaktiv.
- **Kilder** – datakilder, parametre og delte Power Query-queries.
- **Ændringer** – nye og ændrede felter siden forrige `catalog.json` i samme `docs/`-mappe. Kolonner:
  Ændring (Ny/Ændret), Ark, Nøgle, Felt, Før, Efter. Disse felter sammenlignes: tabeller (Type,
  Kildeobjekter, Beskrivelse, Status), kolonner (Datatype, Format, Skjult, Oprindelse, Opstrøms
  kilde (auto), Beskrivelse, Status) og measures (DAX, Format, Mappe, Skjult, Beskrivelse, Status).
  Fanen findes kun, når der er ændringer.
- **Fjernet** – felter fra forrige katalog der ikke findes længere.

Kolonnerne `Dashboard-plads` (direkte binding på visual) og `Dashboard (indirekte)` (indgår via
measure-afhængigheder) gør det muligt at filtrere på alt der påvirker dashboardet.

## lineage.md
1. **Overblik** – datakilde → delte queries → tabeller → rapportsider.
2. **Dashboard-pladser** – én graf pr. plads: plads ← measure ← afhængige measures ← kolonner ← oprindelse, plus en tabel med Power Query-trin pr. kolonne.
3. **Kolonne-lineage pr. tabel** – sammenklappelige tabeller med oprindelse og trin.

Mermaid bruger kun `flowchart LR` (understøttet af Azure DevOps-wiki). `--fence azdo` (standard)
giver `::: mermaid`, `--fence github` giver ```` ```mermaid ````.

## lineage.html (tilvalg, `--html`)
Én selvstændig HTML-side med lineage på tabelniveau. Den virker offline og kræver ingen server.
Skabelonen ligger i `assets/lineage-template.html`, og data indsættes som JSON i
`<script id="lineage-data">`.

- **Kolonner = lag**, fra venstre mod højre: filer (CSV/Excel-ark), databaseskemaer sorteret efter
  navn (raw/landing → bronze → staging → silver → gold; andre skemaer efter deres kilder), Power
  Query-queries, Power BI-tabeller og rapportsider. Når tabeller i samme skema bygger på hinanden,
  deles skemaet i trin (`mp_x_gold · trin 2`).
- **Grupper**: tabeller i en kolonne grupperes efter den tabel, de føder ("føder dim_customer").
- **Stiplet rød kant**: tabellen bruges ikke videre af de læste SQL-filer eller Power Query, eller en
  Power BI-tabel bruges ikke på nogen rapportside. Uden rapportsider markeres modeltabellerne ikke.
- **Klik** på en tabel fremhæver hele dens vej op- og nedstrøms. Klik igen eller tryk Esc for at
  fjerne fremhævningen. Hold musen over en tabel for at se fuldt navn, type, beskrivelse og antal
  forbindelser.
- Databaselagene kræver `--sql`. Uden SQL viser siden kun Power Query → model → sider.
  Temp-tabeller får deres egen kolonne ("temp-tabeller"), og CTE'er følges som underforespørgsler.
  Dynamisk SQL (`execute format(…)`), `MERGE` og `UPDATE` afbryder sporet ligesom i Opstrøms kilde.
  Så vises tabellen før bruddet som "bruges ikke videre".

## model.dbml (dbdiagram.io)
| Power BI | DBML |
|---|---|
| Tabeller | `Table` med `headercolor` pr. type og `TableGroup` (Fakta / Bro / Dimension / Dato / Measures / Hjælpe) |
| Measure-tabel | `Table` hvor hvert measure er en "kolonne" af typen `measure`; DAX og dashboard-plads i `note` |
| Beregnede kolonner | Almindelig kolonne, `note: 'Beregnet (DAX): …'` |
| Skjulte kolonner | Med, markeret `Skjult` i noten (skjult pladsholder i measure-tabellen udelades) |
| Nøgle | `[pk]` på `isKey`-kolonnen eller 1-siden af en relation |
| Relationer | `Ref` med `>` (mange-til-én), `-` (én-til-én), `<>` (mange-til-mange). Inaktive og tovejs-relationer står som kommentar på `Ref` og i tabellens `Note` (DBML har ingen stiplede linjer) |
| Tabelbeskrivelse | `Note` med beskrivelse, type, kilde, kildeobjekter, Power Query-queries, inaktive relationer og dashboard-pladser |
