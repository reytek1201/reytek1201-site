"""The Gaming page's characters, from the `characters` table (edited in the back office).

Renders the "Now playing" strip and Player Select: a row of character slots and a sheet for each.
A character with a POE Source share code gets a full sheet drawn like POE Source's build page: the gear
doll with item art, item tooltips, and skill gems, for the loadout picked in the back office. The build
is fetched from POE Source at build time, with a saved copy. Item, rune and gem art comes from POE Source's
public icon storage, looked up in src/content/poe2_icons.json (refresh it with src/tools/sync_poe_icons.py).
"""
import html, json, math, os, re, unicodedata, urllib.parse, urllib.request

import lastepoch
COLS = 'slug,sort,game,name,status,class_line,blurb,poe_slug,poe_loadout,level,loadout,planner_url,guide_url,guide_credit,videos,portrait'

def _seed(slug):
    """Last Epoch build data shipped with the repo, used only while the database row's loadout is empty."""
    f = os.path.join(HERE, 'content', f'le_loadout_{slug.split("-", 1)[-1].replace("-", "_")}.json')
    try:
        with open(f) as fh: return fh.read()
    except OSError: return None

MARK = '__NOW_PLAYING__'
SELECT_MARK = '__PLAYER_SELECT__'

POE_API = 'https://rtikgugqicnmrgtseoir.supabase.co'
POE_KEY = 'sb_publishable_wNwBeL2L6NRvVN_DtpGz0Q_TnYHHEXX'   # POE Source publishable key: read-only, public builds only
POE_SITE = 'https://www.poe2source.com'
ICON_BASE = f'{POE_API}/storage/v1/object/public/gear-icons/'
HERE = os.path.dirname(os.path.abspath(__file__))
EXT = 'target="_blank" rel="noopener noreferrer"'

e = lambda s: html.escape(str(s if s is not None else ''), True)

# ---------- data ----------

def _match(sets, title):
    t = (title or '').strip().lower()
    return next((x for x in sets if t and (x.get('title') or '').strip().lower() == t), None)

def trim(row, loadout=''):
    """Keep what the sheet shows, for one loadout: its gear set, its skill set and its passive count.

    Stats (life, resists, DPS) and level only exist for the build's active set, so `statsMatch` says
    whether they belong to the loadout shown."""
    s = row.get('summary') or {}
    gear = s.get('gear') or {}
    sets, active = gear.get('itemSets') or [], str(gear.get('activeItemSetId') or '')
    gs = (_match(sets, loadout) or next((x for x in sets if str(x.get('id')) == active), None)
          or (sets[0] if sets else {'id': active, 'title': '', 'items': gear.get('items') or []}))
    title = gs.get('title') or ''
    sk = s.get('skills') or {}
    ss = _match(sk.get('skillSets') or [], title) or {'title': '', 'groups': sk.get('groups') or []}
    tree = s.get('tree') or {}
    spec = _match(tree.get('specs') or [], title)
    out = {k: s.get(k) for k in ('game', 'level', 'className', 'ascendClassName', 'mainSkill', 'attributes', 'offense', 'defense')}
    out |= {
        'passiveCount': len(spec.get('nodes') or []) if spec else s.get('passiveCount'),
        'activeItemSetId': active,
        'statsMatch': str(gs.get('id')) == active,
        'gear': {'id': gs.get('id'), 'title': title, 'items': gs.get('items') or []},
        'skills': {'title': ss.get('title'), 'groups': [
            {k: g.get(k) for k in ('isMain', 'enabled', 'label', 'slot', 'source')}
            | {'gems': [{k: m.get(k) for k in ('name', 'gemId', 'level', 'quality', 'enabled')} for m in g.get('gems') or []]}
            for g in ss.get('groups') or []]},
    }
    return {k: row.get(k) for k in ('share_slug', 'label', 'video_url', 'updated_at')} | {'loadout': loadout or '', 'summary': out}

def _key(code, loadout):
    return f'{code}|{(loadout or "").strip().lower()}'

def load_builds(rows):
    """POE Source builds for the characters with a share code, keyed by code + loadout."""
    wanted = {_key(r['poe_slug'], r.get('poe_loadout')): (r['poe_slug'], r.get('poe_loadout') or '') for r in rows if r.get('poe_slug')}
    snapshot = os.path.join(HERE, 'content', 'poe_builds.json')
    if not wanted: return {}, 'nothing to fetch'
    codes = sorted({c for c, _ in wanted.values()})
    url = f'{POE_API}/rest/v1/saved_builds?' + urllib.parse.urlencode({
        'select': 'share_slug,label,video_url,updated_at,summary', 'share_slug': f'in.({",".join(codes)})'})
    try:
        req = urllib.request.Request(url, headers={'apikey': POE_KEY, 'Authorization': f'Bearer {POE_KEY}'})
        with urllib.request.urlopen(req, timeout=20) as r:
            raw = {x['share_slug']: x for x in json.loads(r.read().decode())}
        data = [trim(raw[c], lo) for c, lo in wanted.values() if c in raw]
        if not data: raise ValueError('no public builds for ' + ', '.join(codes))
        with open(snapshot, 'w') as f: json.dump(data, f, ensure_ascii=False, indent=1); f.write('\n')
        src = 'POE Source'
    except Exception as ex:
        # A showcase, not core content: never fail the build over it, use the last saved copy.
        with open(snapshot) as f: data = json.load(f)
        src = f'saved copy ({ex.__class__.__name__})'
    return {_key(b['share_slug'], b.get('loadout')): b for b in data}, src

# ---------- icons (POE Source's lookup) ----------

_ICONS = None
def icons():
    global _ICONS
    if _ICONS is None:
        try:
            with open(os.path.join(HERE, 'content', 'poe2_icons.json')) as f: _ICONS = json.load(f)
        except OSError: _ICONS = {'byName': {}, 'byMeta': {}, 'gems': {}, 'bases': []}
    return _ICONS

def norm(name):
    name = unicodedata.normalize('NFKD', (name or '').lower()).replace('’', "'").replace('`', "'")
    return re.sub(r'\s+', ' ', name).strip()

def _infer_base(name):
    n = norm(name)
    return next((b for b in icons()['bases'] if len(b) >= 5 and b in n), None) if n else None

def icon_url(path):
    return ICON_BASE + path if path else ''

def item_icon(it):
    by = icons()['byName']
    disp, base = it.get('displayName') or '', it.get('baseType') or ''
    if (it.get('rarity') or '').upper() in ('UNIQUE', 'RELIC'): names = [disp, base, _infer_base(disp)]
    else: names = [base, disp, _infer_base(disp), _infer_base(base)]
    return icon_url(next((by[norm(n)] for n in names if n and norm(n) in by), ''))

def named_icon(name):
    return icon_url(icons()['byName'].get(norm(name), ''))

def gem_info(g):
    ic = icons()
    meta = g.get('gemId') or ''
    path = ic['byMeta'].get(meta) or ic['byName'].get(norm(g.get('name'))) or ''
    color, tags, desc = ic['gems'].get(meta) or ['Colorless', '', '']
    return icon_url(path), color, tags, desc

# ---------- item lines -> tooltip (POE Source's rules, plus rolled ranges) ----------

DROP = re.compile(r'^(Crafted|Prefix|Suffix|Unique ID|Implicits|Catalyst|CatalystQuality|Fractured|Synthesised|Split|Has Alt Variant|'
                  r'New Variant|Variant|Selected Variant|Selected Alt Variant|Has Multiple Variants|Allow Duplicate Variants|League|'
                  r'Source|Upgrade|Charm Slots|Rune|Sockets|Radius|Limited to|Corrupted|Mirrored|\w+BasePercentile):', re.I)
PROPERTY = re.compile(r'^(Quality|Armour|Energy Shield|Evasion Rating|Evasion|Ward|Physical Damage|Elemental Damage|Chaos Damage|'
                      r'Critical (Strike|Hit) Chance|Attacks per Second|Weapon Range|Chance to Block|Block chance|Spirit|Item Level|'
                      r'Duration|Uses|Maximum Charges|Charges per Use|Recovery Amount):\s*(.+)$', re.I)
TONE = (('desecrated', 'desecrated'), ('fractured', 'fractured'), ('crafted', 'crafted'))

def _num(x):
    if abs(x - round(x)) < 1e-9 or abs(x) >= 10: return str(int(math.floor(x + 0.5)))
    return f'{x:.1f}'.rstrip('0').rstrip('.')

def mod_text(line):
    """'{tags:x}{range:0.5}+(10-15) to Strength' -> '+13 to Strength' (PoB rolls a range at its {range} position)."""
    m = re.search(r'\{range:([\d.]+)\}', line)
    rng = float(m.group(1)) if m else 0.5
    text = re.sub(r'\s+', ' ', re.sub(r'\{[^}]*\}', '', line)).strip()
    return re.sub(r'\((-?[\d.]+)-(-?[\d.]+)\)',
                  lambda g: _num(float(g.group(1)) + (float(g.group(2)) - float(g.group(1))) * rng), text)

def parse_item(it):
    rarity = (it.get('rarity') or 'NORMAL').lower()
    name, base = it.get('displayName') or '', it.get('baseType') or ''
    if not name or name.lower() == 'new item': name, base = base or 'Item', ''
    if base.lower() == name.lower(): base = ''
    props, req, n_impl, body, corrupted = [], 0, 0, [], False
    for raw in it.get('lines') or []:
        text = re.sub(r'\{[^}]*\}', '', raw).strip()
        if not text: continue
        if text.lower() == 'corrupted' or text.lower().startswith('corrupted:'): corrupted = corrupted or 'true' in text.lower() or text.lower() == 'corrupted'
        lr = re.match(r'^(LevelReq|Level Req):\s*(\d+)', text, re.I)
        if lr: req = int(lr.group(2)); continue
        im = re.match(r'^Implicits:\s*(\d+)', text, re.I)
        if im: n_impl = int(im.group(1)); continue
        if DROP.match(text) or text in ('None',): continue
        p = PROPERTY.match(text)
        if p:
            k, v = p.group(1), p.group(3).strip()
            if k.lower() == 'quality':
                q = int(float(v.rstrip('%+') or 0))
                if q: props.append(('Quality', f'+{q}%'))
            elif v not in ('0', ''): props.append((k, v))
            continue
        body.append(raw)
    rune_lines = {l.strip().lower() for r in it.get('runes') or [] for l in r.get('lines') or []}
    head, rest = body[:n_impl], body[n_impl:]
    def line(raw):
        tone = next((t for tag, t in TONE if '{' + tag + '}' in raw), '')
        return (mod_text(raw), tone)
    is_rune = lambda raw: '{rune}' in raw or mod_text(raw).lower() in rune_lines
    enchants = [line(x) for x in head if '{enchant}' in x and not is_rune(x)]
    implicits = [line(x) for x in head if '{enchant}' not in x and not is_rune(x)]
    mods = [line(x) for x in rest if not is_rune(x)]
    runes = [(r.get('displayName') or '', [mod_text(l) for l in r.get('lines') or []]) for r in it.get('runes') or []
             if (r.get('displayName') or 'None') != 'None']
    return {'rarity': rarity, 'name': name, 'base': base, 'slot': it.get('slot') or '', 'props': props, 'req': req,
            'enchants': enchants, 'implicits': implicits, 'mods': mods, 'runes': runes, 'corrupted': corrupted,
            'desecrated': bool(it.get('desecrated')), 'icon': item_icon(it), 'sockets': len(it.get('sockets') or [])}

FLOURISH = ('<svg class="it-fl" viewBox="0 0 28 64" aria-hidden="true"><path opacity=".55" d="M26 2 L14 12 L22 22 L10 32 L22 42 L14 52 L26 62 L26 54 L18 44 L28 34 L18 24 L26 14 Z"/>'
            '<path opacity=".9" d="M18 4 L8 14 L16 24 L4 34 L16 44 L8 54 L18 60 L18 52 L10 42 L20 34 L10 26 L18 16 Z"/><circle cx="6" cy="34" r="2.2" opacity=".85"/></svg>')

def tooltip(i, tid, shown):
    sec = []
    if i['props'] or i['req']:
        sec.append(''.join(f'<p class="it-prop"><span>{e(k)}:</span> {e(v)}</p>' for k, v in i['props'])
                   + (f'<p class="it-req">Requires Level <b>{i["req"]}</b></p>' if i['req'] else ''))
    ln = lambda cls, rows: ''.join(f'<p class="{cls}{" t-" + t if t else ""}">{e(x)}</p>' for x, t in rows)
    if i['enchants']: sec.append(ln('it-ench', i['enchants']))
    if i['implicits']: sec.append(ln('it-mod', i['implicits']))
    if i['mods']: sec.append(ln('it-mod', i['mods']))
    if i['runes']:
        sec.append(''.join(f'<div class="it-rune"><p class="it-rn">{e(n)}</p>' + ''.join(f'<p>{e(x)}</p>' for x in (ls or ['Socketed rune'])) + '</div>'
                           for n, ls in i['runes']))
    if i['corrupted']: sec.append('<p class="it-cor">Corrupted</p>')
    icon = f'<span class="it-ic"><img src="{e(i["icon"])}" alt="" loading="lazy" decoding="async" onerror="this.parentNode.remove()"></span>' if i['icon'] else ''
    head = (f'<div class="it-head">{FLOURISH}<div class="it-title"><b>{e(i["name"])}</b>'
            + (f'<span>{e(i["base"])}</span>' if i['base'] else '') + f'{icon}<i class="it-div" aria-hidden="true"></i></div>{FLOURISH}</div>')
    body = '<i class="it-rule" aria-hidden="true"></i>'.join(f'<div class="it-sec">{s}</div>' for s in sec)
    return f'<div class="it r-{i["rarity"]}" id="{tid}"{"" if shown else " hidden"}>{head}<div class="it-body">{body}</div></div>'

# ---------- the gear doll (POE Source's layout: 8 x 7 cells, then flasks and charms) ----------

AREA = {'Weapon 1': 'w1', 'Helmet': 'hm', 'Weapon 2': 'w2', 'Body Armour': 'bd', 'Amulet': 'am', 'Ring 3': 'r3',
        'Ring 1': 'r1', 'Ring 2': 'r2', 'Gloves': 'gl', 'Belt': 'be', 'Boots': 'bt'}
BELT_ROW = ['Flask 1', 'Charm 1', 'Charm 2', 'Charm 3', 'Flask 2']
LABEL = {'Weapon 1': 'Weapon', 'Weapon 2': 'Off hand', 'Body Armour': 'Body armour', 'Ring 1': 'Ring', 'Ring 2': 'Ring', 'Ring 3': 'Ring',
         'Flask 1': 'Life flask', 'Flask 2': 'Mana flask', 'Charm 1': 'Charm', 'Charm 2': 'Charm', 'Charm 3': 'Charm'}
FLASK_SVG = '<svg viewBox="0 0 24 40" aria-hidden="true"><path d="M9 2h6v7c4 2 6 6 6 11v12a6 6 0 0 1-6 6H9a6 6 0 0 1-6-6V20c0-5 2-9 6-11z"/></svg>'

def doll(slug, b):
    s = b['summary']
    gset = s.get('gear') or {}
    items = {it.get('slot'): parse_item(it) for it in gset.get('items') or []}
    first = next((k for k in list(AREA) + BELT_ROW if k in items), None)
    tips = []
    def cell(slot, cls, style=''):
        i = items.get(slot)
        label = LABEL.get(slot, slot)
        if not i:
            inner = FLASK_SVG if slot.startswith('Flask') else ''
            return f'<span class="slot empty {cls}"{style} aria-hidden="true" title="{e(label)}">{inner}</span>'
        tid = f'it-{slug}-{re.sub(r"[^a-z0-9]+", "-", slot.lower())}'
        tips.append(tooltip(i, tid, slot == first))
        art = f'<img class="slot-art" src="{e(i["icon"])}" alt="" loading="lazy" decoding="async" onerror="this.remove()">' if i['icon'] else f'<i>{e(i["name"])}</i>'
        socks = ''
        if i['sockets']:
            runes = [named_icon(n) for n, _ in i['runes']]
            socks = '<span class="socks" aria-hidden="true">' + ''.join(
                f'<span class="sock">' + (f'<img src="{e(runes[k])}" alt="" loading="lazy" decoding="async" onerror="this.remove()">' if k < len(runes) and runes[k] else '') + '</span>'
                for k in range(i['sockets'])) + '</span>'
        mark = '<span class="slot-mark desecrated" title="Desecrated" aria-hidden="true"></span>' if i['desecrated'] else ''
        return (f'<button class="slot r-{i["rarity"]} {cls}"{style} type="button" aria-controls="{tid}" aria-pressed="{"true" if slot == first else "false"}" '
                f'aria-label="{e(label)}: {e(i["name"])}">{art}{socks}{mark}</button>')
    used = [k for k in AREA if k != 'Ring 3' or 'Ring 3' in items]
    cells = ''.join(cell(k, 'sz-' + AREA[k], f' style="grid-area:{AREA[k]}"') for k in used)
    belt = ''.join(cell(k, 'flask' if k.startswith('Flask') else 'charm', f' style="grid-column:{n + 1}"') for n, k in enumerate(BELT_ROW))
    return (f'<div class="doll-wrap"><div class="doll" role="group" aria-label="Equipped gear. Pick a slot to read the item.">{cells}</div>'
            f'<div class="doll-belt" role="group" aria-label="Flasks and charms">{belt}</div></div>'
            + f'<div class="tips" aria-live="polite">{"".join(tips)}</div>')

# ---------- skills: gem cards ----------

def gem_icon(url, color, size, cls=''):
    img = f'<img src="{e(url)}" alt="" loading="lazy" decoding="async" onerror="this.remove()">' if url else ''
    return f'<span class="gem-ic c-{color.lower()} {cls}" style="--s:{size}px">{img}</span>'

def skills(s):
    cards = []
    for g in (s.get('skills') or {}).get('groups') or []:
        gems = [m for m in g.get('gems') or [] if m.get('name') and m.get('enabled', True) is not False]
        if not gems or g.get('enabled') is False: continue
        act = [m for m in gems if 'SupportGem' not in (m.get('gemId') or '')]
        sup = [m for m in gems if 'SupportGem' in (m.get('gemId') or '')]
        head = ''
        for m in act:
            url, color, tags, desc = gem_info(m)
            lvl = ' · '.join(x for x in (f'Level {m["level"]}' if m.get('level') else '', f'{m["quality"]}% quality' if m.get('quality') else '') if x)
            head += (f'<div class="skc-act" title="{e(desc)}">{gem_icon(url, color, 46)}<div><b>{e(m["name"])}</b>'
                     f'<span>{e(lvl)}</span>' + (f'<span class="skc-tags">{e(tags)}</span>' if tags else '') + '</div></div>')
        if not act:
            head = f'<p class="skc-label">{e(g.get("label") or "Supports")}</p>'
        elif g.get('label'):
            head += f'<p class="skc-label">{e(g["label"])}</p>'
        src = g.get('source') or ''
        if src.startswith('Item:'): head += f'<p class="skc-label">Granted by {e(src.split(":", 2)[-1].split(",")[0].strip())}</p>'
        sups = ''.join(f'<li title="{e(gem_info(m)[3])}">{gem_icon(gem_info(m)[0], gem_info(m)[1], 26)}<span>{e(m["name"])}</span></li>' for m in sup)
        cards.append(f'<li class="skc{" main" if g.get("isMain") else ""}">{head}' + (f'<ul class="skc-sup">{sups}</ul>' if sups else '') + '</li>')
    return f'<div class="sk-wrap"><h4>Skill gems</h4><ul class="skcs">{"".join(cards)}</ul></div>' if cards else ''

# ---------- stats (only when they belong to the loadout shown) ----------

def stats(s):
    if not s.get('statsMatch'): return ''
    d, o, a = s.get('defense') or {}, s.get('offense') or {}, s.get('attributes') or {}
    vit = [(k, d.get(f), c) for k, f, c in (('Life', 'life', '#e0524a'), ('Energy shield', 'energyShield', '#8fc8ff'),
                                             ('Mana', 'mana', '#5a7bff'), ('Spirit', 'spirit', '#e9dfb8')) if d.get(f)]
    res = [('Fire', 'fire', d.get('fireResist')), ('Cold', 'cold', d.get('coldResist')),
           ('Lightning', 'light', d.get('lightningResist')), ('Chaos', 'chaos', d.get('chaosResist'))]
    bars = ''.join(
        f'<li class="res {c}{" neg" if (v or 0) < 0 else ""}" style="--v:{max(0, min(int(v or 0), 75)) / 75:.3f}">'
        f'<span>{k}</span><b>{int(v or 0)}%</b><i aria-hidden="true"></i></li>' for k, c, v in res)
    dps, main = o.get('dps'), (s.get('mainSkill') or {}).get('name')
    vit_html = ''.join(f'<div style="--vc:{c}"><dt>{k}</dt><dd>{int(v):,}</dd></div>' for k, v, c in vit)
    attrs = ''.join(f'<span><b>{int(a[f])}</b>{k}</span>' for k, f in (('Str', 'strength'), ('Dex', 'dexterity'), ('Int', 'intelligence')) if a.get(f) is not None)
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
    le = lastepoch.load(r.get('loadout') or _seed(r['slug']))
    lvl = r.get('level') or (le or {}).get('level') or (s.get('level') if s.get('statsMatch') else None)
    cls = r.get('class_line') or ' · '.join(x for x in (s.get('className'), s.get('ascendClassName')) if x)
    meta = ''.join(f'<span>{x}</span>' for x in (e(r.get('game')), e(cls), f'{int(s["passiveCount"])} passives' if s.get('passiveCount') else '') if x)
    loadout = (s.get('gear') or {}).get('title') if b else ''
    head = ('<header class="sh-head">' + (f'<p class="sh-lvl"><span>Level</span><b>{int(lvl)}</b></p>' if lvl else '')
            + f'<div class="sh-id"><h3>{e(r["name"])}</h3><p class="sh-meta">{meta}</p></div>'
            + (f'<p class="sh-loadout"><span>Loadout</span>{e(loadout)}</p>' if loadout else '') + '</header>')
    links = []
    if r.get('poe_slug'):
        q = urllib.parse.urlencode({'loadout': (r.get('poe_loadout') or '').lower()}) + '&amp;' if r.get('poe_loadout') else ''
        links.append(f'<a class="btn primary" href="{POE_SITE}/b/{e(r["poe_slug"])}?{q}utm_source=reytek1201&amp;utm_medium=referral&amp;utm_campaign=gaming_sheet" {EXT}>Open the full build on POE Source ↗</a>')
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
    if le:
        body = f'{lastepoch.body(r["slug"], le)}<div class="sh-about">{about}</div>{eps_html}'
    elif b:
        st_html = stats(s)
        body = (f'<div class="sh-grid{" has-stats" if st_html else ""}">{doll(r["slug"], b)}{st_html}</div>{skills(s)}'
                f'<div class="sh-about">{about}</div>{eps_html}')
    else:
        body = f'<div class="sh-plain"><div class="sh-about">{about}</div>{eps_html}</div>'
    return open_ + head + body + '</article>'

def player_select(rows, builds):
    if not rows: return ''
    sel = (next((r for r in rows if r.get('status') == 'live'), None) or rows[0])['slug']
    slots = ''.join(slot(r, r['slug'] == sel) for r in rows)
    sheets = ''.join(sheet(r, builds.get(_key(r['poe_slug'], r.get('poe_loadout'))) if r.get('poe_slug') else None, r['slug'] == sel) for r in rows)
    return ('  <section class="ps" id="player-select" aria-labelledby="psTitle">\n    <div class="page-in">\n'
            '      <div class="sec-head"><span class="lbl" id="psTitle">› Player select</span><span class="ps-hint" aria-hidden="true">← → to choose</span></div>\n'
            f'      <div class="ps-row" role="tablist" aria-labelledby="psTitle">{slots}<span class="ps-cursor" aria-hidden="true">1P</span></div>\n'
            f'      <div class="ps-screen">{sheets}</div>\n    </div>\n  </section>\n')

# ---------- Now playing ----------

def now_playing(rows):
    """Every Live character, in sort order."""
    return [r for r in rows if r.get('status') == 'live']

def card(r):
    pic = (r.get('portrait') or [{}])[0]
    pick = f'#pick-{e(r["slug"])}'
    art = (f'<a class="gnp-art" href="{pick}" data-pick="{e(r["slug"])}" tabindex="-1" aria-hidden="true"><img src="{e(pic.get("src"))}" alt="" width="{int(pic.get("w") or 480)}" '
           f'height="{int(pic.get("h") or 480)}" loading="lazy" decoding="async"></a>') if pic.get('src') else ''
    links = []
    if r.get('planner_url'):
        links.append(f'<a class="btn primary" href="{e(r["planner_url"])}" {EXT}>Open the build ↗</a>')
    elif r.get('poe_slug'):
        q = '?' + urllib.parse.urlencode({'loadout': r['poe_loadout'].lower()}).replace('&', '&amp;') if r.get('poe_loadout') else ''
        links.append(f'<a class="btn primary" href="{POE_SITE}/b/{e(r["poe_slug"])}{q}" {EXT}>Open the build ↗</a>')
    links.append(f'<a class="btn" href="{pick}" data-pick="{e(r["slug"])}">Character sheet</a>')
    credit = e(r.get('guide_credit'))
    if r.get('guide_url'):
        credit = f'<a class="txt-link" href="{e(r["guide_url"])}" {EXT}>{credit or "Read the guide"} ↗</a>'
    chips = [x for x in (r.get('class_line'), ('Loadout: ' + r['poe_loadout']) if r.get('poe_loadout') else None,
                         ('Level %s' % r['level']) if r.get('level') else None) if x]
    return (f'      <article class="gnp-card{" has-art" if art else ""}" aria-label="{e(r["name"])}">\n        {art}\n        <div class="gnp-body">\n'
            f'          <div class="proj-meta"><span class="proj-status live">Now playing</span></div>\n'
            f'          <h2>{e(r["name"])}</h2>\n'
            f'          <p class="gnp-meta">{e(r.get("game"))}</p>\n'
            + (f'          <p class="gnp-blurb">{e(r["blurb"])}</p>\n' if r.get('blurb') else '')
            + (f'          <div class="gnp-chips">{"".join("<span>" + e(c) + "</span>" for c in chips)}</div>\n' if chips else '')
            + (f'          <p class="gnp-credit">{credit}</p>\n' if credit else '')
            + f'          <div class="page-cta">{"".join(links)}</div>\n'
            + '        </div>\n      </article>\n')

def render(template, rows, builds=None):
    assert template.count(MARK) == 1, MARK
    assert template.count(SELECT_MARK) == 1, SELECT_MARK
    live = now_playing(rows)
    strip = (f'  <section class="gnp" aria-label="Now playing">\n    <div class="page-in">\n'
             f'      <div class="gnp-list{" two" if len(live) > 1 else ""}">\n{"".join(card(r) for r in live)}      </div>\n    </div>\n  </section>\n') if live else ''
    page = template.replace(MARK + '\n', strip, 1)
    return page.replace(SELECT_MARK + '\n', player_select(rows, builds or {}), 1)
