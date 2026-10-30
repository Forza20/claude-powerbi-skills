// Generates the "Salgsoverblik" dashboard page (PBIR) into a PBIP report folder.
// Usage: node gen-layout.js "<path to .Report folder>" "<path to config.json>"
// Field references in config use DAX notation: "Table[Field]".
const fs = require('fs');
const path = require('path');

const [reportDir, configPath] = process.argv.slice(2);
if (!reportDir || !configPath) throw new Error('Usage: node gen-layout.js <ReportFolder> <config.json>');
const cfg = JSON.parse(fs.readFileSync(configPath, 'utf8'));

const PAGE_ID = cfg.pageId || '8d1e4c7a2b5f9e3d6c10';
const pagesDir = path.join(reportDir, 'definition', 'pages');

// Reuse $schema versions from the existing report (never guess them).
function findSchema(fileName, fallback) {
  if (!fs.existsSync(pagesDir)) return fallback;
  const stack = [pagesDir];
  while (stack.length) {
    const d = stack.pop();
    for (const e of fs.readdirSync(d, { withFileTypes: true })) {
      const p = path.join(d, e.name);
      if (e.isDirectory()) { if (!p.includes(PAGE_ID)) stack.push(p); }
      else if (e.name === fileName) {
        try { const s = JSON.parse(fs.readFileSync(p, 'utf8')).$schema; if (s) return s; } catch (_) {}
      }
    }
  }
  return fallback;
}
const SCHEMA_VISUAL = findSchema('visual.json', 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/visualContainer/2.9.0/schema.json');
const SCHEMA_PAGE = findSchema('page.json', 'https://developer.microsoft.com/json-schemas/fabric/item/report/definition/page/2.1.0/schema.json');

const C = Object.assign({
  dark: '#333333', teal: '#1FC8C0', ink: '#252423', sub: '#605E5C',
  border: '#C8C6C4', white: '#FFFFFF', spark: '#E1DFDD', bar: '#C8C6C4',
  gradLow: '#E36C78', gradHigh: '#FDEDEF',
}, cfg.colors || {});

// ---------- helpers ----------
const lit = v => ({ expr: { Literal: { Value: v } } });
const str = s => lit(`'${String(s).replace(/'/g, "''")}'`);
const num = n => lit(`${n}D`);
const int = n => lit(`${n}L`);
const bool = b => lit(b ? 'true' : 'false');
const color = hex => ({ solid: { color: lit(`'${hex}'`) } });
const def = { id: 'default' };

function ref(s) {
  const m = /^'?(.+?)'?\[(.+)\]$/.exec(s);
  if (!m) throw new Error(`Bad field reference "${s}" – use Table[Field]`);
  return { table: m[1], name: m[2] };
}
const measureField = s => { const r = ref(s); return { Measure: { Expression: { SourceRef: { Entity: r.table } }, Property: r.name } }; };
const columnField = s => { const r = ref(s); return { Column: { Expression: { SourceRef: { Entity: r.table } }, Property: r.name } }; };
const qref = s => { const r = ref(s); return `${r.table}.${r.name}`; };
const projM = (s, displayName) => { const r = ref(s); const p = { field: measureField(s), queryRef: qref(s), nativeQueryRef: r.name }; if (displayName) p.displayName = displayName; return p; };
const projC = (s, displayName) => { const r = ref(s); const p = { field: columnField(s), queryRef: qref(s), nativeQueryRef: r.name }; if (displayName) p.displayName = displayName; return p; };

let seq = 0;
const vid = () => { seq += 1; return ('d5b0a1' + seq.toString(16).padStart(4, '0') + 'c3e7f9a2b4').slice(0, 20); };
const visuals = [];
function add(v, pos, z) {
  const { filterConfig, ...visual } = v;
  const c = { $schema: SCHEMA_VISUAL, name: vid(), position: { x: pos[0], y: pos[1], z, height: pos[3], width: pos[2], tabOrder: z }, visual };
  if (filterConfig) c.filterConfig = filterConfig;
  visuals.push(c);
}
function vco({ bg = null, radius = 0, borderColor = null, title = null, titleSize = 12, pad = 8 } = {}) {
  return {
    background: bg ? [{ properties: { show: bool(true), color: color(bg), transparency: num(0) } }] : [{ properties: { show: bool(false) } }],
    border: (borderColor || bg)
      ? [{ properties: { show: bool(true), color: color(borderColor || bg), radius: num(radius), width: num(1) } }]
      : [{ properties: { show: bool(false) } }],
    padding: [{ properties: { top: num(pad), bottom: num(pad), left: num(pad), right: num(pad) } }],
    visualHeader: [{ properties: { show: bool(false) } }],
    dropShadow: [{ properties: { show: bool(false) } }],
    title: title
      ? [{ properties: { show: bool(true), text: str(title), fontSize: num(titleSize), alignment: str('center'), fontColor: color(C.ink), bold: bool(false) } }]
      : [{ properties: { show: bool(false) } }],
  };
}
// Whole numbers everywhere (no K/M display units).
const WHOLE = { labelDisplayUnits: str('1') };

// ---------- 1. navigation rail ----------
add({
  visualType: 'shape',
  objects: {
    shape: [{ properties: { tileShape: str('rectangle') } }],
    fill: [{ properties: { fillColor: color(C.dark), transparency: num(0) }, selector: def }],
    outline: [{ properties: { show: bool(false) }, selector: def }],
  },
  visualContainerObjects: vco({ pad: 0 }),
}, [0, 0, 80, 1080], 0);

function navButton({ y, label, icon, link }) {
  add({
    visualType: 'actionButton',
    objects: {
      text: label
        ? [{ properties: { show: bool(true) } }, { properties: { text: str(label), fontSize: num(10), fontColor: color(C.white), horizontalAlignment: str('center') }, selector: def }]
        : [{ properties: { show: bool(false) } }],
      icon: [{ properties: { show: bool(!!icon) } },
             { properties: { shapeType: str(icon || 'blank'), placement: str('left'), lineColor: color(C.white), iconSize: num(22) }, selector: def }],
      fill: [{ properties: { show: bool(!icon) } },
             { properties: { fillColor: color('#4A4A4A'), transparency: num(0) }, selector: def },
             { properties: { fillColor: color('#5C5C5C'), transparency: num(0) }, selector: { id: 'hover' } }],
      outline: [{ properties: { show: bool(false) } }],
      shape: [{ properties: { tileShape: str('rectangleRounded'), roundEdge: int(6) } }, { properties: { tileShape: str('rectangleRounded') }, selector: def }],
    },
    visualContainerObjects: { background: [{ properties: { show: bool(false) } }], border: [{ properties: { show: bool(false) } }], visualLink: [{ properties: link }] },
    drillFilterOtherVisuals: true,
  }, [8, y, 64, 44], 10 + y);
}
navButton({ y: 16, icon: 'back', link: { show: bool(true), type: str('Back'), tooltip: str('Tilbage') } });
// Nav buttons to the other pages (max 3), bottom-up.
const otherPages = [];
const pagesJsonPath = path.join(pagesDir, 'pages.json');
const pagesJson = JSON.parse(fs.readFileSync(pagesJsonPath, 'utf8'));
for (const id of pagesJson.pageOrder.filter(p => p !== PAGE_ID)) {
  try {
    const pj = JSON.parse(fs.readFileSync(path.join(pagesDir, id, 'page.json'), 'utf8'));
    otherPages.push({ id, name: pj.displayName || id });
  } catch (_) {}
}
otherPages.slice(0, 3).forEach((p, i, arr) => {
  const short = (cfg.navLabels && cfg.navLabels[p.name]) || (p.name.length > 9 ? p.name.slice(0, 8) + '…' : p.name);
  navButton({ y: 1020 - (arr.length - i) * 56, label: short,
    link: { show: bool(true), type: str('PageNavigation'), navigationSection: str(p.id), tooltip: str(p.name) } });
});

// ---------- 2. title ----------
add({
  visualType: 'textbox',
  objects: { general: [{ properties: { paragraphs: [
    { textRuns: [{ value: cfg.title || 'Salgsoverblik', textStyle: { fontFamily: 'Segoe UI Bold', fontSize: '32px', color: C.ink } }], horizontalTextAlignment: 'left' },
    { textRuns: [{ value: cfg.subtitle || '', textStyle: { fontFamily: 'Segoe UI', fontSize: '15px', color: C.sub } }], horizontalTextAlignment: 'left' },
  ] } }] },
  visualContainerObjects: vco({ pad: 0 }),
}, [104, 52, 256, 96], 1000);

// ---------- 3. KPI tiles ----------
function card({ x, y, w, h, measure, label, valueSize = 40, labelSize = 16, valueColor = C.teal, bg = C.dark, colorMeasure = null, pad = 8 }) {
  const value = { show: bool(true), fontSize: num(valueSize), bold: bool(valueSize >= 20), horizontalAlignment: str('center'), ...WHOLE,
    fontColor: colorMeasure ? { solid: { color: { expr: measureField(colorMeasure) } } } : color(valueColor) };
  add({
    visualType: 'cardVisual',
    query: { queryState: { Data: { projections: [projM(measure)] } } },
    objects: {
      value: [{ properties: value, selector: def }],
      label: [{ properties: label
        ? { show: bool(true), text: str(label), fontSize: num(labelSize), fontColor: color(C.white), horizontalAlignment: str('center'), position: str('belowValue') }
        : { show: bool(false) }, selector: def }],
      outline: [{ properties: { show: bool(false) }, selector: def }],
      // cardVisual draws its own inner tile (white by default) over the container background
      fillCustom: [{ properties: { transparency: num(100) }, selector: def }],
      padding: [{ properties: { paddingUniform: num(8) }, selector: def }],
      // "Layout med flere kort → Baggrund": the card's own white tile; off so the dark container shows
      layout: [{ properties: { paddingUniform: num(0), backgroundShow: bool(false) }, selector: def }],
      spacing: [{ properties: { verticalSpacing: num(2) }, selector: def }],
    },
    visualContainerObjects: vco({ bg, radius: 16, pad }),
    drillFilterOtherVisuals: true,
  }, [x, y, w, h], 1100 + x + y);
}
[376, 764, 1152, 1540].forEach((x, i) => {
  const k = cfg.kpis[i];
  if (k) card({ x, y: 20, w: 364, h: 148, measure: k.measure, label: k.label });
});

// ---------- 4. trend line ----------
const t = cfg.trend;
add({
  visualType: 'lineChart',
  query: { queryState: {
    Category: { projections: [projC(t.monthColumn, 'Måned')] },
    Y: { projections: [projM(t.measure, t.label || null)] },
  } },
  objects: {
    categoryAxis: [{ properties: { show: bool(true), axisType: str('Scalar'), showAxisTitle: bool(false), gridlineShow: bool(true), gridlineStyle: str('dotted'), gridlineColor: color('#E1DFDD') } }],
    valueAxis: [{ properties: { show: bool(true), showAxisTitle: bool(true), labelDisplayUnits: str('1'), gridlineShow: bool(true), gridlineStyle: str('dotted'), gridlineColor: color('#E1DFDD') } }],
    dataPoint: [{ properties: { defaultColor: color(C.ink) } }],
    lineStyles: [{ properties: { strokeWidth: num(3), showMarker: bool(false) } }],
    legend: [{ properties: { show: bool(false) } }],
    trend: [{ properties: { show: bool(true), lineColor: color('#A19F9D'), style: str('dashed'), width: num(2), transparency: num(0), displayName: str('Trend') } }],
    forecast: [{ properties: { show: bool(true), lineColor: color(C.ink), width: num(1), bandAreaShow: bool(true), bandAreaColor: color('#C8C6C4'), bandAreaTransparency: num(50), displayName: str('Forecast') } }],
    zoom: [{ properties: { show: bool(true), showOnCategoryAxis: bool(true), showLabels: bool(false) } }],
  },
  visualContainerObjects: vco({ bg: C.white, radius: 8, borderColor: C.border, title: t.title, titleSize: 13 }),
  drillFilterOtherVisuals: true,
}, [96, 200, 952, 548], 1200);

// ---------- 5. monthly tiles ----------
[96, 422, 748].forEach((x, i) => {
  const m = cfg.monthly[i];
  if (!m) return;
  const y = 772, w = 300, h = 284;
  // show:false alone still renders axis titles ("month_start", clipped value title)
  const hidden = extra => [{ properties: { show: bool(false), showAxisTitle: bool(false), gridlineShow: bool(false), ...extra } }];
  add({
    visualType: 'areaChart',
    query: { queryState: { Category: { projections: [projC(t.monthColumn)] }, Y: { projections: [projM(m.sparkMeasure)] } } },
    objects: {
      categoryAxis: hidden({ axisType: str('Scalar') }), valueAxis: hidden(),
      legend: [{ properties: { show: bool(false) } }], labels: [{ properties: { show: bool(false) } }],
      dataPoint: [{ properties: { defaultColor: color(C.spark) } }],
      lineStyles: [{ properties: { strokeWidth: num(1), showMarker: bool(false) } }],
    },
    visualContainerObjects: vco({ bg: C.white, radius: 8, borderColor: C.border, title: m.title, titleSize: 12, pad: 6 }),
    drillFilterOtherVisuals: true,
  }, [x, y, w, h], 1300 + x);
  card({ x: x + 12, y: y + 64, w: w - 24, h: 92, measure: m.currentMeasure, label: null, bg: null, colorMeasure: m.colorMeasure, pad: 4 });
  card({ x: x + 12, y: y + 160, w: w - 24, h: 52, measure: m.labelMeasure, label: null, bg: null, valueSize: 12, valueColor: C.sub, pad: 2 });
});

// ---------- 6. bar chart ----------
const b = cfg.bar;
add({
  visualType: 'clusteredBarChart',
  query: {
    queryState: {
      Category: { projections: [projC(b.categoryColumn, b.categoryLabel || null)] },
      Y: { projections: [projM(b.measure, b.measureLabel || null)] },
    },
    sortDefinition: { sort: [{ field: measureField(b.measure), direction: 'Descending' }], isDefaultSort: true },
  },
  objects: {
    categoryAxis: [{ properties: { show: bool(true), showAxisTitle: bool(false), fontSize: num(11), labelColor: color(C.sub) } }],
    valueAxis: [{ properties: { show: bool(false), showAxisTitle: bool(false), gridlineShow: bool(false) } }],
    dataPoint: [{ properties: { defaultColor: color(C.ink) } }],
    labels: [{ properties: { show: bool(true), fontSize: num(10), color: color(C.sub), labelDisplayUnits: str('1') } }],
    legend: [{ properties: { show: bool(false) } }],
  },
  visualContainerObjects: vco({ bg: C.white, radius: 8, borderColor: C.border, title: b.title, titleSize: 13 }),
  filterConfig: { filters: [{
    name: 'f0a1b2c3d4e5f6a7b8c9d0e1',
    field: columnField(b.categoryColumn),
    type: 'Categorical',
    filter: { Version: 2, From: [{ Name: 'd', Entity: ref(b.categoryColumn).table, Type: 0 }],
      Where: [{ Condition: { Not: { Expression: { In: {
        Expressions: [{ Column: { Expression: { SourceRef: { Source: 'd' } }, Property: ref(b.categoryColumn).name } }],
        Values: [[{ Literal: { Value: 'null' } }]] } } } } }] },
    howCreated: 'User',
  }] },
  drillFilterOtherVisuals: true,
}, [1072, 200, 832, 320], 1600);

// ---------- 7. top-N table ----------
const tb = cfg.table;
const tableVisual = {
  visualType: 'tableEx',
  query: {
    queryState: { Values: { projections: [projC(tb.rowColumn, tb.title), ...tb.columns.map(c => projM(c.measure, c.label))] } },
    sortDefinition: { sort: [{ field: measureField(tb.sortMeasure), direction: 'Descending' }], isDefaultSort: true },
  },
  objects: {
    columnHeaders: [{ properties: { columnAdjustment: str('growToFit'), autoSizeColumnWidth: bool(true), bold: bool(true), fontSize: num(11), fontColor: color(C.ink), backColor: color(C.white) } }],
    values: [{ properties: { fontSize: num(11), fontColorPrimary: color(C.ink), fontColorSecondary: color(C.ink), backColorPrimary: color(C.white), backColorSecondary: color(C.white) } }],
    total: [{ properties: { totals: bool(false) } }],
  },
  visualContainerObjects: { ...vco({ bg: C.white, radius: 8, borderColor: C.border }), stylePreset: [{ properties: { name: str('None') } }] },
  drillFilterOtherVisuals: true,
};
if (tb.gradientMeasure) {
  tableVisual.objects.values.push({
    properties: { backColor: { solid: { color: { expr: { FillRule: {
      Input: measureField(tb.gradientMeasure),
      FillRule: { linearGradient2: {
        min: { color: { Literal: { Value: `'${C.gradLow}'` } } },
        max: { color: { Literal: { Value: `'${C.gradHigh}'` } } },
        nullColoringStrategy: { strategy: { Literal: { Value: "'noColor'" } } },
      } } } } } } } },
    selector: { data: [{ dataViewWildcard: { matchingOption: 1 } }], metadata: qref(tb.gradientMeasure) },
  });
}
if (tb.dataBarMeasure) {
  tableVisual.objects.columnFormatting = [{
    properties: { dataBars: { positiveColor: color(C.bar), negativeColor: color('#D64550'), axisColor: color('#999999'), reverseDirection: bool(false), hideText: bool(false) } },
    selector: { metadata: qref(tb.dataBarMeasure) },
  }];
}
if (tb.topN) {
  const row = ref(tb.rowColumn), ob = ref(tb.topN.orderByColumn);
  tableVisual.filterConfig = { filters: [{
    name: 'f1b2c3d4e5f6a7b8c9d0e1f2',
    field: columnField(tb.rowColumn),
    type: 'TopN',
    filter: {
      Version: 2,
      From: [
        { Name: 'subquery', Expression: { Subquery: { Query: {
          Version: 2,
          From: [{ Name: 'p', Entity: row.table, Type: 0 }, { Name: 'f', Entity: ob.table, Type: 0 }],
          Select: [{ Column: { Expression: { SourceRef: { Source: 'p' } }, Property: row.name }, Name: 'field' }],
          OrderBy: [{ Direction: 2, Expression: { Aggregation: { Expression: { Column: { Expression: { SourceRef: { Source: 'f' } }, Property: ob.name } }, Function: tb.topN.function } } }],
          Top: tb.topN.count || 10,
        } } }, Type: 2 },
        { Name: 'p', Entity: row.table, Type: 0 },
      ],
      Where: [{ Condition: { In: { Expressions: [{ Column: { Expression: { SourceRef: { Source: 'p' } }, Property: row.name } }], Table: { SourceRef: { Source: 'subquery' } } } } }],
    },
    howCreated: 'User',
  }] };
}
add(tableVisual, [1072, 544, 832, 340], 1700);

// ---------- 8. highlight tiles ----------
[1072, 1500].forEach((x, i) => {
  const h = cfg.highlights[i];
  if (!h) return;
  add({
    visualType: 'textbox',
    objects: { general: [{ properties: { paragraphs: [
      { textRuns: [{ value: h.header, textStyle: { fontFamily: 'Segoe UI Semibold', fontSize: '15px', color: C.ink } }], horizontalTextAlignment: 'center' },
    ] } }] },
    visualContainerObjects: vco({ pad: 0 }),
  }, [x, 904, 404, 32], 1800 + x);
  card({ x, y: 944, w: 404, h: 112, measure: h.measure, label: null, valueSize: 28 });
});

// ---------- write ----------
const pageDir = path.join(pagesDir, PAGE_ID);
fs.rmSync(pageDir, { recursive: true, force: true });
fs.mkdirSync(path.join(pageDir, 'visuals'), { recursive: true });
fs.writeFileSync(path.join(pageDir, 'page.json'), JSON.stringify({
  $schema: SCHEMA_PAGE, name: PAGE_ID, displayName: cfg.pageName || 'Dashboard', displayOption: 'FitToPage', height: 1080, width: 1920,
  objects: { background: [{ properties: { color: color(C.white), transparency: num(0) } }] },
}, null, 2));
for (const v of visuals) {
  const d = path.join(pageDir, 'visuals', v.name);
  fs.mkdirSync(d, { recursive: true });
  fs.writeFileSync(path.join(d, 'visual.json'), JSON.stringify(v, null, 2));
}
pagesJson.pageOrder = [PAGE_ID, ...pagesJson.pageOrder.filter(p => p !== PAGE_ID)];
pagesJson.activePageName = PAGE_ID;
fs.writeFileSync(pagesJsonPath, JSON.stringify(pagesJson, null, 2));
console.log(`Wrote ${visuals.length} visuals to ${pageDir}`);
