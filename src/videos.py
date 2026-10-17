"""Music videos, from the `videos` table (edited in the back office), shown on Reytek Vision (/vision/).

YouTube hosts the video. Vision is the site's TV: every video is a channel (CH.01, CH.02 ...) with a poster
on standby, a channel guide and custom controls. The YouTube player is only created when someone tunes in.
The Music page links to it: a slim Reytek Vision link above the turntable, and a Watch button on each release
that has a video. The poster is YouTube's thumbnail, saved to img/video/ at build time so the page doesn't
call out; the saved copy is reused when YouTube can't be reached (local builds).
"""
import html, json, os, re, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
COLS = 'slug,sort,release_title,title,kind,youtube_url,published_on,duration,blurb,poster,created_at,tagline,color'
SITE = 'https://www.reytek1201.com'
KINDS = {'music-video': 'Music video', 'visualizer': 'Visualizer', 'live': 'Live', 'making-of': 'Making of'}
e = lambda s: html.escape(str(s if s is not None else ''), True)
UP = '__UP__'   # replaced with the right number of ../ for the page the link sits on

def svg(path, cls=''):
    return f'<svg{" class=" + chr(34) + cls + chr(34) if cls else ""} viewBox="0 0 16 16" aria-hidden="true">{path}</svg>'
CAM = svg('<path d="M1.5 4.5a1.5 1.5 0 0 1 1.5-1.5h6a1.5 1.5 0 0 1 1.5 1.5v1.6l3.2-1.9a.5.5 0 0 1 .8.4v6.8a.5.5 0 0 1-.8.4L10.5 9.9v1.6A1.5 1.5 0 0 1 9 13H3a1.5 1.5 0 0 1-1.5-1.5z"/>', 'i-cam')
I_PLAY = svg('<path d="M4 2.5v11l9-5.5z"/>', 'i-play')
I_PAUSE = svg('<path d="M3.5 2.5h3v11h-3zM9.5 2.5h3v11h-3z"/>', 'i-pause')
I_VOL = svg('<path d="M2 6v4h3l4 3V3L5 6zM11 5.5a3.5 3.5 0 0 1 0 5l-.8-.8a2.4 2.4 0 0 0 0-3.4z"/>', 'i-vol')
I_MUTE = svg('<path d="M2 6v4h3l4 3V3L5 6zM11 6l3.5 4M14.5 6L11 10" fill="none" stroke="currentColor" stroke-width="1.4" stroke-linecap="round"/>', 'i-mute')
I_FS = svg('<path d="M2 6V2h4v1.4H3.4V6zM10 2h4v4h-1.4V3.4H10zM14 10v4h-4v-1.4h2.6V10zM6 14H2v-4h1.4v2.6H6z"/>')
I_UP = svg('<path d="M3 10l5-5 5 5-1.1 1.1L8 7.2l-3.9 3.9z"/>')
I_DOWN = svg('<path d="M3 6l5 5 5-5-1.1-1.1L8 8.8 4.1 4.9z"/>')

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

def watch_link(row, title):
    """A Watch button on a release row: opens that video's channel on Reytek Vision."""
    return (f'<a class="rel-watch" href="{UP}vision/#{e(row["slug"])}" aria-label="Watch the video for {e(title)} on Reytek Vision">'
            f'{CAM}<span>Watch</span></a>')

def music_link(rows):
    """A slim link to Reytek Vision above the turntable on the Music page. Empty when there are no videos."""
    if not rows: return ''
    n = len(rows)
    return (f'<a class="vis-link" href="{UP}vision/"><i class="vdot" aria-hidden="true"></i><span>›</span><b>Reytek Vision</b>'
            f'<span class="vis-n">{n} channel{"s" if n != 1 else ""}</span><span class="tag">Watch →</span></a>')

def _year(r):
    return (r.get('published_on') or r.get('created_at') or '')[:4]

def _rgb(hexcolor):
    m = re.fullmatch(r'#([0-9a-f]{2})([0-9a-f]{2})([0-9a-f]{2})', hexcolor or '', re.I)
    return ','.join(str(int(g, 16)) for g in m.groups()) if m else None

def _ld(r):
    d = {'@context': 'https://schema.org', '@type': 'VideoObject', 'name': f'{r["title"]} · Reytek',
         'description': r.get('blurb') or f'{KINDS.get(r["kind"], "Video")} for {r["release_title"]} by Reytek.',
         'thumbnailUrl': r['poster_abs'], 'embedUrl': f'https://www.youtube.com/embed/{r["id"]}',
         'contentUrl': f'https://www.youtube.com/watch?v={r["id"]}',
         'publisher': {'@type': 'Person', 'name': 'Reytek', 'url': SITE + '/'}}
    when = (r.get('published_on') or r.get('created_at') or '')[:10]
    if when: d['uploadDate'] = when
    return d

def render_vision(rows):
    """The TV, its channel guide and the data the page script reads."""
    if not rows:
        return '<section class="vis" aria-label="Reytek Vision"><div class="page-in"><p class="lede">No channels on air yet.</p></div></section>'
    chans, items = [], ''
    for i, r in enumerate(rows):
        n = f'{i+1:02d}'
        rgb = _rgb(r.get('color'))
        tag = r.get('tagline') or KINDS.get(r['kind'], 'Video')
        meta = ' · '.join(x for x in (KINDS.get(r['kind'], ''), _year(r), r.get('duration') or '') if x)
        chans.append({'slug': r['slug'], 'id': r['id'], 'n': n, 'title': r['title'], 'tagline': tag, 'meta': meta, 'blurb': r.get('blurb') or '',
                      'rgb': rgb, 'poster': r['poster_src'], 'release': r['release_title']})
        items += (f'<li class="vg-chan{" on" if i == 0 else ""}" style="--cc:{rgb or "var(--sig-rgb)"}"><button type="button" data-ch="{i}" '
                  f'aria-label="Channel {n}: {e(r["title"])}. {e(tag)}"><span class="n">CH.{n}</span>'
                  f'<span class="name"><b>{e(r["title"])}</b><i>{e(tag)}</i></span><span class="tick"></span></button></li>')
    c = chans[0]
    first = rows[0]
    ld = '\n'.join('<script type="application/ld+json">' + json.dumps(_ld(r), ensure_ascii=False).replace('</', '<\\/') + '</script>' for r in rows)
    data = json.dumps(chans, ensure_ascii=False).replace('</', '<\\/')
    nch = len(rows)
    return f'''  <section class="vis" id="vision" aria-label="Reytek Vision">
    <div class="page-in vis-in">
      <div class="tv" id="tv" data-state="standby"{' style="--vc:' + c['rgb'] + '"' if c['rgb'] else ''}>
        <div class="tv-set" id="tvSet">
          <div class="tv-top"><span class="tv-brand">Reytek Vision</span><span class="tv-meter" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></span><span class="tv-tally"><i aria-hidden="true"></i><span id="tvTally">Standby</span></span></div>
          <div class="tv-screen" id="tvScreen">
            <div class="tv-video" id="tvVideo"></div>
            <button class="tv-standby" id="tvStandby" type="button" aria-label="Tune in to channel {c['n']}: {e(c['title'])}">
              <img id="tvPoster" src="{e(c['poster'])}" alt="" width="1280" height="720" decoding="async" onerror="this.remove()">
              <span class="tv-cue"><b id="tvCue">CH.{c['n']}</b><small>Press to tune in</small></span>
              <span class="film-btn" aria-hidden="true"></span>
            </button>
            <div class="tv-osd" id="tvOsd" aria-hidden="true"></div>
            <div class="tv-static" id="tvStatic" aria-hidden="true"></div>
            <div class="tv-end" id="tvEnd" hidden>
              <p class="tv-end-k" id="tvEndK"></p>
              <p class="tv-end-t" id="tvEndT"></p>
              <div class="tv-end-b"><button class="btn primary" type="button" id="tvEndGo"></button><button class="btn" type="button" id="tvEndStay" hidden>Stay here</button><a class="btn" href="{UP}music/#deck">Back to the turntable</a></div>
            </div>
          </div>
          <div class="tv-ctl" role="group" aria-label="Player controls">
            <button class="tv-btn" type="button" id="tvDown" aria-label="Previous channel">{I_DOWN}</button>
            <button class="tv-btn main" type="button" id="tvPlay" aria-pressed="false" aria-label="Play">{I_PLAY}{I_PAUSE}</button>
            <button class="tv-btn" type="button" id="tvUp" aria-label="Next channel">{I_UP}</button>
            <input class="tv-seek" id="tvSeek" type="range" min="0" max="1000" value="0" step="1" aria-label="Seek" disabled>
            <span class="tv-time" id="tvTime">0:00</span>
            <button class="tv-btn" type="button" id="tvMute" aria-pressed="false" aria-label="Mute" disabled>{I_VOL}{I_MUTE}</button>
            <button class="tv-btn" type="button" id="tvFull" aria-pressed="false" aria-label="Full screen">{I_FS}</button>
          </div>
        </div>
        <div class="tv-now">
          <p class="tv-now-k" id="tvNowK">CH.{c['n']}{' · ' + e(c['meta']) if c['meta'] else ''}</p>
          <h2 id="tvNowT">{e(c['title'])}</h2>
          <p id="tvNowB">{e(c['blurb'])}</p>
          <a class="txt-link" id="tvNowLink" href="https://www.youtube.com/watch?v={e(c['id'])}" target="_blank" rel="noopener noreferrer">Watch on YouTube ↗</a>
        </div>
        <p class="vis-sr" id="tvLive" aria-live="polite"></p>
      </div>
      <aside class="vg-wrap" aria-label="Channel guide">
        <div class="vg-head"><span>› Channel guide</span><span>{nch:02d} channel{'s' if nch != 1 else ''}</span></div>
        <ol class="vg" id="vg">{items}</ol>
      </aside>
    </div>
    {ld}
    <script type="application/json" id="visData">{data}</script>
  </section>
'''
