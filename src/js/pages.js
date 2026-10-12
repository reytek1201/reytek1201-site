/* ---------- door pages: release player (Music) and launch countdown (Gaming) ---------- */
(() => {
  const fmt = s => { s = Math.max(0, Math.floor(s || 0)); return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); };
  const track = (name, params) => { try { if (window.gtag) window.gtag('event', name, params); } catch (e) {} };

  /* Music: each release row plays, pauses and seeks. With the turntable on the page, the rows play through it;
     before it has loaded (or without it) they use the site-wide player. Either one keeps going across pages. */
  window.RT.onPage(() => {
  const list = document.getElementById('relList');
  if (!list) return;
  {
    const P = window.RTPlayer, audio = P.audio;
    const ac = new AbortController(), on = { signal: ac.signal };
    const rows = [...list.querySelectorAll('.rel')];
    const srcOf = row => rtUrl(row.dataset.src);
    const queue = rows.map(r => ({ src: srcOf(r), title: r.dataset.title }));
    // the source: whichever of the turntable or the plain player is sounding (the turntable wins when idle)
    const D = () => window.RTDeck || null;
    const deck = () => { const d = D(); return d && d.mounted && d.mounted() ? d : null; };
    const idx = row => { const d = D(); return d && d.find ? d.find(srcOf(row)) : -1; };
    const onDeck = () => { const d = D(); return !!d && (d.playing() || (!!deck() && (audio.paused || !P.src))); };
    const S = {
      row: () => {
        if (onDeck()) { const i = D().index(); return i >= 0 ? rows.find(r => idx(r) === i) || null : null; }
        return P.src ? rows.find(r => srcOf(r) === P.src) || null : null;
      },
      paused: () => onDeck() ? !D().playing() : audio.paused,
      time: () => onDeck() ? D().time() : (audio.currentTime || 0),
      dur: row => onDeck() ? D().dur(idx(row)) : (audio.duration || +row.dataset.dur),
      pause: () => { if (onDeck()) D().stop(); else audio.pause(); },
      seek: (row, k) => {
        const d = deck();
        if (d && idx(row) >= 0) { follow(row); d.seek(idx(row), k); return; }
        if (cur !== row) { play(row); audio.addEventListener('loadedmetadata', () => { audio.currentTime = k * audio.duration; }, { once: true, signal: ac.signal }); }
        else if (audio.duration) audio.currentTime = k * audio.duration;
      }
    };
    let cur = S.row();
    const setRow = (row, on) => {
      row.classList.toggle('playing', on);
      const b = row.querySelector('.rel-play');
      b.setAttribute('aria-pressed', on ? 'true' : 'false');
      b.setAttribute('aria-label', (on ? 'Pause ' : 'Play ') + row.dataset.title);
    };
    const panel = document.getElementById('lyrics');
    let book = {};
    try { book = JSON.parse((document.getElementById('lyrData') || {}).textContent || '{}'); } catch (e) {}
    let lyrRow = null, lyrBtn = null, song = null;
    const still = matchMedia('(prefers-reduced-motion: reduce)');
    const $ = id => document.getElementById(id);
    let shown = '', raf = 0, words = [];

    /* beat clock: index of the last beat at or before t, plus how far we are toward the next one */
    const beatAt = t => {
      const b = song.beats, gap = (b[b.length - 1] - b[0]) / (b.length - 1);
      if (t < b[0]) { const k = Math.floor((t - b[0]) / gap); return { i: k, f: (t - b[0]) / gap - k, gap }; }
      let lo = 0, hi = b.length - 1;
      if (t >= b[hi]) { const k = (t - b[hi]) / gap; return { i: hi + Math.floor(k), f: k - Math.floor(k), gap }; }
      while (hi - lo > 1) { const m = (lo + hi) >> 1; if (b[m] <= t) lo = m; else hi = m; }
      return { i: lo, f: (t - b[lo]) / (b[lo + 1] - b[lo]), gap: b[lo + 1] - b[lo] };
    };
    const rgb = s => s.split(',').map(Number);
    const sectionAt = (t, gap) => {
      const S = song.sections;
      let i = 0;
      for (let n = 0; n < S.length; n++) if (S[n].t - gap <= t) i = n;
      const s = S[i], from = S[i - 1];
      const k = from ? Math.min(1, Math.max(0, (t - (s.t - gap)) / gap)) : 1;
      const a = rgb(from ? from.rgb : s.rgb), c = rgb(s.rgb);
      const lift = from ? from.lift + (s.lift - from.lift) * k : s.lift;
      return { name: s.name, lc: a.map((v, j) => Math.round(v + (c[j] - v) * k)).join(','), lift };
    };
    const lineView = t => {
      const L = song.lines;
      let i = -1;
      for (let n = 0; n < L.length; n++) if (L[n].t <= t) i = n;
      if (i < 0) return { prev: null, now: L[0], next: L[1] || null };
      const line = L[i], nxt = L[i + 1] || null;
      const end = line.end != null ? line.end : (nxt ? nxt.t : line.w[line.w.length - 1][2] + 2);
      if (t < end) return { prev: L[i - 1] || null, now: line, next: nxt };
      return { prev: line, now: nxt, next: L[i + 2] || null };
    };
    const setLine = view => {
      $('lyrPrev').textContent = view.prev ? view.prev.text : '';
      $('lyrNext').textContent = view.next ? view.next.text : '';
      const now = $('lyrNow');
      now.textContent = '';
      words = [];
      if (view.now) view.now.w.forEach(([txt, a, b], n) => {
        if (n) now.append(' ');
        const s = document.createElement('span');
        s.className = 'lw'; s.textContent = txt;
        now.append(s); words.push([s, a, b]);
      });
      now.classList.remove('in');
      if (view.now) { void now.offsetWidth; now.classList.add('in'); }
    };
    const frame = () => {
      if (!panel || panel.hidden || cur !== lyrRow || !song) return;
      const t = S.time();
      const view = lineView(t);
      const key = (view.prev ? view.prev.t : '') + '|' + (view.now ? view.now.t : '');
      if (key !== shown) { shown = key; setLine(view); }
      words.forEach(([s, a, b]) => {
        const f = Math.min(1, Math.max(0, (t - a) / (b - a)));
        s.style.setProperty('--f', f.toFixed(3));
        s.classList.toggle('on', f > 0 && f < 1);
      });
      let near = 0;
      if (view.next) {
        const raw = 1 - Math.min(1, Math.max(0, (view.next.t - t) / 3.6));
        near = raw * raw;
      }
      $('lyrNext').style.setProperty('--near', near.toFixed(3));
      const beat = beatAt(t);
      const sec = sectionAt(t, beat.gap);
      const pos = (((beat.i - song.downbeat) % 4) + 4) % 4;
      const hit = pos === 0 ? 1 : .55;
      const paused = S.paused();
      const pulse = still.matches || paused ? 0 : Math.exp(-beat.f * 4.5) * hit * (.35 + .65 * sec.lift);
      panel.style.setProperty('--lc', sec.lc);
      panel.style.setProperty('--pulse', pulse.toFixed(3));
      panel.querySelector('.lyr-trail').style.setProperty('--ang', ((pos + beat.f) * 90 - 320).toFixed(1) + 'deg');
      panel.querySelector('.lyr-beat').dataset.b = paused ? '' : pos;
      if ($('lyrSec').textContent !== sec.name) $('lyrSec').textContent = sec.name;
    };
    const others = () => document.querySelectorAll('main, footer, .hud, .rail, .cg-strip');
    const closeLyrics = focus => {
      if (!panel || panel.hidden) return;
      panel.hidden = true;
      document.documentElement.classList.remove('lyr-open');
      others().forEach(el => { el.inert = false; });
      if (lyrBtn) lyrBtn.setAttribute('aria-expanded', 'false');
      cancelAnimationFrame(raf);
      if (focus && lyrBtn) lyrBtn.focus();
    };
    const openLyrics = row => {
      if (!panel || !book[row.dataset.title]) return;
      lyrRow = row; lyrBtn = row.querySelector('.rel-lyrics'); song = book[row.dataset.title];
      $('lyrTitle').textContent = row.dataset.title;
      if (cur !== lyrRow || S.paused()) play(lyrRow);
      const art = lyrRow.querySelector('.rel-label') || lyrRow.querySelector('.rel-cover');
      $('lyrArt').src = art.currentSrc || art.src;
      panel.querySelector('.lyr-disc').classList.toggle('round', art.classList.contains('rel-label'));
      panel.hidden = false;
      panel.classList.toggle('spin', !S.paused());
      document.documentElement.classList.add('lyr-open');
      others().forEach(el => { el.inert = true; });
      lyrBtn.setAttribute('aria-expanded', 'true');
      discLabel();
      shown = '';
      frame();
      panel.querySelector('.lyr-x').focus();
    };
    const follow = row => {   // the player moved on (a new pick, or the next track after one ends)
      if (cur && cur !== row) { setRow(cur, false); cur.style.setProperty('--p', 0); cur.querySelector('.rel-t').textContent = fmt(+cur.dataset.dur); }
      lastPaused = null;
      if (lyrRow && row !== lyrRow) closeLyrics(false);
      cur = row;
    };
    const play = row => {
      if (cur !== row) track('play_track', { track: row.dataset.title, from: 'music_page' });
      follow(row);
      const d = deck();
      if (d && idx(row) >= 0) d.play(idx(row)); else P.play(srcOf(row), row.dataset.title, queue);
    };
    const toggle = row => (cur === row && !S.paused()) ? S.pause() : play(row);
    rows.forEach(row => {
      row.querySelector('.rel-play').addEventListener('click', () => toggle(row));
      const wave = row.querySelector('.rel-wave');
      wave.addEventListener('click', e => {
        const r = wave.getBoundingClientRect(), k = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width));
        if (cur !== row) track('play_track', { track: row.dataset.title, from: 'music_page' });
        S.seek(row, k);
      });
    });
    list.querySelectorAll('.rel-lyrics').forEach(b => b.addEventListener('click', () => {
      const row = b.closest('.rel');
      if (panel && !panel.hidden && lyrRow === row) closeLyrics(true); else openLyrics(row);
    }));
    const discLabel = () => {
      if (!panel || !lyrRow) return;
      panel.querySelector('.lyr-disc').setAttribute('aria-label', (cur === lyrRow && !S.paused() ? 'Pause ' : 'Play ') + lyrRow.dataset.title);
    };
    if (panel) {
      panel.querySelector('.lyr-x').addEventListener('click', () => closeLyrics(true));
      panel.querySelector('.lyr-disc').addEventListener('click', () => toggle(lyrRow));
      panel.addEventListener('click', e => { if (e.target === panel) closeLyrics(true); });
      document.addEventListener('keydown', e => { if (e.key === 'Escape' && !panel.hidden) closeLyrics(true); }, on);
    }
    // one watcher follows whichever source is playing: rows light up, progress moves, lyrics stay in time
    let lastPaused = null, lastProg = 0;
    const progress = () => {
      if (!cur) return;
      const d = S.dur(cur), t = S.time();
      if (!d) return;
      cur.style.setProperty('--p', Math.min(1, t / d).toFixed(4));
      cur.querySelector('.rel-t').textContent = fmt(t) + ' / ' + fmt(d);
    };
    const watch = now => {
      raf = requestAnimationFrame(watch);
      const row = S.row(), paused = S.paused();
      if (row && row !== cur) follow(row);
      if (cur && paused !== lastPaused) {
        lastPaused = paused;
        setRow(cur, !paused);
        if (panel) panel.classList.toggle('spin', !paused);
        discLabel();
      }
      if (cur && row === cur && now - lastProg > 200) { lastProg = now; progress(); }
      if (panel && !panel.hidden) frame();
    };
    raf = requestAnimationFrame(watch);
    return () => { closeLyrics(false); cancelAnimationFrame(raf); ac.abort(); };
  }
  });

  /* Projects: the ticket rail. Tickets sway as you sweep past; pull one and it prints out in full */
  window.RT.onPage(() => {
  const rail = document.getElementById('trRail');
  if (!rail) return;
  {
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const ac = new AbortController(), on = { signal: ac.signal };
    const root = document.documentElement;
    const tks = [...rail.querySelectorAll('.tr-tk')];
    let alive = true;

    // days until POE2 1.0
    const days = Math.max(0, Math.ceil((new Date('2026-12-11T00:00:00-05:00') - Date.now()) / 864e5));
    document.querySelectorAll('[data-days]').forEach(el => { el.textContent = days; });

    // long names shrink to fit their ticket
    const fit = () => tks.forEach(li => {
      const n = li.querySelector('.tr-name'); n.style.fontSize = '';
      let f = parseFloat(getComputedStyle(n).fontSize);
      while (n.scrollWidth > n.clientWidth + 1 && f > 12) { f -= .5; n.style.fontSize = f + 'px'; }
    });
    (document.fonts && document.fonts.ready ? document.fonts.ready : Promise.resolve()).then(() => { if (alive) fit(); });
    addEventListener('resize', fit, on);

    // each ticket is a little pendulum hanging from its clip
    const sw = tks.map((el, i) => ({ el, a: (i % 2 ? 1 : -1) * (1 + (i * 37 % 5) * .35), v: 0, rest: (i % 2 ? 1 : -1) * (.6 + (i * 53 % 4) * .4), ph: i * 1.7 }));
    let lastX = null, lastT = 0;
    addEventListener('pointermove', e => {
      if (reduce || e.pointerType !== 'mouse') return;
      const now = performance.now(), dx = lastX == null ? 0 : e.clientX - lastX, dt = Math.max(8, now - lastT);
      lastX = e.clientX; lastT = now;
      const vx = dx / dt;
      sw.forEach(t => {
        const r = t.el.getBoundingClientRect();
        if (e.clientY < r.top - 40 || e.clientY > r.bottom + 20) return;
        const d = Math.abs(e.clientX - (r.left + r.width / 2));
        if (d < r.width * .75) t.v += vx * 1.6 * (1 - d / (r.width * .75));
      });
    }, { passive: true, signal: ac.signal });
    // on phones the rail scrolls: swiping it swings the tickets
    let lastS = rail.scrollLeft;
    rail.addEventListener('scroll', () => {
      const d = rail.scrollLeft - lastS; lastS = rail.scrollLeft;
      if (!reduce) sw.forEach(t => { t.v -= Math.max(-30, Math.min(30, d * .9)); });
    }, { passive: true, signal: ac.signal });
    let prev = performance.now(), raf = 0;
    const frame = now => {
      if (!alive) return;
      raf = requestAnimationFrame(frame);
      const dt = Math.min(.05, (now - prev) / 1000); prev = now;
      sw.forEach(t => {
        const idle = reduce ? 0 : Math.sin(now / 1000 * .9 + t.ph) * .45;
        t.v += (-(t.a - t.rest - idle) * 38 - t.v * 3.2) * dt; t.a += t.v * dt;
        t.a = Math.max(-16, Math.min(16, t.a));
        t.el.style.transform = `rotate(${t.a.toFixed(2)}deg)`;
      });
    };
    raf = requestAnimationFrame(frame);

    // the pulled ticket lives outside the page content, above everything
    const veil = document.createElement('div'); veil.className = 'tr-veil';
    const dlg = document.createElement('div'); dlg.className = 'tr-open'; dlg.setAttribute('role', 'dialog'); dlg.setAttribute('aria-modal', 'true'); dlg.setAttribute('aria-labelledby', 'trOName');
    const paper = document.createElement('div'); paper.className = 'tr-paper'; dlg.appendChild(paper);
    document.body.append(veil, dlg);
    const others = () => document.querySelectorAll('main, footer, .hud, .rail, .cg-strip');
    let cur = -1, opener = null;
    const track = name => { try { if (window.gtag) window.gtag('event', 'open_project', { project: name }); } catch (e) {} };
    const open = i => {
      if (cur >= 0) return;
      cur = i; opener = tks[i].querySelector('.tr-slip');
      const li = tks[i];
      dlg.style.setProperty('--pc', li.style.getPropertyValue('--pc'));
      paper.innerHTML = '<button class="tr-x" type="button" aria-label="Back on the rail">×</button>' + li.querySelector('.tr-full').innerHTML;
      paper.querySelectorAll('.pr').forEach((el, n) => el.style.setProperty('--n', n));
      const h = paper.querySelector('.tr-oname'); if (h) h.id = 'trOName';
      paper.querySelector('.tr-x').addEventListener('click', close);
      track(li.dataset.tk);
      const from = opener.getBoundingClientRect();
      dlg.classList.add('on'); paper.scrollTop = 0;
      const to = dlg.getBoundingClientRect();
      veil.classList.add('on'); root.classList.add('tr-is-open');
      others().forEach(el => { el.inert = true; });
      const done = () => { dlg.style.visibility = ''; dlg.classList.remove('printing'); void dlg.offsetWidth; if (!reduce) dlg.classList.add('printing'); paper.querySelector('.tr-x').focus({ preventScroll: true }); };
      opener.classList.add('gone');
      if (reduce) { done(); return; }
      // the small ticket drops off its clip and flies to where the full one sits
      const fly = opener.cloneNode(true); fly.classList.remove('gone'); fly.classList.add('tr-flyer'); fly.removeAttribute('aria-label');
      Object.assign(fly.style, { left: from.left + 'px', top: from.top + 'px', width: from.width + 'px', margin: 0 });
      fly.style.setProperty('--pc', li.style.getPropertyValue('--pc'));
      dlg.style.visibility = 'hidden'; document.body.appendChild(fly);
      const sx = to.width / from.width, dx = to.left + to.width / 2 - (from.left + from.width / 2), dy = to.top - from.top;
      fly.animate([
        { transform: `rotate(${sw[i].a}deg)` },
        { transform: `translate(0, 26px) rotate(${sw[i].a * 1.6}deg)`, offset: .22 },
        { transform: `translate(${dx}px, ${dy}px) scale(${sx}) rotate(0deg)`, opacity: .35 }
      ], { duration: 520, easing: 'cubic-bezier(.5,0,.15,1)' }).onfinish = () => { fly.remove(); if (cur === i) done(); };
    };
    const close = (quiet) => {
      if (cur < 0) return;
      const back = opener, i = cur;
      dlg.classList.remove('on', 'printing'); veil.classList.remove('on'); root.classList.remove('tr-is-open');
      others().forEach(el => { el.inert = false; });
      back.classList.remove('gone'); cur = -1;
      if (quiet === true) return;
      if (!reduce) back.animate([{ transform: 'translateY(-60px)', opacity: 0 }, { transform: 'translateY(8px)', opacity: 1, offset: .7 }, { transform: 'translateY(0)' }], { duration: 420, easing: 'ease-out' });
      sw[i].v += 40;   // clipping it back makes it swing
      back.focus({ preventScroll: true });
    };
    tks.forEach((li, i) => li.querySelector('.tr-slip').addEventListener('click', () => open(i), on));
    veil.addEventListener('click', () => close(), on);
    document.addEventListener('keydown', e => {
      if (cur < 0) return;
      if (e.key === 'Escape') { e.preventDefault(); close(); return; }
      if (e.key === 'Tab') {   // keep focus inside the open ticket
        const f = [...paper.querySelectorAll('button,a[href]')]; if (!f.length) return;
        const a = f[0], z = f[f.length - 1];
        if (e.shiftKey && document.activeElement === a) { e.preventDefault(); z.focus(); }
        else if (!e.shiftKey && document.activeElement === z) { e.preventDefault(); a.focus(); }
      }
    }, on);
    return () => { alive = false; cancelAnimationFrame(raf); close(true); ac.abort(); veil.remove(); dlg.remove(); document.querySelectorAll('.tr-flyer').forEach(n => n.remove()); };
  }
  });

  /* Gaming: countdown to the Path of Exile 2 1.0 launch */
  window.RT.onPage(() => {
  const cd = document.getElementById('countdown');
  if (!cd) return;
  {
    const to = new Date(cd.dataset.to).getTime(), u = {};
    cd.querySelectorAll('[data-u]').forEach(el => { u[el.dataset.u] = el; });
    const pad = n => String(n).padStart(2, '0');
    const tick = () => {
      let s = Math.max(0, Math.floor((to - Date.now()) / 1000));
      if (s === 0) { cd.classList.add('done'); cd.querySelector('.cd-lbl').textContent = 'Path of Exile 2 · 1.0 is live'; }
      const d = Math.floor(s / 86400); s -= d * 86400;
      const h = Math.floor(s / 3600); s -= h * 3600;
      const m = Math.floor(s / 60); s -= m * 60;
      u.d.textContent = d; u.h.textContent = pad(h); u.m.textContent = pad(m); u.s.textContent = pad(s);
    };
    tick(); const iv = setInterval(tick, 1000);
    return () => clearInterval(iv);
  }
  });
})();
