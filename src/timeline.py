"""The Origin timeline: published moments from Supabase, rendered into pages/origin-timeline.html.

The back office edits the `timeline_moments` table. On every deploy the build fetches the published
rows with the site's publishable key (read-only, published rows only) and renders them here.
content/timeline.json is the last fetched copy, used when the network isn't reachable (local builds).
Set CONTENT_STRICT=1 (as Vercel does) to fail the build instead of using the copy.
"""
import json, os, urllib.request

API = 'https://pehytilcqrmzeuoewdnk.supabase.co'
KEY = 'sb_publishable_FDV1I_WPq08LBsNyHOsbow_iZ0gcXxP'   # publishable: the same key the site's forms use
SNAPSHOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'content', 'timeline.json')
COLS = 'sort,year_label,lane,title,body,anchor,media,media_style'
LANE_INDEX = {'life': 0, 'kitchen': 0, 'sound': 1, 'code': 2, 'play': 3}

def fetch():
    url = f'{API}/rest/v1/timeline_moments?select={COLS}&published=eq.true&order=sort.asc,id.asc'
    req = urllib.request.Request(url, headers={'apikey': KEY, 'Authorization': f'Bearer {KEY}'})
    with urllib.request.urlopen(req, timeout=20) as r:
        return json.loads(r.read().decode())

def load():
    """Published moments, newest from the database when reachable."""
    try:
        rows = fetch()
        if not rows: raise ValueError('no published moments')
        with open(SNAPSHOT, 'w') as f: json.dump(rows, f, ensure_ascii=False, indent=1); f.write('\n')
        return rows, 'database'
    except Exception as e:
        if os.environ.get('CONTENT_STRICT') == '1': raise SystemExit(f'timeline: could not load from the database ({e})')
        with open(SNAPSHOT) as f: return json.load(f), f'saved copy ({e.__class__.__name__})'

def esc(s, attr=False):
    s = str(s or '').replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
    return s.replace('"', '&quot;') if attr else s

def img(m, flat=False):
    cls = 'class="flat" ' if flat else ''
    return (f'<img {cls}src="{esc(m["src"], True)}" alt="{esc(m.get("alt"), True)}" '
            f'width="{int(m["w"])}" height="{int(m["h"])}" loading="lazy" decoding="async">')

def moment(r):
    lane, media, style = r['lane'], r.get('media') or [], r.get('media_style')
    if not media: style = None
    pic = style in ('flat', 'photo')
    if style == 'flat': box = f'<div class="ev-media">{img(media[0], True)}</div>'
    elif style == 'photo': box = f'<figure class="ev-media duo">{img(media[0])}</figure>'
    elif media: box = '<div class="ev-media">' + ''.join(img(m) for m in media) + '</div>'
    else: box = ''
    ident = f'id="{esc(r["anchor"], True)}" ' if r.get('anchor') else ''
    cls = 'ev ev-life' if lane == 'life' else 'ev'
    return (f'        <li {ident}class="{cls}" data-lane="{lane}" style="--li:{LANE_INDEX[lane]}"><span class="ev-dot" aria-hidden="true"></span>'
            f'<span class="ev-yr">{esc(r["year_label"])}</span><div class="ev-card{" has-pic" if pic else ""}"><span class="ev-tag">{lane.capitalize()}</span>'
            f'<h3>{esc(r["title"])}</h3><p>{esc(r["body"])}</p>{box}</div></li>\n')

def render(template, rows):
    """Replace the moments inside <ol class="tl"> of the page template."""
    start = template.index('</li>\n', template.index('<li class="rails"')) + 6
    end = template.index('      </ol>', start)
    return template[:start] + ''.join(moment(r) for r in rows) + template[end:]
