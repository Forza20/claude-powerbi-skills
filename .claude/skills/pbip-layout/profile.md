# Rapportprofil

En profil gemmer brugerens valg, så de ikke skal træffes igen ved hver kørsel: farver, tema,
KPI'er, sektioner og titel. Skillen bruger profilen i stedet for at spørge (trin 3 og 4), og en
pipeline-agent kan bruge den, selvom den ikke kan spørge. Eksempel:
[profile.example.json](profile.example.json).

```json
{
  "name": "min-stil",
  "colors": { "dark": "#0B3D5C", "teal": "#F2A900", "navBtn": "#1C5A80" },
  "theme": true,
  "kpis": [
    { "slot": "KPI 1", "label": "Omsætning" },
    { "measure": "Gns. ordreværdi" },
    { "slot": "KPI 4" }
  ],
  "sections": { "monthly": 2, "highlights": 1, "bar": true, "table": true },
  "title": "Salgsoverblik",
  "subtitle": "Seneste hele måned"
}
```

| Felt | Betydning | Udeladt |
|---|---|---|
| `colors` | farver, nøgler som i [colors.md](colors.md) | *Standard* |
| `theme` | samme farver på alle rapportsider (tema i `StaticResources/RegisteredResources`) | `true`, når `colors` er sat |
| `kpis` | 1–4 KPI'er i rækkefølge. `slot` = forslaget fra layout.md (`KPI 1`–`KPI 4`); `measure` = navnet på et measure i modellen (store/små bogstaver er ligegyldige); `label` = tekst under tallet | forslaget KPI 1–4 |
| `sections.monthly` | antal månedskort, 0–3 | 3 |
| `sections.highlights` | antal fremhævningsfliser, 0–2 | 2 |
| `sections.bar` / `sections.table` | søjlediagram / top-tabel med eller ej | `true` |
| `title` / `subtitle` | sidens titel og undertitel | layoutets |

Sådan bruges felterne:
- `colors`, `theme`, `sections`, `title` og `subtitle` kopieres uændret til config.json.
- `kpis` oversættes til config-formatet: `slot` → det measure, kortlægningen (trin 4) fandt til pladsen;
  `measure` → `Tabel[Measure]` fra modellen. Findes et navngivet measure ikke, så brug forslaget for
  samme nummer, og skriv det under "Åbne punkter" (pipeline) eller spørg (med bruger).
- Profilen ændrer aldrig placeringen af det, der vises – kun hvad der vises og i hvilke farver.
- Det, der udelades, fordeles: færre KPI'er, månedskort eller fremhævninger fylder rækken ud;
  uden søjlediagram eller tabel får den anden hele højre kolonne; uden begge bliver trenden bred.
