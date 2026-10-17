/* ---------- router: pages change without a reload, so the music keeps playing ----------
   The frame (vortex, cursor, rail, guide, footer) stays put. Only the page regions below are swapped.
   The homepage's regions are kept in memory when you leave, so the turntable keeps spinning and
   coming back is instant. If a visit starts on an inner page, the homepage engine loads the first
   time you go home, or right away on the Music page, which borrows the homepage's turntable. */
(() => {
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fmt = s => { s = Math.max(0, Math.floor(s || 0)); return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); };

  const P = window.RTPlayer;

  if (!window.fetch || !history.pushState || !window.DOMParser) return;
  const ROOT = new URL(window.RT_ROOT || './', location.href);
  const PAGES = ['', 'origin/', 'music/', 'vision/', 'projects/', 'gaming/', 'art/', 'work/'];
  const slugOf = href => {
    let u; try { u = new URL(href, location.href); } catch (e) { return null; }
    if (u.origin !== ROOT.origin || !u.pathname.startsWith(ROOT.pathname)) return null;
    const p = u.pathname.slice(ROOT.pathname.length).replace(/index\.html$/, '');
    return PAGES.includes(p) ? p : null;
  };
  const REGIONS = ['.hud-tl', 'nav.chapters', '.hud-bl', 'main', '#lyrics'];
  let cur = slugOf(location.href);
  if (cur == null) return;
  let home = null, seq = 0, busy = false;
  let rDisc = null, rSmall = null, rStrong = null, rSaved = null, lastKey = '';
  const docs = new Map();
  const loadedScripts = new Set([...document.scripts].map(s => s.dataset.rt).filter(Boolean));
  if (window.RT_ENGINE) document.documentElement.classList.add('rt-engine');
  history.scrollRestoration = 'manual';
  history.replaceState({ ...(history.state || {}), rt: 1, y: scrollY }, '');

  // the frame persists across pages, so its links must not depend on the current folder
  const pin = root => root.querySelectorAll('a[href]').forEach(a => { if (!a.closest('main') && slugOf(a.href) != null) a.setAttribute('href', a.href); });
  pin(document.querySelector('#guide') || document.createElement('i'));

  const fetchDoc = href => {
    const u = new URL(href, location.href); u.hash = '';
    const slug = slugOf(u.href);
    const get = url => fetch(url, { credentials: 'same-origin' }).then(r => {
      if (r.ok) return r.text();
      // folder URLs don't resolve everywhere (the preview host): try the page file itself
      if (url.endsWith('/')) return get(url + 'index.html');
      throw new Error('page ' + r.status);
    });
    // cache the text, not the document: nodes get moved out of a parsed page, so each visit parses a fresh copy
    if (!docs.has(slug)) docs.set(slug, get(u.href).catch(e => { docs.delete(slug); throw e; }));
    return docs.get(slug).then(t => new DOMParser().parseFromString(t, 'text/html'));
  };

  /* ---- warp: the page streaks out, a ring of light opens from where you tapped, the next page settles in ---- */
  const warp = document.createElement('div'); warp.id = 'warp'; warp.setAttribute('aria-hidden', 'true');
  document.body.appendChild(warp);
  const root = document.documentElement;
  function warpOut(x, y) {
    if (reduce) return Promise.resolve();
    warp.style.setProperty('--x', (x ?? innerWidth / 2) + 'px'); warp.style.setProperty('--y', (y ?? innerHeight / 2) + 'px');
    warp.classList.remove('go'); void warp.offsetWidth; warp.classList.add('go');
    if (window.rtShock && x != null) window.rtShock(x / innerWidth * 2 - 1, -(y / innerHeight * 2 - 1));
    root.classList.add('rt-out');
    return new Promise(r => setTimeout(r, 170));
  }
  function warpIn() {
    root.classList.remove('rt-out');
    if (reduce) return;
    root.classList.add('rt-in');
    setTimeout(() => root.classList.remove('rt-in'), 420);
  }

  /* ---- the turntable: one deck, shown on the homepage and on the Music page ---- */
  let deckHome = null, engineP = null;
  const deckWrap = () => document.querySelector('.deck-wrap') || (home && home.nodes.main ? home.nodes.main.querySelector('.deck-wrap') : null);
  function mountDeck() {
    const slot = document.getElementById('deckSlot');
    if (!slot || !window.RT_ENGINE) return;
    const w = deckWrap(); if (!w || slot.contains(w)) return;
    deckHome = w.parentNode;
    slot.appendChild(w); slot.classList.add('mounted');
  }
  function unmountDeck() {
    const slot = document.getElementById('deckSlot'), w = slot && slot.querySelector('.deck-wrap');
    if (w && deckHome) deckHome.appendChild(w);   // back into the homepage's music section, on screen or in memory
  }
  // a visit that starts on the Music page: start the homepage engine underneath it, out of sight
  function engineUnder() {
    if (engineP || window.RT_ENGINE || !document.getElementById('deckSlot')) return engineP;
    engineP = (async () => {
      try {
        const doc = await fetchDoc(ROOT.href);
        const hold = document.createElement('div');
        hold.setAttribute('aria-hidden', 'true'); hold.inert = true;
        hold.style.cssText = 'position:fixed;top:0;left:-300vw;width:100vw;visibility:hidden;pointer-events:none';
        const nodes = {};
        // the homepage's paths are relative to the site root, and this page sits a folder down
        doc.querySelectorAll('[src],[href],[poster]').forEach(el => ['src', 'href', 'poster'].forEach(k => {
          const v = el.getAttribute(k); if (v && !/^(#|[a-z]+:)/i.test(v)) el.setAttribute(k, new URL(v, ROOT).href);
        }));
        REGIONS.forEach(sel => { const n = doc.querySelector(sel); if (n) { nodes[sel] = document.adoptNode(n); hold.appendChild(nodes[sel]); } });
        document.body.prepend(hold);   // first in the document, so the engine binds to the homepage's elements
        await loadEngine(doc);
        // the engine lets returning visitors straight in a tick after it starts; keep its homepage in reach until then
        const gate = nodes.main && nodes.main.querySelector('#gate');
        await new Promise(r => { const t0 = performance.now(), chk = () => (!gate || gate.classList.contains('done') || performance.now() - t0 > 4000) ? r() : setTimeout(chk, 30); chk(); });
        home = { nodes, head: headFrom(doc) };
        if (cur === 'music/') mountDeck();
        hold.remove(); hold.inert = false;
        Object.values(nodes).forEach(n => n.removeAttribute && n.removeAttribute('inert'));
        window.RT.cleanups.splice(0).forEach(c => { try { c(); } catch (e) {} });
        window.RT.inits.forEach(fn => window.RT.run(fn));   // the release list now plays through the deck
      } catch (e) { console.warn('turntable unavailable', e); }
    })();
    return engineP;
  }

  /* ---- page lifecycle ---- */
  function closeOverlays() {
    if (document.body.classList.contains('cg-open')) { const k = document.getElementById('guideKey'); if (k) k.click(); }
    const lb = document.getElementById('lb'); if (lb && lb.open) lb.close();
    document.querySelectorAll('main, footer, .hud').forEach(el => { el.inert = false; });
    root.classList.remove('lyr-open');
  }
  function swap(nodes) {
    REGIONS.forEach(sel => {
      const old = document.querySelector(sel), nw = nodes[sel];
      if (old && nw) old.replaceWith(nw);
      else if (!old && nw) { const m = document.querySelector('main'); if (m) m.after(nw); else document.body.appendChild(nw); }
      else if (old && !nw) old.remove();
    });
  }
  function headFrom(doc) {
    const get = (sel, attr) => { const el = doc.querySelector(sel); return el ? el.getAttribute(attr) : null; };
    return { title: doc.title, desc: get('meta[name="description"]', 'content'), canon: get('link[rel="canonical"]', 'href'), og: get('meta[property="og:title"]', 'content'), ogd: get('meta[property="og:description"]', 'content'), ogu: get('meta[property="og:url"]', 'content'), strip: (doc.querySelector('#readout .cg-tag strong') || {}).innerHTML };
  }
  function headNow() { return headFrom(document); }
  function setHead(h) {
    if (h.title) document.title = h.title;
    const set = (sel, attr, v) => { const el = document.querySelector(sel); if (el && v != null) el.setAttribute(attr, v); };
    set('meta[name="description"]', 'content', h.desc); set('link[rel="canonical"]', 'href', h.canon);
    set('meta[property="og:title"]', 'content', h.og); set('meta[property="og:description"]', 'content', h.ogd); set('meta[property="og:url"]', 'content', h.ogu);
    const st = document.querySelector('#readout .cg-tag strong');
    if (st && h.strip) { if (rSaved) { rSaved[1] = h.strip; lastKey = ''; } else st.innerHTML = h.strip; }
  }
  function markGuide(slug) {
    document.querySelectorAll('#guide .cg-chan').forEach(li => {
      const a = li.querySelector('a'), on = slugOf(a.href) === slug, tick = li.querySelector('.tick');
      li.classList.toggle('on', on);
      if (on) a.setAttribute('aria-current', 'page'); else a.removeAttribute('aria-current');
      if (tick) tick.textContent = on ? 'On air' : '';
      const lbl = (a.getAttribute('aria-label') || '').replace(/, on air$/, '');
      a.setAttribute('aria-label', on ? lbl + ', on air' : lbl);
    });
  }
  function loadScript(el) {
    return new Promise(res => {
      const s = document.createElement('script');
      if (el.dataset.rt) s.dataset.rt = el.dataset.rt;
      const src = el.getAttribute('src');
      if (src) { s.src = new URL(src, location.href).href; s.onload = s.onerror = () => res(); document.body.appendChild(s); }
      else { s.textContent = el.textContent; document.body.appendChild(s); res(); }
    });
  }
  async function pageScripts(doc) {
    for (const el of doc.querySelectorAll('script[data-rt]')) {
      const n = el.dataset.rt;
      if (loadedScripts.has(n) || ['boot', 'three', 'main', 'router', 'theme'].includes(n)) continue;
      loadedScripts.add(n);
      await loadScript(el);
    }
  }
  async function loadEngine(doc) {
    // bring in the frame pieces only the homepage has, then start the engine (it skips the intro for returning visitors)
    ['boot', 'strobe', 'gl'].forEach(id => { if (!document.getElementById(id)) { const n = doc.getElementById(id); if (n) document.body.prepend(document.adoptNode(n)); } });
    const br = document.querySelector('.hud-br');
    if (br && !document.getElementById('sound')) { const s = doc.getElementById('sound'); if (s) br.appendChild(document.adoptNode(s)); }
    document.querySelectorAll('#rail .ch, #dock .ch, #guideCh .ch').forEach(a => a.remove());
    try { sessionStorage.setItem('rt-in', '1'); } catch (e) {}
    for (const n of ['boot', 'three', 'main']) {
      if (loadedScripts.has(n) || (n === 'three' && window.THREE)) continue;
      const el = doc.querySelector(`script[data-rt="${n}"]`); if (!el) continue;
      loadedScripts.add(n);
      await loadScript(el);
    }
    root.classList.add('rt-engine');
    if (window.RTSyncSound) window.RTSyncSound();
  }
  function scrollFor(slug, u, y) {
    if (y != null) { scrollTo(0, y); return; }
    if (u.hash) {
      if (slug === '' && window.RTGo && window.RT_HASH_GO && window.RT_HASH_GO[u.hash] != null) { window.RTGo(window.RT_HASH_GO[u.hash]); return; }
      let el = null; try { el = document.querySelector(u.hash); } catch (e) {}
      if (el) { el.scrollIntoView({ block: 'start' }); return; }
    }
    scrollTo(0, 0);
  }
  function pageView() {
    try { if (window.gtag) window.gtag('event', 'page_view', { page_title: document.title, page_location: location.href, page_path: location.pathname }); } catch (e) {}
  }

  async function go(href, opt = {}) {
    const slug = slugOf(href); if (slug == null) { location.href = href; return; }
    const u = new URL(href, location.href);
    if (slug === cur && !opt.pop) {
      if (u.hash && u.hash !== location.hash) { history.pushState({ rt: 1, y: scrollY }, '', u.href); scrollFor(slug, u); }
      else scrollTo({ top: 0, behavior: reduce ? 'auto' : 'smooth' });
      return;
    }
    if (slug === cur) return;
    if (engineP) await engineP;
    const token = ++seq;
    const needDoc = !(slug === '' && home);
    const docP = needDoc ? fetchDoc(u.href) : Promise.resolve(null);
    const out = warpOut(opt.x, opt.y);
    let doc;
    try { doc = await docP; } catch (e) { location.href = href; return; }
    await out;
    if (token !== seq) return;
    busy = true;
    closeOverlays();
    // leave: keep the homepage alive in memory, tear down per-page bindings
    if (cur === '' && window.RTEnter) window.RTEnter();   // leaving during the intro: let it finish, or its scroll lock follows you
    if (cur === '' && window.RT_ENGINE) {
      home = { nodes: {}, head: headNow() };
      REGIONS.forEach(sel => { const n = document.querySelector(sel); if (n) home.nodes[sel] = n; });
    }
    window.RT.cleanups.splice(0).forEach(c => { try { c(); } catch (e) {} });
    if (cur === 'music/') unmountDeck();
    if (!opt.pop) history.pushState({ rt: 1, y: 0 }, '', u.href);
    // enter
    let nodes = {}, head;
    if (doc) { REGIONS.forEach(sel => { const n = doc.querySelector(sel); if (n) nodes[sel] = document.adoptNode(n); }); head = headFrom(doc); }
    else { nodes = home.nodes; head = home.head; }
    swap(nodes);
    document.body.classList.toggle('page', slug !== '');
    if (slug !== '') root.classList.remove('locked');   // inner pages never lock scrolling
    setHead(head); markGuide(slug);
    cur = slug;
    if (slug === '' && !window.RT_ENGINE) await loadEngine(doc);
    if (slug === 'music/') { if (window.RT_ENGINE) mountDeck(); else engineUnder(); }
    if (slug === '') dispatchEvent(new Event('resize'));   // the homepage re-measures itself after being away
    window.RT.inits.forEach(fn => window.RT.run(fn));
    if (doc && slug !== '') await pageScripts(doc);
    scrollFor(slug, u, opt.pop ? opt.y : null);
    const m = document.querySelector('main'); if (m) { m.tabIndex = -1; m.focus({ preventScroll: true }); }
    warpIn();
    pageView();
    busy = false;
  }
  window.RTNav = { go: href => go(href) };

  document.addEventListener('click', e => {
    if (e.defaultPrevented || e.button || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey) return;
    const a = e.target.closest('a[href]');
    if (!a || (a.target && a.target !== '_self') || a.hasAttribute('download') || slugOf(a.href) == null) return;
    e.preventDefault();
    go(a.href, { x: e.clientX || null, y: e.clientY || null });
  });
  const warm = e => { const a = e.target.closest && e.target.closest('a[href]'); if (a && !a.target) { const s = slugOf(a.href); if (s != null && s !== cur && !(s === '' && home)) fetchDoc(a.href).catch(() => {}); } };
  document.addEventListener('pointerover', warm, { passive: true });
  document.addEventListener('touchstart', warm, { passive: true });
  document.addEventListener('focusin', warm);
  addEventListener('popstate', e => {
    const slug = slugOf(location.href);
    if (slug == null || slug === cur) return;
    go(location.href, { pop: true, y: e.state && e.state.y });
  });
  let saveT = 0;
  addEventListener('scroll', () => {
    if (busy || saveT) return;
    saveT = setTimeout(() => { saveT = 0; if (!busy) history.replaceState({ ...(history.state || {}), rt: 1, y: scrollY }, ''); }, 400);
  }, { passive: true });

  /* ---- now playing: a mini player on desktop, the strip readout on phones ---- */
  const np = document.createElement('div');
  np.className = 'np'; np.id = 'np'; np.hidden = true;
  np.innerHTML = '<button type="button" class="np-disc" aria-label="Pause"><span class="np-rec" aria-hidden="true"></span></button>' +
    '<a class="np-tx" href="#"><small>Now playing</small><b></b></a><span class="np-t" aria-hidden="true"></span>';
  document.body.appendChild(np);
  const npDisc = np.querySelector('.np-disc'), npTx = np.querySelector('.np-tx'), npT = np.querySelector('.np-t');
  const strip = document.querySelector('.cg-strip'), readout = document.getElementById('readout');
  if (readout) {
    rDisc = document.createElement('span'); rDisc.className = 'cg-disc'; rDisc.hidden = true; rDisc.setAttribute('aria-hidden', 'true');
    readout.prepend(rDisc);
  }
  const state = () => {
    const d = window.RTDeck;
    if (d && d.playing()) return { src: 'deck', title: d.title(), on: true, t: d.time(), dur: d.dur ? d.dur(d.index()) : 0 };
    if (P.src) return { src: 'player', title: P.title, on: !P.audio.paused, t: P.audio.currentTime, dur: P.audio.duration };
    return null;
  };
  npDisc.addEventListener('click', () => {
    const s = state(); if (!s) return;
    if (s.src === 'deck') window.RTDeck.toggle(); else P.toggle();
  });
  setInterval(() => {
    const s = state();
    const show = !!s && (s.on || s.src === 'player');
    const key = show ? [s.src, s.title, s.on].join('|') : '';
    if (key !== lastKey) {
      lastKey = key;
      np.hidden = !show;
      document.body.classList.toggle('np-on', show);
      if (show) {
        np.classList.toggle('on', s.on);
        npTx.querySelector('b').textContent = s.title;
        npTx.querySelector('small').textContent = s.on ? (s.src === 'deck' ? 'On the deck' : 'Now playing') : 'Paused';
        npTx.setAttribute('href', new URL('music/', ROOT).href);
        npTx.setAttribute('aria-label', `${s.title}: open Music`);
        npDisc.setAttribute('aria-label', (s.on ? 'Pause ' : 'Play ') + s.title);
      }
      if (strip && readout) {
        const tag = readout.querySelector('.cg-tag');
        rSmall = tag && tag.querySelector('small'); rStrong = tag && tag.querySelector('strong');
        strip.classList.toggle('cg-playing', show);
        rDisc.hidden = !show; rDisc.classList.toggle('spin', show && s.on);
        if (rSmall && rStrong) {
          if (show) {
            if (rSaved == null) rSaved = [rSmall.textContent, rStrong.innerHTML];
            rSmall.textContent = (s.on ? 'Now playing' : 'Paused') + ' · ' + (rSaved[1].replace(/<[^>]+>/g, '').trim());
            rStrong.textContent = s.title;
          } else if (rSaved) { rSmall.textContent = rSaved[0]; rStrong.innerHTML = rSaved[1]; rSaved = null; }
        }
      }
    }
    if (show) npT.textContent = s.dur ? fmt(s.t) + ' / ' + fmt(s.dur) : fmt(s.t);
  }, 250);
  if (cur === 'music/') {
    const start = () => setTimeout(engineUnder, 60);
    if (document.readyState === 'complete') start(); else addEventListener('load', start, { once: true });
  }
})();
