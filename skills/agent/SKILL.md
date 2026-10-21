---
name: agent
description: >-
  Kør en sekvens af Power BI skills som en agent-pipeline for et PBIP-projekt. Trigger ALTID når brugeren skriver "Agent:" efterfulgt af et projektnavn — fx "Agent: Salgsrapport" eller "Agent: Økonomi dashboard". Skillen tjekker hvilke sub-skills der er installeret, spørger interaktivt hvilke steps der skal inkluderes, genbruger allerede uploadede PBIP-filer (eller beder om upload), og kører herefter de valgte skills i rækkefølge med fælles data-handoff. Leverer en samlet ZIP med alle outputs, kørselslog og diff mod forrige kørsel. Brug denne skill til automatiseret ugentlig PBIP health check eller som forberedelse til en leverance.
---

# Agent — PBIP Pipeline Operator (v2)

Koordinerer en sekvens af eksisterende Power BI skills og pakker outputtet i en samlet ZIP-fil med kørselslog. Designet til at køre uden unødige stop.

---

## Trigger

Aktiveres når brugeren skriver:
```
Agent: <projektnavn>
```

Eksempel: `Agent: Salgsrapport`, `Agent: Økonomi dashboard`

---

## Step 0 — Tilgængeligheds-tjek

Før menuen vises: tjek hvilke sub-skills der faktisk er installeret:

```bash
ls /mnt/skills/user/
```

Pipeline-steps og deres krævede skills:

| Step | Skill-mappe | Output |
|------|-------------|--------|
| 1 | `measure-analysis-power-bi` | DAX-audit PDF (orphans, anti-patterns) |
| 2 | `measure-excel-power-bi` | Measure-inventar XLSX med rewrites + verificeringsqueries |

**Vis kun installerede steps i menuen.** Hvis et step mangler, nævn det kort ("Step 2 er ikke installeret i denne session") — stop ikke pipelinen af den grund.

**Scripts-fallback:** Sub-skills kan referere til `scripts/*.py` som ikke er bundlet i sessionen. Hvis en scripts-mappe mangler: implementér funktionaliteten efter SKILL.md-spec'en i stedet (input, output-format, kolonner, layout og forbehold er fuldt beskrevet dér). Nævn det i kørselsloggen. Stop ALDRIG pipelinen fordi et script mangler.

---

## Step 1 — Interaktivt step-valg

Præsentér menuen med de tilgængelige steps (brug `ask_user_input_v0` med multi-select hvis muligt):

```
Jeg har fundet følgende tilgængelige steps til [projektnavn]:

  [1] Measure Analysis     → DAX-audit, orphans, anti-patterns (PDF)
  [2] Measure Excel        → Measure-inventar med rewrites (XLSX)

Hvilke steps vil du inkludere?
```

Afvent brugerens svar før du fortsætter. Tilbyd altid en "alle tilgængelige"-mulighed.

---

## Step 2 — Filinput

**Tjek FØRST om en PBIP-zip allerede er uploadet** (kig i `/mnt/user-data/uploads/` og i beskeden der triggede skillen). Hvis ja: brug den og skriv kort at upload-steppet springes over.

Hvis ingen fil findes, bed om upload:

```
Upload venligst dit PBIP-projekt som en ZIP-fil.
```

Verificér efter udpakning at både `<navn>.SemanticModel/definition/tables/` og `<navn>.Report/definition/pages/` findes. Hvis kun `.pbip`-pointer-filen er uploadet (~300 bytes JSON), stop og bed om hele projektet.

---

## Step 3 — Kør pipeline

Kør de valgte steps i nummereret rækkefølge. For hvert step: **læs sub-skillens `SKILL.md` først** og følg dens workflow.

### Data-handoff mellem steps

Steps deler data — kør analysen én gang og genbrug:

```
Step 1 ──► analysis.json ──► Step 2 (genbrug — kør IKKE analysen igen)
```

- Gem mellemresultater i `/home/claude/` (`analysis.json`, `rewrites.json`, `verifications.json`)

### Fejlstrategi

Hvis et step fejler:
1. Notér fejlen i kørselsloggen (step, årsag, evt. workaround)
2. **Fortsæt med de resterende steps** — undtagen steps der direkte afhænger af det fejlede steps output
3. Rapportér alle fejl samlet i den afsluttende opsummering

Stop kun hele pipelinen hvis selve PBIP-strukturen er ugyldig.

---

## Step 4 — Kørselslog og diff

### Kørselslog

Generér altid `KOERSELSLOG.md` i output-mappen med:

```markdown
# Agent-kørsel: <projektnavn>
Dato: <YYYY-MM-DD HH:MM>
Steps kørt: [1, 2]
Steps sprunget over: []

## Nøgletal
- Measures i alt: N (USED: x / DEPENDENCY-ONLY: y / ORPHAN: z)
- Anti-patterns: <AP-id × antal, ...>
- Rewrites foreslået: N

## Leverancer
- <filnavn> (step 1)
- ...

## Bemærkninger
- <scripts-fallback brugt / fejl>
```

### Diff mod forrige kørsel

Gem en maskinlæsbar snapshot `agent_state_<projektnavn>.json` i output-mappen med measure-navne, status og anti-pattern-id'er pr. measure.

Ved hver kørsel: **bed brugeren uploade forrige kørsels state-fil hvis de vil have diff** (sessioner deler ikke filsystem — filen fra sidste kørsel ligger i brugerens forrige ZIP). Hvis en state-fil er uploadet eller findes:

- Sammenlign og rapportér i kørselsloggen under `## Ændringer siden sidst`:
  - Nye measures / slettede measures
  - Nye anti-patterns / løste anti-patterns
  - Status-skift (fx ORPHAN → USED)
- Hvis ingen state-fil findes: skriv "Første kørsel — ingen diff tilgængelig" og fortsæt.

---

## Step 5 — Saml og lever

1. Gem alle step-outputs i `/mnt/user-data/outputs/agent_<projektnavn>/`
2. Tilføj `KOERSELSLOG.md` og `agent_state_<projektnavn>.json`
3. Pak alt i én ZIP: `/mnt/user-data/outputs/agent_<projektnavn>_leverancepakke.zip`
4. Brug `present_files` med ZIP'en først, derefter de vigtigste enkeltfiler
5. Afslut med kort opsummering i chat:
   - Hovedfund (3-5 punkter)
   - Sub-skillsenes standardforbehold (statisk analyse, verificér i DAX Studio, orphan-status er pr. PBIP)
   - Evt. fejl eller fallbacks

---

## Vigtige principper

- **Læs altid hver sub-skills SKILL.md før dens step køres** — følg dens workflow, output-format og forbehold
- **Spørg kun én gang** — step-valget er det eneste obligatoriske stop
- **Genbrug data** — analysen køres én gang, ikke pr. step
- **Fejl stopper ikke pipelinen** — de logges og rapporteres
- **Gentag altid sub-skillsenes forbehold** i den afsluttende opsummering
