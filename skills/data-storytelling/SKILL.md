---
name: data-storytelling
description: Forvandl analyser og rådata til klare forretningsfortællinger i Power BI dashboards, PowerPoint-forslag og klientpræsentationer. Aktivér når brugeren designer eller reviewer et dashboard, vælger visualtype til en KPI, strukturerer drill-through eller narrativ, anvender farve og visuelt hierarki, bygger pre-kickoff PowerPoint, eller QA'er en leverance før klientmøde. Triggerord — DK&EN — "data storytelling", "fortælling med data", "dashboard-design", "dashboard-review", "vælg visualisering/visual", "KPI-narrativ", "visuel hierarki", "drill-through", "client presentation", "stakeholder report".
---

# Data Storytelling

Skill til BI-konsulent-workflow: fra klientbehov til præsentationsklart Power BI dashboard og understøttende PowerPoint. Skrevet til en kontekst hvor leveringen sker som klientmøde, ikke som en delt URL.

## Hvornår denne skill er relevant

- Du designer et nyt dashboard og skal vælge layout og visuals
- Du reviewer et eksisterende dashboard før klientpræsentation
- Du bygger en pre-kickoff PowerPoint med KPI-forslag
- Du strukturerer drill-through-flow eller bookmark-narrativer
- Du QA'er en leverance før klientmødet (definition af done)
- En kollega eller udvikler beder om feedback på et dashboard-mock

## Kerneprincipper

1. **Færre visuals, ikke flere.** Hver visual skal svare på ét spørgsmål klienten har. Hvis du ikke kan formulere spørgsmålet, fjern den.
2. **Konklusion først.** Visuallens overskrift er konklusionen, ikke metricnavnet. "Omsætning Q1: -12%" slår "Omsætning per kvartal".
3. **Hierarki sender øjet.** Den vigtigste insight skal kunne læses på 10 sekunder uden brugerens bevidste søgning. Top-venstre er det dyreste pixel-real-estate.
4. **Farve har en regel.** Rød/grøn kun til performance-signal. Brug altid sekundær signal (ikon, tegn, label) — 8% af mænd har farveblindhed.
5. **Performance er fortælling.** Et dashboard der loader > 1 min har tabt klienten. Storytelling stopper ved loading-spinner.
6. **Dokumentation er en del af leverancen.** Alle measures og dimensions skal være defineret i Wiki før definition af done — ellers er fortællingen uefterprøvelig.

## 5-trins workflow: fra brief til klientklar fortælling

**1. Spørg "hvad skal klienten beslutte"** — ikke "hvad har klienten af data". KPI'er der ikke driver en beslutning er støj.

**2. Skriv narrativet i tekst først.** 3-5 sætninger. "Omsætningen er faldet i Q1 drevet af region Nord. Marketing-spend er konstant, så ROI falder. Anbefaling: omfordel budget til region Syd." Hvis du ikke kan skrive det, har du intet at vise.

**3. Map sætninger til visuals.** Én sætning = én visual. Vælg visualtype efter sætningens type (se `references/chart-selection.md`).

**4. Layout efter narrativ orden, ikke efter datakilde.** F-pattern: top-venstre = headline-konklusion, derefter understøttende detaljer mod højre og nedad. Drill-through til den dybe analyse, ikke som default-visning.

**5. QA mod fortællingen.** Læs visuals i rækkefølge højt. Hænger fortællingen sammen? Mangler der en bro mellem to visuals? Er der visuals uden plads i fortællingen — fjern dem.

## Pre-delivery checklist

Inden et dashboard sendes til klientmøde:

- Kan jeg læse hovedkonklusionen på forsiden uden at klikke?
- Har hver visual en konklusionsoverskrift, ikke kun et metricnavn?
- Er drill-through-stien åbenbar (ikon, instruktion, eller logisk placering)?
- Bruges rød/grøn kun til performance-signal — og altid med sekundær markør?
- Er filtre placeret konsistent på tværs af sider (samme position, samme rækkefølge)?
- Loader rapporten under 1 minut på klientens forventede datavolumen?
- Er alle measures og dimensions dokumenteret i Wiki?
- Er alle tal verificeret mod kilde — ingen DAX-forsinkelse eller filterkontekst-bug?

## Standardfejl jeg ofte ser

- KPI-cards med 12 metrics i toppen — ingen er vigtig hvis alle er
- Donut-charts med >5 kategorier — illæselig
- "Year over year" sammenligning som default når klienten kun bruger MTD
- Drill-through der returnerer til samme side — bryder fortællingen
- Tabeller med 30 kolonner i en præsentationsrapport — det hører til i Excel-eksport
- Slicers øverst på siden uden default-værdi — klienten ser tom rapport
- Conditional formatting uden legend — farver uden forklaring

## Output-format efter opgavetype

| Opgave                           | Leveranceformat                                      |
| -------------------------------- | ---------------------------------------------------- |
| Pre-kickoff KPI-forslag          | PowerPoint, 5-8 KPI'er, en slide per KPI med rationale |
| Dashboard-mock                   | PowerPoint eller wireframe, 1-2 sider                |
| Færdigt dashboard                | Power BI .pbix + Wiki-dokumentation                  |
| Klientpræsentation af færdig BI  | Live demo i mødet + 1-pager handout med konklusioner |
| Review/feedback på kollegaarbejde | Punktvis kommentar pr. visual + revideret layout-skitse |

## Når du svarer i denne skill

- Skriv på dansk medmindre andet er bedt
- Korte punkter, aktiv sætningsstruktur, ingen AI-klicheer
- Gem deliverables i `OUTPUTS/<projektnavn>/`
- Mind om Wiki-dokumentation hvis brugeren ikke selv nævner det
- Flagér performance-risici proaktivt
- Skel mellem klienttyper — offentlig sektor ≠ finans ≠ retail

## Referencer (læs efter behov)

- `references/chart-selection.md` — map sætningstype til visualtype
- `references/color-and-hierarchy.md` — farvepalet, F-pattern, accessibility
- `references/power-bi-patterns.md` — DAX-narrativer, drill-through, bookmarks, themes
- `references/client-presentation.md` — pre-kickoff PowerPoint, handover-møde, 1-pager-handout
