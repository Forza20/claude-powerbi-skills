# Rapportprofil

En profil gemmer brugerens faste valg, så de ikke skal træffes igen ved hver kørsel: farver, de faneblade
brugeren plejer at vælge, titel, logo, navne og tekster. Eksempel: [profile.example.json](profile.example.json).

```json
{
  "name": "min-stil",
  "pages": ["exec", "map", "product", "customer", "tooltip"],
  "colors": { "dark": "#0B3D5C", "teal": "#F2A900", "gold": "#1C5A80" },
  "theme": true,
  "title": "Salgsoverblik",
  "subtitle": "Seneste hele måned",
  "logo": "C:\\brand\\logo.png",
  "targetGrowth": 0.1,
  "labels": { "Measure Table[Total Profit]": "Dækningsbidrag" },
  "texts": { "Monthly Returns": "Monthly Customers" }
}
```

| Felt | Betydning | Hvis udeladt |
|---|---|---|
| `pages` | de faneblade brugeren plejer at vælge (nøgler i layout.md). **Kun et forslag**: brugeren spørges stadig hver gang (SKILL.md trin 3); i pipeline-tilstand spørger orkestratoren før kørslen | alle faneblade forvalgt |
| `colors` | farvenøgler ([colors.md](colors.md)) | skabelonens farver (*Standard*) |
| `theme` | `false` = registrér ikke farvetemaet | registreres |
| `title` / `subtitle` | øverst til venstre på Exec Dashboard (hvor kilderapporten har sit logo) | "Salgsoverblik" |
| `logo` | sti til brugerens eget logo (.png/.jpg) – vises i stedet for titlen | titlen |
| `targetGrowth` | vækst til targets, når modellen ingen har (measures.md "Targets") | spørges; skabelonen 0,1 |
| `labels`, `texts` | viste navne for felter; erstattede titler og tekstbokse (layout.md) | modellens navne; skabelonens tekster |

Sådan bruges den:
- `colors`, `theme`, `title`, `subtitle`, `logo`, `labels` og `texts` kopieres til config.json.
- `pages` forvælger svarene i spørgsmålet om faneblade; det brugeren krydser af, bliver `config.pages`.
- Profilen ændrer aldrig layoutet på et faneblad – kun hvilke faneblade der bygges, deres farver og tekster.
