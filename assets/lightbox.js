(() => {
  const lb = document.getElementById('lb'); if (!lb || !lb.showModal) return;
  const big = document.getElementById('lbImg'), cap = document.getElementById('lbCap'), n = document.getElementById('lbN');
  const imgs = [...document.querySelectorAll('#lanes .ev-media img')];
  let i = 0, list = imgs;
  const vis = () => { const v = imgs.filter(im => im.offsetParent !== null); return v.length ? v : imgs; };
  const show = k => {
    i = (k + list.length) % list.length;
    const im = list[i]; big.src = im.currentSrc || im.src; big.alt = im.alt; cap.textContent = im.alt;
    n.textContent = list.length > 1 ? (i + 1) + ' / ' + list.length : '';
    lb.querySelectorAll('.lb-prev,.lb-next').forEach(b => b.hidden = list.length < 2);
  };
  imgs.forEach(im => {
    im.tabIndex = 0; im.setAttribute('role', 'button'); im.setAttribute('aria-label', 'Expand photo: ' + im.alt);
    const open = () => {
      list = vis(); show(Math.max(0, list.indexOf(im))); lb.showModal(); curs.forEach(c => c && lb.appendChild(c)); document.documentElement.style.overflow = 'hidden';
      try { if (window.gtag) window.gtag('event', 'photo_open', { photo: im.getAttribute('src') }); } catch (e) {}
    };
    im.addEventListener('click', open);
    im.addEventListener('keydown', e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); open(); } });
  });
  document.getElementById('lbPrev').onclick = () => show(i - 1);
  document.getElementById('lbNext').onclick = () => show(i + 1);
  document.getElementById('lbX').onclick = () => lb.close();
  lb.addEventListener('click', e => { if (e.target === lb || e.target.tagName === 'FIGURE') lb.close(); });
  const curs = [document.getElementById('cur'), document.getElementById('dot')];
  const unlock = () => { document.documentElement.style.overflow = ''; curs.forEach(c => c && c.parentNode === lb && document.body.appendChild(c)); };
  lb.addEventListener('close', unlock); lb.addEventListener('cancel', unlock);
  lb.addEventListener('keydown', e => { if (e.key === 'ArrowLeft') show(i - 1); else if (e.key === 'ArrowRight') show(i + 1); });
  let x0 = null;
  lb.addEventListener('touchstart', e => { x0 = e.touches[0].clientX; }, { passive: true });
  lb.addEventListener('touchend', e => { if (x0 === null) return; const dx = e.changedTouches[0].clientX - x0; x0 = null; if (Math.abs(dx) > 50) show(i + (dx < 0 ? 1 : -1)); });
})();
