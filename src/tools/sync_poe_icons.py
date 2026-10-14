"""Copy POE Source's icon lookup into src/content/poe2_icons.json, so character sheets show item, rune and gem art.

    python3 src/tools/sync_poe_icons.py [path/to/poe2source]   # default: ../poe2source next to this repo

Run it when POE Source adds new items. Icons are served from POE Source's public gear-icons storage.
"""
import json, os, sys, unicodedata, re

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(os.path.dirname(ROOT), 'poe2source')
DATA = os.path.join(SRC, 'src', 'data')

def norm(name):
    name = unicodedata.normalize('NFKD', name.lower()).replace('’', "'").replace('`', "'")
    return re.sub(r'\s+', ' ', name).strip()

gear = json.load(open(os.path.join(DATA, 'gear', 'poe2.json')))['items']
items = json.load(open(os.path.join(DATA, 'items', 'poe2.json')))
colors = json.load(open(os.path.join(DATA, 'gem-colors.json'))).get('byMetaId', {})

by_name, by_meta, bases = {}, {}, set()
for key, v in gear.items():
    if not v.get('iconPath'): continue
    by_name[key] = v['iconPath']
    if v.get('metaId'): by_meta[v['metaId']] = v['iconPath']
    if v.get('kind') == 'base': bases.add(norm(v['name']))
for meta, info in items.items():
    icon = (info or {}).get('icon') or ''
    if not icon: continue
    path = re.sub(r'^/?icons/', '', icon)
    by_meta.setdefault(meta, path)
    if info.get('name'): by_name.setdefault(norm(info['name']), path)

# gems: attribute color (gem border), tags and the one-line description for gem tooltips
gems = {}
for meta, info in items.items():
    if '/Gem' not in meta or not info: continue
    gems[meta] = [info.get('color') or colors.get(meta) or 'Colorless', ', '.join(info.get('tags') or []), (info.get('description') or '').strip()]
out = {'byName': dict(sorted(by_name.items())), 'byMeta': dict(sorted(by_meta.items())),
       'gems': dict(sorted(gems.items())),
       'bases': sorted(bases, key=lambda b: (-len(b), b))}
dest = os.path.join(ROOT, 'src', 'content', 'poe2_icons.json')
with open(dest, 'w') as f: json.dump(out, f, ensure_ascii=False, separators=(',', ':')); f.write('\n')
print(f'{len(by_name)} names, {len(by_meta)} ids, {len(gems)} gems -> {os.path.relpath(dest, ROOT)} ({os.path.getsize(dest) // 1024} KB)')
