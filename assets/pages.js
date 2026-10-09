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
    const play = row => {
      if (cur && cur !== row) { setRow(cur, false); cur.style.setProperty('--p', 0); cur.querySelector('.rel-t').textContent = fmt(+cur.dataset.dur); }
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
    audio.addEventListener('play', () => cur && setRow(cur, true));
    audio.addEventListener('pause', () => cur && setRow(cur, false));
    audio.addEventListener('timeupdate', () => {
      if (!cur || !audio.duration) return;
      cur.style.setProperty('--p', (audio.currentTime / audio.duration).toFixed(4));
      cur.querySelector('.rel-t').textContent = fmt(audio.currentTime) + ' / ' + fmt(audio.duration);
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
