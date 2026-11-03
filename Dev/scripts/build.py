#!/usr/bin/env python3
"""Build the ND-iTC website from data/*.json.

    python3 scripts/build.py [YYYY-MM-DD]
    ND_BASE_URL=https://nd-itc.github.io/ND-iTC-site-dev/ python3 scripts/build.py   # dev build

Reads   data/site.json   (releases, allowed-with lists, resources)
        data/tds.json    (active Technical Decisions)
        data/tds_archived.json (archived Technical Decisions)
Reads   data/ndcpp_v4_sfr.json (made by scripts/extract_sfr_map.py; optional)
Writes  index.html, TD/tech_dec.html, TD/tech_dec_arch.html, map/ndcpp-4.0.html,
        feed.xml, sitemap.xml, data/tds.csv

Add a Technical Decision: append it to data/tds.json, run the script, commit.
Python standard library only; the AWL and training pages are rendered from .adoc with asciidoctor
(if it is not installed, those pages are left as they are).
"""
import csv
import datetime
import html
import json
import os
import random
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
os.chdir(ROOT)
SITE = json.load(open('data/site.json', encoding='utf-8'))
TDS = json.load(open('data/tds.json', encoding='utf-8'))
ARCH = json.load(open('data/tds_archived.json', encoding='utf-8')) if os.path.exists('data/tds_archived.json') else []
BASE = os.environ.get('ND_BASE_URL', SITE['base_url'])
if not BASE.endswith('/'):
    BASE += '/'
TODAY = datetime.date.today()
if len(sys.argv) > 1:
    TODAY = datetime.date.fromisoformat(sys.argv[1])

e = html.escape


def esc(s):
    return e(str(s), quote=True)


def fmt_date(iso, short=False):
    d = datetime.date.fromisoformat(iso)
    return d.strftime('%-d %b %Y' if short else '%-d %B %Y')


def is_url(p):
    return bool(re.match(r'https?://', p))


def href(p, depth):
    return p if is_url(p) else ('../' * depth) + p


def abs_url(p):
    return p if is_url(p) else BASE + p


# ---------------------------------------------------------------- icons
ICONS = {
    'pdf': '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h4"/>',
    'html': '<path d="m8 8-4 4 4 4M16 8l4 4-4 4M13.5 5l-3 14"/>',
    'source': '<circle cx="6" cy="6" r="2.2"/><circle cx="6" cy="18" r="2.2"/><circle cx="18" cy="8" r="2.2"/><path d="M6 8.2v7.6M18 10.2c0 4-6 3-11 6.2"/>',
    'copy': '<rect x="9" y="9" width="11" height="11" rx="2"/><path d="M5 15V6a2 2 0 0 1 2-2h9"/>',
    'cite': '<path d="M7 7h4v5H7zM13 7h4v5h-4z"/><path d="M7 12c0 3-1 4-2 5M13 12c0 3-1 4-2 5"/>',
    'link': '<path d="M10 14a4 4 0 0 0 5.7 0l3-3a4 4 0 0 0-5.7-5.7l-1 1"/><path d="M14 10a4 4 0 0 0-5.7 0l-3 3a4 4 0 0 0 5.7 5.7l1-1"/>',
    'download': '<path d="M12 4v11m0 0-4-4m4 4 4-4M5 20h14"/>',
    'search': '<circle cx="11" cy="11" r="6.5"/><path d="m20 20-4-4"/>',
    'sun': '<circle cx="12" cy="12" r="4"/><path d="M12 3v2M12 19v2M3 12h2M19 12h2M5.6 5.6 7 7M17 17l1.4 1.4M5.6 18.4 7 17M17 7l1.4-1.4"/>',
    'book': '<path d="M5 4h11a3 3 0 0 1 3 3v13H8a3 3 0 0 1-3-3z"/><path d="M5 17a3 3 0 0 1 3-3h11"/>',
    'table': '<rect x="3" y="5" width="18" height="14" rx="2"/><path d="M3 10h18M9 10v9"/>',
    'chat': '<path d="M4 5h16v11H9l-5 4z"/>',
    'pencil': '<path d="m4 20 1-4L16 5l3 3L8 19zM14 7l3 3"/>',
    'globe': '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3c3 3 3 15 0 18M12 3c-3 3-3 15 0 18"/>',
    'code': '<path d="m9 8-4 4 4 4M15 8l4 4-4 4"/>',
    'chev': '<path d="m9 6 6 6-6 6"/>',
    'rss': '<path d="M5 5a14 14 0 0 1 14 14M5 11a8 8 0 0 1 8 8"/><circle cx="6" cy="18" r="1.5"/>',
    'arrow': '<path d="M5 12h14m-5-5 5 5-5 5"/>',
    'share': '<circle cx="6" cy="12" r="2.3"/><circle cx="18" cy="6" r="2.3"/><circle cx="18" cy="18" r="2.3"/><path d="m8 11 8-4M8 13l8 4"/>',
    'menu': '<path d="M4 7h16M4 12h16M4 17h16"/>',
    'csv': '<path d="M14 3H7a2 2 0 0 0-2 2v14a2 2 0 0 0 2 2h10a2 2 0 0 0 2-2V8z"/><path d="M14 3v5h5M9 13h6M9 17h6"/>',
}


def icon(name):
    return ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" '
            'stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">%s</svg>' % ICONS[name])


LOGO = ('<svg viewBox="0 0 40 40" aria-hidden="true"><rect width="40" height="40" rx="10" fill="#0c1530"/>'
        '<path d="M8 27 17 12l7 11 8-13" fill="none" stroke="#7f8cff" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"/>'
        '<circle cx="8" cy="27" r="3.2" fill="#0c1530" stroke="#7f8cff" stroke-width="2"/>'
        '<circle cx="17" cy="12" r="3.2" fill="#0c1530" stroke="#7f8cff" stroke-width="2"/>'
        '<circle cx="24" cy="23" r="3.2" fill="#0c1530" stroke="#7f8cff" stroke-width="2"/>'
        '<circle cx="32" cy="10" r="3.6" fill="#c6f432"/></svg>')


def mesh(seed=7, w=1200, h=600, n=30):
    """Deterministic network mesh: nodes, links and travelling pulses."""
    rnd = random.Random(seed)
    cols, rows = 8, 4
    pts = []
    for i in range(n):
        gx, gy = i % cols, (i // cols) % rows
        pts.append((int((gx + .5) * w / cols + rnd.uniform(-60, 60)), int((gy + .5) * h / rows + rnd.uniform(-55, 55))))
    pts = pts[:n]
    links = set()
    for i, p in enumerate(pts):
        d = sorted(((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2, j) for j, q in enumerate(pts) if j != i)
        for _, j in d[:2]:
            links.add(tuple(sorted((i, j))))
    out = ['<svg class="hero-mesh" viewBox="0 0 %d %d" preserveAspectRatio="xMidYMid slice" aria-hidden="true" focusable="false">' % (w, h)]
    for a, b in sorted(links):
        (x1, y1), (x2, y2) = pts[a], pts[b]
        out.append('<line class="mesh-link" x1="%d" y1="%d" x2="%d" y2="%d"/>' % (x1, y1, x2, y2))
    for k, (a, b) in enumerate(sorted(links)):
        if k % 3 == 0:
            (x1, y1), (x2, y2) = pts[a], pts[b]
            out.append('<line class="mesh-pulse" pathLength="246" x1="%d" y1="%d" x2="%d" y2="%d" style="animation-delay:-%.1fs;animation-duration:%.1fs"/>'
                       % (x1, y1, x2, y2, rnd.uniform(0, 6), rnd.uniform(4.5, 8)))
    hubs = set(rnd.sample(range(len(pts)), 5))
    for i, (x, y) in enumerate(pts):
        out.append('<circle class="mesh-node%s" cx="%d" cy="%d" r="%d"/>' % (' hub' if i in hubs else '', x, y, 5 if i in hubs else 3.5))
    out.append('</svg>')
    return ''.join(out)


# ---------------------------------------------------------------- data prep
REL = {r['id']: r for r in SITE['releases']}
for r in SITE['releases']:
    r['status_label'] = {'current': 'Current', 'previous': 'Previous', 'sunset': 'Sunset'}[r['status']]

APPLIES = {
    'NDcPPv4.0': ('NDcPP v4.0', 'ndcpp-4.0'), 'NDSDv4.0': ('ND SD v4.0', 'ndcpp-4.0'),
    'NDcPPv3.0e': ('NDcPP v3.0e', 'ndcpp-3.0e'), 'NDSDv3.0e': ('ND SD v3.0e', 'ndcpp-3.0e'),
    'FWv1.4': ('FW Module v1.4e', 'fw-1.4e'), 'MOD_CPP_FW_v1.4e': ('FW Module v1.4e', 'fw-1.4e'),
    'MOD_FW_v1.4e-SD': ('FW SD v1.4e', 'fw-1.4e'),
}


def prep_td(t, depth):
    n = re.search(r'(\d{6})', t['id']).group(1)
    t = dict(t)
    t['num'] = n
    t['anchor'] = 'RFI-' + n
    t['year'] = t['date'][:4]
    t['url'] = abs_url(t['file'])
    t['labels'] = [APPLIES.get(a, (a, ''))[0] for a in t['applies']]
    t['fams'] = sorted({APPLIES.get(a, ('', ''))[1] for a in t['applies']} - {''})
    t['permalink'] = BASE + 'TD/tech_dec.html#' + t['anchor']
    t['cite'] = 'ND-iTC Technical Decision %s: %s (%s). %s' % (t['id'], t['title'], fmt_date(t['date']), t['url'])
    return t


def action(label, ic, href_=None, copy=None, ok=None, primary=False, new=False, title=None):
    cls = 'act primary' if primary else 'act'
    if copy is not None:
        return ('<button type="button" class="%s" data-copy="%s" data-ok="%s"%s>%s<span>%s</span></button>'
                % (cls, esc(copy), esc(ok or 'Copied'), (' title="%s"' % esc(title)) if title else '', icon(ic), e(label)))
    extra = ' target="_blank" rel="noopener"' if new else ''
    return '<a class="%s" href="%s"%s>%s<span>%s</span></a>' % (cls, esc(href_), extra, icon(ic), e(label))


def doc_row(rel, d, depth=0):
    acts = [action('PDF', 'pdf', href(d['pdf'], depth), primary=True, new=is_url(d['pdf']))]
    if d.get('html'):
        acts.append(action('HTML', 'html', href(d['html'], depth)))
    if d.get('source'):
        acts.append(action('Source', 'source', href(d['source'], depth), new=True))
    acts.append(action('Copy link', 'link', copy=abs_url(d['pdf']), ok='Link copied'))
    return ('<div class="docrow"><div class="meta"><span class="doctype">%s</span><span class="ver">v%s</span></div>'
            '<h4>%s</h4><div class="actions">%s</div></div>' % (e(d['kind']), e(d['version']), e(d['title']), ''.join(acts)))


def release_card(rel):
    return ('<article class="release %s" id="%s"><header><div><h3>%s</h3><p>%s</p></div>'
            '<div style="text-align:right"><span class="status %s">%s</span><div class="when">Published <time datetime="%s">%s</time></div></div></header>%s</article>'
            % (rel['status'], rel['id'], e(rel['name']), e(rel['group']), rel['status'], rel['status_label'],
               rel['date'], fmt_date(rel['date']), ''.join(doc_row(rel, d) for d in rel['docs'])))


def timeline_item(rel):
    return ('<details class="tl-item %s" data-release="%s" id="%s"><summary><span class="status %s">%s</span><h3>%s</h3>'
            '<span class="when">%s · Published <time datetime="%s">%s</time></span>%s</summary><div class="docs">%s</div></details>'
            % (rel['status'], rel['status'], rel['id'], rel['status'], rel['status_label'], e(rel['name']), e(rel['group']),
               rel['date'], fmt_date(rel['date']), icon('chev').replace('<svg ', '<svg class="chev" '),
               ''.join(doc_row(rel, d) for d in rel['docs'])))


# ---------------------------------------------------------------- shared chrome
def head(title, desc, path, depth, extra=''):
    pre = '../' * depth
    canon = BASE + path
    return '''<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>%(title)s</title>
<meta name="description" content="%(desc)s">
<link rel="canonical" href="%(canon)s">
<meta name="theme-color" content="#0c1530">
<meta property="og:type" content="website">
<meta property="og:site_name" content="ND-iTC">
<meta property="og:title" content="%(title)s">
<meta property="og:description" content="%(desc)s">
<meta property="og:url" content="%(canon)s">
<meta property="og:image" content="%(base)simages/og.png">
<meta name="twitter:card" content="summary_large_image">
<link rel="icon" href="%(pre)simages/favicon.svg" type="image/svg+xml">
<link rel="alternate" type="application/atom+xml" title="ND-iTC Technical Decisions" href="%(pre)sfeed.xml">
<link rel="stylesheet" href="%(pre)ssite.css">
<script>try{var t=null,q=/[?&]nd-theme=(light|dark)/.exec(location.search);if(q)t=q[1];try{if(!t)t=localStorage.getItem('nd-theme')}catch(e){}if(!t){var m=/(?:^|;)nd-theme=(light|dark)/.exec(window.name);t=m&&m[1]}if(t==='light'||t==='dark')document.documentElement.setAttribute('data-theme',t)}catch(e){}</script>
%(extra)s</head>
<body>
<a class="skip" href="#main">Skip to content</a>
''' % dict(title=esc(title), desc=esc(desc), canon=canon, base=BASE, pre=pre, extra=extra)


NAV = [  # (group heading, [(label, target, key)])
    (None, [('Home', 'index.html', 'home')]),
    ('Documents', [('Current documents', 'index.html#current', 'docs'), ('Earlier versions', 'index.html#library', 'earlier')]),
    ('Technical Decisions', [('Active decisions', 'TD/tech_dec.html', 'td'), ('Archived decisions', 'TD/tech_dec_arch.html', 'tdarch')]),
    ('Allowed-with lists', [('NDcPP', 'AWL/NDcPP_allowed_with_list.html', 'awl-nd'), ('Firewall PP-Module', 'AWL/FW_allowed_with_list.html', 'awl-fw')]),
    ('Explore', [('NDcPP v4.0 dependency map', 'map/ndcpp-4.0.html', 'map')]),
    ('About', [('Resources', 'index.html#resources', 'res'), ('Join the ND-iTC', 'index.html#join', 'join')]),
]


def topbar(depth, current):
    pre = '../' * depth

    def a(label, target, key):
        return '<a href="%s"%s>%s</a>' % (pre + target, ' aria-current="page"' if key == current else '', label)
    groups = ''
    for heading, items in NAV:
        groups += '<div class="nav-group"%s>%s%s</div>\n' % (
            ' role="group" aria-label="%s"' % heading if heading else '',
            '<span class="nav-h">%s</span>' % heading if heading else '', ''.join(a(*i) for i in items))
    return '''<header class="topbar"><div class="wrap">
<a class="brand" href="%(pre)sindex.html" aria-label="ND-iTC home">%(logo)s<span>ND-iTC<small>Network Device iTC</small></span></a>
<div class="tools">
<button type="button" class="btn-ghost" id="open-search" aria-label="Search documents and decisions">%(s)s<span class="label">Search</span><span class="kbd">⌘K</span></button>
<button type="button" class="btn-ghost" id="theme-toggle" aria-label="Toggle light and dark theme">%(sun)s</button>
<button type="button" class="btn-ghost menu-toggle" id="menu-toggle" aria-label="Menu" aria-expanded="false" aria-controls="nav">%(menu)s</button>
</div>
<nav class="nav" id="nav" aria-label="Main">
%(groups)s</nav>
</div></header>
''' % dict(pre=pre, logo=LOGO, s=icon('search'), sun=icon('sun'), menu=icon('menu'), groups=groups)


PALETTE = '''<div class="palette" id="palette" role="dialog" aria-modal="true" aria-label="Search" hidden>
<div class="palette-box"><input id="palette-input" type="search" placeholder="Search documents, RFI numbers, requirements (e.g. FCS_TLSS_EXT.1)…" autocomplete="off" aria-label="Search">
<ul class="palette-list" id="palette-list" role="listbox"></ul>
<div class="palette-foot"><span>↑↓ to move</span><span>Enter to open</span><span>Esc to close</span></div></div></div>
<div class="toast" id="toast" role="status" aria-live="polite"></div>
'''


def footer(depth):
    pre = '../' * depth
    L = SITE['links']
    return '''<footer class="site"><div class="wrap">
<div><h2>ND-iTC</h2><p>The Network Device international Technical Community: certification bodies, labs and vendors working together on security requirements for network devices.</p></div>
<div><h2>Explore</h2><ul>
<li><a href="%(pre)sindex.html#current">Current documents</a></li>
<li><a href="%(pre)sTD/tech_dec.html">Technical Decisions</a></li>
<li><a href="%(pre)sTD/tech_dec_arch.html">Archived Technical Decisions</a></li>
<li><a href="%(pre)sindex.html#allowed-with">Allowed-with lists</a></li>
<li><a href="%(pre)smap/ndcpp-4.0.html">NDcPP v4.0 dependency map</a></li></ul></div>
<div><h2>Take it with you</h2><ul>
<li><a href="%(pre)sfeed.xml">Technical Decisions feed (Atom)</a></li>
<li><a href="%(pre)sdata/tds.csv" download>All decisions as CSV</a></li>
<li><a href="%(pre)sdata/tds.json" download>All decisions as JSON</a></li>
<li><a href="%(cc)s">Common Criteria Portal</a></li>
<li><a href="%(repo)s">Website source on GitHub</a></li></ul></div>
<div class="legal">PDF editions are the authoritative versions of each document; HTML editions are provided for navigation. Site last built <time datetime="%(iso)s">%(today)s</time>. Released under the repository's <a href="%(repo)s/blob/main/LICENSE">licence</a>.</div>
</div></footer>
''' % dict(pre=pre, cc=L['cc_portal'], repo=L['site_repo'], iso=TODAY.isoformat(), today=fmt_date(TODAY.isoformat()))


def page_end(depth, data):
    pre = '../' * depth
    return PALETTE + '<script type="application/json" id="nd-data">%s</script>\n<script src="%ssite.js"></script>\n</body>\n</html>\n' % (
        json.dumps(data, ensure_ascii=False).replace('</', '<\\/'), pre)


def search_index(depth, tds):
    pre = '../' * depth
    items = []
    for r in SITE['releases']:
        for d in r['docs']:
            items.append(dict(k=d['kind'], t='%s v%s' % (d['short'], d['version']), s=r['name'], u=href(d['pdf'], depth), x='pdf ' + r['status']))
            if d.get('html'):
                items.append(dict(k=d['kind'] + ' HTML', t='%s v%s' % (d['short'], d['version']), s=r['name'], u=href(d['html'], depth), x='html'))
    for a in SITE['awl']:
        items.append(dict(k='AWL', t=a['title'], s='v' + a['version'], u=href(a['html'], depth), x='allowed with list'))
    for t in tds:
        items.append(dict(k='TD', t='%s  %s' % (t['id'], t['title']), s=t['date'], u=pre + 'TD/tech_dec.html#' + t['anchor'],
                          x=t['reference'] + ' ' + ' '.join(t['labels'])))
    for r in SITE['resources']:
        items.append(dict(k='Resource', t=r['title'], s='', u=href(r['href'], depth), x=r['text']))
    items += [dict(k='Page', t='NDcPP v4.0 dependency map', s='', u=pre + 'map/ndcpp-4.0.html', x='sfr dependencies')]
    items += [dict(k='Page', t='Technical Decisions', s='', u=pre + 'TD/tech_dec.html', x='tds rfi'),
              dict(k='Page', t='Archived Technical Decisions', s='', u=pre + 'TD/tech_dec_arch.html', x='tds archive')]
    return {'search': items}


# ---------------------------------------------------------------- home
def build_home(tds):
    cur = [r for r in SITE['releases'] if r['status'] == 'current']
    old = [r for r in SITE['releases'] if r['status'] != 'current']
    ndcpp = REL['ndcpp-4.0']
    fw = REL['fw-2.0']
    latest = sorted(tds, key=lambda t: t['date'], reverse=True)[:5]
    newest = latest[0]['date']

    def link_row(title, sub, target, cta='Open', new=False):
        return ('<a href="%s"%s><div><strong>%s</strong><span>%s</span></div><span class="go">%s →</span></a>'
                % (esc(target), ' target="_blank" rel="noopener"' if new else '', e(title), e(sub), e(cta)))

    d_cpp, d_sd = ndcpp['docs']
    fw_mod, fw_sd, fw_cfg = fw['docs']
    panels = {
        'ndcpp': [link_row('NDcPP v4.0', 'Requirements for the device', d_cpp['pdf'], 'PDF'),
                  link_row('Supporting Document v4.0', 'How each requirement is evaluated', d_sd['pdf'], 'PDF'),
                  link_row('Earlier NDcPP versions', 'v3.0e and v2.2e, kept for reference', '#library', 'View')],
        'fw': [link_row('FW Module v2.0', 'Stateful traffic filter firewall requirements', fw_mod['pdf'], 'PDF'),
               link_row('FW Module Supporting Document v2.0', 'How each requirement is evaluated', fw_sd['pdf'], 'PDF'),
               link_row('PP-Configuration v2.0', 'The valid Network Device + Firewall claim', fw_cfg['pdf'], 'PDF')],
        'td': [link_row('Active Technical Decisions', '%d decisions in force' % len(tds), 'TD/tech_dec.html', 'Open'),
               link_row('Archived Technical Decisions', 'No longer current, kept for traceability', 'TD/tech_dec_arch.html', 'Open'),
               link_row('Request an interpretation', 'Submit a request for the NIT to consider', SITE['links']['rfi_form'], 'Open', new=True)],
        'awl': [link_row('NDcPP allowed-with list', 'PP-Modules and packages allowed with NDcPP v4.0', SITE['awl'][0]['html'], 'Open'),
                link_row('Firewall allowed-with list', 'What may be claimed with the FW Module v2.0', SITE['awl'][1]['html'], 'Open')],
    }
    choices = [('ndcpp', 'NDcPP'), ('fw', 'FW PP-Module'), ('td', 'Technical Decisions'), ('awl', 'Allowed-with lists')]
    chip_html = ''.join('<button type="button" class="chip-btn" data-choice="%s" aria-pressed="%s">%s</button>' % (k, 'true' if i == 0 else 'false', e(v))
                        for i, (k, v) in enumerate(choices))
    panel_html = ''.join('<div class="chooser-out" data-panel="%s"%s>%s</div>' % (k, '' if i == 0 else ' hidden', ''.join(panel_html_))
                         for i, ((k, _), panel_html_) in enumerate(zip(choices, [panels[c[0]] for c in choices])))

    stats = [
        (ndcpp['name'].replace('NDcPP ', ''), 'Current Network Device cPP, published ' + fmt_date(ndcpp['date'], True)),
        (fw['name'].replace('FW Module ', ''), 'Current Firewall PP-Module, published ' + fmt_date(fw['date'], True)),
        (str(len(tds)), 'Technical Decisions on record'),
        (fmt_date(newest, True), 'Most recent Technical Decision'),
    ]
    stats_html = ''.join('<div class="stat"><b>%s</b><span>%s</span></div>' % (e(a), e(b)) for a, b in stats)

    td_items = ''.join(
        '<div class="td-item"><span class="id">%s</span><div><a class="t" href="TD/tech_dec.html#%s">%s</a><div class="sub">%s</div></div><time datetime="%s">%s</time></div>'
        % (e(t['id']), t['anchor'], e(t['title']), ''.join('<span class="tag">%s</span>' % e(l) for l in t['labels']), t['date'], fmt_date(t['date'], True))
        for t in latest)

    awl_cards = ''.join(
        '<div class="card"><h3>%s</h3><p>Applies to %s</p><div class="meta">v%s · %s</div><div class="actions" style="margin-top:.6rem">%s%s</div></div>'
        % (e(a['title']), e(a['applies_to']), e(a['version']), fmt_date(a['date']),
           action('Open', 'html', a['html'], primary=True),
           (action('PDF', 'pdf', a['pdf']) if os.path.exists(a['pdf']) else '') + action('Copy link', 'link', copy=abs_url(a['html']), ok='Link copied'))
        for a in SITE['awl'])

    def res_card(r):
        ext = is_url(r['href'])
        return ('<a class="card" href="%s"%s><span class="ico">%s</span><h3>%s</h3><p>%s</p></a>'
                % (esc(r['href']), ' target="_blank" rel="noopener"' if ext else '', icon(r['icon']), e(r['title']), e(r['text'])))

    counts = {s: len([r for r in old if r['status'] == s]) for s in ('previous', 'sunset')}
    pills = ('<button type="button" class="pill" data-status-filter="all" aria-pressed="true">All<span class="n">%d</span></button>'
             '<button type="button" class="pill" data-status-filter="previous" aria-pressed="false">Previous<span class="n">%d</span></button>'
             '<button type="button" class="pill" data-status-filter="sunset" aria-pressed="false">Sunset<span class="n">%d</span></button>'
             % (len(old), counts['previous'], counts['sunset']))

    desc = ('The Network Device iTC publishes the collaborative Protection Profile for Network Devices (NDcPP), '
            'the Firewall PP-Module, their Supporting Documents, allowed-with lists and Technical Decisions.')
    out = head('ND-iTC | Network Device international Technical Community', desc, '', 0)
    out += topbar(0, 'home')
    out += '''<main id="main">
<section class="hero"><div class="wrap">%(mesh)s
<div class="hero-copy"><span class="eyebrow">Network Device international Technical Community</span>
<h1>Security requirements for the devices that <em>run the network</em>.</h1>
<p class="lede">The ND-iTC brings together certification bodies, evaluation labs and vendors to write the requirements, and the tests, that network device security evaluations are built on.</p>
</div>
<div class="hero-panel"><h2>Which documents do I need?</h2><div class="chooser" role="group" aria-label="Choose what you are evaluating">%(chips)s</div>%(panels)s</div>
</div></section>
<div class="stats"><div class="wrap">%(stats)s</div></div>

<section class="block" id="current"><div class="wrap">
<div class="sec-head"><div><span class="kicker">Authoritative</span><h2>Current documents</h2><p>These are the releases to evaluate against today. Download, link, or copy a ready-made citation for each document.</p></div>
<div class="actions"><a class="act primary" href="map/ndcpp-4.0.html">%(ar)s<span>NDcPP v4.0 dependency map</span></a></div></div>
<div class="release-grid">%(cur)s</div></div></section>

<section class="block" id="decisions"><div class="wrap">
<div class="sec-head"><div><span class="kicker">Between releases</span><h2>Latest Technical Decisions</h2><p>Technical Decisions clarify and update the cPP and related documents between release cycles.</p></div>
<div class="actions"><a class="act primary" href="TD/tech_dec.html">%(ar)s<span>All %(ntd)d decisions</span></a><a class="act" href="feed.xml">%(rss)s<span>Subscribe</span></a><a class="act" href="%(rfi)s" target="_blank" rel="noopener">%(chat)s<span>Request an interpretation</span></a></div></div>
<div class="td-list">%(tds)s</div></div></section>

<section class="block" id="allowed-with"><div class="wrap">
<div class="sec-head"><div><span class="kicker">Combining documents</span><h2>Allowed-with lists</h2><p>The published cPP and PP-Module each have an allowed-with list that defines which PP-Modules and packages may be used with them.</p></div></div>
<div class="cards">%(awl)s</div></div></section>

<section class="block" id="library"><div class="wrap">
<div class="sec-head"><div><span class="kicker">Reference</span><h2>Earlier versions</h2><p>Previous and sunset releases stay available for traceability. Their presence does not mean they are acceptable for new evaluations; check your scheme.</p></div><div class="filters" role="group" aria-label="Filter earlier versions">%(pills)s</div></div>
<div class="timeline">%(old)s</div></div></section>

<section class="block" id="resources"><div class="wrap">
<div class="sec-head"><div><span class="kicker">Tools &amp; guidance</span><h2>Resources</h2></div></div>
<div class="cards">%(res)s</div></div></section>

<section class="block" id="join"><div class="wrap"><div class="join">
<div class="join-intro"><h2>Join the ND-iTC</h2><p>The NDcPP and its Supporting Document are developed in the open. The working versions are on GitHub, where anyone can comment. Membership is for people who want to help write the next versions.</p></div>
<div class="join-grid">
<div class="join-card"><h3>Comment on the documents</h3><p>Spotted a typo, an unclear requirement or a gap? Open an issue on the Documents repository.</p>
<div class="cta" style="margin:0"><a class="btn btn-primary" href="%(issues)s" target="_blank" rel="noopener">Open an issue</a><a class="btn btn-line" href="%(docs)s" target="_blank" rel="noopener">Working documents on GitHub</a></div></div>
<div class="join-card"><h3>Become a member</h3><p>Members come from certification bodies, labs and vendors. To help shape future versions of the NDcPP, email the iTC.</p>
<div class="cta" style="margin:0"><a class="btn btn-primary" href="mailto:%(mail)s">Email the iTC</a><a class="btn btn-line" href="%(gh)s" target="_blank" rel="noopener">ND-iTC on GitHub</a></div></div>
</div>
<p class="join-note">Working versions are drafts. The published documents on this page are the ones to evaluate against.</p>
</div></div></section>
</main>
''' % dict(mesh=mesh(), cpp=d_cpp['pdf'], dl=icon('download'), ar=icon('arrow'), chips=chip_html, panels=panel_html, stats=stats_html,
           cur=''.join(release_card(r) for r in cur), ntd=len(tds), rss=icon('rss'), rfi=esc(SITE['links']['rfi_form']), issues=esc(SITE['links']['issues']), docs=esc(SITE['links']['documents_repo']), chat=icon('chat'),
           tds=td_items, awl=awl_cards, pills=pills, old=''.join(timeline_item(r) for r in old),
           res=''.join(res_card(r) for r in SITE['resources']), mail=SITE['contact_email'], gh=SITE['links']['github_org'])
    out += footer(0) + page_end(0, search_index(0, tds))
    open('index.html', 'w', encoding='utf-8').write(out)


# ---------------------------------------------------------------- TD pages
def build_td(rows, path, title, h1, intro, archive):
    depth = 1
    tds = [prep_td(t, depth) for t in rows]
    all_tds = [prep_td(t, depth) for t in TDS + ARCH]
    years = sorted({t['year'] for t in tds}, reverse=True)
    fam_opts = []
    for rid in ('ndcpp-4.0', 'ndcpp-3.0e', 'fw-2.0', 'fw-1.4e'):
        if any(rid in t['fams'] for t in tds):
            fam_opts.append((rid, REL[rid]['name'] + (' / SD' if rid.startswith('ndcpp') else '')))

    def row(t):
        data = json.dumps(dict(id=t['id'], title=t['title'], reference=t['reference'], date=t['date'], applies=t['labels'], status=t['status'], url=t['url']), ensure_ascii=False)
        text = ' '.join([t['id'], t['title'], t['reference'], t['date'], ' '.join(t['labels']), t['status']]).lower()
        acts = (action('PDF', 'pdf', '../' + t['file'], primary=True) + action('Link', 'link', copy=t['permalink'], ok='Permalink copied', title='Copy a permanent link to this decision') +
                action('Cite', 'cite', copy=t['cite'], ok='Citation copied', title='Copy a formatted citation'))
        return ('<tr id="%s" data-num="%s" data-id="%s" data-date="%s" data-year="%s" data-docs="%s" data-text="%s" data-json="%s">'
                '<td class="id" data-label="ID"><a href="#%s">%s</a></td>'
                '<td class="ttl" data-label="Decision"><a href="../%s">%s</a><div class="ref">%s</div></td>'
                '<td data-label="Published"><time datetime="%s">%s</time></td>'
                '<td data-label="Applies to">%s</td>'
                '<td data-label="Actions"><div class="actions">%s</div></td></tr>'
                % (t['anchor'], t['num'], esc(t['id']), t['date'], t['year'], ' '.join(t['fams']), esc(text), esc(data),
                   t['anchor'], e(t['id']), esc(t['file']), e(t['title']), e(t['reference']) if t['reference'] != 'N/A' else '',
                   t['date'], fmt_date(t['date'], True), ''.join('<span class="tag">%s</span>' % e(l) for l in t['labels']), acts))

    desc = intro
    out = head(title + ' | ND-iTC', desc, path, depth)
    out += topbar(depth, 'tdarch' if archive else 'td')
    out += '<main id="main"><section class="page-head">%s<div class="wrap"><div class="crumbs"><a href="../index.html">ND-iTC</a> / %s</div><h1>%s</h1><p>%s</p></div></section>\n' % (mesh(seed=3, n=24), e(h1), e(h1), e(intro))
    if rows:
        out += '''<div class="toolbar"><div class="wrap">
<div class="row"><label class="search"><span class="sr-only">Search decisions</span>%(s)s<input id="td-q" type="search" placeholder="Search RFI, title or requirement…" autocomplete="off"></label>
<label><span class="sr-only">Applies to</span><select class="field" id="td-doc"><option value="">All documents</option>%(docs)s</select></label>
<label><span class="sr-only">Year</span><select class="field" id="td-year"><option value="">All years</option>%(years)s</select></label>
<span class="count" id="td-count" aria-live="polite"></span></div>
<div class="row"><button type="button" class="act" id="td-export">%(csv)s<span>Export CSV</span></button><button type="button" class="act" id="td-share">%(share)s<span>Copy link to this view</span></button>
<a class="act" href="../feed.xml">%(rss)s<span>Feed</span></a><a class="act" href="%(rfi)s" target="_blank" rel="noopener">%(chat)s<span>New request for interpretation</span></a><button type="button" class="act" id="td-reset">Reset</button></div>
</div></div>
<div class="wrap" style="padding-block:0 3rem">
<table class="tdtable" id="td-table"><thead><tr>
<th data-sort="id" aria-sort="none"><button type="button">ID</button></th><th>Decision</th><th data-sort="date" aria-sort="descending"><button type="button">Published</button></th><th>Applies to</th><th>Get it</th></tr></thead>
<tbody>%(rows)s</tbody></table>
<div class="empty" id="td-none" hidden><h2>No decisions match</h2><p>Try fewer words, or reset the filters.</p></div>
<p class="note">Each decision has a permanent link and its own PDF. Use <strong>Cite</strong> to copy a formatted reference. The full set is also available as <a href="../data/tds.csv" download>CSV</a> and <a href="../data/tds.json" download>JSON</a>. <a href="%(other)s">%(otherl)s</a></p></div>
''' % dict(s=icon('search'), docs=''.join('<option value="%s">%s</option>' % (k, e(v)) for k, v in fam_opts),
           years=''.join('<option>%s</option>' % y for y in years), csv=icon('csv'), share=icon('share'), rss=icon('rss'), chat=icon('chat'),
           rfi=esc(SITE['links']['rfi_form']), rows=''.join(row(t) for t in tds),
           other='tech_dec_arch.html' if not archive else 'tech_dec.html',
           otherl='Archived Technical Decisions →' if not archive else '← Active Technical Decisions')
    else:
        out += '''<div class="wrap" style="padding-block:2rem 3rem"><div class="empty"><h2>Nothing has been archived yet</h2>
<p>Technical Decisions move here when the version they apply to is no longer current, or when a later decision supersedes them. All current decisions are on the <a href="tech_dec.html">active list</a>.</p></div>
<p class="note">Archived decisions stay available for traceability only. The <a href="tech_dec.html">active Technical Decisions</a> page lists everything in force.</p></div>
'''
    out += '</main>' + footer(depth)
    out += page_end(depth, search_index(depth, all_tds))
    open(path, 'w', encoding='utf-8').write(out)


def build_map():
    src = 'data/ndcpp_v4_sfr.json'
    if not os.path.exists(src):
        return False
    m = json.load(open(src, encoding='utf-8'))
    depth = 1
    for x in m['sfrs']:
        x['title'] = re.sub(r'^' + re.escape(x['id'].split('.')[0]) + r'\S*\s+', '', x['title'])
    payload = dict(sfrs=m['sfrs'], external=m['external_components'], cpp='../cPP/NDcPP_v4_0.html', sd='../SD/ND_Supporting_Document_4_0.html')
    path = 'map/ndcpp-4.0.html'
    title = 'NDcPP v4.0 Dependency Map'
    intro = 'Pick a security functional requirement to see what it depends on, what depends on it, and where it is specified and evaluated.'
    out = head(title + ' | ND-iTC', intro, path, depth)
    out += topbar(depth, 'map')
    out += '<main id="main"><section class="page-head">%s<div class="wrap"><div class="crumbs"><a href="../index.html">ND-iTC</a> / Dependency map</div><h1>%s</h1><p>%s</p></div></section>\n' % (mesh(seed=5, n=24), e(title), e(intro))
    out += '''<div class="wrap rm">
<div class="rm-list-col">
<div class="rm-tools"><label class="search"><span class="sr-only">Search requirements</span>%(s)s<input id="rm-q" type="search" placeholder="Search, e.g. FCS_CKM or key generation" autocomplete="off"></label>
<fieldset class="rm-types"><legend class="sr-only">Requirement type</legend>
<label><input type="checkbox" class="rm-type" value="mandatory" checked><span class="rm-badge mandatory">Mandatory</span></label>
<label><input type="checkbox" class="rm-type" value="selection-based" checked><span class="rm-badge selection-based">Selection-based</span></label>
<label><input type="checkbox" class="rm-type" value="optional" checked><span class="rm-badge optional">Optional</span></label></fieldset>
<div class="rm-meta"><span id="rm-count" aria-live="polite"></span><button type="button" class="act" id="rm-reset">Reset</button></div></div>
<div id="rm-list"></div>
<div class="empty" id="rm-none" hidden><h2>No requirements match</h2><p>Clear the search or turn a type back on.</p></div>
</div>
<aside class="rm-detail" id="rm-detail" aria-live="polite"><div class="rm-intro"><h2>How to read this</h2>
<p>Choose a requirement on the left. You will see the requirements it <strong>needs</strong> (dependencies listed in Annex E of the cPP) and those that <strong>need it</strong>, with links to the cPP and the Supporting Document.</p>
<p>Dependency names shown in grey, such as FPT_STM.1, come from the Common Criteria and are satisfied by an extended requirement in this cPP; the cPP's rationale says which.</p>
<p>Whether a selection-based or optional requirement applies to a given product depends on the selections made in its Security Target. The published PDF is authoritative; this map is for navigation.</p></div></aside>
</div>
''' % dict(s=icon('search'))
    out += '</main>' + footer(depth) + '<script type="application/json" id="rm-data">%s</script>\n<script src="../map.js"></script>\n' % json.dumps(payload, ensure_ascii=False).replace('</', '<\\/')
    out += page_end(depth, search_index(depth, [prep_td(t, depth) for t in TDS + ARCH]))
    os.makedirs('map', exist_ok=True)
    open(path, 'w', encoding='utf-8').write(out)
    return True


PROSE_PAGES = [  # (source, output, section key, crumb label, intro)
    ('AWL/NDcPP_allowed_with_list.adoc', 'AWL/NDcPP_allowed_with_list.html', 'awl-nd', 'Allowed-with lists',
     'Packages and PP-Modules to which exact conformance can be claimed alongside the Network Device cPP.'),
    ('AWL/FW_allowed_with_list.adoc', 'AWL/FW_allowed_with_list.html', 'awl-fw', 'Allowed-with lists',
     'Packages and PP-Modules to which exact conformance can be claimed alongside the Stateful Traffic Filter Firewall PP-Module.'),
    ('training/index.adoc', 'training/index.html', 'res', 'Resources',
     'How the ND-iTC uses GitHub and AsciiDoc to write, review and version its documents.'),
]


def build_prose(src, path, key, crumb, intro):
    """Render an AsciiDoc page with asciidoctor and wrap it in the site design."""
    import shutil
    import subprocess
    if not shutil.which('asciidoctor'):
        print('asciidoctor not found: left %s unchanged' % path)
        return
    body = subprocess.run(['asciidoctor', '-s', '-a', 'nofooter', '-a', 'toc!', '-o', '-', src], check=True, capture_output=True, text=True).stdout
    body = re.sub(r'\s*<h1[^>]*>.*?</h1>', '', body, count=1, flags=re.S)  # the page head already shows the title
    first = open(src, encoding='utf-8').readline()
    title = re.sub(r'^=\s*', '', first).strip()
    depth = path.count('/')
    toc = re.findall(r'<h([23]) id="([^"]+)">(.*?)</h\1>', body, re.S)
    toc_html = ''.join('<li class="l%s"><a href="#%s">%s</a></li>' % (l, i, re.sub(r'<[^>]+>', '', t)) for l, i, t in toc)
    out = head(title + ' | ND-iTC', intro, path, depth)
    out += topbar(depth, key)
    out += '<main id="main"><section class="page-head">%s<div class="wrap"><div class="crumbs"><a href="%sindex.html">ND-iTC</a> / %s</div><h1>%s</h1><p>%s</p></div></section>\n' % (
        mesh(seed=4, n=24), '../' * depth, e(crumb), e(title), e(intro))
    out += '<div class="wrap prose-wrap">%s<article class="prose">%s</article></div>' % (
        ('<nav class="prose-toc" aria-label="On this page"><h2>On this page</h2><ul>%s</ul></nav>' % toc_html) if toc_html else '', body)
    out += '</main>' + footer(depth) + page_end(depth, search_index(depth, [prep_td(t, depth) for t in TDS + ARCH]))
    open(path, 'w', encoding='utf-8').write(out)


def write_feeds(tds):
    items = sorted(tds, key=lambda t: t['date'], reverse=True)
    upd = items[0]['date'] + 'T00:00:00Z'
    x = ['<?xml version="1.0" encoding="utf-8"?>', '<feed xmlns="http://www.w3.org/2005/Atom">',
         '<title>ND-iTC Technical Decisions</title>', '<subtitle>Technical Decisions issued by the Network Device iTC</subtitle>',
         '<link href="%sfeed.xml" rel="self"/>' % BASE, '<link href="%sTD/tech_dec.html"/>' % BASE,
         '<id>%sTD/tech_dec.html</id>' % BASE, '<updated>%s</updated>' % upd, '<author><name>ND-iTC</name></author>']
    for t in items:
        x.append('<entry><title>%s: %s</title><link href="%s"/><id>%s</id><updated>%sT00:00:00Z</updated><summary>%s</summary></entry>'
                 % (e(t['id']), e(t['title']), e(t['url']), e(t['permalink']), t['date'],
                    e('Applies to: ' + ', '.join(t['labels']) + ('. Reference: ' + t['reference'] if t['reference'] != 'N/A' else ''))))
    x.append('</feed>')
    open('feed.xml', 'w', encoding='utf-8').write('\n'.join(x) + '\n')
    pages = ['', 'TD/tech_dec.html', 'TD/tech_dec_arch.html', 'map/ndcpp-4.0.html', 'AWL/NDcPP_allowed_with_list.html', 'AWL/FW_allowed_with_list.html']
    s = ['<?xml version="1.0" encoding="UTF-8"?>', '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    s += ['<url><loc>%s%s</loc><lastmod>%s</lastmod></url>' % (BASE, p, TODAY.isoformat()) for p in pages]
    s.append('</urlset>')
    open('sitemap.xml', 'w', encoding='utf-8').write('\n'.join(s) + '\n')
    with open('data/tds.csv', 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f)
        w.writerow(['ID', 'Title', 'Reference', 'Published', 'Applies to', 'Status', 'URL'])
        for t in items:
            w.writerow([t['id'], t['title'], t['reference'], t['date'], '; '.join(t['labels']), t['status'], t['url']])


DOC_PAGES = ['cPP/NDcPP_v3_0e.html', 'cPP/NDcPP_v4_0.html', 'SD/ND_Supporting_Document_3_0e.html',
             'SD/ND_Supporting_Document_4_0.html', 'PP-Module-FW/MOD_CPP_FW_v2.0.html', 'PP-Module-FW/SD_MOD_FW_v2.0.html']


def theme_docs():
    """Add the light/dark theme to the published document pages (idempotent; the documents' text is untouched)."""
    n = 0
    for f in DOC_PAGES:
        if not os.path.exists(f):
            continue
        h = open(f, encoding='utf-8').read()
        pre = '../' * f.count('/')
        block = ('<!-- nd-itc-theme --><link rel="stylesheet" href="%sdoc-theme.css">'
                 '<script src="%sdoc-theme.js"></script><!-- /nd-itc-theme -->') % (pre, pre)
        h2 = re.sub(r'<!-- nd-itc-theme -->.*?<!-- /nd-itc-theme -->', lambda m: block, h, flags=re.S)
        if h2 == h:
            h2 = h.replace('</head>', block + '</head>', 1)
        if h2 != h:
            open(f, 'w', encoding='utf-8').write(h2)
            n += 1
    return n


if __name__ == '__main__':
    prepped = [prep_td(t, 0) for t in TDS]
    missing = [t['file'] for t in TDS + ARCH if not os.path.exists(t['file'])]
    if missing:
        sys.exit('Missing TD files: %s' % missing)
    build_home(prepped)
    build_td(TDS, 'TD/tech_dec.html', 'Technical Decisions', 'Technical Decisions',
             'The iTC issues Technical Decisions in response to requests for interpretation, clarifying and updating the cPP and related documents between release cycles.', False)
    build_td(ARCH, 'TD/tech_dec_arch.html', 'Archived Technical Decisions', 'Archived Technical Decisions',
             'A historical record of Technical Decisions that are no longer current.', True)
    write_feeds(prepped)
    mapped = build_map()
    for args in PROSE_PAGES:
        build_prose(*args)
    theme_docs()
    print('Built: index.html, TD/tech_dec.html, TD/tech_dec_arch.html,%s feed.xml, sitemap.xml, data/tds.csv' % (' map/ndcpp-4.0.html,' if mapped else ''))
