"""The Projects ticket rail, rendered from the `projects` table (edited in the back office)."""
import html

COLS = ('slug,sort,color,tag,name,what,status,logo,logo_style,mod,time_value,lede,story,'
        'order_note,fire_note,plated_note,stat1_value,stat1_label,stat2_value,stat2_label,'
        'shots,shots_style,link_url,link_label,note,more_url,more_label')
STAMP = {'live': 'Live', 'served': 'Served', 'here': "You're here", 'fire': 'On the fire'}

e = lambda s: html.escape(str(s or ''), True)

def rgb(hex_color):
    h = (hex_color or '#22d3ee').lstrip('#')
    return ','.join(str(int(h[i:i + 2], 16)) for i in (0, 2, 4))

def ticket(r, n):
    no = f'#{n:03d}'
    fire = r['status'] == 'fire'
    stamp = e(STAMP.get(r['status'], r['status']))
    logo = (r.get('logo') or [{}])[0]
    face = ' face' if r.get('logo_style') == 'face' else ''
    tv = r.get('time_value') or ''
    time_html = e(tv).replace('{days}', '<span data-days>--</span>')
    flow_state = ['done', 'now', ''] if fire else ['done', 'done', 'done']
    marks = ['✓', '2', '3'] if fire else ['✓', '✓', '✓']
    flow = ''.join(f'<li class="{flow_state[i]}"><i>{marks[i]}</i><b>{step}</b><span>{e(r.get(k))}</span></li>'
                   for i, (step, k) in enumerate([('Order', 'order_note'), ('Fire', 'fire_note'), ('Plated', 'plated_note')]))
    stats = [(r.get(f'stat{i}_value'), r.get(f'stat{i}_label')) for i in (1, 2) if r.get(f'stat{i}_value')]
    shots = r.get('shots') or []
    wide = 'wide' if r.get('shots_style') == 'wide' else ''
    out = [
        f'        <li class="tr-tk{" cooking" if fire else ""}" style="--pc:{rgb(r.get("color"))}" data-tk="{e(r["slug"])}">\n',
        '          <div class="tr-clip" aria-hidden="true"></div>\n',
        f'          <button class="tr-slip" type="button" aria-haspopup="dialog" aria-label="Open the {e(r["name"])} ticket">\n',
        f'            <span class="tr-row tr-mono"><span>Tkt {no}</span><span>{e(r.get("tag"))}</span></span>\n',
        '            <span class="tr-cut"></span>\n',
        f'            <span class="tr-qty"><b>1×</b><span class="tr-name">{e(r["name"])}</span><span class="tr-what">{e(r.get("what"))}</span></span>\n',
        f'            <span class="tr-art"><img class="tr-logo{face}" src="{e(logo.get("src"))}" alt="" width="{int(logo.get("w") or 512)}" height="{int(logo.get("h") or 512)}" loading="lazy" decoding="async"><span class="tr-stamp">{stamp}</span></span>\n',
        '            <span class="tr-cut"></span>\n',
        f'            <span class="tr-mod"><i>Mod:</i> {e(r.get("mod"))}</span>\n',
        f'            <span class="tr-time"><span>{"Fires in" if fire else "Ticket time"}</span><b>{time_html}</b></span>\n',
        '            <span class="tr-pull" aria-hidden="true">Pull ↓</span>\n',
        '          </button>\n',
        '          <div class="tr-full" hidden>\n',
        f'            <div class="tr-row tr-mono pr"><span>Reytek kitchen · build ticket</span><span>{no} · {e(r.get("tag"))}</span></div>\n',
        '            <div class="tr-cut pr"></div>\n',
        f'            <div class="pr"><div class="tr-sub"><span class="tr-mono">1× · {e(r.get("what"))}</span><span class="tr-stamp big">{stamp}</span></div><h2 class="tr-oname">{e(r["name"])}</h2><p class="tr-olede">{e(r.get("lede"))}</p></div>\n',
        '            <div class="tr-cut pr"></div>\n',
        f'            <div class="tr-sec pr"><h3>The order</h3><p>{e(r.get("story"))}</p></div>\n',
        '            <div class="tr-cut pr"></div>\n',
        f'            <div class="tr-sec pr"><h3>Prep → Fire → Plated</h3><ol class="tr-flow">{flow}</ol></div>\n',
    ]
    if stats:
        out.append('            <div class="pr"><div class="tr-stats">' + ''.join(f'<div><b>{e(v)}</b><span>{e(l)}</span></div>' for v, l in stats) + '</div></div>\n')
    if shots:
        out.append('            <div class="tr-sec pr"><h3>On the plate</h3><div class="tr-shots">' + ''.join(
            f'<figure class="{wide}"><img src="{e(s["src"])}" alt="{e(r["name"] + ": " + s.get("alt", ""))}" width="{int(s["w"])}" height="{int(s["h"])}" loading="lazy" decoding="async"><figcaption>{e(s.get("alt"))}</figcaption></figure>'
            for s in shots) + '</div></div>\n')
    out.append('            <div class="tr-cut pr"></div>\n')
    if r.get('link_url'):
        more = f'<a class="txt-link tr-more" href="{e(r["more_url"])}">{e(r.get("more_label"))}</a>' if r.get('more_url') else ''
        out.append(f'            <div class="pr tr-gos"><a class="tr-go" href="{e(r["link_url"])}" target="_blank" rel="noopener"><i></i>{e(r.get("link_label"))}</a>{more}</div>\n')
    elif r.get('note'):
        out.append(f'            <div class="pr"><span class="tr-mono">{html.escape(r["note"], False)}</span></div>\n')
    out += ['          </div>\n', '        </li>\n']
    return ''.join(out)

def render(template, rows):
    start = template.index('aria-label="Projects">\n') + len('aria-label="Projects">\n')
    end = template.index('        </ol>\n      </div>', start)
    page = template[:start] + ''.join(ticket(r, i + 1) for i, r in enumerate(rows)) + template[end:]
    served = sum(1 for r in rows if r['status'] != 'fire')
    page = page.replace('<span><b>5</b> on the rail</span>', f'<span><b>{len(rows)}</b> on the rail</span>', 1)
    return page.replace('<span><b>4</b> served</span>', f'<span><b>{served}</b> served</span>', 1)
