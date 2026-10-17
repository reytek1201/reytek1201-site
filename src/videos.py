"""Music videos on the Music page, from the `videos` table (edited in the back office).

YouTube hosts the video. The page shows a Listen / Watch switch above the turntable, a framed 16:9 screen
with a click-to-load facade (the YouTube player is only created when someone presses play), a Watch button on
each release that has a video, and schema.org VideoObject data for search engines. The poster is YouTube's
thumbnail, saved to img/video/ at build time so the page doesn't call out; the saved copy is reused when
YouTube can't be reached (local builds).
"""
import html, json, os, re, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
COLS = 'slug,sort,release_title,title,kind,youtube_url,published_on,duration,blurb,poster,created_at'
SITE = 'https://www.reytek1201.com'
KINDS = {'music-video': 'Music video', 'visualizer': 'Visualizer', 'live': 'Live', 'making-of': 'Making of'}
e = lambda s: html.escape(str(s if s is not None else ''), True)

CAM = '<svg class="i-cam" viewBox="0 0 16 16" aria-hidden="true"><path d="M1.5 4.5a1.5 1.5 0 0 1 1.5-1.5h6a1.5 1.5 0 0 1 1.5 1.5v1.6l3.2-1.9a.5.5 0 0 1 .8.4v6.8a.5.5 0 0 1-.8.4L10.5 9.9v1.6A1.5 1.5 0 0 1 9 13H3a1.5 1.5 0 0 1-1.5-1.5z"/></svg>'

def video_id(url):
    m = re.search(r'(?:v=|shorts/|youtu\.be/)([A-Za-z0-9_-]{11})', url or '')
    return m.group(1) if m else None

def _save_poster(vid):
    """Save YouTube's thumbnail for this video to img/video/<id>.jpg. Returns True when a local copy exists."""
    path = os.path.join(ROOT, 'img', 'video', f'{vid}.jpg')
    if os.path.exists(path): return True
    for name in ('maxresdefault', 'hqdefault'):
        try:
            with urllib.request.urlopen(urllib.request.Request(f'https://i.ytimg.com/vi/{vid}/{name}.jpg', headers={'User-Agent': 'reytek1201-build'}), timeout=15) as r:
                data = r.read()
            if len(data) > 2000:
                os.makedirs(os.path.dirname(path), exist_ok=True)
                with open(path, 'wb') as f: f.write(data)
                return True
        except Exception:
            continue
    return False

def prepare(rows):
    """Rows with a usable YouTube link, each with its id and where its poster comes from."""
    out = []
    for r in rows:
        vid = video_id(r.get('youtube_url'))
        if not vid:
            print(f'videos: skipped {r.get("slug")}, no YouTube id in its link')
            continue
        r = dict(r, id=vid)
        custom = (r.get('poster') or [{}])[0].get('src')
        if custom: r['poster_src'], r['poster_abs'] = custom, custom
        elif _save_poster(vid): r['poster_src'], r['poster_abs'] = f'img/video/{vid}.jpg', f'{SITE}/img/video/{vid}.jpg'
        else: r['poster_src'] = r['poster_abs'] = f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg'
        out.append(r)
    return out

def by_release(rows):
    return {r['release_title'].strip().lower(): r for r in rows}

def watch_button(row, title):
    return (f'<button class="rel-watch" type="button" data-watch="{e(row["slug"])}" aria-label="Watch the video for {e(title)}">'
            f'{CAM}<span>Watch</span></button>')

def _year(r):
    return (r.get('published_on') or r.get('created_at') or '')[:4]

def _ld(r):
    d = {'@context': 'https://schema.org', '@type': 'VideoObject', 'name': f'{r["title"]} · Reytek',
         'description': r.get('blurb') or f'{KINDS.get(r["kind"], "Video")} for {r["release_title"]} by Reytek.',
         'thumbnailUrl': r['poster_abs'], 'embedUrl': f'https://www.youtube.com/embed/{r["id"]}',
         'contentUrl': f'https://www.youtube.com/watch?v={r["id"]}',
         'publisher': {'@type': 'Person', 'name': 'Reytek', 'url': SITE + '/'}}
    when = (r.get('published_on') or r.get('created_at') or '')[:10]
    if when: d['uploadDate'] = when
    return d

def render(rows):
    """The Listen / Watch switch and the screen. Empty when there are no videos."""
    if not rows: return ''
    picks = ''
    if len(rows) > 1:
        picks = ('<ul class="watch-pick" aria-label="Videos">' + ''.join(
            f'<li><button type="button" data-pick="{e(r["slug"])}" aria-pressed="false">{e(r["title"])}</button></li>' for r in rows) + '</ul>')
    panes = ''
    for r in rows:
        meta = ' · '.join(x for x in (KINDS.get(r['kind'], ''), _year(r), r.get('duration') or '') if x)
        panes += (f'<figure class="watch-pane" id="watch-{e(r["slug"])}" data-slug="{e(r["slug"])}" data-vid="{e(r["id"])}" data-release="{e(r["release_title"])}" data-title="{e(r["title"])}" hidden>'
                  f'<div class="watch-frame"><button class="film-play" type="button" aria-label="Play the video: {e(r["title"])}">'
                  f'<img src="{e(r["poster_src"])}" alt="" width="1280" height="720" loading="lazy" decoding="async" onerror="this.remove()">'
                  '<span class="film-btn" aria-hidden="true"></span></button></div>'
                  f'<figcaption><div class="watch-meta"><b>{e(r["title"])}</b><span>{e(meta)}</span></div>'
                  + (f'<p>{e(r["blurb"])}</p>' if r.get('blurb') else '')
                  + f'<a class="txt-link" href="https://www.youtube.com/watch?v={e(r["id"])}" target="_blank" rel="noopener noreferrer">Watch on YouTube ↗</a></figcaption></figure>')
    ld = '\n'.join('<script type="application/ld+json">' + json.dumps(_ld(r), ensure_ascii=False).replace('</', '<\\/') + '</script>' for r in rows)
    return ('<div class="watch" id="watch">'
            f'<div class="watch-bar"><div class="watch-mode" role="group" aria-label="Listen or watch">'
            f'<button class="wm on" type="button" data-mode="listen" aria-pressed="true">Listen</button>'
            f'<button class="wm" type="button" data-mode="watch" aria-pressed="false">{CAM}Watch</button></div>{picks}</div>'
            f'<div class="watch-screen" hidden>{panes}</div>{ld}</div>')
