"""Last Epoch character sheet: gear doll, idol grid, skills, passives, blessings and stats.

Everything is drawn from the JSON that the "Export to reytek" bookmarklet copies off a Last Epoch Tools planner page
(see le_export.js). The back office stores it as text in characters.loadout. No game art is used: slots get drawn
glyphs coloured by rarity."""
import json
import os
import re
from html import escape as e

RARITIES = ('legendary', 'unique', 'exalted', 'rare', 'magic', 'set', 'normal')

# gear slots in doll order: key, label, grid area
SLOTS = [('head', 'Helmet', 'hd'), ('amulet', 'Amulet', 'am'), ('weapon1', 'Weapon', 'w1'), ('chest', 'Body armor', 'bd'),
         ('weapon2', 'Off hand', 'w2'), ('ring1', 'Ring', 'r1'), ('waist', 'Belt', 'bt'), ('ring2', 'Ring', 'r2'),
         ('hands', 'Gloves', 'gl'), ('feet', 'Boots', 'bo'), ('relic', 'Relic', 'rl')]

# one drawn glyph per slot (24x24, stroked)
G = {
    'head': '<path d="M5 14V9a7 7 0 0 1 14 0v5l-2 5h-3l-1-3h-2l-1 3H7z"/><path d="M9 11h6"/>',
    'amulet': '<path d="M6 3l6 9 6-9"/><circle cx="12" cy="16" r="4.5"/><path d="M12 13.5v5"/>',
    'weapon1': '<path d="M5 20L19 4"/><path d="M15 4h4v4"/><path d="M4 17l3 3"/>',
    'weapon2': '<path d="M12 3l7 3v6c0 4-3 7-7 9-4-2-7-5-7-9V6z"/>',
    'chest': '<path d="M8 3l-5 3v5l3 1v9h12v-9l3-1V6l-5-3-4 3z"/>',
    'ring1': '<circle cx="12" cy="14" r="6"/><path d="M9 6l3-3 3 3-3 3z"/>',
    'waist': '<rect x="3" y="9" width="18" height="7" rx="1.5"/><rect x="9.5" y="8" width="5" height="9" rx="1"/>',
    'hands': '<path d="M7 21v-6l-2-5 2-1 1 3V4h2v8V3h2v9V4h2v9l1-3 2 1-2 6v4z"/>',
    'feet': '<path d="M8 3h6v9l5 3v4a1 1 0 0 1-1 1H6a1 1 0 0 1-1-1v-3l3-1z"/>',
    'relic': '<path d="M12 3c4 0 7 3 7 7 0 3-1 4-2 5v3h-3v-2h-4v2H7v-3c-1-1-2-2-2-5 0-4 3-7 7-7z"/><circle cx="9.5" cy="10" r="1.2"/><circle cx="14.5" cy="10" r="1.2"/>',
    'idol': '<path d="M12 3l6 4v6l-6 8-6-8V7z"/><path d="M12 8v6"/>',
}
G['ring2'] = G['ring1']

def svg(key, cls='le-gl'):
    return f'<svg class="{cls}" viewBox="0 0 24 24" aria-hidden="true">{G.get(key, G["idol"])}</svg>'

NOTE = re.compile(r"^(Only affects|Affects |Prevents |Haste grants|An idol is|There is no|Can stack|All stacks|Prioritises|The health is|"
                  r"Attributes on|Stats on|Your poison damage stats|multiplicative|This buff|and your |\(.+\)$)")
BASE_WORDS = {'legendary', 'unique', 'exalted', 'rare', 'magic', 'set', 'normal', 'primordial', 'heretical'}

def load(text):
    """The saved JSON, or None if it is empty or not valid (the sheet then falls back to the plain layout)."""
    try:
        d = json.loads(text) if text else None
    except ValueError:
        return None
    return d if isinstance(d, dict) and (d.get('equipment') or d.get('idols')) else None

def _lore(l):
    return (not re.search(r'\d', l) and not NOTE.match(l) and (len(l) > 38 or l.endswith('.') or l.startswith(('"', '“')))) or l.startswith('"')

def parse(it):
    L = [x for x in (it or {}).get('lines') or [] if x]
    if not L: return None
    out = {'name': L[0], 'type': L[1] if len(L) > 1 else '', 'base': '', 'props': [], 'imp': [], 'mod': [], 'rel': [], 'lore': '', 'req': [],
           'rar': None}
    i = 2
    if len(L) > 2 and L[2].split(' ')[0].lower() in BASE_WORDS:
        out['base'] = L[2]; i = 3
    out['rar'] = (out['base'].split(' ')[0].lower() if out['base'] else '') or None
    sec = 'props'
    def add(lst, l):
        if re.fullmatch(r'T\d', l):
            if lst: lst[-1]['tier'] = l
            return
        lst.append({'t': l, 'tier': None, 'note': bool(NOTE.match(l))})
    for l in L[i:]:
        if l == 'Implicits': sec = 'imp'; continue
        if l == 'Modifiers': sec = 'mod'; continue
        if l in ('Related abilities', 'Related ailments'): sec = 'rel'; continue
        if re.match(r"^(Requires|Minimum Drop|Primordial Unique|Can't drop|Drops with|Corrupted$)", l) and sec != 'props':
            sec = 'req'
        if sec == 'req': out['req'].append(l)
        elif sec == 'props': out['props'].append(l)
        elif sec == 'imp': add(out['imp'], l)
        elif sec == 'mod': add(out['mod'], l)
        elif sec == 'rel':
            if _lore(l): out['lore'] = l
            else: out['rel'].append(l)
    if out['mod'] and not out['lore'] and _lore(out['mod'][-1]['t']) and not out['mod'][-1]['tier']:
        out['lore'] = out['mod'].pop()['t']
    return out

def rar_class(p, raw):
    if p['rar'] in RARITIES: return p['rar']
    return {'10': 'heretical', '9': 'legendary', '2': 'rare'}.get(str((raw or {}).get('rarityClass')), 'normal')

def card(cid, p, raw, shown):
    li = lambda lst: ''.join(f'<li class="{"note" if x["note"] else "mod"}"><span>{e(x["t"])}</span>' + (f'<i>{e(x["tier"])}</i>' if x['tier'] else '') + '</li>' for x in lst)
    head = f'<header><b class="le-nm">{e(p["name"])}</b><span class="le-ty">{e(p["type"])}' + (f' · {e(p["base"])}' if p['base'] else '') + '</span></header>'
    props = f'<p class="le-pr">{" · ".join(e(x) for x in p["props"])}</p>' if p['props'] else ''
    imp = f'<ul class="le-imp">{li(p["imp"])}</ul>' if p['imp'] else ''
    mod = f'<ul class="le-mods">{li(p["mod"])}</ul>' if p['mod'] else ''
    rel = f'<p class="le-rel">{"".join("<span>" + e(x) + "</span>" for x in p["rel"])}</p>' if p['rel'] else ''
    lore = f'<p class="le-lore">{e(p["lore"])}</p>' if p['lore'] else ''
    req = f'<p class="le-req">{" · ".join(e(x) for x in p["req"][:3])}</p>' if p['req'] else ''
    return (f'<div class="le-card rar-{rar_class(p, raw)}" id="{cid}"' + ('' if shown else ' hidden') + f'>{head}{props}{imp}{mod}{rel}{lore}{req}</div>')

# Item icons saved in img/le/ (from the build guide's gear section), looked up by item name. A missing file falls back to the drawn glyph.
ICONS = {'Lethal Concentration': '2hand_icon_2', 'Mantle of the Pale Ox': 'chest_icon_31', 'Unbroken Legion': 'helm_icon_26',
         "Julra's Obsession": 'gloves_icon_9', 'Foot of the Mountain': 'boots_icon_7', "Brewmaster's Buckle": 'belt_icon_13',
         'Hollow Finger': 'ring_icon_16', 'Unsated Rage': 'ring_icon_28', "Serpent's Milk": 'amulet_icon_23', "Tyrant's Skull": 'relic_icon_3'}
_ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))

def icon(name, key):
    f = ICONS.get(name)
    if f and os.path.exists(os.path.join(_ROOT, 'img', 'le', f + '.jpg')):
        ar = {'2hand': '150/260', 'chest': '150/260', 'belt': '235/128'}.get(f.split('_')[0], '1')
        return (f'<span class="le-ic"><span class="le-icf" style="aspect-ratio:{ar}"><img class="le-ic-i" src="/img/le/{f}.jpg" alt="" '
                f'loading="lazy" decoding="async"></span></span>')
    return svg(key)

def doll(slug, d, first):
    eq, cards, btns = d.get('equipment') or {}, [], []
    for key, label, area in SLOTS:
        raw = eq.get(key); p = parse(raw)
        cid = f'lec-{slug}-{key}'
        cls = f'le-sl a-{area}'
        if not p:
            btns.append(f'<span class="le-sl a-{area} empty" title="{e(label)}">{svg(key)}</span>')
            continue
        shown = key == first
        cards.append(card(cid, p, raw, shown))
        btns.append(f'<button type="button" class="{cls} rar-{rar_class(p, raw)}" aria-controls="{cid}" aria-pressed="{"true" if shown else "false"}" '
                    f'aria-label="{e(label)}: {e(p["name"])}">{icon(p["name"], key)}<span class="le-sn">{e(label)}</span></button>')
    return ''.join(btns), cards

def idol_panel(slug, d, cards_out):
    cells = d.get('idolCells') or ''
    kind = {'b': 'blocked', 'r': 'refract'}
    base = ''.join(f'<span class="le-cell c-{kind.get(cells[i] if i < len(cells) else "n", "open")}" style="grid-column:{i % 5 + 1};grid-row:{i // 5 + 1}"></span>' for i in range(25))
    blocks = []
    for n, raw in enumerate(d.get('idols') or []):
        p = parse(raw)
        if not p: continue
        cid = f'lec-{slug}-idol{n}'
        cards_out.append(card(cid, p, raw, False))
        blocks.append(f'<button type="button" class="le-idol rar-{rar_class(p, raw)}" style="grid-column:{int(raw["col"]) + 1}/span {int(raw["w"])};grid-row:{int(raw["row"]) + 1}/span {int(raw["h"])}" '
                      f'aria-controls="{cid}" aria-pressed="false" aria-label="{e(p["name"])}">{svg("idol", "le-gl")}</button>')
    alt = eq_alt = (d.get('equipment') or {}).get('idol_altar')
    ap = parse(alt)
    if ap:
        cid = f'lec-{slug}-altar'
        cards_out.append(card(cid, ap, alt, False))
        altar = (f'<button type="button" class="le-altar" aria-controls="{cid}" aria-pressed="false">{svg("idol")}<span>{e(ap["name"])}</span></button>')
    else:
        altar = ''
    return (f'<div class="le-box le-idols"><h4>Idols</h4>{altar}<div class="le-igrid" role="group" aria-label="Idol grid">{base}{"".join(blocks)}</div></div>')

STAT_HI = ('Health', 'Mana', 'Armor', 'Movement Speed', 'Dodge Rating', 'Health Regen')

def stats_panel(d):
    st = d.get('stats') or {}
    if not st: return ''
    cols = []
    for title, rows in st.items():
        cols.append(f'<section><h5>{e(title)}</h5><dl>' + ''.join(f'<div><dt>{e(a)}</dt><dd>{e(b)}</dd></div>' for a, b in rows) + '</dl></section>')
    return f'<div class="le-box le-stats"><h4>Character</h4><div class="le-st">{"".join(cols)}</div></div>'

def blessings(d):
    items = []
    for raw in d.get('blessings') or []:
        L = raw.get('lines') or []
        if not L: continue
        eff = [x for x in L[2:] if x not in ('Implicits',) and not x.startswith('Timeline')]
        tl = next((x[len('Timeline: '):] for x in L if x.startswith('Timeline:')), '')
        grand = L[0].startswith('Grand')
        items.append((0 if grand else 1, f'<li class="{"grand" if grand else ""}"><b>{e(L[0])}</b>' + (f'<span>{e("; ".join(eff))}</span>' if eff else '') + (f'<em>{e(tl)}</em>' if tl else '') + '</li>'))
    items.sort(key=lambda x: x[0])
    return f'<div class="le-box le-bless"><h4>Blessings</h4><ul>{"".join(x[1] for x in items)}</ul></div>' if items else ''

def skills(d):
    out = []
    for s in d.get('skills') or []:
        nodes = s.get('nodes') or []
        spent = sum(int(n.get('points') or 0) for n in nodes)
        top = sorted(nodes, key=lambda n: -int(n.get('points') or 0))[:4]
        chips = ''.join(f'<li><span>{e(n.get("name"))}</span><b>{int(n.get("points") or 0)}/{int(n.get("max") or 0)}</b></li>' for n in nodes)
        out.append(f'<li class="le-sk"><details><summary><span class="le-skn">{e(s.get("name"))}</span><span class="le-skl">Lv {int(s.get("level") or 0)}</span>'
                   f'<span class="le-skp">{spent} points</span></summary><ul class="le-nodes">{chips}</ul></details></li>')
    return f'<div class="le-box le-skills"><h4>Skills</h4><ol>{"".join(out)}</ol></div>' if out else ''

def passives(d):
    ps = [p for p in d.get('passives') or [] if p.get('nodes') or p.get('points')]
    if not ps: return ''
    total = sum(int(p.get('points') or 0) for p in ps)
    out = []
    for p in ps:
        pts = int(p.get('points') or 0)
        nodes = ''.join(f'<li><span>{e(n.get("name"))}</span><b>{int(n.get("points") or 0)}/{int(n.get("max") or 0)}</b></li>' for n in p.get('nodes') or [])
        out.append(f'<li class="le-ps"><details><summary><span class="le-pn">{e(p.get("tree"))}</span><span class="le-pp">{pts}</span>'
                   f'<span class="le-bar" aria-hidden="true"><i style="width:{round(100 * pts / total)}%"></i></span></summary><ul class="le-nodes">{nodes}</ul></details></li>')
    return f'<div class="le-box le-pass"><h4>Passives <small>{total} points</small></h4><ol>{"".join(out)}</ol></div>'

def body(slug, d):
    first = next((k for k, _, _ in SLOTS if (d.get('equipment') or {}).get(k)), None)
    btns, cards = doll(slug, d, first)
    idols = idol_panel(slug, d, cards)
    note = ''
    meta = ' · '.join(x for x in (d.get('season'), f'Patch {d["gameVersion"]}' if d.get('gameVersion') else '') if x)
    if meta: note = f'<p class="le-src">{e(meta)}. Read from the Last Epoch Tools planner.</p>'
    return (f'<div class="le" data-le>'
            f'<div class="le-main"><div class="le-box le-dollbox"><h4>Gear</h4><div class="le-doll">{btns}</div></div>'
            f'<div class="le-tipcol"><div class="le-tip" aria-live="polite">{"".join(cards)}</div></div></div>'
            f'<div class="le-row">{idols}{stats_panel(d)}</div>'
            f'<div class="le-row le-row3">{skills(d)}{passives(d)}{blessings(d)}</div>{note}</div>')
