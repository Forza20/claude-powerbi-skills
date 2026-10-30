#!/usr/bin/env python3
"""
sql_lineage.py - Column lineage from SQL files (views, INSERT ... SELECT, CREATE TABLE AS).

Used by build_catalog.py --sql to fill "Opstrøms kilde": a column that Power BI reads from
gold.dim_customers.country is followed back through the SQL that loads it, e.g.
    silver.erp_loc_a101.cntry ← bronze.erp_loc_a101.cntry (afledt: case when ...)

Supported (regex based, no full SQL parser):
    CREATE [OR REPLACE] [MATERIALIZED] VIEW t [(cols)] AS SELECT ...
    CREATE TABLE t AS SELECT ...
    INSERT INTO t [(cols)] SELECT ...      (also inside procedure/function bodies; without a column
                                            list the select items map by position to t's CREATE TABLE)
    FROM/JOIN with aliases, subqueries in FROM (incl. SELECT *), CTE-free selects.
Files are read in name order; a later definition of the same target wins (migrations).

Usage (debug):  python3 sql_lineage.py <sql-dir-or-file> [table.column ...]
"""

import re
import sys
from pathlib import Path

KEYWORDS = {
    'select', 'distinct', 'on', 'from', 'where', 'group', 'by', 'having', 'order', 'limit',
    'offset', 'union', 'all', 'except', 'intersect', 'case', 'when', 'then', 'else', 'end',
    'and', 'or', 'not', 'null', 'is', 'in', 'like', 'ilike', 'between', 'as', 'over',
    'partition', 'desc', 'asc', 'nulls', 'first', 'last', 'interval', 'true', 'false', 'cast',
    'date', 'time', 'timestamp', 'timestamptz', 'text', 'integer', 'int', 'bigint', 'smallint',
    'numeric', 'decimal', 'varchar', 'char', 'boolean', 'bool', 'real', 'double', 'precision',
    'float', 'money', 'uuid', 'json', 'jsonb', 'rows', 'range', 'preceding', 'following',
    'current', 'row', 'unbounded', 'filter', 'within', 'exists', 'any', 'some', 'join', 'left',
    'right', 'full', 'inner', 'outer', 'cross', 'using', 'lateral', 'with', 'epoch', 'year',
    'month', 'day', 'hour', 'minute', 'second', 'now', 'current_date', 'current_timestamp',
    'for', 'to', 'similar', 'escape', 'collate', 'leading', 'trailing', 'both', 'placing', 'at', 'zone',
    'top', 'percent', 'ties', 'only', 'varying', 'character', 'nvarchar', 'datetime', 'datetime2', 'bit',
}
CLAUSE_WORDS = ['from', 'where', 'group by', 'having', 'order by', 'limit', 'offset',
                'union', 'except', 'intersect', 'window', 'fetch']
IDENT = r'(?:"[^"]+"|\[[^\]]+\]|`[^`]+`|[A-Za-z_][\w$]*)'
QNAME = rf'{IDENT}(?:\s*\.\s*{IDENT}){{0,2}}'


def norm(name):
    """'"Gold"."Dim_Customers"' / [gold].[x] -> 'gold.dim_customers'."""
    parts = re.findall(IDENT, name or '')
    return '.'.join(p.strip('"[]`').lower() for p in parts)


def strip_comments(sql):
    out, i, n = [], 0, len(sql)
    while i < n:
        ch = sql[i]
        if ch == "'":
            j = i + 1
            while j < n:
                if sql[j] == "'":
                    if j + 1 < n and sql[j + 1] == "'":
                        j += 2
                        continue
                    break
                j += 1
            out.append(sql[i:j + 1])
            i = j + 1
        elif sql.startswith('--', i):
            while i < n and sql[i] != '\n':
                i += 1
        elif sql.startswith('/*', i):
            end = sql.find('*/', i + 2)
            i = n if end < 0 else end + 2
        else:
            out.append(ch)
            i += 1
    return ''.join(out)


def _scan(s, cb):
    """Call cb(i, depth) for every char outside strings/quoted identifiers; stop when cb is truthy."""
    depth, i, n = 0, 0, len(s)
    while i < n:
        ch = s[i]
        if ch in "'\"":
            j = i + 1
            while j < n and s[j] != ch:
                j += 1
            i = j + 1
            continue
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        if cb(i, depth):
            return i
        i += 1
    return -1


def split_top(s, sep=','):
    parts, last = [], [0]

    def cb(i, d):
        if d == 0 and s[i] == sep:
            parts.append(s[last[0]:i])
            last[0] = i + 1
        return False
    _scan(s, cb)
    parts.append(s[last[0]:])
    return [p.strip() for p in parts if p.strip()]


def find_top_words(s, words):
    """Positions of top-level keywords (multi-word allowed) -> [(pos, word)]."""
    hits = []
    low = s.lower()

    def cb(i, d):
        if d == 0 and (i == 0 or not (low[i - 1].isalnum() or low[i - 1] in '_.$')):
            for w in words:
                if low.startswith(w.split()[0], i):
                    m = re.match(r'\s+'.join(map(re.escape, w.split())) + r'\b', low[i:])
                    if m:
                        hits.append((i, w, m.end()))
                        break
        return False
    _scan(s, cb)
    return hits


def statement_end(s, start):
    end = [len(s)]

    def cb(i, d):
        if d <= 0 and s[i] == ';' and i >= start:
            end[0] = i
            return True
        return d < 0
    _scan(s[start:], lambda i, d: cb(i + start, d))
    return end[0]


def short(text, n=90):
    t = re.sub(r'\s+', ' ', str(text or '')).strip()
    return t if len(t) <= n else t[:n - 1] + '…'


# ---------------------------------------------------------------------------
# SELECT parsing
# ---------------------------------------------------------------------------

def parse_select(sql):
    """'select ... from ...' -> {'items': [...], 'sources': {alias: src}, 'where': str}"""
    s = sql.strip()
    m = re.match(r'^\(?\s*select\b', s, re.I)
    if not m:
        return None
    if s.startswith('('):
        s = s[1:s.rfind(')')] if ')' in s else s[1:]
    body = re.sub(r'^\s*select\s+', '', s, flags=re.I)
    body = re.sub(r'^distinct\s+on\s*\([^)]*\)\s*', '', body, flags=re.I)
    body = re.sub(r'^(distinct|all)\s+', '', body, flags=re.I)
    clauses = find_top_words(body, CLAUSE_WORDS)
    from_pos = next((p for p in clauses if p[1] == 'from'), None)
    select_list = body[:from_pos[0]] if from_pos else body
    rest = body[from_pos[0] + from_pos[2]:] if from_pos else ''
    rest_clauses = [c for c in find_top_words(rest, CLAUSE_WORDS) if c[1] != 'from']
    from_clause = rest[:rest_clauses[0][0]] if rest_clauses else rest
    where = ''
    wc = next((c for c in rest_clauses if c[1] == 'where'), None)
    if wc:
        nxt = [c for c in rest_clauses if c[0] > wc[0]]
        where = rest[wc[0] + wc[2]:nxt[0][0] if nxt else len(rest)].strip()
    sources = parse_from(from_clause)
    items = [parse_item(it) for it in split_top(select_list)]
    return {'items': items, 'sources': sources, 'where': where}


def parse_from(fc):
    sources = {}
    parts = re.split(r'\b(?:natural\s+)?(?:(?:left|right|full)\s+(?:outer\s+)?|inner\s+|cross\s+)?join\b',
                     fc, flags=re.I)
    items = []
    for p in parts:
        items.extend(split_top(p))
    for it in items:
        on = find_top_words(it, ['on', 'using'])
        if on:
            it = it[:on[0][0]]
        it = re.sub(r'^\s*lateral\s+', '', it.strip(), flags=re.I)
        if it.startswith('('):
            depth, j = 0, 0
            for j, ch in enumerate(it):
                depth += ch == '('
                depth -= ch == ')'
                if depth == 0:
                    break
            sub, alias = it[1:j], it[j + 1:].strip()
            alias = re.sub(r'^as\s+', '', alias, flags=re.I).split('(')[0].strip()
            parsed = parse_select(sub)
            if parsed:
                sources[norm(alias) or f'_sub{len(sources)}'] = {'kind': 'sub', 'select': parsed}
            continue
        m = re.match(rf'^({QNAME})(?:\s+(?:as\s+)?({IDENT}))?\s*$', it.strip(), re.I)
        if m:
            table = norm(m.group(1))
            alias = norm(m.group(2)) if m.group(2) and m.group(2).lower() not in KEYWORDS else table.split('.')[-1]
            sources[alias] = {'kind': 'table', 'name': table}
            sources.setdefault(table, {'kind': 'table', 'name': table})
    return sources


def parse_item(item):
    it = item.strip()
    if re.fullmatch(rf'(?:{IDENT}\s*\.\s*)?\*', it):
        q = it.rsplit('.', 1)[0] if '.' in it else ''
        return {'star': True, 'qualifier': norm(q)}
    as_hits = find_top_words(it, ['as'])
    if as_hits:
        pos, _, ln = as_hits[-1]
        alias = it[pos + ln:].strip()
        if re.fullmatch(IDENT, alias):
            return {'name': norm(alias), 'expr': it[:pos].strip()}
    m = re.fullmatch(rf'(?:({IDENT})\s*\.\s*)?({IDENT})', it)
    if m:
        return {'name': norm(m.group(2)), 'expr': it}
    m = re.fullmatch(rf'(.+?[\w)\'"])\s+({IDENT})', it, re.S)
    if m and m.group(2).lower() not in KEYWORDS:
        return {'name': norm(m.group(2)), 'expr': m.group(1).strip()}
    return {'name': '', 'expr': it}


def expr_refs(expr):
    """Column references in an expression -> [(qualifier or '', column)]."""
    s = re.sub(r"'(?:[^']|'')*'", "''", expr)
    s = re.sub(r'::\s*\w+(\s*\([^)]*\))?', ' ', s)                     # ::type casts
    s = re.sub(r'\binterval\s+\'\'', ' ', s, flags=re.I)
    refs = []
    for m in re.finditer(rf'({IDENT})\s*\.\s*({IDENT})(?!\s*[\.(])', s):
        refs.append((norm(m.group(1)), norm(m.group(2))))
    s2 = re.sub(rf'{IDENT}\s*\.\s*{IDENT}', ' ', s)
    for m in re.finditer(r'(?<![\w.$])([A-Za-z_][\w$]*|"[^"]+")(?![\w$.])(?!\s*\()', s2):
        w = m.group(1)
        if w.lower() in KEYWORDS or w.lower().startswith('pg_'):
            continue
        refs.append(('', norm(w)))
    seen, out = set(), []
    for r in refs:
        if r not in seen:
            seen.add(r)
            out.append(r)
    return out


def is_direct(expr):
    return bool(re.fullmatch(rf'\s*(?:{IDENT}\s*\.\s*)?{IDENT}\s*', expr or ''))


# ---------------------------------------------------------------------------
# Resolving a select into target-column mappings
# ---------------------------------------------------------------------------

def _resolve(select, qual, col, depth=0):
    """(qualifier, column) inside a select -> [(table, column)] in real tables."""
    if depth > 8:
        return []
    srcs = select['sources']
    real = {a: s for a, s in srcs.items() if a != s.get('name')} or srcs
    if qual:
        cands = [srcs[qual]] if qual in srcs else []
        if not cands:
            full = [s for s in srcs.values() if s.get('name', '').endswith('.' + qual) or s.get('name') == qual]
            cands = full[:1]
    else:
        uniq = {id(s): s for s in real.values()}
        cands = list(uniq.values()) if len(uniq) == 1 else []
    out = []
    for s in cands:
        if s['kind'] == 'table':
            out.append((s['name'], col))
        else:
            sub = s['select']
            item = next((i for i in sub['items'] if not i.get('star') and i['name'] == col), None)
            if item:
                for q, c in expr_refs(item['expr']):
                    out += _resolve(sub, q, c, depth + 1)
            elif any(i.get('star') for i in sub['items']):
                out += _resolve(sub, '', col, depth + 1)
    return out


def select_mappings(select, target_cols=None):
    """Mappings for each output column of a select: {col: {'refs', 'expr', 'direct'}}."""
    out, pos = {}, 0
    for item in select['items']:
        if item.get('star'):
            continue  # SELECT * into a target: passthrough handled by name below
        name = target_cols[pos] if target_cols and pos < len(target_cols) else item['name']
        pos += 1
        if not name:
            continue
        refs = []
        for q, c in expr_refs(item['expr']):
            refs += _resolve(select, q, c)
        out[name] = {'refs': list(dict.fromkeys(refs)), 'expr': item['expr'],
                     'direct': is_direct(item['expr'])}
    return out


CONSTRAINT_WORDS = {'constraint', 'primary', 'foreign', 'unique', 'check', 'exclude', 'like'}


def create_table_columns(sql):
    """CREATE TABLE t (col type, ...) -> {table: [col, ...]} in declaration order."""
    out = {}
    pat = re.compile(rf'\bcreate\s+(?:(?:temp|temporary|unlogged)\s+)?table\s+(?:if\s+not\s+exists\s+)?'
                     rf'({QNAME})\s*\(', re.I)
    for m in pat.finditer(sql):
        start = m.end()
        close = _scan(sql[start:], lambda i, d: d < 0)
        if close < 0:
            continue
        cols = []
        for part in split_top(sql[start:start + close]):
            first = re.match(IDENT, part.strip())
            if first and first.group(0).lower() not in CONSTRAINT_WORDS:
                cols.append(norm(first.group(0)))
        if cols:
            out[norm(m.group(1))] = cols
    return out


class SqlLineage:
    def __init__(self):
        self.columns = {}     # (table, col) -> mapping
        self.tables = {}      # table -> {'sources': set(), 'where': str, 'file': str}
        self.table_cols = {}  # table -> declared columns (for INSERT INTO t SELECT without a column list)

    def load(self, paths):
        files = []
        for p in paths:
            p = Path(p)
            files += sorted(p.rglob('*.sql')) if p.is_dir() else [p]
        texts = []
        for f in sorted(files, key=lambda x: x.name):
            try:
                texts.append((f.name, f.read_text(encoding='utf-8', errors='replace')))
            except Exception as e:
                print(f'sql_lineage: sprang {f.name} over ({e})', file=sys.stderr)
        # pass 1: declared columns of every table, so an INSERT can map its select by position
        for _, t in texts:
            try:
                self.table_cols.update(create_table_columns(strip_comments(t)))
            except Exception:
                pass
        for name, t in texts:
            try:
                self.add_sql(t, name)
            except Exception as e:  # never stop the catalog because of one file
                print(f'sql_lineage: sprang {name} over ({e})', file=sys.stderr)
        return self

    def add_sql(self, sql, fname=''):
        s = strip_comments(sql)
        for t, c in create_table_columns(s).items():
            self.table_cols.setdefault(t, c)
        pat = re.compile(
            rf'\b(?:create\s+(?:or\s+replace\s+)?(?:materialized\s+)?view\s+(?:if\s+not\s+exists\s+)?(?P<view>{QNAME})'
            rf'\s*(?:\((?P<vcols>[^)]*)\))?\s+as\s+'
            rf'|create\s+(?:temp(?:orary)?\s+)?table\s+(?:if\s+not\s+exists\s+)?(?P<ctas>{QNAME})\s+as\s+'
            rf'|insert\s+into\s+(?P<ins>{QNAME})\s*(?:\((?P<icols>[^)]*)\))?\s*)'
            r'(?=\(?\s*select\b)', re.I)
        for m in pat.finditer(s):
            target = norm(m.group('view') or m.group('ctas') or m.group('ins'))
            cols = m.group('vcols') or m.group('icols')
            cols = [norm(c) for c in cols.split(',')] if cols else None
            end = statement_end(s, m.end())
            select = parse_select(s[m.end():end])
            if not select:
                continue
            if cols is None and m.group('ins') and not any(i.get('star') for i in select['items']):
                # INSERT INTO t SELECT ... without a column list: map by position to t's CREATE TABLE
                declared = self.table_cols.get(target)
                if declared and len(declared) == len(select['items']):
                    cols = declared
            # later definition replaces earlier ones
            for k in [k for k in self.columns if k[0] == target]:
                del self.columns[k]
            for col, mp in select_mappings(select, cols).items():
                self.columns[(target, col)] = mp
            self.tables[target] = {
                'sources': {s['name'] for s in select['sources'].values() if s['kind'] == 'table'}
                | {n for sub in select['sources'].values() if sub['kind'] == 'sub'
                   for n in _sub_tables(sub['select'])},
                'where': select['where'], 'file': fname,
                # raw-lines staging (… from raw_lines where file_name = 'fact_orders'): remember the CSV
                'csv_file': (lambda h: h.group(1) if h else None)(
                    re.search(r"\bfile_name\s*=\s*'([^']+)'", s[m.end():end], re.I)),
            }

    def find_table(self, name):
        """Match a Power Query object ('gold.dim_customers' or 'dim_customers')."""
        n = norm(name)
        if n in self.tables:
            return n
        # name-only fallback; when a schema is given it must match (as a suffix: 'gold' ~ 'mp_x_gold'),
        # otherwise gold.dim_customers could be answered with bronze.dim_customers
        schema = n.rsplit('.', 1)[0] if '.' in n else ''
        hits = [t for t in self.tables if t.split('.')[-1] == n.split('.')[-1]
                and (not schema or ('.' in t and t.rsplit('.', 1)[0].endswith(schema.split('.')[-1])))]
        return hits[0] if len(hits) == 1 else None

    def column_chain(self, table, col):
        t = self.find_table(table)
        if not t or (t, norm(col)) not in self.columns:
            return ''
        levels, frontier, seen = [], [(t, norm(col))], {(t, norm(col))}
        csv_cols = []   # 'fact_orders.csv › amount' for bronze columns split out of a raw_lines table
        for _ in range(8):
            nxt, notes = [], []
            for tc in frontier:
                mp = self.columns.get(tc)
                if not mp:
                    continue
                if not mp['direct']:
                    notes.append(short(mp['expr'], 80))
                for r in mp['refs']:
                    if r[0].split('.')[-1] == 'raw_lines' and r[1] == 'line':
                        # bronze columns follow the CSV header order (medallion rule), so the bronze
                        # column name is the CSV column; the file comes from the file_name filter
                        csv = self.tables.get(tc[0], {}).get('csv_file') or tc[0].split('.')[-1]
                        name = f'{csv}.csv › {tc[1]}'
                        if name not in csv_cols:
                            csv_cols.append(name)
                    if r not in seen:
                        seen.add(r)
                        nxt.append(r)
            if not nxt:
                if notes and levels:
                    levels[-1] += f" (afledt: {'; '.join(notes)})"
                elif notes:
                    levels.append(f"Beregnet i SQL: {'; '.join(notes)}")
                break
            txt = ' + '.join(f'{a}.{b}' for a, b in nxt)
            if notes:
                txt += f" (afledt: {'; '.join(notes)})"
            levels.append(txt)
            frontier = nxt
        if csv_cols:
            levels.append(' + '.join(csv_cols))
        return ' ← '.join(levels)

    def table_chain(self, table):
        t = self.find_table(table)
        if not t:
            return ''
        levels, frontier, seen = [], [t], {t}
        where = self.tables[t].get('where')
        schema = t.rsplit('.', 1)[0] if '.' in t else ''
        for _ in range(8):
            nxt = sorted({s for f in frontier for s in self.tables.get(f, {}).get('sources', set())} - seen)
            if not nxt:
                break
            seen |= set(nxt)
            levels.append(', '.join(nxt))
            # lookups in sibling tables (gold.dim_* from gold.fact_*) have their own chain
            frontier = [n for n in nxt if not (schema and n.startswith(schema + '.'))]
        txt = ' ← '.join(levels)
        if where and txt:
            txt += f' (filter: {short(where, 70)})'
        return txt


def _sub_tables(select):
    out = set()
    for s in select['sources'].values():
        if s['kind'] == 'table':
            out.add(s['name'])
        else:
            out |= _sub_tables(s['select'])
    return out


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)
    sl = SqlLineage().load([sys.argv[1]])
    targets = sys.argv[2:] or sorted({f'{t}.{c}' for t, c in sl.columns})
    for tc in targets:
        t, c = tc.rsplit('.', 1)
        print(f'{tc:45} ← {sl.column_chain(t, c)}')
    for t in sorted(sl.tables):
        print(f'TABLE {t:39} ← {sl.table_chain(t)}')
