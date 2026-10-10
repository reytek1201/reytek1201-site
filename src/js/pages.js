/* ---------- door pages: release player (Music) and launch countdown (Gaming) ---------- */
(() => {
  const fmt = s => { s = Math.max(0, Math.floor(s || 0)); return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); };
  const track = (name, params) => { try { if (window.gtag) window.gtag('event', name, params); } catch (e) {} };

  /* Music: one shared audio element; each release row plays, pauses and seeks on its waveform */
  const list = document.getElementById('relList');
  if (list) {
    const audio = new Audio(); audio.preload = 'none';
    const rows = [...list.querySelectorAll('.rel')];
    let cur = null;
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
      const t = audio.currentTime || 0;
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
      const pulse = still.matches || audio.paused ? 0 : Math.exp(-beat.f * 4.5) * hit * (.35 + .65 * sec.lift);
      panel.style.setProperty('--lc', sec.lc);
      panel.style.setProperty('--pulse', pulse.toFixed(3));
      panel.querySelector('.lyr-trail').style.setProperty('--ang', ((pos + beat.f) * 90 - 320).toFixed(1) + 'deg');
      panel.querySelector('.lyr-beat').dataset.b = audio.paused ? '' : pos;
      if ($('lyrSec').textContent !== sec.name) $('lyrSec').textContent = sec.name;
    };
    const sync = () => frame();
    const arm = () => {
      cancelAnimationFrame(raf);
      const loop = () => { if (!panel || panel.hidden) return; frame(); if (!audio.paused) raf = requestAnimationFrame(loop); };
      raf = requestAnimationFrame(loop);
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
      if (cur !== lyrRow || audio.paused) play(lyrRow);
      const art = lyrRow.querySelector('.rel-label') || lyrRow.querySelector('.rel-cover');
      $('lyrArt').src = art.currentSrc || art.src;
      panel.querySelector('.lyr-disc').classList.toggle('round', art.classList.contains('rel-label'));
      panel.hidden = false;
      panel.classList.toggle('spin', !audio.paused);
      document.documentElement.classList.add('lyr-open');
      others().forEach(el => { el.inert = true; });
      lyrBtn.setAttribute('aria-expanded', 'true');
      discLabel();
      shown = '';
      frame();
      arm();
      panel.querySelector('.lyr-x').focus();
    };
    const play = row => {
      if (cur && cur !== row) { setRow(cur, false); cur.style.setProperty('--p', 0); cur.querySelector('.rel-t').textContent = fmt(+cur.dataset.dur); }
      if (lyrRow && row !== lyrRow) closeLyrics(false);
      if (cur !== row) { cur = row; audio.src = rtUrl(row.dataset.src); track('play_track', { track: row.dataset.title, from: 'music_page' }); }
      audio.play().catch(() => {});
    };
    rows.forEach(row => {
      row.querySelector('.rel-play').addEventListener('click', () => (cur === row && !audio.paused) ? audio.pause() : play(row));
      const wave = row.querySelector('.rel-wave');
      wave.addEventListener('click', e => {
        const r = wave.getBoundingClientRect(), k = Math.min(1, Math.max(0, (e.clientX - r.left) / r.width));
        if (cur !== row) { play(row); audio.addEventListener('loadedmetadata', () => { audio.currentTime = k * audio.duration; }, { once: true }); }
        else if (audio.duration) audio.currentTime = k * audio.duration;
      });
    });
    list.querySelectorAll('.rel-lyrics').forEach(b => b.addEventListener('click', () => {
      const row = b.closest('.rel');
      if (panel && !panel.hidden && lyrRow === row) closeLyrics(true); else openLyrics(row);
    }));
    const discLabel = () => {
      if (!panel || !lyrRow) return;
      panel.querySelector('.lyr-disc').setAttribute('aria-label', (cur === lyrRow && !audio.paused ? 'Pause ' : 'Play ') + lyrRow.dataset.title);
    };
    if (panel) {
      panel.querySelector('.lyr-x').addEventListener('click', () => closeLyrics(true));
      panel.querySelector('.lyr-disc').addEventListener('click', () => (cur === lyrRow && !audio.paused) ? audio.pause() : play(lyrRow));
      panel.addEventListener('click', e => { if (e.target === panel) closeLyrics(true); });
      document.addEventListener('keydown', e => { if (e.key === 'Escape' && !panel.hidden) closeLyrics(true); });
    }
    audio.addEventListener('play', () => { if (cur) setRow(cur, true); if (panel) panel.classList.add('spin'); discLabel(); arm(); });
    audio.addEventListener('pause', () => { if (cur) setRow(cur, false); if (panel) panel.classList.remove('spin'); discLabel(); frame(); });
    audio.addEventListener('seeked', () => { shown = ''; sync(); });
    audio.addEventListener('timeupdate', () => {
      if (!cur || !audio.duration) return;
      cur.style.setProperty('--p', (audio.currentTime / audio.duration).toFixed(4));
      cur.querySelector('.rel-t').textContent = fmt(audio.currentTime) + ' / ' + fmt(audio.duration);
      sync();
    });
    audio.addEventListener('ended', () => { const i = rows.indexOf(cur); if (i >= 0 && i < rows.length - 1) play(rows[i + 1]); else if (cur) setRow(cur, false); });
  }

  /* Gaming: countdown to the Path of Exile 2 1.0 launch */
  const cd = document.getElementById('countdown');
  if (cd) {
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
    tick(); setInterval(tick, 1000);
  }
})();
