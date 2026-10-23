# Layout: Salgsoverblik (dark-tile executive)

Genskabt efter et AdventureWorks-forlæg. Én side, 1920 × 1080, hvid baggrund.
Alle tal vises som **hele tal** (ingen K/M-enheder).

## Farver og typografi
| Rolle | Farve |
|---|---|
| Navigationsbjælke, KPI-fliser, fremhævningsfliser | `#333333` |
| KPI-værdier | `#1FC8C0` (turkis), Segoe UI Bold |
| Linjer, søjler, tekst | `#252423` |
| Sekundær tekst | `#605E5C` |
| Kantlinjer på kort/diagrammer | `#C8C6C4`, radius 8 (KPI-fliser radius 16) |
| Sparkline-fyld | `#E1DFDD` |
| Tabel-gradient (lav → høj) | `#E36C78` → `#FDEDEF` |
| Fald i månedskort | `#D64550` (via farve-measure) |

## Placeringer (x, y, bredde, højde)
| # | Element | Visual | Position | Indhold |
|---|---|---|---|---|
| 1 | Navigationsbjælke | shape | 0, 0, 80, 1080 | mørk baggrund |
| 2 | Tilbage-knap | actionButton | 8, 16, 64, 44 | ikon "back" |
| 3 | Side-knapper (≤3) | actionButton | 8, nederst, 64, 44 | navigation til øvrige sider |
| 4 | Titel | textbox | 104, 52, 256, 96 | titel + undertitel |
| 5–8 | KPI-fliser | cardVisual | y 20, h 148, w 364; x 376 / 764 / 1152 / 1540 | 4 hoved-KPI'er, label under værdi |
| 9 | Trend | lineChart | 96, 200, 952, 548 | hovedmeasure pr. måned, kontinuerlig akse, trendlinje, forecast, zoom-slider |
| 10–12 | Månedskort | areaChart + 2 × cardVisual | y 772, h 284, w 300; x 96 / 422 / 748 | sparkline, seneste måned (farve efter op/ned), "Forrige måned: X (±Y%)" |
| 13 | Søjler pr. kategori | clusteredBarChart | 1072, 200, 832, 320 | measure pr. kategori, sorteret faldende, blanke skjult |
| 14 | Top 10-tabel | tableEx | 1072, 544, 832, 340 | række + 3 measures, data bars, rød gradient på %-kolonne, TopN 10 |
| 15–16 | Fremhævninger | textbox + cardVisual | overskrift y 904 h 32; flise y 944 h 112; w 404; x 1072 / 1500 | tekst-measures (fx top-kategori, top-kanal) |

## Pladser der skal kobles til modellen
| Plads | Forventet indhold | Fallback hvis modellen mangler det |
|---|---|---|
| KPI 1 | Omsætning | — (påkrævet) |
| KPI 2 | Antal ordrer | antal rækker / transaktioner |
| KPI 3 | Indtjening / profit | omsætning efter rabat, gns. ordreværdi |
| KPI 4 | Rate i % (margin, returrate) | margin %, andel aktive kunder |
| Trend | Omsætning pr. måned | — |
| Månedskort 1–3 | Omsætning, ordrer, tredje nøgletal (returer/kunder) | aktive kunder |
| Søjler | Ordrer pr. produktkategori | omsætning pr. kategori / segment |
| Tabel | Top 10 produkter: ordrer, omsætning, %-nøgletal | top 10 kunder |
| Fremhævning 1–2 | Kategori/segment med flest ordrer; næstvigtigste "top"-tekst | top-kanal, top-region |
