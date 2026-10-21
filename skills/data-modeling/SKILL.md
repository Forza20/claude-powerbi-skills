---
name: "data-modeling"
description: "Byg et medallion gold-lag i Power Query og en færdig PBIP (TMDL) fra en silver-Excel, med grill-me-afklaring og trin-for-trin-guide. Trigger: \"Data modeling:\""
---

# Data modeling

Trigger ALTID når brugeren skriver **"Data modeling:"** efterfulgt af en opgave (typisk med en vedhæftet Excel-fil = silver-lag, evt. en .pbip).

Leverancen er altid to ting, der svarer 1:1 til hinanden:
1. Et **dokument** (Docs-artifact) med en step-by-step guide: parameter/kilde → silver → gold (én sektion pr. dimension/fakta) → semantisk model → publish → afstemning.
2. En **PBIP-zip** (TMDL) med Power Query-grupperne `Parametre`, `Silver`, `Gold`, relationer, measures, RLS og en tom rapportside.

Sprog: dansk, korte svar, punktform. Push back på vage krav før analysen starter.

---

## Fase 1 – Udforsk filerne (før første spørgsmål)

- Kopiér uploads til en egen mappe i scratchpad, kør Python med `-I`.
- List alle ark: navn, rækker × kolonner, første 2 rækker.
- Hvis der er vedhæftet en `.pbip`: tjek om det kun er pointer-filen (ca. 13 linjer). Uden `.SemanticModel`/`.Report`-mapperne kan modellen IKKE ses – sig det og spørg om zip af hele projektmappen.
- Profilér de nøgler, der bestemmer designet, i stedet for at spørge om dem:
  - Matcher ordrernes kundenavne kundemasteren? Produktnavne i linjer produktmasteren?
  - Har alle linjer en ordre? Dubletter i ID'er og navne?
  - Testdata (fx kunde 9999 / TEST ACCOUNT, produkt ZZZ-000, tomme dubletprodukter)
  - Er `LineTotal` brutto eller netto (sammenlign med Quantity × UnitPrice og DiscountPct)?
  - Kanal-/statuskoder, datointerval, huller i mål vs. ordrer (samme huller = reel pause, ikke fejl)
  - Brede ark (unpivot), sammensatte felter (split på `|`), kopier af ark (`Sheet1`)

## Fase 2 – Grill brugeren (én beslutning ad gangen)

Stil spørgsmålene ét ad gangen med options A/B/C og **min anbefaling + begrundelse**. Kan et spørgsmål besvares af data, så udforsk i stedet. Standardrækkefølge og anbefalede svar (fra den oprindelige analyse):

| # | Beslutning | Anbefaling |
| --- | --- | --- |
| 1 | Hvilken model er facit? | Brugerens egen PBIP (kræver zip) – ellers en ny salgs- og marginmodel |
| 2 | Hvor ligger gold? | Power Query-grupper inde i PBIP (Dataflow Gen2 senere) |
| 3 | Hvem renser? | Silver: typer, trim, test/dubletter, append. Gold: joins, nøgler, beløb, navne |
| 4 | Nøgler | Heltals-surrogatnøgler for Kunde/Produkt, `-1` = Ukendt. Dato og Kanal beholder naturlig nøgle |
| 5 | Generering af nøgler | `Table.Buffer(Table.Sort(...))` + `Table.AddIndexColumn` fra 1. Regel: nøgler må aldrig bruges uden for modellen |
| 6 | Omsætning | Netto efter rabat. Brutto og rabat bevares til afstemning |
| 7 | Ordrestatus | Alle statusser med, `Status` som tekst i fakta + measure for leveret |
| 8 | Ukendte koder (kanal) | Dimension med pladsholdernavne + `-1`-række |
| 9 | Dim Dato | Dynamisk, hele kalenderår omkring min/max af ordre- og måldatoer |
| 10 | Navngivning | Gold helt dansk (tabeller, kolonner, measures). Nøgler `…Key`, skjult |
| 11 | Deployment | Desktop → refresh → Publish (PBIP kan ikke uploades direkte til Service) |
| 12 | Filplacering | SharePoint/OneDrive > lokal (gateway) |
| 13 | GitHub som kilde | Kun offentligt repo: `Web.Contents("https://raw.githubusercontent.com", [RelativePath = GitHubSti])`. Privat repo → aldrig token i M; brug lokal kopi/SharePoint |
| 14 | RLS | Dynamisk på `Dim Kunde[Region]` med `LOOKUPVALUE`; vis `IN CALCULATETABLE(...)`-variant til flere regioner |
| 15 | Leverance | Doc + PBIP med tom rapportside; afstemning som DAX-forespørgsler (ikke visuals – PBIR-sider fejler oftest) |

Slut grillen med en opsummeringstabel over alle beslutninger og bed om bekræftelse.

## Fase 3 – Beregn afstemningstal

Simulér hele pipelinen i Python på silver-filen, før guiden skrives, så hvert trin får rigtige tjekpunkter:
- Rækker pr. silver-query og pr. gold-tabel (inkl. `-1`-rækker), Dim Dato-rækker
- Linjer på Ukendt produkt/kunde (med LinjeID'er)
- Brutto (= sum LineTotal), rabat, netto, kost, avance, avance %, leveret omsætning, mål
- Pr. år: netto, avance %, mål, målopfyldelse %, vækst %
- Note i guiden: `Number.Round` runder til lige → netto kan afvige få øre

## Fase 4 – Skriv M-koden én gang

Skriv al M-kode i ét Python-generatorscript (scratchpad), der både genererer PBIP og dumper hver query til `.m`-filer. Guiden bruger præcis samme kode.

### Mønstre

**Kilde** (én query, alle silver-queries refererer til den):
```
let
    Fil = Web.Contents("https://raw.githubusercontent.com", [RelativePath = GitHubSti]),
    Kilde = Excel.Workbook(Fil, null, true)
in
    Kilde
```
Lokal variant: `Excel.Workbook(File.Contents(ExcelSti), null, true)`.

**Silver** (`slv_`, ingen load, kildens engelske navne): `Kilde{[Item = "ark", Kind = "Sheet"]}[Data]` → `PromoteHeaders` → `SelectColumns` → `TransformColumnTypes` → `Text.Trim` → fjern test → `Table.Distinct` på nøgle. Append af årsark: reducér til fælles kolonner før `Table.Combine`. Datoer: culture `"en-US"`, `Date.From` fjerner klokkeslæt. Tom rabat → 0.

**Gold-dimension** (surrogatnøgle + Ukendt):
```
Sorteret = Table.Buffer(Table.Sort(Beriget, {{"CustomerID", Order.Ascending}})),
MedKey = Table.AddIndexColumn(Sorteret, "KundeKey", 1, 1, Int64.Type),
Omdoebt = Table.RenameColumns(MedKey, {...danske navne...}),
Valgt = Table.SelectColumns(Omdoebt, {...}),
Ukendt = #table(Value.Type(Valgt), {{-1, null, "Ukendt", ...}}),
Samlet = Table.Combine({Valgt, Ukendt})
```
Fold snowflake ud (kunde → adresse → by → region) til én flad tabel.

**Dim Dato** (dynamisk):
```
Datoer = List.Combine({slv_Ordre[OrderDate], slv_Salgsmaal[MonthStart]}),
Start = #date(Date.Year(List.Min(Datoer)), 1, 1),
Slut = #date(Date.Year(List.Max(Datoer)), 12, 31),
```
Kolonner: Dato, År, Kvartal, MånedNr (skjult, sort-by), Måned, ÅrMåned, Månedstart, Uge.

**Fact**: linjer + ordrehoved (join på OrderID) → navn → nøgle mod GOLD-dimensionerne (`#"Dim Kunde"`) → `null` → `-1` → status oversat til dansk → Brutto, Netto, Rabat (= brutto − netto), Kost med `Number.Round(..., 2)` → danske navne. Fjern navne og `LineTotal`.

**Faldgruber**
- M-trinnavne uden æøå (`Aar`, `Maaned`, `Omdoebt`); kolonnenavne må gerne have dem.
- En kolonne må ikke hedde det samme som et measure (fx `Målbeløb` i stedet for `Salgsmål`).
- Status-filtre i measures skal bruge den oversatte værdi ("Leveret").

## Fase 5 – Generér PBIP (TMDL)

Struktur:
```
<Navn>/
  <Navn>.pbip                      # artifacts → report path
  .gitignore                       # .pbi/localSettings.json, .pbi/cache.abf
  <Navn>.Report/definition.pbir    # version 4.0, datasetReference.byPath ../<Navn>.SemanticModel
  <Navn>.Report/report.json        # én tom sektion "Oversigt"
  <Navn>.SemanticModel/definition.pbism   # version 4.0
  <Navn>.SemanticModel/definition/
    database.tmdl                  # compatibilityLevel: 1601
    model.tmdl                     # culture da-DK, discourageImplicitMeasures, queryGroup Parametre/Silver/Gold, PBI_QueryOrder, ref table/role
    expressions.tmdl               # parameter (meta IsParameterQuery) + Kilde + slv_* med queryGroup
    relationships.tmdl
    tables/<Tabel>.tmdl            # kolonner + partition (mode import, queryGroup: Gold, source = M)
    roles/Region.tmdl              # tablePermission 'Dim Kunde' = [Region] = LOOKUPVALUE(...)
```
Regler:
- Navne med mellemrum eller ikke-ASCII citeres med enkelte anførselstegn (`'Fact Salgsmål'.'Månedstart'`).
- Hver kolonne: `dataType`, `lineageTag` (uuid), `summarizeBy: none` (undtagen Antal = sum), `sourceColumn`; dato-kolonner får `annotation UnderlyingDateTimeDataType = Date`.
- Dim Dato: `dataCategory: Time` + `isKey` på Dato (= markeret datotabel).
- Nøgler og beløbskolonner `isHidden`; Sikkerhed-tabellen `isHidden`.
- Measures i `_Measures` (tom tabel) med `displayFolder` (Salg, Margin, Mål, Tidsintelligens) og formatString `#,0` / `0.0 %`.
- Standard-measures: Omsætning (netto), Bruttoomsætning, Rabat, Rabat %, Antal ordrer, Antal ordrelinjer, Gns. ordreværdi, Omsætning (leveret), Kostpris, Bruttoavance, Avance %, Salgsmål, Afvigelse til mål, Målopfyldelse %, Omsætning ÅTD, Omsætning sidste år, Vækst %.
- Zip mappen og send med SendUserFile.

## Fase 6 – Guiden (Docs-artifact)

Opret dokumentet FØRST (skelet med pending-sektioner), åbn det, og fyld én sektion pr. kald:
1. **Overblik** – beslutningstabel + diagram (kilde → silver → gold → model, gold fremhævet) + regel om surrogatnøgler.
2. **Trin 1: Parameter og kilde** – grupper, parameter, Kilde-kode, credentials (Anonymous), `%20` for mellemrum.
3. **Trin 2: Silver** – tabel (query, ark, rensning, rækker) + kode pr. query + liste over ark uden for scope.
4. **Trin 3+: Én sektion pr. gold-tabel** – hvorfor, kode, kolonnetabel (kolonne, kilde i silver, synlig), tjekpunkt med tal.
5. **Semantisk model** – relationstabel, indstillinger (Auto date/time fra, Mark as date table, sort by, skjul nøgler/beløb), measures, RLS + flere-regioner-variant + kendt begrænsning (mål filtreres ikke af RLS).
6. **Publish** – credentials, scheduled refresh, RLS-tildeling, "RLS gælder kun Viewers", skift til SharePoint ændrer kun Kilde.
7. **Afstemning** – tjekliste + DAX-forespørgsler (`ROW(...)` totaler, `SUMMARIZECOLUMNS` pr. år) med forventede tal i tabeller.

Afslut i chatten med 3–4 korte punkter: hvad der skal rettes ved første åbning (fx `GitHubSti`), credentials, kontroltal – og at filen ikke er testet i Desktop her.