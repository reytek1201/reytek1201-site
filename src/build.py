"""
Build reytek1201.com from the source in src/.

    python3 src/build.py            # writes index.html, assets/ and the page folders at the repo root
    python3 src/build.py --preview  # also writes single-file previews to src/_preview/ (for sharing)

Edit the files in src/, never the built files at the repo root: they are overwritten on every build.
"""
import hashlib, json, os, re, shutil, sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
os.chdir(HERE)
SRC = 'site.src.html'
OUT = ROOT
sys.path.insert(0, HERE)
from seo import reps as SEO_REPS
s = open(SRC).read()
s = s.replace('__PORTRAIT__', open('portrait.b64').read().strip()).replace('__ANYBODY__', open('anybody.b64').read().strip())

# 1. CSS: the single <style> block -> assets/site.css
m = re.search(r'<style>\n?(.*?)</style>', s, re.S)
css = m.group(1)
assert s.count('<style>') == 1
s = s[:m.start()] + '__CSS__' + s[m.end():]

# 2. inline scripts -> assets/*.js (in order). Root resolver goes first.
names = ['theme', 'boot', 'main', 'lightbox']
blocks = list(re.finditer(r'<script>\n?(.*?)</script>', s, re.S))
assert len(blocks) == len(names), len(blocks)
js = {}
for name, b in zip(reversed(names), reversed(blocks)):
    js[name] = b.group(1)
    s = s[:b.start()] + f'__JS_{name}__' + s[b.end():]

ROOT_SHIM = ("/* site root, resolved from this script's own URL so pages at any depth find shared files */\n"
             "window.RT_ROOT = new URL('../', document.currentScript.src).href;\n"
             "window.rtUrl = p => new URL(p, window.RT_ROOT).href;\n")
js['theme'] = ROOT_SHIM + js['theme']
# asset paths inside main.js resolve from the site root, not the current page URL
main = js['main']
a = "const WORKLET_URL = 'deck-worklet.js?v=3';"
assert main.count(a) == 1
main = main.replace(a, "const WORKLET_URL = rtUrl('deck-worklet.js?v=3');")
i = main.index('const TRACKS = ')
j = main.index('\n', i)
main = main[:j+1] + "TRACKS.forEach(t => ['file', 'cover', 'label'].forEach(k => { if (t[k]) t[k] = rtUrl(t[k]); }));\n" + main[j+1:]
k = main.index('// ---- four lanes')
js['lanes'] = main[k:]
main = main[:k]
js['main'] = main

os.makedirs(OUT + '/assets', exist_ok=True)
def put(name, text):
    open(f'{OUT}/assets/{name}', 'w').write(text)
    return f'assets/{name}?v=' + hashlib.md5(text.encode()).hexdigest()[:8]

s = s.replace('__CSS__', f'<link rel="stylesheet" href="{put("site.css", css)}">')
for n in names:
    s = s.replace(f'__JS_{n}__', f'<script src="{put(n + ".js", js[n])}"></script>')
ASSET = {'site.css': f'assets/site.css?v=' + hashlib.md5(css.encode()).hexdigest()[:8]}
for n in names: ASSET[n + '.js'] = f'assets/{n}.js?v=' + hashlib.md5(js[n].encode()).hexdigest()[:8]
ASSET['lanes.js'] = put('lanes.js', js['lanes'])
js['shell'] = open('js/shell.js').read()
ASSET['shell.js'] = put('shell.js', js['shell'])
js['pages'] = open('js/pages.js').read()
ASSET['pages.js'] = put('pages.js', js['pages'])

# phone channel guide: the bottom strip and the full-screen guide. Same markup on the homepage and every inner page.
N_TRACKS = len(json.loads(re.search(r'const TRACKS = (\[.*?\]);\n', js['main']).group(1)))
WORDS = 'zero one two three four five six seven eight nine ten eleven twelve'.split()
GUIDE = [  # number, name, href, one line, lane color
    ('00', 'Signal', '', 'Home · the vortex and the turntable', '237,235,230'),
    ('01', 'Origin', 'origin/', '1976 to now, on four lanes', '237,235,230'),
    ('02', 'Music', 'music/', f'Side A · {WORDS[N_TRACKS] if N_TRACKS < len(WORDS) else N_TRACKS} tracks', 'var(--c1)'),
    ('03', 'Projects', 'projects/', 'KeyMacro, SlidePress, FunkHarp', 'var(--c2)'),
    ('04', 'Gaming', 'gaming/', 'POE Source · Dec 11', 'var(--c3)'),
    ('05', 'Art', 'art/', 'Covers and experiments in light', 'var(--c0)'),
]
GUIDE_THEMES = [('Cyan', '34,211,238'), ('Magenta', '255,61,184'), ('Amber', '255,159,28')]

def guide(slug, up):
    n, name = next((c[0], c[1]) for c in GUIDE if c[2] == slug)
    rows = ''
    for num, nm, href, sub, cc in GUIDE:
        on = href == slug
        dest = (up or './') if href == '' else up + href
        label = f'Channel {num}, {nm}: {sub}' + (', on air' if on else '')
        rows += (f'<li class="cg-chan{" on" if on else ""}" style="--cc:{cc}"><a href="{dest}" aria-label="{label}"' + (' aria-current="page"' if on else '')
                 + f'><span class="n">CH.{num}</span><span class="name"><b>{nm}</b><i>{sub}</i></span><span class="tick">{"On air" if on else ""}</span></a></li>')
    themes = ('<div class="cg-themes" role="radiogroup" aria-label="Color theme">'
              + ''.join(f'<button type="button" role="radio" data-t="{i}" aria-label="{t} theme" style="--c:{c}"><i></i></button>' for i, (t, c) in enumerate(GUIDE_THEMES))
              + '</div>')
    sound = '<button class="cg-snd" type="button" id="guideSound" aria-pressed="false">Sound off</button>' if slug == '' else ''
    return (f'<div class="cg" id="guide" role="dialog" aria-modal="true" aria-label="Channel guide">'
            f'<div class="cg-head"><span>› Channel guide</span><span>{len(GUIDE):02d} channels</span></div>'
            f'<ul class="cg-list">{rows}</ul>'
            f'<div class="cg-foot"><div class="cg-ch" id="guideCh"></div><div class="cg-ctl">{themes}{sound}</div></div></div>\n'
            '<div class="cg-static" id="guideStatic" aria-hidden="true"></div>\n'
            f'<div class="cg-strip"><div class="cg-readout" id="readout"><span class="cg-tag"><small>Now on</small><strong><span class="num">CH.{n}</span> · {name}</strong></span>'
            '<span class="cg-meter" aria-hidden="true"><i></i><i></i><i></i><i></i><i></i></span></div>'
            '<button class="cg-key" type="button" id="guideKey" aria-expanded="false" aria-controls="guide" aria-label="Open the channel guide">'
            '<svg class="lines" viewBox="0 0 24 24" aria-hidden="true"><path d="M4 7h16"/><path d="M4 12h10"/><path d="M4 17h13"/><circle cx="19" cy="12" r="1.2" fill="currentColor" stroke="none"/></svg>'
            '<svg class="x" viewBox="0 0 24 24" aria-hidden="true"><path d="M6 6l12 12M18 6L6 18"/></svg></button></div>')

assert s.count('__GUIDE__') == 1
s = s.replace('__GUIDE__', guide('', ''))

# 3. page document + SEO/GA head, same replacements as build.py
SK = '<!doctype html>\n<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">\n'
i = s.index('<canvas id="gl"')
page = SK + s[:i] + '</head><body>\n' + s[i:] + '\n</body></html>\n'
for a, b in SEO_REPS:
    assert page.count(a) == 1, a
    page = page.replace(a, b)
open(f'{OUT}/index.html', 'w').write(page)

print('built', {k: len(v) for k, v in js.items()}, 'css', len(css), 'html', len(page))

# ---------- inner pages ----------
SRC_TXT = open(SRC).read()
def grab(start, end, txt=SRC_TXT):
    i = txt.index(start); j = txt.index(end, i) + len(end); return txt[i:j]
GA = next(b for a, b in SEO_REPS if 'googletagmanager' in b).split('<title>')[0]
FONTS = grab('<link rel="preconnect" href="https://fonts.googleapis.com">', 'display=swap" rel="stylesheet">')
THEMES = grab('<div class="themes" id="themes"', '</div>')
RAIL = grab('<nav class="rail" id="rail"', '</nav>')
FOOTER = grab('<footer>', '</footer>')
LB = grab('<dialog class="lb" id="lb"', '</dialog>')
NAV = [('Signal', '', ''), ('Origin', 'origin/', ''), ('Music', 'music/', ''), ('Projects', 'projects/', ''), ('Gaming', 'gaming/', ''), ('Art', 'art/', '')]

def inner_page(slug, title, desc, content, scripts, label):
    up = '../' * slug.count('/')
    nav = ''.join((f'<a href="./" aria-current="page" class="on">' if href == slug else f'<a href="{up}{href}{h}"' + (' data-go="0"' if name == 'Signal' else '') + '>') + f'{name}</a>' for name, href, h in NAV)
    url = f'https://www.reytek1201.com/{slug}'
    head = (SK + GA + f'<title>{title}</title>\n<meta name="description" content="{desc}">\n<link rel="canonical" href="{url}">\n'
            '<meta name="robots" content="index,follow,max-image-preview:large">\n<meta name="theme-color" content="#050608">\n'
            f'<meta property="og:site_name" content="REYTEK">\n<meta property="og:title" content="{title}">\n<meta property="og:description" content="{desc}">\n'
            f'<meta property="og:type" content="website">\n<meta property="og:url" content="{url}">\n<meta property="og:image" content="https://www.reytek1201.com/og.jpg">\n'
            '<meta name="twitter:card" content="summary_large_image">\n<meta name="twitter:site" content="@reytek1201">\n'
            '<link rel="icon" type="image/png" sizes="32x32" href="/favicon-32.png">\n<link rel="apple-touch-icon" href="/apple-touch-icon.png">\n'
            + FONTS + f'\n<link rel="stylesheet" href="{up}{ASSET["site.css"]}">\n</head><body>\n')
    content = content.replace('src="img/', f'src="{up}img/').replace('src="covers/', f'src="{up}covers/')
    extra = ''
    mark = '<div id="lyrics"'
    if mark in content:
        i = content.index(mark)
        extra = content[i:].strip() + '\n'
        content = content[:i].rstrip() + '\n'
    body = ('<div id="grain" aria-hidden="true"></div>\n<div class="frame" id="frame" aria-hidden="true"><i></i><i class="on"></i><i></i><i></i></div>\n'
            '<div class="topscrim" aria-hidden="true"></div><div class="botscrim" aria-hidden="true"></div>\n'
            f'<div class="hud hud-tl"><a href="{up}" aria-label="REYTEK home"><span class="dot"></span><b>REYTEK</b><span>/ {label}</span></a></div>\n'
            f'<nav class="hud hud-tr chapters" aria-label="Pages">{nav}</nav>\n<div class="hud hud-bl">Hub v0.1 · {label}</div>\n'
            + RAIL + '\n' + guide(slug, up) + '\n<div class="hud hud-br">' + THEMES + '</div>\n\n<main>\n'
            + content + '</main>\n\n' + extra + FOOTER + '\n\n<div id="cur" aria-hidden="true"></div><div id="dot" aria-hidden="true"></div>\n'
            + LB + '\n' + ''.join(f'<script src="{up}{ASSET[n]}"></script>\n' for n in scripts) + '</body></html>\n')
    html = head + body
    os.makedirs(f'{OUT}/{slug}', exist_ok=True)
    open(f'{OUT}/{slug}index.html', 'w').write(html)
    return html

lanes_html = open('pages/origin-timeline.html').read()
TR = json.loads(re.search(r'const TRACKS = (\[.*?\]);\n', SRC_TXT).group(1))
fmt = lambda x: f'{int(x)//60}:{int(x)%60:02d}'
def wave(peaks, n=120):
    k = len(peaks) / n; bars = []
    for i in range(n):
        v = max(peaks[int(i*k):max(int((i+1)*k), int(i*k)+1)]); h = max(1.2, v * 22)
        bars.append(f'M{i+0.15:.2f} {12-h/2:.2f}h0.7v{h:.2f}h-0.7z')
    return ''.join(bars)
PLAY = '<svg class="i-play" viewBox="0 0 16 16" aria-hidden="true"><path d="M4 2.5v11l9-5.5z"/></svg><svg class="i-pause" viewBox="0 0 16 16" aria-hidden="true"><path d="M3.5 2.5h3v11h-3zM9.5 2.5h3v11h-3z"/></svg>'
LYR = {}
if os.path.isdir('lyrics'):
    for name in sorted(os.listdir('lyrics')):
        if name.endswith('.json'):
            data = json.load(open(os.path.join('lyrics', name)))
            data['beats'] = next(t['beats'] for t in TR if t['title'] == data['title'])
            LYR[data['title']] = data
rel = []
for i, t in enumerate(TR):
    w = wave(t['peaks']); title = t['title']
    label = t.get('label')
    lyr_btn = f'<button class="rel-lyrics" type="button" aria-expanded="false" aria-controls="lyrics" aria-label="Lyrics for {title}">Lyrics</button>' if title in LYR else ''
    rel.append(f'        <li class="rel" data-src="{t["file"]}" data-title="{title}" data-dur="{t["dur"]}">'
               f'<span class="rel-disc{" has-label" if label else ""}"><span class="rel-vinyl" aria-hidden="true"></span><img class="rel-cover" src="{t["cover"]}" alt="Cover art for {title}" width="640" height="640" loading="lazy" decoding="async">'
               + (f'<img class="rel-label" src="{label}" alt="" width="1024" height="1024">' if label else '') + '</span>'
               f'<div class="rel-info"><div class="rel-top"><b>{title}</b>' + ('<span class="rel-new">NEW</span>' if t.get('isNew') else '') + lyr_btn + '</div>'
               f'<span class="rel-meta">A{i+1} · {round(t["bpm"])} BPM · {fmt(t["dur"])}</span>'
               f'<div class="rel-wave" title="Seek"><svg viewBox="0 0 120 24" preserveAspectRatio="none" aria-hidden="true"><path d="{w}"/></svg><svg class="hi" viewBox="0 0 120 24" preserveAspectRatio="none" aria-hidden="true"><path d="{w}"/></svg></div></div>'
               f'<span class="rel-t">{fmt(t["dur"])}</span><button class="rel-play" type="button" aria-pressed="false" aria-label="Play {title}">{PLAY}</button></li>')
gal = []
for t in TR:
    gal.append(f'        <li class="gal"><figure><img src="{t["cover"]}" alt="Cover art for {t["title"]}" width="640" height="640" loading="lazy" decoding="async"><figcaption>{t["title"]} · cover</figcaption></figure></li>')
for t in TR:
    if t.get('label'):
        gal.append(f'        <li class="gal"><figure><img src="{t["label"]}" alt="Record label art for {t["title"]}" width="1024" height="1024" loading="lazy" decoding="async"><figcaption>{t["title"]} · label</figcaption></figure></li>')
P = lambda n: open(f'pages/{n}.html').read()
SCR = ['theme.js', 'shell.js', 'pages.js', 'lightbox.js']
PAGES = {
  'origin/': ('Origin · REYTEK', "From Puerto Rico to Fort Lauderdale's rave scene and three decades in kitchens: Reytek's story across four lanes, kitchen, sound, code and play.",
              P('origin').replace('__LANES__', lanes_html), ['theme.js', 'shell.js', 'lanes.js', 'lightbox.js'], 'Origin'),
  'music/': ('Music · REYTEK', 'Electronic music from Fort Lauderdale, shaped by the early-90s rave scene. Play every Reytek release, from Threshold of Sound to The Light Was Plain.',
             P('music').replace('__RELEASES__', '\n'.join(rel)).replace('__COUNT__', str(len(TR))).replace('__LYRICS_JSON__', json.dumps(LYR, ensure_ascii=False)), SCR, 'Music'),
  'projects/': ('Projects · REYTEK', 'Apps built out of necessity: KeyMacro, a meal planner with a kitchen brain, SlidePress for social posting, the FunkHarp site and this hub.',
                P('projects'), SCR, 'Projects'),
  'gaming/': ('Gaming · REYTEK', 'From his dad\'s arcades in Puerto Rico to POE Source, a Path of Exile 2 companion launching with POE2 1.0 on December 11.',
              P('gaming'), SCR, 'Gaming'),
  'art/': ('Art · REYTEK', 'Visual work, covers and experiments in light by Reytek. The cover and label art for every release so far.',
           P('art').replace('__COVERS__', '\n'.join(gal)), SCR, 'Art'),
}
built = {slug: inner_page(slug, *v) for slug, v in PAGES.items()}

# previews for the claude.ai artifact: inline everything, root = the page's own folder depth
def inline(html, depth):
    html = html.split('<!-- Google tag (gtag.js) -->')[0] + html.split('</script>', 2)[2] if '<!-- Google tag' in html else html
    html = re.sub(r'<link rel="stylesheet" href="(?:\.\./)*assets/site\.css\?v=\w+">', lambda m: '<style>\n' + css + '</style>', html)
    def _i(m):
        t = js[m.group(1)].replace("window.RT_ROOT = new URL('../', document.currentScript.src).href;", f"window.RT_ROOT = new URL('{'../' * depth or './'}', document.baseURI).href;")
        return '<script>\n' + t + '</script>'
    html = re.sub(r'<script src="(?:\.\./)*assets/(\w+)\.js\?v=\w+"></script>', _i, html)
    assert 'assets/' not in html
    # directory links don't resolve in the preview host: point at index.html
    html = html.replace('href="./"', 'href="index.html"')
    html = re.sub(r'href="((?:\.\./)*)(origin|music|projects|gaming|art)/(#[\w-]*)?"', lambda m: f'href="{m.group(1)}{m.group(2)}/index.html{m.group(3) or ""}"', html)
    html = re.sub(r'href="((?:\.\./)+)(#[\w-]*)?"', lambda m: f'href="{m.group(1)}index.html{m.group(2) or ""}"', html)
    return html
if '--preview' in sys.argv:
    PV = os.path.join(HERE, '_preview')
    shutil.rmtree(PV, ignore_errors=True); os.makedirs(PV)
    open(f'{PV}/index.html', 'w').write(inline(page, 0))
    for slug, html in built.items():
        os.makedirs(f'{PV}/{slug}', exist_ok=True)
        open(f'{PV}/{slug}index.html', 'w').write(inline(html, slug.count('/')))
    print('previews in src/_preview/ (copy img, audio, covers next to them to view)')
print('pages: /,', ', '.join('/' + k for k in built))
