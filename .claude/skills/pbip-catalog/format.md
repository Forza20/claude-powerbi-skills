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
| Opstrøms kilde | Lag før Power BI (bronze/silver-tabel, dbt-model, system). Manuel indtil medallion-lineage automatiseres. |
| Status | `Mangler` · `AI-forslag` · `Fra model` · `Redigeret` · `Godkendt` |

`Beskrivelseskilde` (Excel / TMDL / AI) viser hvor teksten kom fra i denne kørsel.

### Status-livscyklus
```
Mangler ──AI-forslag──► AI-forslag ──bruger retter──► Redigeret ──► Godkendt ──writeback──► (TMDL ///)
          TMDL ///  ──► Fra model ───────────────────────────────► Godkendt
```
Præcedens ved hver kørsel: tekst i Excel (status ≠ Fra model) > TMDL `///` > AI-forslag.
Rækker med `Fra model` følger altid modellen, så ændringer i TMDL slår igennem.

## Faner
- **Oversigt** – antal, beskrivelsesstatus, kilde til dashboard-pladser, vejledning.
- **Tabeller** – type (Fakta/Dimension/Dato/Bro/Measures/Hjælpe), kilde, kildeobjekter, opstrøms queries, lagring.
- **Kolonner** – datatype, nøglefelt, beregnet, mulig PII, oprindelse (kildeobjekt.kolonne), Power Query-trin, DAX.
- **Measures** – DAX, direkte afhængigheder, alle kildekolonner (transitivt), bruges af.
- **Dashboard** – én række pr. felt pr. plads på pbip-layout-siden (KPI 1–4, Trend, Månedskort 1–3, Søjler, Top 10-tabel, Fremhævning 1–2).
- **Relationer** – kardinalitet, krydsfilter, aktiv/inaktiv.
- **Kilder** – datakilder, parametre og delte Power Query-queries.
- **Fjernet** – felter fra forrige katalog der ikke findes længere.

Kolonnerne `Dashboard-plads` (direkte binding på visual) og `Dashboard (indirekte)` (indgår via
measure-afhængigheder) gør det muligt at filtrere på alt der påvirker dashboardet.

## lineage.md
1. **Overblik** – datakilde → delte queries → tabeller → rapportsider.
2. **Dashboard-pladser** – én graf pr. plads: plads ← measure ← afhængige measures ← kolonner ← oprindelse, plus en tabel med Power Query-trin pr. kolonne.
3. **Kolonne-lineage pr. tabel** – sammenklappelige tabeller med oprindelse og trin.

Mermaid bruger kun `flowchart LR` (understøttet af Azure DevOps-wiki). `--fence azdo` (standard)
giver `::: mermaid`, `--fence github` giver ```` ```mermaid ````.

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
