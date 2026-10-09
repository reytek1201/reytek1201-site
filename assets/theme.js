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
    document.querySelectorAll('#themes button, .cg-themes button').forEach(b => b.setAttribute('aria-checked', +b.dataset.t === idx ? 'true' : 'false'));
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
    document.querySelectorAll('.cg-themes button').forEach(b => b.addEventListener('click', () => T.set(+b.dataset.t)));
    document.querySelectorAll('#themes, .cg-themes').forEach(g => g.addEventListener('keydown', e => {
      const d = e.key === 'ArrowRight' || e.key === 'ArrowDown' ? 1 : e.key === 'ArrowLeft' || e.key === 'ArrowUp' ? -1 : 0;
      if (d) { e.preventDefault(); T.set(idx + d); g.querySelectorAll('button')[idx].focus(); }
    }));
    guide();
  });

  /* channel guide (phones): the strip's key opens a full-screen list of the six channels */
  function guide() {
    const cg = document.getElementById('guide'), key = document.getElementById('guideKey');
    if (!cg || !key) return;
    const body = document.body, st = document.getElementById('guideStatic');
    const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
    const names = [...cg.querySelectorAll('.cg-chan .name b')];
    names.forEach(b => { b.dataset.name = b.textContent; });
    const isOpen = () => body.classList.contains('cg-open');
    const set = on => {
      if (on === isOpen()) return;
      body.classList.toggle('cg-open', on);
      key.setAttribute('aria-expanded', on ? 'true' : 'false');
      key.setAttribute('aria-label', on ? 'Close the channel guide' : 'Open the channel guide');
      document.querySelectorAll('main, footer, .hud').forEach(el => { el.inert = on; });
      if (!on) { key.focus({ preventScroll: true }); return; }
      if (window.rtScramble && !reduce) names.forEach((b, i) => {
        b.textContent = b.dataset.name.replace(/\S/g, ' ');
        setTimeout(() => window.rtScramble(b, b.dataset.name), i * 40);
      });
      if (window.rtShock) {
        const r = key.getBoundingClientRect();
        window.rtShock((r.left + r.width / 2) / innerWidth * 2 - 1, -((r.top + r.height / 2) / innerHeight * 2 - 1));
      }
      const here = cg.querySelector('.cg-chan a[aria-current="page"]') || cg.querySelector('.cg-chan a');
      setTimeout(() => here.focus({ preventScroll: true }), 60);
    };
    key.addEventListener('click', () => set(!isOpen()));
    const ro = document.getElementById('readout');
    if (ro) ro.addEventListener('click', () => set(true));
    cg.addEventListener('click', e => {
      const a = e.target.closest('.cg-chan a');
      if (!a || e.metaKey || e.ctrlKey || e.shiftKey || e.altKey || e.button) return;
      e.preventDefault();
      if (st && !reduce) { st.classList.remove('go'); void st.offsetWidth; st.classList.add('go'); }
      const go = () => { set(false); if (a.getAttribute('aria-current') !== 'page') location.href = a.href; };
      if (reduce) go(); else setTimeout(go, 160);
    });
    document.addEventListener('keydown', e => {
      if (!isOpen()) return;
      if (e.key === 'Escape') { e.preventDefault(); set(false); return; }
      if (e.key !== 'Tab') return;
      const list = [...cg.querySelectorAll('a[href], button'), key], i = list.indexOf(document.activeElement);
      if (e.shiftKey && i <= 0) { e.preventDefault(); list[list.length - 1].focus(); }
      else if (!e.shiftKey && (i === -1 || i === list.length - 1)) { e.preventDefault(); list[0].focus(); }
    });
    matchMedia('(max-width:820px)').addEventListener('change', e => { if (!e.matches) set(false); });
    const snd = document.getElementById('sound'), gs = document.getElementById('guideSound');
    if (snd && gs) {
      const sync = () => { const on = snd.getAttribute('aria-pressed') === 'true'; gs.setAttribute('aria-pressed', on ? 'true' : 'false'); gs.textContent = on ? 'Sound on' : 'Sound off'; };
      gs.addEventListener('click', () => snd.click());
      new MutationObserver(sync).observe(snd, { attributes: true, attributeFilter: ['aria-pressed'] });
      sync();
    }
  }
  return T;
})();
