"""The Gaming page's "Now playing" card, rendered from the `characters` table (edited in the back office)."""
import html

COLS = 'slug,sort,game,name,status,class_line,blurb,poe_slug,planner_url,guide_url,guide_credit,videos,portrait'
MARK = '__NOW_PLAYING__'

e = lambda s: html.escape(str(s or ''), True)

def now_playing(rows):
    """The first Live character by sort order, or None."""
    return next((r for r in rows if r.get('status') == 'live'), None)

def card(r):
    pic = (r.get('portrait') or [{}])[0]
    art = (f'<div class="gnp-art"><img src="{e(pic.get("src"))}" alt="{e(pic.get("alt") or r["name"])}" width="{int(pic.get("w") or 480)}" '
           f'height="{int(pic.get("h") or 480)}" loading="lazy" decoding="async"></div>') if pic.get('src') else ''
    meta = ' · '.join(e(x) for x in (r.get('game'), r.get('class_line')) if x)
    ext = 'target="_blank" rel="noopener noreferrer"'
    links = []
    if r.get('planner_url'):
        links.append(f'<a class="btn primary" href="{e(r["planner_url"])}" {ext}>Open the build ↗</a>')
    elif r.get('poe_slug'):
        links.append(f'<a class="btn primary" href="https://www.poe2source.com/b/{e(r["poe_slug"])}" {ext}>Open the build on POE Source ↗</a>')
    credit = e(r.get('guide_credit'))
    if r.get('guide_url'):
        credit = f'<a class="txt-link" href="{e(r["guide_url"])}" {ext}>{credit or "Read the guide"} ↗</a>'
    return (f'  <section class="gnp" aria-labelledby="gnpTitle">\n    <div class="page-in">\n'
            f'      <div class="gnp-card{" has-art" if art else ""}">\n        {art}\n        <div class="gnp-body">\n'
            f'          <div class="proj-meta"><span class="proj-status live">Now playing</span><span>{meta}</span></div>\n'
            f'          <h2 id="gnpTitle">{e(r["name"])}</h2>\n'
            + (f'          <p>{e(r["blurb"])}</p>\n' if r.get('blurb') else '')
            + (f'          <p class="gnp-credit">{credit}</p>\n' if credit else '')
            + (f'          <div class="page-cta">{"".join(links)}</div>\n' if links else '')
            + '        </div>\n      </div>\n    </div>\n  </section>\n')

def render(template, rows):
    assert template.count(MARK) == 1, MARK
    r = now_playing(rows)
    return template.replace(MARK + '\n', card(r) if r else '', 1)
