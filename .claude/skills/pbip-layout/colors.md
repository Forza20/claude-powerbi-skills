# Farver på dashboard-siden

Alle farver sættes i `colors` i config.json (hex, `#RRGGBB`). Nøgler, der mangler, får
standardværdien, så en ældre config uden `colors` giver præcis samme side som før.

| Nøgle | Bruges til | Standard |
|---|---|---|
| `page` | sidens baggrund | `#FFFFFF` |
| `panel` | baggrund i graf-, kort- og tabelbokse | `#FFFFFF` |
| `border` | kant om boksene | `#C8C6C4` |
| `ink` | titler, tal i tabeller, trend- og søjlefarve | `#252423` |
| `sub` | undertitel, akser, datalabels | `#605E5C` |
| `dark` | navigationsbjælke og KPI-/fremhævningsfliser | `#333333` |
| `onDark` | tekst og ikoner på `dark` | `#FFFFFF` |
| `teal` | tallene på KPI- og fremhævningsfliserne (accent) | `#1FC8C0` |
| `navBtn` / `navHover` | knapper i navigationsbjælken / ved hover | `#4A4A4A` / `#5C5C5C` |
| `spark` | fladen i månedskortenes sparkline | `#E1DFDD` |
| `bar` | databjælker i tabellen | `#C8C6C4` |
| `grid` | gitterlinjer i trendgrafen | `#E1DFDD` |
| `trendLine` | stiplet trendlinje | `#A19F9D` |
| `band` | forecast-båndet | `#C8C6C4` |
| `gradLow` / `gradHigh` | farveskala i tabellens sidste kolonne (lav → høj) | `#E36C78` / `#FDEDEF` |
| `negative` / `axis` | negative databjælker / databjælkens akse | `#D64550` / `#999999` |
| `white` | ældre nøgle: standard for `page`, `panel` og `onDark` | `#FFFFFF` |

Ikke styret af `colors`: månedskortenes grøn/rød kommer fra `_cm_color`-measures (measures.md).

**Resten af rapporten:** med `colors` registrerer generatoren også et Power BI-tema
(`pbip-layout-theme.json`) med samme farver: sidebaggrund (`page`), boksbaggrund og kant
(`panel`, `border`), tekst (`ink`, `sub`) og dataserier (`teal`, `dark`, `gradLow` …). Så får de
øvrige rapportsider samme udseende som dashboardet. `"theme": false` slår det fra; uden `colors`
fjernes et tidligere tema.

## Varianter

Varianterne ændrer kun farver. Placeringen er den samme (layout.md).

**1. Standard** – lys side, mørke fliser. Ingen `colors` (eller tomt objekt).

**2. Mørk**
```json
"colors": { "page": "#1E1E24", "panel": "#2A2A33", "border": "#3A3A45", "ink": "#F2F2F5", "sub": "#A8A8B3",
  "dark": "#111116", "onDark": "#FFFFFF", "teal": "#1FC8C0", "navBtn": "#2A2A33", "navHover": "#3A3A45",
  "spark": "#3A3A45", "bar": "#4A4A57", "grid": "#3A3A45", "trendLine": "#8A8A96", "band": "#4A4A57",
  "gradLow": "#E36C78", "gradHigh": "#2A2A33", "axis": "#77777F" }
```

**3. Brand** – standard, men med brugerens farver: `dark` = primærfarve, `teal` = accentfarve,
`navBtn` = en lysere tone af primærfarven, `bar`/`spark` = en lys tone af accentfarven.

## Fra et screenshot

`scripts/palette.ps1 -Path <billede>` (Windows PowerShell, ingen ekstra moduler) skalerer billedet
ned, tæller farverne og foreslår nøglerne:

| Nøgle | Hentes fra |
|---|---|
| `page` | den største flade i billedet (baggrunden) |
| `panel` | lys side: hvid; mørk side: den næststørste mørke, neutrale flade |
| `ink` | den neutrale farve med størst kontrast til `panel`, gjort mørkere/lysere til kontrast ≥ 7 |
| `teal` (accent) | den mest brugte mættede farve (knapper, links); ingen → Standards turkis |
| `dark` | en mørk brandfarve (header, footer); ingen → `#333333` (lys side) eller en mørkere `page` |
| øvrige (`sub`, `border`, `navBtn`, `spark`, `bar` …) | blandet ud fra de fire ovenfor |

Accentfarven skal kunne læses som tal på de mørke fliser (kontrast ≥ 4,5). Er den for mørk, gøres
den lysere – `accentFromImage` viser originalen, `accentAdjusted` om den er ændret. `contrastOk`
er `true`, når alle tekstpar består. Et screenshot med store fotos kan give en skæv baggrund; brug
så et udsnit med sidens header, knapper og tekst.

## Kontrast

Tjek før du bygger, at tekst kan læses: kontrastforhold mindst 4,5 for `ink` og `sub` på `panel`/`page`,
og for `teal` og `onDark` på `dark`. Er en brandfarve for lys til `dark`, så brug den som `teal`
(accent) i stedet og behold en mørk `dark`.
