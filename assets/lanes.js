// ---- four lanes: reveal, rail progress, lane filter ----
(() => {
  const tl = document.getElementById('tl'); if (!tl) return;
  const evs = [...tl.querySelectorAll('.ev')];
  if ('IntersectionObserver' in window) {
    const io = new IntersectionObserver(es => es.forEach(e => { if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); } }), { rootMargin: '0px 0px -12% 0px' });
    evs.forEach(el => io.observe(el));
  } else evs.forEach(el => el.classList.add('in'));
  let lastP = -1;
  const tick = () => {
    const r = tl.getBoundingClientRect(), vh = innerHeight;
    const p = Math.min(1, Math.max(0, (vh * 0.62 - r.top) / r.height));
    if (Math.abs(p - lastP) > 0.001) { lastP = p; tl.style.setProperty('--prog', p.toFixed(4)); }
    requestAnimationFrame(tick);
  };
  requestAnimationFrame(tick);
  const btns = [...document.querySelectorAll('.lane-filter button')];
  btns.forEach(b => b.addEventListener('click', () => {
    const lane = b.dataset.lane, on = lane === 'all' || b.getAttribute('aria-pressed') !== 'true' ? lane : 'all';
    btns.forEach(x => x.setAttribute('aria-pressed', x.dataset.lane === on ? 'true' : 'false'));
    tl.dataset.show = on;
    evs.forEach(el => el.classList.toggle('match', el.dataset.lane === on));
    try { if (window.gtag) window.gtag('event', 'lane_filter', { lane: on }); } catch (e) {}
  }));
})();
