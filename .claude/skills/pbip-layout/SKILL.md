---
name: pbip-layout
description: Anvender det gemte "Salgsoverblik"-dashboardlayout (mørke KPI-fliser, trend med forecast, månedskort, kategori-søjler, top 10-tabel, fremhævningsfliser) på et Power BI PBIP-projekt og kobler det til projektets egne measures. Trigger ALTID når brugeren skriver `anvend "layout.md"` (også uden anførselstegn, fx "anvend layout.md") sammen med en PBIP-fil/-mappe eller et åbent PBIP-projekt i Power BI Desktop.
---

# Anvend layout.md på et PBIP-projekt

Layoutet er beskrevet i [layout.md](layout.md). Generatoren
[scripts/gen-layout.js](scripts/gen-layout.js) bygger siden ud fra en konfigurationsfil;
[config.example.json](config.example.json) er den oprindelige konfiguration
(Data Modeling PBIP). DAX-skabeloner til manglende measures ligger i
[measures.md](measures.md).

Arbejd på dansk med brugeren.

## Forudsætninger
- Load skills `powerbi-authoring:semantic-model-authoring` (measures) og
  `powerbi-authoring:powerbi-report-cli` (PBIR, validate, preview) og følg deres regler.
- `powerbi-report-author` CLI installeret (`npm install -g @microsoft/powerbi-report-authoring-cli@latest`).
- Projektet skal være PBIP med PBIR-format (mappen `<Navn>.Report/definition/pages`).
  Er det en .pbix: bed brugeren om Filer → Gem som → *.pbip, og stop.
- Tjek ledig diskplads (`Get-PSDrive C`). Under ~200 MB: sig det til brugeren før der skrives.

## Arbejdsgang

1. **Find projektet.** Brug den uploadede/nævnte sti, ellers søg efter `*.pbip` i
   brugerens mapper. Notér `.Report`-mappen.

2. **Forbind til modellen.** Er projektet åbent i Power BI Desktop: brug
   powerbi-modeling-mcp (`ListLocalInstances` → `Connect`). Ellers `ConnectFolder` på
   `<Navn>.SemanticModel/definition`. List tabeller, kolonner, measures og relationer.

3. **Kortlæg pladserne.** Brug tabellen "Pladser der skal kobles til modellen" i
   [layout.md](layout.md). Find for hver plads det bedste eksisterende measure/kolonne;
   brug fallback når data mangler (fx ingen returer → margin % eller aktive kunder).
   Kør DAX-forespørgsler for at kende værdierne (total, kategorier, seneste måned).
   Tjek fx om en "line_total" er før/efter rabat, og om cost er pr. stk.

4. **Vis kortlægningen og få godkendelse.** Vis en tabel: plads → measure/kolonne → værdi,
   og hvilke nye measures der oprettes. Spørg med AskUserQuestion. Byg ikke før godkendelse.

5. **Opret manglende measures** via MCP ud fra [measures.md](measures.md)
   (månedsakse-kolonne, `_cm`/`_pm`/`_label`/`_cm_color` pr. månedskort, margin,
   top-tekster). Format `#,0` / `0.0%`. Test alle med én samlet `EVALUATE ROW(...)`.

6. **Skriv config.json** i scratchpad med samme struktur som
   [config.example.json](config.example.json). Felter skrives `Tabel[Felt]`.
   `topN.function`: 2 = distinct count, 0 = sum (OrderBy skal være en kolonne-aggregering,
   ikke et measure). `navLabels` giver korte knaptekster (maks ~8 tegn).

7. **Generér og validér.**
   ```
   node "<skill-mappe>/scripts/gen-layout.js" "<.Report-mappe>" "<config.json>"
   powerbi-report-author validate "<.Report-mappe>"
   ```
   Siden får id `8d1e4c7a2b5f9e3d6c10`, navnet "Dashboard" og lægges først. Genkørsel
   overskriver kun denne side. Ret alle fejl i de genererede filer. Fejlen
   `PBIR_JSON_FILE_NO_SCHEMA` på `.pbip`/`definition.pbir` kommer fra Desktop selv og
   kan ignoreres.

8. **Vis i Desktop og tag skærmbillede** efter powerbi-report-cli's preview-regler
   (`--status` → open/reload → `--screenshot`). Ved `hasUnsavedChanges: true`: bed brugeren
   gemme (Ctrl+S) — Desktop kan da overskrive rapportfilerne, så kør trin 7 igen bagefter.
   Gennemgå skærmbilledet og ret fejl (tom visual, afklippet tekst, forkerte farver).

9. **Afrapportér** kort: hvad er bygget, hvilke tal der står hvor, nye measures, og
   eventuelle afvigelser fra layoutet.

## Faste regler
- Alle tal som hele tal (ingen K/M) — generatoren sætter `labelDisplayUnits` = 1.
- Ret aldrig i eksisterende sider; kun dashboard-siden og `pages.json`.
- Publicér aldrig til Fabric uden udtrykkelig besked.
