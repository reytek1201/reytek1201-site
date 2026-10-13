"""Site content edited in the back office: fetch published rows from Supabase at build time.

Each table's last fetched copy is saved in content/<table>.json and used when the database can't be
reached (local builds). CONTENT_STRICT=1 (set on Vercel) fails the build instead.
"""
import json, os, urllib.parse, urllib.request

API = 'https://pehytilcqrmzeuoewdnk.supabase.co'
KEY = 'sb_publishable_FDV1I_WPq08LBsNyHOsbow_iZ0gcXxP'   # publishable: read-only, published rows only
HERE = os.path.dirname(os.path.abspath(__file__))

def load(table, cols):
    snapshot = os.path.join(HERE, 'content', f'{table}.json')
    url = f'{API}/rest/v1/{table}?' + urllib.parse.urlencode({'select': cols, 'published': 'eq.true', 'order': 'sort.asc,id.asc'})
    try:
        req = urllib.request.Request(url, headers={'apikey': KEY, 'Authorization': f'Bearer {KEY}'})
        with urllib.request.urlopen(req, timeout=20) as r:
            rows = json.loads(r.read().decode())
        if not rows: raise ValueError(f'no published rows in {table}')
        with open(snapshot, 'w') as f: json.dump(rows, f, ensure_ascii=False, indent=1); f.write('\n')
        return rows, 'database'
    except Exception as e:
        if os.environ.get('CONTENT_STRICT') == '1': raise SystemExit(f'{table}: could not load from the database ({e})')
        with open(snapshot) as f: return json.load(f), f'saved copy ({e.__class__.__name__})'
