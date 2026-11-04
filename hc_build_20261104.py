#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""HC Dashboard 2026-11-02 数据更新：基于 hc_20261024.html 只换数据，不动 UI
数据源：/tmp/hc_sub_depts.json（部门树）+ /tmp/hc_flow_20261104.json（待入职/待离职明细）"""
import json, re

WS = '/home/node/.openclaw/workspace'
SRC = f'{WS}/hc_20261102.html'
OUT = f'{WS}/hc_20261104.html'
DATE = '2026-11-04'

trees = json.load(open('/tmp/hc_sub_depts.json'))
flows = json.load(open('/tmp/hc_flow_20261104.json'))
yibu = next(t for t in trees if t['departmentName'] == '行业一部')
liubu = next(t for t in trees if t['departmentName'] == '行业六部')

Y_CUR, Y_TOTAL = yibu['currentHc'], yibu['totalHc']
L_CUR, L_TOTAL = liubu['currentHc'], liubu['totalHc']
Y_IN, Y_OUT = yibu['transInHc'], yibu['transOutHc']
L_IN, L_OUT = liubu['transInHc'], liubu['transOutHc']
print(f'一部 cur={Y_CUR}/{Y_TOTAL} in={Y_IN} out={Y_OUT} | 六部 cur={L_CUR}/{L_TOTAL} in={L_IN} out={L_OUT}')

# 子组自洽校验（数据源可靠性先验）
def sum_children(d):
    ch = d['children']
    return (sum(c.get('currentHc') or 0 for c in ch),
            sum(c.get('transInHc') or 0 for c in ch),
            sum(c.get('transOutHc') or 0 for c in ch))
for d, tin, tout in [(yibu, Y_IN, Y_OUT), (liubu, L_IN, L_OUT)]:
    sc, sin, sout = sum_children(d)
    assert sin == tin and sout == tout, f'{d["departmentName"]} 子组流入流出({sin}/{sout})与顶层({tin}/{tout})不一致，中止'
    print(f'  {d["departmentName"]} subs: cur={sc} in={sin} out={sout} (rows={len(d["children"])}) 自洽 ✓')

html = open(SRC, encoding='utf-8').read()
orig_len = len(html)

# ---------- 1. BUDGET_DATA 两行 ----------
def patch_budget(html, l2, **kw):
    pat = r'("l2": "%s",\n    "budget": )\d+(,\n    "actual": )\d+(,\n    "transIn": )\d+(,\n    "transOut": )\d+' % l2
    rep = r'\g<1>%d\g<2>%d\g<3>%d\g<4>%d' % (kw['budget'], kw['actual'], kw['transIn'], kw['transOut'])
    html2, n = re.subn(pat, rep, html, count=1)
    assert n == 1, f'BUDGET_DATA {l2} not patched'
    return html2

html = patch_budget(html, '行业一部', budget=Y_TOTAL, actual=Y_CUR, transIn=Y_IN, transOut=Y_OUT)
html = patch_budget(html, '行业六部', budget=L_TOTAL, actual=L_CUR, transIn=L_IN, transOut=L_OUT)

# ---------- 2. HANGYIBU_SUBS 全量替换 ----------
def js_subs(children):
    rows = []
    for c in children:
        name = c['departmentName']
        leader = (c.get('leaderName') or '—').replace("'", "\\'")
        match = c.get('matchingDegreeName')
        m = f", match:'{match}'" if match else ', match:null'
        rows.append(
            "  {name:'%s', leader:'%s', current:%d, total:%d, transIn:%d, transOut:%d, predict:%d%s},"
            % (name, leader, c.get('currentHc') or 0, c.get('totalHc') or 0,
               c.get('transInHc') or 0, c.get('transOutHc') or 0,
               c.get('predictHc') or 0, m)
        )
    return 'const HANGYIBU_SUBS = [\n' + '\n'.join(rows) + '\n];'

html, n = re.subn(r"const HANGYIBU_SUBS = \[.*?\n\];", js_subs(yibu['children']), html, count=1, flags=re.S)
assert n == 1, 'HANGYIBU_SUBS not patched'

# ---------- 3. DEPT_DETAIL_DB 两个部门块 ----------
# 旧 internHc 保留：从旧文件抓 name->internHc
old_subs = dict()
for m in re.finditer(r'\{\s*"name": "([^"]+)",\s*"leader": "[^"]*",\s*"matchingDegree": "[^"]*",\s*"current": \d+,\s*"internHc": (\d+),', html):
    old_subs[m.group(1)] = int(m.group(2))

def build_subs_json(children):
    parts = []
    for c in children:
        name = c['departmentName']
        cur = c.get('currentHc') or 0
        tot = c.get('totalHc') or 0
        md = c.get('matchingDegreeName') or '匹配'
        match = '超编' if cur > tot else '达标'
        parts.append(
            '      {\n        "name": "%s",\n        "leader": "%s",\n        "matchingDegree": "%s",\n'
            '        "current": %d,\n        "internHc": %d,\n        "total": %d,\n'
            '        "transIn": %d,\n        "transOut": %d,\n        "predict": %d,\n        "match": "%s"\n      }'
            % (name, (c.get('leaderName') or '—').replace('"', '\\"'), md.replace('"', '\\"'), cur,
               old_subs.get(name, 0), tot,
               c.get('transInHc') or 0, c.get('transOutHc') or 0, c.get('predictHc') or 0, match)
        )
    return ',\n'.join(parts)

def patch_dept_header(html, dept, cur, budget, tin, tout):
    pat = r'("%s": \{\n    "deptName": "%s",\n    "leader": "[^"]*",\n    "matchingDegree": "[^"]*",\n    "currentHc": )\d+((?:,\n    "internHc": )\d+)(,\n    "budgetHc": )\d+(,\n    "transIn": )\d+(,\n    "transOut": )\d+' % (dept, dept)
    html2, n = re.subn(pat, lambda m: f"{m.group(1)}{cur}{m.group(2)}{m.group(3)}{budget}{m.group(4)}{tin}{m.group(5)}{tout}", html, count=1)
    assert n == 1, f'DEPT_DETAIL_DB {dept} header not patched'
    return html2

def patch_dept_subs(html, dept, children):
    pat = r'("deptName": "%s",[\s\S]*?"subs": \[)[\s\S]*?(\n    \])' % dept
    html2, n = re.subn(pat, lambda m: m.group(1) + '\n' + build_subs_json(children) + m.group(2), html, count=1)
    assert n == 1, f'DEPT_DETAIL_DB {dept} subs not patched'
    return html2

html = patch_dept_header(html, '行业一部', Y_CUR, Y_TOTAL, Y_IN, Y_OUT)
html = patch_dept_header(html, '行业六部', L_CUR, L_TOTAL, L_IN, L_OUT)
html = patch_dept_subs(html, '行业一部', yibu['children'])
html = patch_dept_subs(html, '行业六部', liubu['children'])

# ---------- 4. 月度趋势 2026年10月 ----------
html, n = re.subn(
    r'("month": "2026年10月",\n        "hcPercent": )[\d.]+(,\n        "totalHc": )%d(,\n        "currentHc": )\d+' % Y_TOTAL,
    r'\g<1>%.1f\g<2>%d\g<3>%d' % (Y_CUR / Y_TOTAL * 100, Y_TOTAL, Y_CUR), html, count=1)
assert n == 1, 'yibu trend not patched'
html, n = re.subn(
    r'("month": "2026年10月",\n        "hcPercent": )[\d.]+(,\n        "totalHc": )%d(,\n        "currentHc": )\d+' % L_TOTAL,
    r'\g<1>%.1f\g<2>%d\g<3>%d' % (L_CUR / L_TOTAL * 100, L_TOTAL, L_CUR), html, count=1)
assert n == 1, 'liubu trend not patched'

# ---------- 5. FLOW_DATA（数据驱动：来自待入职/待离职明细接口）----------
def make_level(lv):
    lv = lv or 'IC'
    return 'L1' if lv.startswith('L1') else ('L2' if lv.startswith('L2') else 'IC')

trans_in, trans_out = [], []
for p in flows['entry']['行业一部']:
    trans_in.append((p['showName'], make_level(p.get('manageLevel')), p['departmentName'],
                     p['entryDate'], p.get('leaderName') or '—'))
for dept_key in ['行业一部', '行业六部']:
    for p in flows['dimission'][dept_key]:
        trans_out.append((p['showName'], make_level(p.get('manageLevel')), p['departmentName'],
                          p['lastDate'], p.get('dimissionTypeName') or '主动离职',
                          make_level(p.get('manageLevel')) in ('L1', 'L2')))

def flow_in(p):
    return ('  {\n    "name": "%s",\n    "level": "%s",\n    "dept": "商业化",\n    "subDept": "%s",\n'
            '    "date": "%s",\n    "manager": "%s",\n    "highlight": false\n  }'
            % (p[0], p[1], p[2], p[3], p[4].replace('"', '\\"')))

def flow_out(p):
    return ('  {\n    "name": "%s",\n    "level": "%s",\n    "dept": "商业化",\n    "subDept": "%s",\n'
            '    "date": "%s",\n    "type": "%s",\n    "highlight": %s\n  }'
            % (p[0], p[1], p[2], p[3], p[4].replace('"', '\\"'), str(p[5]).lower()))

new_flow = ('const FLOW_DATA = {\n  transIn: [\n' + ',\n'.join(flow_in(p) for p in trans_in)
            + '\n],\n  transOut: [\n' + ',\n'.join(flow_out(p) for p in trans_out) + '\n]\n};')
html, n = re.subn(r'const FLOW_DATA = \{.*?\n\};', new_flow, html, count=1, flags=re.S)
assert n == 1, 'FLOW_DATA not patched'
print(f'FLOW: transIn={len(trans_in)} transOut={len(trans_out)}')

# ---------- 6. 时间戳 ----------
for old in ['2026 Q4 · 更新于 2026-11-02', '<title>HC Dashboard · 2026-11-02 · 招财出品</title>']:
    assert old in html, f'timestamp anchor missing: {old}'
html = html.replace('2026 Q4 · 更新于 2026-11-02', f'2026 Q4 · 更新于 {DATE}')
html = html.replace('<title>HC Dashboard · 2026-11-02 · 招财出品</title>', f'<title>HC Dashboard · {DATE} · 招财出品</title>')
html = re.sub(r'(// 真实入离职数据（来自 ehr-workbench/hrbp )[\d-]+(\）)', rf'\g<1>{DATE}\g<2>', html, count=1)
assert f'更新于 {DATE}' in html and f'HC Dashboard · {DATE}' in html, 'timestamp not updated'

open(OUT, 'w', encoding='utf-8').write(html)
print('written:', OUT, len(html), '(src', orig_len, ')')

# ---------- 自检 ----------
chk = open(OUT, encoding='utf-8').read()

block = re.search(r'const HANGYIBU_SUBS = \[([\s\S]*?)\n\];', chk).group(1)
rows = re.findall(r"current:(\d+), total:(\d+), transIn:(\d+), transOut:(\d+), predict:(\d+)", block)
c = [sum(int(r[i]) for r in rows) for i in range(5)]
print('一部subs: cur=%d total=%d in=%d out=%d pred=%d (rows=%d)' % (c[0], c[1], c[2], c[3], c[4], len(rows)))
assert c[0] == Y_CUR and c[2] == Y_IN and c[3] == Y_OUT and c[4] == (yibu.get('predictHc') or 0), '一部 subs sum mismatch'

for dept, exp_cur, exp_in, exp_out in [('行业一部', Y_CUR, Y_IN, Y_OUT), ('行业六部', L_CUR, L_IN, L_OUT)]:
    m = re.search(r'"deptName": "%s",[\s\S]*?"subs": \[([\s\S]*?)\n    \]' % dept, chk)
    rows2 = re.findall(r'"current": (\d+)', m.group(1))
    ins = re.findall(r'"transIn": (\d+)', m.group(1))
    outs = re.findall(r'"transOut": (\d+)', m.group(1))
    print('%s DETAIL subs: rows=%d cur=%d in=%d out=%d' % (dept, len(rows2), sum(map(int, rows2)), sum(map(int, ins)), sum(map(int, outs))))
    assert sum(map(int, ins)) == exp_in and sum(map(int, outs)) == exp_out, f'{dept} detail mismatch'

assert '"budgetHc": ,' not in chk, 'budgetHc broken'
assert re.search(r'"budgetHc": %d,\n    "transIn": %d' % (Y_TOTAL, Y_IN), chk), 'yibu budgetHc wrong'
assert re.search(r'"budgetHc": %d,\n    "transIn": %d' % (L_TOTAL, L_IN), chk), 'liubu budgetHc wrong'

flow_blk = re.search(r'const FLOW_DATA = \{[\s\S]*?\n\};', chk).group(0)
n_in = flow_blk.count('"manager": "')
n_out = flow_blk.count('"type": "')
hl_true = flow_blk.count('"highlight": true')
print('FLOW transIn=%d transOut=%d, highlight_true=%d' % (n_in, n_out, hl_true))
assert n_in == len(trans_in) and n_out == len(trans_out) and hl_true == sum(1 for p in trans_out if p[5])

print('BUDGET 一部:', re.search(r'"l2": "行业一部",\n    "budget": \d+,\n    "actual": \d+,\n    "transIn": \d+,\n    "transOut": \d+', chk).group(0).replace('\n', ' '))
print('BUDGET 六部:', re.search(r'"l2": "行业六部",\n    "budget": \d+,\n    "actual": \d+,\n    "transIn": \d+,\n    "transOut": \d+', chk).group(0).replace('\n', ' '))
print('== ALL CHECKS PASSED ==')
