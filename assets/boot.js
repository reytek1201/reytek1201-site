/* ---------- cold start: a record that spins up as the site loads, then hands off to the vortex ---------- */
window.BOOT = (() => {
  const el = document.getElementById('boot'), cv = document.getElementById('bootRec'), g = cv.getContext('2d');
  const reduce = matchMedia('(prefers-reduced-motion: reduce)').matches;
  let visited = false; try { visited = !!localStorage.getItem('rt-visited'); localStorage.setItem('rt-visited', '1'); } catch (e) {}
  const SHORT_FOR_RETURNING = false;                 // turn on at launch: returning visitors get a quick version
  const MIN = (SHORT_FOR_RETURNING && visited) ? 0.55 : 2.2;   // seconds, so it never just flickers
  const STEPS = { shell: [0.1, 'warming up the platter'], engine: [0.35, '3D engine loaded'], fonts: [0.15, 'type set'], portrait: [0.2, 'portrait developed'], assets: [0.2, 'signal found'] };
  const done = {}; let target = 0, shown = 0, label = 'cold start';
  let angle = 0, dotA = 0, rpm = 0, phase = 'load', pt = 0, t0 = performance.now() / 1000, last = t0, onDone = null, flash = 0, W = 0, H = 0, dpr = 1;
  const clamp = (v, a = 0, b = 1) => Math.min(b, Math.max(a, v)), lerp = (a, b, t) => a + (b - a) * t;
  function mark(k) { if (done[k] || !STEPS[k]) return; done[k] = 1; target = Object.keys(done).reduce((s, n) => s + STEPS[n][0], 0); label = STEPS[k][1]; }
  function size() {
    dpr = Math.min(devicePixelRatio || 1, 2); W = innerWidth; H = innerHeight;
    cv.width = Math.round(W * dpr); cv.height = Math.round(H * dpr); cv.style.width = W + 'px'; cv.style.height = H + 'px';
  }
  size(); addEventListener('resize', size);
  // centre the record where the portrait will open, so the label becomes the face
  function centre() {
    const f = document.getElementById('face');
    if (f) { const r = f.getBoundingClientRect(); if (r.width) return [r.left + r.width / 2, r.top + r.height / 2]; }
    return [W / 2, H * 0.45];
  }
  // tonearm: pivot top right, needle swings in on an arc
  function armGeo(R, cx, cy) { return { px: cx + R * 1.16, py: cy - R * 0.92, L: R * 1.62 }; }
  function needleAt(a, phi) { return [a.px + a.L * Math.cos(phi), a.py + a.L * Math.sin(phi)]; }
  function phiFor(a, cx, cy, r) {
    let lo = Math.PI * 0.5, hi = Math.PI * 0.98;
    for (let i = 0; i < 26; i++) { const m = (lo + hi) / 2, [x, y] = needleAt(a, m); if (Math.hypot(x - cx, y - cy) > r) lo = m; else hi = m; }
    return (lo + hi) / 2;
  }
  let phi = Math.PI * 0.5, lift = 1;
  const MONO = '"IBM Plex Mono", ui-monospace, Menlo, monospace';

  function draw(dt) {
    const [cx, cy] = centre(), R = Math.min(W * 0.34, H * 0.3, 330), rel = phase === 'release' ? clamp(pt / 1.15) : 0;
    g.setTransform(dpr, 0, 0, dpr, 0, 0);
    g.clearRect(0, 0, W, H);
    g.fillStyle = `rgba(5,6,8,${1 - rel})`; g.fillRect(0, 0, W, H);
    const fadeRec = 1 - clamp(rel * 1.6), grooveR = lerp(R * 0.97, R * 0.37, shown);
    if (fadeRec > 0.001) {
      g.save(); g.globalAlpha = fadeRec; g.translate(cx, cy); const sc = 1 + rel * 0.25; g.scale(sc, sc);
      // platter + strobe dots (stand still once at speed)
      g.fillStyle = '#121418'; g.beginPath(); g.arc(0, 0, R * 1.07, 0, 7); g.fill();
      const locked = Math.abs(rpm - 33.333) < 0.25;
      g.fillStyle = locked ? `rgba(${THEME.rgb},.95)` : 'rgba(200,205,214,.35)';
      if (locked) { g.shadowColor = `rgba(${THEME.rgb},.9)`; g.shadowBlur = 6; }
      for (let i = 0; i < 96; i++) { const a = dotA + i / 96 * Math.PI * 2; g.beginPath(); g.arc(Math.cos(a) * R * 1.035, Math.sin(a) * R * 1.035, Math.max(1, R * 0.008), 0, 7); g.fill(); }
      g.shadowBlur = 0;
      // record
      g.fillStyle = '#08090b'; g.beginPath(); g.arc(0, 0, R, 0, 7); g.fill();
      // grooves cut so far (outer edge in to the needle), blank vinyl inside
      g.lineWidth = 1;
      for (let r = R * 0.97; r > grooveR; r -= 2.2) { g.strokeStyle = (Math.round(r) % 2) ? 'rgba(255,255,255,.035)' : 'rgba(0,0,0,.5)'; g.beginPath(); g.arc(0, 0, r, 0, 7); g.stroke(); }
      // light falling across the grooves (fixed: the light doesn't spin, the record does)
      if (g.createConicGradient) {
        const cg = g.createConicGradient(-0.9, 0, 0);
        cg.addColorStop(0, 'rgba(210,220,235,.16)'); cg.addColorStop(0.07, 'rgba(210,220,235,0)'); cg.addColorStop(0.43, 'rgba(210,220,235,0)');
        cg.addColorStop(0.5, 'rgba(210,220,235,.12)'); cg.addColorStop(0.57, 'rgba(210,220,235,0)'); cg.addColorStop(0.93, 'rgba(210,220,235,0)'); cg.addColorStop(1, 'rgba(210,220,235,.16)');
        g.fillStyle = cg; g.beginPath(); g.arc(0, 0, R * 0.97, 0, 7); g.arc(0, 0, grooveR, 0, 7, true); g.fill();
      }
      // the cutting point glows where the needle rides
      if (phase !== 'release') { g.strokeStyle = `rgba(${THEME.rgb},${0.35 + 0.25 * Math.sin(performance.now() / 160)})`; g.lineWidth = 1.5; g.beginPath(); g.arc(0, 0, grooveR, 0, 7); g.stroke(); }
      // label (rotates)
      g.save(); g.rotate(angle);
      const LR = R * 0.33, lg = g.createRadialGradient(0, 0, 0, 0, 0, LR); lg.addColorStop(0, '#16191f'); lg.addColorStop(1, '#0c0d10');
      g.fillStyle = lg; g.beginPath(); g.arc(0, 0, LR, 0, 7); g.fill();
      g.strokeStyle = `rgba(${THEME.rgb},.75)`; g.lineWidth = 1.5; g.beginPath(); g.arc(0, 0, LR * 0.82, 0, 7); g.stroke();
      g.fillStyle = 'rgba(237,235,230,.75)'; g.font = `500 ${Math.max(8, LR * 0.1)}px ${MONO}`; g.textAlign = 'center'; g.textBaseline = 'middle';
      const txt = 'REYTEK · SIDE A · 33⅓ RPM · COLD START · ', st = Math.PI * 2 / txt.length;
      for (let k = 0; k < txt.length; k++) { g.save(); g.rotate(k * st); g.translate(0, -LR * 0.91); g.fillText(txt[k], 0, 0); g.restore(); }
      g.fillStyle = 'rgba(237,235,230,.92)'; g.font = `800 ${Math.max(10, LR * 0.22)}px Anybody, "Arial Black", sans-serif`; g.fillText('REYTEK', 0, -LR * 0.32);
      g.fillStyle = `rgba(${THEME.rgb},.85)`; g.font = `500 ${Math.max(8, LR * 0.1)}px ${MONO}`; g.fillText('SIDE A', 0, LR * 0.3);
      g.restore();
      g.fillStyle = '#c9ced6'; g.beginPath(); g.arc(0, 0, Math.max(2, R * 0.016), 0, 7); g.fill();
      g.restore();
      // tonearm (drawn unrotated, in screen space)
      const a = armGeo(R, cx, cy);
      const want = phase === 'load' ? phiFor(a, cx, cy, grooveR) : phi;
      phi = lerp(phi, want, 1 - Math.exp(-dt * 7));
      lift = lerp(lift, phase === 'load' ? 1 : 0, 1 - Math.exp(-dt * (phase === 'load' ? 6 : 18)));
      const [nx, ny] = needleAt(a, phi), sh = 3 + lift * 12;
      g.save(); g.globalAlpha = fadeRec; g.lineCap = 'round';
      const arm = (ox, oy, col, w) => {
        g.strokeStyle = col; g.lineWidth = w;
        g.beginPath(); g.moveTo(a.px - Math.cos(phi) * R * 0.28 + ox, a.py - Math.sin(phi) * R * 0.28 + oy); g.lineTo(nx - Math.cos(phi) * R * 0.12 + ox, ny - Math.sin(phi) * R * 0.12 + oy); g.stroke();
      };
      arm(sh, sh * 1.2, 'rgba(0,0,0,.55)', R * 0.04);                                       // shadow
      g.fillStyle = '#1b1e24'; g.beginPath(); g.arc(a.px, a.py, R * 0.17, 0, 7); g.fill();      // base
      g.strokeStyle = 'rgba(255,255,255,.12)'; g.lineWidth = 1; g.stroke();
      arm(0, 0, '#cfd4dc', R * 0.032);
      g.strokeStyle = 'rgba(255,255,255,.55)'; g.lineWidth = R * 0.008; arm(-R * 0.006, -R * 0.006, 'rgba(255,255,255,.5)', R * 0.008);
      const cw = needleAt(a, phi + Math.PI).map((v, i) => lerp(i ? a.py : a.px, v, 0.2));      // counterweight
      g.fillStyle = '#2a2e35'; g.beginPath(); g.arc(cw[0], cw[1], R * 0.07, 0, 7); g.fill();
      g.fillStyle = '#9ea4ae'; g.beginPath(); g.arc(a.px, a.py, R * 0.06, 0, 7); g.fill();
      // headshell with the cyan stripe
      g.save(); g.translate(nx, ny); g.rotate(phi);
      g.fillStyle = 'rgba(0,0,0,.5)'; g.fillRect(-R * 0.13 + sh, -R * 0.045 + sh * 1.2, R * 0.16, R * 0.09);
      g.fillStyle = '#16181c'; g.fillRect(-R * 0.13, -R * 0.045, R * 0.16, R * 0.09);
      g.fillStyle = `rgba(${THEME.rgb},.9)`; g.fillRect(-R * 0.12, -R * 0.008, R * 0.13, R * 0.016);
      g.restore();
      // needle glow once it's down
      if (lift < 0.5) { const gr = g.createRadialGradient(nx, ny, 0, nx, ny, R * 0.12); gr.addColorStop(0, `rgba(${THEME.tint(0.55)},${(1 - lift * 2) * 0.9})`); gr.addColorStop(1, `rgba(${THEME.rgb},0)`); g.fillStyle = gr; g.beginPath(); g.arc(nx, ny, R * 0.12, 0, 7); g.fill(); }
      g.restore();
      // readout
      g.save(); g.globalAlpha = fadeRec; g.textAlign = 'center'; g.textBaseline = 'top';
      const ty = cy + R * 1.07 + 28;
      g.font = `500 11px ${MONO}`; g.fillStyle = 'rgba(138,140,148,.9)';
      g.fillText('REYTEK/SYS 26.10 · COLD START', cx, ty);
      g.fillStyle = 'rgba(237,235,230,.95)'; g.font = `500 13px ${MONO}`;
      g.fillText(`> ${label}`, cx, ty + 22);
      g.fillStyle = locked ? `rgba(${THEME.rgb},1)` : `rgba(${THEME.rgb},.7)`; g.font = `500 12px ${MONO}`;
      g.fillText(`${rpm >= 33.2 ? '33⅓' : rpm.toFixed(1)} RPM${locked ? ' · LOCKED' : ''}`, cx, ty + 44);
      g.restore();
    }
    // hand-off: the grooves lift off as rings of light and spin out into the vortex
    if (rel > 0 || flash > 0) {
      g.save(); g.translate(cx, cy); g.globalCompositeOperation = 'lighter';
      const n = 16;
      for (let i = 0; i < n; i++) {
        const r0 = lerp(R * 0.97, R * 0.4, i / (n - 1)), k = clamp(rel * 1.25 - i * 0.025);
        const r = r0 * (1 + k * k * 2.6), al = (1 - k) * 0.55 * (i % 3 === 0 ? 1.4 : 0.8);
        if (al <= 0.005) continue;
        g.strokeStyle = i % 4 === 0 ? `rgba(${THEME.rgb},${al})` : `rgba(237,235,230,${al * 0.7})`; g.lineWidth = 1.2 + (1 - k) * 1.2;
        g.beginPath(); g.ellipse(0, 0, r, r * (0.92 + 0.08 * Math.sin(i)), angle * 0.3 + i, 0, 7); g.stroke();
      }
      if (flash > 0) { const fg = g.createRadialGradient(0, 0, 0, 0, 0, R * 1.4); fg.addColorStop(0, `rgba(${THEME.tint(0.75)},${flash * 0.5})`); fg.addColorStop(1, `rgba(${THEME.rgb},0)`); g.fillStyle = fg; g.beginPath(); g.arc(0, 0, R * 1.4, 0, 7); g.fill(); }
      g.restore();
    }
  }

  function frame(nowMs) {
    const now = nowMs / 1000, dt = Math.max(0, Math.min(0.05, now - last)); last = now;
    const el2 = now - t0;
    // progress eases toward what has really loaded, but never faster than the minimum duration allows
    const cap = reduce ? 1 : clamp(el2 / MIN);
    shown = Math.min(lerp(shown, target, 1 - Math.exp(-dt * 5)) + dt * 0.04, target, cap + 0.0001);
    if (target >= 0.999 && cap >= 1) shown = lerp(shown, 1, 1 - Math.exp(-dt * 8));
    const want = reduce ? 0 : 33.333 * Math.pow(clamp(shown / 0.9), 0.7);
    rpm = phase === 'release' ? 33.333 : lerp(rpm, want, 1 - Math.exp(-dt * 6)); if (Math.abs(rpm - want) < 0.05) rpm = want;
    angle += rpm / 60 * Math.PI * 2 * dt;
    dotA += (rpm - 33.333) / 60 * Math.PI * 2 * dt * 0.35;
    flash *= Math.exp(-dt * 4);
    if (phase === 'load' && shown > 0.995 && target >= 0.999 && (reduce || Math.abs(rpm - 33.333) < 0.25)) { phase = 'drop'; pt = 0; label = 'signal found'; }
    if (phase === 'drop') { pt += dt; if (pt > 0.42) { flash = 1; go(); } }
    if (phase === 'release') { pt += dt; if (pt > 1.25) { el.classList.add('gone'); el.hidden = true; return; } }
    draw(dt);
    requestAnimationFrame(frame);
  }
  function go() {
    if (phase === 'release') return;
    if (!onDone) { phase = 'drop'; pt = 0.3; return; }    // main script not ready yet: hold on the drop
    phase = 'release'; pt = 0; el.classList.add('releasing');
    if (reduce) { pt = 9; el.hidden = true; }
    const f = onDone; onDone = null; f();
  }
  mark('shell');
  requestAnimationFrame(frame);
  return {
    mark,
    ready(fn) { onDone = fn; if (phase === 'drop' && pt > 0.42) go(); },
    skip() { target = 1; shown = 1; rpm = 33.333; phase = 'drop'; pt = 0.42; go(); },
    instant() { target = 1; shown = 1; rpm = 33.333; phase = 'release'; pt = 9; el.classList.add('releasing', 'gone'); el.hidden = true; const f = onDone; onDone = null; if (f) f(); }
  };
})();
