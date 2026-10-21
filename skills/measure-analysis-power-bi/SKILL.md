---
name: Measure Analysis Power BI
description: >-
  Static analysis of Power BI PBIP projects: inventory all DAX measures, classify usage as USED / DEPENDENCY-ONLY / ORPHAN by cross-referencing visual.json files, detect 15+ DAX anti-patterns (manual division-guards, manual YoY/-365 patterns, manual YTD construction, AVERAGEX/SUMX over VALUES, trailing-operator bugs, "-"-string returns, redundant CALCULATE wrappers, FORMAT-in-measure), and produce a Danish-language PDF report with prioritized action list. Use this skill whenever the user asks to analyze, audit, review, optimize, or clean up DAX measures in a Power BI project — including "PBIP analysis", "find unused measures", "DAX optimization", "measure audit", "rens op i model", "find orphan measures", "audit min Power BI model", "DAX best practices review", or any task involving a .pbip file or TMDL files. Also trigger for measure-usage questions like "where is measure X used?" or "which measures are not in use?".
---

# Measure Analysis Power BI

> **Bemærk:** De `scripts/`- og `references/`-filer, som denne SKILL.md henviser til, er ikke med i dette repo. Claude implementerer funktionaliteten ud fra beskrivelsen her (input, output-format, kolonner, layout og forbehold), og nævner det i svaret.

End-to-end statisk analyse af PBIP-projekter (Power BI Project format). Skill'en parser TMDL-semantic-model og PBIR-rapport-JSON, producerer measure-inventar, krydsreferencer brug på tværs af visuals og measures, detekterer DAX anti-patterns, og leverer en Danish-language PDF-rapport.

## Hvornår skill'en skal triggers

Trigger på enhver opgave hvor brugeren vil:
- Auditere measures i en PBIP-model
- Finde ubrugte ("orphan") measures
- Identificere DAX-optimerings-kandidater
- Få en oversigt over hvilke measures der bruges hvor
- Lave governance-dokumentation af en model
- Rydde op i en model før hand-over

Skill'en virker både når brugeren uploader en zip af et PBIP-projekt og når brugeren peger på en lokal mappe i Claude Code.

## Forudsætninger og input

Input skal være et komplet PBIP-projekt med disse to mapper:
```
<projekt>/
├── <ProjektNavn>.SemanticModel/
│   └── definition/tables/*.tmdl
└── <ProjektNavn>.Report/
    └── definition/pages/<page-id>/visuals/<visual-id>/visual.json
```

Hvis brugeren kun uploader `.pbip`-pointer-filen (typisk ~300 bytes JSON), er det IKKE nok — skill'en skal stoppe og bede om hele projektet (zippet er fint).

## End-to-end workflow

### Trin 1: Ekstrahér og verificér struktur

Hvis input er en zip: pak den ud i et working directory under `/home/claude/`.

Verificér at både `.SemanticModel/definition/tables/` og `.Report/definition/pages/` findes. Tæl `.tmdl`-filer og `visual.json`-filer for at give brugeren et indtryk af modellens størrelse.

### Trin 2: Kør analyse-scriptet

Brug `scripts/analyze_pbip.py`. Scriptet tager projekt-roden som argument og producerer en `analysis.json`-fil:

```bash
python3 /home/claude/skill-name/scripts/analyze_pbip.py \
    "/path/to/PBIP project root" \
    /home/claude/analysis.json
```

Scriptet udfører tre passes:
1. **Discovery** — parser alle TMDL-filer og udvinder measures (navn, DAX-udtryk, format string, display folder, description)
2. **Usage** — scanner alle `visual.json` for `"Measure"` block-references og bygger measure-to-measure dependency-graph fra DAX-bodies
3. **Anti-pattern detection** — kører 15+ regex-baserede tjeks mod hver measure's DAX

Scriptet udskriver et resumé til stdout (status counts, top issues) og gemmer den fulde analyse som JSON.

### Trin 3: Generér PDF-rapport

Brug `scripts/build_report.py`. Det læser `analysis.json` og producerer en HTML-rapport som derefter konverteres til PDF med WeasyPrint:

```bash
python3 /home/claude/skill-name/scripts/build_report.py \
    /home/claude/analysis.json \
    /home/claude/report.html \
    "<Projekt-navn til titel>"

weasyprint /home/claude/report.html /mnt/user-data/outputs/<projekt>-DAX-Analyse.pdf
```

Endeligt: brug `present_files` til at give brugeren PDF'en.

### Trin 4: Sammenfat fund i chat

Efter PDF'en er leveret, opsummer kort i chat:
- Total antal measures + status-fordeling (USED/DEP/ORPHAN)
- Top 3-5 mest signifikante fund (ofte: bugs, orphan-grupper, mest gentagne anti-pattern)
- En vigtig advarsel om at det er statisk analyse og at performance-claims skal verificeres mod Performance Analyzer

## Anti-patterns scriptet detekterer

Scriptet detekterer disse DAX anti-patterns. Detaljerede beskrivelser findes i `references/dax-antipatterns.md` — læs den fil hvis du skal forklare et specifikt fund eller foreslå en konkret rewrite.

| ID | Pattern | Fix |
|----|---------|-----|
| AP01 | `IF(SUM(x)<=0/=Blank, 0, .../x)` | `DIVIDE(num, denom, 0)` |
| AP02 | `MIN(date)-365 .. MAX(date)-365` | `DATEADD(date, -1, YEAR)` eller `SAMEPERIODLASTYEAR` |
| AP03 | Manuel YTD med `Min/Max(date)` + `year(now())` | `TOTALYTD` / `DATESYTD` |
| AP04 | `AVERAGEX(VALUES(table[col]), CALCULATE(SUM(...)))` | Verificér mod simpel `DIVIDE(SUM, DISTINCTCOUNT)` |
| AP05 | `FILTER(table, ...)` uden `ALL()` | Boolean filter direkte i `CALCULATE` |
| AP06 | `SELECTEDVALUE`-kill-switch foran `AVERAGEX/SUMX` | Flyt kill-switch til wrapper |
| AP07 | `CALCULATE(SUM(x))` uden filter-arg | Fjern overflødigt CALCULATE |
| AP08 | `SUMX(DISTINCT/VALUES(...), ...)` | `SUMX(SUMMARIZE(...))` eller pre-aggregeret measure |
| AP09 | `CALCULATE([A]/[B])` | `DIVIDE([A], [B], 0)` |
| AP10 | `FIXED + SUBSTITUTE` til formattering | `formatString` på measure |
| AP11 | DAX slutter med trailing operator (`*`, `/`, `+`, `-`) | **Bug** — fjern eller komplettér |
| AP12 | `CALCULATE(FORMAT(...))` | Fjern CALCULATE |
| AP13 | Returnerer streng `"-"` i stedet for `BLANK()` | `BLANK()` + formatString |
| AP14 | `EARLIER()` brug | `VAR` til at fange row context |
| AP15 | `ALL(date)` som separat CALCULATE-arg | Verificér semantik (kan være buggy) |

## Outputs

Skill'en producerer altid:
1. Én PDF-rapport i `/mnt/user-data/outputs/`
2. En kort chat-opsummering (3-5 hovedfund)

Skill'en producerer IKKE:
- Ændringer i selve TMDL-filerne (det er en separat opgave brugeren styrer interaktivt)
- Performance-målinger (kræver Power BI Desktop + DAX Studio)

## Vigtige forbehold som altid skal kommunikeres

Når PDF'en præsenteres, gentag altid disse forbehold i chat:

1. **Statisk analyse** — alle performance-claims er pattern-baserede, ikke målte. Verificér med Performance Analyzer + DAX Studio før du tager dem som sandhed.
2. **Orphan-status er pr. PBIP-projekt** — measures kan stadig bruges i (a) paginerede rapporter (.rdl), (b) Q&A synonyms, (c) RLS-regler udenfor TMDL-tables. Tjek disse før sletning.
3. **Dansk-sproget rapport** — passer til danske leverancer og dansk consulting context. Hvis brugeren beder om engelsk, byg HTML'en med engelske strenge.

## Hvis brugeren beder om noget mere end basis-analysen

- **"Generér også TMDL-rewrites for top-N anti-patterns"** — det er udenfor scope; foreslå at de kører Claude Code interaktivt i projektmappen og bruger fundene som input.
- **"Lav diagram af measure-dependencies"** — hver measures dependencies er allerede i `analysis.json`. Brug Mermaid `flowchart LR` med edges fra dependent→helper. Kør evt. en separat tool-call.
- **"Eksportér til Excel/CSV"** — `analysis.json` indeholder alt; konvertér med pandas til xlsx hvis efterspurgt.

## Test-prompt eksempler skill'en bør håndtere godt

- "Analyser de DAX measures der bruges i denne PBIP fil og giv mig en optimerings-rapport"
- "Find orphan measures i min Power BI model"
- "Audit min hotel-rapport for DAX best practices"
- "Hvilke measures bliver ikke brugt i min model?"
- "Lav en governance-rapport for denne PBIP"
- "Check min model for DAX anti-patterns"
