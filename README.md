# Claude skills for Power BI

Six [Claude skills](https://docs.claude.com/en/docs/agents-and-tools/agent-skills/overview) I built for my own Power BI work: auditing DAX measures, documenting PBIP projects, building a semantic model and designing reports.

> **Language:** the skills are written in Danish, and several triggers are Danish phrases. Claude can still answer in English if you ask it to.

## Skills

| Skill | What it does | When it triggers |
| --- | --- | --- |
| [agent](skills/agent/) | Runs the two measure skills below in sequence on a PBIP project and packs the output into one ZIP with a run log and a diff against the previous run | You write `Agent: <project name>` |
| [data-modeling](skills/data-modeling/) | Builds a medallion gold layer in Power Query and a finished PBIP (TMDL) from a silver Excel file, with clarifying questions and a step-by-step guide | You write `Data modeling:` |
| [data-storytelling](skills/data-storytelling/) | Turns analysis into a clear business story: visual choice per KPI, layout and visual hierarchy, drill-through and a QA checklist before a client meeting | Dashboard design or review, choosing visuals, KPI narrative, client presentations |
| [measure-analysis-power-bi](skills/measure-analysis-power-bi/) | Static analysis of a PBIP project: lists every DAX measure, marks it as used, dependency-only or orphan, flags 15+ DAX anti-patterns and writes a PDF report | Auditing, cleaning up or optimising DAX measures, finding unused measures |
| [measure-excel-power-bi](skills/measure-excel-power-bi/) | Excel inventory of all DAX measures with usage, dependencies, anti-patterns, suggested rewrites and DAX Studio verification queries | You want the measure inventory as a spreadsheet |
| [pbip-governance](skills/pbip-governance/) | Parses TMDL and PBIR to produce governance and handover documentation: data lineage, possible PII columns, RLS inventory and an Azure DevOps wiki bundle | Documenting or auditing a PBIP project, lineage, PII or RLS reviews |

`measure-analysis-power-bi` and `measure-excel-power-bi` describe helper scripts that are not included here. Claude builds that functionality from the description in each SKILL.md instead. `pbip-governance` includes its scripts.

## Install

**Claude Code:** copy a skill folder into `~/.claude/skills/`:

```bash
git clone https://github.com/Forza20/claude-powerbi-skills.git
cp -r claude-powerbi-skills/skills/pbip-governance ~/.claude/skills/
```

**Claude.ai:** zip a skill folder so the folder itself is the root of the zip, then upload it under **Settings → Customize → Skills**:

```bash
cd claude-powerbi-skills/skills
zip -r pbip-governance.zip pbip-governance/
```

Start a new conversation and use one of the triggers above.

## Licence

[MIT](LICENSE)
