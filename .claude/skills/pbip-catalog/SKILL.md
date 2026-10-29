---
name: pbip-catalog
description: Laver data catalog (Excel), data lineage (Markdown + Mermaid) og en datamodel til dbdiagram.io (DBML) for et Power BI PBIP-projekt, typisk lige efter pbip-layout. Felter på dashboard-siden tagges med deres plads (KPI 1, Månedskort 2 …), lineage går fra datakilde gennem Power Query-trin og DAX til visual, og godkendte beskrivelser kan skrives tilbage som `///` i TMDL. Trigger ALTID når brugeren skriver "Katalog:" efterfulgt af et projektnavn, når pbip-layout er færdig og brugeren siger ja til katalog, eller når brugeren beder om data catalog, datakatalog, lineage, dbdiagram, DBML eller dbdocs for et PBIP-projekt.
---

# PBIP Catalog – data catalog, lineage og dbdiagram.io

Arbejd på dansk med brugeren. Tabel-, kolonne- og measure-navne samt DAX/M gengives uændret.

Skillen bygger videre på den fælles parser i `skills/pbip-governance/scripts/parse_pbip.py`
(TMDL/PBIR → JSON med Power Query-trin, kolonne-lineage og DAX-afhængigheder). Den kopieres ikke —
`build_catalog.py` finder den selv (repo-layout, `~/.claude/skills/`, `/mnt/skills/user/`, eller
`--parser` / `PBIP_PARSER`). Format og kolonner er beskrevet i [format.md](format.md).

## Leverancer (i `<projekt>/docs/`)
| Fil | Indhold |
|---|---|
| `catalog.xlsx` | Faner: Oversigt, Tabeller, Kolonner, Measures, Dashboard, Relationer, Kilder (+ Fjernet). Turkise kolonner er til redigering. |
| `lineage.md` | Mermaid: overblik på tabelniveau, én graf pr. dashboard-plads, kolonne-lineage pr. tabel. AzDO-wiki-kompatibel (`::: mermaid`). |
| `model.dbml` | Datamodellen til dbdiagram.io / dbdocs.io med beskrivelser, DAX og dashboard-pladser i noter. |
| `catalog.json` | Maskinlæsbar version (pipeline-handoff og diff mellem kørsler). |
| `missing_descriptions.json` | Felter uden beskrivelse + kontekst, til AI-forslag. |

## Forudsætninger
- `python3` med `openpyxl`.
- PBIP i TMDL-format (`<Navn>.SemanticModel/definition/`). `model.bim` kan katalogiseres, men
  tilbageskrivning kræver TMDL. Er det en .pbix: bed om Filer → Gem som → *.pbip, og stop.
- Dashboard-tagging: `docs/layout-config.json` fra pbip-layout. Mangler den, men findes
  pbip-layout-siden (id `8d1e4c7a2b5f9e3d6c10`), udledes pladserne af visual-positionerne
  (layout.md). Ellers laves kataloget uden dashboard-tags — sig det til brugeren.

## Arbejdsgang

1. **Find projektet.** Brug stien fra pbip-layout, den uploadede mappe eller søg efter `*.pbip`.
   Output-mappen er `<projekt>/docs/`. Findes `catalog.xlsx` dér (eller uploader brugeren en
   rettet version), er det forrige kørsel — den læses og flettes, aldrig overskrives blindt
   (der laves også `catalog.backup.xlsx`).

2. **Første kørsel.**
   ```
   python3 "<skill-mappe>/scripts/build_catalog.py" "<projekt>" [--previous "<rettet catalog.xlsx>"] [--sql <mappe> ...]
   ```
   **Opstrøms kilde** udfyldes automatisk ud fra Power Query (fil › ark › kolonne,
   schema.tabel.kolonne, surrogatnøgler, beregnede kolonner, faste lister). Læser modellen fra en
   database, så led efter SQL der bygger tabellerne i repoet/uploaden (fx `supabase/migrations/`,
   `sql/`, `models/`, `*.sql` med `CREATE VIEW` eller `INSERT INTO … SELECT`) og giv mapperne med
   `--sql`. Så følges kolonnen videre gennem lagene, fx
   `silver.erp_loc_a101.cntry ← bronze.erp_loc_a101.cntry (afledt: case …)`. Nævn hvilke SQL-mapper
   der blev brugt, eller at ingen blev fundet. Tekst brugeren selv har skrevet i Opstrøms kilde
   overskrives aldrig.
   Brug `--fence github` hvis lineage.md skal vises på GitHub i stedet for Azure DevOps-wiki.
   Scriptet skriver en JSON-opsummering (antal, beskrivelsesstatus, fjernede felter).

3. **AI-forslag til manglende beskrivelser.** Læs `docs/missing_descriptions.json` og skriv
   `docs/ai_descriptions.json` som `{ "<Nøgle>": "<beskrivelse>" }`. Regler:
   - 1–2 sætninger på dansk forretningssprog: hvad tallet/feltet betyder, enhed, filtre og
     tidslogik (fx "seneste hele måned"). Brug konteksten (DAX, oprindelse, Power Query-trin,
     dashboard-plads) — opfind ikke forretningsregler der ikke står i koden.
   - Spring tekniske hjælpefelter over hvis du ikke kan sige noget meningsfuldt (lad dem stå som Mangler).
   - Prioritér felter med dashboard-plads, derefter measures, derefter synlige kolonner.
   Kør derefter igen:
   ```
   python3 "<skill-mappe>/scripts/build_catalog.py" "<projekt>" --ai-descriptions "<projekt>/docs/ai_descriptions.json"
   ```
   Præcedens: rettelser i Excel > TMDL `///` > AI-forslag. Et AI-forslag overskriver aldrig noget.

4. **Afrapportér og spørg om næste skridt** (AskUserQuestion, multi-select):
   - "Jeg retter/godkender beskrivelser i Excel" → bed om den rettede `catalog.xlsx` tilbage og gå til trin 5.
   - "Publicér på dbdocs.io" → trin 6.
   - "Færdig".
   Vis kort: antal tabeller/kolonner/measures, dashboard-felter, beskrivelsesstatus,
   mulige PII-kolonner, og hvordan man åbner `model.dbml` i dbdiagram.io
   (dbdiagram.io → Create diagram → indsæt indholdet af `model.dbml`, eller Import → DBML).

5. **Tilbageskrivning til TMDL (særskilt step, kræver godkendelse).**
   - Kør altid tørkørsel først og vis diff'en:
     ```
     python3 "<skill-mappe>/scripts/writeback_descriptions.py" "<projekt>" "<catalog.xlsx>"
     ```
   - Kun rækker med **Status = Godkendt** skrives. Kun `///`-linjer ændres — aldrig DAX, M eller properties.
   - Spørg med AskUserQuestion om diff'en må skrives. Bed brugeren lukke projektet i Power BI
     Desktop først (ellers kan Desktop overskrive filerne).
   - Ved ja: kør igen med `--apply`, og kør derefter `build_catalog.py` igen, så kataloget viser
     beskrivelserne som skrevet til modellen.

6. **dbdocs.io (valgfrit — kun på udtrykkelig besked).** Udgiver en hostet side med ER-diagram og
   søgbart katalog ud fra `model.dbml`:
   ```
   npm install -g dbdocs
   dbdocs login                      # eller sæt DBDOCS_TOKEN (dbdocs token -g)
   dbdocs build "<projekt>/docs/model.dbml" --project "<projektnavn>"
   dbdocs password --set "<kode>" --project "<projektnavn>"   # hvis siden skal være beskyttet
   ```
   Kræver netadgang og en dbdocs-konto. Fejler det, lever filerne og forklar hvordan brugeren selv kører kommandoen.

## Faste regler
- Ret aldrig DAX, Power Query eller rapportfiler. Eneste skrivning i projektet er `///`-linjer i trin 5 efter godkendelse.
- PII-markeringen er en navneheuristik: skriv "mulig PII", aldrig "er PII".
- Udgiv aldrig til dbdocs eller andre tjenester uden udtrykkelig besked.
- Gentag forbehold: statisk analyse; kolonne-lineage gennem Power Query er regex-baseret
  (komplekse M-udtryk, `Table.Combine` med flere kilder og custom-funktioner følges kun delvist);
  SQL-lineagen (`sql_lineage.py`) er også regex-baseret: CTE'er (`WITH …`), dynamisk SQL, dbt-Jinja
  og `MERGE`/`UPDATE` følges ikke — så stopper Opstrøms kilde ved det sidste led, der kunne læses.
