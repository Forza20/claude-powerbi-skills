---
name: pbip-layout
description: Anvender det gemte "Salgsoverblik"-dashboardlayout (mørke KPI-fliser, trend med forecast, månedskort, kategori-søjler, top 10-tabel, fremhævningsfliser) på et Power BI PBIP-projekt og kobler det til projektets egne measures. Trigger ALTID når brugeren skriver `anvend "layout.md"` (også uden anførselstegn, fx "anvend layout.md") sammen med en PBIP-fil/-mappe eller et åbent PBIP-projekt i Power BI Desktop, og når en pipeline-agent (fx `layout-applier`) bliver bedt om at anvende layoutet – se "Pipeline-tilstand".
---

# Anvend layout.md på et PBIP-projekt

Layoutet er beskrevet i [layout.md](layout.md). Generatoren
[scripts/gen-layout.js](scripts/gen-layout.js) bygger siden ud fra en konfigurationsfil;
[config.example.json](config.example.json) er den oprindelige konfiguration
(Data Modeling PBIP). DAX-skabeloner til manglende measures ligger i
[measures.md](measures.md). Farvenøgler og færdige varianter står i [colors.md](colors.md).
Brugerens faste valg (farver, KPI'er, sektioner, titel) kan gemmes som en profil: [profile.md](profile.md).

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
   Forbinder MCP-serveren ikke: læs TMDL-filerne direkte (se "Uden powerbi-modeling-mcp").

   **Profil:** Har brugeren en profil (en `.json` efter [profile.md](profile.md), fx nævnt eller
   uploadet), så læs den nu. Det, profilen fastlægger, spørges der ikke om i trin 3 og 4. Nævn kort,
   hvilke valg der kommer fra profilen.

3. **Farver (kun med en bruger til stede).** Spørg med AskUserQuestion om brugeren har
   farvekoder (en `.md`-fil eller hex-koder) eller et screenshot af en hjemmeside/et brand, som
   farverne skal komme fra. Har brugeren ingen af delene, bruges *Standard* fra colors.md.
   - Lav højst 2 varianter, der kun ændrer farver. Placeringen er fast (layout.md), så
     varianterne må ikke love en anden fordeling af KPI'er eller grafer. Brug fx *Standard* og *Brand*,
     eller *Mørk* og *Brand*.
   - Sæt farverne med `colors`-nøglerne i colors.md. Udled de manglende toner fra primær- og
     accentfarven efter reglen under "Brand".
   - Tjek kontrasten (colors.md → Kontrast). Er en farve for lys som flise-baggrund, brug den som accent.
   - Med egne farver får de øvrige rapportsider samme farver gennem et tema (`theme`, standard til).
     Spørg kun, hvis rapporten har sider, brugeren måske vil beholde som de er.
   *I pipeline-tilstand:* spring trinnet over. Brug profilens farver, hvis der er en profil (se
   Pipeline-tilstand), ellers *Standard* (ingen `colors`).

4. **Kortlæg pladserne.** Brug tabellen "Pladser der skal kobles til modellen" i
   [layout.md](layout.md). Find for hver plads det bedste eksisterende measure/kolonne;
   brug fallback når data mangler (fx ingen returer → margin % eller aktive kunder).
   Kør DAX-forespørgsler for at kende værdierne (total, kategorier, seneste måned).
   Tjek fx om en "line_total" er før/efter rabat, og om cost er pr. stk.
   **KPI-fliserne vælger brugeren selv** (kun med en bruger til stede):
   - Vis forslaget til KPI 1–4 fra tabellen, og en liste over modellens øvrige measures, der giver ét
     tal: navn, værdi og visningsmappe. Udelad hjælpe-measures (`_cm`, `_pm`, `_label`, `_color`, `_spark`).
   - Spørg med AskUserQuestion (multiSelect), hvilke 1–4 KPI'er der skal vises, og om teksten under
     tallet skal være measure-navnet eller en egen tekst (maks ~20 tegn). Rækkefølgen er den, brugeren
     vælger i.
   - Vælger brugeren et tal, modellen ikke har (fx "gns. ordreværdi"), så foreslå DAX ud fra
     measures.md og opret det i trin 6. Gæt ikke på forretningsregler: spørg, hvis definitionen er uklar.
   - Fliserne fordeles jævnt over rækken: 1–4 fliser, aldrig huller. `kpis` i config.json har én
     post pr. valgt KPI i den valgte rækkefølge.
   **Sektionerne vælger brugeren også** (samme AskUserQuestion-runde, kun med en bruger til stede):
   antal månedskort (0–3), antal fremhævningsfliser (0–2), og om søjlediagram og top-tabel skal med.
   Svaret står i `sections` i config.json. Det, der fravælges, giver plads til resten (profile.md,
   sidste punkt). Standard er alt med.
   *I pipeline-tilstand:* brug profilens `kpis` og `sections`, ellers forslaget KPI 1–4 og alle
   sektioner, uden at spørge.

5. **Vis kortlægningen og eksemplerne, og få godkendelse.** Skriv config.json (trin 7) for hver
   farvevariant, og lav et HTML-eksempel med generatoren selv. Den skriver ingen rapportfiler i
   denne tilstand, og placeringen er den samme som i Power BI:
   ```
   node "<skill-mappe>/scripts/gen-layout.js" "<.Report-mappe>" "<config.json>" --preview "<scratchpad>/layout-<variant>.html"
   ```
   Vis en tabel: plads → measure/kolonne → værdi (med de valgte KPI'er), og hvilke nye measures der oprettes. Vis også
   eksemplerne. Kan sessionen udgive sider (Artifact-værktøjet), så udgiv dem som private sider;
   ellers giv stien til filerne. Spørg med AskUserQuestion om kortlægningen og hvilken variant.
   Byg ikke før godkendelse. Tallene i eksemplet er pladsholdere – sig det.
   *I pipeline-tilstand:* spørg ikke og lav ingen eksempler – skriv tabellen til fil og fortsæt (se nedenfor).

6. **Opret manglende measures** via MCP ud fra [measures.md](measures.md)
   (månedsakse-kolonne, `_cm`/`_pm`/`_label`/`_cm_color` pr. månedskort, margin,
   top-tekster). Format `#,0` / `0.0%`. Test alle med én samlet `EVALUATE ROW(...)`.
   Slutter data midt i en måned: månedskort, sparklines og trend bruger kun hele måneder
   (`_spark`-measures i measures.md), så kurverne ikke ender med et kunstigt fald.

7. **Skriv config.json** i scratchpad med samme struktur som
   [config.example.json](config.example.json). Felter skrives `Tabel[Felt]`. Den valgte
   farvevariant står i `colors` (nøgler: colors.md); uden `colors` bruges *Standard*.
   Valgte sektioner står i `sections`, temaet i `theme`, og titel/undertitel i `title`/`subtitle`
   (felterne er beskrevet i profile.md).
   `topN.function`: 2 = distinct count, 0 = sum (OrderBy skal være en kolonne-aggregering,
   ikke et measure). TopN beholder uafgjorte, så tabellen kan vise mere end 10 rækker – nævn det
   i afrapporteringen (eller `layout-mapping.md`), eller tilføj et tiebreaker-measure. `navLabels` giver korte knaptekster (maks ~8 tegn).
   Gem også en kopi som `<projektmappe>/docs/layout-config.json` (opret `docs/`), så
   pbip-catalog kan tagge felterne med deres plads på dashboardet.

8. **Generér og validér.**
   ```
   node "<skill-mappe>/scripts/gen-layout.js" "<.Report-mappe>" "<config.json>"
   powerbi-report-author validate "<.Report-mappe>"
   ```
   Siden får id `8d1e4c7a2b5f9e3d6c10`, navnet "Dashboard" og lægges først. Genkørsel
   overskriver kun denne side. Ret alle fejl i de genererede filer. Fejlen
   `PBIR_JSON_FILE_NO_SCHEMA` på `.pbip`/`definition.pbir` kommer fra Desktop selv og
   kan ignoreres.

9. **Vis i Desktop og tag skærmbillede** efter powerbi-report-cli's preview-regler
   (`--status` → open/reload → `--screenshot`). Ved `hasUnsavedChanges: true`: bed brugeren
   gemme (Ctrl+S) — Desktop kan da overskrive rapportfilerne, så kør trin 8 igen bagefter.
   Gennemgå skærmbilledet og ret fejl (tom visual, afklippet tekst, forkerte farver).
   Tjek især at KPI- og fremhævningsfliserne har `dark`-farven fra config (standard `#333333`), og at
   farverne svarer til det godkendte eksempel. `cardVisual` tegner sin egen hvide
   flise ("Layout med flere kort → Baggrund"); generatoren slår den fra med
   `objects.layout.backgroundShow = false` (`fillCustom.transparency = 100` alene virker ikke). Er fliserne
   alligevel hvide bokse med mørk kant, så notér det under "Åbne punkter" i `layout-mapping.md` – eller,
   med en bruger til stede: få brugeren til at slå baggrunden fra på én flise i Desktop, gem, sammenlign
   `visual.json` før/efter, og ret `card()` i `scripts/gen-layout.js` med den egenskab, Desktop skrev.
   *I pipeline-tilstand:* bed ikke brugeren om noget – stop og meld tilbage (se nedenfor).

10. **Afrapportér** kort: hvad er bygget, hvilke tal der står hvor, nye measures, og
    eventuelle afvigelser fra layoutet og den valgte farvevariant.
    Har brugeren valgt farver, KPI'er eller sektioner uden en profil: tilbyd at gemme valgene som
    profil (profile.md), fx `profiles/<navn>.json` i brugerens projekt eller pipeline-repo. KPI'er
    gemmes med measure-navn (`measure`), så profilen også passer på andre modeller med samme navne.

11. **Tilbyd data catalog.** Spørg om skillen `pbip-catalog` skal køres nu (data catalog i Excel,
    lineage og dbdiagram.io-model ud fra projektet og `docs/layout-config.json`). Ved ja: indlæs
    `pbip-catalog` med Skill-værktøjet, eller følg `.claude/skills/pbip-catalog/SKILL.md` i repoet.
    *I pipeline-tilstand:* spørg ikke – skriv i `layout-mapping.md`, at kataloget kan køres bagefter.

## Faste regler
- Alle tal som hele tal (ingen K/M) — generatoren sætter `labelDisplayUnits` = 1.
- Ret aldrig i eksisterende sider; kun dashboard-siden og `pages.json`. Undtagelse: med egne farver
  registrerer generatoren et tema (`StaticResources/RegisteredResources/pbip-layout-theme.json` og
  `customTheme` i `definition/report.json`), som de øvrige sider følger. Uden farver fjernes det igen.
- Publicér aldrig til Fabric uden udtrykkelig besked.

## Pipeline-tilstand (kørt af en agent uden bruger)

Gælder når skillen køres af en subagent, fx `layout-applier` i `/messy-pipeline`, eller når opgaven
siger "pipeline-tilstand". En subagent kan ikke stille spørgsmål til brugeren, så:

- **Profil:** har opgaven eller `run.json` (`profile`) en profilsti, så brug den profil til farver,
  tema, KPI'er, sektioner og titel (profile.md). Ellers *Standard*: ingen `colors`, forslaget KPI 1–4
  og alle sektioner. Skriv i `layout-mapping.md`, hvilken profil der blev brugt, og hvilke
  profil-measures der ikke fandtes i modellen.
- **Trin 3 (farver):** spørg ikke; brug profilen eller *Standard*. Lav ingen HTML-eksempler.
- **Trin 5 (godkendelse):** skriv kortlægningstabellen (plads → measure/kolonne → værdi → nye
  measures → brugt fallback) til `layout-mapping.md` i kørselsmappen, og fortsæt uden at spørge.
  Vælg altid den plads-kobling, der står først i tabellen i layout.md; brug fallback kun når modellen
  mangler data, og skriv hvilken.
- **Trin 9 (Desktop):** tjek først at Desktop er lukket, før filer skrives. Er Desktop åben med
  ugemte ændringer, eller fejler åbning/skærmbillede (hukommelse, login): forsøg ikke igen, skriv ikke
  videre, og afslut med status `waiting_for_user` og årsagen. Den kaldende orkestrator spørger brugeren.
- **Ingen AskUserQuestion** nogen steder. Al tvivl skrives som en "Åbne punkter"-liste i
  `layout-mapping.md` sammen med det valg, du traf.
- **Skills:** indlæs `powerbi-authoring:semantic-model-authoring` og
  `powerbi-authoring:powerbi-report-cli` med Skill-værktøjet. Findes de ikke i sessionen: følg denne
  fil alene og notér det i `layout-mapping.md`.
- **Formatering:** reglen "alle tal som hele tal" gælder dashboard-siden, også hvis andre sider i
  projektet bruger mio. Nævn forskellen i `layout-mapping.md`; ret ikke de andre sider.

### Uden powerbi-modeling-mcp

Når MCP-serveren ikke forbinder (i og uden for pipeline-tilstand):

- **Model:** læs tabeller, kolonner, measures og relationer direkte i
  `<Navn>.SemanticModel/definition/*.tmdl` og `tables/*.tmdl`.
- **Værdier (trin 4):** kan DAX ikke køres, så hent kontroltallene fra kilden. For en PBIP bygget med
  `supabase-medallion-powerbi`: SQL på gold-skemaet via Supabase MCP, eller projektets
  `expected-values.md`.
- **Nye measures (trin 6):** skriv dem direkte i `tables/_Measures.tmdl` (eller den eksisterende
  measure-tabel) med **Desktop lukket**: tab-indrykning, ét nyt GUID pr. `lineageTag`, navne i
  anførselstegn ved mellemrum, flerlinjet DAX ét niveau dybere end egenskaberne. Kontrollér bagefter,
  at ingen lineageTag går igen, og at ingen linje er indrykket med mellemrum.
- **Test:** i stedet for `EVALUATE ROW(...)`: åbn i Desktop (trin 9) og sammenlign kort og tabel med
  kontroltallene fra kilden.
