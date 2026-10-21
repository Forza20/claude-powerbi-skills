---
name: Measure Excel Power BI
description: >-
  Generate a structured Excel workbook (.xlsx) with a complete inventory of all DAX measures from a Power BI PBIP project: name, DAX expression, table, display folder, format string, usage stats, dependencies, and detected anti-patterns. For each anti-pattern: a suggested rewrite, a Danish explanation, and a DAX verification query for DAX Studio. Color-coded by status (USED green / DEPENDENCY-ONLY yellow / ORPHAN red), sorted hot-to-cold, auto-filter, frozen panes, and a separate "Oversigt" summary sheet. Use this skill when the user wants a spreadsheet or Excel file of Power BI measures — including "lav et Excel ark med measures", "export measures to Excel", "give me an xlsx with measure names and code", or any task asking for measure inventory in spreadsheet form. Also trigger for DAX rewrite suggestions in spreadsheet form. Excel counterpart to "Measure Analysis Power BI" — choose this for spreadsheet output, the other for PDF.
---

# Measure Excel Power BI

> **Bemærk:** De `scripts/`- og `references/`-filer, som denne SKILL.md henviser til, er ikke med i dette repo. Claude implementerer funktionaliteten ud fra beskrivelsen her (input, output-format, kolonner, layout og forbehold), og nævner det i svaret.

Statisk analyse af et Power BI Project (PBIP) der producerer et struktureret Excel-regneark med komplet measure-inventar — navn, DAX-udtryk, brug-statistik, anti-pattern-flags, **foreslået ny DAX-rewrite, årsag, og ready-to-paste verificerings-query** pr. measure.

## Hvornår skill'en skal triggers

Trigger når brugeren vil have **en spreadsheet/xlsx/regneark** der lister measures fra et Power BI-projekt. Dette er Excel-output-varianten; hvis brugeren beder om en **PDF-rapport eller narrativ analyse**, brug "Measure Analysis Power BI" i stedet.

Eksempler på prompts der triggers denne skill:
- "Lav et Excel ark med alle DAX measures i denne PBIP"
- "Export måle-koden til xlsx"
- "Give me a spreadsheet listing all measures and their DAX code"
- "Jeg skal sende en oversigt til klienten i Excel"
- "Excel-ark med foreslåede DAX-rewrites"
- "Lav verificeringsqueries til mine measures"

## Forudsætninger og input

Input skal være et komplet PBIP-projekt med både `.SemanticModel/` og `.Report/` mapperne — typisk leveret som zip. Hvis brugeren kun uploader `.pbip`-pointer-filen (~300 bytes JSON), stop og bed om hele projektet.

## End-to-end workflow

Skill'en kører i fem faser. Fase 3 er den vigtige hvor agenten (Claude) skal generere konkrete DAX-rewrites for komplekse patterns.

### Trin 1: Ekstrahér og verificér struktur

Hvis input er en zip: pak ud i et working directory under `/home/claude/`. Verificér at både `<navn>.SemanticModel/definition/tables/` og `<navn>.Report/definition/pages/` findes.

### Trin 2: Kør analyse-scriptet

```bash
python3 <skill-path>/scripts/analyze_pbip.py \
    "/path/to/PBIP project root" \
    /home/claude/analysis.json
```

### Trin 3: Generér rewrite-forslag (hybrid: regex + LLM)

Skill'en bruger en hybrid tilgang:
- **Simple patterns** (DIVIDE-konvertering, "-" → BLANK, fjern overflødigt CALCULATE) håndteres deterministisk med regex
- **Komplekse patterns** (YoY -365 → DATEADD, manuel YTD → TOTALYTD, kill-switch-refaktorering, FIXED+SUBSTITUTE → formatString, AVERAGEX(VALUES) → DIVIDE+DISTINCTCOUNT, etc.) kræver LLM-rewrites fra agenten

**3a. Generér prompt-batch:**
```bash
python3 <skill-path>/scripts/generate_rewrites.py prompts \
    /home/claude/analysis.json \
    /home/claude/llm_prompts.json
```

**3b. Agenten (Claude) genererer rewrites:**

Læs `llm_prompts.json`, generér en konkret DAX-rewrite for hver entry, skriv til `llm_responses.json`:
```json
[
  {"measure": "Belægningsprocent", "rewrite": "DIVIDE(\n    SUM(...),\n    SUM(...),\n    0\n)"}
]
```

Retningslinjer:
- Brug konkrete kolonnenavne fra original DAX, ikke placeholders
- `BLANK()` ikke `"-"`
- `DIVIDE(num, denom, 0)` for safe division
- `DATEADD(<date_col>, -1, YEAR)` for YoY (ikke -365 dage)
- `TOTALYTD(<measure>, <date_col>)` for YTD
- VAR-pattern foran iterators (kill-switch optimisation)
- For tekst-formattering (FIXED+SUBSTITUTE): erstat med numerisk + formatString-kommentar
- Bevar Danish kolonnenavne nøjagtigt

**3c. Merge:**
```bash
python3 <skill-path>/scripts/generate_rewrites.py merge \
    /home/claude/analysis.json \
    /home/claude/llm_responses.json \
    /home/claude/rewrites.json
```

### Trin 4: Generér verificerings-queries

Verificerings-queries kompletterer rewrites — de giver brugeren en ready-to-paste DAX-query der kan køres mod faktisk model i DAX Studio for at sammenligne original vs rewrite.

```bash
python3 <skill-path>/scripts/generate_verifications.py \
    /home/claude/analysis.json \
    /home/claude/rewrites.json \
    /home/claude/verifications.json
```

Scriptet genererer to typer queries:

**Individuelle queries** (én pr. måler) bruger `DEFINE MEASURE` til at injicere rewrite som en midlertidig måler, derefter `EVALUATE SUMMARIZECOLUMNS` der returnerer Original, Rewrite, Diff og Status pr. år/måned. Findes i `verifications.json` under nøglen `individual`. To kategorier:

- **`numeric_diff`**: når begge måler returnerer numerisk → simpel `[Original] - [Rewrite]` diff med `OK`/`AFVIG`-status (tolerance < 0.01 for floating-point)
- **`type_mismatch`**: når original returnerer streng `"-"` men rewrite returnerer `BLANK()`/numerisk → speciel sammenligning der tjekker `OK (begge tomme)` eller `AFVIG: original=- ny=...`

**Batch queries** (én eller flere queries der dækker ALLE målere på én gang) returnerer en sammenfatning som tabel: én række pr. måler med kolonner `Måler`, `Kind`, `Status`, `MaxDiff`. Findes i `verifications.json` under nøglen `batch_queries` som en liste. Findes typisk én batch op til 40 målere; over 40 splittes i flere batches for at undgå query-størrelses-problemer.

Brugeren paster batch-querien i DAX Studio, kører F5, og får øjeblikkeligt en oversigt over hvilke målere matcher og hvilke afviger — uden at skulle køre 50+ individuelle queries manuelt.

### Trin 5: Byg Excel-arbejdsbogen

```bash
python3 <skill-path>/scripts/build_xlsx.py \
    /home/claude/analysis.json \
    /mnt/user-data/outputs/<projekt>-Measures-Oversigt.xlsx \
    "<Projekt display navn>" \
    /home/claude/rewrites.json \
    /home/claude/verifications.json
```

Begge sidste args er valgfri — uden dem får arket tomme rewrite-/verifikations-kolonner men virker stadig som basal inventar.

### Trin 6: Lever filen

Brug `present_files`. Sammenfat kort i chat hvor mange measures har rewrites og verifikations-queries, og forklar hvordan brugeren paster query'en i DAX Studio.

## Hurtig levering uden LLM-rewrites

Hvis tid er kritisk:

```bash
python3 <skill-path>/scripts/generate_rewrites.py regex_only \
    /home/claude/analysis.json \
    /home/claude/rewrites.json
python3 <skill-path>/scripts/generate_verifications.py \
    /home/claude/analysis.json \
    /home/claude/rewrites.json \
    /home/claude/verifications.json
python3 <skill-path>/scripts/build_xlsx.py \
    /home/claude/analysis.json \
    /mnt/user-data/outputs/<projekt>-Measures-Oversigt.xlsx \
    "<Projekt display navn>" \
    /home/claude/rewrites.json \
    /home/claude/verifications.json
```

Komplekse measures får `(kompleks pattern — manuel rewrite nødvendig)` i Foreslået ny DAX-kolonnen og verifikations-kolonnen springes over for dem.

## Indhold af det genererede Excel-ark

### "Measures"-fanen (15 kolonner)

| # | Kolonne | Indhold |
|---|---------|---------|
| 1 | Measure-navn | Som defineret i TMDL |
| 2 | DAX-udtryk | Komplet DAX, monospace |
| 3 | Status | USED / DEPENDENCY-ONLY / ORPHAN |
| 4 | Tabel | TMDL-tabel |
| 5 | Display Folder | Folder-sti |
| 6 | Format String | TMDL formatString |
| 7 | Visuals (antal) | Antal visual.json-filer |
| 8 | Sider (antal) | Antal unikke sider |
| 9 | Brugt af measures (antal) | Referrer count |
| 10 | Brugt af measures (navne) | Referrer-liste |
| 11 | Refererer til measures | Dependency-liste |
| 12 | Anti-patterns fundet | Bullet-liste |
| 13 | **Foreslået ny DAX** | Konkret rewrite |
| 14 | **Årsag** | Forklaring af forbedringen |
| 15 | **Verificering (DAX-query)** | Ready-to-paste DAX Studio-query |

### Sortering, styling, navigation

Sorteret USED → DEPENDENCY-ONLY → ORPHAN, status-farvekodning, frozen panes på `B2`, auto-filter. Row heights skalerer efter længst af original DAX, rewrite, verificering, issues og reason.

## Outputs

1. Én .xlsx-fil i `/mnt/user-data/outputs/`
2. En kort chat-opsummering

## Vigtige forbehold

Når .xlsx præsenteres, gentag altid:

1. **Rewrites er statiske forslag** — verificér med queries i kolonne 15 før udrulning
2. **Verificerings-queries kører ikke automatisk** — brugeren skal åbne DAX Studio (eller Power BI Desktop's "DAX query view"), connecte til modellen, paste query, og tjekke "Status"-kolonnen for AFVIG-værdier
3. **Floating-point tolerance er 0.01** — for measures der opererer på beløb i øre kan det være for groft; for procentvise forskelle for groft. Justér i query hvis nødvendigt
4. **Type-mismatch-queries kræver visuel inspektion** — ikke alle "AFVIG"-rækker er reelle bugs; nogle er forventede konsekvenser af type-skiftet (string → numerisk)
5. **Status er pr. PBIP** — ORPHAN ≠ ubrugt globalt
