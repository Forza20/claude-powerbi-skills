# Farver

Hver farve på skabelonens faneblade er en farvenøgle (template.json → `colors`). `colors` i config.json
sætter dem (HEX, `#RRGGBB`); en nøgle der udelades beholder skabelonens farve, så uden `colors` ser
fanebladene præcis ud som kilderapporten (*Standard*). `colors` ændrer kun farveværdier: faneblade, visuals,
placeringer, størrelser, felter, skrifttyper, talformater, tekster og bogmærker er ens for alle varianter
(`tests/colors-only.test.js`). En ukendt nøgle eller en værdi, der ikke er `#RRGGBB`, stopper generatoren.

| Nøgle | Bruges til | Skabelon |
|---|---|---|
| `dark` | navigationsskinne, KPI- og fremhævningsfliser, figurer, dataserier, tooltip-baggrund | `#333333` |
| `teal` | accent: KPI-værdier, datalabels, aktive navigationsikoner, fremhævninger | `#20E2D7` |
| `onDark` | tekst og ikoner på `dark` | `#FFFFFF` |
| `panel` | lyse baggrunde, den lave ende af farveskalaer | `#FFFFFF` |
| `muted` | sekundære titler | `#666666` |
| `soft` | baggrund på slicer-elementer | `#E6E6E6` |
| `bar` | databjælker i tabeller | `#CCCCCC` |
| `axis` | databjælkernes akse; temaets tekstfarve | `#252423` |
| `bad` | fald, høj returrate (rød = dårligere) | `#DE6A73` |
| `badDark` | returserien | `#A1343C` |
| `gold` | anden seriefarve (donuts) | `#E1C233` |

Navigationsikonerne farves også om med nøglerne (de hvide = `onDark`, accentikonerne = `teal`). Temaet
`pbip-layout-theme.json` indeholder kun farver: seriefarverne starter med `dark`, `gold`, `teal`, `bad`, så
grafer uden egen farve følger valget. `"theme": false` udelader temaet.

## Varianter (kun farver)

**1. Standard** – skabelonen som den er. Ingen `colors`.

**2. Mørk**
```json
"colors": { "dark": "#111116", "muted": "#A8A8B3", "teal": "#1FC8C0", "onDark": "#F2F2F5", "panel": "#2A2A33",
  "soft": "#3A3A45", "bar": "#4A4A57", "axis": "#F2F2F5" }
```

**3. Brand** – brugerens farver: `dark` = primærfarve, `teal` = accentfarve, `gold` = en anden brandfarve.
Behold `bad` rød, medmindre brandet siger andet: den betyder "dårligere".

## Fra HEX-koder

Kobl brugerens koder til nøglerne: den mørkeste brandfarve → `dark`, den mest synlige → `teal`, en anden
→ `gold`; tekst og baggrund kun når brugeren beder om en mørk eller farvet side.

## Fra et screenshot

`scripts/palette.ps1 -Path <billede>` (Windows PowerShell, ingen ekstra moduler) skalerer billedet ned,
tæller farverne og foreslår hver nøgle (`suggestion`):

| Nøgle | Tages fra |
|---|---|
| `panel` | lyst billede: hvid; mørkt billede: det næststørste mørke, neutrale område |
| `axis` | den neutrale farve med mest kontrast til `panel`, gjort mørkere/lysere til kontrast ≥ 7 |
| `teal` | den mest brugte mættede farve (knapper, links); ingen → `#1FC8C0` |
| `dark` | en mørk brandfarve (header, footer); ingen → `#333333` |
| `gold` | en anden mættet farve med en anden farvetone (ikke rød); ingen → skabelonens |
| `muted`, `soft`, `bar` | blandet af ovenstående; `bad`, `badDark` forbliver røde |

Accentfarven skal kunne læses som tal på de mørke fliser (kontrast ≥ 4,5); er den for mørk, gøres den
lysere – `accentFromImage` viser originalen, `accentAdjusted` om den blev ændret. `contrastOk` er `true`, når
alle tekstpar består. Et screenshot med store fotos kan skævvride baggrunden (`siteIsDark: true` for en lys
side): brug et udsnit med header, knapper og tekst.

## Kontrast

Tjek før du bygger: `onDark` og `teal` på `dark` mindst 4,5; `axis` og `muted` på `panel` mindst 4,5. Er en
brandfarve for lys til `dark`, så brug den som `teal` og behold en mørk `dark`.
