/* Export to reytek: reads a Last Epoch Tools build planner page you are viewing (the same text you'd see by hovering
   each item, skill node and passive) and copies it as JSON for the reytek1201 back office. Nothing is sent anywhere. */
(async () => {
  const toast = document.createElement('div');
  toast.style.cssText = 'position:fixed;z-index:99999;right:16px;bottom:16px;max-width:340px;padding:12px 14px;border-radius:10px;background:#0b0b0e;color:#fff;border:1px solid #00d4ff;font:13px/1.4 system-ui,sans-serif;box-shadow:0 8px 30px #000a';
  toast.textContent = 'Export to reytek: reading your build, give it about a minute. Keep this tab open.';
  document.body.appendChild(toast);
  const $ = (s, r = document) => r.querySelector(s), $$ = (s, r = document) => [...r.querySelectorAll(s)];
  const vis = e => e && e.offsetParent !== null;
  const txt = e => String((e && e.innerText) || '').trim();
  // timers are throttled in background tabs, so wait with a message-channel spin instead
  const sleep = ms => new Promise(res => { const t0 = performance.now(), mc = new MessageChannel(); mc.port1.onmessage = () => performance.now() - t0 >= ms ? res() : mc.port2.postMessage(0); mc.port2.postMessage(0); });
  const fire = (el, types) => { const r = el.getBoundingClientRect(); for (const t of types) el.dispatchEvent(new MouseEvent(t, { bubbles: true, clientX: r.x + r.width / 2, clientY: r.y + r.height / 2 })); };
  const over = async (el, ms = 650) => { fire(el, ['mouseout', 'mouseleave']); await sleep(120); fire(el, ['mouseover', 'mouseenter', 'mousemove']); await sleep(ms); };
  const out_ = el => fire(el, ['mouseout', 'mouseleave']);
  const cards = () => $$('.item-card').filter(e => vis(e) && txt(e).length > 10);
  const tips = () => $$('.tippy-box').filter(e => vis(e) && txt(e).length > 3);
  const STOP = /^(Effective Level for Legendary Potential|LP\d|LP with|Obtained from|Drops with|Fixed affix pool|Random Drop|Rune of Ascendance)/;
  const readCard = c => {
    if (!c) return null;
    const lines = []; for (const l of txt(c).split('\n').map(s => s.trim()).filter(Boolean)) { if (STOP.test(l)) break; lines.push(l); }
    return { rarityClass: (c.className.match(/item-rarity(\d+)/) || [])[1] || null, lines: lines.slice(0, 60) };
  };
  const hoverItem = async el => {
    out_(el); await sleep(150); const before = new Set(cards());
    fire(el, ['mouseover', 'mouseenter', 'mousemove']);
    let c = null; for (let i = 0; i < 20 && !c; i++) { await sleep(150); c = cards().find(x => !before.has(x)) || null; }
    const it = readCard(c); out_(el); await sleep(100); return it;
  };
  const hoverNode = async (n, pts) => {   // the node tooltip starts with its point count, then its name
    out_(n); await sleep(250);
    const before = new Set($$('.tippy-box')); fire(n, ['mouseover', 'mouseenter', 'mousemove']);
    let t = [];
    for (let i = 0; i < 30; i++) { await sleep(80); const hit = $$('.tippy-box').filter(b => !before.has(b)).map(txt).find(s => s.split('\n')[0].trim() === pts); if (hit) { t = hit.split('\n').map(s => s.trim()).filter(Boolean); break; } }
    out_(n);
    return { name: t[1] || '', points: +pts.split('/')[0], max: +pts.split('/')[1], text: t.slice(2).join(' ').slice(0, 220) };
  };

  const body = txt(document.body), g = re => { const m = body.match(re); return m ? m[1].trim() : null; };
  const out = { v: 1, source: { url: location.href.split('#')[0], site: 'Last Epoch Tools', title: document.title, exportedAt: new Date().toISOString() } };
  out.class = g(/Class:\s*([^\n]+)/); out.level = +g(/Level:\s*(\d+)/) || null;
  out.season = g(/Season\s*\d+:\s*([^\n]+)/); out.gameVersion = g(/Game Version:\s*([^\n]+)/);

  out.stats = {};
  $$('.stat-table-header').filter(vis).forEach(h => {
    const lines = txt(h.parentElement).split('\n').map(s => s.trim()).filter(Boolean).slice(1), rows = [];
    for (let i = 0; i + 1 < lines.length; i += 2) rows.push([lines[i], lines[i + 1]]);
    out.stats[txt(h).replace(/\s*\(.*\)$/, '')] = rows;
  });

  out.equipment = {}; out.blessings = [];
  for (const el of $$('.equipped-item')) {
    const key = ([...el.classList].find(c => c.startsWith('item-')) || '').slice(5);
    const it = await hoverItem(el); if (!it || /No item selected/i.test(it.lines[0] || '')) continue;
    if (key === 'blessing') out.blessings.push(it); else out.equipment[key] = it;
  }

  out.idols = [];
  const grid = $('.idol-grid'); if (grid) {
    const gr = grid.getBoundingClientRect(), cell = gr.width / 5;
    for (const el of $$('.idol-bitmap-container')) {
      const it = await hoverItem(el), r = el.getBoundingClientRect(); if (!it) continue;
      out.idols.push({ col: Math.round((r.x - gr.x) / cell), row: Math.round((r.y - gr.y) / cell), w: Math.round(r.width / cell), h: Math.round(r.height / cell), ...it });
    }
  }

  { // which idol-grid cells are open, blocked or refracted slots
    const gr = $('.idol-grid') && $('.idol-grid').getBoundingClientRect(), cells = Array(25).fill('n');
    if (gr) { const cell = gr.width / 5; $$('.idol-slot').filter(vis).forEach(e => { const r = e.getBoundingClientRect(); if (r.width > 60) return; const c = Math.round((r.x - gr.x) / cell), w = Math.round((r.y - gr.y) / cell); if (c >= 0 && c < 5 && w >= 0 && w < 5) cells[w * 5 + c] = /blocked/.test(e.className) ? 'b' : /refracted/.test(e.className) ? 'r' : 'n'; }); }
    out.idolCells = cells.join('');
  }

  out.skills = [];
  $('.skills-panel-tab').click(); await sleep(1000);
  const nSkills = $$('.skill-spec-slot.slot-with-skill').length;
  for (let i = 0; i < nSkills; i++) {
    $$('.skill-spec-slot.slot-with-skill')[i].click(); await sleep(800);
    const hdr = $$('[class*=skill]').filter(vis).map(txt).find(t => /^[^\n]+\nLevel \d+/.test(t)) || '';
    const nodes = [];
    for (const n of $$('.tree-node.node-taken')) {
      const p = txt($('.tree-node-points', n)); if (/^\d+\/\d+$/.test(p)) nodes.push(await hoverNode(n, p));
    }
    out.skills.push({ slot: i, name: hdr.split('\n')[0], level: +(hdr.match(/Level (\d+)/) || [])[1] || null, nodes });
    const back = $('.back-button'); if (back) { back.click(); await sleep(400); }
  }
  const x1 = $$('[class*=close]').filter(vis)[0]; if (x1) x1.click(); await sleep(400);

  out.passives = [];
  $('.passives-panel-tab').click(); await sleep(1000);
  const readTree = async name => {
    const nodes = [];
    for (const n of $$('.tree-node-passive.node-taken')) { const p = txt(n); if (/^\d+\/\d+$/.test(p)) nodes.push(await hoverNode(n, p)); }
    out.passives.push({ tree: name, points: nodes.reduce((s, n) => s + n.points, 0), nodes });
  };
  for (const d of [$('.base-class-diamond'), ...$$('.class-mastery-diamond')].filter(Boolean)) {   // base class, then each mastery
    const l = txt(d).split('\n').filter(Boolean), name = l.find(x => /^[A-Za-z]/.test(x) && !/^(Base Class|Mastered)$/i.test(x));
    if (!(parseInt(l[0], 10) > 0)) { out.passives.push({ tree: name, points: 0, nodes: [] }); continue; }
    d.click(); await sleep(900); await readTree(name);
  }
  const x2 = $$('[class*=close]').filter(vis)[0]; if (x2) x2.click();

  const json = JSON.stringify(out);
  try { await navigator.clipboard.writeText(json); out.copied = true; } catch (e) { out.copied = false; }
  window.__reytekLE = out;
  if (out.copied) { toast.textContent = 'Copied. Open the back office, edit the Last Epoch character and paste into "Last Epoch build data".'; }
  else {
    toast.innerHTML = 'Select all and copy this, then paste it into the back office:<br>';
    const ta = document.createElement('textarea'); ta.value = json; ta.style.cssText = 'width:100%;height:90px;margin-top:6px'; toast.appendChild(ta); ta.focus(); ta.select();
  }
  setTimeout(() => { if (out.copied) toast.remove(); }, 20000);
  return out;
})();
