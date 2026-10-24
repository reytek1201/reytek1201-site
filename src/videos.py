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
I_POWER = svg('<path d="M8 1.5v6M4.4 3.8a5.2 5.2 0 1 0 7.2 0" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round"/>')
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

# The set: a chunky chassis drawn in SVG (viewBox 0 0 1200 840): a big screen on top and a pad deck beneath it. Traces are drawn three times: dim base, glow, traveling pulse.
TRACES = ['M116,120 V250 L136,270 V420 L122,434 V580', 'M136,120 V170 L144,178', 'M130,640 V560 L142,548',
          'M210,32 H420 L436,48 H640', 'M680,32 H900 L916,48 H990', 'M236,700 H520 L536,690 H760 L776,700 H980', 'M300,708 H460',
          'M1072,130 V300 L1064,308 V560', 'M1078,340 V420', 'M860,708 H1010 L1024,694']
NODES = [(116, 120), (122, 580), (640, 48), (990, 48), (980, 700), (1064, 560)]

def _traces(cls, pulse=False, boot=False):
    out = f'<g class="trg {cls}">'
    for i, d in enumerate(TRACES):
        out += f'<path d="{d}" pathLength="100"' + (f' style="--i:{i}"' if boot else '') + '></path>'
    if not pulse:
        out += ''.join(f'<circle cx="{x}" cy="{y}" r="2.6"></circle>' for x, y in NODES)
    return out + '</g>'

CHASSIS = 'M170,12 H1030 L1100,82 V650 L1030,720 H170 L100,650 V82 Z'
BEZEL = 'M215,40 H985 L1005,60 V506 L985,526 H215 L195,506 V60 Z'
DECK = 'M215,544 H985 L1005,564 V666 L985,686 H215 L195,666 V564 Z'
SHELL = (f'<path d="{CHASSIS}" fill="url(#tvsShell)" stroke="#000" stroke-width="3"></path>'
         '<path d="M182,26 H1018 L1084,92 V640 L1018,706 H182 L116,640 V92 Z" fill="none" stroke="#fff" stroke-opacity=".07" stroke-width="1.5"></path>'
         '<path d="M100,82 L116,92 M170,12 L182,26 M1030,12 L1018,26 M1100,82 L1084,92 M1100,650 L1084,640 M1030,720 L1018,706 M170,720 L182,706 M100,650 L116,640" stroke="#fff" stroke-opacity=".12" stroke-width="1.5" fill="none"></path>')

ART = ('<svg class="tv-art" viewBox="0 0 1200 840" width="1200" height="840" aria-hidden="true" focusable="false"><defs>'
       '<linearGradient id="tvsShell" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1b212c"></stop><stop offset="1" stop-color="#080a0f"></stop></linearGradient>'
       '<linearGradient id="tvsSheen" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".14"></stop><stop offset=".45" stop-color="#fff" stop-opacity=".03"></stop><stop offset="1" stop-color="#fff" stop-opacity="0"></stop></linearGradient>'
       '<linearGradient id="tvsMetal" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#363d4b"></stop><stop offset="1" stop-color="#0d1015"></stop></linearGradient>'
       '<radialGradient id="tvsFloor" cx=".5" cy=".5" r=".5"><stop offset="0" class="tvs-accent" stop-opacity=".5"></stop><stop offset="1" class="tvs-accent" stop-opacity="0"></stop></radialGradient>'
       '<linearGradient id="tvsFade" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".5"></stop><stop offset="1" stop-color="#fff" stop-opacity="0"></stop></linearGradient>'
       '<mask id="tvsRefl" maskUnits="userSpaceOnUse" x="0" y="790" width="1200" height="50"><rect x="0" y="790" width="1200" height="50" fill="url(#tvsFade)"></rect></mask>'
       '<filter id="tvsGlow" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="3.5"></feGaussianBlur></filter></defs>'
       '<ellipse class="tv-floor" cx="600" cy="796" rx="470" ry="40" fill="url(#tvsFloor)"></ellipse>'
       '<g mask="url(#tvsRefl)"><g transform="translate(0,1580) scale(1,-1)" opacity=".7">' + SHELL + _traces('tr-refl') + '</g></g>'
       '<path d="M470,716 H730 L762,758 H438 Z" fill="url(#tvsMetal)" stroke="#000" stroke-width="2"></path>'
       '<path d="M380,758 H820 L862,782 H338 Z" fill="url(#tvsMetal)" stroke="#000" stroke-width="2"></path>'
       '<path class="tv-edge" d="M338,782 H862" stroke-width="2"></path><path class="tv-edge dim" d="M440,758 H760" stroke-width="1.5"></path>'
       + SHELL
       + '<g filter="url(#tvsGlow)" class="tr-glow">' + _traces('tr-g') + '</g>'
       + '<g class="tr-base">' + _traces('tr-b', boot=True) + '</g>'
       + '<g class="tr-pulse">' + _traces('tr-p', pulse=True) + '</g>'
       + f'<path d="{BEZEL}" fill="#04060a" stroke="#000" stroke-width="3"></path>'
       + f'<path d="{BEZEL} M220,76 V494 H980 V76 Z" fill="url(#tvsSheen)" fill-rule="evenodd"></path>'
       '<path d="M219,48 H981 L997,64 V502 L981,518 H219 L203,502 V64 Z" fill="none" stroke="#fff" stroke-opacity=".09" stroke-width="1.5"></path>'
       + f'<path class="tv-edge lit" d="{BEZEL}" stroke-width="1.5" fill="none"></path>'
       + f'<path d="{DECK}" fill="#06080c" stroke="#000" stroke-width="3"></path>'
       + f'<path d="{DECK}" fill="url(#tvsSheen)" opacity=".5"></path>'
       '<path class="tv-edge lit" d="M219,548 H981 L1001,568 V662 L981,682 H219 L199,662 V568 Z" stroke-width="1.5" fill="none"></path>'
       '<path class="tv-edge dim" d="M703,556 V674" stroke-width="1.5"></path></svg>')

PTRACES = ['M40,10 H120 L130,19 H210', 'M238,10 H318', 'M30,306 H90 L98,298 H190', 'M240,306 H328', 'M4,60 V110 L8,114 V200',
           'M354,60 V130 L350,134 V210', 'M4,236 V280 L12,288', 'M354,240 V280 L346,288']
PNODES = [(40, 10), (318, 10), (30, 306), (328, 306), (4, 60), (354, 60)]

def _ptraces(cls, pulse=False, boot=False):
    out = f'<g class="trg {cls}">'
    for i, d in enumerate(PTRACES):
        out += f'<path d="{d}" pathLength="100"' + (f' style="--i:{i}"' if boot else '') + '></path>'
    if not pulse:
        out += ''.join(f'<circle cx="{x}" cy="{y}" r="2.2"></circle>' for x, y in PNODES)
    return out + '</g>'

PART = ('<svg class="tv-art-m" viewBox="0 0 358 316" aria-hidden="true" focusable="false"><defs>'
        '<linearGradient id="tvmShell" x1="0" y1="0" x2="0" y2="1"><stop offset="0" stop-color="#1e2531"></stop><stop offset="1" stop-color="#080a0f"></stop></linearGradient>'
        '<linearGradient id="tvmSheen" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="#fff" stop-opacity=".13"></stop><stop offset=".5" stop-color="#fff" stop-opacity=".02"></stop><stop offset="1" stop-color="#fff" stop-opacity="0"></stop></linearGradient>'
        '<filter id="tvmGlow" x="-10%" y="-10%" width="120%" height="120%"><feGaussianBlur stdDeviation="2.5"></feGaussianBlur></filter></defs>'
        '<path d="M26,0 H332 L358,26 V290 L332,316 H26 L0,290 V26 Z" fill="url(#tvmShell)" stroke="#000" stroke-width="2.5"></path>'
        '<path d="M26,0 H332 L358,26 V150 L0,60 V26 Z" fill="url(#tvmSheen)"></path>'
        '<path d="M30,5 H328 L353,28 V288 L328,311 H30 L5,288 V28 Z" fill="none" stroke="#fff" stroke-opacity=".08" stroke-width="1"></path>'
        '<path d="M0,26 L5,28 M26,0 L30,5 M332,0 L328,5 M358,26 L353,28 M358,290 L353,288 M332,316 L328,311 M26,316 L30,311 M0,290 L5,288" stroke="#fff" stroke-opacity=".14" stroke-width="1.2" fill="none"></path>'
        '<path d="M14,300 H24 M334,300 H344 M150,12 H208" stroke="#000" stroke-opacity=".55" stroke-width="2" fill="none"></path>'
        + '<g filter="url(#tvmGlow)" class="tr-glow">' + _ptraces('tr-g') + '</g>'
        + '<g class="tr-base">' + _ptraces('tr-b', boot=True) + '</g>'
        + '<g class="tr-pulse">' + _ptraces('tr-p', pulse=True) + '</g>'
        + '<path d="M12,24 H346 V228 H12 Z" fill="#04060a" stroke="#000" stroke-width="2"></path>'
        '<path d="M12,24 H346 V228 H12 Z" class="tv-edge lit" fill="none" stroke-width="1"></path>'
        '<path d="M12,262 H346" stroke="#000" stroke-opacity=".5" stroke-width="2"></path>'
        '</svg>')

def _bars(n=5):
    return '<span class="tv-meter" aria-hidden="true">' + '<i></i>' * n + '</span>'

def _btn(act, label, icon, cls='tv-btn', extra=''):
    return f'<button class="{cls}" type="button" data-act="{act}" aria-label="{label}"{extra}>{icon}</button>'

PAD_N = 8   # the deck has eight pads; with more channels the deck pages (vision.js) and the guide lists them all

def _pads(chans, cls):
    out = ''
    for k in range(PAD_N):
        if k < len(chans):
            c = chans[k]
            out += (f'<button type="button" class="tv-pad {"on" if k == 0 else "lit"}" data-pad="{k}" style="--pc:{c["rgb"] or "var(--sig-rgb)"}" '
                    f'aria-label="Channel {c["n"]}: {e(c["title"])}"><b><span>{c["n"]}</span><i></i></b><small>{e(c["title"])}</small></button>')
        else:
            out += (f'<button type="button" class="tv-pad off" data-pad="{k}" disabled aria-label="Channel {k+1:02d}, empty">'
                    f'<b><span>{k+1:02d}</span><i></i></b><small>Open slot</small></button>')
    return f'<div class="{cls}" role="group" aria-label="Channels">{out}</div>'

def render_vision(rows, ld_on=True):
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
    ld = '' if not ld_on else '\n'.join('<script type="application/ld+json">' + json.dumps(_ld(r), ensure_ascii=False).replace('</', '<\\/') + '</script>' for r in rows)
    data = json.dumps(chans, ensure_ascii=False).replace('</', '<\\/')
    nch = len(rows)
    seek = '<input class="tv-seek" data-seek type="range" min="0" max="1000" value="0" step="1" aria-label="Seek" disabled>'
    playb = lambda cls: f'<button class="{cls}" type="button" data-act="play" aria-pressed="false" aria-label="Play">{I_PLAY}{I_PAUSE}</button>'
    muteb = lambda cls: f'<button class="{cls}" type="button" data-act="mute" aria-pressed="false" aria-label="Mute" disabled>{I_VOL}{I_MUTE}</button>'
    fullb = lambda cls: _btn('full', 'Full screen', I_FS, cls, ' aria-pressed="false"')
    power = lambda cls: f'<button class="{cls}" type="button" data-act="power" aria-pressed="true" aria-label="Power off">{I_POWER}</button>'
    html_ = f"""  <section class="vis" id="vision" aria-label="Reytek Vision">
    <div class="page-in vis-in">
      <div class="tv" id="tv" data-state="standby" data-power="on" data-vis="1"{' style="--vc:' + c['rgb'] + '"' if c['rgb'] else ''}>
        <div class="tv-fit" id="tvFit"><div class="tv-rig" id="tvRig"><div class="tv-tilt" id="tvTilt"><div class="tv-body">
          {ART}{PART}
          <div class="tv-top"><span class="tv-brand">Reytek Vision</span><span class="tv-tally"><i aria-hidden="true"></i><span id="tvTally">Standby</span></span></div>
          <div class="tv-set" id="tvSet">
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
              <div class="tv-fsbar" id="tvFsBar">{playb('tv-btn')}{muteb('tv-btn')}<span class="tv-time" data-time>0:00</span>{_btn('full', 'Exit full screen', I_FS, 'tv-btn', ' aria-pressed="true"')}</div>
              <div class="tv-off" aria-hidden="true"></div>
            </div>
          </div>
          <div class="tv-foot"><span id="tvFoot">CH.{c['n']} · {e(c['title'])}</span>{_bars()}</div>
          {_pads(chans, 'tv-pads')}
          <div class="tv-console" role="group" aria-label="Set controls">
            <div class="tc-row">{power('tc-pwr')}<div class="tc-read"><span class="k">Channel</span><b id="tvChNum">{c['n']}</b></div>{_bars(4)}</div>
            <div class="tc-row"><span class="tc-t" data-time>0:00</span>{seek}</div>
            <div class="tc-btns">{_btn('down', 'Previous channel', I_DOWN, 'tv-btn sm')}{playb('tv-btn sm main')}{_btn('up', 'Next channel', I_UP, 'tv-btn sm')}{muteb('tv-btn sm')}{fullb('tv-btn sm')}</div>
          </div>
          <div class="tv-ctl" role="group" aria-label="Player controls">
            {power('tv-btn pwr')}{_btn('down', 'Previous channel', I_DOWN)}{playb('tv-btn main')}{_btn('up', 'Next channel', I_UP)}
            {seek}<span class="tv-time" data-time>0:00</span>{muteb('tv-btn')}{fullb('tv-btn')}
          </div>
        </div></div></div></div>
        {_pads(chans, 'tv-pads-m')}
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
"""
    return html_


def render_home(rows):
    """The homepage's Watch side: the same set as Reytek Vision (built by render_vision, run by vision.js), beside the turntable.
    Returns (tabs, pane); both empty when there are no videos."""
    if not rows: return '', ''
    tabs = ('<div class="stage-tabs" role="tablist" aria-label="Listen or watch">'
            '<button type="button" role="tab" id="tabListen" aria-selected="true" aria-controls="paneListen">Listen</button>'
            '<button type="button" role="tab" id="tabWatch" aria-selected="false" aria-controls="paneWatch" tabindex="-1">Watch</button></div>')
    pane = ('<div class="stage-pane vwatch" id="paneWatch" role="tabpanel" aria-labelledby="tabWatch" hidden>\n'
            + render_vision(rows, ld_on=False) + '      </div>')
    return tabs, pane
