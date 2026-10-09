/* ---------- page shell: the frame every inner page shares (cursor, channels, buttons) ---------- */
/* The homepage runs the full engine in main.js; this is the light version for pages like /origin/. */
(() => {
  const $ = s => document.querySelector(s);
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  const fine = matchMedia('(pointer:fine)').matches;
  const clamp = (v, a, b) => Math.min(b, Math.max(a, v));
  const GLYPHS = '#/\\=+X01<>*%';
  document.body.classList.add('lit', 'entered', 'page');
  try { sessionStorage.setItem('rt-in', '1'); } catch (e) {}

  /* cursor: the same ring and dot as the homepage */
  const cur = $('#cur'), dot = $('#dot');
  if (fine && cur && dot) {
    document.body.classList.add('has-cursor');
    let px = innerWidth / 2, py = innerHeight / 2, cx = px, cy = py;
    addEventListener('pointermove', e => {
      px = e.clientX; py = e.clientY; dot.style.transform = `translate(${px}px,${py}px)`;
      if (e.pointerType === 'mouse') { cur.classList.add('on'); dot.classList.add('on'); }
    }, { passive: true });
    document.addEventListener('pointerleave', () => { cur.classList.remove('on'); dot.classList.remove('on'); });
    document.addEventListener('pointerover', e => cur.classList.toggle('hot', !!e.target.closest('a,button,input,.ev-media img,[data-zoom] img')));
    let lastT = performance.now();
    const tick = now => {
      const k = 1 - Math.exp(-Math.max(0, Math.min(0.05, (now - lastT) / 1000)) * 32); lastT = now;
      cx += (px - cx) * k; cy += (py - cy) * k;
      cur.style.transform = `translate(${cx}px,${cy}px)`; dot.style.transform = `translate(${px}px,${py}px)`;
      requestAnimationFrame(tick);
    };
    requestAnimationFrame(tick);
  }

  /* channels: social icons in the side rail and the footer */
  const CHANNELS = [
    { name: 'SoundCloud', handle: 'reytek1201', verb: 'Listen', url: 'https://soundcloud.com/reytek1201',
      g: '<path d="M2.5 15.5v-2.5"/><path d="M5 16.5V11"/><path d="M7.5 16.5V9"/><path d="M10 16.5V7.5"/><path d="M12.5 16.5V6.8a5.6 5.6 0 0 1 7 4.4 2.7 2.7 0 0 1 .3 5.3h-7.3"/>' },
    { name: 'YouTube', handle: 'Reytek1201', verb: 'Watch', url: 'https://www.youtube.com/@Reytek1201',
      g: '<rect x="2.5" y="5.5" width="19" height="13" rx="4"/><path d="M10 9.2v5.6l4.8-2.8z"/>' },
    { name: 'X', handle: 'reytek1201', verb: 'Follow', url: 'https://x.com/reytek1201',
      g: '<path d="M4 4h4.6L20 20h-4.6z"/><path d="M19.5 4l-6.4 7.2"/><path d="M10.9 12.8L4.5 20"/>' },
    { name: 'Instagram', handle: 'reytek.1201', verb: 'See the art', url: 'https://www.instagram.com/reytek.1201/',
      g: '<rect x="3.5" y="3.5" width="17" height="17" rx="5"/><circle cx="12" cy="12" r="4"/><circle cx="17" cy="7" r=".5"/>' },
    { name: 'TikTok', handle: 'reytek1201', verb: 'Watch', url: 'https://www.tiktok.com/@reytek1201',
      g: '<path d="M14 3.5v11a3.5 3.5 0 1 1-3.5-3.5"/><path d="M14 3.5c.5 2.7 2.4 4.4 5 4.6"/>' },
    { name: 'Facebook', handle: 'Reytek', verb: 'Connect', url: 'https://www.facebook.com/profile.php?id=61580613560322',
      g: '<path d="M15.5 3.5h-2a3.5 3.5 0 0 0-3.5 3.5v13.5"/><path d="M7.5 10.5h7.5"/>' }
  ];
  function scrambleText(el, text) {
    if (reduce) { el.textContent = text; return; }
    let f = 0; clearInterval(el._sc);
    el._sc = setInterval(() => {
      f++;
      el.textContent = text.split('').map((ch, i) => (i < f / 1.6 || ch === ' ') ? ch : GLYPHS[Math.floor(Math.random() * GLYPHS.length)]).join('');
      if (f / 1.6 >= text.length) { clearInterval(el._sc); el.textContent = text; }
    }, 28);
  }
  function makeChannel(c, i) {
    const a = document.createElement('a');
    a.className = 'ch'; a.href = c.url; a.target = '_blank'; a.rel = 'noopener';
    a.setAttribute('aria-label', `${c.name}, @${c.handle} (opens in a new tab)`);
    const g = c.g.replace(/<(path|rect|circle) /g, '<$1 pathLength="1" ');
    a.innerHTML = `<svg viewBox="0 0 48 48" aria-hidden="true"><circle class="ring" cx="24" cy="24" r="22.5"/><circle class="arc" cx="24" cy="24" r="22.5"/>` +
      `<g transform="translate(12 12)"><g class="ghost c">${g}</g><g class="ghost m">${g}</g><g class="glyph">${g}</g></g></svg>` +
      `<span class="tip" aria-hidden="true"><b>${c.name}</b><i>ch.0${i + 1} · ${c.verb}</i></span>`;
    const label = a.querySelector('.tip b');
    a.addEventListener('pointerenter', () => scrambleText(label, c.name));
    a.addEventListener('focus', () => scrambleText(label, c.name));
    a.addEventListener('pointermove', e => {
      if (reduce || e.pointerType !== 'mouse') return;
      const r = a.getBoundingClientRect(), dx = e.clientX - (r.left + r.width / 2), dy = e.clientY - (r.top + r.height / 2);
      a.style.transform = `translate(${clamp(dx * 0.3, -7, 7)}px,${clamp(dy * 0.3, -7, 7)}px)`;
    });
    a.addEventListener('pointerleave', () => { a.style.transform = ''; });
    return a;
  }
  const rail = $('#rail'), dock = $('#dock'), railIcons = [];
  CHANNELS.forEach((c, i) => { if (rail) { const a = makeChannel(c, i); rail.appendChild(a); railIcons.push(a); } if (dock) dock.appendChild(makeChannel(c, i)); });
  let pingIdx = 0;
  if (railIcons.length && !reduce) setInterval(() => { const a = railIcons[pingIdx++ % railIcons.length]; a.classList.remove('ping'); void a.offsetWidth; a.classList.add('ping'); }, 1600);
  const foot = document.querySelector('footer');
  if (foot && 'IntersectionObserver' in window) new IntersectionObserver(es => es.forEach(en => document.body.classList.toggle('foot-in', en.isIntersecting)), { threshold: 0.25 }).observe(foot);

  /* buttons: the same magnetic pull and ripple as the homepage */
  document.querySelectorAll('.btn').forEach(bt => {
    bt.addEventListener('pointermove', e => {
      if (reduce || e.pointerType !== 'mouse') return;
      const r = bt.getBoundingClientRect(), dx = e.clientX - (r.left + r.width / 2), dy = e.clientY - (r.top + r.height / 2);
      bt.style.setProperty('--mgx', clamp(dx * 0.18, -6, 6).toFixed(1) + 'px'); bt.style.setProperty('--mgy', clamp(dy * 0.3, -4, 4).toFixed(1) + 'px');
    });
    bt.addEventListener('pointerleave', () => { bt.style.setProperty('--mgx', '0px'); bt.style.setProperty('--mgy', '0px'); });
    bt.addEventListener('pointerdown', e => {
      if (reduce) return;
      const r = bt.getBoundingClientRect(), rp = document.createElement('span'); rp.className = 'rip';
      rp.style.left = (e.clientX - r.left) + 'px'; rp.style.top = (e.clientY - r.top) + 'px'; rp.style.setProperty('--rs', (Math.max(r.width, r.height) / 5).toFixed(1));
      bt.appendChild(rp); setTimeout(() => rp.remove(), 700);
    });
  });

  /* the frame's corner light rests top-right, like the homepage when it's quiet */
  const corners = document.querySelectorAll('#frame i');
  corners.forEach((c, i) => c.classList.toggle('on', i === 1));
})();
