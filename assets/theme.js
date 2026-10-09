/* site root, resolved from this script's own URL so pages at any depth find shared files */
window.RT_ROOT = new URL('../', document.currentScript.src).href;
window.rtUrl = p => new URL(p, window.RT_ROOT).href;
/* ---------- theme: one accent color (cyan / magenta / amber) drives the whole site ---------- */
window.THEME = (() => {
  const LIST = [
    { id: 'cyan', sig: [34, 211, 238], pulse: [224, 56, 143] },
    { id: 'magenta', sig: [255, 61, 184], pulse: [34, 211, 238] },
    { id: 'amber', sig: [255, 159, 28], pulse: [34, 211, 238] }
  ];
  let idx = 0;
  try { const i = LIST.findIndex(t => t.id === localStorage.getItem('rt-theme')); if (i >= 0) idx = i; } catch (e) {}
  const cur = { s: LIST[idx].sig.slice(), p: LIST[idx].pulse.slice() };
  const subs = [], settles = [], root = document.documentElement;
  const T = { LIST, rgb: '', hex: '', c: [0, 0, 0], p: [0, 0, 0], ver: 0 };
  const mixW = (a, k) => a.map(v => Math.round(v + (255 - v) * k));
  T.tint = k => mixW(cur.s, k).join(',');
  T.dim = k => cur.s.map(v => Math.round(v * k));
  function apply() {
    const s = cur.s.map(Math.round), p = cur.p.map(Math.round);
    T.rgb = s.join(','); T.hex = '#' + s.map(v => v.toString(16).padStart(2, '0')).join('');
    T.c = cur.s.map(v => v / 255); T.p = cur.p.map(v => v / 255); T.ver++;
    root.style.setProperty('--sig-rgb', T.rgb); root.style.setProperty('--pulse-rgb', p.join(','));
    root.style.setProperty('--sig-hot', mixW(cur.s, 0.86).join(','));
    subs.forEach(f => { try { f(T); } catch (e) {} });
  }
  T.on = f => { subs.push(f); try { f(T); } catch (e) {} };
  T.onSettle = f => settles.push(f);
  T.index = () => idx;
  function marks() {
    root.dataset.theme = LIST[idx].id;
    document.querySelectorAll('#themes button').forEach((b, i) => b.setAttribute('aria-checked', i === idx ? 'true' : 'false'));
  }
  let anim = 0;
  T.set = i => {
    i = ((i % LIST.length) + LIST.length) % LIST.length; if (i === idx) return;
    idx = i; try { localStorage.setItem('rt-theme', LIST[i].id); } catch (e) {}
    try { if (window.gtag) window.gtag('event', 'theme_change', { theme: LIST[i].id }); } catch (e) {}
    marks();
    const from = { s: cur.s.slice(), p: cur.p.slice() }, to = LIST[i], t0 = performance.now(), id = ++anim;
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches, DUR = reduce ? 1 : 700;
    const step = now => {
      if (id !== anim) return;
      const t = Math.min(1, (now - t0) / DUR), e = t < .5 ? 4 * t * t * t : 1 - Math.pow(-2 * t + 2, 3) / 2;
      for (let k = 0; k < 3; k++) { cur.s[k] = from.s[k] + (to.sig[k] - from.s[k]) * e; cur.p[k] = from.p[k] + (to.pulse[k] - from.p[k]) * e; }
      apply();
      if (t < 1) requestAnimationFrame(step); else settles.forEach(f => { try { f(T); } catch (e) {} });
    };
    requestAnimationFrame(step);
  };
  apply();
  document.addEventListener('DOMContentLoaded', () => {
    marks();
    document.querySelectorAll('#themes button').forEach((b, i) => b.addEventListener('click', () => T.set(i === idx && matchMedia('(max-width:640px)').matches ? idx + 1 : i)));
    const g = document.getElementById('themes');
    if (g) g.addEventListener('keydown', e => {
      const d = e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? -1 : 0;
      if (d) { e.preventDefault(); T.set(idx + d); g.querySelectorAll('button')[idx].focus(); }
    });
  });
  return T;
})();
