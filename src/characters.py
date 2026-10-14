"""The Gaming page's characters, from the `characters` table (edited in the back office).

Renders the "Now playing" strip and Player Select: a row of character slots and a sheet for each.
A character with a POE Source share code gets a full sheet (gear doll, item tooltips, skills, stats)
from POE Source's saved_builds, fetched at build time like the site's own content, with a saved copy.
"""
import html, json, math, os, re, urllib.parse, urllib.request

COLS = 'slug,sort,game,name,status,class_line,blurb,poe_slug,planner_url,guide_url,guide_credit,videos,portrait'
MARK = '__NOW_PLAYING__'
SELECT_MARK = '__PLAYER_SELECT__'

POE_API = 'https://rtikgugqicnmrgtseoir.supabase.co'
POE_KEY = 'sb_publishable_wNwBeL2L6NRvVN_DtpGz0Q_TnYHHEXX'   # POE Source publishable key: read-only, public builds only
POE_SITE = 'https://www.poe2source.com'
HERE = os.path.dirname(os.path.abspath(__file__))
EXT = 'target="_blank" rel="noopener noreferrer"'

e = lambda s: html.escape(str(s if s is not None else ''), True)

# ---------- data ----------

def trim(row):
    """Keep what the sheet shows: the active gear set, the skill groups and the stats (not the passive tree)."""
    s = dict(row.get('summary') or {})
    s.pop('tree', None)
    gear = s.get('gear') or {}
    sets = gear.get('itemSets') or []
    active = str(gear.get('activeItemSetId') or '')
    keep = [x for x in sets if str(x.get('id')) == active] or sets[:1] or [{'id': '1', 'title': '', 'items': gear.get('items') or []}]
    s['gear'] = {'activeItemSetId': active, 'itemSets': keep}
    sk = s.get('skills') or {}
    s['skills'] = {'activeSkillSetId': sk.get('activeSkillSetId'), 'groups': [
        {k: g.get(k) for k in ('isMain', 'enabled', 'label', 'slot', 'source')}
        | {'gems': [{k: m.get(k) for k in ('name', 'level', 'enabled', 'gemId')} for m in g.get('gems') or []]}
        for g in sk.get('groups') or []]}
    return {k: row.get(k) for k in ('share_slug', 'label', 'video_url', 'updated_at')} | {'summary': s}

def load_builds(rows):
    """POE Source builds for the characters that have a share code, keyed by code."""
    codes = sorted({r['poe_slug'] for r in rows if r.get('poe_slug')})
    snapshot = os.path.join(HERE, 'content', 'poe_builds.json')
    if not codes: return {}, 'nothing to fetch'
    url = f'{POE_API}/rest/v1/saved_builds?' + urllib.parse.urlencode({
        'select': 'share_slug,label,video_url,updated_at,summary', 'share_slug': f'in.({",".join(codes)})'})
    try:
        req = urllib.request.Request(url, headers={'apikey': POE_KEY, 'Authorization': f'Bearer {POE_KEY}'})
        with urllib.request.urlopen(req, timeout=20) as r:
            data = [trim(x) for x in json.loads(r.read().decode())]
        if not data: raise ValueError('no public builds for ' + ', '.join(codes))
        with open(snapshot, 'w') as f: json.dump(data, f, ensure_ascii=False, indent=1); f.write('\n')
        src = 'POE Source'
    except Exception as ex:
        # A showcase, not core content: never fail the build over it, use the last saved copy.
        with open(snapshot) as f: data = json.load(f)
        src = f'saved copy ({ex.__class__.__name__})'
    return {b['share_slug']: b for b in data}, src

# ---------- PoB item lines -> tooltip ----------

META = re.compile(r'^(Crafted|Prefix|Suffix|LevelReq|Implicits|Quality|Sockets|Rune|Charm Slots|Unique ID|Item Level|Radius|'
                  r'Limited to|Selected Variant|Variant|League|Source|Corrupted|Mirrored|Catalyst|CatalystQuality|Talisman Tier|'
                  r'Has Alt Variant\w*|Armour|Evasion|Energy Shield|Ward|Spirit|Rarity|Requires Class|ArmourBasePercentile|'
                  r'EvasionBasePercentile|EnergyShieldBasePercentile|WardBasePercentile|Split|Fractured|Synthesised): ?(.*)$')
PROPS = ('Armour', 'Evasion', 'Energy Shield', 'Ward', 'Spirit')

def _num(x):
    if abs(x - round(x)) < 1e-9 or abs(x) >= 10: return str(int(math.floor(x + 0.5)))
    return f'{x:.1f}'.rstrip('0').rstrip('.')

def mod_text(line):
    """'{tags:x}{range:0.5}+(10-15) to Strength' -> '+13 to Strength' (PoB rolls a range at its {range} position)."""
    m = re.search(r'\{range:([\d.]+)\}', line)
    rng = float(m.group(1)) if m else 0.5
    text = re.sub(r'\{[^}]*\}', '', line)
    return re.sub(r'\((-?[\d.]+)-(-?[\d.]+)\)',
                  lambda g: _num(float(g.group(1)) + (float(g.group(2)) - float(g.group(1))) * rng), text).strip()

def parse_item(it):
    rarity = (it.get('rarity') or 'NORMAL').lower()
    name, base = it.get('displayName') or '', it.get('baseType') or ''
    if not name or name == 'New Item': name, base = base or 'Item', ''
    if base == name: base = ''
    props, req, corrupted, quality, n_impl, mods = [], 0, False, 0, 0, []
    for line in it.get('lines') or []:
        m = META.match(line)
        if m:
            k, v = m.group(1), m.group(2).strip()
            try:
                if k in PROPS and v not in ('0', ''): props.append((k, v))
                elif k == 'LevelReq': req = int(float(v or 0))
                elif k == 'Quality': quality = int(float(v or 0))
                elif k == 'Implicits': n_impl = int(v or 0)
                elif k == 'Corrupted': corrupted = v.lower() == 'true'
            except ValueError: pass
            continue
        mods.append(line)
    head, rest = mods[:n_impl], mods[n_impl:]
    return {
        'rarity': rarity, 'name': name, 'base': base, 'slot': it.get('slot') or '',
        'props': ([('Quality', f'+{quality}%')] if quality else []) + props,
        'req': req,
        'enchants': [mod_text(x) for x in head if '{enchant}' in x],
        'implicits': [mod_text(x) for x in head if '{enchant}' not in x],
        'mods': [mod_text(x) for x in rest],
        'corrupted': corrupted,
        'art': f'{POE_SITE}/icons/poe2/{re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")}.png' if rarity == 'unique' else '',
    }

# where each slot sits on the doll (CSS grid areas), like the in-game equipment screen
AREA = {'Weapon 1': 'w1', 'Helmet': 'hm', 'Weapon 2': 'w2', 'Amulet': 'am', 'Ring 1': 'r1', 'Body Armour': 'bd',
        'Ring 2': 'r2', 'Gloves': 'gl', 'Belt': 'be', 'Boots': 'bt'}
BELT_ROW = ['Flask 1', 'Charm 1', 'Charm 2', 'Charm 3', 'Flask 2']
SLOT_LABEL = {'Weapon 1': 'Weapon', 'Weapon 2': 'Off hand', 'Body Armour': 'Body', 'Ring 1': 'Ring', 'Ring 2': 'Ring'}

def tooltip(i, tid, shown):
    sec = []
    if i['props'] or i['req']:
        sec.append(''.join(f'<p class="it-prop"><span>{e(k)}:</span> {e(v)}</p>' for k, v in i['props'])
                   + (f'<p class="it-req">Requires Level <b>{i["req"]}</b></p>' if i['req'] else ''))
    if i['enchants']: sec.append(''.join(f'<p class="it-ench">{e(x)}</p>' for x in i['enchants']))
    if i['implicits']: sec.append(''.join(f'<p class="it-mod">{e(x)}</p>' for x in i['implicits']))
    if i['mods']: sec.append(''.join(f'<p class="it-mod">{e(x)}</p>' for x in i['mods']))
    if i['corrupted']: sec.append('<p class="it-cor">Corrupted</p>')
    head = f'<b>{e(i["name"])}</b>' + (f'<span>{e(i["base"])}</span>' if i['base'] else '')
    body = ''.join(f'<div class="it-sec">{s}</div>' for s in sec)
    return (f'<div class="it r-{i["rarity"]}" id="{tid}"{"" if shown else " hidden"}>'
            f'<div class="it-head">{head}</div><div class="it-body">{body}</div></div>')

def fmt_date(iso):
    try:
        y, m, d = (int(x) for x in iso.split('-'))
        return f'{"Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()[m - 1]} {d}, {y}'
    except Exception: return iso

def doll(slug, b):
    s = b['summary']
    gset = ((s.get('gear') or {}).get('itemSets') or [{}])[0]
    items = {it.get('slot'): parse_item(it) for it in gset.get('items') or []}
    first = next((k for k in list(AREA) + BELT_ROW if k in items), None)
    tips = []
    def cell(slot, area=None):
        i = items.get(slot)
        label = SLOT_LABEL.get(slot, slot)
        style = f' style="grid-area:{area}"' if area else ''
        sm = ' sm' if not area else ' one' if area in ('am', 'r1', 'r2') else ''
        if not i: return f'<span class="slot empty{sm}"{style} aria-hidden="true"><i>{e(label)}</i></span>'
        tid = f'it-{slug}-{re.sub(r"[^a-z0-9]+", "-", slot.lower())}'
        tips.append(tooltip(i, tid, slot == first))
        art = f'<img src="{e(i["art"])}" alt="" loading="lazy" decoding="async" onerror="this.remove()">' if i['art'] else ''
        return (f'<button class="slot r-{i["rarity"]}{sm}"{style} type="button" aria-controls="{tid}" aria-pressed="{"true" if slot == first else "false"}" '
                f'aria-label="{e(label)}: {e(i["name"])}, {i["rarity"]}">{art}<i>{e(i["name"])}</i></button>')
    cells = ''.join(cell(k, a) for k, a in AREA.items())
    small = ''.join(cell(k) for k in BELT_ROW if k in items)
    title, saved = gset.get('title') or '', (b.get('updated_at') or '')[:10]
    stamp = ' · '.join(x for x in (f'Gear set: {e(title)}' if title else '', f'saved {fmt_date(saved)}' if saved else '') if x)
    return (f'<div class="doll-wrap"><div class="doll" role="group" aria-label="Equipped gear. Pick a slot to read the item.">{cells}</div>'
            + (f'<div class="doll-belt">{small}</div>' if small else '')
            + (f'<p class="doll-stamp">{stamp}</p>' if stamp else '') + '</div>'
            + f'<div class="tips" aria-live="polite">{"".join(tips)}</div>')

def skills(s):
    out = []
    for g in (s.get('skills') or {}).get('groups') or []:
        gems = [m for m in g.get('gems') or [] if m.get('name') and m.get('enabled', True)]
        if not gems or g.get('enabled') is False: continue
        act = [m for m in gems if 'SupportGem' not in (m.get('gemId') or '')]
        sup = [m for m in gems if 'SupportGem' in (m.get('gemId') or '')]
        if not act: continue
        src = g.get('source') or ''
        frm = f'<span class="sk-from">from the {e(src.split(",")[-1].strip())}</span>' if src.startswith('Item:') else ''
        chain = ''.join(f'<li class="gem act"><b>{e(m["name"])}</b><i>{e(m.get("level"))}</i></li>' for m in act[:1])
        chain += ''.join(f'<li class="gem sup">{e(m["name"])}</li>' for m in sup)
        out.append(f'<li class="sk{" main" if g.get("isMain") else ""}"><ol class="chain">{chain}</ol>{frm}</li>')
    return f'<div class="sk-wrap"><h4>Skills</h4><ol class="sks">{"".join(out)}</ol></div>' if out else ''

def stats(s):
    d, o, a = s.get('defense') or {}, s.get('offense') or {}, s.get('attributes') or {}
    vit = [(k, d.get(f), c) for k, f, c in (('Life', 'life', '#e0524a'), ('Energy shield', 'energyShield', '#8fc8ff'),
                                             ('Mana', 'mana', '#5a7bff'), ('Spirit', 'spirit', '#e9dfb8')) if d.get(f)]
    res = [('Fire', 'fire', d.get('fireResist')), ('Cold', 'cold', d.get('coldResist')),
           ('Lightning', 'light', d.get('lightningResist')), ('Chaos', 'chaos', d.get('chaosResist'))]
    bars = ''.join(
        f'<li class="res {c}{" neg" if (v or 0) < 0 else ""}" style="--v:{max(0, min(int(v or 0), 75)) / 75:.3f}">'
        f'<span>{k}</span><b>{int(v or 0)}%</b><i aria-hidden="true"></i></li>' for k, c, v in res)
    dps, main = o.get('dps'), (s.get('mainSkill') or {}).get('name')
    attrs = ''.join(f'<span><b>{int(a[f])}</b>{k}</span>' for k, f in (('Str', 'strength'), ('Dex', 'dexterity'), ('Int', 'intelligence')) if a.get(f) is not None)
    vit_html = ''.join(f'<div style="--vc:{c}"><dt>{k}</dt><dd>{int(v):,}</dd></div>' for k, v, c in vit)
    return ('<div class="st"><h4>Stats</h4>'
            + (f'<p class="st-dps"><b>{int(round(dps)):,}</b><span>DPS{" with " + e(main) if main else ""}</span></p>' if dps else '')
            + (f'<dl class="st-vit">{vit_html}</dl>' if vit else '')
            + f'<ul class="st-res" aria-label="Resistances, capped at 75%">{bars}</ul>'
            + (f'<p class="st-attr">{attrs}</p>' if attrs else '') + '</div>')

# ---------- Player Select ----------

GAME_CODE = {'Path of Exile 2': 'PoE2', 'Path of Exile': 'PoE', 'Last Epoch': 'LE'}
STATE = {'live': 'Live', 'retired': 'Retired', 'locked': 'Locked'}

def code(game):
    return GAME_CODE.get(game) or ''.join(w[0] for w in re.findall(r'[A-Za-z0-9]+', game or '?') if w.lower() not in ('of', 'the'))[:4]

def videos(r):
    out = []
    for line in (r.get('videos') or '').splitlines():
        if not line.strip(): continue
        label, _, ref = line.rpartition('|') if '|' in line else ('', '', line)
        m = re.search(r'(?:v=|youtu\.be/|shorts/|embed/)([\w-]{11})', ref) or re.fullmatch(r'\s*([\w-]{11})\s*', ref)
        if m: out.append((label.strip() or 'Watch', m.group(1)))
    return out

def portrait(r):
    pic = (r.get('portrait') or [{}])[0]
    if pic.get('src'): return pic['src']
    v = videos(r)
    return f'https://i.ytimg.com/vi/{v[0][1]}/oar2.jpg' if v else ''

LOCK = ('<svg class="ps-lock" viewBox="0 0 24 24" aria-hidden="true"><rect x="5" y="10.5" width="14" height="10" rx="2"/>'
        '<path d="M8 10.5V8a4 4 0 0 1 8 0v2.5"/></svg>')

def slot(r, selected):
    st = r.get('status') or 'retired'
    locked = st == 'locked'
    pic = '' if locked else portrait(r)
    img = f'<img src="{e(pic)}" alt="" loading="lazy" decoding="async" onerror="this.remove()">' if pic else ''
    mark = f'<span class="ps-code" aria-hidden="true">{"???" if locked else e(code(r.get("game")))}</span>'
    name = 'Locked' if locked else r['name']
    return (f'<button class="ps-slot is-{st}{" has-pic" if pic else ""}" type="button" role="tab" id="pick-{e(r["slug"])}" data-slug="{e(r["slug"])}" '
            f'aria-selected="{"true" if selected else "false"}" aria-controls="sheet-{e(r["slug"])}" tabindex="{0 if selected else -1}">'
            f'<span class="ps-pic">{img}{mark}{LOCK if locked else ""}</span>'
            f'<span class="ps-cap"><span class="ps-game">{e(r.get("game"))}</span><b class="ps-name">{e(name)}</b>'
            f'<span class="ps-state">{STATE.get(st, st)}</span></span></button>')

def sheet(r, b, selected):
    st = r.get('status') or 'retired'
    open_ = (f'<article class="sheet is-{st}" role="tabpanel" id="sheet-{e(r["slug"])}" aria-labelledby="pick-{e(r["slug"])}" tabindex="0"'
             + ('' if selected else ' hidden') + '>')
    if st == 'locked':
        return (open_ + f'<div class="sh-locked">{LOCK}<h3>{e(r.get("game"))}</h3><p>Locked for now.</p></div></article>')
    s = (b or {}).get('summary') or {}
    lvl = s.get('level')
    cls = r.get('class_line') or ' · '.join(x for x in (s.get('className'), s.get('ascendClassName')) if x)
    meta = ''.join(f'<span>{x}</span>' for x in (e(r.get('game')), e(cls), f'{int(s["passiveCount"])} passives' if s.get('passiveCount') else '') if x)
    head = ('<header class="sh-head">' + (f'<p class="sh-lvl"><span>Level</span><b>{int(lvl)}</b></p>' if lvl else '')
            + f'<div class="sh-id"><h3>{e(r["name"])}</h3><p class="sh-meta">{meta}</p></div></header>')
    links = []
    if r.get('poe_slug'):
        links.append(f'<a class="btn primary" href="{POE_SITE}/b/{e(r["poe_slug"])}?utm_source=reytek1201&amp;utm_medium=referral&amp;utm_campaign=gaming_sheet" {EXT}>Open the full build on POE Source ↗</a>')
    elif r.get('planner_url'):
        links.append(f'<a class="btn primary" href="{e(r["planner_url"])}" {EXT}>Open the build planner ↗</a>')
    if r.get('slug') == 'kaelen': links.append('<a class="btn" href="../art/#kaelen">See the series in Art</a>')
    credit = ''
    if r.get('guide_url'):
        credit = f'<p class="sh-credit"><a class="txt-link" href="{e(r["guide_url"])}" {EXT}>{e(r.get("guide_credit") or "Read the guide")} ↗</a></p>'
    elif r.get('guide_credit'):
        credit = f'<p class="sh-credit">{e(r["guide_credit"])}</p>'
    eps = ''.join(
        f'<li class="ep"><div class="ep-frame" data-yt="{e(v)}" data-title="{e(r["name"] + ", " + lab)}"><button class="film-play" type="button" aria-label="Play {e(lab)}">'
        f'<img src="https://i.ytimg.com/vi/{e(v)}/oar2.jpg" alt="" loading="lazy" decoding="async" onerror="this.remove()"><span class="film-btn" aria-hidden="true"></span></button></div>'
        f'<span>{e(lab)}</span></li>' for lab, v in videos(r))
    about = ((f'<p class="sh-blurb">{e(r["blurb"])}</p>' if r.get('blurb') else '') + credit
             + (f'<div class="page-cta">{"".join(links)}</div>' if links else ''))
    eps_html = f'<div class="sh-eps"><h4>Episodes</h4><ol>{eps}</ol></div>' if eps else ''
    if b:
        body = f'<div class="sh-grid">{doll(r["slug"], b)}{stats(s)}</div>{skills(s)}<div class="sh-about">{about}</div>{eps_html}'
    else:
        body = f'<div class="sh-plain"><div class="sh-about">{about}</div>{eps_html}</div>'
    return open_ + head + body + '</article>'

def player_select(rows, builds):
    if not rows: return ''
    sel = (next((r for r in rows if r.get('status') == 'live'), None) or rows[0])['slug']
    slots = ''.join(slot(r, r['slug'] == sel) for r in rows)
    sheets = ''.join(sheet(r, builds.get(r.get('poe_slug') or ''), r['slug'] == sel) for r in rows)
    return ('  <section class="ps" id="player-select" aria-labelledby="psTitle">\n    <div class="page-in">\n'
            '      <div class="sec-head"><span class="lbl" id="psTitle">› Player select</span><span class="ps-hint" aria-hidden="true">← → to choose</span></div>\n'
            f'      <div class="ps-row" role="tablist" aria-labelledby="psTitle">{slots}<span class="ps-cursor" aria-hidden="true">1P</span></div>\n'
            f'      <div class="ps-screen">{sheets}</div>\n    </div>\n  </section>\n')

# ---------- Now playing ----------

def now_playing(rows):
    """The first Live character by sort order, or None."""
    return next((r for r in rows if r.get('status') == 'live'), None)

def card(r):
    pic = (r.get('portrait') or [{}])[0]
    art = (f'<div class="gnp-art"><img src="{e(pic.get("src"))}" alt="{e(pic.get("alt") or r["name"])}" width="{int(pic.get("w") or 480)}" '
           f'height="{int(pic.get("h") or 480)}" loading="lazy" decoding="async"></div>') if pic.get('src') else ''
    meta = ' · '.join(e(x) for x in (r.get('game'), r.get('class_line')) if x)
    links = []
    if r.get('planner_url'):
        links.append(f'<a class="btn primary" href="{e(r["planner_url"])}" {EXT}>Open the build ↗</a>')
    elif r.get('poe_slug'):
        links.append(f'<a class="btn primary" href="{POE_SITE}/b/{e(r["poe_slug"])}" {EXT}>Open the build on POE Source ↗</a>')
    links.append(f'<a class="btn" href="#pick-{e(r["slug"])}" data-pick="{e(r["slug"])}">Character sheet</a>')
    credit = e(r.get('guide_credit'))
    if r.get('guide_url'):
        credit = f'<a class="txt-link" href="{e(r["guide_url"])}" {EXT}>{credit or "Read the guide"} ↗</a>'
    return (f'  <section class="gnp" aria-labelledby="gnpTitle">\n    <div class="page-in">\n'
            f'      <div class="gnp-card{" has-art" if art else ""}">\n        {art}\n        <div class="gnp-body">\n'
            f'          <div class="proj-meta"><span class="proj-status live">Now playing</span><span>{meta}</span></div>\n'
            f'          <h2 id="gnpTitle">{e(r["name"])}</h2>\n'
            + (f'          <p>{e(r["blurb"])}</p>\n' if r.get('blurb') else '')
            + (f'          <p class="gnp-credit">{credit}</p>\n' if credit else '')
            + f'          <div class="page-cta">{"".join(links)}</div>\n'
            + '        </div>\n      </div>\n    </div>\n  </section>\n')

def render(template, rows, builds=None):
    assert template.count(MARK) == 1, MARK
    assert template.count(SELECT_MARK) == 1, SELECT_MARK
    r = now_playing(rows)
    page = template.replace(MARK + '\n', card(r) if r else '', 1)
    return page.replace(SELECT_MARK + '\n', player_select(rows, builds or {}), 1)
