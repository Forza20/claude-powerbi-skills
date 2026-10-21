#!/usr/bin/env python3
"""
parse_pbip.py — Parse a Power BI Project (PBIP) folder into structured JSON.

Usage:
    python3 parse_pbip.py <pbip_folder_path> [--output /path/to/output.json]

Outputs JSON to stdout (or to --output file) with keys:
    - model: {name, tables, relationships, roles, dataSources}
    - report: {pages}
"""

import json
import os
import re
import sys
from pathlib import Path


PII_PATTERNS = [
    'email', 'e-mail', 'mail', 'phone', 'telefon', 'mobil', 'tlf',
    'cpr', 'ssn', 'passport', 'pas', 'cvr', 'vat',
    'name', 'navn', 'fornavn', 'efternavn', 'firstname', 'lastname', 'fullname',
    'address', 'adresse', 'postnr', 'zip', 'postal', 'city', 'by',
    'dob', 'birth', 'fødsel', 'fodsel', 'birthday',
    'ip', 'ipaddress', 'deviceid', 'userid',
    'iban', 'account', 'kontonummer', 'kortnummer', 'cardnumber',
    'salary', 'løn', 'lon', 'income', 'indkomst',
    'gender', 'køn', 'kon', 'ethnic', 'religion', 'nationality', 'nationalitet',
]


def unquote_tmdl(s):
    s = s.strip()
    if len(s) >= 2 and s[0] == s[-1] and s[0] in ("'", '"'):
        return s[1:-1]
    return s


def split_table_column(s):
    """Parse 'Table.Column' or 'Table'.'Column' (with optional quoting)."""
    s = s.strip()
    m = re.match(r"^'?([^'.]+)'?\.'?([^']+)'?$", s)
    if m:
        return m.group(1), m.group(2)
    parts = s.split('.', 1)
    if len(parts) == 2:
        return parts[0], parts[1]
    return s, ''


def is_pii(col_name):
    lower = col_name.lower()
    return any(p in lower for p in PII_PATTERNS)


def identify_m_source(m_expr):
    """Extract source kind and details from Power Query M expression."""
    if not m_expr:
        return {'kind': 'Unknown', 'details': '(no expression)'}

    patterns = [
        (r'Sql\.Databases?\(\s*"([^"]+)"(?:\s*,\s*"([^"]+)")?',
         'SQL Server', lambda r: f'{r[0]} / {r[1]}' if r[1] else r[0]),
        (r'Snowflake\.Databases\(\s*"([^"]+)"\s*,\s*"([^"]+)"',
         'Snowflake', lambda r: f'{r[0]} / {r[1]}'),
        (r'AzureStorage\.DataLake\(\s*"([^"]+)"', 'Azure Data Lake', lambda r: r[0]),
        (r'AzureStorage\.Blobs\(\s*"([^"]+)"', 'Azure Blob', lambda r: r[0]),
        (r'Databricks\.Catalogs\(\s*"([^"]+)"', 'Databricks', lambda r: r[0]),
        (r'PostgreSQL\.Database\(\s*"([^"]+)"\s*,\s*"([^"]+)"',
         'PostgreSQL', lambda r: f'{r[0]} / {r[1]}'),
        (r'MySQL\.Database\(\s*"([^"]+)"\s*,\s*"([^"]+)"',
         'MySQL', lambda r: f'{r[0]} / {r[1]}'),
        (r'Oracle\.Database\(\s*"([^"]+)"', 'Oracle', lambda r: r[0]),
        (r'Web\.Contents\(\s*"([^"]+)"', 'Web / REST', lambda r: r[0]),
        (r'SharePoint\.(Files|Contents)\(\s*"([^"]+)"',
         'SharePoint', lambda r: r[1]),
        (r'OData\.Feed\(\s*"([^"]+)"', 'OData', lambda r: r[0]),
        (r'Excel\.Workbook\(File\.Contents\(\s*"([^"]+)"',
         'Excel File', lambda r: r[0]),
        (r'Csv\.Document\(File\.Contents\(\s*"([^"]+)"',
         'CSV File', lambda r: r[0]),
        (r'Folder\.Files\(\s*"([^"]+)"', 'Folder', lambda r: r[0]),
        (r'Pbi\.Dataflows?\(', 'Dataflow', lambda r: '(Power BI Dataflow)'),
        (r'#shared\s*\[', 'Shared / Dataflow', lambda r: '(Dataflow or shared)'),
    ]

    for pat, kind, fmt in patterns:
        match = re.search(pat, m_expr, re.IGNORECASE)
        if match:
            groups = match.groups()
            return {'kind': kind, 'details': fmt(groups)}

    return {'kind': 'Other', 'details': '(unrecognized)'}


def parse_table_tmdl(text):
    """Parse a single table .tmdl file into a table dict."""
    lines = text.split('\n')
    header_match = re.search(r'^\s*table\s+(.+?)\s*$', text, re.MULTILINE)
    if not header_match:
        return None

    table = {
        'name': unquote_tmdl(header_match.group(1)),
        'isHidden': False,
        'dataCategory': '',
        'description': '',
        'columns': [],
        'measures': [],
        'partitions': [],
    }

    i = 0
    n = len(lines)
    while i < n:
        line = lines[i]
        trimmed = line.strip()
        indent = len(line) - len(line.lstrip())

        # Top-level table block — capture table-level props
        if indent == 0 and re.match(r'^table\s', trimmed):
            i += 1
            while i < n:
                l = lines[i]
                ind = len(l) - len(l.lstrip())
                t = l.strip()
                if ind == 0 and t:
                    break
                if re.match(r'^isHidden\s*:?\s*true', t, re.IGNORECASE):
                    table['isHidden'] = True
                dc = re.match(r'^dataCategory\s*:?\s*(.+)$', t, re.IGNORECASE)
                if dc:
                    table['dataCategory'] = dc.group(1).strip()
                if t.startswith('///'):
                    table['description'] += re.sub(r'^///\s?', '', t) + ' '
                # Break on child block start
                if ind > 0 and re.match(r'^(column|measure|partition|hierarchy|calculationGroup)\s+', t):
                    break
                i += 1
            continue

        # Column block
        if re.match(r'^column\s+', trimmed):
            name_match = re.match(r'^column\s+(.+?)\s*(=.*)?$', trimmed)
            col = {
                'name': unquote_tmdl(name_match.group(1)) if name_match else '',
                'dataType': '',
                'isHidden': False,
                'isKey': False,
                'isCalculated': '=' in trimmed,
            }
            base = indent
            i += 1
            while i < n:
                l = lines[i]
                ind = len(l) - len(l.lstrip())
                t = l.strip()
                if ind <= base and t:
                    break
                dt = re.match(r'^dataType\s*:?\s*(\w+)', t, re.IGNORECASE)
                if dt:
                    col['dataType'] = dt.group(1)
                if re.match(r'^isHidden\s*:?\s*true', t, re.IGNORECASE):
                    col['isHidden'] = True
                if re.match(r'^isKey\s*:?\s*true', t, re.IGNORECASE):
                    col['isKey'] = True
                i += 1
            table['columns'].append(col)
            continue

        # Measure block
        if re.match(r'^measure\s+', trimmed):
            m = {
                'name': '',
                'expression': '',
                'displayFolder': '',
                'description': '',
                'formatString': '',
                'isHidden': False,
            }
            inline = re.match(r'^measure\s+(.+?)\s*=\s*(.*)$', trimmed)
            if inline:
                m['name'] = unquote_tmdl(inline.group(1))
                m['expression'] = inline.group(2).strip()
            else:
                just = re.match(r'^measure\s+(.+?)\s*$', trimmed)
                if just:
                    m['name'] = unquote_tmdl(just.group(1))
            base = indent
            i += 1
            expr_lines = [m['expression']] if m['expression'] else []
            while i < n:
                l = lines[i]
                ind = len(l) - len(l.lstrip())
                t = l.strip()
                if ind <= base and t:
                    break
                df = re.match(r'^displayFolder\s*:?\s*(.+)$', t, re.IGNORECASE)
                fs = re.match(r'^formatString\s*:?\s*(.+)$', t, re.IGNORECASE)
                hid = re.match(r'^isHidden\s*:?\s*true', t, re.IGNORECASE)
                if df:
                    m['displayFolder'] = df.group(1).strip()
                    i += 1
                    continue
                if t.startswith('///'):
                    m['description'] += re.sub(r'^///\s?', '', t) + ' '
                    i += 1
                    continue
                if fs:
                    m['formatString'] = fs.group(1).strip()
                    i += 1
                    continue
                if hid:
                    m['isHidden'] = True
                    i += 1
                    continue
                # Otherwise treat as DAX expression line
                if ind > base:
                    expr_lines.append(l[base + 1:] if len(l) > base + 1 else l.strip())
                i += 1
            m['expression'] = '\n'.join(expr_lines).strip()
            m['expression'] = re.sub(r'^```[\w-]*\n?', '', m['expression'])
            m['expression'] = re.sub(r'\n?```\s*$', '', m['expression'])
            table['measures'].append(m)
            continue

        # Partition block
        if re.match(r'^partition\s+', trimmed):
            p = {'name': '', 'mode': 'import', 'mExpression': '', 'sourceType': ''}
            name_match = re.match(r'^partition\s+(.+?)\s*=\s*(\w+)?', trimmed)
            if name_match:
                p['name'] = unquote_tmdl(name_match.group(1))
                if name_match.group(2):
                    p['sourceType'] = name_match.group(2)
            base = indent
            i += 1
            m_lines = []
            in_source = False
            source_indent = -1
            while i < n:
                l = lines[i]
                ind = len(l) - len(l.lstrip())
                t = l.strip()
                if ind <= base and t:
                    break
                md = re.match(r'^mode\s*:?\s*(\w+)', t, re.IGNORECASE)
                if md:
                    p['mode'] = md.group(1).lower()
                if re.match(r'^source\s*=', t) or re.match(r'^source\s*$', t):
                    in_source = True
                    source_indent = ind
                    inline_m = re.match(r'^source\s*=\s*(.+)$', t)
                    if inline_m:
                        m_lines.append(inline_m.group(1))
                    i += 1
                    continue
                if in_source:
                    if ind > source_indent:
                        m_lines.append(l[source_indent + 1:] if len(l) > source_indent + 1 else l.strip())
                    elif t:
                        in_source = False
                i += 1
            expr = '\n'.join(m_lines).strip()
            expr = re.sub(r'^```m?\n?', '', expr)
            expr = re.sub(r'\n?```\s*$', '', expr)
            p['mExpression'] = expr
            table['partitions'].append(p)
            continue

        i += 1

    table['description'] = table['description'].strip()
    return table


def parse_relationships_tmdl(text):
    rels = []
    regex = re.compile(
        r'relationship\s+[\w-]+\s*\n((?:[ \t]+.*\n?)+)',
        re.MULTILINE
    )
    for match in regex.finditer(text):
        body = match.group(1)
        rel = {
            'from': {},
            'to': {},
            'crossFilter': 'singleDirection',
            'active': True,
        }
        fc = re.search(r'fromColumn\s*:?\s*(.+)', body)
        tc = re.search(r'toColumn\s*:?\s*(.+)', body)
        cf = re.search(r'crossFilteringBehavior\s*:?\s*(\w+)', body)
        ac = re.search(r'isActive\s*:?\s*(false|true)', body, re.IGNORECASE)
        if fc:
            t, c = split_table_column(fc.group(1).strip())
            rel['from'] = {'table': t, 'column': c}
        if tc:
            t, c = split_table_column(tc.group(1).strip())
            rel['to'] = {'table': t, 'column': c}
        if cf:
            rel['crossFilter'] = cf.group(1)
        if ac:
            rel['active'] = ac.group(1).lower() == 'true'
        if rel['from'].get('table') and rel['to'].get('table'):
            rels.append(rel)
    return rels


def parse_roles_tmdl(text):
    roles = []
    lines = text.split('\n')
    current = None
    i = 0
    while i < len(lines):
        l = lines[i]
        trimmed = l.strip()
        indent = len(l) - len(l.lstrip())

        if indent == 0 and re.match(r'^role\s+', trimmed):
            if current:
                roles.append(current)
            name = unquote_tmdl(re.sub(r'^role\s+', '', trimmed).strip())
            current = {'name': name, 'modelPermission': 'read', 'tablePermissions': []}
        elif current and re.match(r'^tablePermission\s+', trimmed):
            tp_match = re.match(r'^tablePermission\s+(.+?)\s*=\s*(.*)$', trimmed)
            if tp_match:
                tp = {
                    'table': unquote_tmdl(tp_match.group(1)),
                    'filter': tp_match.group(2).strip(),
                }
                if not tp['filter']:
                    base = indent
                    expr_lines = []
                    j = i + 1
                    while j < len(lines):
                        ll = lines[j]
                        ind = len(ll) - len(ll.lstrip())
                        if ind <= base and ll.strip():
                            break
                        expr_lines.append(ll.strip())
                        j += 1
                    tp['filter'] = '\n'.join(expr_lines)
                    i = j - 1
                current['tablePermissions'].append(tp)
        elif current:
            mp = re.match(r'^modelPermission\s*:?\s*(\w+)', trimmed)
            if mp:
                current['modelPermission'] = mp.group(1)
        i += 1
    if current:
        roles.append(current)
    return roles


def parse_tmsl(obj, model):
    """Fallback parser for legacy model.bim TMSL JSON."""
    m = obj.get('model', obj)
    for t in m.get('tables', []):
        table = {
            'name': t['name'],
            'isHidden': bool(t.get('isHidden')),
            'dataCategory': t.get('dataCategory', ''),
            'description': t.get('description', ''),
            'columns': [],
            'measures': [],
            'partitions': [],
        }
        for c in t.get('columns', []):
            table['columns'].append({
                'name': c['name'],
                'dataType': c.get('dataType', ''),
                'isHidden': bool(c.get('isHidden')),
                'isKey': bool(c.get('isKey')),
                'isCalculated': c.get('type') == 'calculated',
            })
        for me in t.get('measures', []):
            expr = me.get('expression', '')
            if isinstance(expr, list):
                expr = '\n'.join(expr)
            table['measures'].append({
                'name': me['name'],
                'expression': expr,
                'displayFolder': me.get('displayFolder', ''),
                'description': me.get('description', ''),
                'formatString': me.get('formatString', ''),
                'isHidden': bool(me.get('isHidden')),
            })
        for p in t.get('partitions', []):
            src = p.get('source', {})
            expr = src.get('expression', '')
            if isinstance(expr, list):
                expr = '\n'.join(expr)
            table['partitions'].append({
                'name': p['name'],
                'mode': p.get('mode', 'import'),
                'mExpression': expr,
                'sourceType': src.get('type', ''),
            })
        model['tables'].append(table)

    for r in m.get('relationships', []):
        model['relationships'].append({
            'from': {'table': r['fromTable'], 'column': r['fromColumn']},
            'to': {'table': r['toTable'], 'column': r['toColumn']},
            'crossFilter': r.get('crossFilteringBehavior', 'singleDirection'),
            'active': r.get('isActive', True),
        })

    for r in m.get('roles', []):
        role = {
            'name': r['name'],
            'modelPermission': r.get('modelPermission', 'read'),
            'tablePermissions': [],
        }
        for tp in r.get('tablePermissions', []):
            role['tablePermissions'].append({
                'table': tp.get('name', tp.get('table', '')),
                'filter': tp.get('filterExpression', tp.get('filter', '')),
            })
        model['roles'].append(role)


def parse_model(pbip_root):
    """Find and parse SemanticModel. Returns model dict."""
    pbip_root = Path(pbip_root)
    model = {
        'name': '',
        'tables': [],
        'relationships': [],
        'roles': [],
        'dataSources': [],
    }

    # Project name from .pbip file
    for f in pbip_root.iterdir():
        if f.suffix == '.pbip':
            model['name'] = f.stem
            break

    # Find SemanticModel folder
    sm_dirs = list(pbip_root.glob('*.SemanticModel'))
    if not sm_dirs:
        raise RuntimeError(f'No *.SemanticModel folder found in {pbip_root}')
    sm_dir = sm_dirs[0]

    definition_dir = sm_dir / 'definition'
    bim_file = sm_dir / 'model.bim'

    if definition_dir.is_dir():
        # TMDL format
        tables_dir = definition_dir / 'tables'
        if tables_dir.is_dir():
            for tmdl_file in sorted(tables_dir.glob('*.tmdl')):
                text = tmdl_file.read_text(encoding='utf-8')
                t = parse_table_tmdl(text)
                if t:
                    model['tables'].append(t)

        # Relationships
        rel_file = definition_dir / 'relationships.tmdl'
        if rel_file.is_file():
            model['relationships'] = parse_relationships_tmdl(
                rel_file.read_text(encoding='utf-8')
            )
        # Sometimes in model.tmdl
        model_file = definition_dir / 'model.tmdl'
        if model_file.is_file():
            extra = parse_relationships_tmdl(model_file.read_text(encoding='utf-8'))
            model['relationships'].extend(extra)

        # Roles
        roles_dir = definition_dir / 'roles'
        if roles_dir.is_dir():
            for role_file in sorted(roles_dir.glob('*.tmdl')):
                model['roles'].extend(parse_roles_tmdl(
                    role_file.read_text(encoding='utf-8')
                ))
        roles_file = definition_dir / 'roles.tmdl'
        if roles_file.is_file():
            model['roles'].extend(parse_roles_tmdl(
                roles_file.read_text(encoding='utf-8')
            ))

    elif bim_file.is_file():
        # Legacy TMSL
        obj = json.loads(bim_file.read_text(encoding='utf-8'))
        parse_tmsl(obj, model)
    else:
        raise RuntimeError(f'Neither definition/ nor model.bim found in {sm_dir}')

    # Data source inventory
    sources = {}
    for t in model['tables']:
        for p in t['partitions']:
            src = identify_m_source(p['mExpression'])
            key = f"{src['kind']}::{src['details']}"
            if key not in sources:
                sources[key] = {**src, 'tables': []}
            if t['name'] not in sources[key]['tables']:
                sources[key]['tables'].append(t['name'])
    model['dataSources'] = list(sources.values())

    return model


def extract_field_from_expr(pr):
    """Extract 'Table.Column' or 'Measure' string from a PBIR projection."""
    try:
        f = pr.get('field', pr)
        col = f.get('Column') or f.get('Measure') or f.get('HierarchyLevel')
        if not col:
            return None
        expr = col.get('Expression', {})
        source_ref = expr.get('SourceRef', {})
        entity = source_ref.get('Entity') or source_ref.get('Source')
        prop = col.get('Property') or col.get('Level')
        if entity and prop:
            return f'{entity}.{prop}'
        if prop:
            return prop
    except (KeyError, TypeError, AttributeError):
        pass
    return None


def extract_pbir_visual(vo):
    inner = vo.get('visual', vo)
    visual = {
        'type': inner.get('visualType', 'unknown'),
        'title': '',
        'fields': [],
    }
    try:
        t = inner.get('objects', {}).get('title', [{}])[0].get(
            'properties', {}).get('text', {}).get('expr', {}).get(
            'Literal', {}).get('Value')
        if t:
            visual['title'] = t.strip("'")
    except (KeyError, IndexError, AttributeError, TypeError):
        pass
    query_state = inner.get('query', {}).get('queryState', {})
    for role, rdata in query_state.items():
        for pr in rdata.get('projections', []):
            field = extract_field_from_expr(pr)
            if field:
                visual['fields'].append(field)
    return visual


def extract_legacy_visual(config, query):
    sv = config.get('singleVisual', {})
    visual = {
        'type': sv.get('visualType', 'unknown'),
        'title': '',
        'fields': [],
    }
    try:
        t = sv.get('objects', {}).get('title', [{}])[0].get(
            'properties', {}).get('text', {}).get('expr', {}).get(
            'Literal', {}).get('Value')
        if t:
            visual['title'] = t.strip("'")
    except (KeyError, IndexError, AttributeError, TypeError):
        pass
    for role, prs in sv.get('projections', {}).items():
        for pr in prs:
            if 'queryRef' in pr:
                visual['fields'].append(pr['queryRef'])
    return visual


def parse_report(pbip_root):
    pbip_root = Path(pbip_root)
    report = {'pages': []}

    report_dirs = list(pbip_root.glob('*.Report'))
    if not report_dirs:
        return report
    report_dir = report_dirs[0]

    pbir_def = report_dir / 'definition' / 'pages'
    if pbir_def.is_dir():
        # PBIR format
        page_order = {}
        pages_json = pbir_def / 'pages.json'
        if pages_json.is_file():
            try:
                pf = json.loads(pages_json.read_text(encoding='utf-8'))
                for idx, name in enumerate(pf.get('pageOrder', [])):
                    page_order[name] = idx
            except (json.JSONDecodeError, KeyError):
                pass

        for page_folder in sorted(pbir_def.iterdir()):
            if not page_folder.is_dir():
                continue
            page_file = page_folder / 'page.json'
            if not page_file.is_file():
                continue
            try:
                obj = json.loads(page_file.read_text(encoding='utf-8'))
            except json.JSONDecodeError:
                continue
            page = {
                'name': obj.get('name', page_folder.name),
                'displayName': obj.get('displayName', page_folder.name),
                'visuals': [],
                'order': page_order.get(obj.get('name'), 999),
            }
            visuals_dir = page_folder / 'visuals'
            if visuals_dir.is_dir():
                for vf in sorted(visuals_dir.iterdir()):
                    if not vf.is_dir():
                        continue
                    vjson = vf / 'visual.json'
                    if vjson.is_file():
                        try:
                            vo = json.loads(vjson.read_text(encoding='utf-8'))
                            page['visuals'].append(extract_pbir_visual(vo))
                        except json.JSONDecodeError:
                            pass
            report['pages'].append(page)
        report['pages'].sort(key=lambda p: p['order'])
    else:
        # Legacy report.json
        report_json = report_dir / 'report.json'
        if report_json.is_file():
            try:
                obj = json.loads(report_json.read_text(encoding='utf-8'))
                for s in obj.get('sections', []):
                    page = {
                        'name': s.get('name', ''),
                        'displayName': s.get('displayName', s.get('name', '')),
                        'visuals': [],
                    }
                    for vc in s.get('visualContainers', []):
                        try:
                            cfg = json.loads(vc.get('config', '{}'))
                            q = vc.get('query')
                            if isinstance(q, str):
                                q = json.loads(q) if q else None
                            page['visuals'].append(extract_legacy_visual(cfg, q))
                        except (json.JSONDecodeError, TypeError):
                            pass
                    report['pages'].append(page)
            except json.JSONDecodeError:
                pass

    return report


def main():
    args = sys.argv[1:]
    if not args or args[0] in ('-h', '--help'):
        print(__doc__)
        sys.exit(0 if args else 1)

    pbip_path = args[0]
    output_file = None
    if '--output' in args:
        idx = args.index('--output')
        if idx + 1 < len(args):
            output_file = args[idx + 1]

    if not os.path.isdir(pbip_path):
        print(f'Error: {pbip_path} is not a directory', file=sys.stderr)
        sys.exit(1)

    result = {
        'model': parse_model(pbip_path),
        'report': parse_report(pbip_path),
    }

    out_json = json.dumps(result, indent=2, ensure_ascii=False)
    if output_file:
        Path(output_file).write_text(out_json, encoding='utf-8')
        print(f'Wrote {output_file}')
    else:
        print(out_json)


if __name__ == '__main__':
    main()
