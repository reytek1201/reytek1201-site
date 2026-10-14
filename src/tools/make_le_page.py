#!/usr/bin/env python3
"""Writes le-export/index.html: the drag-to-bookmarks page for the Export to reytek bookmarklet (src/tools/le_export.js).
Run it after editing le_export.js, then commit le-export/."""
import os, re, urllib.parse
HERE = os.path.dirname(os.path.abspath(__file__)); ROOT = os.path.normpath(os.path.join(HERE, '..', '..'))
src = open(os.path.join(HERE, 'le_export.js')).read()
src = re.sub(r'/\*.*?\*/', '', src, flags=re.S)
lines = []
for ln in src.split('\n'):
    if '://' not in ln: ln = re.sub(r'\s//\s.*$', '', ln)
    if ln.strip() and not ln.strip().startswith('//'): lines.append(ln.strip())
href = 'javascript:' + urllib.parse.quote('\n'.join(lines), safe="()*!~'-_.,:;=+$&@/?[]{}|<>")
page = f'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="robots" content="noindex"><title>Export to reytek</title>
<style>body{{margin:0;background:#0b0b0e;color:#e8e8ee;font:16px/1.55 system-ui,sans-serif;padding:32px 16px}}main{{max-width:620px;margin:0 auto}}
h1{{font-size:26px;margin:0 0 6px}}a.bm{{display:inline-block;margin:14px 0 22px;padding:12px 20px;border:1px solid #00d4ff;border-radius:10px;color:#00d4ff;text-decoration:none;font-weight:600;cursor:grab}}
ol{{padding-left:20px}}li{{margin:8px 0}}small{{color:#9a9aa6}}</style></head><body><main>
<h1>Export to reytek</h1><p>Copies a Last Epoch Tools build as data for the Gaming page. It only reads the page you are looking at and sends nothing anywhere.</p>
<a class="bm" href="{href}">Export to reytek</a>
<ol><li>Drag the button above onto your bookmarks bar.</li>
<li>Open your build on lastepochtools.com/planner and keep the tab in front.</li>
<li>Click the bookmark and wait about a minute for the "Copied" note.</li>
<li>Back office, Characters, the Last Epoch character, paste into "Last Epoch build data", save.</li></ol>
<p><small>It reads the planner's current layout, so if the site changes, it may need an update.</small></p></main></body></html>'''
os.makedirs(os.path.join(ROOT, 'le-export'), exist_ok=True)
open(os.path.join(ROOT, 'le-export', 'index.html'), 'w').write(page)
print('le-export/index.html', len(page), 'bytes; bookmarklet', len(href))
