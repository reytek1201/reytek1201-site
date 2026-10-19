/* ---------- Reytek Vision: the site's TV ----------
   A chunky set with a power button, a keypad and a channel guide. Every video is a channel. Standby shows the poster;
   pressing it (or a channel) tunes in: a scanline flash, the channel number on screen, then the YouTube player
   (privacy mode, controls off) with the set's own controls. The player loads only on tune-in. When a video starts,
   every other sound on the site stops; when the site's sound starts, the video pauses. The picture is never covered
   by effects while it plays. Leaving the page removes the player. */
(() => {
  const track = (name, params) => { try { if (window.gtag) window.gtag('event', name, params); } catch (e) {} };
  const fmt = s => { s = Math.max(0, Math.floor(s || 0)); return Math.floor(s / 60) + ':' + String(s % 60).padStart(2, '0'); };

  window.RT.onPage(() => {
    const tv = document.getElementById('tv');
    if (!tv) return;
    let chans = [];
    try { chans = JSON.parse((document.getElementById('visData') || {}).textContent || '[]'); } catch (e) {}
    if (!chans.length) return;
    const $ = id => document.getElementById(id);
    const all = sel => [...tv.querySelectorAll(sel)];
    const el = {
      vision: $('vision'), fit: $('tvFit'), rig: $('tvRig'), tilt: $('tvTilt'), screen: $('tvScreen'), mount: $('tvVideo'), standby: $('tvStandby'), poster: $('tvPoster'),
      cue: $('tvCue'), osd: $('tvOsd'), stat: $('tvStatic'), end: $('tvEnd'), endK: $('tvEndK'), endT: $('tvEndT'), endGo: $('tvEndGo'), endStay: $('tvEndStay'),
      fsbar: $('tvFsBar'), chnum: $('tvChNum'), foot: $('tvFoot'),
      nowK: $('tvNowK'), nowT: $('tvNowT'), nowB: $('tvNowB'), nowLink: $('tvNowLink'), tally: $('tvTally'), live: $('tvLive')
    };
    const acts = n => all('[data-act="' + n + '"]');
    const seeks = all('[data-seek]'), times = all('[data-time]');
    const guide = [...document.querySelectorAll('.vg-chan')];
    const reduce = matchMedia('(prefers-reduced-motion: reduce)');
    const wide = matchMedia('(min-width: 760px)');
    const ac = new AbortController(), on = { signal: ac.signal };
    const YT_HOST = 'https://www.youtube-nocookie.com';
    const FS = el.screen.requestFullscreen ? 'requestFullscreen' : el.screen.webkitRequestFullscreen ? 'webkitRequestFullscreen' : null;
    let player = null, apiP = null, ready = false, idx = 0, tuned = false, st = -1, dragging = false, powered = true;
    let osdT = 0, endT = 0, tuneSeq = 0, bootT = 0, keyT = 0, keyBuf = '', fsT = 0;

    const each = (list, fn) => list.forEach(fn);
    if (!FS) each(acts('full'), b => { b.hidden = true; });
    const setNav = () => { const d = chans.length < 2; each(acts('up').concat(acts('down')), b => { b.disabled = d; }); };
    setNav();

    const setState = s => {
      tv.dataset.state = s;
      el.tally.textContent = { standby: 'Standby', tuning: 'Tuning', playing: 'On air', paused: 'Paused', ended: 'Signal ends' }[s] || '';
      const playing = s === 'playing';
      each(acts('play'), b => { b.setAttribute('aria-pressed', playing ? 'true' : 'false'); b.setAttribute('aria-label', playing ? 'Pause' : 'Play'); });
    };
    const setTimes = (t, v) => { each(times, x => { x.textContent = t; }); if (v != null) each(seeks, x => { x.value = v; }); };
    const enableSeek = yes => { each(seeks, x => { x.disabled = !yes; }); each(acts('mute'), b => { b.disabled = !yes; }); };
    const posterUrl = c => /^https?:/.test(c.poster) ? c.poster : rtUrl(c.poster);
    const select = (i, announce) => {
      idx = (i + chans.length) % chans.length;
      const c = chans[idx];
      if (c.rgb) tv.style.setProperty('--vc', c.rgb); else tv.style.removeProperty('--vc');
      guide.forEach((li, n) => { li.classList.toggle('on', n === idx); li.querySelector('.tick').textContent = n === idx && tuned ? 'On air' : ''; });
      el.nowK.textContent = 'CH.' + c.n + (c.meta ? ' · ' + c.meta : '');
      el.nowT.textContent = c.title; el.nowB.textContent = c.blurb; el.nowB.hidden = !c.blurb;
      el.nowLink.href = 'https://www.youtube.com/watch?v=' + c.id;
      el.cue.textContent = 'CH.' + c.n;
      if (el.chnum) el.chnum.textContent = c.n;
      if (el.foot) el.foot.textContent = 'CH.' + c.n + ' · ' + c.title;
      el.standby.setAttribute('aria-label', 'Tune in to channel ' + c.n + ': ' + c.title);
      if (!tuned && el.poster) { el.poster.src = posterUrl(c); }
      if (announce) el.live.textContent = 'Channel ' + c.n + ': ' + c.title;
    };
    const showOsd = text => {
      el.osd.textContent = text; el.osd.classList.add('on');
      clearTimeout(osdT); osdT = setTimeout(() => el.osd.classList.remove('on'), 2200);
    };
    const flash = () => {
      if (reduce.matches) return;
      el.stat.classList.remove('go'); void el.stat.offsetWidth; el.stat.classList.add('go');
    };
    const clearEnd = () => { clearInterval(endT); el.end.hidden = true; };

    const loadApi = () => apiP || (apiP = new Promise((res, rej) => {
      if (window.YT && window.YT.Player) return res();
      const prev = window.onYouTubeIframeAPIReady;
      window.onYouTubeIframeAPIReady = () => { try { if (prev) prev(); } catch (e) {} res(); };
      const s = document.createElement('script');
      s.src = 'https://www.youtube.com/iframe_api'; s.onerror = () => { apiP = null; rej(new Error('player')); };
      document.head.appendChild(s);
    }));

    const onState = e => {
      st = e.data;
      if (st === 1) {
        setState('playing');
        if (window.RTSite) window.RTSite.quiet();
        enableSeek(true);
      } else if (st === 2) setState('paused');
      else if (st === 0) onEnd();
    };

    const tune = async i => {
      if (!powered) power(true);
      const seq = ++tuneSeq;
      clearEnd();
      tuned = true;
      select(i, true);
      const c = chans[idx];
      el.standby.hidden = true;
      setState('tuning');
      flash(); showOsd('CH.' + c.n);
      if (window.RTSite) window.RTSite.quiet();   // the site's music stops the moment you tune in
      try { await loadApi(); } catch (e) {
        if (seq !== tuneSeq) return;
        tuned = false; el.standby.hidden = false; setState('standby'); select(idx);
        el.live.textContent = 'The player could not load. Use Watch on YouTube instead.';
        return;
      }
      if (seq !== tuneSeq) return;
      if (!player) {
        const d = document.createElement('div');
        el.mount.replaceChildren(d);
        const noFs = !document.fullscreenEnabled && !document.webkitFullscreenEnabled;   // iPhone: let the system player take over
        player = new YT.Player(d, {
          host: YT_HOST, videoId: c.id,
          playerVars: { autoplay: 1, controls: 0, rel: 0, playsinline: noFs ? 0 : 1, fs: 0, modestbranding: 1, iv_load_policy: 3, disablekb: 1, origin: location.origin },
          events: {
            onReady: () => { ready = true; try { player.playVideo(); } catch (e) {} },
            onStateChange: onState
          }
        });
      } else if (ready) { player.loadVideoById(c.id); }
      track('video_play', { video: c.id });
    };

    const onEnd = () => {
      setState('ended');
      el.endStay.hidden = chans.length < 2;
      if (chans.length > 1) {
        const nx = chans[(idx + 1) % chans.length];
        let n = 5;
        const paint = () => { el.endK.textContent = 'Next · CH.' + nx.n; el.endT.textContent = nx.title + ' in ' + n; };
        el.endGo.textContent = 'Tune now';
        el.endGo.onclick = () => tune(idx + 1);
        el.endStay.onclick = () => { clearEnd(); };
        paint(); el.end.hidden = false;
        clearInterval(endT);
        endT = setInterval(() => { n -= 1; if (n <= 0) { clearInterval(endT); tune(idx + 1); } else paint(); }, 1000);
      } else {
        el.endK.textContent = 'Signal ends'; el.endT.textContent = '';
        el.endGo.textContent = 'Watch again';
        el.endGo.onclick = () => { clearEnd(); try { player.seekTo(0, true); player.playVideo(); } catch (e) {} };
        el.end.hidden = false;
      }
      el.endGo.focus({ preventScroll: true });
    };

    // power: off stops the picture and dims the shell; on runs a short boot (traces draw, screen opens)
    const fullOn = () => !!(document.fullscreenElement || document.webkitFullscreenElement);
    const exitFull = () => { try { if (fullOn()) (document.exitFullscreen || document.webkitExitFullscreen).call(document); } catch (e) {} };
    const power = yes => {
      if (yes === powered) return;
      powered = yes;
      tv.dataset.power = yes ? 'on' : 'off';
      each(acts('power'), b => { b.setAttribute('aria-pressed', yes ? 'true' : 'false'); b.setAttribute('aria-label', yes ? 'Power off' : 'Power on'); });
      clearTimeout(bootT);
      if (!yes) {
        tuneSeq++; clearEnd(); exitFull(); keyBuf = '';
        try { if (player && ready) player.stopVideo(); } catch (e) {}
        try { if (player && player.destroy) player.destroy(); } catch (e) {}
        player = null; ready = false; st = -1; tuned = false;
        el.mount.replaceChildren();
        el.standby.hidden = false; el.osd.classList.remove('on');
        enableSeek(false); setTimes('0:00', 0);
        setState('standby'); select(idx);
        delete tv.dataset.boot;
        el.live.textContent = 'Power off';
      } else {
        if (!reduce.matches) { tv.dataset.boot = '1'; bootT = setTimeout(() => { delete tv.dataset.boot; }, 1400); }
        el.live.textContent = 'Power on';
      }
    };

    // controls
    el.standby.addEventListener('click', () => tune(idx), on);
    guide.forEach((li, n) => li.querySelector('button').addEventListener('click', () => tune(n), on));
    each(acts('power'), b => b.addEventListener('click', () => power(!powered), on));
    each(acts('up'), b => b.addEventListener('click', () => tune(idx + 1), on));
    each(acts('down'), b => b.addEventListener('click', () => tune(idx - 1), on));
    each(acts('play'), b => b.addEventListener('click', () => {
      if (!powered) power(true);
      if (!tuned) return tune(idx);
      if (!player || !ready) return;
      try { if (st === 1) player.pauseVideo(); else { clearEnd(); player.playVideo(); } } catch (e) {}
    }, on));
    each(acts('mute'), b => b.addEventListener('click', () => {
      if (!player || !ready) return;
      try {
        const m = player.isMuted(); if (m) player.unMute(); else player.mute();
        each(acts('mute'), x => { x.setAttribute('aria-pressed', m ? 'false' : 'true'); x.setAttribute('aria-label', m ? 'Mute' : 'Unmute'); });
      } catch (e) {}
    }, on));
    each(seeks, s => {
      s.addEventListener('input', () => { dragging = true; try { setTimes(fmt(s.value / 1000 * player.getDuration()), s.value); } catch (e) {} }, on);
      s.addEventListener('change', () => { dragging = false; try { player.seekTo(s.value / 1000 * player.getDuration(), true); } catch (e) {} }, on);
    });
    const toggleFull = () => {
      if (!FS || !powered) return;
      try { if (fullOn()) (document.exitFullscreen || document.webkitExitFullscreen).call(document); else el.screen[FS](); } catch (e) {}
    };
    each(acts('full'), b => b.addEventListener('click', toggleFull, on));
    const fsChange = () => {
      const f = fullOn();
      each(acts('full'), b => { if (!el.fsbar.contains(b)) b.setAttribute('aria-pressed', f ? 'true' : 'false'); });
      if (f) pokeBar();
    };
    document.addEventListener('fullscreenchange', fsChange, on);
    document.addEventListener('webkitfullscreenchange', fsChange, on);
    // in full screen the control bar shows on movement and hides after a moment
    const pokeBar = () => { el.fsbar.classList.add('on'); clearTimeout(fsT); fsT = setTimeout(() => { if (!el.fsbar.contains(document.activeElement)) el.fsbar.classList.remove('on'); }, 2600); };
    el.screen.addEventListener('pointermove', () => { if (fullOn()) pokeBar(); }, on);
    el.screen.addEventListener('click', () => { if (fullOn()) pokeBar(); }, on);

    // keypad: digits build a channel number; no such channel shows NO SIGNAL
    const digit = d => {
      if (!powered) power(true);
      keyBuf = (keyBuf + d).slice(-2);
      showOsd('CH.' + keyBuf.padStart(2, '0'));
      clearTimeout(keyT);
      keyT = setTimeout(() => {
        const n = parseInt(keyBuf, 10), buf = keyBuf; keyBuf = '';
        if (n >= 1 && n <= chans.length) tune(n - 1);
        else { flash(); showOsd('NO SIGNAL'); el.live.textContent = 'No signal on channel ' + buf.padStart(2, '0'); }
      }, 1200);
    };
    all('[data-key]').forEach(b => b.addEventListener('click', () => digit(b.dataset.key), on));

    // keyboard, while focus is on the TV or the guide: up/down channel, space play/pause, F full screen, M mute, digits
    document.addEventListener('keydown', e => {
      if (e.metaKey || e.ctrlKey || e.altKey || !el.vision.contains(e.target)) return;
      if (e.target.matches && e.target.matches('input')) return;
      const k = e.key;
      if (k === 'ArrowUp' && chans.length > 1) { e.preventDefault(); tune(idx - 1); }
      else if (k === 'ArrowDown' && chans.length > 1) { e.preventDefault(); tune(idx + 1); }
      else if ((k === 'f' || k === 'F') && FS) { e.preventDefault(); toggleFull(); }
      else if (k === 'm' || k === 'M') { e.preventDefault(); const b = acts('mute').find(x => x.offsetParent !== null && !x.disabled); if (b) b.click(); }
      else if (/^[0-9]$/.test(k)) { e.preventDefault(); const kb = tv.querySelector('[data-key="' + k + '"]'); if (kb) digit(k); else { showOsd('LOCKED'); el.live.textContent = 'Channel ' + k + ' is locked'; } }
      else if (k === ' ' && !(e.target.closest && e.target.closest('button, a'))) { e.preventDefault(); const b = acts('play').find(x => x.offsetParent !== null) || acts('play')[0]; if (b) b.click(); }
    }, on);

    // progress, and the handoff: if the site's sound starts while the video plays, the video pauses
    const poll = setInterval(() => {
      if (!player || !ready || typeof player.getCurrentTime !== 'function') return;
      try {
        const d = player.getDuration() || 0, t = player.getCurrentTime() || 0;
        if (!dragging) setTimes(fmt(t), d ? Math.round(t / d * 1000) : 0);
        if (st === 1 && window.RTSite && window.RTSite.sounding()) player.pauseVideo();
      } catch (e) {}
    }, 250);

    // the rig is drawn at 1200x680 and scaled to the width of its box; phones use the plain layout instead
    const fit = () => { if (wide.matches && el.fit.clientWidth) el.rig.style.setProperty('--s', (el.fit.clientWidth / 1200).toFixed(4)); else el.rig.style.removeProperty('--s'); };
    const ro = window.ResizeObserver ? new ResizeObserver(fit) : null;
    if (ro) ro.observe(el.fit);
    fit();
    wide.addEventListener('change', fit, on);

    // a small tilt toward the pointer, desktop only; never while reduced motion is on
    const fine = matchMedia('(pointer: fine)');
    const tiltOn = () => wide.matches && fine.matches && !reduce.matches;
    const onMove = e => {
      if (!tiltOn() || fullOn()) return;
      const r = el.fit.getBoundingClientRect();
      const x = Math.max(-1, Math.min(1, ((e.clientX - r.left) / r.width - .5) * 2));
      const y = Math.max(-1, Math.min(1, ((e.clientY - r.top) / r.height - .5) * 2));
      el.tilt.style.transform = 'perspective(1400px) rotateY(' + (x * 4).toFixed(2) + 'deg) rotateX(' + (-y * 3).toFixed(2) + 'deg)';
    };
    const onLeave = () => { el.tilt.style.transform = ''; };
    el.fit.addEventListener('pointermove', onMove, on);
    el.fit.addEventListener('pointerleave', onLeave, on);

    // off screen, the glow animations pause
    const io = window.IntersectionObserver ? new IntersectionObserver(es => { tv.dataset.vis = es[es.length - 1].isIntersecting ? '1' : '0'; }) : null;
    if (io) io.observe(tv);

    // a link ending in #<channel> selects it (standby: nothing plays until pressed)
    const fromHash = () => {
      const slug = decodeURIComponent((location.hash || '').slice(1));
      const i = chans.findIndex(c => c.slug === slug);
      if (i >= 0 && !tuned) select(i, false);
    };
    fromHash();
    addEventListener('hashchange', fromHash, on);
    select(idx, false);

    // first look: the traces draw in once
    if (!reduce.matches) { tv.dataset.boot = '1'; bootT = setTimeout(() => { delete tv.dataset.boot; }, 1400); }

    return () => {
      ac.abort(); clearInterval(poll); clearInterval(endT); clearTimeout(osdT); clearTimeout(bootT); clearTimeout(keyT); clearTimeout(fsT);
      if (ro) ro.disconnect(); if (io) io.disconnect();
      exitFull();
      try { if (player && player.destroy) player.destroy(); } catch (e) {}
    };
  });
})();
