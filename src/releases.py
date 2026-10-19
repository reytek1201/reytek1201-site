"""Releases (the music), from the `releases` table edited in the back office.

On every deploy the build fetches the published releases with the site's publishable key and turns them into the
turntable's track list, the Music page's release list and the lyrics. content/releases.json is the last copy that
was fetched (or, before anything is published in the database, the tracks that shipped with the repo) and is used
when the network can't be reached or the database has nothing published yet. CONTENT_STRICT=1 (Vercel) fails the
build on a network error instead of using the copy.
"""
import json, os, urllib.parse, urllib.request
from sitecontent import API, KEY

HERE = os.path.dirname(os.path.abspath(__file__))
SNAPSHOT = os.path.join(HERE, 'content', 'releases.json')
COLS = 'sort,title,is_new,release_date,notes,audio,cover,label_art,duration,gain,bpm,peaks,beats,lyrics_text,lyrics'
DEFAULT_SECTION = {'t': 0, 'name': 'Song', 'rgb': '34,211,238', 'lift': 0.6}

def load():
    """Published releases: from the database when it has some, otherwise the saved copy."""
    url = f'{API}/rest/v1/releases?' + urllib.parse.urlencode({'select': COLS, 'published': 'eq.true', 'order': 'sort.asc,id.asc'})
    try:
        req = urllib.request.Request(url, headers={'apikey': KEY, 'Authorization': f'Bearer {KEY}'})
        with urllib.request.urlopen(req, timeout=20) as r:
            rows = json.loads(r.read().decode())
    except Exception as e:
        if os.environ.get('CONTENT_STRICT') == '1': raise SystemExit(f'releases: could not load from the database ({e})')
        with open(SNAPSHOT) as f: return json.load(f), f'saved copy ({e.__class__.__name__})'
    if not rows:
        with open(SNAPSHOT) as f: return json.load(f), 'saved copy (nothing published in the database yet)'
    with open(SNAPSHOT, 'w') as f: json.dump(rows, f, ensure_ascii=False, indent=1); f.write('\n')
    return rows, 'database'

def _first(images):
    return ((images or [{}])[0] or {}).get('src') or ''

def tracks(rows):
    """The shape the turntable and the Music page use. Releases without audio yet are left out."""
    out = []
    for r in rows:
        audio = (r.get('audio') or {}).get('src')
        peaks = r.get('peaks') or []
        if not audio or len(peaks) < 10 or not r.get('duration'): continue
        label = _first(r.get('label_art'))
        t = {'title': r['title'], 'file': audio, 'cover': _first(r.get('cover')) or label, 'bpm': float(r.get('bpm') or 0),
             'dur': float(r['duration']), 'gain': float(r.get('gain') or 1), 'beats': r.get('beats') or [], 'peaks': peaks}
        if label: t['label'] = label
        if r.get('is_new'): t['isNew'] = True
        out.append(t)
    return out

def lyrics(rows):
    """Karaoke (timed words, needs beats) keyed by title, and plain lyrics keyed by title for releases without timing."""
    timed, plain = {}, {}
    for r in rows:
        ly, beats = r.get('lyrics'), r.get('beats') or []
        if ly and ly.get('lines') and len(beats) >= 8:
            timed[r['title']] = {'title': r['title'], 'downbeat': ly.get('downbeat', 0), 'sections': ly.get('sections') or [DEFAULT_SECTION],
                                 'lines': ly['lines'], 'beats': beats}
        elif (r.get('lyrics_text') or '').strip():
            plain[r['title']] = r['lyrics_text'].strip()
    return timed, plain
