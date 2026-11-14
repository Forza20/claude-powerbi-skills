---
name: pbip-layout
description: Bygger en af to rapportskabeloner ind i et Power BI PBIP-projekt – AdventureWorks (Exec Dashboard, Map, Product Detail, Customer Detail, Category Tooltip, Q&A, Decomposition Tree, Key Influencers – taget fra adventureworks_report.pbix med farver, navigation, bogmærker og layout) eller Business (Home + modulerne Marketing, Sales og Finance med hver sit overblik og drillthrough; skabelonens measures laves ud fra modellens egne kolonner) og kobler hvert faneblad til projektets egne measures og kolonner. Brugeren vælger altid, hvilke faneblade der skal med; farver kan komme fra HEX-koder eller et screenshot og ændrer kun farverne. Trigger ALTID når brugeren skriver `anvend "layout.md"` (også uden anførselstegn, fx "anvend layout.md") sammen med en PBIP-fil/-mappe eller et åbent PBIP-projekt i Power BI Desktop, og når en pipeline-agent (fx `layout-applier`) bliver bedt om at anvende layoutet – se "Pipeline-tilstand".
disable-model-invocation: true
---

# Anvend rapportskabelonen på et PBIP-projekt

Der er to skabeloner, begge rigtige rapporter skilt ad i `templates/<nøgle>/` (faneblade, visuals,
bogmærker, ikoner; hver farve er en farvenøgle):
- **`adventureworks`** – salgsrapporten. [layout.md](layout.md) beskriver fanebladene og hvert skabelonfelt
  med hvad det skal være og en reserveløsning.
- **`business`** – Home + modulerne Marketing, Sales, Finance (overblik + drillthrough hver).
  [layout-business.md](layout-business.md): modulerne, datakontrakten, farverne. Her kobles *kolonner* til en
  datakontrakt, og [scripts/gen-measures.js](scripts/gen-measures.js) laver skabelonens measures og felterne.

[scripts/gen-report.js](scripts/gen-report.js) bygger de valgte faneblade fra en config
([config.example.json](config.example.json)). Measures og parametre: [measures.md](measures.md). Farver:
[colors.md](colors.md). Faste valg: en profil ([profile.md](profile.md)).

Arbejd med brugeren på brugerens sprog.

## Forudsætninger
- Indlæs skills `powerbi-authoring:semantic-model-authoring` (measures) og
  `powerbi-authoring:powerbi-report-cli` (PBIR, validate, preview), og følg deres regler.
- `powerbi-report-author` CLI installeret (`npm install -g @microsoft/powerbi-report-authoring-cli@latest`).
- Projektet skal være PBIP i PBIR-format (`<Navn>.Report/definition/pages`). En .pbix: bed brugeren om
  Filer → Gem som → *.pbip, og stop.

## Arbejdsgang

1. **Find projektet.** Den uploadede/navngivne sti, ellers søg efter `*.pbip`. Notér `.Report`-mappen.

2. **Forbind til modellen.** Åben i Power BI Desktop: powerbi-modeling-mcp (`ListLocalInstances` →
   `Connect`); ellers `ConnectFolder` på `<Navn>.SemanticModel/definition`. List tabeller, kolonner,
   measures og relationer (uden MCP: læs TMDL'en, "Uden powerbi-modeling-mcp"). Læs brugerens profil, hvis
   der er en, og sig hvilke valg der kommer fra den.

3. **Skabelon og faneblade – spørg altid, også med en profil.** Først skabelonen (én AskUserQuestion), når
   den ikke er givet (`config.template`, profilens `template`, `run.json → layout_template`):
   "AdventureWorks – salgsrapport (ordrer, produkter, kunder, kort)" · "Business – Marketing, Sales og Finance
   (Home + moduler)". Anbefal ud fra modellen: leads/kampagner, opportunities/pipeline eller
   hovedbog/kontotyper → Business; ordrelinjer med produkter og kunder → AdventureWorks.
   **Business:** ét multiSelect "Hvilke moduler og faneblade skal rapporten have?" – Home · Marketing
   (+ Campaign Detail) · Sales (+ Opportunity Detail) · Finance (+ P&L Detail); beskrivelsen siger, hvad
   modellen har eller mangler til modulet (layout-business.md → Påkrævet pr. modul). Et modul giver begge
   dets faneblade; spørg kun om drillthrough-siden særskilt, hvis modellen ikke kan fylde den.
   **AdventureWorks:** AskUserQuestion med to multiSelect-spørgsmål; hver
   mulighed = et faneblad, beskrivelsen = hvad det viser, og hvad modellen har eller mangler til det
   (layout.md → Faneblade):
   - "Hvilke dashboard-faneblade skal rapporten have?" – Exec Dashboard, Map, Product Detail, Customer Detail
   - "Hvilke analyse-faneblade skal rapporten have?" – Category Tooltip, Q&A, Decomposition Tree, Key Influencers
   En profils `pages` markeres "(plejer at blive valgt)". Anbefal ikke et faneblad, modellen ikke kan fylde
   (et kort uden en placeringskolonne). Svaret er `config.pages`. Intet valgt: stop og spørg igen.

4. **Farver (kun med en bruger til stede).** Spørg, om brugeren har farvekoder (HEX, en `.md`-fil) eller
   et screenshot af en hjemmeside eller et brand. Ingen af delene: *Standard* – skabelonens egne farver.
   - **Et farvevalg ændrer kun farver.** HEX-koder eller et screenshot udfylder kun `colors` (og `theme`) i
     config.json – faneblade, felter, tekster, skrifttyper, talformater og placeringer er præcis som med
     *Standard*. Generatoren afviser ukendte nøgler og alt, der ikke er `#RRGGBB`;
     `node "<skill-mappe>/tests/colors-only.test.js"` og `tests/business.test.js` beviser det – kør begge efter
   ændringer i `gen-report.js`. Business-nøglerne: layout-business.md → Farver (good/bad/neutral er faste).
   - **Screenshot:** mål farverne i stedet for at gætte:
     `powershell -NoProfile -ExecutionPolicy Bypass -File "<skill-mappe>/scripts/palette.ps1" -Path "<billede>"`
     → `suggestion` har hver farvenøgle; nævn `accentAdjusted`. Stien til et indsat billede står i beskeden
     (`[Image: source: …]`); uden fil: aflæs farverne visuelt og sig, at de er skønnede.
   - HEX-koder: kobl dem til nøglerne (colors.md → "Fra HEX-koder"); tjek kontrasten (colors.md).
   - Højst 2 varianter (fx *Standard* og *Brand*); de adskiller sig kun i farver.
   *I pipeline-tilstand:* profilens farver, ellers *Standard*.

5. **Kobl skabelonfelterne.** *Business:* kobl datakontrakten i stedet og lad `gen-measures.js` lave
   measures og felter (layout-business.md → Datakontrakt → measures): `suggest-fields.js` foreslår
   `config.contract`, du tjekker betydning og værdier (`config.values`), og
   `node "<skill-mappe>/scripts/gen-measures.js" "<config.json>" --write-config --spec … | --tmdl …` skriver
   measures og `config.fields`. Hver `skipped` measure og hver `derive`-kolonne er en beslutning (trin 7).
   Spring trin 6 over. *AdventureWorks:* start med forslaget:
   `node "<skill-mappe>/scripts/suggest-fields.js" "<.SemanticModel-mappe>" --config "<config.json>"`
   (config.json med `template` og `pages`; det udfylder `fields` ud fra navne i
   `templates/<nøgle>/field-hints.json` og skriver `how` pr. felt – navn, reserveløsning, `make: <opskrift>`
   eller ingen – og de `decisions` en reserveløsning gav). Tjek det derefter felt for felt med layout.md's
   tabeller – det forventede indhold først, så reserveløsningen, `null` når intet passer. Kør DAX for at kende værdierne. Tjek
   betydninger: er en "line total" før eller efter rabat; er en rate "høj = dårlig" (skabelonen: returrate).
   Når en reserveløsning ændrer betydningen: sæt `labels` og `texts` (template.json → `pages[].texts` har
   hver tekst præcist). `node gen-report.js … --preview` lister hvert felt, der ikke er koblet.

6. **Measures og parametre fanebladene skal bruge** (measures.md): forrige måned, targets, afvigelser,
   prisjustering, omsætning pr. kunde, feltparametrene. Targets: modellens egne, når den har dem; ellers
   spørg brugeren om væksten i forhold til sidste måned (profil `targetGrowth`, skabelonen 10 %). I en
   pipeline-power-bi-kørsel skrives de i `choices.json → build`, og `rebuild.js` bygger modellen – aldrig i
   hånden i TMDL'en dér.

7. **Vis koblingen og et preview, og få godkendelse.** Skriv config.json (trin 8) og
   ```
   node "<skill-mappe>/scripts/gen-report.js" - "<config.json>" --preview "<scratchpad>/layout-preview.html"
   ```
   (en wireframe af de valgte faneblade: placeringer, størrelser, baggrundsfarver, titler og felter; Power
   BI tegner selve visuals). Vis en tabel: faneblad → skabelonfelt → modelfelt → værdi, nye measures, og hvad
   der udelades (`dropped`). Udgiv previewet som privat side, når Artifact-værktøjet findes, ellers giv
   stien. Spørg med AskUserQuestion om koblingen og farverne, **og hver beslutning** (nedenfor); byg først
   efter godkendelse. *I pipeline-tilstand:* intet preview, intet spørgsmål – tabellen skrives i
   `layout-mapping.md`, beslutningerne i `layout-decisions.json`.

   **Beslutninger – brugeren bestemmer, med din anbefaling.** Det, dataene lader stå åbent, vælges ikke i
   stilhed og noteres ikke bare: det er en beslutning med din anbefaling og alternativerne. Typisk:
   - en reserveløsning der ændrer betydningen (margin % hvor skabelonen har en returrate): farveskalaens
     retning (`reverseScales`), teksterne (`texts`) eller en anden measure;
   - targets: modellens egne, eller sidste måned + en vækst (5 / 10 / 15 %);
   - et skabelonfelt uden match (`null`): udelad feltet eller visualet, eller brug et navngivet alternativ;
   - et faneblad modellen ikke kan fylde godt (et kort med kun byer, Key Influencers med få attributter);
   - en synlig kolonne med persondata på et faneblad (topkunder).
   Spørg med AskUserQuestion, højst 4 pr. kald: pr. beslutning ét spørgsmål der står alene (hvad dataene
   viser, hvorfor det betyder noget), anbefalingen først med "(Recommended)" og begrundelsen i beskrivelsen,
   derefter 1–3 alternativer med deres virkning; brugeren kan altid skrive sit eget ("Other"). Indarbejd
   svarene i config.json (eller measures), før der bygges.

8. **config.json** (scratchpad) som [config.example.json](config.example.json) (Business:
   [config.example-business.json](config.example-business.json) – desuden `contract`, `values`, `currencyFormat`): `template`, `pages`,
   `fields` (`Tabel[Felt]` eller `null`), `labels`, `texts`, `reverseScales` (skabelonfelter hvis
   farveskalaer skal gå den anden vej), `title`/`subtitle` eller `logo`, `colors`, `theme`,
   `completeMonth` (`Tabel[Kolonne]`, en sand/falsk kolonne i datotabellen, der er sand for hele
   måneder, fx `dim_date[is_complete_month]`; `suggest-fields.js` foreslår den). Månedskortene (KPI)
   filtreres til hele måneder, ellers ender de i en tom eller halv måned og viser "(Tom)" / -100 %.
   Mangler kolonnen: foreslå at tilføje den i datotabellen (anbefalet) eller accepter advarslen. Gem en kopi som `<projektmappe>/docs/layout-config.json` (opret `docs/`), så pbip-catalog kan
   mærke felterne med deres faneblad.

9. **Generér og tjek.**
   ```
   node "<skill-mappe>/scripts/gen-report.js" "<.Report-mappe>" "<config.json>"
   node "<skill-mappe>/scripts/check-fields.js" "<.Report-mappe>" "<.SemanticModel-mappe>"
   node "<skill-mappe>/scripts/validate-report.js" "<.Report-mappe>"
   ```
   `gen-report.js` skriver fanebladene (med id'er), bogmærkerne, `dropped` (udeladte visuals og hvorfor) og
   `notes` (felter udeladt af et visual, basistema ændret). `check-fields.js` skal sige `ok: true`: hvert
   felt rapporten bruger findes i modellen. `validate-report.js` kører `powerbi-report-author validate` og
   holder skabelonens kendte fund (`known`) adskilt fra nye (`new`); `ok: true` = ingen ny fejl. De kendte
   stammer fra skabelonens kilderapport (Desktop skrev dem): `PBIR_FORMATTING_PROP_NESTED` på
   `anomalyDetection` (omsætningstrenden), `PBIR_VISUAL_TYPE_DEPRECATED` (`map`, `qnaVisual`),
   `PBIR_DRILLTHROUGH_BACK_BUTTON_MISSING`, `PBIR_JSON_FILE_NO_SCHEMA` på `.pbip`/`definition.pbir`,
   `PBIR_SCHEMA_UNREACHABLE` offline – "ret" dem ikke. Ret alt under `new`. En ny kørsel erstatter fanebladene fra den forrige
   (samme id'er) og lader rapportens egne faneblade være.

10. **Vis det i Desktop og tag et screenshot** efter powerbi-report-cli's preview-regler (`--status` →
    åbn/genindlæs → `--screenshot`), ét pr. faneblad. Med `hasUnsavedChanges: true`: bed brugeren gemme
    (Ctrl+S) – Desktop kan så overskrive rapportfilerne, så kør trin 9 igen bagefter. Tjek: ingen tomme
    visuals eller fejlikoner, fliserne i `dark` med `teal` tal, navigationsknapper kun til de valgte
    faneblade, filterpanelet åbner med filterikonet, drillthrough til Product Detail virker.
    *I pipeline-tilstand:* spørg ikke – stop og meld tilbage (se nedenfor).

11. **Rapportér** kort: de byggede faneblade, hvilket modelfelt der står hvor, nye measures og parametre,
    hvad der blev udeladt, farverne. Tilbyd at gemme valgene som profil (profile.md), fx `profiles/<navn>.json`.

12. **Tilbyd et datakatalog** (`pbip-catalog`, læser `docs/layout-config.json`). *I pipeline-tilstand:*
    spørg ikke – skriv i `layout-mapping.md`, at kataloget kan køres bagefter.

## Faste regler
- Fanebladene er 1280 × 720 og beholder skabelonens layout og formater.
- Visningsenheder er altid "Ingen": tal vises aldrig som "tusind", K eller mio., men som heltal eller
  decimaltal efter measurets formatstreng. `gen-report.js` sætter det på hvert visual
  (`scripts/display-units.js`); en ældre rapport rettes med `node scripts/display-units.js <Navn>.Report`.
- Brugeren vælger fanebladene, hver gang. Byg aldrig et faneblad, brugeren ikke har valgt.
- Ændr aldrig rapportens egne faneblade. Det generatoren ændrer ud over sine faneblade: `pages.json` (dens
  faneblade først), bogmærker til dens faneblade, dens ikoner og et logo, basistemaet (→ skabelonens) og
  farvetemaet `pbip-layout-theme.json` (kun farver).
- Udgiv aldrig til Fabric uden en udtrykkelig instruks.

## Pipeline-tilstand (kørt af en agent uden bruger)

Når en subagent kører skillen (`layout-applier` i `/messy-pipeline`, en pipeline-power-bi-kørsel), eller
opgaven siger "pipeline-tilstand":

- **Skabelon:** `run.json` → `layout_template` (`adventureworks` hvis den mangler).
- **Faneblade:** orkestratoren spurgte brugeren før kørslen – fanebladene står i `run.json` → `layout_pages`
  (eller opgaven). **Ingen faneblade angivet: vælg dem ikke selv** – afslut med status `waiting_for_user`
  og årsagen "faneblade ikke valgt"; orkestratoren spørger.
- **Profil:** `run.json` → `profile` giver farver, titel, labels, tekster og target-vækst. Ellers
  *Standard*; target-væksten er en beslutning (nedenfor).
- **Ingen AskUserQuestion** – men heller ingen stille valg. Hver beslutning (trin 7) skrives i
  `layout-decisions.json` i kørselsmappen, og **anbefalingen anvendes**, så kørslen bliver færdig:
  ```json
  [ { "id": "return-rate-scale", "question": "Dataene har ingen returer; margin % står hvor skabelonen viser returraten. Hvilken vej skal farveskalaen gå?",
      "why": "I skabelonen er høj = rød (dårlig); for margin er høj godt.",
      "options": [ { "label": "Høj margin = lys, lav = rød", "recommended": true, "effect": "reverseScales: [\"Measure Table[Return Rate]\"]" },
                   { "label": "Behold skabelonens retning", "effect": "ingen ændring" } ],
      "applied": "Høj margin = lys, lav = rød" } ]
  ```
  Orkestratoren (`/messy-pipeline`, pipeline-power-bi's overdragelse) stiller brugeren spørgsmålene med
  AskUserQuestion; et andet svar end det anvendte ændrer config.json, og `gen-report.js` køres igen.
- **Kobling:** skriv `layout-mapping.md` i kørselsmappen: faneblad → skabelonfelt → modelfelt → værdi →
  reserveløsning; nye measures og parametre; `dropped`; beslutningerne og hvad der blev anvendt. Første match i layout.md vinder; en
  reserveløsning kun når modellen mangler data.
- **Desktop (trin 10):** tjek at Desktop er lukket, før der skrives. Er Desktop åben med ugemte ændringer,
  eller fejler åbning/screenshot (hukommelse, login): prøv ikke igen, skriv ikke videre, afslut med
  `waiting_for_user` og årsagen.
- **Skills:** indlæs `powerbi-authoring:semantic-model-authoring` og `powerbi-authoring:powerbi-report-cli`
  med Skill-værktøjet; mangler de, følg denne fil alene og notér det.

### Uden powerbi-modeling-mcp

- **Model:** læs tabeller, kolonner, measures og relationer i `<Navn>.SemanticModel/definition/tables/*.tmdl`.
- **Værdier (trin 5):** kan DAX ikke køres, tag kontrolværdierne fra kilden (`expected-values.md`, eller SQL
  på gold-skemaet for et supabase-medallion-powerbi-projekt).
- **Nye measures (trin 6):** uden for en pipeline-power-bi-kørsel skrives de i measuretabellens TMDL med
  **Desktop lukket**: tab-indrykning, en ny GUID pr. `lineageTag`, navne i anførselstegn når de indeholder
  mellemrum. Tjek at ingen lineageTag gentages.
- **Test:** åbn i Desktop (trin 10) og sammenlign KPI-fliserne med kontrolværdierne.

## Lav en skabelon fra en anden rapport

`node "<skill-mappe>/scripts/extract-template.js" "<Navn.Report>" "<skill-mappe>/templates/<nøgle>"`
gør en rapport gemt som PBIP (PBIR) til en skabelon. `--keys <sæt>` vælger farvenøgler, fanebladsnøgler,
temaets seriefarver og rettelser til kilderapporten (`KEYSETS` i scriptet; `business` for Business-skabelonen).
Den stopper ved en farve, den ikke har en nøgle til (tilføj den i sættets `classify()`; `'fixed'` = farven
bliver som den er), beholder de håndskrevne filer (`field-hints.json`, `modules.json`, `contract.json`,
`measures/`), fjerner formatering bundet til enkelte dataværdier og logoet, og skriver
template.json (faneblade, felter, tekster, farver, ikoner). Beskriv derefter fanebladene og felterne i
layout.md og kør testen.
